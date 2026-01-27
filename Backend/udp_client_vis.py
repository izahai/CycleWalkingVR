import json
import math
import socket
import threading
import time

import pygame


UDP_IP = "127.0.0.1"
UDP_PORT = 9000
SOCKET_TIMEOUT_S = 0.1

WINDOW_W = 900
WINDOW_H = 700
BG_COLOR = (15, 18, 22)
AXIS_COLOR = (80, 90, 110)
POINT_OLDEST_COLOR = (80, 120, 170)
POINT_NEWEST_COLOR = (180, 240, 255)
TEXT_COLOR = (230, 230, 230)

WORLD_SCALE = 300
FOV = 3.0
Z_CLIP = -2.5
ROTATE_SPEED = 0.008
MAX_POINTS = 10
CIRCLE_SEGMENTS = 64

positions = []
latest_ts = 0.0
circle_data = None
yline_data = None
degree_data = None
lock = threading.Lock()


def recv_loop():
    global circle_data, yline_data, degree_data, latest_ts
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(SOCKET_TIMEOUT_S)
    while True:
        try:
            data, _addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        try:
            msg = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        ts = float(msg.get("ts", time.time()))
        age = time.time() - ts
        if "angle_deg" in msg and "angular_velocity" in msg:
            with lock:
                degree_data = (
                    float(msg["angle_deg"]),
                    float(msg["angular_velocity"]),
                    ts,
                )
            print(
                f"recv degree: angle={msg['angle_deg']:.3f} "
                f"vel={msg['angular_velocity']:.3f} age={age:.2f}s"
            )
            continue

        msg_type = msg.get("type", "pos")
        if msg_type == "circle":
            if not all(k in msg for k in ("center", "normal", "radius")):
                continue
            center = msg["center"]
            normal = msg["normal"]
            radius = msg["radius"]
            if len(center) < 3 or len(normal) < 3:
                continue
            with lock:
                circle_data = (
                    (float(center[0]), float(center[1]), float(center[2])),
                    (float(normal[0]), float(normal[1]), float(normal[2])),
                    float(radius),
                )
            print(
                f"recv circle: r={float(radius):.6f} age={age:.2f}s"
            )
            continue
        if msg_type == "refline":
            if not all(k in msg for k in ("origin", "highest")):
                continue
            origin = msg["origin"]
            highest = msg["highest"]
            if len(origin) < 3 or len(highest) < 3:
                continue
            with lock:
                yline_data = (
                    (float(origin[0]), float(origin[1]), float(origin[2])),
                    (float(highest[0]), float(highest[1]), float(highest[2])),
                )
            print(f"recv yline: age={age:.2f}s")
            continue
        if not all(k in msg for k in ("x", "y", "z")):
            continue
        pos = (float(msg["x"]), float(msg["y"]), float(msg["z"]))
        with lock:
            positions.append(pos)
            if len(positions) > MAX_POINTS:
                del positions[: len(positions) - MAX_POINTS]
            latest_ts = ts
        print(
            f"recv pos: x={pos[0]:.6f} y={pos[1]:.6f} "
            f"z={pos[2]:.6f} age={age:.2f}s"
        )


def rotate_point(x, y, z, yaw, pitch):
    # Yaw around Y axis, pitch around X axis.
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)

    xz = x * cos_y + z * sin_y
    zz = -x * sin_y + z * cos_y

    yz = y * cos_p - zz * sin_p
    zz2 = y * sin_p + zz * cos_p
    return xz, yz, zz2


def project_point(x, y, z, cx, cy):
    z = max(z, Z_CLIP)
    depth = FOV / (FOV + z)
    sx = cx + x * WORLD_SCALE * depth
    sy = cy - y * WORLD_SCALE * depth
    return int(sx), int(sy), depth


def draw_axes(screen, cx, cy, yaw, pitch):
    axis_len = 1.5
    for axis in ("x", "y", "z"):
        if axis == "x":
            x, y, z = axis_len, 0.0, 0.0
        elif axis == "y":
            x, y, z = 0.0, axis_len, 0.0
        else:
            x, y, z = 0.0, 0.0, axis_len
        rx, ry, rz = rotate_point(x, y, z, yaw, pitch)
        sx, sy, _ = project_point(rx, ry, rz, cx, cy)
        pygame.draw.line(screen, AXIS_COLOR, (cx, cy), (sx, sy), 2)


def _normalize(vec):
    length = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])
    if length < 1e-12:
        return (0.0, 1.0, 0.0)
    return (vec[0] / length, vec[1] / length, vec[2] / length)


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def draw_circle(screen, center, normal, radius, yaw, pitch, cx, cy):
    n = _normalize(normal)
    # Pick a reference vector not parallel to n.
    ref = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = _normalize(_cross(n, ref))
    v = _cross(n, u)
    points = []
    for i in range(CIRCLE_SEGMENTS + 1):
        angle = 2.0 * math.pi * i / CIRCLE_SEGMENTS
        x = center[0] + radius * (u[0] * math.cos(angle) + v[0] * math.sin(angle))
        y = center[1] + radius * (u[1] * math.cos(angle) + v[1] * math.sin(angle))
        z = center[2] + radius * (u[2] * math.cos(angle) + v[2] * math.sin(angle))
        rx, ry, rz = rotate_point(x, y, z, yaw, pitch)
        sx, sy, _ = project_point(rx, ry, rz, cx, cy)
        points.append((sx, sy))
    if len(points) > 1:
        pygame.draw.lines(screen, (255, 160, 80), False, points, 2)


def draw_yline(screen, origin, highest, yaw, pitch, cx, cy):
    ox, oy, oz = rotate_point(origin[0], origin[1], origin[2], yaw, pitch)
    hx, hy, hz = rotate_point(highest[0], highest[1], highest[2], yaw, pitch)
    osx, osy, _ = project_point(ox, oy, oz, cx, cy)
    hsx, hsy, _ = project_point(hx, hy, hz, cx, cy)
    pygame.draw.line(screen, (255, 220, 120), (osx, osy), (hsx, hsy), 2)


def main():
    thread = threading.Thread(target=recv_loop, daemon=True)
    thread.start()

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("UDP Tracker Position")
    font = pygame.font.SysFont("monospace", 16)
    clock = pygame.time.Clock()

    yaw = 0.0
    pitch = 0.0
    dragging = False
    last_mouse = (0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                yaw += dx * ROTATE_SPEED
                pitch += dy * ROTATE_SPEED
                pitch = max(-1.4, min(1.4, pitch))
                last_mouse = event.pos

        screen.fill(BG_COLOR)
        cx, cy = WINDOW_W // 2, WINDOW_H // 2
        draw_axes(screen, cx, cy, yaw, pitch)

        with lock:
            pts = list(positions)[-MAX_POINTS:]
            age = time.time() - latest_ts if latest_ts else 0.0
            circle = circle_data
            yline = yline_data
            degree = degree_data

        if pts:
            denom = max(1, len(pts) - 1)
            projected = []
            for i, (x, y, z) in enumerate(pts):
                rx, ry, rz = rotate_point(x, y, z, yaw, pitch)
                sx, sy, depth = project_point(rx, ry, rz, cx, cy)
                t = i / denom
                color = _lerp_color(POINT_OLDEST_COLOR, POINT_NEWEST_COLOR, t)
                projected.append((depth, sx, sy, color))

            # Draw far-to-near so closer points appear on top.
            projected.sort(key=lambda item: item[0])
            for depth, sx, sy, color in projected:
                size = max(2, int(3 * depth))
                pygame.draw.circle(screen, color, (sx, sy), size)

        if circle is not None:
            center, normal, radius = circle
            draw_circle(screen, center, normal, radius, yaw, pitch, cx, cy)

        if yline is not None:
            origin, highest = yline
            draw_yline(screen, origin, highest, yaw, pitch, cx, cy)

        label = f"points={len(pts)} age={age:.2f}s"
        screen.blit(font.render(label, True, TEXT_COLOR), (12, 12))
        if degree is not None:
            angle_deg, angular_velocity, ts = degree
            deg_age = time.time() - ts
            deg_label = (
                f"angle={angle_deg:.2f} deg vel={angular_velocity:.2f} "
                f"deg/s age={deg_age:.2f}s"
            )
            screen.blit(font.render(deg_label, True, TEXT_COLOR), (12, 32))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
