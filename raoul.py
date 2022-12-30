import asyncio
import subprocess
import sys


import structlog
from fastapi import FastAPI, Response
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect


app = FastAPI()
queue = None
ffmpeg = None
log = structlog.get_logger()
FRAME_SEPARATOR = b"\xff\xd8"
BUFFER_SIZE = 65536

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
def health():
    return "ok"


@app.on_event("startup")
async def on_startup():
    global queue, ffmpeg
    queue = asyncio.Queue()
    cmd = "ffmpeg -f mpegts -c:v h264 -i - -c:v libvpx-vp9 -f webm -"
    # ffmpeg = await asyncio.create_subprocess_shell(
    #    cmd,
    #    stdin=subprocess.PIPE,
    #    stdout=subprocess.PIPE,
    #    stderr=sys.stdout,
    #    limit=BUFFER_SIZE,
    # )


gws = None


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    global gws
    gws = ws
    log.info("Accepting connection")
    while True:
        try:
            data = await ws.receive_bytes()
        except WebSocketDisconnect:
            log.info("Closing connection", exc_info=True)
            break

        else:
            await queue.put(data)
    log.info("over")


async def iter_jpeg_frames(queue):
    data = await queue.get() + await queue.get() + await queue.get() + await queue.get()
    log.debug(data[:30])
    log.debug("getting frames")
    first_frame_index = data.index(FRAME_SEPARATOR)
    data = data[first_frame_index:]
    while True:
        frame_count = data.count(FRAME_SEPARATOR)
        for _ in range(frame_count - 1):
            end = data.index(FRAME_SEPARATOR, len(FRAME_SEPARATOR))
            frame = data[0:end]
            yield frame
            data = data[end:]
        data = data + await queue.get()


async def iter_multipart_frames(queue):
    async for frame in iter_jpeg_frames(queue):
        yield b"--FRAME\r\n"
        yield b"Content-Type: image/jpeg\r\n"
        yield f"Content-Length {len(frame)}\r\n\r\n".encode()
        yield frame
        yield b"\r\n"


@app.get("/video")
async def mjpeg(response: Response):
    headers = {
        "Age": "0",
        "Cache-Control": "no-cache, private",
        "Pragma": "no-cache",
        "Content-Type": "multipart/x-mixed-replace; boundary=FRAME",
    }

    await gws.send_bytes(b"yolo")
    return StreamingResponse(iter_multipart_frames(queue), headers=headers)
