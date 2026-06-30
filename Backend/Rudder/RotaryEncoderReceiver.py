import socket
import json
import threading
import sys
import time

try:
    import msvcrt
except Exception:
    msvcrt = None

DEGREES_PER_STATE = 24


class RotaryEncoderReceiver:
    def __init__(self, port=6001):
        self.state = {
            "rotate": 0.0,
            "button": 0
        }

        # protect access to `state`
        self._lock = threading.Lock()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", port))

        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

        # start keyboard listener (Windows only)
        if msvcrt is not None:
            self._kbd_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
            self._kbd_thread.start()

    def _listen(self):
        while True:
            data, _ = self.sock.recvfrom(1024)
            msg = json.loads(data.decode())

            if msg.get("type") == "input":
                raw_state = msg["rotate"]

                # Convert state (1..9) -> degrees
                with self._lock:
                    self.state["rotate"] = raw_state * DEGREES_PER_STATE
                    self.state["button"] = msg.get("button", 0)
                    # print("Rudder state:", self.state)

    def _keyboard_listener(self):
        # simple Windows console keylistener: q -> left, e -> right
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                try:
                    key = ch.decode('utf-8')
                except Exception:
                    continue

                if key.lower() == 'q':
                    with self._lock:
                        self.state['rotate'] -= DEGREES_PER_STATE
                        print(f"Rudder rotate -> {self.state['rotate']}")
                elif key.lower() == 'e':
                    with self._lock:
                        self.state['rotate'] += DEGREES_PER_STATE
                        print(f"Rudder rotate -> {self.state['rotate']}")
            else:
                # avoid busy loop
                time.sleep(0.05)

    def get(self):
        with self._lock:
            return self.state.copy()


if __name__ == "__main__":
    print("Starting Rotary Encoder Receiver on port 6001...")
    receiver = RotaryEncoderReceiver(port=6001)
    
    try:
        while True:
            state = receiver.get()
            print(f"Rotate: {state['rotate']:.2f}°, Button: {state['button']}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nShutdown")