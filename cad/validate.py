#!/usr/bin/env python3
"""
Phase 1 + Phase 2 + Phase 2.5 + Phase 3 validation.

Rebuilds the geometry in memory with perturbed parameters and checks that
the resulting bounding boxes respond correctly, then reopens the saved
deepreal.FCStd and verifies its structure and injected view state.

Coordinate convention under test: -Y = FRONT/USER side (screen/pixels,
seated user, sensor heads); +Y = REAR/MOUNT side (back of lid; rear arm
integrated into the housing as one extruded side profile, forming the
laptop-lid pocket; future magnetic mount).

Run headless from the repository root (after cad/build.py):

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd cad/validate.py

Exits non-zero if any check fails.

Note: freecadcmd executes this file with __name__ set to the module name,
not "__main__", so main() is invoked unconditionally at import time. Do not
import this module.
"""

import importlib
import math
import os
import shutil
import sys
import tempfile
import time
import zipfile

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
    if not os.path.exists(os.path.join(HERE, "parameters.py")):
        HERE = os.path.join(HERE, "cad")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import document  # noqa: E402
import parameters  # noqa: E402
import parts  # noqa: E402
import sensor_heads  # noqa: E402

FAILURES = []

HOUSING = parts.MAIN_HOUSING_NAME
DISPLAY = parts.DISPLAY_REFERENCE_NAME
FACE = sensor_heads.FACE_HEAD_NAME
INTERACTION = sensor_heads.INTERACTION_HEAD_NAME
FACE_MARK = sensor_heads.FACE_ORIENTATION_NAME
INTERACTION_MARK = sensor_heads.INTERACTION_ORIENTATION_NAME


def check(label, actual, expected, tol=1e-6):
    ok = abs(actual - expected) <= tol
    print("[{}] {}: expected {}, got {}".format(
        "PASS" if ok else "FAIL", label, expected, actual))
    if not ok:
        FAILURES.append(label)


def check_true(label, condition):
    print("[{}] {}".format("PASS" if condition else "FAIL", label))
    if not condition:
        FAILURES.append(label)


def extents(obj):
    bb = obj.Shape.BoundBox
    return bb.XLength, bb.YLength, bb.ZLength


def axis_center_y(obj):
    bb = obj.Shape.BoundBox
    return (bb.YMin + bb.YMax) / 2.0


def axis_center_z(obj):
    bb = obj.Shape.BoundBox
    return (bb.ZMin + bb.ZMax) / 2.0


def build_with(**overrides):
    params = parameters.get_params()
    params.update(overrides)
    doc = document.build_document(params)
    objects = {obj.Name: obj for obj in doc.Objects}
    return doc, objects


def cylinder_axis_along_x(obj):
    """True if the solid has a cylindrical face whose axis is parallel to X."""
    x_axis = App.Vector(1, 0, 0)
    for face in obj.Shape.Faces:
        surface = face.Surface
        if surface.TypeId == "Part::GeomCylinder":
            if abs(abs(surface.Axis * x_axis) - 1.0) < 1e-9:
                return True
    return False


def slab_bb(shape_obj, z_low, z_high):
    """Bounding box of an object's material between two Z heights."""
    probe = Part.makeBox(400.0, 400.0, z_high - z_low,
                         App.Vector(-200.0, -200.0, z_low))
    return shape_obj.Shape.common(probe).BoundBox


def planar_mount_faces(arm_obj, face_y):
    """Planar arm faces normal to Y sitting exactly on the mount plane."""
    return [f for f in arm_obj.Shape.Faces
            if f.Surface.TypeId == "Part::GeomPlane"
            and f.BoundBox.YLength < 1e-9
            and abs(f.CenterOfMass.y - face_y) < 1e-6]


def x_axis_cylindrical_faces(arm_obj):
    """Cylindrical arm faces whose axis runs along X (the arc sweep)."""
    x_axis = App.Vector(1, 0, 0)
    return [f for f in arm_obj.Shape.Faces
            if f.Surface.TypeId == "Part::GeomCylinder"
            and abs(abs(f.Surface.Axis * x_axis) - 1.0) < 1e-9]


def main():
    base = parameters.resolve(parameters.get_params())

    print("--- Phase 1 regression: baseline dimensions ---")
    doc, o = build_with()
    check("housing width == MAIN_BODY_WIDTH",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])
    check("housing depth == MAIN_BODY_DEPTH",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"])
    # The housing solid carries the integrated rear arm (Phase 3): verify
    # the rectangular body with a thin slab above the arm's reach.
    body_mid_z = (base["MAIN_BODY_DISPLAY_OFFSET_Z"]
                  + base["MAIN_BODY_HEIGHT"] * 0.75)
    body = slab_bb(o[HOUSING], body_mid_z - 0.25, body_mid_z + 0.25)
    check("rectangular body width == MAIN_BODY_WIDTH",
          body.XLength, base["MAIN_BODY_WIDTH"])
    check("rectangular body depth == MAIN_BODY_DEPTH",
          body.YLength, base["MAIN_BODY_DEPTH"])
    check("housing top == bottom + MAIN_BODY_HEIGHT",
          o[HOUSING].Shape.BoundBox.ZMax,
          base["MAIN_BODY_DISPLAY_OFFSET_Z"] + base["MAIN_BODY_HEIGHT"])
    check("display thickness == DISPLAY_LID_THICKNESS",
          extents(o[DISPLAY])[1], base["DISPLAY_LID_THICKNESS"])
    check("housing bottom derives from MAIN_BODY_LID_TOP_CLEARANCE",
          base["MAIN_BODY_DISPLAY_OFFSET_Z"],
          base["MAIN_BODY_LID_TOP_CLEARANCE"])
    check("display top edge at Z=0", o[DISPLAY].Shape.BoundBox.ZMax, 0.0)

    print("--- Phase 1 regression: MAIN_BODY_WIDTH regenerates ---")
    _, o = build_with(MAIN_BODY_WIDTH=base["MAIN_BODY_WIDTH"] + 20.0)
    check("housing width follows MAIN_BODY_WIDTH",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"] + 20.0)
    check("display width unaffected",
          extents(o[DISPLAY])[0], base["DISPLAY_REFERENCE_WIDTH"])

    print("--- Phase 1 regression: MAIN_BODY_HEIGHT regenerates ---")
    _, o = build_with(MAIN_BODY_HEIGHT=base["MAIN_BODY_HEIGHT"] + 10.0)
    check("housing top follows MAIN_BODY_HEIGHT",
          o[HOUSING].Shape.BoundBox.ZMax,
          base["MAIN_BODY_DISPLAY_OFFSET_Z"]
          + base["MAIN_BODY_HEIGHT"] + 10.0)

    print("--- Phase 1 regression: MAIN_BODY_DEPTH regenerates ---")
    _, o = build_with(MAIN_BODY_DEPTH=base["MAIN_BODY_DEPTH"] + 3.0)
    check("housing depth follows MAIN_BODY_DEPTH",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"] + 3.0)

    print("--- Phase 1 regression: DISPLAY_LID_THICKNESS touches only the reference ---")
    _, o = build_with(DISPLAY_LID_THICKNESS=base["DISPLAY_LID_THICKNESS"] + 2.0)
    check("display thickness follows DISPLAY_LID_THICKNESS",
          extents(o[DISPLAY])[1], base["DISPLAY_LID_THICKNESS"] + 2.0)
    check("housing depth unaffected by DISPLAY_LID_THICKNESS",
          extents(o[HOUSING])[1], base["MAIN_BODY_DEPTH"])
    check("housing width unaffected by DISPLAY_LID_THICKNESS",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    print("--- Phase 2: sensor-head geometry (user side = -Y) ---")
    doc, o = build_with()
    front_face_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                    - base["MAIN_BODY_DEPTH"] / 2.0)
    rear_face_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                   + base["MAIN_BODY_DEPTH"] / 2.0)
    check_true("face and interaction heads are distinct objects",
               o[FACE] is not o[INTERACTION])
    check_true("face head is separate from Main_Housing",
               o[FACE] is not o[HOUSING])
    check_true("interaction head is separate from Main_Housing",
               o[INTERACTION] is not o[HOUSING])
    check("face head length == derived symmetric length",
          extents(o[FACE])[0], base["FACE_HEAD_LENGTH"])
    check("interaction head length == derived symmetric length",
          extents(o[INTERACTION])[0], base["INTERACTION_HEAD_LENGTH"])
    check("face head Y extent == FACE_HEAD_DIAMETER",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("face head Z extent == FACE_HEAD_DIAMETER",
          extents(o[FACE])[2], base["FACE_HEAD_DIAMETER"])
    check("interaction head Y extent == INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("interaction head Z extent == INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[2], base["INTERACTION_HEAD_DIAMETER"])
    check_true("face head cylinder axis along X",
               cylinder_axis_along_x(o[FACE]))
    check_true("interaction head cylinder axis along X",
               cylinder_axis_along_x(o[INTERACTION]))
    check("face head starts after the left end margin",
          o[FACE].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"])
    check("interaction head starts after the centre gap",
          o[INTERACTION].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"]
          + base["FACE_HEAD_LENGTH"] + base["SENSOR_HEAD_CENTER_GAP"])
    check("interaction head leaves the right end margin",
          base["MAIN_BODY_WIDTH"] / 2.0 - o[INTERACTION].Shape.BoundBox.XMax,
          base["SENSOR_HEAD_END_MARGIN"])
    check("face head axis on the housing user-side face (Y)",
          axis_center_y(o[FACE]),
          front_face_y - base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"])
    check("face head axis at housing vertical centre (Z)",
          axis_center_z(o[FACE]),
          base["MAIN_BODY_DISPLAY_OFFSET_Z"] + base["MAIN_BODY_HEIGHT"] / 2.0
          + base["SENSOR_HEAD_AXIS_Z_OFFSET_FROM_BODY_CENTER"])
    check("face head protrudes toward the user past the front face",
          front_face_y - o[FACE].Shape.BoundBox.YMin,
          base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"]
          + base["FACE_HEAD_DIAMETER"] / 2.0)
    check("interaction head protrudes toward the user past the front face",
          front_face_y - o[INTERACTION].Shape.BoundBox.YMin,
          base["SENSOR_HEAD_AXIS_Y_OFFSET_FROM_FRONT_FACE"]
          + base["INTERACTION_HEAD_DIAMETER"] / 2.0)
    check_true("face head does not protrude past the rear (mount) face",
               o[FACE].Shape.BoundBox.YMax <= rear_face_y + 1e-6)
    check_true("interaction head does not protrude past the rear (mount) face",
               o[INTERACTION].Shape.BoundBox.YMax <= rear_face_y + 1e-6)

    print("--- Phase 2: FACE_HEAD_DIAMETER touches only the face head ---")
    _, o = build_with(FACE_HEAD_DIAMETER=base["FACE_HEAD_DIAMETER"] + 6.0)
    check("face head Y extent follows FACE_HEAD_DIAMETER",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"] + 6.0)
    check("face head Z extent follows FACE_HEAD_DIAMETER",
          extents(o[FACE])[2], base["FACE_HEAD_DIAMETER"] + 6.0)
    check("interaction head diameter unaffected",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("housing width unaffected by FACE_HEAD_DIAMETER",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    print("--- Phase 2: INTERACTION_HEAD_DIAMETER touches only the interaction head ---")
    _, o = build_with(INTERACTION_HEAD_DIAMETER=base["INTERACTION_HEAD_DIAMETER"] + 6.0)
    check("interaction head Y extent follows INTERACTION_HEAD_DIAMETER",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"] + 6.0)
    check("face head diameter unaffected",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2: margins, gap, explicit lengths ---")
    _, o = build_with(SENSOR_HEAD_END_MARGIN=base["SENSOR_HEAD_END_MARGIN"] + 2.0)
    check("face head start follows SENSOR_HEAD_END_MARGIN",
          o[FACE].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"] + 2.0)
    check("derived head length shrinks with larger margins",
          extents(o[FACE])[0],
          (base["MAIN_BODY_WIDTH"] - 2.0 * (base["SENSOR_HEAD_END_MARGIN"] + 2.0)
           - base["SENSOR_HEAD_CENTER_GAP"]) / 2.0)
    _, o = build_with(SENSOR_HEAD_CENTER_GAP=base["SENSOR_HEAD_CENTER_GAP"] + 4.0)
    check("interaction head start follows SENSOR_HEAD_CENTER_GAP",
          o[INTERACTION].Shape.BoundBox.XMin,
          -base["MAIN_BODY_WIDTH"] / 2.0 + base["SENSOR_HEAD_END_MARGIN"]
          + (base["MAIN_BODY_WIDTH"] - 2.0 * base["SENSOR_HEAD_END_MARGIN"]
             - base["SENSOR_HEAD_CENTER_GAP"] - 4.0) / 2.0
          + base["SENSOR_HEAD_CENTER_GAP"] + 4.0)
    _, o = build_with(FACE_HEAD_LENGTH=40.0)
    check("explicit FACE_HEAD_LENGTH honoured",
          extents(o[FACE])[0], 40.0)
    check("interaction head keeps derived length when face is explicit",
          extents(o[INTERACTION])[0], base["INTERACTION_HEAD_LENGTH"])

    print("--- Phase 2: orientation marks (flush debug strips) ---")
    mark_t = base["ORIENTATION_MARK_THICKNESS"]
    mark_w = base["ORIENTATION_MARK_WIDTH"]

    def mark_extents_yz(rot_deg):
        """(Y, Z) bounding extents of a mark pitched rot_deg about X."""
        c = abs(math.cos(math.radians(rot_deg)))
        s = abs(math.sin(math.radians(rot_deg)))
        return mark_t * c + mark_w * s, mark_t * s + mark_w * c

    _, o = build_with()
    check("baseline face mark thin in Y (flush strip)",
          extents(o[FACE_MARK])[1], mark_t)
    check("baseline face mark width in Z",
          extents(o[FACE_MARK])[2], mark_w)
    check("face mark nearly flush with the barrel surface",
          (axis_center_y(o[FACE]) - base["FACE_HEAD_DIAMETER"] / 2.0)
          - o[FACE_MARK].Shape.BoundBox.YMin,
          mark_t - base["ORIENTATION_MARK_EMBED"])
    check_true("face mark sits on the user side of the housing front face",
               o[FACE_MARK].Shape.BoundBox.YMax <= front_face_y + 1e-6)
    check_true("interaction mark sits on the user side of the housing front face",
               o[INTERACTION_MARK].Shape.BoundBox.YMax <= front_face_y + 1e-6)
    # Nominal orientations per the geometry specification: face drum
    # forward, interaction drum pitched down (provisional angle).
    int_base_y, int_base_z = mark_extents_yz(
        base["INTERACTION_HEAD_ROTATION_DEG"])
    check("baseline interaction mark Y extent matches the nominal pitch",
          extents(o[INTERACTION_MARK])[1], int_base_y)
    check("baseline interaction mark Z extent matches the nominal pitch",
          extents(o[INTERACTION_MARK])[2], int_base_z)
    check_true("interaction drum is nominally pitched (not flush-Y)",
               int_base_y > mark_t + 0.1)

    print("--- Phase 2: independent rotation about X ---")
    _, o = build_with(FACE_HEAD_ROTATION_DEG=90.0)
    check("rotated face mark Y extent grows to mark width",
          extents(o[FACE_MARK])[1], mark_w)
    check("rotated face mark Z extent collapses to thickness",
          extents(o[FACE_MARK])[2], mark_t)
    check("face mark X extent unchanged (rotation about X)",
          extents(o[FACE_MARK])[0],
          base["FACE_HEAD_LENGTH"] * base["ORIENTATION_MARK_LENGTH_FRACTION"])
    check("interaction mark keeps its baseline pitch (Y)",
          extents(o[INTERACTION_MARK])[1], int_base_y)
    check("interaction mark keeps its baseline pitch (Z)",
          extents(o[INTERACTION_MARK])[2], int_base_z)
    check("face barrel envelope unchanged by its own rotation (Y)",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("interaction barrel envelope unchanged by face rotation (Y)",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("housing unaffected by face rotation",
          extents(o[HOUSING])[0], base["MAIN_BODY_WIDTH"])

    _, o = build_with(INTERACTION_HEAD_ROTATION_DEG=90.0)
    check("rotated interaction mark Y extent grows to mark width",
          extents(o[INTERACTION_MARK])[1], mark_w)
    check("rotated interaction mark Z extent collapses to thickness",
          extents(o[INTERACTION_MARK])[2], mark_t)
    face_base_y, face_base_z = mark_extents_yz(
        base["FACE_HEAD_ROTATION_DEG"])
    check("face mark keeps its baseline pitch (Y)",
          extents(o[FACE_MARK])[1], face_base_y)
    check("face mark keeps its baseline pitch (Z)",
          extents(o[FACE_MARK])[2], face_base_z)

    print("--- Phase 2: model structure / no later-phase geometry ---")
    doc, o = build_with()
    part_features = [obj for obj in doc.Objects if obj.TypeId == "Part::Feature"]
    check("exactly six Part::Feature solids", len(part_features), 6)
    check("exactly eight document objects (2 groups + 6 parts)",
          len(doc.Objects), 8)
    references = doc.getObject(document.GROUP_REFERENCES)
    product = doc.getObject(document.GROUP_PRODUCT)
    check_true("References group exists", references is not None)
    check_true("Product group exists", product is not None)
    check_true("display reference is in References group",
               references is not None and o[DISPLAY] in references.Group)
    check_true("face mark is in References group",
               references is not None and o[FACE_MARK] in references.Group)
    check_true("interaction mark is in References group",
               references is not None and o[INTERACTION_MARK] in references.Group)
    check_true("main housing is in Product group",
               product is not None and o[HOUSING] in product.Group)
    check_true("face head is in Product group",
               product is not None and o[FACE] in product.Group)
    check_true("interaction head is in Product group",
               product is not None and o[INTERACTION] in product.Group)

    print("--- Phase 3: single-profile housing + arm, laptop-lid pocket ---")
    doc, o = build_with()
    housing = o[HOUSING]
    housing_bb = housing.Shape.BoundBox
    display_bb = o[DISPLAY].Shape.BoundBox
    face_y = base["REAR_ARM_MOUNT_FACE_Y"]
    arc_cz = base["REAR_ARM_ARC_CENTER_Z"]
    radius = base["REAR_ARM_RADIUS"]
    bottom_z = base["REAR_ARM_BOTTOM_Z"]
    rear_y = base["REAR_ARM_REAR_Y"]
    housing_front_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                       - base["MAIN_BODY_DEPTH"] / 2.0)
    housing_rear_y = (base["MAIN_BODY_DISPLAY_OFFSET_Y"]
                      + base["MAIN_BODY_DEPTH"] / 2.0)
    housing_bot_z = base["MAIN_BODY_DISPLAY_OFFSET_Z"]
    housing_top_z = housing_bot_z + base["MAIN_BODY_HEIGHT"]
    lid_front_y = display_bb.YMin
    lid_rear_y = display_bb.YMax

    # One coherent extruded side profile: a single connected solid,
    # never a separate arm object.
    check("Main_Housing is exactly one connected solid",
          len(housing.Shape.Solids), 1)
    check_true("Main_Housing solid is valid", housing.Shape.isValid())
    check_true("no separate Rear_Arm object remains",
               doc.getObject("Rear_Arm") is None)
    product = doc.getObject(document.GROUP_PRODUCT)
    check("Product group holds exactly the housing and two heads",
          len(product.Group), 3)
    check_true("arm volume is inside Main_Housing (interior probe)",
               housing.Shape.isInside(
                   App.Vector(0.0, face_y + 0.4 * radius,
                              arc_cz - 0.4 * radius), 1e-6, True))
    check("single-profile housing spans the full device width",
          housing_bb.XLength, base["MAIN_BODY_WIDTH"])
    check("single-profile solid has exactly 8 faces (no splitter "
          "debris)", len(housing.Shape.Faces), 8)

    # The arm in its corrected LOWER position: a true circular
    # quarter-profile hanging below the body, tangent to the rear face
    # exactly at the bottom-rear corner (the GREEN annotation target).
    arc_faces = x_axis_cylindrical_faces(housing)
    check_true("housing carries one true cylindrical arc face",
               len(arc_faces) == 1)
    if arc_faces:
        surf = arc_faces[0].Surface
        check("arc face radius == resolved REAR_ARM_RADIUS",
              surf.Radius, radius)
        check("arc face centre Y == MOUNT_FACE_Y", surf.Center.y, face_y)
        check("arc centre Z == housing bottom plane (lower position)",
              surf.Center.z, housing_bot_z)
        check("arc face spans the full device width",
              arc_faces[0].BoundBox.XLength, base["MAIN_BODY_WIDTH"])
        check("arc top endpoint lands exactly on the housing rear plane",
              arc_faces[0].BoundBox.YMax, housing_rear_y)
        check("arc top endpoint lands exactly on the housing bottom "
              "plane", arc_faces[0].BoundBox.ZMax, housing_bot_z)
        check("arc bottom endpoint at the mounting-face tip",
              arc_faces[0].BoundBox.ZMin, bottom_z)
    mount_faces = planar_mount_faces(housing, face_y)
    check_true("housing carries the planar vertical mounting face",
               len(mount_faces) == 1)
    if mount_faces:
        mf_bb = mount_faces[0].BoundBox
        check("mounting face spans the full device width",
              mf_bb.XLength, base["MAIN_BODY_WIDTH"])
        check("mounting face bottom at the arm tip",
              mf_bb.ZMin, bottom_z)
        check("mounting face top at the housing bottom face",
              mf_bb.ZMax, housing_bot_z)
    check("derived radius lands the arc exactly on the rear plane",
          rear_y, housing_rear_y)
    check("arc centre sits on the housing bottom plane (parameter)",
          arc_cz, housing_bot_z)

    # The corrected lower connection: rear face and arc meet at the
    # bottom-rear corner with a shared tangent -- one continuous
    # silhouette, no lower band, no subdivision seam.
    rear_faces = [f for f in housing.Shape.Faces
                  if f.Surface.TypeId == "Part::GeomPlane"
                  and f.BoundBox.YLength < 1e-9
                  and abs(f.CenterOfMass.y - housing_rear_y) < 1e-6]
    check_true("exactly one planar rear face (no lower band)",
               len(rear_faces) == 1)
    if rear_faces:
        rf_bb = rear_faces[0].BoundBox
        check("rear face spans the full housing height",
              rf_bb.ZLength, base["MAIN_BODY_HEIGHT"])
        check("rear face bottom == housing bottom plane",
              rf_bb.ZMin, housing_bot_z)
        check_true("rear face unsubdivided (4 boundary edges)",
                   len(rear_faces[0].Edges) == 4)
    # Regression for the reported artifact: the old embedded-arm
    # construction left a full-width horizontal seam on the rear face at
    # the arc tangent height (housing bottom + 6 mm). That edge must not
    # exist.
    old_crossover_z = housing_bot_z + 6.0
    seam_edges = [e for e in housing.Shape.Edges
                  if e.BoundBox.XLength > 0.9 * base["MAIN_BODY_WIDTH"]
                  and e.BoundBox.ZLength < 1e-9
                  and abs(e.BoundBox.ZMin - old_crossover_z) < 1e-6]
    check_true("no full-width seam at the old crossover height "
               "(Z = housing bottom + 6)", not seam_edges)

    # Silhouette sanity.
    check("profile silhouette bottom == arm bottom tip",
          housing_bb.ZMin, bottom_z)
    check("profile silhouette top == rectangular body top",
          housing_bb.ZMax, housing_top_z)
    check("profile silhouette rear == housing rear face",
          housing_bb.YMax, housing_rear_y)

    # The intentional laptop-lid pocket: the slot bounded above by the
    # housing bottom face (ceiling) and at the rear by the arm's
    # mounting face (wall). With the single-profile construction the
    # ceiling is a real standalone face, not a boolean leftover.
    check("pocket width == LAPTOP_LID_POCKET_CLEARANCE",
          face_y - lid_rear_y, base["LAPTOP_LID_POCKET_CLEARANCE"])
    check("pocket ceiling height == MAIN_BODY_LID_TOP_CLEARANCE",
          housing_bot_z, base["MAIN_BODY_LID_TOP_CLEARANCE"])
    ceilings = [f for f in housing.Shape.Faces
                if f.Surface.TypeId == "Part::GeomPlane"
                and f.BoundBox.ZLength < 1e-9
                and abs(f.BoundBox.ZMax - housing_bot_z) < 1e-6]
    check_true("exactly one horizontal face at the housing bottom (the "
               "pocket ceiling; no residual lower strip)",
               len(ceilings) == 1)
    if ceilings:
        c_bb = ceilings[0].BoundBox
        check("pocket ceiling spans the lid front plane to the mounting "
              "face", c_bb.YLength, face_y - housing_front_y)
        check("pocket ceiling front == housing front plane",
              c_bb.YMin, housing_front_y)
        check("pocket ceiling rear == mounting face", c_bb.YMax, face_y)
        check("pocket ceiling spans the full device width",
              c_bb.XLength, base["MAIN_BODY_WIDTH"])
    # Pocket ceiling rays: the first device material directly above the
    # lid's top edge (and above the clearance slot behind it) must be the
    # housing bottom face at exactly housing_bot_z -- nothing hangs down
    # into the pocket.
    ray_over_lid = Part.makeBox(1.0, 1.0, housing_top_z,
                                App.Vector(-0.5, -0.5, 0.0))
    check("first material above the lid top edge is the pocket ceiling",
          housing.Shape.common(ray_over_lid).BoundBox.ZMin,
          housing_bot_z)
    slot_mid_y = (lid_rear_y + face_y) / 2.0
    ray_over_slot = Part.makeBox(1.0, 1.0, housing_top_z,
                                 App.Vector(-0.5, slot_mid_y - 0.5, 0.0))
    check("pocket ceiling extends over the clearance slot",
          housing.Shape.common(ray_over_slot).BoundBox.ZMin,
          housing_bot_z)
    probe = Part.makeBox(400.0, face_y - lid_front_y, housing_bot_z,
                         App.Vector(-200.0, lid_front_y, 0.0))
    check("pocket cavity is free of device material (lid can enter)",
          housing.Shape.common(probe).Volume, 0.0)
    check("laptop lid does not intersect the housing",
          housing.Shape.common(o[DISPLAY].Shape).Volume, 0.0)
    check_true("laptop lid remains a separate reference object",
               o[DISPLAY] is not housing
               and o[DISPLAY] in doc.getObject(
                   document.GROUP_REFERENCES).Group)
    check("housing front plane flush with the lid front plane",
          housing_bb.YMin, lid_front_y)
    check_true("arm tip descends below the lid top edge (captures it)",
               bottom_z < 0.0)
    check_true("arm is compact (tip in the top quarter of the lid)",
               bottom_z > -base["DISPLAY_REFERENCE_HEIGHT"] / 4.0)
    check("interaction drum still at its nominal pitch",
          extents(o[INTERACTION_MARK])[1], int_base_y)
    check("face head diameter unchanged by the arm correction",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("interaction head diameter unchanged",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    face_axis_z = axis_center_z(o[FACE])

    print("--- Phase 3: pocket parameters regenerate the pocket ---")
    # Expected values are recomputed from `base` (plain floats) because
    # build_with() closes and replaces the document.
    _, o2 = build_with(LAPTOP_LID_POCKET_CLEARANCE=
                       base["LAPTOP_LID_POCKET_CLEARANCE"] + 1.0)
    h2 = o2[HOUSING]
    check_true("mounting face follows LAPTOP_LID_POCKET_CLEARANCE",
               len(planar_mount_faces(h2, face_y + 1.0)) == 1)
    check("arc radius re-derives to the bottom-rear corner",
          x_axis_cylindrical_faces(h2)[0].Surface.Radius, radius - 1.0)
    check("arc top still lands on the housing rear plane",
          x_axis_cylindrical_faces(h2)[0].BoundBox.YMax, housing_rear_y)
    check("arm tip follows the re-derived radius",
          h2.Shape.BoundBox.ZMin, housing_bot_z - (radius - 1.0))
    check("head geometry unchanged by pocket clearance edit",
          extents(o2[FACE])[1], base["FACE_HEAD_DIAMETER"])
    _, o2 = build_with(MAIN_BODY_LID_TOP_CLEARANCE=
                       base["MAIN_BODY_LID_TOP_CLEARANCE"] + 2.0)
    h2 = o2[HOUSING]
    check("arm and ceiling follow MAIN_BODY_LID_TOP_CLEARANCE",
          h2.Shape.BoundBox.ZMin, bottom_z + 2.0)
    check("housing top follows MAIN_BODY_LID_TOP_CLEARANCE",
          h2.Shape.BoundBox.ZMax, housing_top_z + 2.0)
    check("heads ride with the housing (face axis Z follows)",
          axis_center_z(o2[FACE]), face_axis_z + 2.0)
    check("head diameter unchanged by lid-top clearance edit",
          extents(o2[FACE])[1], base["FACE_HEAD_DIAMETER"])
    _, o2 = build_with(MAIN_BODY_LID_FRONT_OFFSET=
                       base["MAIN_BODY_LID_FRONT_OFFSET"] + 2.0)
    h2 = o2[HOUSING]
    check("housing front follows MAIN_BODY_LID_FRONT_OFFSET",
          h2.Shape.BoundBox.YMin, housing_front_y + 2.0)
    check("arm radius re-derives with the housing rear",
          x_axis_cylindrical_faces(h2)[0].Surface.Radius, radius + 2.0)
    check("arc top lands on the shifted rear plane",
          x_axis_cylindrical_faces(h2)[0].BoundBox.YMax,
          housing_rear_y + 2.0)
    _, o2 = build_with(REAR_ARM_RADIUS=12.5)
    h2 = o2[HOUSING]
    check("explicit REAR_ARM_RADIUS override honoured",
          x_axis_cylindrical_faces(h2)[0].Surface.Radius, 12.5)
    check("explicit-radius arm tucks under the housing rear",
          h2.Shape.BoundBox.YMax, housing_rear_y)
    check("explicit-radius arm bottom follows RADIUS",
          h2.Shape.BoundBox.ZMin, housing_bot_z - 12.5)
    strips = [f for f in h2.Shape.Faces
              if f.Surface.TypeId == "Part::GeomPlane"
              and f.BoundBox.ZLength < 1e-9
              and abs(f.BoundBox.ZMax - housing_bot_z) < 1e-6]
    check("smaller explicit radius leaves a flat bottom strip behind "
          "the arc", len(strips), 2)

    _, o2 = build_with(LAPTOP_LID_POCKET_CLEARANCE=
                       base["LAPTOP_LID_POCKET_CLEARANCE"] + 1.0,
                       MAIN_BODY_LID_TOP_CLEARANCE=
                       base["MAIN_BODY_LID_TOP_CLEARANCE"] + 2.0)
    check("housing width unaffected by pocket edits",
          extents(o2[HOUSING])[0], base["MAIN_BODY_WIDTH"])
    check("face head diameter unaffected by pocket edits",
          extents(o2[FACE])[1], base["FACE_HEAD_DIAMETER"])
    check("interaction head diameter unaffected by pocket edits",
          extents(o2[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    check("display reference unaffected by pocket edits",
          extents(o2[DISPLAY])[0], base["DISPLAY_REFERENCE_WIDTH"])

    print("--- Phase 3: pocket invariants ---")
    try:
        build_with(LAPTOP_LID_POCKET_CLEARANCE=0.2)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects a sub-0.5 mm pocket clearance", raised)
    try:
        build_with(MAIN_BODY_LID_TOP_CLEARANCE=0.0)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects the housing touching the lid top",
               raised)
    try:
        build_with(MAIN_BODY_LID_FRONT_OFFSET=30.0)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects housing placements with no pocket "
               "room", raised)
    try:
        build_with(REAR_ARM_RADIUS=1.0)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects a sub-2 mm arm radius", raised)
    try:
        build_with(REAR_ARM_RADIUS=base["MAIN_BODY_LID_TOP_CLEARANCE"]
                   + 0.5)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects an arm tip that does not capture the "
               "lid top edge", raised)
    try:
        build_with(REAR_ARM_RADIUS=radius + 5.0)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects an arc reaching past the housing rear "
               "face", raised)
    try:
        build_with(FACE_HEAD_DIAMETER=48.0, INTERACTION_HEAD_DIAMETER=48.0)
        raised = False
    except ValueError:
        raised = True
    check_true("resolve() rejects heads that break the pocket ceiling",
               raised)

    print("--- Phase 3: no cable or mounting-stack geometry ---")
    doc, o = build_with()
    forbidden = ("usb", "cable", "magnet", "plate", "tape", "foam",
                 "adhesive")
    check_true("no USB-C cable or Phase 4 mounting objects exist",
               not any(tok in obj.Name.lower()
                       for obj in doc.Objects for tok in forbidden))

    print("--- Phase 2.5: live-reload architecture ---")
    import live_reload
    import review_camera

    watched = {os.path.basename(p) for p in live_reload.watched_files()}
    for required in ("parameters.py", "parts.py", "sensor_heads.py",
                     "rear_arm.py", "document.py"):
        check_true("watched: " + required, required in watched)
    for excluded in ("build.py", "validate.py", "live_reload.py",
                     "start_dev.py", "review_camera.py", "review_view.py",
                     "capture_review_view.py", "review_view_preset.py"):
        check_true("not watched: " + excluded, excluded not in watched)
    check_true("deepreal.FCStd is not a watch trigger",
               not any(p.endswith(".FCStd") for p in live_reload.watched_files()))

    deb = live_reload.Debouncer(0.4)
    deb.note_change(0.0)
    deb.note_change(0.1)
    deb.note_change(0.2)
    check_true("debouncer suppresses rapid burst", not deb.due(0.5))
    check_true("debouncer fires once burst is quiet", deb.due(0.61))
    deb.fire()
    check_true("debouncer resets after firing", not deb.due(1.0))

    fd, tmp_file = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    try:
        snap = live_reload.snapshot([tmp_file])
        changed, snap = live_reload.detect_changes([tmp_file], snap)
        check_true("no change detected without edits", not changed)
        later_ns = int((time.time() + 5.0) * 1e9)
        os.utime(tmp_file, ns=(later_ns, later_ns))
        changed, snap = live_reload.detect_changes([tmp_file], snap)
        check_true("mtime change detected", changed)
    finally:
        os.remove(tmp_file)

    tmp_dir = tempfile.mkdtemp()
    sys.path.insert(0, tmp_dir)
    probe_mod = "deepreal_reload_probe"
    try:
        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("VALUE = 1\n")
        importlib.import_module(probe_mod)
        check("probe module initial value", sys.modules[probe_mod].VALUE, 1)

        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("def broken(:\n")
        try:
            live_reload.reload_modules([probe_mod])
            raised = False
        except Exception:
            raised = True
        check_true("broken module reload raises (session catches it)", raised)
        check("module keeps last good state after failed reload",
              sys.modules[probe_mod].VALUE, 1)

        with open(os.path.join(tmp_dir, probe_mod + ".py"), "w") as fh:
            fh.write("VALUE = 2\n")
        live_reload.reload_modules([probe_mod])
        check("module recovers with new value", sys.modules[probe_mod].VALUE, 2)
    finally:
        sys.path.remove(tmp_dir)
        sys.modules.pop(probe_mod, None)

    try:
        reloaded = live_reload.reload_geometry_modules()
        check_true("geometry modules reload without error (reloaded: {})"
                   .format(", ".join(reloaded)), True)
    except Exception:
        check_true("geometry modules reload without error", False)

    print("--- Phase 2.5: in-place rebuild without duplication ---")
    doc, o = build_with()
    for _ in range(20):
        document.rebuild_in_place(doc)
    names = sorted(obj.Name for obj in doc.Objects)
    check("object count stable after 20 in-place rebuilds",
          len(doc.Objects), 8)
    check_true("no duplicate object names after 20 rebuilds",
               len(names) == len(set(names)))
    o = {obj.Name: obj for obj in doc.Objects}
    check_true("sensor heads still separate after rebuilds",
               o[FACE] is not o[INTERACTION])
    check_true("heads still in Product group after rebuilds",
               o[FACE] in doc.getObject(document.GROUP_PRODUCT).Group
               and o[INTERACTION] in doc.getObject(document.GROUP_PRODUCT).Group)
    check("face head diameter intact after rebuilds",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    p27 = parameters.resolve(dict(parameters.get_params(),
                                  FACE_HEAD_DIAMETER=27.0))
    document.rebuild_in_place(doc, p27)
    o = {obj.Name: obj for obj in doc.Objects}
    check("in-place rebuild applies FACE_HEAD_DIAMETER=27",
          extents(o[FACE])[1], 27.0)
    check("interaction head unchanged by face-only edit",
          extents(o[INTERACTION])[1], base["INTERACTION_HEAD_DIAMETER"])
    document.rebuild_in_place(doc)
    o = {obj.Name: obj for obj in doc.Objects}
    check("in-place rebuild returns to default diameter",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2.5: failed reload keeps the last valid model ---")
    bad = parameters.resolve(dict(parameters.get_params(),
                                  FACE_HEAD_DIAMETER=-5.0))
    try:
        document.rebuild_in_place(doc, bad)
        raised = False
    except Exception:
        raised = True
    check_true("invalid geometry raises during staging", raised)
    check("model intact after failed rebuild (object count)",
          len(doc.Objects), 8)
    o = {obj.Name: obj for obj in doc.Objects}
    check("face head intact after failed rebuild",
          extents(o[FACE])[1], base["FACE_HEAD_DIAMETER"])
    document.rebuild_in_place(doc)
    check("rebuild succeeds again after failure",
          extents({obj.Name: obj for obj in doc.Objects}[FACE])[1],
          base["FACE_HEAD_DIAMETER"])

    print("--- Phase 2.5: orphan cleanup / generated-object ownership ---")
    doc, o = build_with()
    check_true("all generated objects carry the ownership stamp",
               all(getattr(obj, "DeepRealGenerated", False)
                   for obj in doc.Objects))
    orphan = doc.addObject("Part::Feature", "Orphan_Probe")
    orphan.Shape = Part.makeSphere(5.0, App.Vector(0.0, 0.0, 15.0))
    document._mark_generated(orphan)  # as if a previous build created it
    doc.getObject(document.GROUP_REFERENCES).addObject(orphan)
    manual = doc.addObject("Part::Feature", "Manual_Notes")
    manual.Shape = Part.makeBox(1.0, 1.0, 1.0)
    doc.getObject(document.GROUP_REFERENCES).addObject(manual)
    doc.recompute()
    check("object count with probe objects", len(doc.Objects), 10)
    document.rebuild_in_place(doc)
    check("stamped orphan removed on rebuild", len(doc.Objects), 9)
    check_true("orphan name gone from the document",
               doc.getObject("Orphan_Probe") is None)
    check_true("manual (unstamped) object survives rebuild",
               doc.getObject("Manual_Notes") is not None)
    check_true("standard generated set intact after cleanup",
               all(doc.getObject(n) is not None for n in (
                   DISPLAY, HOUSING, FACE, INTERACTION,
                   FACE_MARK, INTERACTION_MARK)))
    check_true("groups still exist after cleanup",
               doc.getObject(document.GROUP_REFERENCES) is not None
               and doc.getObject(document.GROUP_PRODUCT) is not None)

    print("--- Phase 2.5: review camera preset ---")
    check_true("missing preset -> None (fallback to iso+fitAll)",
               review_camera.load_preset(
                   os.path.join(tempfile.gettempdir(),
                                "deepreal_no_such_preset.py")) is None)
    preset_probe = os.path.join(tmp_dir, "preset_probe.py")
    with open(preset_probe, "w") as fh:
        fh.write('CAMERA_SETTINGS = "#Inventor V2.1 ascii\\n\\n'
                 'OrthographicCamera { }\\n"\n')
    loaded = review_camera.load_preset(preset_probe)
    check_true("preset file loads as a camera string",
               isinstance(loaded, str) and "OrthographicCamera" in loaded)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("--- Phase 2.5: no GUI XML injection anywhere ---")
    # Needles are built dynamically so this file's own source stays clean.
    needle_zip_write = "write" + "str"
    needle_module = "view" + "state"
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(HERE, name)) as fh:
            src = fh.read()
        check_true("{}: no archive-injection code".format(name),
                   needle_zip_write not in src and needle_module not in src)

    print("--- document presentation ---")
    doc, o = build_with()
    check_true("no touched/invalid objects after build recompute",
               all(not ({"Touched", "Invalid"} & set(obj.State))
                   for obj in doc.Objects))

    if os.path.exists(document.OUTPUT_PATH):
        if document.DOC_NAME in App.listDocuments():
            App.closeDocument(document.DOC_NAME)
        saved = App.openDocument(document.OUTPUT_PATH)
        names = sorted(obj.Name for obj in saved.Objects)
        print("  saved objects:", ", ".join(names))
        check("saved document object count", len(saved.Objects), 8)
        for name in (DISPLAY, HOUSING, FACE, INTERACTION, FACE_MARK,
                     INTERACTION_MARK):
            check_true("saved document contains " + name,
                       saved.getObject(name) is not None)
        check_true("saved document has no separate Rear_Arm object",
                   saved.getObject("Rear_Arm") is None)
        check_true("saved document fully recomputed (no touched/invalid)",
                   all(not ({"Touched", "Invalid"} & set(obj.State))
                       for obj in saved.Objects))
        App.closeDocument(saved.Name)

        with zipfile.ZipFile(document.OUTPUT_PATH) as zf:
            zip_members = zf.namelist()
        print("  archive members:", ", ".join(zip_members))
        check_true("no GuiDocument.xml in freshly built file (GUI XML "
                   "injection removed; view state stays GUI-side)",
                   "GuiDocument.xml" not in zip_members)
    else:
        check_true("deepreal.FCStd exists (run build.py first)", False)

    print()
    if FAILURES:
        print("VALIDATION FAILED ({} check(s)):".format(len(FAILURES)))
        for label in FAILURES:
            print("  -", label)
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(1)
    print("All validation checks passed (Phases 1, 2, 2.5 and 3).")
    sys.stdout.flush()


# freecadcmd quirks: an unhandled exception makes it run the script a
# second time and still exit 0, and sys.exit() drops buffered stdout.
# Catch everything, flush explicitly, and exit with a real status code.
try:
    main()
except SystemExit:
    raise
except Exception:
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    sys.exit(1)
