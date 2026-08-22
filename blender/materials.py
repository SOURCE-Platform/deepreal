"""DeepReal Blender material library.

Every material is created deterministically by name: build_all() first
removes any existing material with the same name, so repeated scene
rebuilds (the whole point of the pipeline) never accumulate duplicates
or pick up manual edits from a stale .blend.

All materials are Principled BSDF and are tuned for Cycles. Values are
art-directed starting points for the studio product shot, not physics.

Import-safe: nothing runs at import time.
"""

import bpy


def _fresh_principled(name):
    """(Re)create material `name` with a Principled BSDF; return (mat, bsdf)."""
    old = bpy.data.materials.get(name)
    if old is not None:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    return mat, bsdf


def _set(bsdf, socket, value):
    """Set a Principled input if this Blender version has it (4.x renamed
    several sockets; guard so the library works across versions)."""
    try:
        bsdf.inputs[socket].default_value = value
        return True
    except (KeyError, RuntimeError):
        return False


def build_all():
    """Build the full library; returns {name: material}."""

    mats = {}

    def make(name, base, metallic=0.0, roughness=0.5, **extra):
        mat, bsdf = _fresh_principled(name)
        _set(bsdf, "Base Color", (*base, 1.0))
        _set(bsdf, "Metallic", metallic)
        _set(bsdf, "Roughness", roughness)
        for socket, value in extra.items():
            _set(bsdf, socket.replace("_", " "), value)
        mats[name] = mat
        return mat

    # --- DeepReal device -------------------------------------------------
    # Smooth professional 3D print (SLS/MJF nylon): satin, light warm grey,
    # no visible layer texture.
    make("Device_Printed_Nylon", (0.74, 0.73, 0.70),
         roughness=0.46, **{"coat_weight": 0.10, "coat_roughness": 0.30})

    # The two sensor drums: matte dark anodized aluminium per the drum
    # industrial-design reference (precision cylindrical instrument).
    make("Device_Sensor_Drum", (0.16, 0.16, 0.17),
         metallic=1.0, roughness=0.42)

    # Drum optics: flush glass with thin dark machined bezels.
    make("Optic_Glass_Depth", (0.04, 0.035, 0.06),
         roughness=0.05, **{"coat_weight": 0.6, "coat_roughness": 0.03})
    make("Optic_Glass_RGB", (0.035, 0.05, 0.045),
         roughness=0.05, **{"coat_weight": 0.6, "coat_roughness": 0.03})
    make("Optic_Projector_Inset", (0.02, 0.02, 0.02), roughness=0.4)
    make("Optic_Bezel", (0.10, 0.10, 0.11), metallic=1.0, roughness=0.35)
    # Internal placeholder volumes: matte near-black, visible only in
    # cutaway/exploded views of the drum.
    make("Sensor_Internal", (0.08, 0.08, 0.085), roughness=0.8)

    # Device-side magnetic plate: bright nickel-plated steel.
    make("Mount_Magnet_Nickel", (0.70, 0.71, 0.72),
         metallic=1.0, roughness=0.22)

    # Laptop-side keeper plate: thin steel, lightly brushed.
    make("Mount_Steel_Plate", (0.60, 0.61, 0.63),
         metallic=1.0, roughness=0.38)

    # 3M double-sided foam tape: grey closed-cell foam, fully diffuse.
    make("Mount_Foam_Tape", (0.52, 0.53, 0.54), roughness=0.95)

    # --- MacBook Air (silver) ---------------------------------------------
    make("MacBook_Aluminium", (0.75, 0.76, 0.78),
         metallic=1.0, roughness=0.40)
    make("MacBook_Keyboard_Well", (0.055, 0.055, 0.06), roughness=0.75)
    make("MacBook_Keycap", (0.10, 0.10, 0.11), roughness=0.60)
    make("MacBook_Trackpad", (0.72, 0.73, 0.75),
         metallic=0.30, roughness=0.16)
    # Screen assembly: black glossy glass. Screen is OFF for now (zero
    # emission) -- a later pass can drive Emission Strength for content.
    make("MacBook_Screen_Glass", (0.015, 0.015, 0.02), roughness=0.06)
    make("MacBook_Screen_Active", (0.02, 0.022, 0.03),
         roughness=0.05, **{"emission_color": (0.05, 0.07, 0.10, 1.0),
                            "emission_strength": 0.0})
    make("MacBook_Hinge", (0.12, 0.12, 0.13), metallic=0.8, roughness=0.45)
    make("MacBook_Foot", (0.07, 0.07, 0.075), roughness=0.90)

    # --- Debug / CAD review ------------------------------------------------
    make("Debug_Red", (0.78, 0.06, 0.06),
         **{"emission_color": (0.78, 0.06, 0.06, 1.0),
            "emission_strength": 0.4})

    return mats
