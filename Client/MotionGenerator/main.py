import socket
import json
import time
import math

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

# ================= UDP CONFIG =================
UDP_IP = "127.0.0.1"
UDP_PORT = 9000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ================= PYGAME + OPENGL =================
pygame.init()
pygame.display.set_caption("Motion Generator - 3D View")
screen_size = (960, 640)
screen = pygame.display.set_mode(
    screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
)
clock = pygame.time.Clock()


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
def generate_leg_pose(t, phase, x_offset):
    pos_world = [
        x_offset,  # <-- fixed X position
        0.9 + 0.15 * math.sin(t + phase),
        0.15 * math.cos(t + phase),
    ]

    angle = t + phase
    rot_world = [
        math.sin(angle / 2.0),
        0.0,
        0.0,
        math.cos(angle / 2.0),
    ]

    return pos_world, rot_world


setup_gl(*screen_size)
quadric = gluNewQuadric()

print("3D controls: left-drag rotate, right-drag pan, wheel zoom, R reset.")

# ================= MAIN LOOP =================
start_time = time.time()
running = True

cam_target = [0.0, 0.9, 0.0]
cam_yaw = 45.0
cam_pitch = 20.0
cam_distance = 3.0

mouse_rotate = False
mouse_pan = False
last_mouse_pos = None

while running:
    t = (time.time() - start_time) * 2.0  # speed factor

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
                cam_target = [0.0, 0.9, 0.0]
                cam_yaw = 45.0
                cam_pitch = 20.0
                cam_distance = 3.0
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
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

            if mouse_rotate:
                cam_yaw += dx * 0.3
                cam_pitch -= dy * 0.3
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

    lpos, lrot = generate_leg_pose(t, 0.0, -0.18)
    rpos, rrot = generate_leg_pose(t, math.pi, 0.18)

    draw_sphere(quadric, lpos, 0.06, (0.1, 0.7, 1.0))
    draw_sphere(quadric, rpos, 0.06, (1.0, 0.4, 0.3))

    # UDP send
    for leg_id, pos, rot in [
        ("left_leg", lpos, lrot),
        ("right_leg", rpos, rrot),
    ]:
        packet = json.dumps(
            {
                "id": leg_id,
                "pos": pos,
                "rot": rot,
                "ts": time.time(),
            }
        ).encode("utf-8")
        sock.sendto(packet, (UDP_IP, UDP_PORT))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
