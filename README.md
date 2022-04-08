# Javascript canvas drawing tool using Redis pub/sub

## Features
 * Uses [FastAPI](https://fastapi.tiangolo.com/) for serving WebSockets
 * Draw commands are communicated using Redis PubSub
 * There is no local echo
 * Drawings are also stored to a [Redis Stream](https://redis.io/docs/manual/data-types/streams/) for replay
   * Stream is deleted on clear

## Usage

```
pip install -r requirements.txt
uvicorn websocket:app
```

Redis settings can be defined with environment variables `REDIS_HOST`, `REDIS_PORT` and `REDIS_PASS`.

Server will by default listen on `http://127.0.0.1:8000`. Alternatively you can give uvicorn parameters `--host` and `--port`

By default a new UUID will be generated on access none is specified. Each canvas has its own pubsub topic and stream.
