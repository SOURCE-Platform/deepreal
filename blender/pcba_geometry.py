"""Dimensioned two-sided population for the Main PCBA packaging study."""

import math
import os

import bpy
from mathutils import Matrix, Vector

from assembly_primitives import MM, box, cylinder, material, tag, tube
from pcba_bom import ALL_PARTS, BOARD, PLANNING_ZONES
EVIDENCE_SUPPORT = "REPRESENTATIVE SUPPORT POPULATION - SCHEMATIC NOT FROZEN"

def _materials():
    return {
        "package": material("PCBA_Package_Mold", (0.010, 0.012, 0.015),
                            roughness=0.32),
        "compute": material("PCBA_Compute_Package", (0.014, 0.017, 0.022),
                            metallic=0.08, roughness=0.30),
        "power": material("PCBA_Power_Package", (0.018, 0.020, 0.024),
                          roughness=0.36),
        "connector": material("PCBA_Connector_Housing", (0.34, 0.36, 0.38),
                              metallic=0.62, roughness=0.29),
        "latch": material("PCBA_FPC_Latch", (0.16, 0.17, 0.16),
                          roughness=0.39),
        "copper": material("PCBA_Pads_Copper", (0.78, 0.52, 0.12),
                           metallic=0.96, roughness=0.20),
        "ceramic": material("PCBA_Ceramic", (0.48, 0.42, 0.31),
                            roughness=0.58),
        "resistor": material("PCBA_Resistor", (0.025, 0.023, 0.021),
                             roughness=0.45),
        "inductor": material("PCBA_Power_Inductor", (0.17, 0.18, 0.19),
                             metallic=0.22, roughness=0.48),
        "bulk": material("PCBA_Bulk_Capacitor", (0.045, 0.047, 0.052),
                          metallic=0.30, roughness=0.37),
        "silk": material("PCBA_Silkscreen", (0.86, 0.88, 0.82),
                         roughness=0.61),
        "zone": material("PCBA_Planning_Zone", (0.94, 0.56, 0.05),
                         roughness=0.45, alpha=0.09),
    }

def _side_y(side, height):
    half = BOARD["thickness"] / 2.0
    direction = -1.0 if side == "TOP" else 1.0
    return BOARD["center_y"] + direction * (half + height / 2.0)
def _surface_y(side, offset=0.0):
    half = BOARD["thickness"] / 2.0
    direction = -1.0 if side == "TOP" else 1.0
    return BOARD["center_y"] + direction * (half + offset)
def _tag_part(obj, part):
    tag(obj, part["subsystem"], part["status"])
    obj["PCBA_Component"] = True
    for key in ("ref", "manufacturer", "part_number", "package", "side",
                "status", "source", "step_source"):
        obj["PCBA_" + key.title().replace("_", "")] = part[key]
    obj["PCBA_Body_mm"] = "{:.3f} x {:.3f} x {:.3f}".format(
        part["width"], part["depth"], part["height"])
    return obj
def _compound_boxes(name, specs, mat, collection):
    vertices, faces = [], []
    for cx, cy, cz, dx, dy, dz in specs:
        base = len(vertices)
        for sx, sy, sz in ((-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
                           (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)):
            vertices.append(((cx + sx*dx/2)*MM, (cy + sy*dy/2)*MM,
                             (cz + sz*dz/2)*MM))
        faces.extend(tuple(base + i for i in face) for face in (
            (0,1,2,3), (4,7,6,5), (0,4,5,1),
            (1,5,6,2), (2,6,7,3), (4,0,3,7)))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj
def _pad_array(part, rows, columns, pitch, mats, collection):
    y = _surface_y(part["side"], 0.035)
    sign = -1.0 if part["side"] == "TOP" else 1.0
    y += sign * 0.035
    specs = []
    for row in range(rows):
        z = part["z"] + (row - (rows - 1) / 2.0) * pitch
        for column in range(columns):
            x = part["x"] + (column - (columns - 1) / 2.0) * pitch
            specs.append((x, y, z, pitch * 0.48, 0.07, pitch * 0.48))
    obj = _compound_boxes(part["name"] + "_BGA_Pad_Field", specs,
                          mats["copper"], collection)
    return tag(obj, part["subsystem"], "FOOTPRINT PATTERN - PACKAGE FAMILY")
def _qfn_pads(part, mats, collection):
    y = _surface_y(part["side"], 0.04)
    specs = []
    count_x = max(2, int(part["width"] / 0.7))
    count_z = max(2, int(part["depth"] / 0.7))
    for index in range(count_x):
        x = part["x"] + (index - (count_x - 1) / 2.0) * 0.65
        for z in (part["z"] - part["depth"] / 2.0 - 0.18,
                  part["z"] + part["depth"] / 2.0 + 0.18):
            specs.append((x, y, z, 0.34, 0.08, 0.70))
    for index in range(count_z):
        z = part["z"] + (index - (count_z - 1) / 2.0) * 0.65
        for x in (part["x"] - part["width"] / 2.0 - 0.18,
                  part["x"] + part["width"] / 2.0 + 0.18):
            specs.append((x, y, z, 0.70, 0.08, 0.34))
    return _compound_boxes(part["name"] + "_Land_Pattern", specs,
                           mats["copper"], collection)


def _silk(ref, x, z, side, mats, collection, size=0.85, offset=.05):
    curve = bpy.data.curves.new("Silk_" + ref, "FONT")
    curve.body = ref
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size * MM
    curve.extrude = 0.018 * MM
    curve.materials.append(mats["silk"])
    obj = bpy.data.objects.new("Silkscreen_" + ref, curve)
    obj.location = (x * MM, _surface_y(side, offset) * MM, z * MM)
    obj.rotation_euler.x = math.radians(90.0 if side == "TOP" else -90.0)
    collection.objects.link(obj)
    return tag(obj, "PCBA identification", "PRELIMINARY REFERENCE DESIGNATOR")


def _manufacturer_usb(part, mats, collection):
    path = os.path.join(os.path.dirname(__file__), "vendor_cad", "hirose",
                        "CX90M3-24P_4800919000_STEP.stl")
    if not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    imported = list(set(bpy.data.objects) - before)
    if not imported:
        return None
    obj = imported[0]
    obj.name = part["name"]
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    # STL is unitless. Bake the STEP millimetres and axis permutation into
    # mesh coordinates so later parenting cannot discard the import scale.
    for vertex in obj.data.vertices:
        source = vertex.co.copy()
        vertex.co = Vector((source.y*MM, source.z*MM, source.x*MM))
    obj.matrix_world = Matrix.Identity(4)
    obj.data.update()
    lows = Vector(tuple(min(vertex.co[i] for vertex in obj.data.vertices)
                          for i in range(3)))
    highs = Vector(tuple(max(vertex.co[i] for vertex in obj.data.vertices)
                           for i in range(3)))
    center = (lows + highs) / 2.0
    target = Vector((part["x"]*MM, _side_y("TOP", part["height"])*MM,
                     part["z"]*MM))
    for vertex in obj.data.vertices:
        vertex.co += target - center
    obj.data.materials.append(mats["connector"])
    obj["PCBA_Geometry"] = "MANUFACTURER STEP CONVERTED TO STL"
    return _tag_part(obj, part)


def _fpc_details(part, mats, collection):
    objects = []
    side = part["side"]
    direction = -1.0 if side == "TOP" else 1.0
    latch = box(part["name"] + "_Latch",
                (part["x"], _side_y(side, part["height"] + 0.20),
                 part["z"] - 0.65),
                (part["width"] - 0.8, 0.20, 0.65), 0.08,
                mats["latch"], collection)
    objects.append(tag(latch, part["subsystem"], "CONNECTOR LATCH ENVELOPE"))
    y = _surface_y(side, 0.045) + direction * 0.045
    contacts = []
    count = 51 if "51-position" in part["package"] else 22
    pitch = 0.3 if count == 51 else 0.5
    for index in range(count):
        x = part["x"] + (index - (count - 1) / 2.0) * pitch
        contacts.append((x, y, part["z"] + 1.0,
                         pitch * 0.48, 0.09, 0.75))
    pads = _compound_boxes(part["name"] + "_{}_Pin_Lands".format(count), contacts,
                           mats["copper"], collection)
    objects.append(tag(pads, part["subsystem"],
                       "{}-POSITION LAND PATTERN".format(count)))
    return objects


def _major_population(mats, collection):
    objects = []
    bga_grids = {
        "NXP_iMX95": (27, 27, 0.50),
        "Face_CrossLink_NX": (11, 11, 0.50),
        "Interaction_CrossLink_NX": (11, 11, 0.50),
        "LPDDR4X_4GB": (20, 10, 0.50),
        "eMMC_32GB": (17, 9, 0.65),
    }
    for part in ALL_PARTS:
        if part["name"] == "USB_C_Receptacle":
            body = _manufacturer_usb(part, mats, collection)
        else:
            body = None
        if body is None:
            mat = mats["connector"] if part["ref"].startswith("J") \
                else mats["power"] if "Power" in part["subsystem"] \
                or "USB" in part["subsystem"] else mats["compute"] \
                if part["name"] in {"NXP_iMX95", "Face_CrossLink_NX",
                                    "Interaction_CrossLink_NX"} \
                else mats["package"]
            body = box(part["name"],
                       (part["x"], _side_y(part["side"], part["height"]),
                        part["z"]),
                       (part["width"], part["height"], part["depth"]),
                       min(0.35, part["height"] / 3.0), mat, collection)
            _tag_part(body, part)
            body["PCBA_Geometry"] = "DIMENSIONED PARAMETRIC ENVELOPE"
        objects.append(body)
        if part["ref"] in {"U1", "U2", "U3", "U4", "U5", "U15"}:
            marking = part["ref"] + "  " + part["manufacturer"]
            objects.append(_silk(marking, part["x"], part["z"], part["side"],
                                 mats, collection, .72, part["height"] + .04))
        if part["name"] in bga_grids:
            objects.append(_pad_array(part, *bga_grids[part["name"]],
                                      mats, collection))
        elif not part["ref"].startswith("J"):
            objects.append(_qfn_pads(part, mats, collection))
        if "Optical_Head_Connector" in part["name"]:
            objects += _fpc_details(part, mats, collection)
        objects.append(_silk(part["ref"], part["x"],
                             part["z"] + part["depth"]/2 + 0.75,
                             part["side"], mats, collection))
    return objects
def _blocked(x, z, side, occupied):
    if abs(x) > 41.0 or z < -20.8 or z > -1.4:
        return True
    if any((x-hx)**2 + (z-hz)**2 < 2.35**2
           for hx, hz in ((-42,-22.5),(-42,-.5),(42,-22.5),(42,-.5))):
        return True
    return any(item[0] == side and abs(x-item[1]) < item[3]/2 + 0.55
               and abs(z-item[2]) < item[4]/2 + 0.55 for item in occupied)


def _representative_support(mats, collection):
    objects, pad_specs = [], []
    inductors = (("L1",28.0,-11.0,3.2,3.2), ("L2",18.0,-18.0,3.2,3.2),
                 ("L3",21.0,-2.5,3.0,3.0), ("L4",21.0,-8.0,3.0,3.0),
                 ("L5",19.0,-12.5,2.0,2.0), ("L6",22.0,-5.0,2.0,2.0),
                 ("L7",19.0,-15.0,2.0,2.0))
    bulk_caps = ((-36,-17),(-28,-19),(28,-19),(36,-22))
    occupied = [(p["side"], p["x"], p["z"], p["width"], p["depth"])
                for p in ALL_PARTS]
    occupied += [("TOP", x, z, width, depth)
                 for _, x, z, width, depth in inductors]
    occupied += [("BOTTOM", x, z, 3.2, 2.5) for x, z in bulk_caps]
    zones = (
        ("CPU", "TOP", -15, 3, -18, 1, 36),
        ("FACE", "TOP", -39, -19, -20, -5, 20),
        ("DDR", "TOP", 3, 14, -17, 1, 18),
        ("PWR", "TOP", 14, 31, -18, 1, 28),
        ("USB", "TOP", 31, 40, -21, 1, 14),
        ("AUX", "BOTTOM", -40, 40, -21, 0, 44),
    )
    ref_index = 1
    for prefix, side, x0, x1, z0, z1, target in zones:
        placed = 0
        z = z0 + 0.7
        while z < z1 and placed < target:
            x = x0 + 0.7
            while x < x1 and placed < target:
                if not _blocked(x, z, side, occupied):
                    is_cap = (ref_index % 3) != 0
                    width, depth = ((0.80, 0.42) if is_cap else (1.00, 0.50))
                    height = 0.38
                    name = ("C" if is_cap else "R") + \
                        "_{:03d}_{}_Representative".format(ref_index, prefix)
                    body = box(name, (x, _side_y(side, height), z),
                               (width, height, depth), 0.08,
                               mats["ceramic" if is_cap else "resistor"],
                               collection)
                    body["PCBA_Component"] = True
                    body["PCBA_Side"] = side
                    body["PCBA_Status"] = "RESERVED"
                    objects.append(tag(body, prefix + " support", EVIDENCE_SUPPORT))
                    y = _surface_y(side, 0.035)
                    pad_specs.extend(((x-width*.55, y, z, width*.55, .07, depth*1.25),
                                      (x+width*.55, y, z, width*.55, .07, depth*1.25)))
                    occupied.append((side, x, z, width, depth))
                    placed += 1
                    ref_index += 1
                x += 1.18
            z += 1.12

    pads = _compound_boxes("Representative_Support_Land_Patterns", pad_specs,
                           mats["copper"], collection)
    objects.append(tag(pads, "Support footprints", EVIDENCE_SUPPORT))

    for ref, x, z, width, depth in inductors:
        obj = box(ref + "_Power_Inductor", (x, _side_y("TOP", 2.0), z),
                  (width, 2.0, depth), 0.35, mats["inductor"], collection)
        obj["PCBA_Component"] = True
        obj["PCBA_Side"] = "TOP"
        obj["PCBA_Status"] = "RESERVED"
        objects.append(tag(obj, "Power magnetics", EVIDENCE_SUPPORT))
        objects.append(_silk(ref, x, z + depth/2 + .6,
                             "TOP", mats, collection, .72))

    for index, (x, z) in enumerate(bulk_caps, 1):
        obj = box("Bulk_Capacitor_Reserved_{:02d}".format(index),
                  (x, _side_y("BOTTOM", 1.2), z), (3.2, 1.2, 2.5),
                  0.25, mats["bulk"], collection)
        obj["PCBA_Component"] = True
        obj["PCBA_Side"] = "BOTTOM"
        obj["PCBA_Status"] = "RESERVED"
        objects.append(tag(obj, "Motor/emitter bulk energy", EVIDENCE_SUPPORT))
    return objects


def _vias_and_zones(mats, collection):
    objects = []
    for index, x in enumerate(range(-38, 39, 4), 1):
        for z in (-19.8, 0.8):
            via = tube("PCBA_Ground_Via_{:02d}_{}".format(index, "B" if z < 0 else "T"),
                       (x, BOARD["center_y"], z), Vector((0,1,0)),
                       0.18, 0.34, BOARD["thickness"] + 0.08,
                       mats["copper"], collection, segments=16)
            objects.append(tag(via, "Ground stitching", "REPRESENTATIVE VIA FIELD"))
    for name, x, z, width, depth, side in PLANNING_ZONES:
        zone = box(name, (x, _surface_y(side, 0.02), z),
                   (width, 0.04, depth), 0.15, mats["zone"], collection)
        zone.display_type = "WIRE"
        zone.hide_render = True
        objects.append(tag(zone, "Engineering reservation", "PLANNING ZONE"))
    return objects


def build(collection):
    mats = _materials()
    objects = _major_population(mats, collection)
    objects += _representative_support(mats, collection)
    objects += _vias_and_zones(mats, collection)

    lever = box("Tamper_Enclosure_Actuator_Interface",
                (0.0, 13.45, -23.0), (0.55, 2.4, 0.55), 0.10,
                mats["connector"], collection)
    lever["Mechanical_Contact"] = "Must close against shield/lid feature"
    objects.append(tag(lever, "Tamper detection", "PROVISIONAL MECHANICAL LINK"))

    keepout = cylinder("Microphone_Acoustic_Keepout", (9.0, 17.8, -20.0),
                       Vector((0,1,0)), 2.4, 1.3, mats["zone"], collection,
                       segments=32)
    keepout.display_type = "WIRE"
    keepout.hide_render = True
    objects.append(tag(keepout, "Audio", "ACOUSTIC KEEP-OUT"))
    return objects
