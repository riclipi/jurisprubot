#!/usr/bin/env python3
"""
Script para executar workers do Celery
"""

import os
import sys
import click
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.celery_app import app

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.command()
@click.option(
    '--queue', '-q',
    multiple=True,
    default=['default'],
    help='Filas para processar (default, scraping, processing, embedding)'
)
@click.option(
    '--concurrency', '-c',
    default=4,
    help='Número de processos worker'
)
@click.option(
    '--loglevel', '-l',
    default='info',
    help='Nível de log (debug, info, warning, error)'
)
@click.option(
    '--autoscale',
    default='10,3',
    help='Autoscale workers (max,min)'
)
def run_worker(queue, concurrency, loglevel, autoscale):
    """Executa worker do Celery"""
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║     Jurisprudência Pipeline Worker       ║
    ╚══════════════════════════════════════════╝
    
    Filas: {', '.join(queue)}
    Concorrência: {concurrency}
    Log Level: {loglevel}
    Autoscale: {autoscale}
    """)
    
    # Montar comando
    argv = [
        'worker',
        f'--loglevel={loglevel}',
        f'--concurrency={concurrency}',
        f'--autoscale={autoscale}',
    ]
    
    # Adicionar filas
    for q in queue:
        argv.extend(['-Q', q])
    
    # Executar worker
    app.worker_main(argv)


@click.group()
def cli():
    """CLI para gerenciar pipeline Celery"""
    pass


@cli.command()
def beat():
    """Executa o scheduler (beat) do Celery"""
    print("""
    ╔══════════════════════════════════════════╗
    ║    Jurisprudência Pipeline Scheduler     ║
    ╚══════════════════════════════════════════╝
    """)
    
    argv = [
        'beat',
        '--loglevel=info',
    ]
    
    app.start(argv)


@cli.command()
def flower():
    """Executa o Flower (interface web para monitoramento)"""
    print("""
    ╔══════════════════════════════════════════╗
    ║    Jurisprudência Pipeline Monitor       ║
    ╚══════════════════════════════════════════╝
    
    Acesse: http://localhost:5555
    """)
    
    os.system('celery -A src.pipeline.celery_app flower')


@cli.command()
@click.option('--task', '-t', required=True, help='Nome da task')
@click.option('--args', '-a', help='Argumentos em formato JSON')
def run_task(task, args):
    """Executa uma task manualmente"""
    import json
    
    task_args = []
    if args:
        task_args = json.loads(args)
    
    # Mapear nomes curtos para nomes completos
    task_map = {
        'check_new': 'src.pipeline.tasks.scraping.check_new_cases',
        'process_pending': 'src.pipeline.tasks.processing.process_pending_pdfs',
        'generate_embeddings': 'src.pipeline.tasks.embedding.generate_pending_embeddings',
        'daily_report': 'src.pipeline.tasks.reporting.generate_daily_report',
        'health': 'src.pipeline.tasks.maintenance.check_system_health',
    }
    
    full_task_name = task_map.get(task, task)
    
    print(f"Executando task: {full_task_name}")
    print(f"Argumentos: {task_args}")
    
    result = app.send_task(full_task_name, args=task_args)
    print(f"Task ID: {result.id}")
    print("Aguardando resultado...")
    
    try:
        output = result.get(timeout=60)
        print("Resultado:")
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Erro: {e}")


@cli.command()
def status():
    """Verifica status do sistema"""
    from src.database.database_manager import get_db_manager
    
    print("Verificando status do sistema...")
    
    # Verificar Redis
    try:
        from redis import Redis
        redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        redis.ping()
        print("✓ Redis: OK")
    except Exception as e:
        print(f"✗ Redis: {e}")
    
    # Verificar PostgreSQL
    try:
        db = get_db_manager()
        stats = db.get_statistics()
        print("✓ PostgreSQL: OK")
        print(f"  - Total de casos: {stats['total_cases']}")
        print(f"  - Casos processados: {stats['processed_cases']}")
    except Exception as e:
        print(f"✗ PostgreSQL: {e}")
    
    # Verificar Celery
    try:
        i = app.control.inspect()
        stats = i.stats()
        if stats:
            print("✓ Celery Workers: OK")
            for worker, info in stats.items():
                print(f"  - {worker}: {info.get('total', {})}")
        else:
            print("✗ Celery Workers: Nenhum worker ativo")
    except Exception as e:
        print(f"✗ Celery: {e}")


# Adicionar comando worker ao CLI
cli.add_command(run_worker, name='worker')


if __name__ == '__main__':
    cli()