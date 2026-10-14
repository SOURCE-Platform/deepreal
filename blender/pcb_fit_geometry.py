"""Pure geometry helpers for an unrouted mechanical PCB fit study."""

import math


def signed_area(points):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(points, points[1:] + points[:1])) / 2


def section_loops(vertices, triangles, plane, tolerance=0.0001):
    """Slice Blender XYZ millimetres at constant Y into closed X/Z loops.

    Reject ambiguous topology rather than approximating the board by its box.
    Quantization joins floating-point copies of shared triangle edges only.
    """
    edges = set()
    for triangle in triangles:
        points = [vertices[index] for index in triangle]
        distances = [point[1] - plane for point in points]
        if all(abs(distance) <= tolerance for distance in distances):
            raise ValueError("coplanar section face; choose another plane")
        cuts = set()
        for index in range(3):
            a, b = points[index], points[(index + 1) % 3]
            da, db = distances[index], distances[(index + 1) % 3]
            if abs(da) <= tolerance:
                cuts.add(tuple(round(a[i] / tolerance) for i in (0, 2)))
            if da * db < 0 and abs(da) > tolerance and abs(db) > tolerance:
                fraction = da / (da - db)
                cuts.add(tuple(round((a[i] + fraction * (b[i] - a[i])) /
                                     tolerance) for i in (0, 2)))
        if len(cuts) == 2:
            edges.add(tuple(sorted(cuts)))
        elif len(cuts) > 2:
            raise ValueError("ambiguous triangle section")
    if not edges:
        raise ValueError("no board section")
    neighbors = {}
    for a, b in edges:
        neighbors.setdefault(a, set()).add(b)
        neighbors.setdefault(b, set()).add(a)
    if any(len(adjacent) != 2 for adjacent in neighbors.values()):
        raise ValueError("section is not a set of simple closed loops")
    unseen = set(neighbors)
    loops = []
    while unseen:
        start = min(unseen)
        previous, current = None, start
        loop = []
        while True:
            loop.append(current)
            unseen.remove(current)
            following = min(neighbors[current] - {previous})
            previous, current = current, following
            if current == start:
                break
            if current not in unseen:
                raise ValueError("self-touching section")
        points = [[round(v * tolerance, 6) for v in point] for point in loop]
        # Remove triangulation subdivisions, not corners or hole geometry.
        changed = True
        while changed and len(points) > 3:
            changed = False
            for index, b in enumerate(points):
                a, c = points[index - 1], points[(index + 1) % len(points)]
                ab = [b[i] - a[i] for i in range(2)]
                bc = [c[i] - b[i] for i in range(2)]
                cross = abs(ab[0] * bc[1] - ab[1] * bc[0])
                if cross <= tolerance * math.hypot(*ab) and sum(
                        ab[i] * bc[i] for i in range(2)) >= 0:
                    points.pop(index)
                    changed = True
                    break
        if abs(signed_area(points)) <= tolerance ** 2:
            raise ValueError("zero-area section")
        loops.append(points)
    return sorted(loops, key=lambda p: abs(signed_area(p)), reverse=True)


def to_kicad(point, origin_mm, board_center_height_mm):
    """Keep the original KiCad datum fixed even when the outline gains a wing."""
    return [round(origin_mm[0] + point[0], 6),
            round(origin_mm[1] + board_center_height_mm - point[1], 6)]


def from_kicad(point, origin_mm, board_center_height_mm):
    return [round(point[0] - origin_mm[0], 6),
            round(origin_mm[1] + board_center_height_mm - point[1], 6)]


def positive_box_overlap(a, b):
    """Conservative body-box screen, not an exact solid intersection."""
    widths = [min(a["max_mm"][i], b["max_mm"][i]) -
              max(a["min_mm"][i], b["min_mm"][i]) for i in range(3)]
    return [round(v, 6) for v in widths] if min(widths) > 0.0001 else None
