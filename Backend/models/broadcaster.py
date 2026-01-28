import json
import socket
import time

from utils.polar_utils import (
    best_fit_3d_circle, line_origin_to_highest_y,
    angle_deg_from_highest
)

class TrackerUdpBroadcaster:
    def __init__(self, ip="255.255.255.255", port=9000, broadcast=True):
        
        # --- Network ---
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if broadcast:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
        # --- Logic ---
        self.centerV = self.v_normV = self.radiusV = self.ref_lineV = None
        self.centerH = self.v_normH = self.radiusH = self.ref_lineH = None
        
        self.num_point_init = 100
        self._init_pointsV = []
        self._init_pointsH = []
        
        self.prev_ang = 0
        self.prev_time = 0

    def close(self):
        self.sock.close()

    def _update_vertical_circle(self, pos):
        self._init_pointsV.append([pos[0], pos[1], pos[2]])
        if len(self._init_pointsV) >= self.num_point_init:
            _circle = best_fit_3d_circle(self._init_pointsV)
            self.centerV, self.v_normV, self.radiusV = _circle
            self.ref_lineV = line_origin_to_highest_y(self._init_pointsV, self.centerV)
            self._init_pointsV = []
            return True
        return False

    def _update_horizontal_circle(self, pos):
        self._init_pointsH.append([pos[0], pos[1], pos[2]])
        if len(self._init_pointsH) >= self.num_point_init:
            _circle = best_fit_3d_circle(self._init_pointsH)
            self.centerH, self.v_normH, self.radiusH = _circle
            self._init_pointsH = []
            return True
        return False
    
    def angle_diff_deg(self, curr, prev):
        diff = curr - prev
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        return diff


    def send_xyz_position(self, pos):
        if pos is None:
            return

        packet = json.dumps(
            {
                "x": pos[0],
                "y": pos[1],
                "z": pos[2],
                "ts": time.time(),
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)
        
    def send_degree_position(self, pos):
        if pos is None:
            return

        if self.center is None or self.ref_lineV is None:
            return

        origin, highest = self.ref_lineV
        angle_deg = angle_deg_from_highest(origin, highest, pos)
        ts = time.time()
        
        dt = ts - self.prev_time if self.prev_time else 0.0
        if dt > 0:
            d_angle = self.angle_diff_deg(angle_deg, self.prev_ang)
            angular_velocity = d_angle / dt
        else:
            angular_velocity = 0.0

        self.prev_time = ts
        self.prev_ang = angle_deg
        
        packet = json.dumps(
            {
                "angle_deg": angle_deg,
                "angular_velocity": angular_velocity,
                "ts": ts,
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)
        return angle_deg

    def send_circle(self, c, n, r):        
        packet = json.dumps(
            {
                "center": c,
                "normal": n,
                "radius": r,
                "ts": time.time(),
                "type": "circle",
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)

    def send_ref_line(self):
        if self.ref_lineV is None:
            return

        origin, highest = self.ref_lineV
        packet = json.dumps(
            {
                "origin": origin,
                "highest": highest,
                "ts": time.time(),
                "type": "refline",
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)