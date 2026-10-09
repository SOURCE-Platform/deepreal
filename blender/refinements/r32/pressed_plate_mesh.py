"""Continuous rounded steel plate with a smooth, line-centered logo relief."""

import math
from collections import defaultdict

import bpy

MM = .001
WIDTH = 112.0
HEIGHT = 26.0
CORNER = 1.6
Z_CENTER = -14.0
BACK_Y = 1.9
FACE_Y = 2.25
LOGO_WIDTH = 103.0
GROOVE_RADIUS = .95
GROOVE_DEPTH = .15
GRID = .18
PROFILE = "rounded"


def artwork_segments(strokes):
    points = [p for stroke in strokes for p in stroke]
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    scale = LOGO_WIDTH / (xmax - xmin)
    xmid, ymid = (xmax + xmin) / 2, (ymax + ymin) / 2
    transformed = [[((p[0] - xmid) * scale,
                     Z_CENTER + (ymid - p[1]) * scale)
                    for p in stroke] for stroke in strokes]
    segments = [(a, b) for stroke in transformed
                for a, b in zip(stroke, stroke[1:])]
    logo_height = (ymax - ymin) * scale
    return segments, logo_height


def spatial_index(segments):
    buckets = defaultdict(list)
    cell = GROOVE_RADIUS * 2
    for idx, (a, b) in enumerate(segments):
        lo_x = math.floor((min(a[0], b[0]) - GROOVE_RADIUS) / cell)
        hi_x = math.floor((max(a[0], b[0]) + GROOVE_RADIUS) / cell)
        lo_z = math.floor((min(a[1], b[1]) - GROOVE_RADIUS) / cell)
        hi_z = math.floor((max(a[1], b[1]) + GROOVE_RADIUS) / cell)
        for ix in range(lo_x, hi_x + 1):
            for iz in range(lo_z, hi_z + 1):
                buckets[ix, iz].append(idx)
    return buckets, cell


def depth_at(x, z, segments, buckets, cell):
    closest = GROOVE_RADIUS ** 2
    for idx in buckets.get((math.floor(x / cell), math.floor(z / cell)), ()):
        (ax, az), (bx, bz) = segments[idx]
        dx, dz = bx - ax, bz - az
        length_sq = dx * dx + dz * dz
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) /
                              length_sq)) if length_sq else 0
        d_sq = (x - ax - t * dx) ** 2 + (z - az - t * dz) ** 2
        closest = min(closest, d_sq)
    if closest >= GROOVE_RADIUS ** 2:
        return 0.0
    u = 1 - math.sqrt(closest) / GROOVE_RADIUS
    if PROFILE == "creased":
        # Zero slope at the outer shoulder, two meeting slopes at the line.
        return GROOVE_DEPTH * u * u
    # Rounded comparison profile has a horizontal tangent at its bottom.
    return GROOVE_DEPTH * u * u * (3 - 2 * u)


def rounded_half_height(x):
    across = abs(x)
    half = HEIGHT / 2
    if across <= WIDTH / 2 - CORNER:
        return half
    run = across - (WIDTH / 2 - CORNER)
    return half - CORNER + math.sqrt(max(0, CORNER ** 2 - run ** 2))


def build(strokes, material, collection):
    segments, logo_height = artwork_segments(strokes)
    buckets, cell = spatial_index(segments)
    nx = math.ceil(WIDTH / GRID)
    nz = math.ceil(HEIGHT / GRID)
    vertices, faces = [], []
    for i in range(nx + 1):
        x = -WIDTH / 2 + WIDTH * i / nx
        zhalf = rounded_half_height(x)
        for j in range(nz + 1):
            z = Z_CENTER - zhalf + 2 * zhalf * j / nz
            drop = depth_at(x, z, segments, buckets, cell)
            vertices.append((x * MM, (FACE_Y - drop) * MM, z * MM))
    row = nz + 1
    for i in range(nx):
        for j in range(nz):
            a = i * row + j
            faces.append((a, a + 1, a + row + 1, a + row))
    front_count = len(vertices)
    # Perimeter goes counterclockwise when viewed from the laptop side.
    perimeter = [i * row for i in range(nx + 1)]
    perimeter += [nx * row + j for j in range(1, nz + 1)]
    perimeter += [i * row + nz for i in range(nx - 1, -1, -1)]
    perimeter += [j for j in range(nz - 1, 0, -1)]
    for index in perimeter:
        x, _, z = vertices[index]
        vertices.append((x, BACK_Y * MM, z))
    for k, front in enumerate(perimeter):
        next_k = (k + 1) % len(perimeter)
        faces.append((front, perimeter[next_k],
                      front_count + next_k, front_count + k))
    faces.append(tuple(front_count + k for k in range(len(perimeter))))
    mesh = bpy.data.meshes.new("Coined_Logo_Continuous_Surface")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("DeepReal_Tall_Pressed_430_Steel_Target", mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons[:nx * nz]:
        poly.use_smooth = True
    obj["Plate_Size_mm"] = f"{WIDTH} x {HEIGHT} x {FACE_Y-BACK_Y:.2f}"
    obj["Logo_Width_mm"] = LOGO_WIDTH
    obj["Logo_Height_mm"] = round(logo_height, 2)
    obj["Max_Logo_Depth_mm"] = GROOVE_DEPTH
    obj["Groove_Shoulder_Radius_mm"] = GROOVE_RADIUS
    obj["Groove_Profile"] = PROFILE
    obj["Concept_Only"] = "visual coined finish; manufacturing not validated"
    return obj, logo_height
