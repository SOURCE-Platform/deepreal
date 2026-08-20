"""Import the APPROVED exterior as read-only reference geometry.

Opens cad/deepreal.FCStd, copies the shapes of interest into the
feasibility document as EXT_* Part::Feature objects, then closes the
source document WITHOUT saving. The approved file is never written;
validate_feasibility.py additionally guards its checksum against the
committed main-branch blob.
"""

import os

import FreeCAD as App

APPROVED_DOC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "deepreal.FCStd"))

# Objects copied as reference. Names match cad/deepreal.FCStd @ dacd90c.
REFERENCE_OBJECTS = [
    "MacBook_Air_M2_Display_Reference",
    "Main_Housing",
    "Face_Sensor_Head",
    "Interaction_Sensor_Head",
]


def import_exterior_reference(doc):
    src = App.openDocument(APPROVED_DOC)
    copied = []
    try:
        for name in REFERENCE_OBJECTS:
            obj = src.getObject(name)
            if obj is None:
                raise RuntimeError("approved model is missing object %r"
                                   % name)
            feat = doc.addObject("Part::Feature", "EXT_" + name)
            feat.Shape = obj.Shape.copy()
            feat.addProperty("App::PropertyString", "SourceFile",
                             "Feasibility").SourceFile = "cad/deepreal.FCStd"
            feat.addProperty("App::PropertyString", "SourceObject",
                             "Feasibility").SourceObject = name
            copied.append(feat)
    finally:
        App.closeDocument(src.Name)   # read-only visit; never saved
    return copied
