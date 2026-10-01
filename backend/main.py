"""
SecureRAG FastAPI Backend Entry Point.

Why it is needed:
Configures the FastAPI application, mounts routes, handles CORS for Streamlit frontend,
and provides exception handlers to protect sensitive details from normal users.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes import health, documents, chat, users

# Configure application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SecureRAG")

app = FastAPI(
    title="SecureRAG API",
    description="Permission-Aware Multi-Tenant Document Intelligence Platform API",
    version="1.0.0"
)

# Enable CORS for Streamlit / Frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler ensuring stack traces are logged internally
    while returning safe, structured error responses to clients.
    """
    logger.error(f"Unhandled Exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
