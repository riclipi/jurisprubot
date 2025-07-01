"""
Configuração centralizada de logging
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Formatter para logs em JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata log record em JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process': record.process,
            'thread': record.thread,
            'service': os.getenv('SERVICE_NAME', 'jurisprudencia-api'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': os.getenv('APP_VERSION', '1.0.0')
        }
        
        # Adicionar informações de exceção se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Adicionar campos extras
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Adicionar contexto de request se disponível
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Filtro para adicionar contexto aos logs"""
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Adiciona contexto ao log record"""
        # Adicionar contexto global
        for key, value in self.context.items():
            setattr(record, key, value)
        
        return True
    
    def set_context(self, **kwargs):
        """Define contexto global"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Limpa contexto global"""
        self.context.clear()


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_json: bool = True
) -> logging.Logger:
    """
    Configura sistema de logging
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para arquivo de log
        max_file_size: Tamanho máximo do arquivo de log
        backup_count: Número de arquivos de backup
        use_json: Se deve usar formato JSON
    
    Returns:
        Logger configurado
    """
    
    # Converter nível para constante
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Limpar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configurar formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo se especificado
    if log_file:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Adicionar filtro de contexto
    context_filter = ContextFilter()
    root_logger.addFilter(context_filter)
    
    # Configurar loggers específicos
    configure_specific_loggers(numeric_level)
    
    return root_logger


def configure_specific_loggers(level: int):
    """Configura loggers específicos"""
    
    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    
    # Configurar loggers da aplicação
    app_loggers = [
        'src.api',
        'src.scraper',
        'src.processing',
        'src.database',
        'src.rag',
        'src.pipeline',
        'src.auth'
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger com nome específico
    
    Args:
        name: Nome do logger
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """
    Faz log com contexto adicional
    
    Args:
        logger: Logger instance
        level: Nível do log
        message: Mensagem
        **context: Contexto adicional
    """
    
    # Criar record com contexto
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Adicionar contexto
    record.extra_fields = context
    
    # Fazer log
    logger.handle(record)


class RequestLogger:
    """Logger para requests HTTP"""
    
    def __init__(self, logger_name: str = 'src.api.requests'):
        self.logger = get_logger(logger_name)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: str = None,
        request_id: str = None,
        **extra
    ):
        """Log de request HTTP"""
        
        context = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration * 1000,
            'request_id': request_id,
            'user_id': user_id,
            **extra
        }
        
        level = 'ERROR' if status_code >= 500 else 'WARNING' if status_code >= 400 else 'INFO'
        message = f"{method} {path} - {status_code} ({duration:.2f}s)"
        
        log_with_context(self.logger, level, message, **context)


class TaskLogger:
    """Logger para tarefas Celery"""
    
    def __init__(self, logger_name: str = 'src.pipeline.tasks'):
        self.logger = get_logger(logger_name)
    
    def log_task_start(self, task_name: str, task_id: str, **context):
        """Log início de tarefa"""
        message = f"Task {task_name} started"
        log_with_context(
            self.logger, 'INFO', message,
            task_name=task_name,
            task_id=task_id,
            **context
        )
    
    def log_task_success(self, task_name: str, task_id: str, duration: float, **context):
        """Log sucesso de tarefa"""
        message = f"Task {task_name} completed successfully ({duration:.2f}s)"
        log_with_context(
            self.logger, 'INFO', message,
            task_name=task_name,
            task_id=task_id,
            duration=duration,
            **context
        )
    
    def log_task_failure(self, task_name: str, task_id: str, error: str, **context):
        """Log falha de tarefa"""
        message = f"Task {task_name} failed: {error}"
        log_with_context(
            self.logger, 'ERROR', message,
            task_name=task_name,
            task_id=task_id,
            error=error,
            **context
        )


# Instâncias globais
request_logger = RequestLogger()
task_logger = TaskLogger()

# Configuração padrão baseada em variáveis de ambiente
def setup_default_logging():
    """Configura logging padrão baseado em variáveis de ambiente"""
    
    level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', './logs/app.log')
    use_json = os.getenv('LOG_FORMAT', 'json').lower() == 'json'
    
    return setup_logging(
        level=level,
        log_file=log_file,
        use_json=use_json
    )