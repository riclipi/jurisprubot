"""
API REST principal com FastAPI
Endpoints para busca, análise e gerenciamento de jurisprudência
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Dict
import logging

from .routers import auth, search, cases, analytics, admin
from .models import HealthCheck
from ..database.database_manager import get_db_manager
from ..monitoring import setup_default_logging, metrics_collector, get_logger

# Configurar logging
setup_default_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando API Jurisprudência...")
    db = get_db_manager()
    
    # Verificar conexão com banco
    try:
        stats = db.get_statistics()
        logger.info(f"Banco conectado. Total de casos: {stats.get('total_cases', 0)}")
    except Exception as e:
        logger.error(f"Erro ao conectar com banco: {e}")
    
    yield
    
    # Shutdown
    logger.info("Encerrando API...")


# Criar aplicação
app = FastAPI(
    title="Jurisprudência API",
    description="API para busca e análise de jurisprudência do TJSP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/", response_model=HealthCheck)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Jurisprudência API",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Verifica saúde do sistema"""
    db = get_db_manager()
    
    try:
        # Verificar banco
        stats = db.get_statistics()
        
        return {
            "status": "healthy",
            "service": "Jurisprudência API",
            "version": "1.0.0",
            "database": "connected",
            "total_cases": stats.get("total_cases", 0),
            "total_documents": stats.get("total_documents", 0)
        }
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/v1/stats")
async def get_statistics():
    """Retorna estatísticas gerais do sistema"""
    db = get_db_manager()
    
    try:
        stats = db.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "O recurso solicitado não foi encontrado",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return {
        "error": "Internal Server Error",
        "message": "Erro interno do servidor",
        "detail": str(exc) if app.debug else None
    }


@app.get("/metrics")
async def get_metrics():
    """Endpoint para métricas do Prometheus"""
    return Response(
        content=metrics_collector.get_metrics(),
        media_type=metrics_collector.get_content_type()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )