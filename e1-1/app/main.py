import os
import redis 

from fastapi import FastAPI

app = FastAPI()

redis_host = os.environ.get("REDIS_HOST", "localhost")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)


@app.get("/")
def read_root():
    count = r.incr("visit_count")
    return {"message": "Hello", "visit_count": count}

@app.get("/health")
def read_health():
    return {"status": "ok"}