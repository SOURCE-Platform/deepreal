"""Nominal solid screening on evaluated copies, never the retained CAD."""

from collections import Counter

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from pcb_fit_geometry import positive_box_overlap


WELD_MM = 0.00001
VOLUME_MM3 = 0.00001


def snapshot(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        points = [evaluated.matrix_world @ v.co * 1000 for v in mesh.vertices]
        faces = [tuple(t.vertices) for t in mesh.loop_triangles]
    finally:
        evaluated.to_mesh_clear()
    return from_points(points, faces, obj.name)


def from_points(points, faces, name):
    # glTF duplicates vertices at normal/material seams. Weld only the
    # inspection copy at 10 nm to assess boundary topology and containment.
    ids, welded, mapping = {}, [], []
    for point in points:
        key = tuple(round(v / WELD_MM) for v in point)
        if key not in ids:
            ids[key] = len(welded)
            welded.append(Vector(point))
        mapping.append(ids[key])
    triangles = [tuple(mapping[i] for i in face) for face in faces]
    triangles = [f for f in triangles if len(set(f)) == 3]
    if not welded or not triangles:
        raise ValueError("empty fit geometry: " + name)
    edges = Counter(tuple(sorted((a, b))) for f in triangles
                    for a, b in zip(f, f[1:] + f[:1]))
    parents = list(range(len(welded)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    for a, b in edges:
        parents[find(a)] = find(b)
    representatives = {}
    for i, point in enumerate(welded):
        representatives.setdefault(find(i), point)
    return {
        "name": name, "vertices": welded, "triangles": triangles,
        "tree": BVHTree.FromPolygons(welded, triangles, all_triangles=True),
        "box": {"min_mm": [min(p[i] for p in welded) for i in range(3)],
                "max_mm": [max(p[i] for p in welded) for i in range(3)]},
        "nonmanifold_edges": sum(count != 2 for count in edges.values()),
        "representatives": list(representatives.values()),
    }


def inside(point, solid):
    if solid["nonmanifold_edges"]:
        return None
    box = solid["box"]
    if any(point[i] < box["min_mm"][i] or point[i] > box["max_mm"][i] for i in range(3)):
        return False
    nearest = solid["tree"].find_nearest(point)
    if nearest[0] is None or nearest[3] <= 0.0001:
        return None
    parities = []
    for vector in ((1, .371, .529), (.413, 1, .677), (.293, .593, 1)):
        direction, origin, count = Vector(vector).normalized(), point.copy(), 0
        for _ in range(2048):
            hit = solid["tree"].ray_cast(origin, direction)
            if hit[0] is None:
                break
            count += 1
            origin = hit[0] + direction * WELD_MM * 4
        else:
            return None
        parities.append(count % 2)
    return bool(parities[0]) if len(set(parities)) == 1 else None


def intersection_volume(first, second):
    objects = []
    try:
        for item in (first, second):
            mesh = bpy.data.meshes.new("Fit_Boolean_Inspection")
            mesh.from_pydata([p * .001 for p in item["vertices"]], [], item["triangles"])
            mesh.update()
            obj = bpy.data.objects.new(mesh.name, mesh)
            bpy.context.scene.collection.objects.link(obj)
            objects.append(obj)
        modifier = objects[0].modifiers.new("Fit intersection only", "BOOLEAN")
        modifier.operation, modifier.solver, modifier.object = "INTERSECT", "EXACT", objects[1]
        modifier.use_self = True
        evaluated = objects[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bad_edges = sum(not edge.is_manifold for edge in bm.edges)
            volume = abs(bm.calc_volume(signed=True)) * 1e9 if bm.faces else 0
            return volume, bad_edges
        finally:
            bm.free()
            evaluated.to_mesh_clear()
    finally:
        for obj in objects:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(mesh)


def screen(first, second):
    widths = positive_box_overlap(first["box"], second["box"])
    if not widths:
        return None
    crossings = len(first["tree"].overlap(second["tree"]))
    membership = [inside(p, second) for p in first["representatives"]] + \
        [inside(p, first) for p in second["representatives"]]
    contained = any(value is True for value in membership)
    uncertain = bool(first["nonmanifold_edges"] or second["nonmanifold_edges"])
    if not crossings and not contained:
        if uncertain or None in membership:
            return {"status": "OPEN_GEOMETRY_UNRESOLVED" if uncertain else "BOUNDARY_OR_RAY_UNRESOLVED",
                    "box_overlap_mm": widths}
        return None
    result = {"box_overlap_mm": widths, "surface_triangle_pairs": crossings,
              "containment_detected": contained,
              "input_nonmanifold_edges": [first["nonmanifold_edges"], second["nonmanifold_edges"]]}
    if uncertain:
        return {**result, "status": "OPEN_GEOMETRY_UNRESOLVED"}
    volume, bad_edges = intersection_volume(first, second)
    result.update(intersection_volume_mm3=volume, intersection_nonmanifold_edges=bad_edges)
    if bad_edges:
        return {**result, "status": "BOOLEAN_TOPOLOGY_UNRESOLVED"}
    if volume > VOLUME_MM3:
        return {**result, "status": "POSITIVE_NOMINAL_SOLID_INTERSECTION"}
    # Surface contacts are not tolerance-qualified clearance.
    return {**result, "status": "CONTACT_OR_SUBTHRESHOLD_INTERSECTION"} if crossings else None


def self_test():
    def cube(name, minimum, maximum):
        a, b = minimum, maximum
        points = [Vector(p) for p in (
            (a[0], a[1], a[2]), (b[0], a[1], a[2]),
            (b[0], b[1], a[2]), (a[0], b[1], a[2]),
            (a[0], a[1], b[2]), (b[0], a[1], b[2]),
            (b[0], b[1], b[2]), (a[0], b[1], b[2]))]
        quads = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
        triangles = [(q[0], q[1], q[2]) for q in quads] + [(q[0], q[2], q[3]) for q in quads]
        return from_points(points, triangles, name)

    first = cube("unit", (0, 0, 0), (1, 1, 1))
    tests = (("overlap", (.5, 0, 0), (1.5, 1, 1), .5),
             ("contained", (.25, .25, .25), (.75, .75, .75), .125),
             ("touching", (1, 0, 0), (2, 1, 1), 0),
             ("separate", (2, 0, 0), (3, 1, 1), 0))
    results = {}
    for name, lo, hi, expected in tests:
        second = cube(name, lo, hi)
        volume, bad = intersection_volume(first, second)
        if bad or abs(volume - expected) > 1e-6:
            raise ValueError("solid-screen self test failed: " + name)
        found = screen(first, second)
        if expected and (not found or found["status"] != "POSITIVE_NOMINAL_SOLID_INTERSECTION"):
            raise ValueError("containment/crossing screen failed: " + name)
        results[name] = {"expected_mm3": expected, "actual_mm3": volume}
    return results
