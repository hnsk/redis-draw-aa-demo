import json
from os import environ
from time import time

import redis.asyncio as redis

from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.responses import FileResponse

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or '6379')
REDIS_PASS = environ.get('REDIS_PASS') or None

rpool = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASS,
    decode_responses=True
)

class ConnectionManager:
    """ Class for managing WebSocket connections"""
    def __init__(self):
        self.active_connections: list = []
        self.subscribed = False
    
    async def subscribe(self):
        """ Hack to enable background subscription to Redis pubsub. """
        self.subscribed = True
        sub = rpool.pubsub()
        await sub.subscribe("draw")
        print("subscribed")
        async for message in sub.listen():
            if message["data"] != 1:
                data = json.loads(message["data"])
                data["sdelay"] = f"{(time() - data['stime']) * 1000:.3f}"
                await self.send_broadcast(data)

    async def connect(self, websocket: WebSocket) -> None:
        """ Accept WebSocket connection and subscribe to available streams. """
        self.active_connections.append(websocket)
        await websocket.accept()

    def disconnect(self, websocket: WebSocket) -> None:
        """ On client disconnection remove client from active connections. """
        self.active_connections.remove(websocket)

    @staticmethod
    async def send(websocket: WebSocket, message):
        """ Send JSON message to a single client."""
        await websocket.send_json(message)

    async def send_broadcast(self, message) -> None:
        """ Send broadcast JSON message to all active clients. """
        for connection in self.active_connections:
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

@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    """ Draw client websocket endpoint. """
    await manager.connect(websocket)
    print(f"Connected {websocket}")
    try:
        while True:
            res = await websocket.receive_json()
            res['stime'] = time()
            await rpool.publish("draw", json.dumps(res))

    except Exception as e:
        print(e)
        print(f"Client disconnected: {websocket}")
        manager.disconnect(websocket)

@app.get("/sub")
async def subscribe(background_tasks: BackgroundTasks):
    """ Subscribe needs to be called by one client for background processing. """
    if not manager.subscribed:
        print("subscribing")
        background_tasks.add_task(manager.subscribe)    
