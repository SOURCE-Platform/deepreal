"""Visibility groups for the feasibility document.

Gate 1: thirteen groups G00..G12. Gate 1.5B adds G13..G18 for the
discrete depth-sensing components and the three in-drum layout studies.
Groups are App::DocumentObjectGroup; objects may appear in more than one
group (e.g. no-fit envelopes live in their functional group AND
G11_NoFit_Reference).
"""

GROUP_DEFS = [
    ("G00_Exterior_Reference",
     "Approved exterior + laptop reference, copied read-only"),
    ("G01_Drum_Shells_Context",
     "Dia 24 x 54 drum shell volumes (positions from approved model)"),
    ("G02_Drum_Interior_Assumed",
     "Assumed usable interior volumes (wall/end-cap ASSUMPTION)"),
    ("G03_Drum_Travel_Markers",
     "Rotation-travel limit markers (+/-75 deg from -Y)"),
    ("G04_Sensors_RGB",
     "RGB camera envelopes (RPi CM3 board, CM3 sensor assembly)"),
    ("G05_Sensors_Depth_StructuredLight",
     "Structured-light depth envelopes (Orbbec all-in-one modules)"),
    ("G06_Actuators_SmartServo",
     "Smart-servo actuator envelope (DYNAMIXEL XL330)"),
    ("G07_Actuators_DCGearmotor",
     "DC gearmotor actuator envelope (Pololu 75:1 MP)"),
    ("G08_Actuators_GimbalBLDC",
     "Gimbal BLDC actuator envelope (T-Motor GB2208)"),
    ("G09_Bearings_Supports",
     "Bearing/shaft support placeholders (no components researched yet)"),
    ("G10_Wiring_Harness",
     "Wiring/slip-ring placeholders (no components researched yet)"),
    ("G11_NoFit_Reference",
     "Components that cannot fit the drum; kept visible for comparison"),
    ("G12_Review_Preset_Notes",
     "Reserved for review annotations (presets act on view only)"),
    ("G13_Sensors_IR_Camera",
     "Global-shutter NIR camera die (OmniVision OV9281 bare sensor)"),
    ("G14_Depth_Projectors",
     "Structured-light dot projectors (ams BELICE-850, Belago1.2)"),
    ("G15_Sensors_Depth_ToF",
     "Time-of-flight imagers (Infineon IRS2877A, IRS2976C) + "
     "illuminator placeholder"),
    ("G16_Layout_SL_A",
     "In-drum layout SL-A: axial RGB -> IR -> projector (BELICE-850)"),
    ("G17_Layout_SL_B",
     "In-drum layout SL-B: RGB axial, IR + projector (Belago1.2) share "
     "a cross-section station"),
    ("G18_Layout_ToF_A",
     "In-drum layout ToF-A: IRS2877A + flood-illuminator placeholder + "
     "carrier-PCB keep-out"),
]


def build(doc, exterior, context, envelopes, layout_objs=None):
    groups = {}
    for name, _desc in GROUP_DEFS:
        grp = doc.addObject("App::DocumentObjectGroup", name)
        groups[name] = grp

    for obj in exterior:
        groups["G00_Exterior_Reference"].addObject(obj)
    for obj in context["shells"]:
        groups["G01_Drum_Shells_Context"].addObject(obj)
    for obj in context["interiors"]:
        groups["G02_Drum_Interior_Assumed"].addObject(obj)
    for obj in context["travel"]:
        groups["G03_Drum_Travel_Markers"].addObject(obj)

    functional = {
        "rpi_cm3_sensor_assembly": "G04_Sensors_RGB",
        "rpi_camera_module_3": "G04_Sensors_RGB",
        "orbbec_astra_mini_pro": "G05_Sensors_Depth_StructuredLight",
        "orbbec_astra_embedded_s": "G05_Sensors_Depth_StructuredLight",
        "robotis_xl330_m288": "G06_Actuators_SmartServo",
        "pololu_5137": "G07_Actuators_DCGearmotor",
        "tmotor_gb2208": "G08_Actuators_GimbalBLDC",
        "ov9281_ir_camera": "G13_Sensors_IR_Camera",
        "ams_belice_850": "G14_Depth_Projectors",
        "ams_belago1_2": "G14_Depth_Projectors",
        "infineon_irs2877a": "G15_Sensors_Depth_ToF",
        "infineon_irs2976c": "G15_Sensors_Depth_ToF",
        "tof_illuminator_placeholder": "G15_Sensors_Depth_ToF",
    }
    no_fit = {"orbbec_astra_mini_pro", "orbbec_astra_embedded_s",
              "tmotor_gb2208"}
    for key, obj in envelopes.items():
        groups[functional[key]].addObject(obj)
        if key in no_fit:
            groups["G11_NoFit_Reference"].addObject(obj)

    if layout_objs:
        layout_group = {
            "SL-A": "G16_Layout_SL_A",
            "SL-B": "G17_Layout_SL_B",
            "ToF-A": "G18_Layout_ToF_A",
        }
        for lname, objs in layout_objs.items():
            for obj in objs:
                groups[layout_group[lname]].addObject(obj)
    return groups
