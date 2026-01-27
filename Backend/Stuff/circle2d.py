import socket
import json
import time
import math
import sys
import pygame

# ================= UDP CONFIG =================
UDP_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
UDP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ================= SEND TIMING =================
SEND_HZ = 90.0
SEND_DT = 1.0 / SEND_HZ
send_accumulator = 0.0
last_time = time.perf_counter()

# ================= PYGAME =================
pygame.init()
screen_size = (600, 640)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D Circular Motion (Uniform UDP)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 26)

# ================= PARAMETERS =================
radius = 200
center = (screen_size[0] // 2, 300)

min_speed = 0.05     # rotations per second
max_speed = 2.0
motion_speed = 1.0

start_time = time.time()
running = True
dragging_slider = False

# ================= SLIDER =================
def slider_rect():
    return pygame.Rect(100, 560, 400, 12)

def speed_from_mouse(mx):
    r = slider_rect()
    t = max(0.0, min(1.0, (mx - r.x) / r.width))
    return min_speed + t * (max_speed - min_speed)

def draw_slider(speed):
    r = slider_rect()
    pygame.draw.rect(screen, (60, 60, 70), r)
    t = (speed - min_speed) / (max_speed - min_speed)
    handle_x = r.x + int(t * r.width)
    pygame.draw.rect(screen, (0, 180, 255), (r.x, r.y, handle_x - r.x, r.height))
    pygame.draw.circle(screen, (230, 230, 230), (handle_x, r.centery), 8)

# ================= MAIN LOOP =================
while running:
    # ---------- TIME ----------
    now = time.perf_counter()
    dt = now - last_time
    last_time = now
    send_accumulator += dt

    # ---------- EVENTS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                motion_speed = min(max_speed, motion_speed + 0.05)
            elif event.key == pygame.K_MINUS:
                motion_speed = max(min_speed, motion_speed - 0.05)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and slider_rect().inflate(10, 10).collidepoint(event.pos):
                dragging_slider = True
                motion_speed = speed_from_mouse(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_slider = False

        elif event.type == pygame.MOUSEMOTION:
            if dragging_slider:
                motion_speed = speed_from_mouse(event.pos[0])

    # ---------- MOTION ----------
    t = time.time() - start_time
    angle_deg = (t * motion_speed * 360.0) % 360.0
    angle_rad = math.radians(angle_deg)

    x = center[0] + radius * math.cos(angle_rad)
    y = center[1] + radius * math.sin(angle_rad)

    # ---------- DRAW ----------
    screen.fill((18, 18, 22))
    pygame.draw.circle(screen, (90, 90, 100), center, radius, 2)
    pygame.draw.circle(screen, (0, 180, 255), (int(x), int(y)), 8)

    draw_slider(motion_speed)

    screen.blit(
        font.render(f"Angle: {angle_deg:.2f}°", True, (230, 230, 230)),
        (20, 20),
    )
    screen.blit(
        font.render(f"Speed: {motion_speed:.2f} rps", True, (230, 230, 230)),
        (20, 50),
    )

    pygame.display.flip()

    # ---------- UNIFORM UDP SEND ----------
    while send_accumulator >= SEND_DT:
        packet = json.dumps(
            {
                "angle_deg": angle_deg,
                "angular_velocity": motion_speed * 360.0,  # deg/sec (VR-friendly)
                "ts": time.time(),
            }
        ).encode("utf-8")

        sock.sendto(packet, (UDP_IP, UDP_PORT))
        send_accumulator -= SEND_DT

    # ---------- RENDER LIMIT ----------
    clock.tick(120)  # rendering only, NOT network timing

pygame.quit()