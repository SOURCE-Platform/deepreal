"""Visible flex and power routing between the rotating drums and main PCBA."""

from assembly_primitives import material, tag, wire


def build(collection):
    flex = material("Interconnect_Flex", (0.78, 0.38, 0.035),
                    metallic=0.12, roughness=0.48)
    power = material("Interconnect_Power", (0.08, 0.09, 0.11),
                     roughness=0.66)
    objects = []

    # Four independent camera links: face RGB/depth and interaction
    # depth/tracking. Curves show service loops, not a frozen production route.
    routes = (
        ("Face_RGB_MIPI_Flex", -42.0, -35.0),
        ("Face_Depth_MIPI_Flex", -20.0, -23.0),
        ("Interaction_Depth_MIPI_Flex", 18.0, -11.0),
        ("Interaction_Tracking_MIPI_Flex", 40.0, 1.0),
    )
    for name, drum_x, board_x in routes:
        side = -1.0 if drum_x < 0 else 1.0
        obj = wire(name, (
            (drum_x, 7.5, 18.0),
            (drum_x + 4.0 * side, 9.0, 7.0),
            (drum_x + 2.0 * side, 12.0, 2.0),
            (board_x, 16.2, 0.8),
        ), 0.55, flex, collection)
        objects.append(tag(obj, "Camera interconnect", "SERVICE-LOOP CONCEPT"))

    for label, x in (("Face_Projector_Power", -31.0),
                     ("Interaction_Projector_Power", 31.0)):
        side = -1.0 if x < 0 else 1.0
        obj = wire(label, (
            (x, 7.0, 22.0),
            (x + 5.0 * side, 11.0, 8.0),
            (x, 15.5, -5.0),
            (x * 0.8, 16.5, -19.0),
        ), 0.42, power, collection)
        objects.append(tag(obj, "Projector interconnect", "ROUTING CONCEPT"))
    return objects
