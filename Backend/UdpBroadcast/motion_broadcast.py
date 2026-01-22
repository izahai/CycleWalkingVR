#!/usr/bin/env python3

import errno
import socket
import sys
import time


def die(what: str) -> None:
    print(what, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    listen_port = 9001
    broadcast_port = 9000
    buffer_size = 2048

    try:
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except OSError:
        die("socket(recv) failed")

    try:
        recv_sock.bind(("", listen_port))
    except OSError:
        recv_sock.close()
        die("bind failed")

    try:
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except OSError:
        recv_sock.close()
        die("socket(send) failed")

    try:
        send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
        send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except OSError:
        recv_sock.close()
        send_sock.close()
        die("setsockopt failed")

    send_addr = ("255.255.255.255", broadcast_port)

    try:
        while True:
            try:
                data, _ = recv_sock.recvfrom(buffer_size)
            except OSError:
                die("recvfrom failed")

            try:
                send_sock.sendto(data, send_addr)
            except OSError as exc:
                if exc.errno == errno.ENOBUFS:
                    time.sleep(0.002)
                    continue
                die("sendto failed")
    finally:
        recv_sock.close()
        send_sock.close()


if __name__ == "__main__":
    main()
