from fastapi import APIRouter
from datetime import datetime
from .database import database
from .config import get_settings
import psutil
import platform

router = APIRouter(tags=["Health"])
settings = get_settings()
start_time = datetime.utcnow()


@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with system info."""
    try:
        # Database check
        await database.fetch_one("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "environment": "development" if settings.debug else "production",
        "components": {
            "database": db_status,
            "api": "healthy"
        },
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    }


@router.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness probe."""
    try:
        await database.fetch_one("SELECT 1")
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {"alive": True}