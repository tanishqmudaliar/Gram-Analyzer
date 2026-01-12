from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from .config import get_settings
from .database import init_db, connect_db, disconnect_db
from .routes import auth, analytics
from .log_stream import handle_websocket
from .error_handler import setup_exception_handlers
from .health import router as health_router
import time

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print(f"🚀 Starting {settings.app_name}...")
    print(f"📝 Debug mode: {settings.debug}")
    print(f"🔑 Machine UUID: {settings.machine_uuid[:8]}...")
    
    await init_db()
    await connect_db()
    print("✅ Database connected")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await disconnect_db()
    print("✅ Cleanup complete")


app = FastAPI(
    title="GramAnalyzer API",
    description="Instagram Analytics API powered by Instagrapi",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
)

# Middleware - order matters!
# 1. CORS (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "capacitor://localhost",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(health_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "GramAnalyzer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live log streaming."""
    await handle_websocket(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )