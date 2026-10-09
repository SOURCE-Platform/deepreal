"""Side-supported rotating-drum, motor, bearing and flex envelopes."""

import bpy
from mathutils import Vector

import macbook
from assembly_primitives import box, cylinder, routed_wire, tube, wire
from r21_chassis import material

MM = .001
AXIS = (-1.5, 20.0)


def remove_superseded():
    removed = []
    for collection in bpy.data.collections:
        if "FIXED DRIVE + SUPPORT" in collection.name:
            for obj in list(collection.objects):
                removed.append(obj.name)
                bpy.data.objects.remove(obj, do_unlink=True)
    for side, outer_end in (("Face", "Left"),
                            ("Interaction", "Right")):
        for suffix in ("Ring_Gear", "Drum_Axle", "Encoder_Magnet",
                       "Sensor_Head_Flat_End_" + outer_end,
                       "Sensor_Head_Flat_End_" + (
                           "Right" if outer_end == "Left" else "Left")):
            obj = bpy.data.objects.get(side + "_" + suffix)
            if obj:
                removed.append(obj.name)
                bpy.data.objects.remove(obj, do_unlink=True)
        for suffix in ("Head_Power_Data_Flex_ROUTE_CONCEPT",
                       "Motor_Power_Harness_ROUTE_CONCEPT",
                       "Encoder_Feedback_ROUTE_CONCEPT"):
            obj = bpy.data.objects.get(side + "_" + suffix)
            if obj:
                removed.append(obj.name)
                bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def rotating(obj, pivot, note):
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    obj["R21_Role"] = "rotating with drum"
    obj["R21_Status"] = note
    return obj


def fixed(obj, note):
    obj["R21_Role"] = "fixed to enclosure support"
    obj["R21_Status"] = note
    return obj


def add_mechanisms(scene):
    collection = bpy.data.collections.new("12 — R21 SIDE BEARINGS AND INTERNAL DRIVES")
    scene.collection.children.link(collection)
    collection.color_tag = "COLOR_05"
    shell_mat = bpy.data.objects["Face_Sensor_Head"].data.materials[0]
    steel = material("R21_Bearing_Stainless_Envelope", (.42, .47, .5, 1), .7, .26)
    dark = material("R21_Internal_Drive_Graphite", (.06, .075, .08, 1), .35, .39)
    amber = material("R21_Flex_Amber_Concept", (.7, .3, .05, 1), .0, .5)
    pcb = material("R21_Encoder_PCB_Green", (.03, .18, .12, 1), .05, .55)
    magnet_mat = material("R21_Encoder_Magnet", (.27, .31, .33, 1), .55, .32)
    built = []
    for side, sign in (("Face", -1), ("Interaction", 1)):
        pivot = bpy.data.objects[side + "_Rotating_Drum_Pivot_R15"]
        pivot.location.x += sign * 2 * MM
        pivot["R21_Provisional_Optical_Directions_deg"] = (
            [-45, 0, 45] if side == "Face" else [0, 22.5, 45])
        pivot["R21_Stop_Status"] = "poses only; no physical hard stop"
        bpy.context.view_layer.update()

        # A broad open inner end lets the fixed motor bracket enter from the
        # center support without a slot through the rotating sidewall.
        inner = tube(side + "_Open_Inner_End_Ring_R21",
                     (sign * 2.75, *AXIS), macbook.X,
                     9.15, 11.94, 1.10, shell_mat, collection, 96)
        outer = tube(side + "_Flat_Outer_End_R21",
                     (sign * 56.1, *AXIS), macbook.X,
                     2.35, 12.0, .25, shell_mat, collection, 96)
        for obj in (inner, outer):
            built.append(rotating(obj, pivot,
                "visual shell end; attachment and sealing unverified"))

        # Inner race fixed to the divider, outer race represented as a
        # rotating annulus attached to the drum's inner lip.
        fixed_inner = tube(side + "_Inner_Bearing_Fixed_Race_ENV_R21",
                           (sign * 3.8, *AXIS), macbook.X,
                           8.45, 9.05, 1.5, steel, collection, 96)
        moving_inner = tube(side + "_Inner_Bearing_Rotating_Race_ENV_R21",
                            (sign * 3.8, *AXIS), macbook.X,
                            9.30, 10.15, 1.5, steel, collection, 96)
        built.append(fixed(fixed_inner, "large bearing envelope, not a selected part"))
        built.append(rotating(moving_inner, pivot,
                              "rotating bearing race envelope; drum coupling open"))
        # Two recessed webs connect the fixed race to the divider. Their
        # radial envelope stays inside the open rotating lip during travel.
        for label, z, tab_z in (("Upper", 27.3, 28.0),
                                ("Lower", 12.7, 12.0)):
            bridge = box(side + "_Inner_Race_" + label + "_Web_R21",
                         (sign * 2.25, -1.5, z), (1.5, 1.5, 2.0),
                         .2, steel, collection)
            tab = box(side + "_Inner_Race_" + label + "_Tab_R21",
                      (sign * 3.5, -1.5, tab_z), (1.0, 1.5, 2.2),
                      .2, steel, collection)
            built.extend((fixed(bridge, "center-divider bearing web concept"),
                          fixed(tab, "bearing-race mounting tab concept")))

        # Outer spindle is hollow; the moving flex meets it near the axis.
        spindle = tube(side + "_Outer_Hollow_Fixed_Spindle_ENV_R21",
                       (sign * 56.5, *AXIS), macbook.X,
                       1.0, 2.0, 6.2, steel, collection, 64)
        bearing = tube(side + "_Outer_Bearing_ENV_R21",
                       (sign * 54.9, *AXIS), macbook.X,
                       2.08, 3.50, 1.8, steel, collection, 64)
        hub = tube(side + "_Outer_Rotating_Hub_R21",
                   (sign * 54.9, *AXIS), macbook.X,
                   3.62, 5.4, 2.0, dark, collection, 64)
        built.extend((fixed(spindle, "hollow cable feed; bend life unverified"),
                      fixed(bearing, "bearing envelope, not a selected part"),
                      rotating(hub, pivot, "hub attachment to end face unverified")))

        # The encoder stays inside the narrow drum/support joint. Its magnet
        # rotates with the end face; the board and Hall IC stay on the cheek.
        encoder_magnet = cylinder(side + "_End_Encoder_Magnet_R21",
                                  (sign * 56.35, 4.5, 20), macbook.X,
                                  1.0, .50, magnet_mat, collection, 32)
        encoder_board = box(side + "_End_Encoder_PCB_ENV_R21",
                            (sign * 57.0, 4.5, 20), (.4, 3.4, 3.4),
                            .12, pcb, collection)
        encoder_ic = box(side + "_End_Encoder_IC_ENV_R21",
                         (sign * 56.74, 4.5, 20), (.18, 1.15, 1.15),
                         .06, dark, collection)
        built.extend((rotating(encoder_magnet, pivot,
                              "encoder magnet; angular datum unverified"),
                      fixed(encoder_board, "board recess and mounting unmodeled"),
                      fixed(encoder_ic, "Hall encoder envelope; IC unselected")))

        motor = cylinder(side + "_Center_Fed_Motor_Stator_ENV_R21",
                         (sign * 9.7, 5.0, 20), macbook.X,
                         3.0, 9.2, dark, collection, 64)
        mount = box(side + "_Motor_Cantilever_R21",
                    (sign * 3.4, 5.0, 20), (6.8, 3.2, 3.2),
                    .4, steel, collection)
        pinion = cylinder(side + "_Motor_Pinion_ENV_R21",
                          (sign * 15.2, 5.0, 20), macbook.X,
                          2.4, 1.7, steel, collection, 48)
        ring = tube(side + "_Internal_Ring_Gear_ENV_R21",
                    (sign * 15.2, *AXIS), macbook.X,
                    9.0, 10.4, 1.7, dark, collection, 96)
        for obj in (motor, mount, pinion):
            built.append(fixed(obj, "motor/gear envelope; torque, teeth and fastening open"))
        built.append(rotating(ring, pivot,
                              "ring gear envelope; tooth and shell coupling open"))

        # The moving and fixed pieces are deliberately separate to mark the
        # unresolved dynamic-flex transition at the hollow outer spindle.
        moving_flex = wire(side + "_Moving_Head_Flex_PROXY_R21",
                           [(sign * 36, -5.5, 20), (sign * 48, -4, 21),
                            (sign * 52, -.5, 20), (sign * 54.2, -1.5, 20)],
                           .30, amber, collection)
        moving_flex.parent = pivot
        moving_flex.matrix_parent_inverse = pivot.matrix_world.inverted()
        moving_flex["R21_Status"] = "rest-pose flex proxy; bend sweep unverified"
        fixed_flex = routed_wire(side + "_Fixed_Harness_PROXY_R21",
                                 [(sign * 54.3, -1.5, 20),
                                  (sign * 58.3, -1.5, 20),
                                  (sign * 58.3, 4.5, 15),
                                  (sign * 58.3, 12, 6),
                                  (sign * 51, 12, -18)],
                                 .18, .8, amber, collection)
        fixed_flex["R21_Status"] = "schematic fixed harness to main PCBA"
        built.extend((moving_flex, fixed_flex))
    return built
