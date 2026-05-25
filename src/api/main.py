from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

# Importar routers
from routers import (
    auth,
    chess,
    logs,
    import_pgn,
    features,
    exercises,
    reports,
    notifications,
    analysis,
)

from middleware.jwt_middleware import JWTMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    print(">> Iniciando Chess Trainer API...")
    yield
    print("<< Cerrando Chess Trainer API...")


# Crear la aplicación FastAPI
app = FastAPI(
    title="Chess Trainer API",
    description="API unificada para el sistema Chess Trainer con React + FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
    ],  # Vite y React dev servers (múltiples puertos)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware JWT (aplicar a rutas protegidas)
jwt_middleware = JWTMiddleware(
    excluded_paths=[
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
        "/api/auth/login",
        # Rutas temporales para testing sin auth (si son necesarias)
        "/api/chess/test/games/1",
        "/api/chess/test/games/2",
        "/api/chess/test/analyze",
    ]
)


# Middleware personalizado para aplicar JWT
@app.middleware("http")
async def jwt_middleware_handler(request: Request, call_next):
    """Aplicar middleware JWT personalizado"""
    return await jwt_middleware(request, call_next)


# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(chess.router, prefix="/api/chess", tags=["chess"])
app.include_router(logs.router, prefix="/api/logs", tags=["logging"])
app.include_router(import_pgn.router, tags=["import"])
app.include_router(features.router, tags=["features"])
app.include_router(exercises.router, tags=["exercises"])
app.include_router(reports.router, tags=["reports"])
app.include_router(notifications.router, tags=["notifications"])
app.include_router(analysis.router, tags=["analysis", "ml", "shap"])


@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Chess Trainer API - ¡Bienvenido!",
            "version": "1.0.0",
            "status": "active",
            "docs": "/docs",
        },
        headers={"Content-Type": "application/json"},
    )


@app.get("/favicon.ico")
async def favicon():
    """Endpoint para favicon (evita errores 404)"""
    return JSONResponse(
        status_code=200,
        content={"message": "No favicon available"},
        headers={"Content-Type": "application/json"},
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint para Render y monitoring.
    Verifica: API, Database, Ollama (si está configurado)
    """
    import httpx
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "service": "chess-trainer-api",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": "ok",
            "database": "unknown",
            "ollama": "unknown"
        }
    }
    
    # Check Database
    try:
        from db.session import get_session
        db = get_session()
        db.execute("SELECT 1")
        db.close()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama (optional - don't fail if not configured)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:11434/api/version")
            if response.status_code == 200:
                health_status["checks"]["ollama"] = "ok"
            else:
                health_status["checks"]["ollama"] = "not_running"
    except Exception:
        health_status["checks"]["ollama"] = "not_configured"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status,
        headers={"Content-Type": "application/json"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador global de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador global de excepciones generales"""
    import traceback

    error_detail = traceback.format_exc()
    print(f"ERROR NO MANEJADO: {exc}")
    print(f"TRACEBACK: {error_detail}")

    # For development, return the actual error
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": f"Error interno del servidor: {str(exc)}",
            "detail": error_detail,
            "status_code": 500,
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


