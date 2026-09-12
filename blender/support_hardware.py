"""Concept mounting hardware connecting internal assemblies to the shell."""

import macbook
from mathutils import Vector

from assembly_primitives import MM, box, cylinder, link_only, material, tag


def _routing_clip(name, center, outer, inner, height, mat, collection,
                  subsystem, evidence):
    """Create an open cable channel instead of a solid placeholder block."""
    obj = macbook.frame(
        name, Vector(tuple(value * MM for value in center)),
        macbook.X, macbook.Y,
        tuple(value * MM for value in outer), 0.55 * MM,
        tuple(value * MM for value in inner), 0.35 * MM,
        height * MM, mat)
    link_only(obj, collection)
    obj["Channel_Clearance_mm"] = (
        "{:.2f} x {:.2f}".format(inner[0], inner[1]))
    return tag(obj, subsystem, evidence)


def build(collection):
    """Build removable brackets/standoffs as a distinct presentation layer."""
    bracket = material("Support_Bracket", (0.12, 0.14, 0.16),
                       metallic=0.82, roughness=0.38)
    fastener = material("Support_Fastener", (0.48, 0.50, 0.53),
                        metallic=0.96, roughness=0.24)
    ground = material("Support_Grounded_Clip", (0.58, 0.60, 0.62),
                      metallic=0.94, roughness=0.27)
    relief = material("Support_Strain_Relief", (0.08, 0.09, 0.10),
                      roughness=0.64)
    objects = []

    # Four rear standoffs retain the stationary PCBA without occupying the
    # central thermal-transfer area.
    for x_label, x in (("L", -42.0), ("R", 42.0)):
        for z_label, z in (("B", -22.5), ("T", -0.5)):
            post = cylinder("PCBA_Standoff_{}_{}".format(x_label, z_label),
                            (x, 19.15, z), Vector((0.0, 1.0, 0.0)),
                            1.7, 4.0, bracket, collection, segments=32)
            post["Mounting_Interface"] = "Seats against rear PCB face"
            objects.append(tag(post, "Internal mounting",
                               "CONCEPT STANDOFF"))
            screw = cylinder("PCBA_Fastener_{}_{}".format(x_label, z_label),
                             (x, 15.0, z), Vector((0.0, 1.0, 0.0)),
                             1.15, 1.1, fastener, collection, segments=32)
            screw["Mounting_Interface"] = "Seats against front PCB face"
            objects.append(tag(screw, "Internal mounting",
                               "CONCEPT FASTENER"))

    # These carrier blocks represent the housing interfaces for the two
    # outer drum bearings. Their final molded shape remains open.
    for label, x in (("Face", -54.2), ("Interaction", 54.2)):
        carrier = box("{}_Bearing_Carrier".format(label),
                      (x, 6.6, 20.0), (6.0, 2.4, 15.0), 1.2,
                      bracket, collection)
        objects.append(tag(carrier, "Internal mounting",
                           "CONCEPT BEARING CARRIER"))

    # Each side has a divider and fitted channels for the actual data and
    # power/motion routes. Unlike the old solid blocks, these parts surround
    # the cables without occupying the cable volume.
    for label, sign in (("Face", -1.0), ("Interaction", 1.0)):
        divider = box(label + "_Lane_Grounded_Divider",
                      (sign * 50.75, 9.75, -10.0),
                      (0.45, 5.5, 25.0), 0.20, ground, collection)
        objects.append(tag(divider, "Cable lane support",
                           "GROUNDED-DIVIDER CONCEPT"))

        data_clip = _routing_clip(
            label + "_Data_Lane_Grounded_Clip",
            (sign * 48.2, 9.0, -11.0),
            (6.0, 5.4), (4.8, 4.2), 3.2, ground, collection,
            "Camera cable support", "GROUNDED-CHANNEL CONCEPT")
        objects.append(data_clip)
        power_clip = _routing_clip(
            label + "_Power_Motion_Lane_Grounded_Clip",
            (sign * 53.0, 12.0, -11.0),
            (5.6, 5.2), (4.4, 4.0), 3.2, ground, collection,
            "Power/motion cable support", "GROUNDED-CHANNEL CONCEPT")
        objects.append(power_clip)

        boundary = _routing_clip(
            label + "_Boundary_Ground_Clamp",
            (sign * 50.5, 10.5, -18.5),
            (10.8, 10.0), (9.4, 8.6), 2.4, ground, collection,
            "Shield boundary clamp", "GROUND-TERMINATION CHANNEL")
        boundary["Grounding_Intent"] = (
            "Cable shield termination at electronics enclosure boundary")
        objects.append(boundary)

        for location, x, y, z, outer, inner in (
            ("Drum_Data", sign * 48.2, 9.0, 4.5,
             (6.0, 5.4), (4.8, 4.2)),
            ("Drum_Power", sign * 53.0, 12.0, 4.5,
             (5.6, 5.2), (4.4, 4.0)),
            ("PCBA_Data", sign * 48.2, 9.0, -14.5,
             (6.0, 5.4), (4.8, 4.2)),
            ("PCBA_Power", sign * 53.0, 12.0, -14.5,
             (5.6, 5.2), (4.4, 4.0)),
        ):
            strain = _routing_clip(
                "{}_{}_Strain_Relief".format(label, location),
                (x, y, z), outer, inner, 2.8, relief, collection,
                "Cable strain relief", "FITTED SERVICEABILITY CHANNEL")
            objects.append(strain)

    return objects
