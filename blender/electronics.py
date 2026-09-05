"""Blender concept geometry for the stationary DeepReal electronics."""

from assembly_primitives import box, material, tag


BOARD_Y = 18.0
BOARD_Z = -11.5
SHIELD_X0 = -44.0
SHIELD_X1 = 44.0
SHIELD_Z0 = -25.0
SHIELD_Z1 = -2.2
SHIELD_FRONT_Y = 12.2
CONNECTOR_Z = 0.5


def _materials():
    return {
        "board": material("Electronics_PCBA", (0.025, 0.20, 0.07),
                          roughness=0.58),
        "soc": material("Electronics_iMX95", (0.92, 0.48, 0.05),
                        metallic=0.18, roughness=0.32),
        "fpga": material("Electronics_FPGA", (0.02, 0.42, 0.68),
                         metallic=0.12, roughness=0.34),
        "memory": material("Electronics_Memory", (0.035, 0.045, 0.07),
                           roughness=0.30),
        "power": material("Electronics_Power", (0.44, 0.12, 0.52),
                          roughness=0.40),
        "driver": material("Electronics_Driver", (0.06, 0.46, 0.34),
                           roughness=0.38),
        "connector": material("Electronics_Connector", (0.72, 0.74, 0.76),
                              metallic=0.55, roughness=0.30),
        "shield": material("EMI_Shield_Can", (0.30, 0.34, 0.40),
                           metallic=0.92, roughness=0.30),
        "copper": material("Thermal_Spreader_Copper", (0.66, 0.24, 0.06),
                           metallic=0.95, roughness=0.25),
        "pad": material("Thermal_Pad", (0.12, 0.30, 0.36),
                        roughness=0.72),
        "mic": material("Electronics_Microphone", (0.12, 0.12, 0.13),
                        metallic=0.55, roughness=0.35),
        "keepout": material("Electronics_Keepout", (0.94, 0.55, 0.04),
                            roughness=0.45, alpha=0.10),
    }


def _component(name, x, z, dims, mat, collection, subsystem,
               evidence="REFERENCE PACKAGE"):
    obj = box(name, (x, BOARD_Y - dims[1] / 2.0 - 0.8, z), dims, 0.35,
              mat, collection)
    return tag(obj, subsystem, evidence)


def _shield_can(mats, collection):
    """One grounded shallow can over the populated board area.

    A narrow strip at the top of the PCBA remains outside the perimeter for
    cable connectors. Harnesses terminate there; only PCB traces continue
    beneath the can.
    """
    front_y = SHIELD_FRONT_Y
    board_face_y = BOARD_Y - 0.8
    x0, x1 = SHIELD_X0, SHIELD_X1
    z0, z1 = SHIELD_Z0, SHIELD_Z1
    wall = 0.30
    objects = []
    objects.append(box("EMI_Shield_Can_Lid",
                       ((x0 + x1) / 2.0, front_y, (z0 + z1) / 2.0),
                       (x1 - x0, wall, z1 - z0), 0.8,
                       mats["shield"], collection))
    depth = board_face_y - front_y
    mid_y = (front_y + board_face_y) / 2.0
    for name, center, dims in (
        ("EMI_Shield_Can_Wall_Left", (x0, mid_y, BOARD_Z),
         (wall, depth, z1 - z0)),
        ("EMI_Shield_Can_Wall_Right", (x1, mid_y, BOARD_Z),
         (wall, depth, z1 - z0)),
        ("EMI_Shield_Can_Wall_Top", ((x0 + x1) / 2.0, mid_y, z1),
         (x1 - x0, depth, wall)),
        ("EMI_Shield_Can_Wall_Bottom", ((x0 + x1) / 2.0, mid_y, z0),
         (x1 - x0, depth, wall)),
    ):
        objects.append(box(name, center, dims, 0.15,
                           mats["shield"], collection))
    for obj in objects:
        tag(obj, "EMI shield", "FORMED-SHEET CONCEPT")
    return objects


def build(collection):
    mats = _materials()
    objects = []
    board = box("Main_PCBA", (0.0, BOARD_Y, BOARD_Z),
                (90.0, 1.6, 28.0), 0.8, mats["board"], collection)
    objects.append(tag(board, "Main electronics", "REQUIRED ENVELOPE"))

    keepout = box("Main_PCBA_Populated_Keepout", (0.0, 15.5, BOARD_Z),
                  (90.0, 15.0, 28.0), 1.0, mats["keepout"], collection)
    keepout.display_type = "WIRE"
    keepout.hide_render = True
    objects.append(tag(keepout, "Main electronics", "REFERENCE RESERVE"))

    specs = (
        ("NXP_iMX95", -5.0, BOARD_Z + 1.0, (15.0, 3.0, 15.0), "soc",
         "Proof Engine SoC"),
        ("CrossLink_NX_FPGA", -28.0, BOARD_Z + 1.0,
         (13.0, 2.6, 13.0), "fpga", "Trusted camera bridge"),
        ("LPDDR_1", 12.0, BOARD_Z - 4.0, (8.0, 2.2, 6.0), "memory",
         "Working memory"),
        ("LPDDR_2", 12.0, BOARD_Z + 6.0, (8.0, 2.2, 6.0), "memory",
         "Working memory"),
        ("eMMC_Storage", 29.0, BOARD_Z - 7.0, (10.0, 2.0, 7.0), "memory",
         "System storage"),
        ("PMIC_PF09", 29.0, BOARD_Z + 6.0, (6.0, 2.0, 6.0), "power",
         "Power management"),
        ("PMIC_PF53", 38.0, BOARD_Z + 6.0, (6.0, 2.0, 6.0), "power",
         "Power management"),
        ("USB_PD_Controller", 40.0, BOARD_Z - 8.0, (5.0, 1.5, 5.0),
         "power", "USB power negotiation"),
        ("USB_ESD_Protection", 40.0, BOARD_Z - 1.5, (4.0, 1.3, 3.0),
         "driver", "USB protection"),
        ("Motor_Driver_A", 27.0, BOARD_Z - 1.0, (4.0, 1.4, 4.0),
         "driver", "Motor control"),
        ("Motor_Driver_B", 33.0, BOARD_Z - 1.0, (4.0, 1.4, 4.0),
         "driver", "Motor control"),
        ("Projector_Driver_A", -31.0, BOARD_Z - 8.5, (4.0, 1.4, 4.0),
         "driver", "IR emitter control"),
        ("Projector_Driver_B", -24.5, BOARD_Z - 8.5, (4.0, 1.4, 4.0),
         "driver", "IR emitter control"),
    )
    for name, x, z, dims, mat, subsystem in specs:
        objects.append(_component(name, x, z, dims, mats[mat], collection,
                                  subsystem))

    mic = box("PDM_MEMS_Microphone", (-42.0, BOARD_Y - 1.4, CONNECTOR_Z),
              (4.0, 1.2, 3.0), 0.3, mats["mic"], collection)
    objects.append(tag(mic, "Audio", "REFERENCE PACKAGE"))

    for index, x in enumerate((-16.0, -5.0, 6.0, 17.0)):
        connector = box("Camera_Flex_Connector_{}".format(index + 1),
                        (x, BOARD_Y - 1.4, CONNECTOR_Z),
                        (7.0, 1.2, 2.0), 0.2, mats["connector"], collection)
        objects.append(tag(connector, "Camera interconnect"))

    edge_connectors = (
        ("Face_Motor_Connector", -38.0, "Motor interconnect"),
        ("Face_Projector_Connector", -27.0, "Projector interconnect"),
        ("Interaction_Projector_Connector", 28.0,
         "Projector interconnect"),
        ("Interaction_Motor_Connector", 39.0, "Motor interconnect"),
    )
    for name, x, subsystem in edge_connectors:
        connector = box(name, (x, BOARD_Y - 1.4, CONNECTOR_Z),
                        (7.0, 1.2, 2.0), 0.2, mats["connector"], collection)
        objects.append(tag(connector, subsystem, "BOARD-EDGE CONNECTOR"))

    objects += _shield_can(mats, collection)

    spreader = box("Thermal_Spreader", (0.0, BOARD_Y + 1.55, BOARD_Z),
                   (76.0, 1.5, 30.0), 1.0, mats["copper"], collection)
    objects.append(tag(spreader, "Thermal", "CONCEPT HEAT PATH"))
    pad = box("Housing_Thermal_Pad", (0.0, 21.65, BOARD_Z),
              (60.0, 2.7, 20.0), 0.8, mats["pad"], collection)
    objects.append(tag(pad, "Thermal", "CONCEPT INTERFACE"))

    tamper = box("Case_Open_Tamper_Switch", (42.0, 21.0, CONNECTOR_Z),
                 (4.0, 3.0, 3.0), 0.4, mats["driver"], collection)
    objects.append(tag(tamper, "Tamper detection", "REQUIRED CONCEPT"))
    return objects
