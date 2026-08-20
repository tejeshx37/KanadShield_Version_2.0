from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import (
    ai,
    acts,
    alerts,
    auth,
    bookmarks,
    change_radar,
    citizens,
    compare,
    dashboard,
    documents,
    graph,
    judgments,
    organizations,
    research,
    schemes,
    search,
    timeline,
)
from app.core.config import get_settings
from app.core.rate_limit import limiter

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = settings.X_FRAME_OPTIONS
    response.headers["Content-Security-Policy"] = settings.CSP_HEADER_VALUE
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = {"error": {"code": "http_error", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces, SQL text, or filesystem paths to the client.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(acts.router, prefix=settings.API_V1_PREFIX)
app.include_router(judgments.router, prefix=settings.API_V1_PREFIX)
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(graph.router, prefix=settings.API_V1_PREFIX)
app.include_router(compare.router, prefix=settings.API_V1_PREFIX)
app.include_router(timeline.router, prefix=settings.API_V1_PREFIX)
app.include_router(change_radar.router, prefix=settings.API_V1_PREFIX)
app.include_router(schemes.router, prefix=settings.API_V1_PREFIX)
app.include_router(citizens.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookmarks.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(research.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
