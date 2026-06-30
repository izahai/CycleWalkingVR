import math

import pygame


WIDTH = 1000
HEIGHT = 700
FPS = 60

CIRCLE_RADIUS = 90.0
ORBIT_RADIUS = 220.0
SAMPLE_STEPS = 240
CIRCLE_SEGMENTS = 120
CONNECT_STRIDE = 6
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


def make_circle_points(center, normal, radius, segments=CIRCLE_SEGMENTS):
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


def build_swept_geometry(fixed_point):
    circles = []
    center_path = []
    for i in range(SAMPLE_STEPS):
        t = (math.tau * i) / SAMPLE_STEPS
        center = (
            ORBIT_RADIUS * math.cos(t),
            fixed_point[1],
            ORBIT_RADIUS * math.sin(t),
        )
        center_path.append(center)
        normal = (fixed_point[0] - center[0], fixed_point[1] - center[1], fixed_point[2] - center[2])
        circle_points = make_circle_points(center, normal, CIRCLE_RADIUS)
        circles.append(circle_points)
    return circles, center_path


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swept Shape of Rotating Circle (drag to orbit view)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier", 16)

    yaw = 0.4
    pitch = 0.35
    dragging = False
    last_mouse = None

    fixed_point = (0.0, 0.0, 0.0)
    circles, center_path = build_swept_geometry(fixed_point)
    bar_half = scale((0.0, 1.0, 0.0), BAR_LENGTH * 0.5)
    bar_start = add(fixed_point, scale(bar_half, -1))
    bar_end = add(fixed_point, bar_half)

    running = True
    while running:
        clock.tick(FPS)
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
                    yaw = (yaw + math.tau) % math.tau
                    pitch = (pitch + math.tau) % math.tau
                last_mouse = event.pos
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill((14, 14, 20))

        # Draw swept surface as wireframe ribbons.
        for circle in circles:
            projected_circle = []
            for point in circle:
                rotated = rotate_yaw_pitch(point, yaw, pitch)
                camera_space = (rotated[0], rotated[1], rotated[2] + CAMERA_DIST)
                projected = project(camera_space)
                if projected:
                    projected_circle.append(projected)
            if projected_circle:
                pygame.draw.aalines(screen, (90, 190, 230), False, projected_circle)

        for i in range(len(circles) - 1):
            a = circles[i]
            b = circles[i + 1]
            for j in range(0, min(len(a), len(b)), CONNECT_STRIDE):
                pa = rotate_yaw_pitch(a[j], yaw, pitch)
                pb = rotate_yaw_pitch(b[j], yaw, pitch)
                pa = (pa[0], pa[1], pa[2] + CAMERA_DIST)
                pb = (pb[0], pb[1], pb[2] + CAMERA_DIST)
                pa2 = project(pa)
                pb2 = project(pb)
                if pa2 and pb2:
                    pygame.draw.aaline(screen, (70, 140, 190), pa2, pb2)

        projected_path = []
        for point in center_path:
            rotated = rotate_yaw_pitch(point, yaw, pitch)
            projected = project((rotated[0], rotated[1], rotated[2] + CAMERA_DIST))
            if projected:
                projected_path.append(projected)
        if projected_path:
            pygame.draw.aalines(screen, (255, 160, 80), False, projected_path)

        rotated_bar_start = rotate_yaw_pitch(bar_start, yaw, pitch)
        rotated_bar_end = rotate_yaw_pitch(bar_end, yaw, pitch)
        bar_start_screen = project((rotated_bar_start[0], rotated_bar_start[1], rotated_bar_start[2] + CAMERA_DIST))
        bar_end_screen = project((rotated_bar_end[0], rotated_bar_end[1], rotated_bar_end[2] + CAMERA_DIST))
        if bar_start_screen and bar_end_screen:
            pygame.draw.line(screen, (160, 150, 255), bar_start_screen, bar_end_screen, 3)

        label = font.render("Swept surface wireframe - drag to orbit view", True, (220, 220, 230))
        screen.blit(label, (12, 12))
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
