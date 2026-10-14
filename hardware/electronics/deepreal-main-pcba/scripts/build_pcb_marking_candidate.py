#!/usr/bin/env python3
"""Private annotation-only correction; leave all placement/copper/rules intact."""

import argparse
import hashlib
import json
import math
import re
import textwrap
from pathlib import Path

from build_pcb_connector_candidate import child, children, replace_ranges
from build_pcb_fit_candidate import top_level_blocks
from build_pcb_model_candidate import reference


OLD_NOTE = "U1 PROXY: 548-BALL MAP REQUIRED"
NEW_NOTE = "U1: 548 positions; AF22 unresolved; lands provisional"
WRAPS = {
    "PRELIMINARY PLACEMENT — NOT FOR FABRICATION":
        "PRELIMINARY PLACEMENT —\nNOT FOR FABRICATION",
    "UNROUTED: vendor pin maps + FPGA + DDR gates open":
        "UNROUTED: vendor pin maps\n+ FPGA + DDR gates open",
    "Support placeholders: 144 C / 44 R":
        "Support placeholders:\n144 C / 44 R",
    "DEEPREAL MAIN PCBA": "DEEPREAL\nMAIN PCBA",
}


def node(text, name):
    return child(text, re.match(r"\((\w+)", text)[1], name)[2]


def annotations(text):
    result = {}
    for start, _, block in top_level_blocks(text)[0]:
        nodes = [(start, block, None)] if block.startswith("(gr_text ") else []
        if block.startswith("(footprint "):
            ref = reference(block)
            nodes += [(start + a, item, ref) for a, _, item in children(block, "footprint")
                      if item.startswith('(property "Reference" ')]
        for offset, item, ref in nodes:
            uid = node(item, "uuid").split('"')[1]
            if uid in result:
                raise ValueError("Duplicate annotation UUID")
            result[uid] = (offset, offset + len(item), item, ref)
    return result


def annotation_signature(block):
    """Only placement and font size may differ; retain layer/visibility/mirror."""
    edits = []
    at = node(block, "at")
    if at:
        start = block.index(at)
        edits.append((start, start + len(at), "(at ALLOWED)"))
    effects = node(block, "effects")
    font = node(effects, "font")
    size = node(font, "size")
    if size:
        start = block.index(effects) + effects.index(font) + font.index(size)
        edits.append((start, start + len(size), "(size ALLOWED)"))
    normalized = replace_ranges(block, edits).replace(OLD_NOTE, NEW_NOTE)
    if normalized.startswith("(gr_text "):
        # Line wrapping may change whitespace, never the warning's words.
        match = re.match(r'\(gr_text ("(?:\\.|[^"\\])*")', normalized)
        value = " ".join(json.loads(match[1]).split())
        normalized = normalized[:match.start(1)] + json.dumps(value) + normalized[match.end(1):]
    return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+', normalized)


def verify_scope(before, after, allowed):
    old, new = annotations(before), annotations(after)
    if set(old) != set(new) or not set(allowed) <= set(old):
        raise ValueError("Annotation identity set changed")
    left, right = [], []
    for uid in allowed:
        a, b = old[uid], new[uid]
        if annotation_signature(a[2]) != annotation_signature(b[2]):
            raise ValueError("Non-position/size annotation edit: " + uid)
        left.append((a[0], a[1], "(ANNOTATION " + uid + ")"))
        right.append((b[0], b[1], "(ANNOTATION " + uid + ")"))
    if replace_ranges(before, left) != replace_ranges(after, right):
        raise ValueError("Change outside allowed annotations")


def rect(box):
    return (box.GetX(), box.GetY(), box.GetRight(), box.GetBottom())


def inflated(box, margin):
    x0, y0, x1, y1 = box
    return (x0 - margin, y0 - margin, x1 + margin, y1 + margin)


def intersects(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def warning_variants(text):
    """Reflow whole words only; never abbreviate or merge warning words."""
    words = " ".join(text.split())
    options = [WRAPS.get(words, text), words]
    options += [textwrap.fill(words, width=width, break_long_words=False,
                              break_on_hyphens=False) for width in (20, 16, 12, 9)]
    return list(dict.fromkeys(options))


def placement_offsets(origin, bounds, step, board_level):
    if board_level:
        # Board-level warnings may use the whole board; references stay local.
        xs = range(math.ceil((bounds[0] - origin[0]) / step),
                   math.floor((bounds[2] - origin[0]) / step) + 1)
        ys = range(math.ceil((bounds[1] - origin[1]) / step),
                   math.floor((bounds[3] - origin[1]) / step) + 1)
    else:
        xs = ys = range(-48, 49)
    return sorted(((x, y) for x in xs for y in ys),
                  key=lambda p: (p[0] ** 2 + p[1] ** 2, p))


def make_plan(board, drc, pcbnew):
    ids = {item["uuid"] for finding in drc["violations"]
           if finding["type"] in ("text_height", "silk_edge_clearance",
                                  "silk_overlap", "silk_over_copper")
           for item in finding["items"]}
    texts = {}
    for fp in board.GetFootprints():
        for item in (fp.Reference(), fp.Value(), *list(fp.GraphicalItems())):
            if item.m_Uuid.AsString() in ids and isinstance(item, pcbnew.PCB_FIELD):
                if item.GetName() != "Reference":
                    continue
                texts[item.m_Uuid.AsString()] = item
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.m_Uuid.AsString() in ids:
            texts[item.m_Uuid.AsString()] = item
    silk = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    texts = {uid: item for uid, item in texts.items()
             if item.GetLayer() in silk and item.IsVisible()}
    obstacles = {layer: [] for layer in silk}
    for fp in board.GetFootprints():
        side = pcbnew.B_SilkS if fp.IsFlipped() else pcbnew.F_SilkS
        fp.BuildCourtyardCaches()
        courtyard = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        if courtyard.OutlineCount():
            obstacles[side].append(rect(courtyard.BBox()))
        for pad in fp.Pads():
            for layer, mask in ((pcbnew.F_SilkS, pcbnew.F_Mask),
                                (pcbnew.B_SilkS, pcbnew.B_Mask)):
                if pad.IsOnLayer(mask):
                    obstacles[layer].append(rect(pad.GetBoundingBox()))
        for item in (*list(fp.GraphicalItems()), fp.Reference(), fp.Value()):
            if (item.GetLayer() in silk and item.m_Uuid.AsString() not in texts
                    and (not hasattr(item, "IsVisible") or item.IsVisible())):
                obstacles[item.GetLayer()].append(rect(item.GetBoundingBox()))
    for item in board.GetDrawings():
        layer = item.GetLayer()
        if layer == pcbnew.Edge_Cuts:
            for side in silk:
                obstacles[side].append(rect(item.GetBoundingBox()))
        elif layer in silk and item.m_Uuid.AsString() not in texts:
            obstacles[layer].append(rect(item.GetBoundingBox()))
    outline = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(outline, False):
        raise ValueError("No valid native board outline")
    margin = pcbnew.FromMM(0.25)
    step = pcbnew.FromMM(0.25)
    bounds = rect(outline.BBox())
    plan = []
    # Long warnings first, followed by stable UUID order; no random layout.
    for uid, item in sorted(texts.items(), key=lambda pair: (-len(pair[1].GetText()), pair[0])):
        original = item.GetPosition()
        origin = (original.x, original.y)
        original_text = item.GetText()
        board_level = not isinstance(item, pcbnew.PCB_FIELD)
        variants = warning_variants(original_text) if board_level else [original_text]
        offsets = placement_offsets(origin, bounds, step, board_level)
        old_size = item.GetTextSize()
        size = ((pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)) if board_level else
                (max(old_size.x, pcbnew.FromMM(0.8)),
                 max(old_size.y, pcbnew.FromMM(0.8))))
        item.SetTextSize(pcbnew.VECTOR2I(*size))
        layer = item.GetLayer()
        chosen = None
        for variant in variants:
            item.SetText(variant)
            item.SetPosition(pcbnew.VECTOR2I(*origin))
            base = inflated(rect(item.GetBoundingBox()), margin)
            for dx, dy in offsets:
                shift = (dx * step, dy * step)
                box = tuple(v + shift[i % 2] for i, v in enumerate(base))
                points = ((box[0], box[1]), (box[2], box[1]),
                          (box[2], box[3]), (box[0], box[3]))
                if not all(outline.Contains(pcbnew.VECTOR2I(*p)) for p in points):
                    continue
                if any(intersects(box, obstacle) for obstacle in obstacles[layer]):
                    continue
                chosen = (origin[0] + shift[0], origin[1] + shift[1])
                item.SetPosition(pcbnew.VECTOR2I(*chosen))
                break
            if chosen is not None:
                break
        if chosen is None:
            item.SetText(original_text)
            item.SetPosition(pcbnew.VECTOR2I(*origin))
        obstacles[layer].append(rect(item.GetBoundingBox()))
        plan.append({
            "uuid": uid, "text": item.GetText(),
            "original_text": original_text,
            "search_scope": "whole_board" if board_level else "reference_local_12mm",
            "original_position_mm": [pcbnew.ToMM(v) for v in origin],
            "position_mm": [pcbnew.ToMM(v) for v in (chosen or origin)],
            "size_mm": [pcbnew.ToMM(v) for v in size],
            "original_size_mm": [pcbnew.ToMM(old_size.x), pcbnew.ToMM(old_size.y)],
            "conservative_placement_found": chosen is not None,
            "distance_mm": math.dist(origin, chosen or origin) / 1e6,
        })
    return plan


def build(source, drc_path, output):
    # This module owns the sole wx.App. A second macOS wx.App aborts at shutdown.
    import export_kicad_design as native
    import pcbnew

    if output.exists():
        raise FileExistsError("Refusing to overwrite candidate: " + str(output))
    before = source.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    layout = json.loads((source.parent / "engineering-layout-export.json").read_text())
    if layout["metadata"]["source_board_sha256"] != source_hash:
        raise ValueError("Source layout does not match the source board")
    board = pcbnew.LoadBoard(str(source))
    plan = make_plan(board, json.loads(drc_path.read_text()), pcbnew)
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == OLD_NOTE:
            item.SetText(NEW_NOTE)
            plan.append({"uuid": item.m_Uuid.AsString(), "text": NEW_NOTE,
                         "reason": "Ballmap exists; AF22 and land qualification remain open."})
    output.mkdir(parents=True)
    scratch = output / "native-annotation-scratch.kicad_pcb"
    pcbnew.SaveBoard(str(scratch), board)
    original, proposed = annotations(before), annotations(scratch.read_text())
    allowed = [entry["uuid"] for entry in plan]
    after = replace_ranges(before, [(original[uid][0], original[uid][1],
                                     proposed[uid][2]) for uid in allowed])
    verify_scope(before, after, allowed)
    target = output / "deepreal-main-pcba-marking-candidate.kicad_pcb"
    target.write_text(after, encoding="utf-8")
    for name in (source.stem + ".kicad_pro", "fp-lib-table"):
        path = source.parent / name
        if path.exists():
            destination = (target.stem + ".kicad_pro") if name.endswith(".kicad_pro") else name
            (output / destination).write_bytes(path.read_bytes())
    result = pcbnew.LoadBoard(str(target))
    tracks, vias = native.copper(result)
    layout.update({"board": native.board_outline(result), "components": native.components(result),
                   "pads": native.pads(result), "holes": native.holes(result),
                   "tracks": tracks, "vias": vias, "zones": native.zones(result)})
    layout.setdefault("metadata", {}).update({
        "source_board": str(target), "source_board_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "design_status": "PRIVATE_ANNOTATION_ONLY_UNROUTED_DRC_UNQUALIFIED",
        "predecessor_board_sha256": source_hash,
        "release_permissions": {"manufacturing": False, "public_export": False}})
    (output / "engineering-layout-export.json").write_text(json.dumps(layout, indent=2) + "\n")
    audit = {
        "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate": str(target), "candidate_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "annotations": plan, "scope_guard_passed": True,
        "scope": "Listed annotation position/font-size, warning line wraps and obsolete U1 note.",
        "copper_placement_rules_models_unchanged": True,
        "drc_required": True, "assembly_readability_qualified": False,
        "release_permissions": {"manufacturing": False, "canonical_replacement": False,
                                "public_export": False, "deployment": False},
    }
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise ValueError("Source board changed during the build")
    (output / "marking-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"candidate": str(target), "annotations": len(plan),
                      "placement_unresolved": sum(entry.get("conservative_placement_found") is False
                                                  for entry in plan)}))
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--drc", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.source, args.drc, args.output)


if __name__ == "__main__":
    main()
