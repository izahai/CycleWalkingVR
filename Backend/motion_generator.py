import json
import time
import math

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

# ================= RECORDING CONFIG =================
RECORD_DURATION_SEC = 10.0
RECORD_OUTPUT_PATH = "sphere_positions_horizontal.json"

# ================= ORBIT CONFIG =================
# Control the motion here.
ORBIT_ORIGIN = [1.0, 1.0, 1.0]
ORBIT_NORMAL = [0.0, 1.0, 0.0]
ORBIT_RADIUS = 0.5

# ================= PYGAME + OPENGL =================
pygame.init()
pygame.display.set_caption("Motion Generator - 3D View")
screen_size = (960, 640)
screen = pygame.display.set_mode(
    screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
)
clock = pygame.time.Clock()


def update_caption(speed_value):
    pygame.display.set_caption(
        f"Motion Generator - 3D View | speed: {speed_value:.2f}x"
    )


def get_speed_slider_rect(window_size):
    margin = 20
    width = 220
    height = 12
    x = margin
    y = window_size[1] - margin - height
    return x, y, width, height


def speed_from_slider(x, slider_rect, min_speed, max_speed):
    sx, _, sw, _ = slider_rect
    t = clamp((x - sx) / max(sw, 1), 0.0, 1.0)
    return min_speed + t * (max_speed - min_speed)


def draw_speed_slider(window_size, speed_value, min_speed, max_speed):
    sx, sy, sw, sh = get_speed_slider_rect(window_size)
    t = clamp((speed_value - min_speed) / max(max_speed - min_speed, 0.001), 0.0, 1.0)
    handle_x = sx + t * sw

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_size[0], window_size[1], 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    # Bar background
    glColor3f(0.1, 0.1, 0.12)
    glBegin(GL_QUADS)
    glVertex2f(sx, sy)
    glVertex2f(sx + sw, sy)
    glVertex2f(sx + sw, sy + sh)
    glVertex2f(sx, sy + sh)
    glEnd()

    # Filled portion
    glColor3f(0.2, 0.7, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(sx, sy)
    glVertex2f(handle_x, sy)
    glVertex2f(handle_x, sy + sh)
    glVertex2f(sx, sy + sh)
    glEnd()

    # Handle
    handle_w = 8
    glColor3f(0.9, 0.9, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(handle_x - handle_w, sy - 4)
    glVertex2f(handle_x + handle_w, sy - 4)
    glVertex2f(handle_x + handle_w, sy + sh + 4)
    glVertex2f(handle_x - handle_w, sy + sh + 4)
    glEnd()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def setup_gl(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = max(width / max(height, 1), 0.1)
    gluPerspective(60.0, aspect, 0.05, 50.0)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (2.0, 5.0, 3.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glClearColor(0.07, 0.07, 0.08, 1.0)


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def normalize(vec):
    length = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])
    if length == 0:
        return [0.0, 0.0, 0.0]
    return [vec[0] / length, vec[1] / length, vec[2] / length]


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def camera_vectors(yaw_deg, pitch_deg):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cam_dir = [
        math.cos(pitch) * math.cos(yaw),
        math.sin(pitch),
        math.cos(pitch) * math.sin(yaw),
    ]
    forward = normalize([-cam_dir[0], -cam_dir[1], -cam_dir[2]])
    world_up = [0.0, 1.0, 0.0]
    right = normalize(cross(forward, world_up))
    up = cross(right, forward)
    return forward, right, up, cam_dir


def apply_camera(target, yaw_deg, pitch_deg, distance):
    _, _, _, cam_dir = camera_vectors(yaw_deg, pitch_deg)
    cam_pos = [
        target[0] + cam_dir[0] * distance,
        target[1] + cam_dir[1] * distance,
        target[2] + cam_dir[2] * distance,
    ]
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(
        cam_pos[0],
        cam_pos[1],
        cam_pos[2],
        target[0],
        target[1],
        target[2],
        0.0,
        1.0,
        0.0,
    )


def draw_3d_grid(size=2.0, step=0.25):
    glDisable(GL_LIGHTING)
    glColor3f(0.18, 0.18, 0.2)
    glBegin(GL_LINES)
    count = int(size / step)
    for i in range(-count, count + 1):
        x = i * step
        z = i * step
        # XZ plane at y=0
        glVertex3f(x, 0.0, -size)
        glVertex3f(x, 0.0, size)
        glVertex3f(-size, 0.0, z)
        glVertex3f(size, 0.0, z)
        # XY plane at z=0
        glVertex3f(x, -size, 0.0)
        glVertex3f(x, size, 0.0)
        glVertex3f(-size, z, 0.0)
        glVertex3f(size, z, 0.0)
        # YZ plane at x=0
        glVertex3f(0.0, x, -size)
        glVertex3f(0.0, x, size)
        glVertex3f(0.0, -size, z)
        glVertex3f(0.0, size, z)
    glEnd()
    glEnable(GL_LIGHTING)


def draw_axes(length=0.5):
    glDisable(GL_LIGHTING)
    glBegin(GL_LINES)
    glColor3f(1.0, 0.2, 0.2)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(length, 0.0, 0.0)
    glColor3f(0.2, 1.0, 0.2)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, length, 0.0)
    glColor3f(0.2, 0.4, 1.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, length)
    glEnd()
    glEnable(GL_LIGHTING)


def draw_sphere(quadric, pos, radius, color):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glColor3f(color[0], color[1], color[2])
    gluSphere(quadric, radius, 24, 16)
    glPopMatrix()


# ================= MOTION =================
def generate_orbit_pose(t, origin, normal, radius):
    angle = t
    n = normalize(normal)
    if abs(n[0]) < 0.9:
        ref = [1.0, 0.0, 0.0]
    else:
        ref = [0.0, 0.0, 1.0]
    basis_u = normalize(cross(n, ref))
    basis_v = cross(n, basis_u)
    offset = [
        radius * math.cos(angle) * basis_u[0] + radius * math.sin(angle) * basis_v[0],
        radius * math.cos(angle) * basis_u[1] + radius * math.sin(angle) * basis_v[1],
        radius * math.cos(angle) * basis_u[2] + radius * math.sin(angle) * basis_v[2],
    ]
    pos_world = [
        origin[0] + offset[0],
        origin[1] + offset[1],
        origin[2] + offset[2],
    ]

    rot_world = [
        math.sin(angle / 2.0),
        0.0,
        0.0,
        math.cos(angle / 2.0),
    ]

    return pos_world, rot_world


setup_gl(*screen_size)
quadric = gluNewQuadric()

# Tunables
motion_speed = 10.0  # higher = faster leg cycle
invert_camera_rotation = False  # set True to invert mouse rotate
min_motion_speed = 0.2
max_motion_speed = 12.0

print("3D controls: left-drag rotate, right-drag pan, wheel zoom, R reset.")
print("Speed: drag slider or use +/- to change motion speed.")
update_caption(motion_speed)

# ================= MAIN LOOP =================
start_time = time.time()
running = True
positions = []
positions_saved = False

orbit_origin = ORBIT_ORIGIN[:]
orbit_normal = ORBIT_NORMAL[:]
orbit_radius = ORBIT_RADIUS

cam_target = orbit_origin[:]
cam_yaw = 45.0
cam_pitch = 20.0
cam_distance = 3.0

mouse_rotate = False
mouse_pan = False
last_mouse_pos = None
dragging_speed = False

while running:
    t = (time.time() - start_time) * motion_speed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            screen_size = (max(event.w, 320), max(event.h, 240))
            screen = pygame.display.set_mode(
                screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
            )
            setup_gl(*screen_size)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                cam_target = orbit_origin[:]
                cam_yaw = 45.0
                cam_pitch = 20.0
                cam_distance = 3.0
            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                motion_speed = clamp(
                    motion_speed + 0.2, min_motion_speed, max_motion_speed
                )
                update_caption(motion_speed)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                motion_speed = clamp(
                    motion_speed - 0.2, min_motion_speed, max_motion_speed
                )
                update_caption(motion_speed)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                slider_rect = get_speed_slider_rect(screen_size)
                sx, sy, sw, sh = slider_rect
                mx, my = event.pos
                if sx - 10 <= mx <= sx + sw + 10 and sy - 10 <= my <= sy + sh + 10:
                    dragging_speed = True
                    motion_speed = speed_from_slider(
                        mx, slider_rect, min_motion_speed, max_motion_speed
                    )
                    update_caption(motion_speed)
                else:
                    mouse_rotate = True
                last_mouse_pos = event.pos
            elif event.button == 3:
                mouse_pan = True
                last_mouse_pos = event.pos
            elif event.button == 4:
                cam_distance = clamp(cam_distance * 0.9, 0.8, 12.0)
            elif event.button == 5:
                cam_distance = clamp(cam_distance * 1.1, 0.8, 12.0)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if dragging_speed:
                    dragging_speed = False
                mouse_rotate = False
            elif event.button == 3:
                mouse_pan = False
            last_mouse_pos = None
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                cam_distance = clamp(cam_distance * 0.9, 0.8, 12.0)
            elif event.y < 0:
                cam_distance = clamp(cam_distance * 1.1, 0.8, 12.0)
        elif event.type == pygame.MOUSEMOTION:
            if last_mouse_pos is None:
                last_mouse_pos = event.pos
            dx = event.pos[0] - last_mouse_pos[0]
            dy = event.pos[1] - last_mouse_pos[1]
            last_mouse_pos = event.pos

            if dragging_speed:
                slider_rect = get_speed_slider_rect(screen_size)
                motion_speed = speed_from_slider(
                    event.pos[0], slider_rect, min_motion_speed, max_motion_speed
                )
                update_caption(motion_speed)
            elif mouse_rotate:
                rotate_dir = -1.0 if invert_camera_rotation else 1.0
                cam_yaw += dx * 0.3 * rotate_dir
                cam_pitch -= dy * 0.3 * rotate_dir
                cam_pitch = clamp(cam_pitch, -89.0, 89.0)
            elif mouse_pan:
                _, right, up, _ = camera_vectors(cam_yaw, cam_pitch)
                pan_speed = 0.002 * cam_distance
                cam_target[0] += (-dx * pan_speed) * right[0] + (dy * pan_speed) * up[0]
                cam_target[1] += (-dx * pan_speed) * right[1] + (dy * pan_speed) * up[1]
                cam_target[2] += (-dx * pan_speed) * right[2] + (dy * pan_speed) * up[2]

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    apply_camera(cam_target, cam_yaw, cam_pitch, cam_distance)

    draw_3d_grid()
    draw_axes()

    pos, rot = generate_orbit_pose(t, orbit_origin, orbit_normal, orbit_radius)

    # Draw orbit center
    draw_sphere(quadric, orbit_origin, 0.04, (1.0, 0.4, 0.2))
    draw_sphere(quadric, pos, 0.06, (0.2, 0.7, 1.0))
    
    draw_speed_slider(screen_size, motion_speed, min_motion_speed, max_motion_speed)

    # Record sphere position for the first RECORD_DURATION_SEC seconds.
    now = time.time()
    if not positions_saved:
        if now - start_time <= RECORD_DURATION_SEC:
            positions.append(
                {
                    "pos": [pos[0], pos[1], pos[2]],
                }
            )
        else:
            with open(RECORD_OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "duration_sec": RECORD_DURATION_SEC,
                        "count": len(positions),
                        "samples": positions,
                    },
                    f,
                    indent=2,
                )
            positions_saved = True


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
