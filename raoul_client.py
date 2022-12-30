import asyncio
import subprocess
import sys

import structlog
import websockets

log = structlog.get_logger()

cmd = "libcamera-vid -t 0 --codec mjpeg --framerate 30 -q 100 -n -o -"

BUFFER_SIZE = 65_536


async def run():
    async with websockets.connect(
        "ws://C02CM2JHMD6P-Hadrien-David.local:8000/ws"
    ) as ws:
        async with CameraCapture(ws) as capture:
            while True:
                await ws.recv()
                capture.on = True
                await ws.recv()


class CameraCapture:
    def __init__(self, ws):
        self.on = False
        self.ws = ws

    async def __aenter__(self):
        self.process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=sys.stdout, limit=BUFFER_SIZE
        )
        await self.process.stdout.read(BUFFER_SIZE)
        self._capture_task = asyncio.create_task(self._capture())
        log.info("Running libcamera", cmd=cmd)
        return self

    async def _capture(self):
        while True:
            data = await self.process.stdout.read(BUFFER_SIZE)
            if self.on:
                await self.ws.send(data)

    async def __aexit__(self, exc_type, exc, tb):
        self._capture_task.cancel()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
