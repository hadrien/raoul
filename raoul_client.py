import os
import socket
import subprocess
import sys
import tempfile
from concurrent import futures

import structlog

log = structlog.get_logger()

cmd = "libcamera-vid -v -t 0 --inline --framerate 60 -o -"
# cmd = "find ."

BUFFER_SIZE = 16_384


def new_socket_address():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    os.unlink(path)
    return path


def handle_video_stream(socket_address):
    video_stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    video_stream.bind(socket_address)
    video_stream.listen(1)

    log.debug("Waiting for connection")
    connection, _ = video_stream.accept()
    log.debug("Connecting")
    try:
        while True:
            data = connection.recv(BUFFER_SIZE)
            if data:
                log.debug("Receiving", len=len(data))
            else:
                break

    finally:
        log.info("End")
        connection.close()
        video_stream.close()


def run_libcamera_vid(socket_address):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while True:
        try:
            client.connect(socket_address)
        except (ConnectionRefusedError, FileNotFoundError):
            pass
        else:
            break

    subprocess.run(
        cmd.split(),
        stdout=client.makefile(mode="wb"),
        stderr=sys.stdout,
        check=True,
    )


def run():
    executor = futures.ThreadPoolExecutor(max_workers=1)
    socket_address = new_socket_address()
    executor.submit(handle_video_stream, socket_address)
    run_libcamera_vid(socket_address)


if __name__ == "__main__":
    run()
