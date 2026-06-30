import math
import sys
from collections import deque

import pygame


WIDTH = 1000
HEIGHT = 700
FPS = 60

CIRCLE_RADIUS = 90.0
ORBIT_RADIUS = 220.0
ORBIT_SPEED = 0.6  # radians per second
TRAIL_LENGTH = 70
BAR_LENGTH = 260.0
FOV = 500.0
CAMERA_DIST = 520.0


def normalize(v):
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z)
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def rotate_yaw_pitch(point, yaw, pitch):
    x, y, z = point
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)

    # Yaw around Y axis
    xz = x * cy + z * sy
    zz = -x * sy + z * cy

    # Pitch around X axis
    yz = y * cp - zz * sp
    zz2 = y * sp + zz * cp
    return (xz, yz, zz2)


def project(point):
    x, y, z = point
    if z <= 1:
        return None
    scale_factor = FOV / z
    screen_x = int(WIDTH * 0.5 + x * scale_factor)
    screen_y = int(HEIGHT * 0.5 - y * scale_factor)
    return (screen_x, screen_y)


def make_circle_points(center, normal, radius, segments=120):
    n = normalize(normal)
    if n == (0.0, 0.0, 0.0):
        return []
    up = (0.0, 1.0, 0.0)
    if abs(n[1]) > 0.9:
        up = (1.0, 0.0, 0.0)
    tangent = normalize(cross(n, up))
    bitangent = cross(n, tangent)

    points = []
    for i in range(segments + 1):
        angle = (math.tau * i) / segments
        offset = add(scale(tangent, math.cos(angle) * radius), scale(bitangent, math.sin(angle) * radius))
        points.append(add(center, offset))
    return points


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Rotating Circle (drag to orbit view)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier", 16)

    yaw = 0.4
    pitch = 0.35
    dragging = False
    last_mouse = None
    time_accum = 0.0
    trail = deque(maxlen=TRAIL_LENGTH)

    fixed_point = (0.0, 0.0, 0.0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        time_accum += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                last_mouse = None
            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                if last_mouse:
                    dx = mx - last_mouse[0]
                    dy = my - last_mouse[1]
                    yaw += dx * 0.005
                    pitch += dy * 0.005
                    pitch = max(-1.4, min(1.4, pitch))
                last_mouse = event.pos
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        orbit_angle = time_accum * ORBIT_SPEED
        center = (
            ORBIT_RADIUS * math.cos(orbit_angle),
            fixed_point[1],
            ORBIT_RADIUS * math.sin(orbit_angle),
        )
        normal = (fixed_point[0] - center[0], fixed_point[1] - center[1], fixed_point[2] - center[2])

        circle_points = make_circle_points(center, normal, CIRCLE_RADIUS)
        trail.append((circle_points, center))
        bar_dir = (0.0, 1.0, 0.0)
        bar_half = scale(bar_dir, BAR_LENGTH * 0.5)
        bar_start = add(fixed_point, scale(bar_half, -1))
        bar_end = add(fixed_point, bar_half)

        screen.fill((18, 16, 28))
        trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        if trail:
            count = len(trail)
            for idx, (trail_circle, trail_center) in enumerate(trail):
                alpha = 40 if count == 1 else int(30 + 170 * (idx / (count - 1)))
                trail_color = (90, 190, 230, alpha)
                line_color = (240, 160, 70, max(20, alpha - 30))

                projected_trail = []
                for point in trail_circle:
                    rotated = rotate_yaw_pitch(point, yaw, pitch)
                    camera_space = (rotated[0], rotated[1], rotated[2] + CAMERA_DIST)
                    projected = project(camera_space)
                    if projected:
                        projected_trail.append(projected)

                if projected_trail:
                    pygame.draw.lines(trail_surface, trail_color, False, projected_trail, 2)

                rotated_center_trail = rotate_yaw_pitch(trail_center, yaw, pitch)
                rotated_fixed_trail = rotate_yaw_pitch(fixed_point, yaw, pitch)
                center_trail_screen = project(
                    (rotated_center_trail[0], rotated_center_trail[1], rotated_center_trail[2] + CAMERA_DIST)
                )
                fixed_trail_screen = project(
                    (rotated_fixed_trail[0], rotated_fixed_trail[1], rotated_fixed_trail[2] + CAMERA_DIST)
                )
                if center_trail_screen and fixed_trail_screen:
                    pygame.draw.line(trail_surface, line_color, fixed_trail_screen, center_trail_screen, 2)

        # Build projected geometry
        projected_circle = []
        for point in circle_points:
            rotated = rotate_yaw_pitch(point, yaw, pitch)
            camera_space = (rotated[0], rotated[1], rotated[2] + CAMERA_DIST)
            projected = project(camera_space)
            if projected:
                projected_circle.append(projected)

        rotated_center = rotate_yaw_pitch(center, yaw, pitch)
        rotated_fixed = rotate_yaw_pitch(fixed_point, yaw, pitch)
        rotated_bar_start = rotate_yaw_pitch(bar_start, yaw, pitch)
        rotated_bar_end = rotate_yaw_pitch(bar_end, yaw, pitch)

        center_screen = project((rotated_center[0], rotated_center[1], rotated_center[2] + CAMERA_DIST))
        fixed_screen = project((rotated_fixed[0], rotated_fixed[1], rotated_fixed[2] + CAMERA_DIST))
        bar_start_screen = project(
            (rotated_bar_start[0], rotated_bar_start[1], rotated_bar_start[2] + CAMERA_DIST)
        )
        bar_end_screen = project((rotated_bar_end[0], rotated_bar_end[1], rotated_bar_end[2] + CAMERA_DIST))

        if projected_circle:
            pygame.draw.lines(screen, (100, 208, 255), False, projected_circle, 2)

        if center_screen and fixed_screen:
            pygame.draw.line(screen, (255, 170, 60), fixed_screen, center_screen, 2)
            pygame.draw.circle(screen, (255, 95, 95), fixed_screen, 6)
            pygame.draw.circle(screen, (100, 255, 140), center_screen, 5)
        if bar_start_screen and bar_end_screen:
            pygame.draw.line(screen, (160, 150, 255), bar_start_screen, bar_end_screen, 3)
        if trail:
            screen.blit(trail_surface, (0, 0))

        overlay = [
            "Left-drag: orbit view",
            "Circle center orbits around fixed point",
            "Line from center to fixed point is circle normal",
            "Fixed vertical bar through fixed point (normal stays orthogonal)",
        ]
        for i, text in enumerate(overlay):
            label = font.render(text, True, (220, 220, 230))
            screen.blit(label, (12, 12 + i * 18))

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
