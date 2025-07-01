"""
Sistema de métricas usando Prometheus
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Métricas da API
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

# Métricas do banco de dados
database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation', 'table']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

# Métricas de busca
search_requests_total = Counter(
    'search_requests_total',
    'Total search requests',
    ['search_type']
)

search_duration_seconds = Histogram(
    'search_duration_seconds',
    'Search duration in seconds',
    ['search_type']
)

search_results_count = Histogram(
    'search_results_count',
    'Number of search results returned',
    ['search_type']
)

# Métricas do Celery
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name']
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue_name']
)

# Métricas de PDFs
pdf_processed_total = Counter(
    'pdf_processed_total',
    'Total PDFs processed',
    ['status']
)

pdf_processing_duration_seconds = Histogram(
    'pdf_processing_duration_seconds',
    'PDF processing duration in seconds'
)

pdf_size_bytes = Histogram(
    'pdf_size_bytes',
    'PDF file size in bytes'
)

# Decoradores para instrumentação automática

def track_http_requests(func: Callable) -> Callable:
    """Decorator para rastrear requests HTTP"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Extrair informações do request
        request = kwargs.get('request') or args[0] if args else None
        method = getattr(request, 'method', 'UNKNOWN')
        path = getattr(request.url, 'path', 'unknown') if hasattr(request, 'url') else 'unknown'
        
        try:
            response = await func(*args, **kwargs)
            status = getattr(response, 'status_code', 200)
            
            # Registrar métricas
            http_requests_total.labels(method=method, endpoint=path, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(
                time.time() - start_time
            )
            
            return response
        except Exception as e:
            # Registrar erro
            http_requests_total.labels(method=method, endpoint=path, status=500).inc()
            raise
    
    return wrapper


def track_database_queries(operation: str, table: str = 'unknown'):
    """Decorator para rastrear queries do banco"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                database_queries_total.labels(operation=operation, table=table).inc()
                database_query_duration_seconds.labels(operation=operation, table=table).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                logger.error(f"Database query failed: {e}")
                raise
        
        return wrapper
    return decorator


def track_search_requests(search_type: str):
    """Decorator para rastrear requests de busca"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Registrar métricas
                search_requests_total.labels(search_type=search_type).inc()
                search_duration_seconds.labels(search_type=search_type).observe(
                    time.time() - start_time
                )
                
                # Contar resultados se possível
                if hasattr(result, 'get') and 'results' in result:
                    results_count = len(result['results'])
                    search_results_count.labels(search_type=search_type).observe(results_count)
                
                return result
            except Exception as e:
                logger.error(f"Search request failed: {e}")
                raise
        
        return wrapper
    return decorator


def track_celery_tasks(task_name: str):
    """Decorator para rastrear tarefas Celery"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(task_name=task_name, status='success').inc()
                celery_task_duration_seconds.labels(task_name=task_name).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                celery_tasks_total.labels(task_name=task_name, status='failure').inc()
                logger.error(f"Celery task {task_name} failed: {e}")
                raise
        
        return wrapper
    return decorator


def track_pdf_processing(func: Callable) -> Callable:
    """Decorator para rastrear processamento de PDFs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            pdf_processed_total.labels(status='success').inc()
            pdf_processing_duration_seconds.observe(time.time() - start_time)
            
            # Registrar tamanho do PDF se disponível
            if 'pdf_path' in kwargs:
                try:
                    import os
                    size = os.path.getsize(kwargs['pdf_path'])
                    pdf_size_bytes.observe(size)
                except:
                    pass
            
            return result
        except Exception as e:
            pdf_processed_total.labels(status='failure').inc()
            logger.error(f"PDF processing failed: {e}")
            raise
    
    return wrapper


class MetricsCollector:
    """Coletor centralizado de métricas"""
    
    @staticmethod
    def update_connection_count(count: int):
        """Atualiza contador de conexões ativas"""
        active_connections.set(count)
    
    @staticmethod
    def update_database_connections(count: int):
        """Atualiza contador de conexões do banco"""
        database_connections_active.set(count)
    
    @staticmethod
    def update_queue_length(queue_name: str, length: int):
        """Atualiza tamanho da fila Celery"""
        celery_queue_length.labels(queue_name=queue_name).set(length)
    
    @staticmethod
    def get_metrics() -> str:
        """Retorna métricas no formato Prometheus"""
        return generate_latest()
    
    @staticmethod
    def get_content_type() -> str:
        """Retorna content type das métricas"""
        return CONTENT_TYPE_LATEST


# Instância global do coletor
metrics_collector = MetricsCollector()