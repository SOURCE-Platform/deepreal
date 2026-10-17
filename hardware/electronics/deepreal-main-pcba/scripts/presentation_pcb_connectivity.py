"""Explicit, unverified presentation connections, never an engineering netlist.

The templates below propose local bypass/bias/filter roles from placement.
They do not establish real IC pin functions, voltages, values or feasibility.
"""

from collections import defaultdict
import copy
import heapq
import math

from demo_pcb_router import inside_polygon, simplify

GROUND = "CONCEPT_RETURN"
MAJOR = ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9",
         "U13", "U14", "U15", "U16", "U17", "U18", "U19")


def pad_key(p):
    return p["ref"], p["pad"]


def endpoint(p):
    return {k: p[k] for k in ("ref", "pad", "position")}


def source_space(geometry):
    space = CopperSpace(geometry["outlines"])
    native = geometry["native_evidence"]
    source_layers = {pad_key(p): p["layers"] for p in native["pads"]}
    for p in geometry["pads"]:
        if min(p["aabb_size"]) >= .04 or not p["pad"]:
            space.pad(p, source_layers[pad_key(p)])
    for track in native["tracks"]:
        space.line(track["layer"], track["start"], track["end"], track["width_mm"])
    for via in native["vias"]:
        space.via(via)
    return space


def retained_connections(old, geometry):
    # Retire the one-ended local details and the 81 unterminated escape stubs.
    space, result = source_space(geometry), []
    old_vias = {tuple(v["position_mm"]): v for v in old["vias"]}
    for c in old["connections"]:
        if c["purpose"] in ("illustrative local component connection", "illustrative package fan-out"):
            continue
        exempt = frozenset(pad_key(e) for e in c["endpoints"])
        vias = {tuple(p) for path in c["paths"] for p in path["points"] if tuple(p) in old_vias}
        if any(not space.clear(a, b, 1 if path["layer"] == 0 else 10, c["width_mm"]/2, exempt=exempt)
               for path in c["paths"] for a, b in zip(path["points"], path["points"][1:])):
            continue
        if any(not space.clear(p, p, layer, old_vias[p]["diameter_mm"]/2, via=True)
               for p in vias for layer in range(1, 11)):
            continue
        result.append(copy.deepcopy(c))
        for path in c["paths"]:
            for a, b in zip(path["points"], path["points"][1:]):
                space.line(1 if path["layer"] == 0 else 10, a, b, c["width_mm"])
        for p in vias:
            space.via(old_vias[p])
    return result


def connection_plan(geometry, old, displayed_refs):
    by_ref = defaultdict(dict)
    for p in geometry["pads"]:
        if p["pad"] and min(p["aabb_size"]) >= .04:
            by_ref[p["ref"]].setdefault(p["pad"], p)
    source_pads = {pad_key(p): p for p in geometry["native_evidence"]["pads"]}
    retained = retained_connections(old, geometry)
    used = {pad_key(e) for c in retained for e in c["endpoints"]}
    anchor_space = source_space(geometry)
    retained_vias = set()
    old_vias = {tuple(v["position_mm"]): v for v in old["vias"]}
    for c in retained:
        for path in c["paths"]:
            for a, b in zip(path["points"], path["points"][1:]):
                anchor_space.line(1 if path["layer"] == 0 else 10, a, b, c["width_mm"])
            retained_vias.update(tuple(p) for p in path["points"] if tuple(p) in old_vias)
    for position in retained_vias:
        anchor_space.via(old_vias[position])
    parts, roots, nets = [], [], {}

    def escapable(p):
        a = p["position"]
        return any(anchor_space.clear(a, [a[0]+dx, a[1]+dy], 1 if p["layers"][0] == 0 else 10,
                                      .06, exempt=pad_key(p))
                   for dx, dy in ((.1, 0), (-.1, 0), (0, .1), (0, -.1),
                                  (.1, .1), (.1, -.1), (-.1, .1), (-.1, -.1)))

    def take_pad(ref, purpose):
        center = geometry["centers"][ref]
        available = [p for p in by_ref[ref].values() if not p["net"] and pad_key(p) not in used and escapable(p)]
        if not available:
            raise ValueError("No unassigned presentation anchor remains on " + ref)
        # Perimeter pads are easier to escape without fabricator-specific via-in-pad.
        p = max(available, key=lambda p: math.dist(p["position"], center))
        used.add(pad_key(p))
        return {**endpoint(p), "surface_layer": p["layers"][0], "purpose": purpose}

    def root(net, ref, role):
        binding = take_pad(ref, role)
        roots.append({**binding, "net_id": net})
        nets.setdefault(net, {"id": net, "role": role, "pin_functions_verified": False})

    refs = sorted(ref for ref, pads in by_ref.items() if ref in displayed_refs
                  and len(pads) == 2 and ref.startswith(("C", "R", "L", "D")))
    proposed = [r for r in refs if not any(p["net"] for p in by_ref[r].values())]
    domains = {r: min(MAJOR, key=lambda u: math.dist(geometry["centers"][r], geometry["centers"][u]))
               for r in proposed}
    for domain in sorted(set(domains.values())):
        root("CONCEPT_SUPPLY_" + domain, domain, "proposed_local_supply")
        root(GROUND, domain, "proposed_return_interface")
    for ref in refs:
        pads = sorted(by_ref[ref].values(), key=lambda p: p["pad"])
        kind = {"C": "capacitor", "R": "resistor", "L": "inductor", "D": "diode"}[ref[0]]
        if any(p["net"] for p in pads):
            terminals = []
            for p in pads:
                native = source_pads[pad_key(p)]
                if not p["net"] or not native["connected_track_uuids"]:
                    raise ValueError("Assigned terminal has no native copper evidence: " + ref)
                terminals.append({
                    **endpoint(p), "surface_layer": p["layers"][0],
                    "mode": "engineering_reference", "native_net": native["net"],
                    "native_track_ids": native["connected_track_uuids"],
                })
            parts.append({"ref": ref, "kind": kind, "role": "existing_partial_engineering", "terminals": terminals})
            continue
        domain = domains[ref]
        supply = "CONCEPT_SUPPLY_" + domain
        if kind == "capacitor":
            terminal_nets, role = [supply, GROUND], "proposed_local_bypass"
        else:
            signal = "CONCEPT_NODE_" + ref
            # If a small IC runs out of unassigned pads, use the next nearest interface.
            targets = sorted(MAJOR, key=lambda u: math.dist(geometry["centers"][ref], geometry["centers"][u]))
            for target in targets:
                if any(not p["net"] and pad_key(p) not in used and escapable(p) for p in by_ref[target].values()):
                    root(signal, target, "proposed_unverified_protected_node" if kind == "diode"
                         else "proposed_component_interface")
                    break
            else:
                raise ValueError("No unassigned proposed interface for " + ref)
            terminal_nets = [signal, GROUND if kind == "diode" else supply]
            role = {"resistor": "proposed_bias", "inductor": "proposed_supply_filter",
                    "diode": "proposed_tvs_shunt"}[kind]
        parts.append({
            "ref": ref, "kind": kind, "role": role, "domain": domain,
            "terminals": [{
                **endpoint(p), "surface_layer": p["layers"][0], "mode": "illustrative_proposal",
                "net_id": net, "target_layer": (2 if p["layers"][0] == 0 else 9) if net == GROUND
                else (4 if p["layers"][0] == 0 else 7) if net.startswith("CONCEPT_SUPPLY_")
                else (3 if p["layers"][0] == 0 else 8),
            } for p, net in zip(pads, terminal_nets)],
        })
    return {
        "classification": "UNVERIFIED_PRESENTATION_PROPOSAL",
        "source_inventory_sha256": geometry["native_evidence"]["source_sha256"],
        "part_count": len(parts), "rc_part_count": sum(p["kind"] in ("capacitor", "resistor") for p in parts),
        "parts": parts, "roots": roots, "nets": list(nets.values()),
        "real_pin_functions_verified": False, "voltages_and_values_verified": False,
        "native_export_matches_current_geometry": False,
    }


def segment_distance(a, b, c, d):
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def distance(p, a, b):
        length = sum((b[i]-a[i])**2 for i in (0, 1))
        t = max(0, min(1, sum((p[i]-a[i])*(b[i]-a[i]) for i in (0, 1))/length)) if length else 0
        return math.dist(p, [a[i] + t*(b[i]-a[i]) for i in (0, 1)])

    if (cross(a, b, c)*cross(a, b, d) < 0 and cross(c, d, a)*cross(c, d, b) < 0):
        return 0
    return min(distance(a, c, d), distance(b, c, d), distance(c, a, b), distance(d, a, b))


def intersects_box(a, b, box):
    # Open interior: touching an inflated clearance boundary meets the minimum.
    lo, hi = 0, 1
    for i in (0, 1):
        delta = b[i] - a[i]
        if abs(delta) < 1e-12:
            if not box[i]+1e-9 < a[i] < box[i+2]-1e-9:
                return False
        else:
            x, y = (box[i]-a[i])/delta, (box[i+2]-a[i])/delta
            lo, hi = max(lo, min(x, y)), min(hi, max(x, y))
            if lo > hi:
                return False
    return hi-lo > 1e-9


class CopperSpace:
    """Spatial index of copper envelopes, using explicit layer numbers 1..10."""

    def __init__(self, outlines, clearance=.045):
        self.outlines, self.clearance = outlines, clearance
        self.buckets = defaultdict(list)
        self.items = []

    def inside(self, p, radius=0):
        return all(sum(inside_polygon([p[0]+dx, p[1]+dy], loop) for loop in self.outlines) % 2
                   for dx, dy in ((-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius)))

    def add(self, layers, item, box):
        index = len(self.items)
        self.items.append(item)
        for layer in layers:
            for x in range(math.floor(box[0]), math.floor(box[2])+1):
                for y in range(math.floor(box[1]), math.floor(box[3])+1):
                    self.buckets[layer, x, y].append(index)

    def pad(self, p, layers):
        box = [p["position"][i] - p["aabb_size"][i]/2 for i in (0, 1)]
        box += [p["position"][i] + p["aabb_size"][i]/2 for i in (0, 1)]
        self.add(layers, {"box": box, "pad": pad_key(p), "net": None}, box)

    def line(self, layer, a, b, width, net=None):
        r = width/2
        box = [min(a[i], b[i])-r for i in (0, 1)] + [max(a[i], b[i])+r for i in (0, 1)]
        self.add([layer], {"a": a, "b": b, "radius": r, "net": net}, box)

    def via(self, via, net=None):
        p, r = via["position_mm"], via["diameter_mm"]/2
        self.add(range(1, 11), {"a": p, "b": p, "radius": r, "net": net},
                 [p[0]-r, p[1]-r, p[0]+r, p[1]+r])

    def clear(self, a, b, layer, radius, net=None, exempt=None, via=False):
        reach = radius + self.clearance
        box = [min(a[i], b[i])-reach for i in (0, 1)] + [max(a[i], b[i])+reach for i in (0, 1)]
        seen = set()
        for x in range(math.floor(box[0]), math.floor(box[2])+1):
            for y in range(math.floor(box[1]), math.floor(box[3])+1):
                for index in self.buckets.get((layer, x, y), ()):
                    if index in seen:
                        continue
                    seen.add(index)
                    item = self.items[index]
                    if "pad" in item:
                        if (item["pad"] == exempt or isinstance(exempt, frozenset) and item["pad"] in exempt) and not via:
                            continue
                        bounds = item["box"]
                        if intersects_box(a, b, [bounds[0]-reach, bounds[1]-reach,
                                                 bounds[2]+reach, bounds[3]+reach]):
                            return False
                    elif net is not None and item["net"] == net and not via:
                        continue
                    elif segment_distance(a, b, item["a"], item["b"]) < reach + item["radius"] - 1e-8:
                        return False
        return True


class ConnectionRouter:
    def __init__(self, geometry, old, plan):
        self.geometry, self.plan = geometry, plan
        self.connections = retained_connections(old, geometry)
        self.space = source_space(geometry)
        self.vias = []
        old_vias = {tuple(v["position_mm"]): v for v in old["vias"]}
        via_nets = {}
        for c in self.connections:
            c["net_id"] = "CONCEPT_BUS_" + c["id"]
            for path in c["paths"]:
                for a, b in zip(path["points"], path["points"][1:]):
                    self.space.line(1 if path["layer"] == 0 else 10, a, b, c["width_mm"], c["net_id"])
                for p in path["points"]:
                    if tuple(p) in old_vias:
                        other = via_nets.setdefault(tuple(p), c["net_id"])
                        if other != c["net_id"]:
                            raise ValueError("Old via joins unrelated illustrative connections")
        for p, net in sorted(via_nets.items()):
            self.add_via(p, net, [1, 10], old_vias[p]["diameter_mm"], old_vias[p]["drill_mm"])
        self.inner_paths = []
        self.next_connection = max(int(c["id"][5:]) for c in old["connections"]) + 1

    def add_via(self, p, net, taps, diameter=.30, drill=.15):
        via = {
            "id": f"PV_{len(self.vias)+1:04d}", "position_mm": list(p),
            "diameter_mm": diameter, "drill_mm": drill, "net_id": net,
            "span": [1, 10], "taps": sorted(set(taps)), "type": "proposed_through",
        }
        self.vias.append(via)
        self.space.via(via, net)
        return via

    def escape(self, terminal, taps):
        start, surface, net = terminal["position"], terminal["surface_layer"], terminal["net_id"]
        layer, width = (1 if surface == 0 else 10), (.24 if terminal["ref"].startswith("L") else .12)
        # Fine, local search. All edges, not only sampled vertices, are checked.
        step = .10
        center = self.geometry["centers"][terminal["ref"]]
        direction = [start[i]-center[i] for i in (0, 1)]
        length = math.hypot(*direction)
        direction = [v/length for v in direction] if length else [1, 0]
        scores, previous, queue = {(0, 0): 0}, {}, [(0, (0, 0))]
        found = None

        def point(cell):
            return [round(start[i]+cell[i]*step, 6) for i in (0, 1)]

        while queue:
            score, cell = heapq.heappop(queue)
            if score != scores.get(cell):
                continue
            p = point(cell)
            distance = math.dist(p, start)
            if distance >= .45 and self.space.inside(p, .20) and all(
                    self.space.clear(p, p, l, .15, via=True) for l in range(1, 11)):
                found = cell
                break
            if distance > 3.8:
                continue
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                other = cell[0]+dx, cell[1]+dy
                q = point(other)
                if not self.space.inside(q, width/2+.06) or not self.space.clear(
                        p, q, layer, width/2, net, pad_key(terminal)):
                    continue
                cost = math.hypot(dx, dy) + .18*(1-(dx*direction[0]+dy*direction[1])/math.hypot(dx, dy))
                candidate = score + cost
                if candidate < scores.get(other, math.inf):
                    scores[other], previous[other] = candidate, cell
                    heapq.heappush(queue, (candidate, other))
        if found is None:
            raise ValueError("No clear outer escape for " + str(pad_key(terminal)))
        cells = [found]
        while cells[-1] in previous:
            cells.append(previous[cells[-1]])
        points = simplify([point(c) for c in reversed(cells)])
        via = self.add_via(points[-1], net, [layer] + taps)
        connection = {
            "id": f"DEMO_{self.next_connection:04d}", "purpose": "proposed terminal-to-layer connection",
            "net_id": net, "width_mm": width,
            "endpoints": [endpoint(terminal), {"ref": "VISUAL_VIA", "pad": via["id"], "position": points[-1]}],
            "paths": [{"layer": surface, "points": points}],
        }
        self.next_connection += 1
        self.connections.append(connection)
        for a, b in zip(points, points[1:]):
            self.space.line(layer, a, b, width, net)
        terminal["connection_id"], terminal["via_id"] = connection["id"], via["id"]
        return via

    def inner_route(self, first, last, layer, net):
        start, end, step = first["position_mm"], last["position_mm"], .20
        origin = [20, 20]

        def cell(p):
            return tuple(round((p[i]-origin[i])/step) for i in (0, 1))

        def point(c):
            return [round(origin[i]+c[i]*step, 6) for i in (0, 1)]

        def attachments(p):
            center = cell(p)
            return {c for dx in range(-2, 3) for dy in range(-2, 3)
                    for c in [(center[0]+dx, center[1]+dy)]
                    if self.space.inside(point(c), .15) and self.space.clear(p, point(c), layer, .08, net)}

        starts, goals = attachments(start), attachments(end)
        if not starts or not goals:
            raise ValueError("Inner endpoint cannot reach grid: " + first["id"])
        scores = {c: math.dist(start, point(c))/step for c in starts}
        previous, queue = {}, [(score+math.dist(point(c), end)/step, c) for c, score in scores.items()]
        heapq.heapify(queue)
        found = None
        while queue:
            _, current = heapq.heappop(queue)
            if current in goals:
                found = current
                break
            p = point(current)
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                other = current[0]+dx, current[1]+dy
                q = point(other)
                if not self.space.inside(q, .15) or not self.space.clear(p, q, layer, .08, net):
                    continue
                score = scores[current] + math.hypot(dx, dy)
                if score < scores.get(other, math.inf):
                    scores[other], previous[other] = score, current
                    h = math.dist(q, end)/step
                    heapq.heappush(queue, (score+h, other))
        if found is None:
            raise ValueError(f"No inner route on layer {layer} for {net}: {first['id']} -> {last['id']}")
        cells = [found]
        while cells[-1] in previous:
            cells.append(previous[cells[-1]])
        points = [start] + [point(c) for c in reversed(cells)] + [end]
        points = simplify([p for i, p in enumerate(points) if not i or p != points[i-1]])
        if len(points) < 2:
            raise ValueError("Empty inner connection")
        path = {
            "id": f"IP_{len(self.inner_paths)+1:04d}", "net_id": net, "layer": layer,
            "width_mm": .16, "points": points, "from_via": first["id"], "to_via": last["id"],
        }
        self.inner_paths.append(path)
        for a, b in zip(points, points[1:]):
            self.space.line(layer, a, b, .16, net)
        first["taps"] = sorted(set(first["taps"] + [layer]))
        last["taps"] = sorted(set(last["taps"] + [layer]))
        return path

    def run(self, progress=print):
        proposed = [t for p in self.plan["parts"] for t in p["terminals"] if t["mode"] == "illustrative_proposal"]
        all_terminals = proposed + self.plan["roots"]
        # Dense underside/edge contacts first; routing remains deterministic.
        all_terminals.sort(key=lambda t: (
            1 if t["ref"].startswith(("C", "R", "L", "D")) else 0,
            math.dist(t["position"], [65, 33]), t["ref"], t["pad"]))
        vias_by_terminal = {}
        for i, terminal in enumerate(all_terminals):
            if "target_layer" in terminal:
                taps = [terminal["target_layer"]]
            elif terminal["net_id"] == GROUND:
                taps = [2, 9]
            else:
                taps = []  # Inner routing records only the layers actually reached.
            vias_by_terminal[pad_key(terminal)] = self.escape(terminal, taps)
            if i % 25 == 0:
                progress(f"Outer escapes {i+1}/{len(all_terminals)}")
        roots = defaultdict(list)
        for terminal in self.plan["roots"]:
            roots[terminal["net_id"]].append(vias_by_terminal[pad_key(terminal)])
        groups = defaultdict(list)
        for terminal in proposed:
            if terminal["net_id"] != GROUND:
                groups[terminal["net_id"], terminal["target_layer"]].append(vias_by_terminal[pad_key(terminal)])
        for i, ((net, layer), members) in enumerate(sorted(groups.items())):
            tree = list(roots[net])
            if len(tree) != 1:
                raise ValueError("Inner net must have one declared interface root: " + net)
            while members:
                _, member, target = min((math.dist(m["position_mm"], t["position_mm"]), mi, ti)
                                        for mi, m in enumerate(members) for ti, t in enumerate(tree))
                node = members.pop(member)
                self.inner_route(node, tree[target], layer, net)
                tree.append(node)
            progress(f"Inner network {i+1}/{len(groups)}: {net}, layer {layer}")
        return self
