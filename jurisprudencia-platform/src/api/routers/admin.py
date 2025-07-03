"""
Router para endpoints administrativos
Gerenciamento do sistema e tasks
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from datetime import datetime

from ..models import TaskRequest, TaskResponse
from ...database.database_manager import get_db_manager
from ...pipeline.celery_app import app as celery_app

logger = logging.getLogger(__name__)
router = APIRouter()

# Segurança básica (melhorar em produção)
security = HTTPBearer()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica token de admin (implementar autenticação real)"""
    # TODO: Implementar verificação real de JWT
    if credentials.credentials != "admin-secret-token":
        raise HTTPException(status_code=401, detail="Token inválido")
    return credentials.credentials


@router.get("/system/status")
async def get_system_status(
    token: str = Depends(verify_admin_token)
):
    """
    Retorna status completo do sistema
    """
    try:
        db = get_db_manager()
        
        # Status do banco
        db_stats = db.get_statistics()
        
        # Status do Celery
        celery_status = {
            "workers": {},
            "scheduled_tasks": 0,
            "active_tasks": 0
        }
        
        try:
            # Inspecionar workers
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            active = inspect.active()
            
            if stats:
                for worker, info in stats.items():
                    celery_status["workers"][worker] = {
                        "status": "online",
                        "pool": info.get("pool", {}),
                        "total_tasks": info.get("total", {})
                    }
                    
            if active:
                for worker, tasks in active.items():
                    celery_status["active_tasks"] += len(tasks)
                    
        except Exception as e:
            logger.error(f"Erro ao inspecionar Celery: {e}")
            celery_status["error"] = str(e)
        
        # Status geral
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "connected",
                "statistics": db_stats
            },
            "celery": celery_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/execute", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    token: str = Depends(verify_admin_token)
):
    """
    Executa uma task Celery manualmente
    """
    try:
        # Mapear nomes de tasks
        task_map = {
            "check_new_cases": "src.pipeline.tasks.scraping.check_new_cases",
            "process_pending": "src.pipeline.tasks.processing.process_pending_pdfs",
            "generate_embeddings": "src.pipeline.tasks.embedding.generate_pending_embeddings",
            "daily_report": "src.pipeline.tasks.reporting.generate_daily_report",
            "cleanup_logs": "src.pipeline.tasks.maintenance.cleanup_old_logs",
            "health_check": "src.pipeline.tasks.maintenance.check_system_health"
        }
        
        full_task_name = task_map.get(request.task_name, request.task_name)
        
        # Enviar task
        result = celery_app.send_task(
            full_task_name,
            args=request.args or [],
            kwargs=request.kwargs or {}
        )
        
        return TaskResponse(
            task_id=result.id,
            task_name=full_task_name,
            status="submitted",
            submitted_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Erro ao executar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    token: str = Depends(verify_admin_token)
):
    """
    Verifica status de uma task
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)
                
        return response
        
    except Exception as e:
        logger.error(f"Erro ao verificar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    token: str = Depends(verify_admin_token)
):
    """
    Cancela uma task em execução
    """
    try:
        result = celery_app.AsyncResult(task_id)
        result.revoke(terminate=True)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao cancelar task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/processing")
async def get_processing_logs(
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    token: str = Depends(verify_admin_token)
):
    """
    Retorna logs de processamento
    """
    try:
        db = get_db_manager()
        
        with db.get_session() as session:
            query = session.query(db.ProcessingLog)
            
            if status:
                query = query.filter(db.ProcessingLog.status == status)
                
            logs = query.order_by(
                db.ProcessingLog.created_at.desc()
            ).limit(limit).all()
            
            return {
                "total": len(logs),
                "logs": [
                    {
                        "id": str(log.id),
                        "process_type": log.process_type,
                        "case_id": str(log.case_id) if log.case_id else None,
                        "status": log.status,
                        "error_message": log.error_message,
                        "start_time": log.start_time.isoformat() if log.start_time else None,
                        "duration_seconds": log.duration_seconds,
                        "created_at": log.created_at.isoformat()
                    }
                    for log in logs
                ]
            }
            
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/cleanup")
async def cleanup_system(
    days: int = Query(30, ge=7, le=365),
    token: str = Depends(verify_admin_token)
):
    """
    Executa limpeza do sistema
    """
    try:
        from ...pipeline.tasks.maintenance import cleanup_old_logs, optimize_embeddings
        
        # Agendar tasks de limpeza
        tasks = [
            cleanup_old_logs.delay(days),
            optimize_embeddings.delay()
        ]
        
        return {
            "success": True,
            "message": "Limpeza agendada",
            "tasks": [t.id for t in tasks],
            "cleanup_days": days
        }
        
    except Exception as e:
        logger.error(f"Erro ao agendar limpeza: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/database/vacuum")
async def vacuum_database(
    token: str = Depends(verify_admin_token)
):
    """
    Executa VACUUM ANALYZE no PostgreSQL
    """
    try:
        from ...pipeline.tasks.maintenance import vacuum_database
        
        task = vacuum_database.delay()
        
        return {
            "success": True,
            "message": "VACUUM agendado",
            "task_id": task.id
        }
        
    except Exception as e:
        logger.error(f"Erro ao agendar VACUUM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration(
    token: str = Depends(verify_admin_token)
):
    """
    Retorna configuração atual do sistema
    """
    import os
    
    # Configurações seguras para exibir
    safe_config = {
        "api": {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": os.getenv("API_PORT", "8000"),
            "workers": os.getenv("API_WORKERS", "4")
        },
        "database": {
            "url": "postgresql://***:***@***:5432/***",  # Ocultar credenciais
            "connected": True
        },
        "redis": {
            "url": "redis://***:6379/0",
            "connected": True
        },
        "embeddings": {
            "model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "dimension": os.getenv("EMBEDDING_DIMENSION", "384")
        },
        "celery": {
            "broker": "redis://***:6379/0",
            "timezone": os.getenv("CELERY_TIMEZONE", "America/Sao_Paulo")
        }
    }
    
    return safe_config