from tracker_source.json_tracker import JsonTrackerSource
# from tracker_source.openvr_tracker import OpenVRTrackerSource
from tracker_source.vive_tracker import ViveTrackers
from models.broadcaster import TrackerUdpBroadcaster
from models.states import TrackerState
from models.tracker_runner import TrackerRunner
from utils.util import parse_args

import time

def main():
    print("Type 'v' or 'h' or 'sc' or 'q' or 'steam'")
    
    LAN_IP = "255.255.255.255"
    LOCALHOST_IP = "127.0.0.1"
    SEND_HZ = 10.0
    
    udp = TrackerUdpBroadcaster(ip=LOCALHOST_IP, port=9000)
    tracker1 =  ViveTrackers(JsonTrackerSource("spv.json", loop=True)) 
    tracker2 =  ViveTrackers(JsonTrackerSource("sph.json", loop=True))
    # tracker = ViveTrackers(OpenVRTrackerSource())
    runner = TrackerRunner(udp, tracker1, send_hz=SEND_HZ)

    while True:
        cmd = input("> ").strip().lower()

        if cmd == "v":
            runner.state = TrackerState.COLLECT_VERTICAL
            runner.tracker = tracker1
            runner.run()
            print("Back to command mode.")
        elif cmd == "h":
            runner.state = TrackerState.COLLECT_HORIZONTAL
            runner.tracker = tracker2
            runner.run()
            print("Back to command mode.")
        elif cmd == "sc":
            runner.state = TrackerState.SEND_CIRCLE
            runner.run()
            print("Back to command mode.")
        elif cmd == "rl":
            runner.state = TrackerState.SEND_REF_LINE
            runner.run()
        elif cmd == "stream":
            runner.state = TrackerState.STREAMING
            runner.set_send_hz(send_hz=60.0)
            runner.run()
            print("Back to command mode.")
        elif cmd == "quit":
            print("Exiting.")
            break
        else:
            print("Unknown command. Use: start | quit")


if __name__ == "__main__":
    main()
