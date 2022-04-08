import asyncio
import json
from os import environ
from time import time
from typing import Literal, Optional
import uuid

import redis.exceptions
import redis.asyncio as aioredis

from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, constr, Field, ValidationError

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or '6379')
REDIS_PASS = environ.get('REDIS_PASS') or None

rpool = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASS,
    decode_responses=True
)

class ConnectionManager:
    """ Class for managing WebSocket connections"""
    def __init__(self):
        self.active_connections: dict = {}
        self.subscribed = {}
    
    async def subscribe(self, canvas_id):
        """ Hack to enable background subscription to Redis pubsub. """
        self.subscribed[canvas_id] = True
        while self.subscribed[canvas_id]:
            try:
                sub = rpool.pubsub()
                await sub.subscribe(f"draw:{canvas_id}", f"chat:{canvas_id}")
                async for message in sub.listen():
                    if message["type"] == "subscribe":
                        continue
                    try:
                        data = json.loads(message["data"])
                        data["sdelay"] = f"{(time() - data['stime']) * 1000:.3f}"
                        await self.send_broadcast(canvas_id, data)
                    except TypeError as e:
                        pass
                    if not self.subscribed[canvas_id]:
                        break
            except redis.exceptions.ConnectionError:
                self.subscribed[canvas_id] = False

    async def connect(self, canvas_id: uuid.UUID, websocket: WebSocket) -> None:
        """ Accept WebSocket connection and subscribe to available streams. """
        if canvas_id not in self.active_connections:
            self.active_connections[canvas_id] = []
            self.subscribed[canvas_id] = False
        self.active_connections[canvas_id].append(websocket)
        await websocket.accept()

    def disconnect(self, canvas_id: uuid.UUID, websocket: WebSocket) -> None:
        """ On client disconnection remove client from active connections. """
        self.active_connections[canvas_id].remove(websocket)

    @staticmethod
    async def send(websocket: WebSocket, message):
        """ Send JSON message to a single client."""
        await websocket.send_json(message)

    async def send_broadcast(self, canvas_id: uuid.UUID, message) -> None:
        """ Send broadcast JSON message to all active clients. """
        for connection in self.active_connections[canvas_id]:
            await connection.send_json(message)

manager = ConnectionManager()

# Create FastAPI app instance
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    pass

@app.get("/")
async def read_index():
    return FileResponse('draw.html')

class CanvasPoint(BaseModel):
    """ BaseModel to define draw point message. """
    t: Literal["point"]
    c: str
    x: int
    y: int
    color: Optional[constr(max_length=9, regex="^#")]
    width: int = Field(ge=1, le=10)
    stime: float
    ctime: float

class CanvasLine(BaseModel):
    """ BaseModel to define draw line message. """
    t: Literal["line"]
    c: str
    fx: int
    fy: int
    tx: int
    ty: int
    color: Optional[constr(max_length=9, regex="^#")]
    width: int = Field(ge=1, le=10)
    stime: float
    ctime: int

class CanvasClear(BaseModel):
    """ Basemodel to define a clear canvas message. """
    t: Literal["clear"]
    c: Optional[str]
    stime: float
    ctime: int

class ChatMessage(BaseModel):
    t: Literal["chat"]
    stime: float
    m: constr(max_length=512)

TYPES = {
    "point": CanvasPoint,
    "line": CanvasLine,
    "clear": CanvasClear,
    "chat": ChatMessage
}

@app.websocket("/ws/{canvas_id}")
async def websocket_endpoint(canvas_id: uuid.UUID, websocket: WebSocket):
    """ Draw client websocket endpoint. """
    await manager.connect(canvas_id, websocket)
    print(f"Connected {websocket}")
    try:
        while True:
            res = await websocket.receive_json()
            if "t" in res.keys():
                if res["t"] == "connected":
                    await read_stream(canvas_id, "drawstream", websocket)
                    await read_stream(canvas_id, "chatstream", websocket)
                else:
                    try:
                        res_json = ""
                        res["stime"] = time()
                        if res["t"] in TYPES:
                            res_json = TYPES[res["t"]](**res).json()
                        else:
                            await manager.send(websocket, {"error": "invalid type"})
                        if res["t"] != "chat":
                            await rpool.publish(f"draw:{canvas_id}", res_json)
                            if res["t"] == "clear":
                                await rpool.delete(f"drawstream:{canvas_id}")
                            else:
                                await rpool.xadd(
                                    name=f"drawstream:{canvas_id}",
                                    fields={"json": res_json}
                                )
                        else:
                            await rpool.publish(f"chat:{canvas_id}", res_json)
                            await rpool.xadd(
                                name=f"chatstream:{canvas_id}",
                                fields={"json": res_json}
                            )
                    except ValidationError:
                        await manager.send(websocket, {"error": "invalid message"})
            else:
                await manager.send(websocket, {"error": "no message type specified"})

    except Exception as e:
        print(f"Client disconnected: {websocket}")
        manager.disconnect(canvas_id, websocket)

@app.get("/sub/{canvas_id}")
async def subscribe(canvas_id: uuid.UUID, background_tasks: BackgroundTasks):
    """ Subscribe needs to be called by one client for background processing. """
    if not manager.subscribed[canvas_id]:
        print("foo")
        background_tasks.add_task(manager.subscribe, canvas_id)

async def read_stream(canvas_id: uuid.UUID, stream: str, websocket: WebSocket):
    start_id = 0
    while True:
        results = await rpool.xread(
            streams={
                f"{stream}:{canvas_id}": start_id,},
            count=100
        )
        if results:
            for entry in results[0][1]:
                await manager.send(websocket, json.loads(entry[1]["json"]))
            start_id = results[0][1][-1][0]
        else:
            break

@app.get("/uuid/new", response_class=JSONResponse)
def get_new_uuid():
    return {"uuid": uuid.uuid4()}

async def main():
    pass

if __name__ == '__main__':
    asyncio.run(main())
