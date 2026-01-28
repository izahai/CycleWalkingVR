from models.tracker_runner import TrackerRunner
from tracker_source.json_tracker import JsonTrackerSource
from tracker_source.vive_tracker import ViveTrackers
from models.broadcaster import TrackerUdpBroadcaster

import time


def run_tracker(
    udp: TrackerUdpBroadcaster,
    tracker: ViveTrackers,
    runner: TrackerRunner
):
    try:
        while True:
            runner.tick()
            time.sleep(0.001)

    finally:
        udp.close()
        tracker.shutdown()

def main():
    print("Type 'start' to run, 'quit' to exit.")
    
    LAN_IP = "255.255.255.255"
    LOCALHOST_IP = "127.0.0.1"
    SEND_HZ = 20.0
    
    udp = TrackerUdpBroadcaster(ip=LOCALHOST_IP, port=9000)
    tracker =  ViveTrackers(JsonTrackerSource("sphere_positions_horizontal.json", loop=True))
    runner = TrackerRunner(udp, tracker, send_hz=SEND_HZ)

    while True:
        cmd = input("> ").strip().lower()

        if cmd == "start":
            run_tracker(udp, tracker, runner)
            print("Back to command mode.")
        elif cmd == "quit":
            print("Exiting.")
            break
        else:
            print("Unknown command. Use: start | quit")


if __name__ == "__main__":
    main()
