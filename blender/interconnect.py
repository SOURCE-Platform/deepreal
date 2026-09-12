"""Two combined optical-head flex routes for the v0.1 electrical baseline."""

from assembly_primitives import material, routed_wire, tag, wire


def _route(obj, lane):
    obj["Cable_Lane"] = lane
    obj["Physical_Intent"] = (
        "51-conductor dynamic flex; power, control and four MIPI lane pairs")
    obj["Electrical_Status"] = "CONTACT ORDER AND STACK-UP NOT FROZEN"
    return obj


def build(collection):
    flex = material("Interconnect_Flex", (0.78, 0.38, 0.035),
                    metallic=0.12, roughness=0.48)
    reference = material("Interconnect_Ground_Reference",
                         (0.52, 0.55, 0.58), metallic=0.88,
                         roughness=0.30)
    objects = []

    for side_name, x in (("Face", -48.2), ("Interaction", 48.2)):
        lane = wire(side_name + "_Data_Lane", (
            (x, 8.0, 9.0), (x, 8.0, 0.0),
            (x, 8.0, -12.0), (x, 8.0, -22.0),
        ), 0.24, reference, collection)
        lane["Lane_Type"] = "Combined head flex with continuous reference"
        objects.append(tag(lane, side_name + " optical-head lane",
                           "GROUND-REFERENCE CONCEPT"))

    routes = (
        ("Face_Optical_Head_Flex", -31.0, -22.0, -49.2, -1.0),
        ("Interaction_Optical_Head_Flex", 31.0, 22.0, 49.2, 1.0),
    )
    for name, drum_x, board_x, lane_x, side in routes:
        obj = routed_wire(name, (
            (drum_x, 7.2, 20.0),
            (drum_x + 4.0 * side, 7.8, 15.0),
            (lane_x, 8.0, 10.0),
            (lane_x, 8.0, -10.0),
            (lane_x, 10.5, -23.5),
            (board_x + 5.0 * side, 13.2, -23.5),
            (board_x, 14.75, -23.5),
        ), 0.72, 3.0, flex, collection)
        lane = "Face_Data_Lane" if side < 0 else "Interaction_Data_Lane"
        objects.append(tag(_route(obj, lane), "Optical-head interconnect",
                           "COMBINED 51-CONDUCTOR FLEX CONCEPT"))
    return objects
