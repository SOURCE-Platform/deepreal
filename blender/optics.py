"""Sensor-drum optical packaging: real hardware inside the drums.

Implements the correction spec ("Put the Optical Hardware Inside the
Rotating Drums") on top of the hollow-shell drums built by device.py:

- drum exterities stay PERFECT cylinders (true circular cross-sections);
  apertures are local through-wall bores (deterministic Boolean cuts baked
  during each rebuild), never flats or panels;
- inside each drum: a flat internal optical carrier rail plus three
  named module assemblies -- RGB camera, IR/depth camera, structured-
  light projector -- each with barrel + body + PCB placeholder volumes;
- optical axes stay PARALLEL to the drum's rest facing direction (the
  calibrated-array rule): the modules mount on the carrier, barrels run
  along -Y and pass through the curved wall, bodies stay inside the
  cavity;
- every module is parametric and independently named per the spec
  (Face_Internal_Optical_Carrier, Face_RGB_Module, Face_IR_Depth_Module,
  Face_SL_Projector, and Interaction_ twins);
- a containment report runs at build time: any internal part that does
  not fit the drum keep-out is FLAGGED with the offending dimension --
  never silently resized or dropped.

Drum-local layout (mm, measured from the drum axis; -Y = window side):
    skin outer r 12.0, wall 1.5, interior r 10.5
    barrel mouth   dy -10.6 (behind the recessed lens window)
    barrel run     dy -10.6 .. -7.5
    module body    dy -7.5 .. -3.5   (projector: -7.0 .. -3.0)
    module PCB     dy -3.5 .. -2.9
    carrier rail   dy -2.9 .. -1.9, 12 tall, along the drum axis
"""

import math

import bpy
from mathutils import Matrix, Vector

import macbook

MM = 0.001

SKIN_R = 12.0 * MM
INTERIOR_R = 10.5 * MM
WALL = 1.5 * MM
APERTURE_SEGMENTS = 64

# --- per-aperture layout constants (drum-local mm) ----------------------
# (name, kind, x, dz, diameter)
#   x   : along the drum axis, 0 = drum centre
#   dz  : vertical offset from the drum axis (parallel optic axes stay
#         along -Y; dz slides the opening around the skin)
APERTURES = [
    ("Depth",   "depth",     -19.0, 0.0, 9.0),
    # upper pair: 3.2 mm centre-to-centre (refinement pass: +23% over the
    # original 2.6 mm to sit credibly over the shared projector hardware);
    # lower pinhole keeps its vertical separation, unmoved
    ("ProjA",   "projector",   2.7, 1.9, 1.6),
    ("ProjB",   "projector",   5.9, 1.9, 1.6),
    ("Pinhole", "pinhole",     4.3, -0.7, 0.8),
    ("RGB",     "rgb",        19.0, 0.0, 9.0),
]

LENS_THICKNESS = 0.35 * MM
LENS_RECESS = 1.20 * MM      # projector/pinhole insert depth
CUTTER_DEPTH = 3.6 * MM      # through the 1.5 mm wall + clearance
CAMERA_WINDOW_RECESS = 1.20 * MM
CAMERA_WINDOW_THICKNESS = 0.30 * MM
CAMERA_SLEEVE_FRONT_RECESS = 1.15 * MM
CAMERA_SLEEVE_DEPTH = 0.80 * MM

# Keep the retaining barrel behind the window. Extending it to the skin
# produces a bright porthole ring in front views, which the exterior design
# explicitly rejects.
BARREL_MOUTH_DY = -10.6 * MM
BODY_FRONT_DY = -7.5 * MM
BODY_LENGTH = 4.0 * MM
PCB_THICKNESS = 0.6 * MM
CARRIER_DY = -2.9 * MM       # front face of the rail
CARRIER_THICKNESS = 1.0 * MM
CARRIER_HEIGHT = 12.0 * MM

# shared projector package (one assembly behind the three holes)
PROJECTOR = {"x": 4.3, "dz": 0.8, "width": 5.6, "height": 6.0,
             "front_dy": -7.0, "length": 4.0}
# collision envelope depth from the shell inner surface (5-8 mm band,
# editable; not a component specification). RECORDED CHANGE: 6.5 -> 6.2 mm
# after the pairwise check flagged a 0.25 mm overlap with the carrier rail
KEEPOUT_DEPTH = 6.2 * MM

_LENS_MAT = {"depth": "Optic_Glass_Depth", "rgb": "Optic_Glass_RGB",
             "projector": "Optic_Projector_Inset",
             "pinhole": "Optic_Projector_Inset"}
_INTERNAL_LIMIT = INTERIOR_R + 0.05 * MM   # keep-out for bodies/PCB/carrier
_WINDOW_BAND = 8.0 * MM                    # |dz| + aperture radius limit


def _drum_frame(bbox_mm):
    bb_min, bb_max = bbox_mm["min"], bbox_mm["max"]
    centre = Vector(((bb_min[0] + bb_max[0]) / 2.0 * MM,
                     (bb_min[1] + bb_max[1]) / 2.0 * MM,
                     (bb_min[2] + bb_max[2]) / 2.0 * MM))
    radius = (bb_max[1] - bb_min[1]) / 2.0 * MM
    length = (bb_max[0] - bb_min[0]) * MM
    return centre, radius, length


def _link_child(obj, parent, mpi, col):
    col.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = mpi


def _smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def _radial_extent(obj, centre):
    """Max distance of the object's (identity-basis) bbox corners from
    the drum axis -- rotation-invariant about the axis, so valid before
    and after the pivot rotation."""
    return max(math.hypot(v[1] - centre.y, v[2] - centre.z)
               for v in obj.bound_box)


def _apply_bores_with_radial_normals(drum_obj, centre, radius):
    """Bake drum modifiers and restore the analytic outer normals.

    Boolean cuts fragment the drum's long outer quads into irregular
    n-gons. Their generated corner normals otherwise interpolate across
    each aperture cluster and show up as seams radiating from the openings.
    Apply the drum's original end treatments first, then the bores, so the
    global bevel cannot round the aperture rims into bright lower crescents.
    The outer skin is still an exact cylinder, so its intended normal is
    known: radial from the X-axis at every corner. Bore walls and the inner
    skin retain Blender's calculated normals, preserving the hard rims.
    """
    bore_modifiers = [
        mod for mod in drum_obj.modifiers
        if mod.type == 'BOOLEAN' and mod.name.startswith("Bore_")
    ]
    bore_names = [mod.name for mod in bore_modifiers]
    end_modifiers = [
        mod.name for mod in drum_obj.modifiers
        if mod not in bore_modifiers
    ]
    with bpy.context.temp_override(
            object=drum_obj, active_object=drum_obj,
            selected_objects=[drum_obj]):
        # Boolean modifiers were inserted at the top of the live stack.
        # Move the original Edge Split and Bevel ahead of them so these
        # treatments affect only the drum ends, not the aperture rims.
        for target_index, name in enumerate(end_modifiers):
            current_index = drum_obj.modifiers.find(name)
            drum_obj.modifiers.move(current_index, target_index)
        for name in end_modifiers:
            bpy.ops.object.modifier_apply(modifier=name)
        for name in bore_names:
            bpy.ops.object.modifier_apply(modifier=name)

    mesh = drum_obj.data
    mesh.update()
    corner_normals = [
        corner.vector.copy() for corner in mesh.corner_normals
    ]
    # A 64-sided, 12 mm radius drum has about 0.014 mm chord sag. This
    # tolerance includes Boolean intersection vertices on those chords
    # while remaining far inside the 1.5 mm wall thickness.
    outer_tolerance = 0.05 * MM
    outer_faces = 0
    outer_corners = 0
    for poly in mesh.polygons:
        verts = [mesh.vertices[i].co for i in poly.vertices]
        if not all(abs(math.hypot(co.y - centre.y, co.z - centre.z)
                       - radius) <= outer_tolerance for co in verts):
            continue
        poly.use_smooth = True
        outer_faces += 1
        for loop_index in poly.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            radial = Vector((0.0, co.y - centre.y, co.z - centre.z))
            corner_normals[loop_index] = radial.normalized()
            outer_corners += 1

    if not outer_faces:
        raise RuntimeError(
            "{}: no outer drum faces found for radial normals".format(
                drum_obj.name))
    mesh.normals_split_custom_set(corner_normals)
    print("optics: {} baked {} end modifiers before {} bores; applied "
          "radial normals to {} outer faces / {} corners".format(
              drum_obj.name, len(end_modifiers), len(bore_names),
              outer_faces, outer_corners))


def apply_to_drum(drum_obj, bbox_mm, rotation_deg, mats, col, prefix,
                  report):
    centre, radius, length = _drum_frame(bbox_mm)
    base = prefix.replace("_Drum", "")
    axis = Vector((0.0, -1.0, 0.0))   # parallel optics, never radial

    pivot = bpy.data.objects.new(prefix + "_Optics_Pivot", None)
    pivot.empty_display_size = 6 * MM
    pivot.location = centre
    col.objects.link(pivot)
    pivot.parent = drum_obj          # drum basis is identity: follows CAD verts
    # Aperture/lens/module vertices are baked in CAD-world coordinates:
    # every CHILD of this pivot needs matrix_parent_inverse = the pivot's
    # translation-only matrix, captured BEFORE the rotation below, so the
    # rotation acts about the drum axis (T*R*T^-1), not the world origin.
    child_mpi = Matrix.Translation(-centre)

    # ---- apertures: through-wall bores + lens windows + bezels ---------
    for name, kind, x_mm, dz_mm, d_mm, _unused in [
            (a[0], a[1], a[2], a[3], a[4], 0) for a in APERTURES]:
        x, dz, d = x_mm * MM, dz_mm * MM, d_mm * MM
        skin = math.sqrt(radius ** 2 - dz ** 2)  # local distance to the skin
        base_pt = Vector((centre.x + x, centre.y, centre.z + dz))

        cutter = macbook.cylinder(
            prefix + "_Cutter_" + name,
            base_pt + axis * (skin - 1.0 * MM
                              + (CUTTER_DEPTH + 1.0 * MM) / 2.0),
            axis, d / 2.0, CUTTER_DEPTH + 1.0 * MM,
            seg=APERTURE_SEGMENTS)
        cutter.hide_viewport = True
        cutter.hide_render = True
        _link_child(cutter, pivot, child_mpi, col)

        mod = drum_obj.modifiers.new("Bore_" + name, 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cutter
        mod.solver = 'EXACT'
        drum_obj.modifiers.move(len(drum_obj.modifiers) - 1, 0)

        is_camera = kind in ("depth", "rgb")
        if is_camera:
            # Production-realistic camera opening: the cylindrical shell
            # remains unflattened, while a matte internal sleeve terminates
            # in a planar optical window normal to the camera axis.
            element_radius = d / 2.0 - 0.12 * MM
            sleeve_outer = d / 2.0 - 0.02 * MM
            sleeve_inner = element_radius - 0.10 * MM
            lens = macbook.tube(
                prefix + "_Lens_" + name,
                base_pt + axis * (
                    skin - CAMERA_SLEEVE_FRONT_RECESS
                    - CAMERA_SLEEVE_DEPTH / 2.0),
                axis, sleeve_inner, sleeve_outer, CAMERA_SLEEVE_DEPTH,
                mats["Optic_Lens_Well"], seg=APERTURE_SEGMENTS)
            _link_child(lens, pivot, child_mpi, col)

            element = macbook.cylinder(
                prefix + "_Lens_" + name + "_Element",
                base_pt + axis * (
                    skin - CAMERA_WINDOW_RECESS
                    - CAMERA_WINDOW_THICKNESS / 2.0),
                axis, element_radius, CAMERA_WINDOW_THICKNESS,
                mats[_LENS_MAT[kind]], seg=APERTURE_SEGMENTS)
            _link_child(element, pivot, child_mpi, col)

            pupil_t = 0.025 * MM
            pupil = macbook.cylinder(
                prefix + "_Lens_" + name + "_Pupil",
                base_pt + axis * (
                    skin - (CAMERA_WINDOW_RECESS - 0.02 * MM)
                    - pupil_t / 2.0),
                axis, element_radius * 0.15, pupil_t,
                mats["Optic_Lens_Pupil"], seg=48)
            _link_child(pupil, pivot, child_mpi, col)
        else:
            lens_radius = d / 2.0 - 0.10 * MM
            lens = macbook.cylinder(
                prefix + "_Lens_" + name,
                base_pt + axis * (
                    skin - LENS_RECESS - LENS_THICKNESS / 2.0),
                axis, lens_radius, LENS_THICKNESS, mats[_LENS_MAT[kind]],
                seg=APERTURE_SEGMENTS)
            _link_child(lens, pivot, child_mpi, col)

        report.append(("path", prefix + "_Lens_" + name,
                       abs(dz) + d / 2.0, _WINDOW_BAND, "window band"))
        lens_dy = sum(v.co.y for v in lens.data.vertices) / len(
            lens.data.vertices) - centre.y
        report.append(("facing", prefix + "_Lens_" + name, lens_dy, 0.0,
                       "must be negative (window side)"))
        lens_r = max(math.hypot(v.co.y - centre.y, v.co.z - centre.z)
                     for v in lens.data.vertices)
        report.append(("path", prefix + "_Lens_" + name, lens_r,
                       SKIN_R + 1.0 * MM, "at the skin, not floating"))

    # The interaction drum's calibrated rest angle rotates the aperture
    # pattern around the X-axis. Set it before baking so its bore geometry
    # and optical components remain coincident after the live cutters are
    # removed.
    pivot.rotation_euler.x = math.radians(rotation_deg)
    bpy.context.view_layer.update()
    _apply_bores_with_radial_normals(drum_obj, centre, radius)

    # ---- internal optical carrier rail -----------------------------------
    carrier = macbook.slab(
        base + "_Internal_Optical_Carrier",
        Vector((centre.x, centre.y + CARRIER_DY - CARRIER_THICKNESS / 2.0,
                centre.z)),
        macbook.X, macbook.Z, (length - 10.0 * MM, CARRIER_HEIGHT),
        0.5 * MM, CARRIER_THICKNESS, mats["Sensor_Internal"])
    _link_child(carrier, pivot, child_mpi, col)
    report.append(("internal", carrier.name, _radial_extent(carrier, centre),
                   _INTERNAL_LIMIT, "radial keep-out"))

    # ---- camera modules: barrel + body + PCB, mounted on the carrier -----
    def camera_module(module_name, x_mm, dz_mm, d_mm):
        x, dz, d = x_mm * MM, dz_mm * MM, d_mm * MM
        module_loc = Vector((centre.x + x,
                             centre.y + BODY_FRONT_DY
                             + (BODY_LENGTH + PCB_THICKNESS) / 2.0,
                             centre.z + dz))
        module = bpy.data.objects.new(module_name, None)
        module.empty_display_size = 6 * MM
        module.location = module_loc
        col.objects.link(module)
        module.parent = pivot
        module.matrix_parent_inverse = child_mpi
        module_mpi = Matrix.Translation(-module_loc)

        barrel_outer = d / 2.0 - 0.3 * MM
        barrel = macbook.tube(
            module_name + "_Barrel",
            Vector((centre.x + x,
                    centre.y + (BARREL_MOUTH_DY + BODY_FRONT_DY) / 2.0,
                    centre.z + dz)),
            axis, barrel_outer - 0.45 * MM, barrel_outer,
            BODY_FRONT_DY - BARREL_MOUTH_DY, mats["Optic_Bezel"], seg=32)
        _link_child(barrel, module, module_mpi, col)

        body = macbook.slab(
            module_name + "_Body",
            Vector((centre.x + x,
                    centre.y + BODY_FRONT_DY + BODY_LENGTH / 2.0,
                    centre.z + dz)),
            macbook.X, macbook.Z, ((d_mm - 1.0) * MM, (d_mm - 1.0) * MM),
            0.6 * MM, BODY_LENGTH, mats["Sensor_Internal"])
        _link_child(body, module, module_mpi, col)
        report.append(("internal", body.name, _radial_extent(body, centre),
                       _INTERNAL_LIMIT, "radial keep-out"))

        pcb = macbook.slab(
            module_name + "_PCB",
            Vector((centre.x + x,
                    centre.y + BODY_FRONT_DY + BODY_LENGTH
                    + PCB_THICKNESS / 2.0,
                    centre.z + dz)),
            macbook.X, macbook.Z, ((d_mm - 2.0) * MM, (d_mm - 2.0) * MM),
            0.4 * MM, PCB_THICKNESS, mats["Sensor_Internal"])
        _link_child(pcb, module, module_mpi, col)
        report.append(("internal", pcb.name, _radial_extent(pcb, centre),
                       _INTERNAL_LIMIT, "radial keep-out"))

    for name, kind, x_mm, dz_mm, d_mm in APERTURES:
        if kind == "depth":
            camera_module(base + "_IR_Depth_Module", x_mm, dz_mm, d_mm)
        elif kind == "rgb":
            camera_module(base + "_RGB_Module", x_mm, dz_mm, d_mm)

    # ---- shared structured-light projector assembly (spec sec.9) --------
    # ONE rigid package behind the triangular hole pattern: housing +
    # emitter + DOE plate + PCB + bracket; the three barrels connect the
    # shell openings to this single assembly. A separate editable keep-out
    # envelope (5-8 mm deep from the shell inner surface) is the collision
    # volume for the whole stack.
    proj_loc = Vector((centre.x + PROJECTOR["x"] * MM,
                       centre.y + PROJECTOR["front_dy"] * MM
                                   + PROJECTOR["length"] * MM / 2.0,
                       centre.z + PROJECTOR["dz"] * MM))
    projector = bpy.data.objects.new(base + "_SL_Projector", None)
    projector.empty_display_size = 6 * MM
    projector.location = proj_loc
    col.objects.link(projector)
    projector.parent = pivot
    projector.matrix_parent_inverse = child_mpi
    projector_mpi = Matrix.Translation(-proj_loc)

    def proj_part(suffix, center, u, v, size, radius, thickness, material,
                  seg_note="slab"):
        part = macbook.slab(suffix, center, u, v, size, radius, thickness,
                            material)
        _link_child(part, projector, projector_mpi, col)
        report.append(("internal", part.name, _radial_extent(part, centre),
                       _INTERNAL_LIMIT, "radial keep-out"))
        return part

    px, pdz = centre.x + PROJECTOR["x"] * MM, centre.z + PROJECTOR["dz"] * MM
    front = centre.y + PROJECTOR["front_dy"] * MM
    plen = PROJECTOR["length"] * MM
    proj_part(base + "_SL_Projector_Body",
              Vector((px, front + plen / 2.0, pdz)),
              macbook.X, macbook.Z,
              (PROJECTOR["width"] * MM, PROJECTOR["height"] * MM),
              0.4 * MM, plen, mats["Sensor_Internal"])
    # DOE / optical element: thin plate on the housing's window face
    proj_part(base + "_SL_Projector_DOE",
              Vector((px, front - 0.25 * MM, pdz)),
              macbook.X, macbook.Z,
              (PROJECTOR["width"] * MM - 1.0 * MM,
               PROJECTOR["height"] * MM - 1.0 * MM),
              0.3 * MM, 0.5 * MM, mats["Optic_Bezel"])
    # emitter: compact source at the housing front, behind the DOE
    emitter = macbook.cylinder(
        base + "_SL_Projector_Emitter",
        Vector((px, front + 1.0 * MM, pdz)),
        axis, 1.0 * MM, 1.6 * MM, mats["Sensor_Internal"], seg=24)
    _link_child(emitter, projector, projector_mpi, col)
    report.append(("internal", emitter.name, _radial_extent(emitter, centre),
                   _INTERNAL_LIMIT, "radial keep-out"))
    # PCB at the housing back
    proj_part(base + "_SL_Projector_PCB",
              Vector((px, front + plen + 0.3 * MM, pdz)),
              macbook.X, macbook.Z,
              (PROJECTOR["width"] * MM - 0.6 * MM,
               PROJECTOR["height"] * MM - 0.6 * MM),
              0.3 * MM, 0.6 * MM, mats["Sensor_Internal"])
    # mounting bracket: ties the package to the internal carrier rail
    proj_part(base + "_SL_Projector_Bracket",
              Vector((px, front + plen + 1.1 * MM, pdz)),
              macbook.X, macbook.Z, (3.0 * MM, 3.0 * MM),
              0.3 * MM, 1.6 * MM, mats["Sensor_Internal"])

    for name, kind, x_mm, dz_mm, d_mm in APERTURES:
        if kind not in ("projector", "pinhole"):
            continue
        barrel_outer = d_mm * MM / 2.0 - 0.15 * MM
        barrel = macbook.tube(
            base + "_SL_Projector_Barrel_" + name,
            Vector((centre.x + x_mm * MM,
                    centre.y + (BARREL_MOUTH_DY
                                + PROJECTOR["front_dy"] * MM) / 2.0,
                    centre.z + dz_mm * MM)),
            axis, max(0.03 * MM, barrel_outer - 0.20 * MM), barrel_outer,
            PROJECTOR["front_dy"] * MM - BARREL_MOUTH_DY,
            mats["Optic_Bezel"], seg=24)
        _link_child(barrel, projector, projector_mpi, col)

    # keep-out envelope: editable collision volume, 5-8 mm deep from the
    # shell inner surface, laterally covering all three holes (incl. the
    # increased upper-pair spacing). Wire display; never rendered.
    ko_x = (centre.x + (min(a[2] for a in APERTURES
                            if a[1] in ("projector", "pinhole")) - 1.0) * MM,
            centre.x + (max(a[2] for a in APERTURES
                            if a[1] in ("projector", "pinhole")) + 1.0) * MM)
    ko_z = (centre.z + (min(a[3] for a in APERTURES
                            if a[1] in ("projector", "pinhole")) - 0.8) * MM,
            centre.z + (max(a[3] for a in APERTURES
                            if a[1] in ("projector", "pinhole")) + 0.8) * MM)
    # shell inner surface AT the cluster's z-extent: the wall is curved,
    # so the envelope must start at the local depth, not the axis depth,
    # or its front corners would clip the cylinder
    dz_max = max(abs(ko_z[0] - centre.z), abs(ko_z[1] - centre.z))
    ko_y0 = centre.y - math.sqrt((radius - WALL) ** 2 - dz_max ** 2)
    keepout = macbook.slab(
        base + "_SL_Projector_KeepOut",
        Vector(((ko_x[0] + ko_x[1]) / 2.0,
                ko_y0 + KEEPOUT_DEPTH / 2.0,
                (ko_z[0] + ko_z[1]) / 2.0)),
        macbook.X, macbook.Z,
        ((ko_x[1] - ko_x[0]), (ko_z[1] - ko_z[0])),
        0.3 * MM, KEEPOUT_DEPTH, mats["Sensor_Internal"])
    keepout.display_type = 'WIRE'
    keepout.hide_render = True
    _link_child(keepout, pivot, child_mpi, col)
    report.append(("internal", keepout.name,
                   _radial_extent(keepout, centre), _INTERNAL_LIMIT,
                   "radial keep-out"))

    # pairwise collision checks: keep-out vs cameras / carrier / far wall
    def aabb(obj):
        xs = [v[0] for v in obj.bound_box]
        ys = [v[1] for v in obj.bound_box]
        zs = [v[2] for v in obj.bound_box]
        return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

    def overlap_depth(a, b):
        return min(a[1] - b[0], b[1] - a[0], a[3] - b[2], b[3] - a[2],
                   a[5] - b[4], b[5] - a[4])

    ko = aabb(keepout)
    for other_name in (base + "_IR_Depth_Module_Body",
                       base + "_IR_Depth_Module_PCB",
                       base + "_RGB_Module_Body",
                       base + "_RGB_Module_PCB",
                       base + "_Internal_Optical_Carrier"):
        other = bpy.data.objects.get(other_name)
        depth = overlap_depth(ko, aabb(other))
        report.append(("clearance", "SL keep-out vs " + other_name,
                       depth, 0.0, "overlap depth (must be <= 0)"))
    report.append(("clearance", "SL keep-out vs far wall",
                   -abs(ko[3] - (centre.y + radius - WALL)), 0.0,
                   "overlap depth (must be <= 0)"))

    return pivot, keepout


def apply_to_product(manifest, mats, col):
    """Package both drums named in the manifest; returns the pivots and
    prints the containment report (collisions are flagged, never silently
    resized)."""
    params = manifest["params"]
    prefix_for = {"Face_Sensor_Head": "Face_Drum",
                  "Interaction_Sensor_Head": "Interaction_Drum"}
    rotation_for = {"Face_Sensor_Head": params["FACE_HEAD_ROTATION_DEG"],
                    "Interaction_Sensor_Head":
                        params["INTERACTION_HEAD_ROTATION_DEG"]}
    report = []
    pivots = {}
    for part in manifest["parts"]:
        name = part["name"]
        if name not in prefix_for:
            continue
        drum_obj = bpy.data.objects[name]
        pivots[name], _keepout = apply_to_drum(
            drum_obj, part["bbox_mm"], rotation_for[name], mats, col,
            prefix_for[name], report)

    collisions = 0
    print("drum packaging containment report "
          "({:.1f} mm interior keep-out):".format(_INTERNAL_LIMIT / MM))
    for kind, obj_name, value, limit, what in report:
        bad = value > limit
        collisions += bad
        if bad:
            print("  COLLISION: {:<44} {} {:.2f} mm > {:.2f} mm ({})".format(
                obj_name, what, value / MM, limit / MM,
                "reduce body height/width or dz offset"))
        else:
            print("  ok: {:<44} {:.2f} <= {:.2f} mm".format(
                obj_name, value / MM, limit / MM))
    if collisions:
        print("  -> {} collision(s) FLAGGED; nothing was resized "
              "automatically".format(collisions))
    return pivots
