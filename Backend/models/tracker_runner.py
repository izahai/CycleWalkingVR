# tracker/runner.py
import time
from models.states import TrackerState


class TrackerRunner:
    def __init__(self, udp, tracker, send_hz=20.0):
        self.udp = udp
        self.tracker = tracker
        self.send_dt = 1.0 / send_hz

        self.state = TrackerState.COLLECT_VERTICAL
        self.last_time = time.perf_counter()
        self.accumulator = 0.0

    def tick(self):
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        self.accumulator += dt

        while self.accumulator >= self.send_dt:
            pos = self.tracker.get_tracker_position()
            self._handle_sample(pos)
            self.accumulator -= self.send_dt

    def _handle_sample(self, pos):
        if self.state == TrackerState.COLLECT_VERTICAL:
            self.udp._update_vertical_circle(pos)

            if self.udp.centerV:
                self.state = TrackerState.SEND_VERTICAL

        elif self.state == TrackerState.SEND_VERTICAL:
            self.udp.send_circle(
                self.udp.centerV,
                self.udp.v_normV,
                self.udp.v_normV
            )
            self.udp.send_ref_line()
            print("[DONE] Computing vertical circle!")

            self.state = TrackerState.STREAM_POSITIONS

        elif self.state == TrackerState.STREAM_POSITIONS:
            self.udp.send_xyz_position(pos)
            print(pos)