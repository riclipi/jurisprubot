"""
Tasks de manutenção e limpeza do sistema
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

from celery import Task
from src.pipeline.celery_app import app
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


@app.task
def cleanup_old_logs(days: int = 30):
    """
    Remove logs antigos do banco
    
    Args:
        days: Dias para manter logs
    """
    logger.info(f"Iniciando limpeza de logs mais antigos que {days} dias")
    
    db = get_db_manager()
    
    try:
        db.cleanup_old_logs(days)
        
        # Também limpar logs do Celery
        with db.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Limpar queries antigas
            deleted_queries = session.query(db.SearchQuery).filter(
                db.SearchQuery.created_at < cutoff_date
            ).delete()
            
            logger.info(f"Removidas {deleted_queries} queries antigas")
        
        return {
            'status': 'success',
            'cutoff_days': days,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza de logs: {e}")
        raise


@app.task
def vacuum_database():
    """
    Executa VACUUM ANALYZE no PostgreSQL
    """
    logger.info("Executando VACUUM ANALYZE no banco")
    
    db = get_db_manager()
    
    try:
        db.vacuum_analyze()
        
        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao executar VACUUM: {e}")
        raise


@app.task
def check_system_health() -> Dict:
    """
    Verifica saúde do sistema
    """
    logger.info("Verificando saúde do sistema")
    
    db = get_db_manager()
    health = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'issues': []
    }
    
    try:
        # Verificar conexão com banco
        with db.get_session() as session:
            session.execute("SELECT 1")
        health['database'] = 'ok'
    except Exception as e:
        health['database'] = 'error'
        health['issues'].append(f"Database: {str(e)}")
        health['status'] = 'unhealthy'
    
    # Verificar espaço em disco
    import shutil
    usage = shutil.disk_usage('/')
    free_percent = (usage.free / usage.total) * 100
    
    health['disk_free_percent'] = round(free_percent, 2)
    if free_percent < 10:
        health['issues'].append(f"Low disk space: {free_percent:.1f}% free")
        health['status'] = 'warning' if health['status'] == 'healthy' else health['status']
    
    # Verificar estatísticas
    try:
        stats = db.get_statistics()
        health['statistics'] = stats
        
        # Alertas baseados em estatísticas
        if stats.get('total_cases', 0) == 0:
            health['issues'].append("No cases in database")
            
    except Exception as e:
        health['issues'].append(f"Stats error: {str(e)}")
    
    logger.info(f"Health check completed: {health['status']}")
    
    return health


@app.task
def cleanup_failed_tasks():
    """
    Limpa tasks que falharam permanentemente
    """
    logger.info("Limpando tasks com falha permanente")
    
    db = get_db_manager()
    
    try:
        with db.get_session() as session:
            # Buscar casos com status 'error' há mais de 7 dias
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            failed_cases = session.query(db.Case).filter(
                db.Case.status == 'error',
                db.Case.updated_at < cutoff
            ).all()
            
            cleaned = 0
            for case in failed_cases:
                # Tentar reprocessar ou marcar como abandonado
                if case.pdf_path and Path(case.pdf_path).exists():
                    # Reagendar processamento
                    from .processing import process_pdf
                    process_pdf.delay(str(case.id))
                    case.status = 'downloaded'
                    logger.info(f"Reagendado processamento do caso {case.case_number}")
                else:
                    # Marcar como abandonado
                    case.status = 'abandoned'
                    logger.warning(f"Caso {case.case_number} marcado como abandonado")
                
                cleaned += 1
            
            session.commit()
        
        return {
            'status': 'success',
            'cleaned_count': cleaned,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar tasks com falha: {e}")
        raise


@app.task
def optimize_embeddings():
    """
    Otimiza armazenamento de embeddings (compactação, deduplicação)
    """
    logger.info("Otimizando embeddings")
    
    db = get_db_manager()
    
    try:
        with db.get_session() as session:
            # Contar embeddings duplicados
            duplicates = session.execute("""
                SELECT chunk_id, COUNT(*) as count
                FROM embeddings
                GROUP BY chunk_id
                HAVING COUNT(*) > 1
            """).fetchall()
            
            removed = 0
            for chunk_id, count in duplicates:
                # Manter apenas o mais recente
                embeddings = session.query(db.Embedding).filter_by(
                    chunk_id=chunk_id
                ).order_by(db.Embedding.created_at.desc()).all()
                
                # Remover duplicados
                for emb in embeddings[1:]:
                    session.delete(emb)
                    removed += 1
            
            session.commit()
            
            logger.info(f"Removidos {removed} embeddings duplicados")
        
        # Executar VACUUM após limpeza
        vacuum_database.delay()
        
        return {
            'status': 'success',
            'duplicates_removed': removed,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao otimizar embeddings: {e}")
        raise