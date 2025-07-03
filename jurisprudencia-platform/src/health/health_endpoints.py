#!/usr/bin/env python3
"""
🌐 ENDPOINTS DE HEALTH CHECK E STATUS
Endpoints FastAPI para monitoramento de saúde
"""

from fastapi import APIRouter, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

from .health_check import (
    HealthCheckService, 
    HealthStatus,
    create_health_service
)
from ..auth.dependencies import get_current_user_optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/health", tags=["Health"])

# Serviço global (será inicializado na aplicação)
health_service: Optional[HealthCheckService] = None


def get_health_service() -> HealthCheckService:
    """Obter serviço de health check"""
    if not health_service:
        raise HTTPException(status_code=500, detail="Health service not initialized")
    return health_service


@router.get("/", response_model=Dict[str, str])
async def health_check():
    """
    Health check básico (rápido)
    
    Retorna:
    - 200: Sistema saudável
    - 503: Sistema não saudável
    """
    try:
        service = get_health_service()
        health = await service.check_health(use_cache=True)
        
        response_data = {
            "status": health.status.value,
            "timestamp": health.timestamp.isoformat()
        }
        
        if health.status == HealthStatus.HEALTHY:
            return response_data
        elif health.status == HealthStatus.DEGRADED:
            return JSONResponse(
                status_code=200,
                content=response_data,
                headers={"X-Health-Status": "degraded"}
            )
        else:
            return JSONResponse(
                status_code=503,
                content=response_data
            )
            
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/live", response_model=Dict[str, str])
async def liveness_probe():
    """
    Liveness probe para Kubernetes
    
    Verifica se a aplicação está viva e respondendo
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_probe():
    """
    Readiness probe para Kubernetes
    
    Verifica se a aplicação está pronta para receber tráfego
    """
    try:
        service = get_health_service()
        health = await service.check_health(use_cache=True)
        
        # Só está ready se healthy ou degraded
        is_ready = health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        
        response_data = {
            "ready": is_ready,
            "status": health.status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if is_ready:
            return response_data
        else:
            return JSONResponse(
                status_code=503,
                content=response_data
            )
            
    except Exception as e:
        logger.error(f"Erro no readiness probe: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/startup", response_model=Dict[str, Any])
async def startup_probe():
    """
    Startup probe para Kubernetes
    
    Verifica se a aplicação completou a inicialização
    """
    try:
        service = get_health_service()
        
        # Verificar se todos os componentes críticos estão inicializados
        health = await service.check_health(use_cache=False)
        
        # Verificar componentes críticos
        critical_components = ['PostgreSQL', 'Redis']
        critical_healthy = all(
            comp.status != HealthStatus.UNKNOWN
            for comp in health.components
            if comp.component in critical_components
        )
        
        response_data = {
            "started": critical_healthy,
            "uptime_seconds": health.uptime_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if critical_healthy:
            return response_data
        else:
            return JSONResponse(
                status_code=503,
                content=response_data
            )
            
    except Exception as e:
        logger.error(f"Erro no startup probe: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "started": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/status", response_model=Dict[str, Any])
async def detailed_status(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Status detalhado do sistema
    
    Requer autenticação para informações completas
    """
    try:
        service = get_health_service()
        
        # Status básico para usuários não autenticados
        if not current_user:
            health = await service.check_health(use_cache=True)
            return {
                "status": health.status.value,
                "timestamp": health.timestamp.isoformat(),
                "version": health.version,
                "message": "Authenticate for detailed information"
            }
        
        # Status detalhado para usuários autenticados
        detailed = await service.get_detailed_status()
        
        # Adicionar informações do usuário
        detailed['requested_by'] = {
            'user_id': current_user.get('id'),
            'username': current_user.get('username')
        }
        
        return detailed
        
    except Exception as e:
        logger.error(f"Erro ao obter status detalhado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Métricas no formato Prometheus
    
    Endpoint para scraping do Prometheus
    """
    try:
        service = get_health_service()
        
        # Forçar atualização das métricas
        await service.check_health(use_cache=False)
        
        # Obter métricas
        metrics = service.get_prometheus_metrics()
        
        return PlainTextResponse(
            content=metrics,
            media_type="text/plain; version=0.0.4"
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{component_type}", response_model=Dict[str, Any])
async def component_status(
    component_type: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Status de um tipo específico de componente
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        service = get_health_service()
        detailed = await service.get_detailed_status()
        
        if component_type not in detailed['components']:
            raise HTTPException(
                status_code=404, 
                detail=f"Component type '{component_type}' not found"
            )
        
        return {
            "component_type": component_type,
            "components": detailed['components'][component_type],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter status do componente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_health_cache(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Forçar atualização do cache de health check
    
    Requer autenticação
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        service = get_health_service()
        
        # Forçar atualização
        health = await service.check_health(use_cache=False)
        
        return {
            "status": "refreshed",
            "health_status": health.status.value,
            "timestamp": health.timestamp.isoformat(),
            "refreshed_by": current_user.get('username')
        }
        
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def health_history(
    hours: int = 24,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Histórico de health checks (se disponível)
    
    Requer autenticação
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Implementar armazenamento e recuperação de histórico
    return {
        "message": "Health history not implemented yet",
        "requested_hours": hours,
        "timestamp": datetime.utcnow().isoformat()
    }


# Funções de inicialização
def init_health_endpoints(app_config: Dict[str, Any]):
    """Inicializar endpoints de health com configuração"""
    global health_service
    
    # Criar serviço com configuração
    health_service = create_health_service(app_config)
    
    logger.info("Health endpoints initialized")


# Middleware para adicionar headers de saúde
async def health_status_middleware(request, call_next):
    """Adicionar status de saúde aos headers da resposta"""
    response = await call_next(request)
    
    # Adicionar header se possível
    try:
        if health_service:
            health = await health_service.check_health(use_cache=True)
            response.headers["X-Health-Status"] = health.status.value
            response.headers["X-Health-Timestamp"] = health.timestamp.isoformat()
    except:
        pass
    
    return response