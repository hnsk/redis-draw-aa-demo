# Javascript canvas drawing tool using Redis pub/sub

## Features
 * Uses [FastAPI](https://fastapi.tiangolo.com/) for serving WebSockets
 * Draw commands are communicated using Redis PubSub
 * There is no local echo

## Usage

```
pip install -r requirements.txt
uvicorn websocket:app
```

Redis settings can be defined with environment variables `REDIS_HOST`, `REDIS_PORT` and `REDIS_PASS`.

Server will by default listen on `127.0.0.1:8000`. Alternatively you can give uvicorn parameters `--host` and `--port`
