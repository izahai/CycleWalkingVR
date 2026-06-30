import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Tracker runner")

    parser.add_argument("--ip", default="127.0.0.1", help="Target IP address")
    parser.add_argument("--port", type=int, default=9000, help="UDP port")
    parser.add_argument("--hz", type=float, default=10.0, help="Send frequency")

    return parser.parse_args()