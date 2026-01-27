import json
import math
import random

import pygame
import numpy as np


def load_positions(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "samples" in data:
        samples = data["samples"]
    elif isinstance(data, list):
        samples = data
    else:
        raise ValueError("Unrecognized JSON format; expected list or {samples: [...]}.")

    positions = []
    for item in samples:
        if isinstance(item, dict):
            pos = item.get("pos") or item.get("position") or item.get("p")
        else:
            pos = item

        if not pos or len(pos) < 3:
            continue

        positions.append([float(pos[0]), float(pos[1]), float(pos[2])])

    return positions


def choose_random_points(points, k):
    if k <= 0:
        return []
    k = min(k, len(points))
    return random.sample(points, k)


def centroid(points):
    if not points:
        return None

    indices = list(range(len(points)))
    random.shuffle(indices)

    centers = []
    for i in range(0, len(indices) - 2, 3):
        a = points[indices[i]]
        b = points[indices[i + 1]]
        c = points[indices[i + 2]]

        ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
        ac = [c[0] - a[0], c[1] - a[1], c[2] - a[2]]
        n = [
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        ]
        n2 = n[0] * n[0] + n[1] * n[1] + n[2] * n[2]
        if n2 < 1e-12:
            continue

        ab2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]
        ac2 = ac[0] * ac[0] + ac[1] * ac[1] + ac[2] * ac[2]

        nxab = [
            n[1] * ab[2] - n[2] * ab[1],
            n[2] * ab[0] - n[0] * ab[2],
            n[0] * ab[1] - n[1] * ab[0],
        ]
        acxn = [
            ac[1] * n[2] - ac[2] * n[1],
            ac[2] * n[0] - ac[0] * n[2],
            ac[0] * n[1] - ac[1] * n[0],
        ]

        scale = 1.0 / (2.0 * n2)
        center = [
            a[0] + (ac2 * nxab[0] + ab2 * acxn[0]) * scale,
            a[1] + (ac2 * nxab[1] + ab2 * acxn[1]) * scale,
            a[2] + (ac2 * nxab[2] + ab2 * acxn[2]) * scale,
        ]
        centers.append(center)

    if not centers:
        return None

    sx = sy = sz = 0.0
    for x, y, z in centers:
        sx += x
        sy += y
        sz += z
    n = float(len(centers))
    return [sx / n, sy / n, sz / n]


def best_fit_3d_circle(points):
    if not points:
        return None

    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[1] < 3:
        return None

    center = np.asarray(centroid(points), dtype=float)
    centered = pts - center
    cov = centered.T @ centered
    _, _, vh = np.linalg.svd(cov)
    normal = vh[-1]
    norm = np.linalg.norm(normal)
    if norm < 1e-12:
        return None
    normal = normal / norm
    deltas = pts - center
    radii = np.linalg.norm(deltas, axis=1)
    radius = float(np.mean(radii)) if radii.size else 0.0
    return center.tolist(), normal.tolist(), radius


def line_origin_to_highest_y(points, origin):
    if not points:
        return None

    max_y = max(p[1] for p in points)
    highest = [origin[0], max_y, origin[2]]
    return origin, highest


def angle_deg_from_highest(origin, highest, point):
    # Compute angle in YZ plane from origin->highest to origin->point.
    v0y = highest[1] - origin[1]
    v0z = highest[2] - origin[2]
    v1y = point[1] - origin[1]
    v1z = point[2] - origin[2]

    a0 = math.atan2(v0z, v0y)
    a1 = math.atan2(v1z, v1y)
    deg = math.degrees(a1 - a0) % 360.0
    return deg


def visualize_points(points, center, window_size=(640, 640)):
    if not points:
        return

    pygame.init()
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Sphere Positions (YZ projection)")
    clock = pygame.time.Clock()

    # Project to YZ plane for visualization.
    yz_points = [(p[1], p[2]) for p in points]
    cy, cz = center[1], center[2]
    line = line_origin_to_highest_y(points, center)

    ys = [p[0] for p in yz_points]
    zs = [p[1] for p in yz_points]
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    pad = 40
    w, h = window_size
    span_y = max(max_y - min_y, 1e-6)
    span_z = max(max_z - min_z, 1e-6)

    def to_screen(y, z):
        x = pad + (y - min_y) / span_y * (w - 2 * pad)
        y_screen = h - (pad + (z - min_z) / span_z * (h - 2 * pad))
        return int(x), int(y_screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill((18, 18, 22))

        # Draw points.
        for y, z in yz_points:
            px, py = to_screen(y, z)
            pygame.draw.circle(screen, (0, 180, 255), (px, py), 3)

        # Draw centroid.
        cx, cy_screen = to_screen(cy, cz)
        pygame.draw.circle(screen, (255, 80, 80), (cx, cy_screen), 6)
        pygame.draw.line(screen, (255, 80, 80), (cx - 8, cy_screen), (cx + 8, cy_screen), 2)
        pygame.draw.line(screen, (255, 80, 80), (cx, cy_screen - 8), (cx, cy_screen + 8), 2)

        # Draw line from center to highest Y point.
        if line is not None:
            origin, highest = line
            ox, oy = to_screen(origin[1], origin[2])
            hx, hy = to_screen(highest[1], highest[2])
            pygame.draw.line(screen, (255, 200, 80), (ox, oy), (hx, hy), 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
