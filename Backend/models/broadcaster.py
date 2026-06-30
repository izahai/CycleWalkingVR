import json
import socket
import time

from utils.math_utils import (
    best_fit_3d_circle, line_origin_to_highest_y,
    angle_deg_from_highest, closest_point_on_line,
    distance_between_points, project_point_to_circle_rim,
    circle_points_at_distance, angle_deg_from_ref,
    y_direction
)

class TrackerUdpBroadcaster:
    def __init__(self, ip="255.255.255.255", port=9000, broadcast=True):
        
        # --- Network ---
        self.addr = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if broadcast:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
        # --- Logic ---
        self.centerV = self.v_normV = self.radiusV = self.ref_pointV = None
        self.centerH = self.v_normH = self.radiusH = None
        self.centerC = self.v_normC = self.radiusC = self.ref_pointC = None
        self.i_is_y_up = None
        self.ref_degree = None
        
        self.num_point_init = 100
        self._init_pointsV = []
        self._init_pointsH = []
        
        self.prev_ang = 0
        self.prev_time = 0
        self.prev_pos = None

    def close(self):
        self.sock.close()

    def _update_vertical_circle(self, pos):
        self._init_pointsV.append([pos[0], pos[1], pos[2]])
        if len(self._init_pointsV) >= self.num_point_init:
            _circle = best_fit_3d_circle(self._init_pointsV)
            self.centerV, self.v_normV, self.radiusV = _circle
            _, self.ref_pointV = line_origin_to_highest_y(self._init_pointsV, self.centerV)
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
    
    def _compute_center_circle(self):
        self.centerC = closest_point_on_line(self.centerV, self.v_normV, self.centerH)
        self.v_normC = self.v_normH
        self.radiusC = distance_between_points(self.centerC, self.centerV)
        
    def _compute_center_ref_line(self, pos):
        self.ref_pointC = project_point_to_circle_rim(
            self.centerC, self.v_normC, self.radiusC, pos)
        
    def _mark_ref_rudder_degree(self, deg):
        self.ref_degree = deg
        
    def _compute_rudder_degree(self, pos):
        candidates = circle_points_at_distance(
            self.centerC, self.v_normC, self.radiusC, pos, self.radiusV)
        final_degree = 0.0
        degrees = []
        for p in candidates:
            degrees.append(angle_deg_from_ref(self.centerC, self.ref_pointC, p))
            
        if not degrees:
            return 0.0
        
        if self.i_is_y_up == 1:
            final_degree = max(degrees)
        else:
            final_degree = min(degrees)
        
        return final_degree
        
    def _update_y_direction(self, pos):
        if self.prev_pos == None:
            self.prev_pos = pos
            return
        self.i_is_y_up = y_direction(pos, self.prev_pos)
        self.prev_pos = pos
        return
            
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
        
    def send_degree_position(self, pos, deg):
        if pos is None:
            return

        if self.centerV is None or self.ref_pointV is None:
            return

        angle_deg = angle_deg_from_highest(self.centerH, self.ref_pointV, pos)
        rudder_deg = deg - self.ref_degree
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
                "rudder_deg": rudder_deg,
                "ts": ts,
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)
        return angle_deg, rudder_deg

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

    def send_ref_line(self, origin, point):
        packet = json.dumps(
            {
                "origin": origin,
                "point": point,
                "ts": time.time(),
                "type": "refline",
            }
        ).encode("utf-8")
        self.sock.sendto(packet, self.addr)