import time

from Broadcaster.udp_broadcast import TrackerUdpBroadcaster
from TrackerSource.json_tracker import JsonTrackerSource
from TrackerSource.vive_tracker import ViveTrackers

LAN_IP = "255.255.255.255"
LOCALHOST_IP = "127.0.0.1"
SEND_HZ = 90.0
SEND_DT = 1.0 / SEND_HZ
last_time = time.perf_counter()
accumulator = 0.0

# Real device
# vt = ViveTrackers(OpenVRTrackerSource())

# OR simulation
vt = ViveTrackers(JsonTrackerSource("sphere_positions.json", loop=True))
udp = TrackerUdpBroadcaster(ip=LOCALHOST_IP, port=9000)

try:
    while True:
        now = time.perf_counter()
        dt = now - last_time
        last_time = now
        accumulator += dt

        while accumulator >= SEND_DT:
            pos = vt.get_tracker_position()
            udp.send_position(pos)
            print(pos)
            accumulator -= SEND_DT

        time.sleep(0.001)
finally:
    udp.close()
    vt.shutdown()


# nc -u -l 9000