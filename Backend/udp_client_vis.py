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
POINT_COLOR = (120, 220, 255)
TEXT_COLOR = (230, 230, 230)

WORLD_SCALE = 300
FOV = 3.0
Z_CLIP = -2.5
ROTATE_SPEED = 0.008
MAX_POINTS = 10

positions = []
latest_ts = 0.0
lock = threading.Lock()


def recv_loop():
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
        if not all(k in msg for k in ("x", "y", "z")):
            continue
        with lock:
            pos = (float(msg["x"]), float(msg["y"]), float(msg["z"]))
            positions.append(pos)
            if len(positions) > MAX_POINTS:
                del positions[: len(positions) - MAX_POINTS]
            latest_ts = float(msg.get("ts", time.time()))
        ts = float(msg.get("ts", time.time()))
        age = time.time() - ts
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
            pts = list(positions)
            age = time.time() - latest_ts if latest_ts else 0.0

        for x, y, z in pts:
            rx, ry, rz = rotate_point(x, y, z, yaw, pitch)
            sx, sy, depth = project_point(rx, ry, rz, cx, cy)
            size = max(2, int(3 * depth))
            pygame.draw.circle(screen, POINT_COLOR, (sx, sy), size)

        label = f"points={len(pts)} age={age:.2f}s"
        screen.blit(font.render(label, True, TEXT_COLOR), (12, 12))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
