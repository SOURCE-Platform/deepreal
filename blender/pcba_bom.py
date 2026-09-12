"""Electrical-baseline population for the preliminary Main PCBA.

Coordinates are millimetres in the established board X/Z plane. ``height`` is
normal to the PCB. This is a placement/packaging contract, not routed copper.
Source: docs/design/main-pcba-mechanical-bom-v0.2.csv.
"""

BOARD = {
    "width": 90.0, "depth": 28.0, "thickness": 1.6,
    "center_y": 16.35, "center_z": -11.5,
}


def _part(name, ref, maker, number, package, width, depth, height,
          x, z, side, status, subsystem, source, step=""):
    return {
        "name": name, "ref": ref, "manufacturer": maker,
        "part_number": number, "package": package,
        "width": width, "depth": depth, "height": height,
        "x": x, "z": z, "side": side, "status": status,
        "subsystem": subsystem, "source": source, "step_source": step,
    }


MAJOR_PARTS = (
    _part("NXP_iMX95", "U1", "NXP", "MIMX9596CVTXNAC",
          "FC-PBGA-548 SOT2251-1", 15.0, 15.0, 1.584,
          -5.0, -8.0, "TOP", "PINMAP_REQUIRED", "Compute",
          "NXP IMX95IEC Rev 8"),
    _part("Face_CrossLink_NX", "U2", "Lattice", "LIFCL-17",
          "121-ball csfBGA", 6.0, 6.0, 1.0,
          -28.0, -16.5, "TOP", "COMPILE_REQUIRED", "Face camera bridge",
          "Lattice CrossLink-NX selection table"),
    _part("Interaction_CrossLink_NX", "U3", "Lattice", "LIFCL-17",
          "121-ball csfBGA", 6.0, 6.0, 1.0,
          24.0, -16.5, "TOP", "COMPILE_REQUIRED",
          "Interaction camera bridge", "Lattice CrossLink-NX selection table"),
    _part("LPDDR4X_4GB", "U4", "Micron", "MT53E1G32D2FW-046 AAT:B",
          "200-ball TFBGA", 10.0, 14.5, 1.1,
          9.5, -8.0, "TOP", "DDR_VALIDATION_REQUIRED", "Working memory",
          "Micron production catalog"),
    _part("PMIC_PF09", "U5", "NXP", "MPF0900AVNA2ES",
          "HVQFN56", 8.0, 8.0, 0.53,
          27.5, -5.0, "TOP", "SEQUENCE_REVIEW", "Power management",
          "NXP PF09 Rev 1.3"),
    _part("PF53_SOC", "U6", "NXP", "MPF5302BVNAAEP",
          "H-FC-PQFN24", 3.5, 4.5, 0.75,
          17.0, -2.5, "TOP", "SEQUENCE_REVIEW", "VDD_SOC regulator",
          "NXP PF53 ordering table"),
    _part("PF53_ARM", "U7", "NXP", "MPF5301BVNABEP",
          "H-FC-PQFN24", 3.5, 4.5, 0.75,
          17.0, -8.3, "TOP", "SEQUENCE_REVIEW", "VDD_ARM regulator",
          "NXP PF53 ordering table"),
    _part("System_5V_Buck", "U8", "Texas Instruments", "TPS56637RPAR",
          "VQFN-HR10 RPA", 3.0, 3.0, 1.0,
          32.5, -11.0, "TOP", "CALC_REQUIRED", "System power",
          "TI TPS56637 product data"),
    _part("Motor_6V_Buck", "U9", "Texas Instruments", "TPS56637RPAR",
          "VQFN-HR10 RPA", 3.0, 3.0, 1.0,
          32.5, -15.5, "TOP", "CALC_REQUIRED", "Motor power",
          "TI TPS56637 product data"),
    _part("VBUS_eFuse", "U10", "Texas Instruments", "TPS259472LRPWR",
          "WQFN10 RPW", 2.0, 2.0, 0.8,
          34.0, -18.7, "TOP", "BASELINE", "VBUS protection",
          "TI TPS25947 product data"),
    _part("USB_PD_Controller", "U11", "Infineon", "CYPD3177-24LQXQ",
          "QFN24", 4.0, 4.0, 0.6,
          34.5, -2.8, "TOP", "BASELINE", "USB-PD negotiation",
          "Infineon CYPD3177 data sheet"),
    _part("USB_SS_Mux", "U12", "Texas Instruments", "HD3SS3212IRKSR",
          "VQFN20 RKS", 2.5, 4.5, 1.0,
          34.0, -10.5, "BOTTOM", "BASELINE", "USB data",
          "TI HD3SS3212 product data"),
    _part("Face_Motor_Driver", "U13", "Texas Instruments", "DRV8213RTER",
          "WQFN16 RTE", 3.0, 3.0, 0.8,
          -32.0, -18.0, "BOTTOM", "BASELINE", "Face motion",
          "TI DRV8213 product data"),
    _part("Interaction_Motor_Driver", "U14", "Texas Instruments",
          "DRV8213RTER", "WQFN16 RTE", 3.0, 3.0, 0.8,
          32.0, -18.0, "BOTTOM", "BASELINE", "Interaction motion",
          "TI DRV8213 product data"),
    _part("eMMC_32GB", "U15", "Micron", "MTFC32GBCAQTC-AAT",
          "153-ball BGA", 11.5, 13.0, 1.3,
          -20.0, -8.0, "BOTTOM", "PINMAP_REQUIRED", "Boot storage",
          "Micron production catalog"),
    _part("Board_ID_EEPROM", "U16", "Microchip", "AT24C64D-MAHM-T",
          "UDFN8", 2.0, 3.0, 0.6,
          -3.0, -18.3, "BOTTOM", "BASELINE", "Board identity",
          "Microchip production data"),
    _part("Sensor_Clock_Buffer", "U17", "Texas Instruments", "LMK1C1104DQFR",
          "WSON8 DQF", 2.0, 2.0, 0.8,
          2.0, -19.5, "BOTTOM", "BASELINE", "Sensor clocking",
          "TI product data"),
    _part("Face_Absolute_Angle", "U18", "ams OSRAM", "AS5600L-AWLM",
          "WLCSP15", 2.07, 2.63, 0.6,
          -39.0, -3.0, "TOP", "SUPPLY_RECHECK", "Face pose",
          "AS5600L data sheet"),
    _part("Interaction_Absolute_Angle", "U19", "ams OSRAM", "AS5600L-AWLM",
          "WLCSP15", 2.07, 2.63, 0.6,
          39.0, -3.0, "TOP", "SUPPLY_RECHECK", "Interaction pose",
          "AS5600L data sheet"),
    _part("Main_Board_Temperature", "U20", "Texas Instruments",
          "TMP117AIDRVR", "WSON6 DRV", 2.0, 2.0, 0.8,
          -14.5, -17.5, "TOP", "BASELINE", "Thermal monitoring",
          "TI TMP117 product data"),
    _part("PDM_MEMS_Microphone", "MK1", "TDK", "MMICT3902-00-012",
          "Bottom-port LGA", 3.5, 2.65, 0.98,
          9.0, -20.0, "BOTTOM", "BASELINE", "Audio",
          "TDK T3902 product data"),
    _part("Case_Open_Tamper_Switch", "SW1", "Omron", "D3SK-B1R",
          "Surface-mount NC detector", 3.0, 3.5, 0.9,
          0.0, -23.0, "TOP", "MECHANICAL_GATE", "Tamper detection",
          "Omron product data"),
)


PROTECTION_PARTS = (
    _part("USB_SS_ESD", "D1", "Texas Instruments", "TPD4EUSB30DQAR",
          "USON10 DQA", 2.5, 1.0, 0.55, 38.0, -18.7, "BOTTOM",
          "SI_REVIEW", "USB protection", "TI product data"),
    _part("USB2_ESD", "D2", "Texas Instruments", "TPD2EUSB30ADRTR",
          "SOT-9X3 DRT", 1.0, 1.0, 0.6, 39.8, -18.7, "BOTTOM",
          "SI_REVIEW", "USB protection", "TI product data"),
    _part("VBUS_TVS", "D9", "TBD", "Low-profile TVS", "TBD",
          3.0, 2.0, 1.0, 38.0, -20.0, "TOP", "SELECTION_REQUIRED",
          "VBUS protection", "Surge requirement"),
)


HEAD_CONNECTORS = (
    _part("Face_Optical_Head_Connector", "J2", "Hirose",
          "FH26W-51S-0.3SHW(97)", "0.3mm FPC 51-position",
          15.6, 3.2, 1.0, -22.0, -23.5, "TOP", "FLEX_SI_GATE",
          "Face optical head", "Hirose FH26 catalog"),
    _part("Interaction_Optical_Head_Connector", "J3", "Hirose",
          "FH26W-51S-0.3SHW(97)", "0.3mm FPC 51-position",
          15.6, 3.2, 1.0, 22.0, -23.5, "TOP", "FLEX_SI_GATE",
          "Interaction optical head", "Hirose FH26 catalog"),
)


OTHER_CONNECTORS = (
    _part("USB_C_Receptacle", "J1", "Hirose", "CX90M3-24P",
          "Mid-mount USB Type-C", 7.85, 12.0, 3.16,
          41.075, -11.5, "TOP", "BASELINE", "USB-C power/data",
          "Hirose drawing", "Hirose official STEP"),
    _part("Face_Motor_Encoder", "J4", "TBD", "6-position low-profile",
          "Reserved", 5.0, 2.6, 1.2, -34.0, -23.7, "TOP", "RESERVED",
          "Face motion", "Function envelope"),
    _part("Interaction_Motor_Encoder", "J5", "TBD",
          "6-position low-profile", "Reserved", 5.0, 2.6, 1.2,
          34.0, -23.7, "TOP", "RESERVED", "Interaction motion",
          "Function envelope"),
)


ALL_PARTS = MAJOR_PARTS + PROTECTION_PARTS + HEAD_CONNECTORS + OTHER_CONNECTORS

PLANNING_ZONES = (
    ("iMX95_Neighborhood", -5.0, -8.0, 20.0, 20.0, "TOP"),
    ("DDR_Neighborhood", 9.5, -8.0, 12.0, 17.0, "TOP"),
    ("Face_FPGA_Corridor", -28.0, -16.5, 15.0, 15.0, "TOP"),
    ("Interaction_FPGA_Corridor", 24.0, -16.5, 15.0, 15.0, "TOP"),
    ("Power_Island", 25.0, -6.0, 24.0, 17.0, "TOP"),
    ("USB_Subsystem", 36.0, -11.0, 16.0, 22.0, "TOP"),
)
