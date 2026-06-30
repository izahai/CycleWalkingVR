# tracker/runner.py
import time
from models.states import TrackerState
from models.broadcaster import TrackerUdpBroadcaster
from tracker_source import abc_tracker

class TrackerRunner:
    def __init__(self, 
        udp : TrackerUdpBroadcaster, 
        tracker : abc_tracker, 
        send_hz=20.0):
        
        self.udp = udp
        self.tracker = tracker
        self.send_dt = 1.0 / send_hz

        self.state = TrackerState.STREAMING
        self.last_time = time.perf_counter()
        self.accumulator = 0.0
        
    def run(self):
        self.reset_timing()
        while True:
            is_return = self.tick()
            if is_return:
                break
            time.sleep(0.001)
        return

    def tick(self):
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        self.accumulator += dt
        is_return = False

        while self.accumulator >= self.send_dt:
            pos = self.tracker.get_tracker_position()
            deg = self.tracker.get_tracker_rudder_degree()
            is_return = self._handle_sample(pos, deg)
            self.accumulator -= self.send_dt
        
        return is_return

    def reset_timing(self):
        self.last_time = time.perf_counter()
        self.accumulator = 0.0
        
    def set_send_hz(self, send_hz: float):
        if send_hz <= 0.0:
            raise ValueError("send_hz must be > 0")

        self.send_dt = 1.0 / send_hz
        self.reset_timing()


    def _handle_sample(self, pos, deg):
        if pos == None:
            return False
        
        self.udp._update_y_direction(pos)
        
        if self.state == TrackerState.COLLECT_VERTICAL:
            self.udp._update_vertical_circle(pos)
            if self.udp.centerV:
                print("[DONE] Computing vertical circle!")
                self.state = TrackerState.RETURN
        elif self.state == TrackerState.COLLECT_HORIZONTAL:
            self.udp._update_horizontal_circle(pos)
            if self.udp.centerH:
                self.udp._compute_center_circle()
                print("[DONE] Computing horizontal circle!")
                self.state = TrackerState.RETURN
        elif self.state == TrackerState.SEND_CIRCLE:
            self.udp.send_circle(self.udp.centerV, self.udp.v_normV, self.udp.radiusV)
            # self.udp.send_circle(self.udp.centerH, self.udp.v_normH, self.udp.radiusH)
            # self.udp.send_circle(self.udp.centerC, self.udp.v_normC, self.udp.radiusC)
            print("[DONE] Send circle!")
            self.state = TrackerState.RETURN
        elif self.state == TrackerState.SEND_REF_LINE:
            self.udp._mark_ref_rudder_degree(deg)
            # self.udp._compute_center_ref_line(pos)
            self.udp.send_ref_line(self.udp.centerV, self.udp.ref_pointV)
            # self.udp.send_ref_line(self.udp.centerC, self.udp.ref_pointC)
            self.state = TrackerState.RETURN
        elif self.state == TrackerState.RETURN:
            return True
        elif self.state == TrackerState.STREAMING:
            res = self.udp.send_degree_position(pos, deg)
            print(res)
            return False
        
        # --- STREAMING DATA ---
        self.udp.send_xyz_position(pos)
        print(pos, deg)
        return False
