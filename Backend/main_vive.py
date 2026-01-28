import time
from models.broadcaster import TrackerUdpBroadcaster
from models.tracker_runner import TrackerRunner
from tracker_source.json_tracker import JsonTrackerSource
from tracker_source.vive_tracker import ViveTrackers

LAN_IP = "255.255.255.255"
LOCALHOST_IP = "127.0.0.1"
SEND_HZ = 20.0
SEND_DT = 1.0 / SEND_HZ


def run_tracker(udp : TrackerUdpBroadcaster):
    last_time = time.perf_counter()
    accumulator = 0.0
    circleV_sent = False
    circleH_sent = False

    if not circleV_sent:
        vt = ViveTrackers(JsonTrackerSource("sphere_positions_horizontal.json", loop=True))
    elif not circleH_sent:
        vt = ViveTrackers(JsonTrackerSource("sphere_positions_vertical.json", loop=True))

    # print("Tracker running. Type 'stop' to stop.")

    try:
        while True:
            # # Non-blocking stop check
            # if check_stop():
            #     print("Stopping tracker...")
            #     break

            now = time.perf_counter()
            dt = now - last_time
            last_time = now
            accumulator += dt

            while accumulator >= SEND_DT:
                pos = vt.get_tracker_position()

                if not udp.centerV:
                    udp._update_vertical_circle(pos)
                elif not circleV_sent:
                    udp.send_circle(udp.centerV, udp.v_normV, udp.v_normV)
                    udp.send_ref_line()
                    circleV_sent = True
                    print("[DONE] Computing vertical circle!")
                    return
                else:
                    udp.send_xyz_position(pos)
                    print(pos)

                accumulator -= SEND_DT

            time.sleep(0.001)

    finally:
        udp.close()
        vt.shutdown()


def check_stop():
    """Check for user input without blocking"""
    import sys
    import select

    if select.select([sys.stdin], [], [], 0.0)[0]:
        cmd = sys.stdin.readline().strip().lower()
        return cmd == "stop"
    return False


def main():
    print("Type 'start' to run the tracker.")
    print("Type 'quit' to exit.")
    
    udp = TrackerUdpBroadcaster(ip=LOCALHOST_IP, port=9000)

    while True:
        cmd = input("> ").strip().lower()

        if cmd == "start":
            run_tracker(udp)
            print("Back to command mode.")
        elif cmd == "quit":
            print("Exiting.")
            break
        else:
            print("Unknown command. Use: start | quit")


if __name__ == "__main__":
    main()
