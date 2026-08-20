"""Drum context geometry for the feasibility document.

Reference volumes derived from the APPROVED model (positions pinned from
cad/deepreal.FCStd @ dacd90c, see registry.py):

  * two drum shells: dia 24 x 54 mm, axes along X at Y=-1.5 / Z=20
  * two "assumed usable interior" volumes using the ASSUMED wall/end-cap
    thicknesses from registry.py (explicitly labelled assumptions)
  * rotation-travel limit markers: thin radial plates at +/-75 deg about
    each drum axis (150 deg representative travel within the 140-160 deg
    requirement), measured from the user-facing (-Y) direction
"""

import FreeCAD as App
import Part

import registry


def build(doc):
    created = {"shells": [], "interiors": [], "travel": []}
    drums = [
        ("Face", registry.DRUM_FACE_X_MIN),
        ("Interaction", registry.DRUM_INTERACTION_X_MIN),
    ]
    r_shell = registry.DRUM_SHELL_DIAMETER / 2.0
    r_inner = registry.ASSUMED_INNER_DIAMETER / 2.0
    for label, x_min in drums:
        shell = doc.addObject("Part::Feature", "Ctx_%s_Drum_Shell" % label)
        shell.Shape = Part.makeCylinder(
            r_shell, registry.DRUM_SHELL_LENGTH,
            App.Vector(x_min, registry.DRUM_AXIS_Y, registry.DRUM_AXIS_Z),
            App.Vector(1, 0, 0))
        shell.addProperty("App::PropertyString", "Context", "Feasibility")\
            .Context = "drum shell, dims from approved model"
        created["shells"].append(shell)

        interior = doc.addObject("Part::Feature",
                                 "Ctx_%s_Interior_Assumed" % label)
        interior.Shape = Part.makeCylinder(
            r_inner, registry.ASSUMED_INNER_LENGTH,
            App.Vector(x_min + registry.ASSUMED_END_CAP_MM,
                       registry.DRUM_AXIS_Y, registry.DRUM_AXIS_Z),
            App.Vector(1, 0, 0))
        interior.addProperty("App::PropertyString", "Context",
                             "Feasibility").Context = (
            "ASSUMED usable interior (wall %.2f mm, end caps %.2f mm): "
            "assumption, not a design decision"
            % (registry.ASSUMED_WALL_MM, registry.ASSUMED_END_CAP_MM))
        created["interiors"].append(interior)

        # Travel limit markers: radial plates from the axis to the shell
        # surface, spanning the drum length, at +/- half the
        # representative travel measured from the user-facing (-Y)
        # direction about +X.
        half = registry.TRAVEL_MARK_DEG / 2.0
        for sign, suffix in ((-1.0, "Minus"), (1.0, "Plus")):
            plate = doc.addObject(
                "Part::Feature",
                "Ctx_%s_Travel_%s%02d" % (label, suffix, int(half)))
            # Box: X = drum length, Y = radial reach (0..r), Z thin.
            plate.Shape = Part.makeBox(
                registry.DRUM_SHELL_LENGTH, r_shell, 0.5,
                App.Vector(x_min, 0.0, -0.25))
            # Move onto the axis, then rotate about +X. Rotation about X
            # by 180 deg maps the plate's local +Y onto -Y (the user-
            # facing 0 deg direction); +/- half-travel sweeps from there.
            plate.Placement = App.Placement(
                App.Vector(0.0, registry.DRUM_AXIS_Y,
                           registry.DRUM_AXIS_Z),
                App.Rotation(App.Vector(1, 0, 0),
                             180.0 + sign * half))
            plate.addProperty("App::PropertyString", "Context",
                              "Feasibility").Context = (
                "rotation travel limit marker, %+.1f deg from -Y "
                "(representative %.0f deg travel of required %.0f-%.0f)"
                % (sign * half, registry.TRAVEL_MARK_DEG,
                   registry.TRAVEL_MIN_DEG, registry.TRAVEL_MAX_DEG))
            created["travel"].append(plate)
    return created
