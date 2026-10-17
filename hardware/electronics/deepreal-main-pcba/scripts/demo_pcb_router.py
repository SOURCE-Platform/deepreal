"""Geometry-only routing for a disclosed nonworking visual demo.

Pad pairs are chosen for appearance, NOT from a circuit netlist.
Never use this module to produce fabrication or electrical design evidence.
"""

import heapq
import math


def inside_polygon(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            crossing = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing:
                inside = not inside
    return inside


def simplify(points):
    result = []
    for point in points:
        if len(result) > 1:
            a, b = result[-2:]
            cross = (b[0] - a[0]) * (point[1] - b[1]) - (b[1] - a[1]) * (point[0] - b[0])
            dot = (b[0] - a[0]) * (point[0] - b[0]) + (b[1] - a[1]) * (point[1] - b[1])
            if abs(cross) < 1e-8 and dot > 0:
                result.pop()
        result.append(point)
    return result


class DemoRouter:
    def __init__(self, outlines, pads, existing_tracks=(), step=.2):
        self.step = step
        self.origin = [min(p[i] for loop in outlines for p in loop) for i in (0, 1)]
        maximum = [max(p[i] for loop in outlines for p in loop) for i in (0, 1)]
        self.nx, self.ny = [math.ceil((maximum[i] - self.origin[i]) / step) + 1 for i in (0, 1)]
        self.size = self.nx * self.ny
        self.inside = set()
        self.obstacles = [set(), set()]
        self.occupied = [set(), set()]
        self.routes, self.vias, self.failures = [], {}, 0
        # Odd/even polygon membership also excludes the native mounting cutout.
        for y in range(self.ny):
            for x in range(self.nx):
                point = self.point(y * self.nx + x)
                if all(sum(inside_polygon((point[0] + dx, point[1] + dy), loop)
                           for loop in outlines) % 2
                       for dx, dy in ((-.25, -.25), (.25, -.25), (.25, .25), (-.25, .25))):
                    self.inside.add(y * self.nx + x)
        for pad in pads:
            for layer in pad["layers"]:
                # Rotated pad AABBs are deliberately conservative.
                self.block_box(layer, pad["position"], [v / 2 + .09 for v in pad["aabb_size"]])
        for track in existing_tracks:
            self.block_line(track["layer"], track["start"], track["end"], track["width"] / 2 + .12)

    def point(self, cell):
        return [round(self.origin[0] + (cell % self.nx) * self.step, 5),
                round(self.origin[1] + (cell // self.nx) * self.step, 5)]

    def cell(self, point):
        x, y = [round((point[i] - self.origin[i]) / self.step) for i in (0, 1)]
        return y * self.nx + x

    def nearby(self, point, radius):
        center = self.cell(point)
        x, y = center % self.nx, center // self.nx
        reach = math.ceil(radius / self.step)
        for yy in range(max(0, y - reach), min(self.ny, y + reach + 1)):
            for xx in range(max(0, x - reach), min(self.nx, x + reach + 1)):
                cell = yy * self.nx + xx
                p = self.point(cell)
                if math.hypot(p[0] - point[0], p[1] - point[1]) <= radius + .001:
                    yield cell

    def block_box(self, layer, center, half):
        x0, y0 = [math.floor((center[i] - half[i] - self.origin[i]) / self.step) for i in (0, 1)]
        x1, y1 = [math.ceil((center[i] + half[i] - self.origin[i]) / self.step) for i in (0, 1)]
        for y in range(max(0, y0), min(self.ny, y1 + 1)):
            for x in range(max(0, x0), min(self.nx, x1 + 1)):
                self.obstacles[layer].add(y * self.nx + x)

    def block_line(self, layer, start, end, radius):
        count = max(1, math.ceil(math.dist(start, end) / (self.step / 2)))
        for i in range(count + 1):
            point = [start[k] + (end[k] - start[k]) * i / count for k in (0, 1)]
            self.obstacles[layer].update(self.nearby(point, radius))

    def route(self, start, goal, width=.16, label="illustrative", end_via=False):
        first, last = self.cell(start["position"]), self.cell(goal["position"])
        if first not in self.inside or last not in self.inside:
            self.failures += 1
            return False
        exemptions = [set(), set()]
        for endpoint in (start, goal):
            for layer in endpoint["layers"]:
                exemptions[layer].update(self.nearby(endpoint["position"], .48))

        def free(cell, layer):
            return (cell in self.inside and cell not in self.occupied[layer]
                    and (cell not in self.obstacles[layer] or cell in exemptions[layer]))

        goals = {layer * self.size + last for layer in goal["layers"]}

        def heuristic(cell, layer):
            dx, dy = abs(cell % self.nx - last % self.nx), abs(cell // self.nx - last // self.nx)
            return max(dx, dy) + .41421356 * min(dx, dy) + (0 if layer in goal["layers"] else 9)

        queue, scores, previous = [], {}, {}
        for layer in start["layers"]:
            node = layer * self.size + first
            if free(first, layer):
                scores[node] = 0
                heapq.heappush(queue, (heuristic(first, layer), 0, node))
        found = None
        expansions = 0
        while queue and expansions < 22000:
            _, score, node = heapq.heappop(queue)
            if score != scores.get(node):
                continue
            if node in goals:
                found = node
                break
            expansions += 1
            layer, cell = divmod(node, self.size)
            x, y = cell % self.nx, cell // self.nx
            neighbors = []
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                xx, yy = x + dx, y + dy
                other = yy * self.nx + xx
                if not 0 <= xx < self.nx or not 0 <= yy < self.ny or not free(other, layer):
                    continue
                if dx and dy and not (free(y * self.nx + xx, layer) and free(yy * self.nx + x, layer)):
                    continue
                neighbors.append((layer * self.size + other, 1.41421356 if dx and dy else 1))
            if free(cell, 1 - layer) and all(
                    c not in self.obstacles[1 - layer] and c not in self.occupied[1 - layer]
                    for c in self.nearby(self.point(cell), .24)):
                neighbors.append(((1 - layer) * self.size + cell, 9))
            for other, cost in neighbors:
                candidate = score + cost
                if candidate < scores.get(other, math.inf):
                    scores[other], previous[other] = candidate, node
                    ll, cc = divmod(other, self.size)
                    heapq.heappush(queue, (candidate + heuristic(cc, ll), candidate, other))
        if found is None:
            self.failures += 1
            return False
        nodes = [found]
        while nodes[-1] in previous:
            nodes.append(previous[nodes[-1]])
        nodes.reverse()
        layer, _ = divmod(nodes[0], self.size)
        paths = [{"layer": layer, "points": [start["position"], self.point(first)]}]
        for a, b in zip(nodes, nodes[1:]):
            old_layer, old_cell = divmod(a, self.size)
            new_layer, new_cell = divmod(b, self.size)
            if old_layer != new_layer:
                self.vias[tuple(self.point(old_cell))] = .48
                paths.append({"layer": new_layer, "points": [self.point(new_cell)]})
            else:
                paths[-1]["points"].append(self.point(new_cell))
        paths[-1]["points"].append(goal["position"])
        for path in paths:
            unique = [p for i, p in enumerate(path["points"]) if i == 0 or p != path["points"][i - 1]]
            path["points"] = simplify(unique)
        paths = [p for p in paths if len(p["points"]) > 1]
        if not paths:
            return False
        self.routes.append({
            "id": f"DEMO_{len(self.routes) + 1:04d}", "purpose": label, "width_mm": width,
            "endpoints": [{k: endpoint[k] for k in ("ref", "pad", "position")} for endpoint in (start, goal)],
            "paths": paths,
        })
        for node in nodes:
            layer, cell = divmod(node, self.size)
            self.occupied[layer].update(self.nearby(self.point(cell), .205))
        if end_via:
            self.vias[tuple(goal["position"])] = .48
        for position in self.vias:
            for layer in (0, 1):
                self.occupied[layer].update(self.nearby(position, .28))
        return True


def design_demo(geometry):
    pads = geometry["pads"]
    router = DemoRouter(geometry["outlines"], pads, geometry["existing_surface_tracks"])
    by_ref = {}
    for pad in pads:
        if not pad["net"] and pad["pad"] and not pad["ref"].startswith("TP"):
            by_ref.setdefault(pad["ref"], []).append(pad)
    used = set()

    def key(pad):
        return pad["ref"], pad["pad"]

    def available(ref):
        seen = set()
        result = []
        for pad in by_ref.get(ref, []):
            k = key(pad)
            if k not in used and k not in seen:
                result.append(pad)
                seen.add(k)
        return result

    def bus(a, b, count, width=.16):
        first, second = available(a), available(b)
        if not first or not second:
            return
        ca, cb = geometry["centers"][a], geometry["centers"][b]
        distance = math.dist(ca, cb)
        direction = [(cb[i] - ca[i]) / distance for i in (0, 1)]
        tangent = [-direction[1], direction[0]]

        def select(items, center, sign):
            edge = sorted(items, key=lambda p: -sign * sum(
                (p["position"][i] - center[i]) * direction[i] for i in (0, 1)))[:count]
            return sorted(edge, key=lambda p: sum(p["position"][i] * tangent[i] for i in (0, 1)))

        for start, end in zip(select(first, ca, 1), select(second, cb, -1)):
            if router.route(start, end, width, f"illustrative {a}-{b} bus"):
                used.update((key(start), key(end)))

    for a, b, count in [
            ("U1", "U4", 24), ("U1", "U15", 16), ("U1", "U2", 12),
            ("U1", "U3", 12), ("U2", "J2", 14), ("U3", "J3", 14),
            ("U5", "U6", 4), ("U5", "U7", 4), ("U5", "U1", 4),
            ("U6", "L3", 3), ("U7", "L4", 3), ("U8", "L1", 3),
            ("U13", "J4", 4), ("U14", "J5", 4), ("U16", "U1", 4),
            ("U17", "U2", 3), ("U17", "U3", 3), ("U18", "U13", 3),
            ("U19", "U14", 3)]:
        bus(a, b, count, .24 if a in ("U5", "U6", "U7", "U8") else .16)

    # Distribute local details across the whole board, not a single routed island.
    major = [r for r in by_ref if r.startswith("U") and r not in ("U10", "U11", "U12", "U20", "U23")]
    for ref in sorted(by_ref):
        if not ref.startswith(("C", "R", "D", "Y", "MK")):
            continue
        local = available(ref)
        if not local:
            continue
        center = geometry["centers"][ref]
        nearest = sorted(major, key=lambda r: math.dist(center, geometry["centers"][r]))[:2]
        candidates = sorted([p for r in nearest for p in available(r)],
                            key=lambda p: math.dist(local[0]["position"], p["position"]))
        for target in candidates[:4]:
            if math.dist(local[0]["position"], target["position"]) > 13:
                continue
            if router.route(local[0], target, .16, "illustrative local component connection"):
                used.update((key(local[0]), key(target)))
                break

    # Perimeter escape stubs and via rings add recognizable BGA fan-out detail.
    for ref in ("U1", "U2", "U3", "U4", "U15", "U5", "U13", "U14"):
        if ref not in geometry["centers"]:
            continue
        center = geometry["centers"][ref]
        outer = sorted(available(ref), key=lambda p: -math.dist(p["position"], center))
        successes = 0
        for pad in outer:
            dx, dy = [pad["position"][i] - center[i] for i in (0, 1)]
            length = math.hypot(dx, dy)
            if not length:
                continue
            end = router.point(router.cell([pad["position"][0] + dx / length * 1.2,
                                           pad["position"][1] + dy / length * 1.2]))
            if any(c in router.obstacles[l] or c in router.occupied[l]
                   for l in (0, 1) for c in router.nearby(end, .25)):
                continue
            goal = {"ref": "VISUAL_VIA", "pad": str(len(router.vias) + 1),
                    "position": end, "layers": pad["layers"]}
            if router.route(pad, goal, .12, "illustrative package fan-out", end_via=True):
                used.add(key(pad))
                successes += 1
            if successes >= 18:
                break
    return {
        "connections": router.routes,
        "vias": [{"position_mm": list(point), "diameter_mm": diameter, "drill_mm": .22}
                 for point, diameter in sorted(router.vias.items())],
        "unrouted_visual_attempts": router.failures,
    }
