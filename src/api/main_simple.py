from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Importar solo el router de chess sin auth
from routers import chess


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    print("🚀 Iniciando Chess Trainer API...")
    yield
    print("🛑 Cerrando Chess Trainer API...")


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
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir solo router de chess (sin auth por ahora)
app.include_router(chess.router, prefix="/chess", tags=["chess"])


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
    """Endpoint de salud"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "chess-trainer-api"},
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
    print(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "status_code": 500,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_simple:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
