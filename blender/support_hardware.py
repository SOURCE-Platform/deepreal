"""Concept mounting hardware connecting internal assemblies to the shell."""

from mathutils import Vector

from assembly_primitives import box, cylinder, material, tag


def build(collection):
    """Build removable brackets/standoffs as a distinct presentation layer."""
    bracket = material("Support_Bracket", (0.12, 0.14, 0.16),
                       metallic=0.82, roughness=0.38)
    fastener = material("Support_Fastener", (0.48, 0.50, 0.53),
                        metallic=0.96, roughness=0.24)
    objects = []

    # Four rear standoffs retain the stationary PCBA without occupying the
    # central thermal-transfer area.
    for x_label, x in (("L", -42.0), ("R", 42.0)):
        for z_label, z in (("B", -22.5), ("T", -0.5)):
            post = cylinder("PCBA_Standoff_{}_{}".format(x_label, z_label),
                            (x, 20.8, z), Vector((0.0, 1.0, 0.0)),
                            1.7, 4.0, bracket, collection, segments=32)
            objects.append(tag(post, "Internal mounting",
                               "CONCEPT STANDOFF"))
            screw = cylinder("PCBA_Fastener_{}_{}".format(x_label, z_label),
                             (x, 16.9, z), Vector((0.0, 1.0, 0.0)),
                             1.15, 1.0, fastener, collection, segments=32)
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

    return objects
