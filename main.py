from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import uuid
import time

app = FastAPI()

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-xmrp4q.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Rate Limiter
# ----------------------------
RATE_LIMIT = 9
WINDOW = 10  # seconds
clients = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Don't rate-limit CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()

        timestamps = clients.get(client_id, [])

        # Keep only timestamps within the window
        timestamps = [t for t in timestamps if now - t < WINDOW]

        if len(timestamps) >= RATE_LIMIT:
            request_id = (
                request.headers.get("X-Request-ID")
                or str(uuid.uuid4())
            )

            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "request_id": request_id,
                },
            )

            response.headers["X-Request-ID"] = request_id
            return response

        timestamps.append(now)
        clients[client_id] = timestamps

        return await call_next(request)


# ----------------------------
# Request Context
# ----------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = (
            request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response


# IMPORTANT:
# RequestContext is OUTERMOST.
# BaseHTTPMiddleware executes in reverse order.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "22f1001700@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }