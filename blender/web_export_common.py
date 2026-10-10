"""Shared Blender-to-web mesh staging for the DeepReal appearance studies."""

import hashlib
import json
from pathlib import Path

import bpy


def require_r36_source():
    source = Path(bpy.data.filepath)
    if not source.name.startswith("deepreal-inner-bearing-window-r36"):
        raise RuntimeError("Load the R36 exterior-bearing study before exporting")
    return source


def require_r38_source():
    source = Path(bpy.data.filepath)
    if not source.name.startswith("deepreal-exterior-mount-r38"):
        raise RuntimeError("Load the R38 exterior mount study before exporting")
    return source


def stage_meshes(objects, label):
    collection = bpy.data.collections.new(label)
    bpy.context.scene.collection.children.link(collection)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    staged = []
    drum_material = bpy.data.materials["Device_Sensor_Drum.001"]
    for original in objects:
        evaluated = original.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(
            evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
        if not mesh or not mesh.vertices or not mesh.polygons:
            raise RuntimeError("Empty export mesh: " + original.name)
        if mesh.validate(verbose=False):
            print("REPAIRED EXPORT COPY", original.name)
        for index, slot in enumerate(mesh.materials):
            if slot is None:
                mesh.materials[index] = drum_material
        clone = bpy.data.objects.new(original.name + "_WEB", mesh)
        collection.objects.link(clone)
        clone.matrix_world = original.matrix_world.copy()
        staged.append(clone)
    return staged


def export_glb(output, objects):
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_yup=True,
        export_materials="EXPORT",
        export_normals=True,
        export_texcoords=True,
        export_cameras=False,
        export_lights=False,
    )
    print("EXPORTED", output, output.stat().st_size, "bytes")


def write_manifest(path, source, asset, data):
    path.write_text(json.dumps({
        "source_blend": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "asset": asset.name,
        "asset_sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
        **data,
    }, indent=2) + "\n")
