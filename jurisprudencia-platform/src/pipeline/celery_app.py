"""
Configuração do Celery para pipeline de dados em tempo real
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Criar instância do Celery
app = Celery('jurisprudencia')

# Configuração
app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Serialização
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Task execution
    task_soft_time_limit=300,  # 5 minutos
    task_time_limit=600,       # 10 minutos
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Task routing
    task_routes={
        'pipeline.tasks.scraping.*': {'queue': 'scraping'},
        'pipeline.tasks.processing.*': {'queue': 'processing'},
        'pipeline.tasks.embedding.*': {'queue': 'embedding'},
        'pipeline.tasks.notification.*': {'queue': 'notification'},
    },
    
    # Queues configuration
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('scraping', Exchange('scraping'), routing_key='scraping'),
        Queue('processing', Exchange('processing'), routing_key='processing'),
        Queue('embedding', Exchange('embedding'), routing_key='embedding'),
        Queue('notification', Exchange('notification'), routing_key='notification'),
    ),
    
    # Retry configuration
    task_annotations={
        '*': {
            'rate_limit': '10/s',
            'max_retries': 3,
            'default_retry_delay': 60,  # 1 minuto
        },
        'pipeline.tasks.scraping.*': {
            'rate_limit': '1/s',  # Respeitar rate limit do TJSP
        },
    },
)

# Beat schedule para tarefas agendadas
app.conf.beat_schedule = {
    # Verificar novos casos a cada 30 minutos
    'check-new-cases': {
        'task': 'pipeline.tasks.scraping.check_new_cases',
        'schedule': crontab(minute='*/30'),
        'options': {
            'expires': 1800,  # Expira em 30 minutos
        }
    },
    
    # Processar PDFs pendentes a cada 10 minutos
    'process-pending-pdfs': {
        'task': 'pipeline.tasks.processing.process_pending_pdfs',
        'schedule': crontab(minute='*/10'),
    },
    
    # Gerar embeddings a cada 15 minutos
    'generate-embeddings': {
        'task': 'pipeline.tasks.embedding.generate_pending_embeddings',
        'schedule': crontab(minute='*/15'),
    },
    
    # Limpeza de logs antigos (diariamente às 3h)
    'cleanup-old-logs': {
        'task': 'pipeline.tasks.maintenance.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Estatísticas diárias (todos os dias às 8h)
    'daily-statistics': {
        'task': 'pipeline.tasks.reporting.generate_daily_report',
        'schedule': crontab(hour=8, minute=0),
    },
}

# Auto-descoberta de tasks
app.autodiscover_tasks(['src.pipeline.tasks'])

# Configuração de logging
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'