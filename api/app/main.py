from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import get_settings
from .database import init_db, connect_db, disconnect_db
from .routes import auth, analytics
from .log_stream import handle_websocket

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    await init_db()
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(
    title="GramAnalyzer API",
    description="Instagram Analytics API powered by Instagrapi",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "capacitor://localhost",  # For Capacitor mobile app
        "http://localhost",  # For Capacitor Android
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "GramAnalyzer API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live log streaming."""
    await handle_websocket(websocket)
