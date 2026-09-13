"""Import native KiCad geometry; preserve defects and label missing models.

This is a review transport, not an electrical or package audit. Envelopes for
missing 3D models are explicitly representative and contain no invented pads.
"""

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from assembly_primitives import link_only, material
from pcba_bom import ALL_PARTS, BOARD
from pcba_kicad_data import DEFAULT_EXPORT, load

ROOT = Path(DEFAULT_EXPORT).parent
DIRECTORY = ROOT / "generated-review"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_inputs():
    data = load()
    manifest = json.loads((DIRECTORY / "native-review-manifest.json").read_text())
    checks = ((ROOT / data["metadata"]["source_board"], "source_board_sha256"),
              (Path(DEFAULT_EXPORT), "source_export_sha256"),
              (DIRECTORY / manifest["glb"], "glb_sha256"))
    for path, key in checks:
        if digest(path) != manifest[key]:
            raise ValueError("stale native review geometry: " + str(path))
    if digest(ROOT / "design-status.json") != data["metadata"]["source_status_sha256"]:
        raise ValueError("stale design status: regenerate the KiCad export")
    for model in manifest.get("model_sources", []):
        path = Path(model["resolved"])
        current = digest(path) if path.is_file() else None
        if current != model["sha256"]:
            raise ValueError("changed model library: regenerate native export: " + str(path))
    return data, manifest


def _owner(obj, refs):
    while obj:
        if obj.name in refs:
            return obj.name
        obj = obj.parent
    return None


def _join(objects):
    if len(objects) == 1:
        return objects[0]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    return objects[0]


def _envelope(item, part, origin, top_seat, collection):
    """Selected-package body only; not a footprint substitute or pin mapping."""
    x, y = item["position_mm"]
    height = part["height"] * .001
    top = item["side"] == "TOP"
    z = top_seat + height/2 if top else -.000085-height/2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(
        (x-origin[0])*.001, (origin[1]-y)*.001, z))
    obj = bpy.context.object
    obj.dimensions = (part["width"]*.001, part["depth"]*.001, height)
    obj.rotation_euler.z = math.radians(item["rotation_deg"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material("PCBA_Representative_Envelope",
        (.12, .15, .20), roughness=.6))
    link_only(obj, collection)
    obj["PCBA_ModelStatus"] = "REPRESENTATIVE_ENVELOPE_MISSING_KICAD_MODEL"
    obj["PCBA_EnvelopeSource"] = part["source"]
    return obj


def build(collection):
    data, manifest = checked_inputs()
    refs = {c["ref"]: c for c in data["components"]}
    metadata = {c["ref"]: c for c in ALL_PARTS}
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(DIRECTORY / manifest["glb"]))
    imported = sorted(set(bpy.data.objects) - before, key=lambda obj: obj.name)
    empties = [o for o in imported if o.type == "EMPTY"]
    groups, surfaces = {}, []
    anchors = {}
    for obj in imported:
        if obj.name in refs:
            anchors[obj.name] = obj.matrix_world.copy()
        if obj.type == "MESH":
            ref = _owner(obj, refs)
            if ref:
                groups.setdefault(ref, []).append(obj)
            else:
                surfaces.append(obj)
    if set(groups) != set(manifest["native_model_refs"]):
        raise ValueError("native component meshes disagree with export inventory")
    # glTF import gives Blender X/Y plane, Z up, units metres. Match the
    # device's X/Z board plane, with top components facing negative Y.
    substrates = [o for o in surfaces if o.data.name.endswith("_PCB")]
    if len(substrates) != 1:
        raise ValueError("native board substrate must be unambiguous")
    substrate = substrates[0]
    corners = [substrate.matrix_world @ Vector(v) for v in substrate.bound_box]
    low, high = min(v.z for v in corners), max(v.z for v in corners)
    transform = Matrix.Translation((0, BOARD["center_y"]*.001+(high+low)/2,
                                    BOARD["center_z"]*.001)) @ Matrix.Rotation(math.pi/2, 4, "X")
    objects = []
    for ref, meshes in sorted(groups.items()):
        obj = _join(meshes)
        obj["PCBA_ModelStatus"] = "NATIVE_MODEL_UNVERIFIED_FOOTPRINT"
        objects.append((ref, obj))
    for ref in manifest["missing_model_refs"]:
        if ref not in metadata:
            raise ValueError("missing model has no documented envelope: " + ref)
        obj = _envelope(refs[ref], metadata[ref], manifest["origin_mm"],
                        high+.000085, collection)
        anchors[ref] = obj.matrix_world.copy()
        # A footprint anchor is at the board surface, not at the body's centre.
        anchors[ref].translation.z = high+.000085 if refs[ref]["side"] == "TOP" else -.000085
        objects.append((ref, obj))
    max_anchor_error = 0.0
    for ref, obj in objects:
        item = refs[ref]
        expected = Vector(((item["position_mm"][0]-manifest["origin_mm"][0])*.001,
                           (manifest["origin_mm"][1]-item["position_mm"][1])*.001))
        actual = anchors[ref].translation
        error = (Vector((actual.x, actual.y))-expected).length*1000
        max_anchor_error = max(max_anchor_error, error)
        if error > .1:
            raise ValueError("native placement disagreement: " + ref)
        obj.name = metadata.get(ref, {}).get("name", "PCBA_"+ref)
        obj["PCBA_Component"] = True
        obj["PCBA_Ref"] = ref
        obj["PCBA_Side"] = item["side"]
        obj["PCBA_Footprint"] = item["footprint"]
        obj["PCBA_Value"] = item["value"]
        obj["PCBA_UUID"] = item["uuid"]
        obj["PCBA_RotationDeg"] = item["rotation_deg"]
        obj["PCBA_Anchor_mm"] = list(transform @ anchors[ref].translation * 1000)
    all_meshes = [o for _, o in objects]+surfaces
    for index, obj in enumerate(surfaces):
        obj.name = "Main_PCBA" if obj == substrate else "PCBA_Native_Surface_{:02d}".format(index)
        obj["PCBA_NativeSurface"] = True
        # Native GLB gives the substrate alpha .98. In EEVEE its transparent
        # rear face can composite over the front mask/pads. A real opaque
        # substrate and silkscreen must not use that transparency shortcut.
        for mat in obj.data.materials:
            mat.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value = 1
        if "soldermask" in obj.data.name:
            for mat in obj.data.materials:
                shader = mat.node_tree.nodes.get("Principled BSDF")
                shader.inputs["Base Color"].default_value = (.008, .075, .022, 1)
                shader.inputs["Alpha"].default_value = 1
                shader.inputs["Roughness"].default_value = .5
    for obj in all_meshes:
        matrix = transform @ obj.matrix_world
        obj.parent = None
        obj.data = obj.data.copy()
        obj.data.transform(matrix)
        obj.matrix_world = Matrix.Identity(4)
        link_only(obj, collection)
        obj["PCBA_SourceBoardHash"] = manifest["source_board_sha256"]
        obj["PCBA_PublicAllowed"] = False
    for obj in empties:
        bpy.data.objects.remove(obj, do_unlink=True)
    substrate["PCBA_ImportReport"] = json.dumps({
        "native_model_count": len(groups), "envelope_refs": manifest["missing_model_refs"],
        "pad_or_hole_only_refs": manifest["pad_or_hole_only_refs"],
        "component_count": len(objects), "max_anchor_error_mm": max_anchor_error,
        "tracks": len(data["tracks"]), "vias": len(data["vias"]),
        "nominal_board_thickness_mm": data["board"]["thickness_mm"],
        "native_substrate_thickness_mm": (high-low)*1000,
        "engineering_status": "BLOCKED", "public_visual_allowed": False})
    # Existing flex-study presentation uses this material, not its geometry.
    material("PCBA_Connector_Housing", (.15, .16, .18), roughness=.5)
    print("NATIVE PCBA IMPORT", substrate["PCBA_ImportReport"])
    return all_meshes
