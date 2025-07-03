#!/usr/bin/env python3
"""
📋 SISTEMA DE AUDITORIA COMPLETO
Registra todas as ações, acessos e mudanças no sistema
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid
from contextlib import asynccontextmanager
import logging
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, Text, Integer, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import aioredis
from functools import wraps
import inspect
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base SQLAlchemy
Base = declarative_base()


class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    # Autenticação
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Acesso a dados
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DOWNLOAD = "data_download"
    
    # Modificações
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    
    # Sistema
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_ERROR = "system_error"
    
    # Segurança
    SECURITY_ALERT = "security_alert"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # API
    API_CALL = "api_call"
    API_ERROR = "api_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class AuditSeverity(Enum):
    """Severidade do evento"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Evento de auditoria"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    duration_ms: Optional[float] = None
    stack_trace: Optional[str] = None


class AuditLog(Base):
    """Modelo de log de auditoria"""
    __tablename__ = 'audit_logs_complete'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(100), unique=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Informações do usuário
    user_id = Column(String(100), index=True)
    user_name = Column(String(200))
    ip_address = Column(String(45), index=True)
    user_agent = Column(Text)
    session_id = Column(String(100), index=True)
    
    # Informações do recurso
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(200), index=True)
    action = Column(String(100), index=True)
    result = Column(String(50))
    
    # Detalhes
    error_message = Column(Text)
    metadata = Column(JSON)
    request_data = Column(JSON)
    response_data = Column(JSON)
    duration_ms = Column(Float)
    stack_trace = Column(Text)
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    data_hash = Column(String(64))  # Hash para integridade
    
    # Índices compostos
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_resource_timestamp', 'resource_type', 'resource_id', 'timestamp'),
        Index('idx_event_severity', 'event_type', 'severity'),
    )


class AuditStatistics(Base):
    """Estatísticas agregadas de auditoria"""
    __tablename__ = 'audit_statistics'
    
    id = Column(Integer, primary_key=True)
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    count = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    avg_duration_ms = Column(Float)
    error_count = Column(Integer, default=0)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditRetention(Base):
    """Configuração de retenção de logs"""
    __tablename__ = 'audit_retention'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), unique=True)
    retention_days = Column(Integer, nullable=False)
    archive_enabled = Column(Boolean, default=True)
    compress_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AuditService:
    """Serviço principal de auditoria"""
    
    def __init__(self, db_url: Optional[str] = None, redis_url: Optional[str] = None):
        # Configurar banco
        if not db_url:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///audit.db')
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Redis para cache e fila
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = None
        
        # Configurações
        self.batch_size = 100
        self.flush_interval = 5  # segundos
        self.event_buffer = []
        self.buffer_lock = asyncio.Lock()
        
        # Configurar retenção padrão
        self._setup_default_retention()
    
    async def initialize(self):
        """Inicializar conexões assíncronas"""
        self.redis = await aioredis.create_redis_pool(self.redis_url)
    
    async def close(self):
        """Fechar conexões"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
    
    def _setup_default_retention(self):
        """Configurar políticas de retenção padrão"""
        default_policies = [
            (AuditEventType.LOGIN.value, 365),
            (AuditEventType.LOGIN_FAILED.value, 90),
            (AuditEventType.DATA_ACCESS.value, 180),
            (AuditEventType.DATA_EXPORT.value, 730),
            (AuditEventType.CREATE.value, 365),
            (AuditEventType.UPDATE.value, 365),
            (AuditEventType.DELETE.value, 2555),  # 7 anos
            (AuditEventType.CONFIG_CHANGE.value, 730),
            (AuditEventType.PERMISSION_CHANGE.value, 1095),
            (AuditEventType.SECURITY_ALERT.value, 1095),
            (AuditEventType.API_CALL.value, 30),
        ]
        
        with self.SessionLocal() as session:
            for event_type, days in default_policies:
                existing = session.query(AuditRetention).filter(
                    AuditRetention.event_type == event_type
                ).first()
                
                if not existing:
                    retention = AuditRetention(
                        event_type=event_type,
                        retention_days=days
                    )
                    session.add(retention)
            
            session.commit()
    
    def create_event(self, event_type: AuditEventType, **kwargs) -> AuditEvent:
        """Criar evento de auditoria"""
        event_id = f"{event_type.value}_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"
        
        return AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            severity=kwargs.get('severity', AuditSeverity.INFO),
            **kwargs
        )
    
    async def log_event(self, event: AuditEvent):
        """Registrar evento de auditoria"""
        try:
            # Adicionar ao buffer
            async with self.buffer_lock:
                self.event_buffer.append(event)
                
                # Flush se necessário
                if len(self.event_buffer) >= self.batch_size:
                    await self._flush_buffer()
            
            # Publicar evento em tempo real se crítico
            if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                await self._publish_realtime_event(event)
            
        except Exception as e:
            logger.error(f"Erro ao registrar evento de auditoria: {e}")
    
    async def _flush_buffer(self):
        """Gravar buffer no banco"""
        if not self.event_buffer:
            return
        
        try:
            with self.SessionLocal() as session:
                for event in self.event_buffer:
                    # Calcular hash para integridade
                    event_dict = asdict(event)
                    event_json = json.dumps(event_dict, sort_keys=True, default=str)
                    data_hash = hashlib.sha256(event_json.encode()).hexdigest()
                    
                    # Criar registro
                    log = AuditLog(
                        event_id=event.event_id,
                        event_type=event.event_type.value,
                        severity=event.severity.value,
                        timestamp=event.timestamp,
                        user_id=event.user_id,
                        user_name=event.user_name,
                        ip_address=event.ip_address,
                        user_agent=event.user_agent,
                        session_id=event.session_id,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        action=event.action,
                        result=event.result,
                        error_message=event.error_message,
                        metadata=event.metadata,
                        request_data=event.request_data,
                        response_data=event.response_data,
                        duration_ms=event.duration_ms,
                        stack_trace=event.stack_trace,
                        data_hash=data_hash
                    )
                    session.add(log)
                
                session.commit()
            
            # Limpar buffer
            self.event_buffer.clear()
            
        except Exception as e:
            logger.error(f"Erro ao gravar buffer de auditoria: {e}")
    
    async def _publish_realtime_event(self, event: AuditEvent):
        """Publicar evento em tempo real via Redis"""
        if self.redis:
            try:
                channel = f"audit:{event.event_type.value}"
                event_json = json.dumps(asdict(event), default=str)
                await self.redis.publish(channel, event_json)
            except Exception as e:
                logger.error(f"Erro ao publicar evento em tempo real: {e}")
    
    def audit_decorator(self, event_type: AuditEventType, 
                       resource_type: Optional[str] = None):
        """Decorator para auditar funções automaticamente"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                event = None
                
                try:
                    # Extrair informações do contexto
                    context = kwargs.get('audit_context', {})
                    
                    # Executar função
                    result = await func(*args, **kwargs)
                    
                    # Criar evento de sucesso
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                    event = self.create_event(
                        event_type=event_type,
                        severity=AuditSeverity.INFO,
                        user_id=context.get('user_id'),
                        user_name=context.get('user_name'),
                        ip_address=context.get('ip_address'),
                        user_agent=context.get('user_agent'),
                        session_id=context.get('session_id'),
                        resource_type=resource_type or func.__name__,
                        action=func.__name__,
                        result='success',
                        duration_ms=duration,
                        metadata={
                            'function': func.__name__,
                            'module': func.__module__,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    # Criar evento de erro
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                    event = self.create_event(
                        event_type=event_type,
                        severity=AuditSeverity.ERROR,
                        user_id=context.get('user_id'),
                        user_name=context.get('user_name'),
                        ip_address=context.get('ip_address'),
                        user_agent=context.get('user_agent'),
                        session_id=context.get('session_id'),
                        resource_type=resource_type or func.__name__,
                        action=func.__name__,
                        result='error',
                        error_message=str(e),
                        duration_ms=duration,
                        stack_trace=traceback.format_exc(),
                        metadata={
                            'function': func.__name__,
                            'module': func.__module__,
                            'error_type': type(e).__name__
                        }
                    )
                    raise
                    
                finally:
                    # Registrar evento
                    if event:
                        asyncio.create_task(self.log_event(event))
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Versão síncrona similar
                start_time = datetime.utcnow()
                event = None
                
                try:
                    context = kwargs.get('audit_context', {})
                    result = func(*args, **kwargs)
                    
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                    event = self.create_event(
                        event_type=event_type,
                        severity=AuditSeverity.INFO,
                        user_id=context.get('user_id'),
                        resource_type=resource_type or func.__name__,
                        action=func.__name__,
                        result='success',
                        duration_ms=duration
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                    event = self.create_event(
                        event_type=event_type,
                        severity=AuditSeverity.ERROR,
                        resource_type=resource_type or func.__name__,
                        action=func.__name__,
                        result='error',
                        error_message=str(e),
                        duration_ms=duration
                    )
                    raise
                    
                finally:
                    if event:
                        # Usar thread para não bloquear
                        asyncio.run(self.log_event(event))
            
            # Retornar wrapper apropriado
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def search_logs(self, filters: Dict[str, Any], 
                         limit: int = 100, offset: int = 0) -> List[Dict]:
        """Pesquisar logs de auditoria"""
        try:
            with self.SessionLocal() as session:
                query = session.query(AuditLog)
                
                # Aplicar filtros
                if 'event_type' in filters:
                    query = query.filter(AuditLog.event_type == filters['event_type'])
                
                if 'user_id' in filters:
                    query = query.filter(AuditLog.user_id == filters['user_id'])
                
                if 'resource_type' in filters:
                    query = query.filter(AuditLog.resource_type == filters['resource_type'])
                
                if 'resource_id' in filters:
                    query = query.filter(AuditLog.resource_id == filters['resource_id'])
                
                if 'severity' in filters:
                    query = query.filter(AuditLog.severity == filters['severity'])
                
                if 'start_date' in filters:
                    query = query.filter(AuditLog.timestamp >= filters['start_date'])
                
                if 'end_date' in filters:
                    query = query.filter(AuditLog.timestamp <= filters['end_date'])
                
                if 'ip_address' in filters:
                    query = query.filter(AuditLog.ip_address == filters['ip_address'])
                
                # Ordenar e paginar
                logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
                
                # Converter para dict
                results = []
                for log in logs:
                    log_dict = {
                        'id': str(log.id),
                        'event_id': log.event_id,
                        'event_type': log.event_type,
                        'severity': log.severity,
                        'timestamp': log.timestamp.isoformat(),
                        'user_id': log.user_id,
                        'user_name': log.user_name,
                        'ip_address': log.ip_address,
                        'resource_type': log.resource_type,
                        'resource_id': log.resource_id,
                        'action': log.action,
                        'result': log.result,
                        'error_message': log.error_message,
                        'duration_ms': log.duration_ms,
                        'metadata': log.metadata
                    }
                    results.append(log_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Erro ao pesquisar logs: {e}")
            return []
    
    async def get_statistics(self, start_date: datetime, end_date: datetime,
                           group_by: str = 'event_type') -> Dict:
        """Obter estatísticas de auditoria"""
        try:
            with self.SessionLocal() as session:
                # Buscar ou calcular estatísticas
                stats = session.query(AuditStatistics).filter(
                    AuditStatistics.period_start >= start_date,
                    AuditStatistics.period_end <= end_date
                ).all()
                
                if not stats:
                    # Calcular estatísticas em tempo real
                    return await self._calculate_statistics(start_date, end_date, group_by)
                
                # Agregar estatísticas existentes
                result = {}
                for stat in stats:
                    key = stat.event_type
                    if key not in result:
                        result[key] = {
                            'count': 0,
                            'unique_users': set(),
                            'unique_ips': set(),
                            'total_duration': 0,
                            'error_count': 0
                        }
                    
                    result[key]['count'] += stat.count
                    result[key]['error_count'] += stat.error_count
                    
                return result
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    async def _calculate_statistics(self, start_date: datetime, end_date: datetime,
                                  group_by: str) -> Dict:
        """Calcular estatísticas em tempo real"""
        with self.SessionLocal() as session:
            logs = session.query(AuditLog).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).all()
            
            stats = {}
            for log in logs:
                key = getattr(log, group_by, 'unknown')
                if key not in stats:
                    stats[key] = {
                        'count': 0,
                        'unique_users': set(),
                        'unique_ips': set(),
                        'total_duration': 0,
                        'error_count': 0,
                        'events': []
                    }
                
                stats[key]['count'] += 1
                if log.user_id:
                    stats[key]['unique_users'].add(log.user_id)
                if log.ip_address:
                    stats[key]['unique_ips'].add(log.ip_address)
                if log.duration_ms:
                    stats[key]['total_duration'] += log.duration_ms
                if log.result == 'error':
                    stats[key]['error_count'] += 1
            
            # Converter sets para contagens
            for key in stats:
                stats[key]['unique_users'] = len(stats[key]['unique_users'])
                stats[key]['unique_ips'] = len(stats[key]['unique_ips'])
                if stats[key]['count'] > 0 and stats[key]['total_duration'] > 0:
                    stats[key]['avg_duration'] = stats[key]['total_duration'] / stats[key]['count']
                del stats[key]['events']
            
            return stats
    
    async def verify_integrity(self, event_id: str) -> bool:
        """Verificar integridade de um log"""
        try:
            with self.SessionLocal() as session:
                log = session.query(AuditLog).filter(
                    AuditLog.event_id == event_id
                ).first()
                
                if not log:
                    return False
                
                # Recalcular hash
                log_dict = {
                    'event_id': log.event_id,
                    'event_type': log.event_type,
                    'severity': log.severity,
                    'timestamp': log.timestamp.isoformat(),
                    'user_id': log.user_id,
                    'user_name': log.user_name,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'session_id': log.session_id,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'action': log.action,
                    'result': log.result,
                    'error_message': log.error_message,
                    'metadata': log.metadata,
                    'request_data': log.request_data,
                    'response_data': log.response_data,
                    'duration_ms': log.duration_ms,
                    'stack_trace': log.stack_trace
                }
                
                log_json = json.dumps(log_dict, sort_keys=True)
                calculated_hash = hashlib.sha256(log_json.encode()).hexdigest()
                
                return calculated_hash == log.data_hash
                
        except Exception as e:
            logger.error(f"Erro ao verificar integridade: {e}")
            return False
    
    async def cleanup_old_logs(self):
        """Limpar logs antigos baseado na política de retenção"""
        try:
            with self.SessionLocal() as session:
                # Obter políticas de retenção
                policies = session.query(AuditRetention).all()
                
                for policy in policies:
                    cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
                    
                    if policy.archive_enabled:
                        # Arquivar antes de deletar
                        await self._archive_logs(policy.event_type, cutoff_date)
                    
                    # Deletar logs antigos
                    deleted = session.query(AuditLog).filter(
                        AuditLog.event_type == policy.event_type,
                        AuditLog.timestamp < cutoff_date
                    ).delete()
                    
                    logger.info(f"Removidos {deleted} logs de {policy.event_type}")
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro na limpeza de logs: {e}")
    
    async def _archive_logs(self, event_type: str, cutoff_date: datetime):
        """Arquivar logs antes de deletar"""
        # Implementar arquivamento para S3, blob storage, etc
        logger.info(f"Arquivando logs de {event_type} anteriores a {cutoff_date}")
        # TODO: Implementar arquivamento real
    
    async def export_logs(self, filters: Dict[str, Any], format: str = 'json') -> str:
        """Exportar logs de auditoria"""
        logs = await self.search_logs(filters, limit=10000)
        
        if format == 'json':
            return json.dumps(logs, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Formato não suportado: {format}")


# Context manager para auditoria
@asynccontextmanager
async def audit_context(service: AuditService, user_info: Dict[str, Any]):
    """Context manager para adicionar contexto de auditoria"""
    context_data = {
        'user_id': user_info.get('user_id'),
        'user_name': user_info.get('user_name'),
        'ip_address': user_info.get('ip_address'),
        'user_agent': user_info.get('user_agent'),
        'session_id': user_info.get('session_id')
    }
    
    # Adicionar ao contexto local
    audit_context_var.set(context_data)
    
    try:
        yield context_data
    finally:
        # Limpar contexto
        audit_context_var.set(None)


# Variável de contexto para auditoria
import contextvars
audit_context_var = contextvars.ContextVar('audit_context', default=None)


# Worker para processar buffer periodicamente
async def audit_buffer_worker(service: AuditService):
    """Worker para processar buffer de auditoria"""
    while True:
        try:
            await asyncio.sleep(service.flush_interval)
            async with service.buffer_lock:
                await service._flush_buffer()
        except Exception as e:
            logger.error(f"Erro no worker de auditoria: {e}")


if __name__ == "__main__":
    # Exemplo de uso
    async def test_audit():
        service = AuditService()
        await service.initialize()
        
        # Criar evento manual
        event = service.create_event(
            event_type=AuditEventType.LOGIN,
            user_id="user123",
            user_name="João Silva",
            ip_address="192.168.1.100",
            metadata={
                'browser': 'Chrome',
                'os': 'Windows 10'
            }
        )
        
        await service.log_event(event)
        
        # Usar decorator
        @service.audit_decorator(AuditEventType.DATA_ACCESS, "processo")
        async def acessar_processo(processo_id: str, audit_context=None):
            print(f"Acessando processo {processo_id}")
            return {"id": processo_id, "status": "ativo"}
        
        # Executar com contexto
        user_info = {
            'user_id': 'user456',
            'user_name': 'Maria Santos',
            'ip_address': '192.168.1.101'
        }
        
        async with audit_context(service, user_info):
            result = await acessar_processo("PROC-001", audit_context=user_info)
            print(f"Resultado: {result}")
        
        # Aguardar flush
        await asyncio.sleep(1)
        async with service.buffer_lock:
            await service._flush_buffer()
        
        # Pesquisar logs
        logs = await service.search_logs({'user_id': 'user456'})
        print(f"Logs encontrados: {len(logs)}")
        
        # Estatísticas
        stats = await service.get_statistics(
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow()
        )
        print(f"Estatísticas: {stats}")
        
        await service.close()
    
    # Executar teste
    asyncio.run(test_audit())