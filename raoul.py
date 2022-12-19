import structlog
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect


app = FastAPI()
log = structlog.get_logger()


@app.get("/health")
def health():
    return "ok"


@app.websocket("/ws")
async def websocket(websocket: WebSocket):
    await websocket.accept()
    log.info("Accepting connection")
    while True:
        try:
            data = await websocket.receive_bytes()

        except WebSocketDisconnect:
            log.info("Closing connection", exc_info=True)
            break

        else:
            log.debug("Receiving", len=len(data))
