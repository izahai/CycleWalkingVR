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

def line_from_point_and_vector(point, vector):
    px, py, pz = point
    vx, vy, vz = vector

    def line(t):
        return [
            px + vx * t,
            py + vy * t,
            pz + vz * t,
        ]

    return line

def closest_point_on_line(point_on_line, direction, point):
    px, py, pz = point_on_line
    vx, vy, vz = direction
    qx, qy, qz = point

    # Vector from line point to query point
    wx = qx - px
    wy = qy - py
    wz = qz - pz

    # Dot products
    vv = vx*vx + vy*vy + vz*vz
    if vv < 1e-12:
        raise ValueError("Direction vector has zero length")

    t = (wx*vx + wy*vy + wz*vz) / vv

    return [
        px + vx * t,
        py + vy * t,
        pz + vz * t,
    ]
    
def distance_between_points(a, b):
    ax, ay, az = a
    bx, by, bz = b

    dx = bx - ax
    dy = by - ay
    dz = bz - az

    return math.sqrt(dx*dx + dy*dy + dz*dz)

def y_direction(cur, last):
    """
    Compare Y components of two 3D points.

    Returns:
        1  -> y increased
        -1 -> y decreased
        0  -> no change
    """
    if cur[1] > last[1]:
        return 1
    elif cur[1] < last[1]:
        return -1
    else:
        return 0

def circle_points_at_distance(
    circle_center,
    circle_normal,
    circle_radius,
    point,
    d,
    offset=0.1,
    eps=1e-9,
):
    C = np.asarray(circle_center, float)
    n = np.asarray(circle_normal, float)
    P = np.asarray(point, float)

    n_norm = np.linalg.norm(n)
    if n_norm < eps:
        raise ValueError("Circle normal has zero length")
    n = n / n_norm

    # Effective distance with tolerance
    d_min = max(d - offset, 0.0)
    d_max = d + offset

    # Distance from point to circle plane
    h = abs(np.dot(P - C, n))

    # Sphere shell does not reach plane
    if h > d_max + eps:
        return []

    # Projection of P onto circle plane
    P_proj = P - np.dot(P - C, n) * n

    # Radius range of intersection circle (sphere ∩ plane)
    rho_min = math.sqrt(max(d_min * d_min - h * h, 0.0))
    rho_max = math.sqrt(max(d_max * d_max - h * h, 0.0))

    v = P_proj - C
    D = np.linalg.norm(v)

    # No intersection even with tolerance
    if D > circle_radius + rho_max + eps:
        return []
    if D < abs(circle_radius - rho_max) - eps:
        return []

    # Use midpoint radius for point construction
    rho = 0.5 * (rho_min + rho_max)

    # Tangent (one solution)
    if abs(D - (circle_radius + rho)) < eps or abs(D - abs(circle_radius - rho)) < eps:
        if D < eps:
            return []
        dir_vec = v / D
        return [(C + circle_radius * dir_vec).tolist()]

    # Two intersection points
    u = v / D
    w = np.cross(n, u)

    a = (circle_radius**2 - rho**2 + D**2) / (2 * D)
    h2 = circle_radius**2 - a**2
    h2 = max(h2, 0.0)
    b = math.sqrt(h2)

    p0 = C + a * u
    p1 = p0 + b * w
    p2 = p0 - b * w

    return [p1.tolist(), p2.tolist()]


def project_point_to_circle_rim(center, normal, radius, point, eps=1e-12):
    """
    Project a 3D point onto the closest point on a circle rim.

    Args:
        center: [x, y, z] circle center
        normal: [nx, ny, nz] circle normal
        radius: circle radius
        point:  [x, y, z] point to project

    Returns:
        [x, y, z] point on the circle rim
    """
    cx, cy, cz = center
    nx, ny, nz = normal
    px, py, pz = point

    # Normalize normal
    n_len = math.sqrt(nx*nx + ny*ny + nz*nz)
    if n_len < eps:
        raise ValueError("Normal vector has zero length")
    nx /= n_len
    ny /= n_len
    nz /= n_len

    # Vector from center to point
    vx = px - cx
    vy = py - cy
    vz = pz - cz

    # Remove normal component (project onto plane)
    d = vx*nx + vy*ny + vz*nz
    pxp = px - d*nx
    pyp = py - d*ny
    pzp = pz - d*nz

    # Direction from center in plane
    dx = pxp - cx
    dy = pyp - cy
    dz = pzp - cz

    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    if length < eps:
        raise ValueError("Point projects to circle center; direction undefined")

    # Scale to circle radius
    scale = radius / length

    return [
        cx + dx * scale,
        cy + dy * scale,
        cz + dz * scale,
    ]
    
def angle_deg_from_ref(origin, ref_point, point):
    # Reference vector (origin -> ref_point)
    v0y = ref_point[1] - origin[1]
    v0z = ref_point[2] - origin[2]

    # Target vector (origin -> point)
    v1y = point[1] - origin[1]
    v1z = point[2] - origin[2]

    # Angles in plane
    a0 = math.atan2(v0z, v0y)
    a1 = math.atan2(v1z, v1y)

    # Difference, wrapped to [0, 360)
    return (math.degrees(a1 - a0)) % 360.0
