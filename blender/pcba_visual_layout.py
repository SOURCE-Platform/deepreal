"""Tool-neutral production-intent copper layout shared by KiCad and Blender.

This is presentation data, not an electrical netlist or fabrication source.
"""

DISCLAIMER = "ILLUSTRATIVE COPPER - NOT ELECTRICALLY ROUTED"


def _lanes(name, side, subsystem, width, count, start, end, spacing,
           axis="z", waypoints=()):
    paths = []
    offset0 = -(count - 1) * spacing / 2.0
    for index in range(count):
        offset = offset0 + index * spacing
        if axis == "z":
            first = (start[0], start[1] + offset)
            last = (end[0], end[1] + offset)
            middle = tuple((x, z + offset) for x, z in waypoints)
        else:
            first = (start[0] + offset, start[1])
            last = (end[0] + offset, end[1])
            middle = tuple((x + offset, z) for x, z in waypoints)
        paths.append((first,) + middle + (last,))
    return {
        "name": name, "side": side, "subsystem": subsystem,
        "class": "DIFF_PAIR" if count % 2 == 0 and width <= 0.13 else "SIGNAL",
        "width": width, "paths": tuple(paths),
    }


TRACE_GROUPS = (
    _lanes("DDR_Data_Corridor", "TOP", "Compute / LPDDR4X", 0.085, 14,
           (2.62, -8.0), (4.38, -8.0), 0.72),
    _lanes("DDR_Command_Corridor", "TOP", "Compute / LPDDR4X", 0.085, 6,
           (2.62, -13.2), (4.38, -13.2), 0.62),
    _lanes("Face_Head_MIPI", "TOP", "Face camera bridge", 0.11, 8,
           (-27.6, -21.75), (-27.6, -19.62), 0.42, axis="x"),
    _lanes("Face_FPGA_to_SoC", "TOP", "Face camera bridge", 0.11, 8,
           (-24.88, -16.9), (-12.62, -14.0), 0.38,
           waypoints=((-23.5, -18.4), (-14.2, -18.4))),
    _lanes("Interaction_Head_MIPI", "TOP", "Interaction camera bridge",
           0.11, 8, (24.0, -21.75), (24.0, -19.62), 0.42, axis="x"),
    _lanes("Interaction_FPGA_to_SoC", "TOP", "Interaction camera bridge",
           0.11, 8, (20.88, -16.9), (2.62, -14.1), 0.38,
           waypoints=((19.3, -19.2), (4.2, -19.2))),
    _lanes("SoC_Left_Fanout", "TOP", "Compute control", 0.10, 6,
           (-12.62, -7.5), (-18.0, -7.5), 0.62,
           waypoints=((-14.5, -7.5), (-16.0, -5.9))),
    _lanes("SoC_Lower_Fanout", "TOP", "Compute control", 0.10, 8,
           (-5.0, -15.62), (-5.0, -18.0), 0.54, axis="x"),
    _lanes("USB_CC_and_Control", "TOP", "USB-C power/data", 0.12, 4,
           (37.0, -6.0), (36.58, -3.0), 0.42,
           waypoints=((35.9, -5.2), (35.9, -4.5))),
    _lanes("USB_SuperSpeed", "BOTTOM", "USB data", 0.11, 4,
           (37.0, -12.0), (35.35, -10.5), 0.36,
           waypoints=((36.2, -12.0), (35.7, -11.5))),
    _lanes("eMMC_Data", "BOTTOM", "Boot storage", 0.10, 10,
           (-14.12, -8.0), (-8.7, -8.0), 0.58),
    _lanes("Face_Motor_Power", "BOTTOM", "Face motion", 0.34, 2,
           (-32.0, -19.62), (-34.0, -22.25), 0.78,
           waypoints=((-32.0, -21.0), (-33.2, -21.8))),
    _lanes("Interaction_Motor_Power", "BOTTOM", "Interaction motion",
           0.34, 2, (32.0, -19.62), (34.0, -22.25), 0.78,
           waypoints=((32.0, -21.0), (33.2, -21.8))),
    _lanes("Rear_Service_Bus", "BOTTOM", "Board service", 0.12, 6,
           (-11.5, -18.0), (20.0, -18.0), 0.52,
           waypoints=((-7.0, -20.0), (15.5, -20.0))),
    _lanes("VBUS_Power_Path", "TOP", "USB power", 0.62, 2,
           (37.0, -17.0), (33.8, -17.0), 1.15,
           waypoints=((35.2, -17.0), (34.5, -16.0))),
    _lanes("System_Power_Distribution", "TOP", "Power management", 0.48, 3,
           (31.8, -9.8), (15.0, -9.8), 1.25,
           waypoints=((29.8, -11.0), (22.0, -11.0), (19.0, -9.8))),
)


POURS = (
    {"name": "Power_Island_Pour", "side": "TOP", "subsystem": "Power",
     "center": (25.5, -10.0), "size": (20.0, 17.0)},
    {"name": "USB_VBUS_Pour", "side": "TOP", "subsystem": "USB power",
     "center": (35.5, -16.8), "size": (8.0, 5.0)},
    {"name": "Processor_Ground_Plane", "side": "BOTTOM",
     "subsystem": "Compute return", "center": (-3.0, -8.0),
     "size": (24.0, 15.0)},
    {"name": "Motor_Return_Plane", "side": "BOTTOM",
     "subsystem": "Motion return", "center": (0.0, -21.4),
     "size": (66.0, 4.0)},
)


def _via_row(x0, x1, z, step, kind="GROUND"):
    count = int(round((x1 - x0) / step)) + 1
    return tuple({"x": x0 + index * step, "z": z, "kind": kind}
                 for index in range(count))


VIAS = (
    _via_row(-38.0, 38.0, 0.5, 4.0) +
    _via_row(-38.0, 38.0, -19.8, 4.0) +
    _via_row(-10.5, 0.5, -16.8, 1.0, "BGA_ESCAPE") +
    _via_row(-12.0, -8.0, -8.0, 0.8, "eMMC_TRANSITION") +
    _via_row(17.0, 33.0, -18.0, 2.0, "POWER_THERMAL") +
    _via_row(-31.0, -25.0, -20.1, 1.0, "MIPI_TRANSITION") +
    _via_row(21.0, 27.0, -20.1, 1.0, "MIPI_TRANSITION")
)


TEST_PADS = tuple(
    {"name": "TP{:02d}".format(index + 1), "side": side, "x": x, "z": z}
    for index, (side, x, z) in enumerate((
        ("TOP", -39.0, -6.0), ("TOP", -39.0, -9.0),
        ("TOP", -39.0, -12.0), ("TOP", 15.5, -2.0),
        ("TOP", 18.0, -2.0), ("TOP", 20.5, -2.0),
        ("BOTTOM", -8.0, -3.0), ("BOTTOM", -5.0, -3.0),
        ("BOTTOM", -2.0, -3.0), ("BOTTOM", 1.0, -3.0),
    ))
)
