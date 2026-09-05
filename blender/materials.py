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
    normalized = socket.replace("_", "").replace(" ", "").lower()
    aliases = {
        "iorlevel": "speculariorlevel",
    }
    normalized = aliases.get(normalized, normalized)
    for input_socket in bsdf.inputs:
        candidate = input_socket.name.replace(" ", "").lower()
        if candidate == normalized:
            input_socket.default_value = value
            return True
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
    # Near-black satin anodized aluminium across the stationary housing,
    # rear arm, and both rotating drums. Keep the finish shared so the
    # straight-on product view reads as one instrument.
    anodized = (0.025, 0.028, 0.032)
    make("Device_Housing_Anodized", anodized, metallic=0.92,
         roughness=0.32, **{"coat_weight": 0.12,
                           "coat_roughness": 0.24})
    make("Device_Sensor_Drum", anodized, metallic=0.92,
         roughness=0.58, **{"coat_weight": 0.12,
                           "coat_roughness": 0.24})

    # Reference-component optical appearance: a matte-black recessed well
    # surrounds each element, OV9281-class IR/depth glass carries a faint
    # violet AR cast, and IMX708-class RGB glass a faint green/cyan cast.
    make("Optic_Lens_Well", (0.0015, 0.0018, 0.0020), roughness=0.58,
         **{"ior_level": 0.02})
    make("Optic_Cover_Glass", (0.012, 0.014, 0.016),
         roughness=0.08, **{"ior": 1.46, "ior_level": 0.18,
                           "transmission_weight": 0.92})
    make("Optic_Glass_Depth", (0.0018, 0.0010, 0.0030),
         roughness=0.12, **{"ior": 1.52, "ior_level": 0.28,
                           "transmission_weight": 0.28,
                           "coat_weight": 0.10,
                           "coat_roughness": 0.08})
    make("Optic_Glass_RGB", (0.0008, 0.0025, 0.0015),
         roughness=0.12, **{"ior": 1.52, "ior_level": 0.28,
                           "transmission_weight": 0.28,
                           "coat_weight": 0.10,
                           "coat_roughness": 0.08})
    make("Optic_Lens_Pupil", (0.0005, 0.0007, 0.0008),
         roughness=0.18, **{"ior_level": 0.10})
    make("Optic_Projector_Inset", (0.006, 0.006, 0.008),
         roughness=0.34, **{"ior_level": 0.10, "coat_weight": 0.05,
                           "coat_roughness": 0.20})
    make("Optic_Bezel", (0.008, 0.009, 0.010),
         metallic=0.35, roughness=0.52)
    # Internal placeholder volumes: matte near-black, visible only in
    # cutaway/exploded views of the drum.
    make("Sensor_Internal", (0.003, 0.0035, 0.004), roughness=0.86)

    # Device-side magnetic plate: bright nickel-plated steel.
    make("Mount_Magnet_Nickel", (0.70, 0.71, 0.72),
         metallic=1.0, roughness=0.22)

    # Laptop-side keeper plate: thin steel, lightly brushed.
    make("Mount_Steel_Plate", (0.60, 0.61, 0.63),
         metallic=1.0, roughness=0.38)

    # 3M double-sided foam tape: grey closed-cell foam, fully diffuse.
    make("Mount_Foam_Tape", (0.52, 0.53, 0.54), roughness=0.95)

    # USB-C receptacle: bright tin-plated stamped shell + gold contacts.
    make("USB_Shell_Tin", (0.62, 0.62, 0.60), metallic=1.0, roughness=0.35)
    make("USB_Tongue_Gold", (0.75, 0.66, 0.42), metallic=1.0, roughness=0.30)
    # Cable assembly: non-metallic charcoal jacket matched to the device.
    make("Cable_Jacket", (0.025, 0.028, 0.032), roughness=0.62)
    make("Cable_Overmold", (0.020, 0.022, 0.025), roughness=0.56)

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
