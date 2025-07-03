#!/usr/bin/env python3
"""
🚨 SISTEMA DE REGRAS DE ALERTAS
Define regras automáticas para gerar alertas baseados em eventos
"""

import os
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import re

from .notification_service import (
    NotificationService, NotificationEvent, 
    NotificationType, NotificationPriority, NotificationChannel
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base SQLAlchemy
Base = declarative_base()


class AlertCondition(Enum):
    """Condições de alerta"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    RATE_EXCEEDED = "rate_exceeded"


class AlertCategory(Enum):
    """Categorias de alertas"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    BUSINESS = "business"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    PROCESS = "process"


@dataclass
class AlertRule:
    """Regra de alerta"""
    id: str
    name: str
    description: str
    category: AlertCategory
    enabled: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    cooldown_minutes: int = 60
    last_triggered: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertRuleDB(Base):
    """Regra de alerta no banco"""
    __tablename__ = 'alert_rules'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    category = Column(String(50))
    enabled = Column(Boolean, default=True)
    conditions = Column(JSON)
    actions = Column(JSON)
    priority = Column(Integer, default=2)
    cooldown_minutes = Column(Integer, default=60)
    last_triggered = Column(DateTime, nullable=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AlertHistory(Base):
    """Histórico de alertas disparados"""
    __tablename__ = 'alert_history'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(50), index=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    event_data = Column(JSON)
    matched_conditions = Column(JSON)
    actions_taken = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(String(500), nullable=True)


class AlertMetrics(Base):
    """Métricas para alertas baseados em threshold"""
    __tablename__ = 'alert_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON)


class AlertEngine:
    """Motor de processamento de alertas"""
    
    def __init__(self, db_url: Optional[str] = None):
        # Configurar banco
        if not db_url:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///alerts.db')
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Serviço de notificações
        self.notification_service = NotificationService(db_url)
        
        # Cache de regras
        self.rules_cache: Dict[str, AlertRule] = {}
        self._load_rules()
        
        # Condições customizadas
        self.custom_conditions: Dict[str, Callable] = {}
        
        # Ações customizadas
        self.custom_actions: Dict[str, Callable] = {}
        
        # Inicializar regras padrão
        self._initialize_default_rules()
    
    def _load_rules(self):
        """Carregar regras do banco"""
        try:
            with self.SessionLocal() as session:
                db_rules = session.query(AlertRuleDB).filter(
                    AlertRuleDB.enabled == True
                ).all()
                
                self.rules_cache.clear()
                for db_rule in db_rules:
                    rule = AlertRule(
                        id=db_rule.id,
                        name=db_rule.name,
                        description=db_rule.description,
                        category=AlertCategory(db_rule.category),
                        enabled=db_rule.enabled,
                        conditions=db_rule.conditions or [],
                        actions=db_rule.actions or [],
                        priority=NotificationPriority(db_rule.priority),
                        cooldown_minutes=db_rule.cooldown_minutes,
                        last_triggered=db_rule.last_triggered,
                        metadata=db_rule.metadata or {}
                    )
                    self.rules_cache[rule.id] = rule
                    
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {e}")
    
    def _initialize_default_rules(self):
        """Inicializar regras padrão"""
        default_rules = [
            # Segurança
            AlertRule(
                id="security_failed_login",
                name="Múltiplas tentativas de login falhas",
                description="Alerta quando há muitas tentativas de login falhas",
                category=AlertCategory.SECURITY,
                conditions=[
                    {
                        "field": "event_type",
                        "condition": AlertCondition.EQUALS.value,
                        "value": "login_failed"
                    },
                    {
                        "field": "count",
                        "condition": AlertCondition.THRESHOLD_EXCEEDED.value,
                        "value": 5,
                        "window_minutes": 5
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["email", "slack"],
                        "template": "security_alert"
                    },
                    {
                        "type": "block_ip",
                        "duration_minutes": 30
                    }
                ],
                priority=NotificationPriority.HIGH
            ),
            
            # Performance
            AlertRule(
                id="performance_slow_query",
                name="Query lenta detectada",
                description="Alerta quando queries demoram muito",
                category=AlertCategory.PERFORMANCE,
                conditions=[
                    {
                        "field": "query_time",
                        "condition": AlertCondition.GREATER_THAN.value,
                        "value": 5000  # 5 segundos
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["slack"]
                    },
                    {
                        "type": "log_query"
                    }
                ],
                priority=NotificationPriority.MEDIUM
            ),
            
            # Erro
            AlertRule(
                id="error_rate_high",
                name="Taxa de erro alta",
                description="Alerta quando a taxa de erro está alta",
                category=AlertCategory.ERROR,
                conditions=[
                    {
                        "field": "error_rate",
                        "condition": AlertCondition.RATE_EXCEEDED.value,
                        "value": 0.05,  # 5%
                        "window_minutes": 10
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["email", "slack", "sms"],
                        "priority": "urgent"
                    }
                ],
                priority=NotificationPriority.URGENT
            ),
            
            # Business
            AlertRule(
                id="business_new_process",
                name="Novo processo importante",
                description="Alerta quando processo de alto valor é criado",
                category=AlertCategory.BUSINESS,
                conditions=[
                    {
                        "field": "event_type",
                        "condition": AlertCondition.EQUALS.value,
                        "value": "processo_criado"
                    },
                    {
                        "field": "valor_causa",
                        "condition": AlertCondition.GREATER_THAN.value,
                        "value": 1000000  # R$ 1 milhão
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["email"],
                        "recipients": ["diretoria@empresa.com"]
                    }
                ],
                priority=NotificationPriority.HIGH
            ),
            
            # Sistema
            AlertRule(
                id="system_disk_space",
                name="Espaço em disco baixo",
                description="Alerta quando espaço em disco está acabando",
                category=AlertCategory.SYSTEM,
                conditions=[
                    {
                        "field": "disk_usage_percent",
                        "condition": AlertCondition.GREATER_THAN.value,
                        "value": 90
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["email", "slack"]
                    },
                    {
                        "type": "cleanup_old_files"
                    }
                ],
                priority=NotificationPriority.HIGH,
                cooldown_minutes=120
            ),
            
            # Compliance
            AlertRule(
                id="compliance_data_retention",
                name="Dados próximos do limite de retenção",
                description="Alerta sobre dados que precisam ser arquivados",
                category=AlertCategory.COMPLIANCE,
                conditions=[
                    {
                        "field": "days_until_retention_limit",
                        "condition": AlertCondition.LESS_THAN.value,
                        "value": 30
                    }
                ],
                actions=[
                    {
                        "type": "notification",
                        "channels": ["email"]
                    },
                    {
                        "type": "schedule_archival"
                    }
                ],
                priority=NotificationPriority.MEDIUM
            )
        ]
        
        # Salvar regras padrão se não existirem
        with self.SessionLocal() as session:
            for rule in default_rules:
                existing = session.query(AlertRuleDB).filter(
                    AlertRuleDB.id == rule.id
                ).first()
                
                if not existing:
                    db_rule = AlertRuleDB(
                        id=rule.id,
                        name=rule.name,
                        description=rule.description,
                        category=rule.category.value,
                        enabled=rule.enabled,
                        conditions=rule.conditions,
                        actions=rule.actions,
                        priority=rule.priority.value,
                        cooldown_minutes=rule.cooldown_minutes,
                        metadata=rule.metadata
                    )
                    session.add(db_rule)
            
            session.commit()
        
        # Recarregar cache
        self._load_rules()
    
    async def process_event(self, event_data: Dict[str, Any]) -> List[str]:
        """Processar evento e verificar regras"""
        triggered_rules = []
        
        for rule_id, rule in self.rules_cache.items():
            if not rule.enabled:
                continue
            
            # Verificar cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            # Verificar condições
            if await self._check_conditions(rule, event_data):
                # Executar ações
                await self._execute_actions(rule, event_data)
                
                # Atualizar última vez disparada
                self._update_last_triggered(rule.id)
                
                # Registrar no histórico
                self._log_alert_history(rule, event_data)
                
                triggered_rules.append(rule.id)
        
        return triggered_rules
    
    async def _check_conditions(self, rule: AlertRule, event_data: Dict[str, Any]) -> bool:
        """Verificar se todas as condições são atendidas"""
        try:
            for condition in rule.conditions:
                field = condition.get('field')
                cond_type = AlertCondition(condition.get('condition'))
                expected_value = condition.get('value')
                
                # Obter valor do campo
                actual_value = self._get_field_value(event_data, field)
                
                # Verificar condição especial de threshold
                if cond_type == AlertCondition.THRESHOLD_EXCEEDED:
                    window = condition.get('window_minutes', 5)
                    if not await self._check_threshold(field, expected_value, window):
                        return False
                
                # Verificar condição especial de rate
                elif cond_type == AlertCondition.RATE_EXCEEDED:
                    window = condition.get('window_minutes', 5)
                    if not await self._check_rate(field, expected_value, window):
                        return False
                
                # Verificar condições normais
                else:
                    if not self._evaluate_condition(actual_value, cond_type, expected_value):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar condições: {e}")
            return False
    
    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Obter valor de campo (suporta notação de ponto)"""
        parts = field.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _evaluate_condition(self, actual_value: Any, condition: AlertCondition, 
                          expected_value: Any) -> bool:
        """Avaliar condição"""
        try:
            if condition == AlertCondition.EQUALS:
                return actual_value == expected_value
            
            elif condition == AlertCondition.NOT_EQUALS:
                return actual_value != expected_value
            
            elif condition == AlertCondition.GREATER_THAN:
                return float(actual_value) > float(expected_value)
            
            elif condition == AlertCondition.LESS_THAN:
                return float(actual_value) < float(expected_value)
            
            elif condition == AlertCondition.CONTAINS:
                return expected_value in str(actual_value)
            
            elif condition == AlertCondition.NOT_CONTAINS:
                return expected_value not in str(actual_value)
            
            elif condition == AlertCondition.REGEX:
                return bool(re.match(expected_value, str(actual_value)))
            
            elif condition == AlertCondition.IN:
                return actual_value in expected_value
            
            elif condition == AlertCondition.NOT_IN:
                return actual_value not in expected_value
            
            else:
                return False
                
        except Exception as e:
            logger.error(f"Erro ao avaliar condição: {e}")
            return False
    
    async def _check_threshold(self, field: str, threshold: float, 
                             window_minutes: int) -> bool:
        """Verificar se threshold foi excedido"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)
            
            with self.SessionLocal() as session:
                # Contar eventos no período
                if field == "count":
                    # Contar eventos genéricos
                    count = session.query(AlertHistory).filter(
                        AlertHistory.triggered_at >= since
                    ).count()
                    return count > threshold
                else:
                    # Verificar métricas
                    metrics = session.query(AlertMetrics).filter(
                        AlertMetrics.metric_name == field,
                        AlertMetrics.timestamp >= since
                    ).all()
                    
                    if metrics:
                        avg_value = sum(m.metric_value for m in metrics) / len(metrics)
                        return avg_value > threshold
                    
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao verificar threshold: {e}")
            return False
    
    async def _check_rate(self, field: str, max_rate: float, 
                        window_minutes: int) -> bool:
        """Verificar se taxa foi excedida"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)
            
            with self.SessionLocal() as session:
                # Calcular taxa
                if field == "error_rate":
                    # Contar erros vs total
                    total = session.query(AlertHistory).filter(
                        AlertHistory.triggered_at >= since
                    ).count()
                    
                    errors = session.query(AlertHistory).filter(
                        AlertHistory.triggered_at >= since,
                        AlertHistory.success == False
                    ).count()
                    
                    if total > 0:
                        rate = errors / total
                        return rate > max_rate
                    
                    return False
                else:
                    # Taxa genérica baseada em métricas
                    metrics = session.query(AlertMetrics).filter(
                        AlertMetrics.metric_name == field,
                        AlertMetrics.timestamp >= since
                    ).all()
                    
                    if len(metrics) >= 2:
                        # Calcular taxa de mudança
                        first_value = metrics[0].metric_value
                        last_value = metrics[-1].metric_value
                        
                        if first_value > 0:
                            rate = (last_value - first_value) / first_value
                            return abs(rate) > max_rate
                    
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao verificar taxa: {e}")
            return False
    
    async def _execute_actions(self, rule: AlertRule, event_data: Dict[str, Any]):
        """Executar ações da regra"""
        for action in rule.actions:
            action_type = action.get('type')
            
            try:
                if action_type == 'notification':
                    await self._action_notification(rule, action, event_data)
                
                elif action_type == 'block_ip':
                    await self._action_block_ip(action, event_data)
                
                elif action_type == 'log_query':
                    await self._action_log_query(action, event_data)
                
                elif action_type == 'cleanup_old_files':
                    await self._action_cleanup_files(action, event_data)
                
                elif action_type == 'schedule_archival':
                    await self._action_schedule_archival(action, event_data)
                
                elif action_type in self.custom_actions:
                    # Executar ação customizada
                    await self.custom_actions[action_type](rule, action, event_data)
                
                else:
                    logger.warning(f"Ação desconhecida: {action_type}")
                    
            except Exception as e:
                logger.error(f"Erro ao executar ação {action_type}: {e}")
    
    async def _action_notification(self, rule: AlertRule, action: Dict, 
                                 event_data: Dict[str, Any]):
        """Ação: enviar notificação"""
        # Determinar canais
        channels = action.get('channels', [])
        if channels:
            channels = [NotificationChannel(c) for c in channels]
        else:
            channels = None
        
        # Criar evento de notificação
        notification = self.notification_service.create_event(
            type=NotificationType.WARNING if rule.category == AlertCategory.SECURITY 
                 else NotificationType.INFO,
            title=f"Alerta: {rule.name}",
            message=rule.description,
            priority=rule.priority,
            channels=channels,
            recipient=action.get('recipients', [None])[0],
            template=action.get('template'),
            metadata={
                'rule_id': rule.id,
                'category': rule.category.value,
                'event_data': event_data,
                'triggered_at': datetime.utcnow().isoformat()
            }
        )
        
        # Enviar
        await self.notification_service.send_notification(notification)
    
    async def _action_block_ip(self, action: Dict, event_data: Dict[str, Any]):
        """Ação: bloquear IP"""
        ip = event_data.get('ip_address')
        duration = action.get('duration_minutes', 30)
        
        if ip:
            # Implementar bloqueio de IP (exemplo)
            logger.info(f"Bloqueando IP {ip} por {duration} minutos")
            # TODO: Implementar bloqueio real via firewall/nginx/etc
    
    async def _action_log_query(self, action: Dict, event_data: Dict[str, Any]):
        """Ação: registrar query lenta"""
        query = event_data.get('query')
        query_time = event_data.get('query_time')
        
        if query:
            logger.warning(f"Query lenta ({query_time}ms): {query[:200]}...")
            # TODO: Salvar em tabela específica de queries lentas
    
    async def _action_cleanup_files(self, action: Dict, event_data: Dict[str, Any]):
        """Ação: limpar arquivos antigos"""
        logger.info("Iniciando limpeza de arquivos antigos")
        # TODO: Implementar limpeza real de arquivos temporários/logs antigos
    
    async def _action_schedule_archival(self, action: Dict, event_data: Dict[str, Any]):
        """Ação: agendar arquivamento"""
        logger.info("Agendando arquivamento de dados")
        # TODO: Implementar agendamento de arquivamento
    
    def _update_last_triggered(self, rule_id: str):
        """Atualizar última vez que regra foi disparada"""
        try:
            with self.SessionLocal() as session:
                rule = session.query(AlertRuleDB).filter(
                    AlertRuleDB.id == rule_id
                ).first()
                
                if rule:
                    rule.last_triggered = datetime.utcnow()
                    session.commit()
                    
                    # Atualizar cache
                    if rule_id in self.rules_cache:
                        self.rules_cache[rule_id].last_triggered = rule.last_triggered
                        
        except Exception as e:
            logger.error(f"Erro ao atualizar last_triggered: {e}")
    
    def _log_alert_history(self, rule: AlertRule, event_data: Dict[str, Any]):
        """Registrar alerta no histórico"""
        try:
            with self.SessionLocal() as session:
                history = AlertHistory(
                    rule_id=rule.id,
                    event_data=event_data,
                    matched_conditions=rule.conditions,
                    actions_taken=rule.actions,
                    success=True
                )
                session.add(history)
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao registrar histórico: {e}")
    
    def add_metric(self, metric_name: str, metric_value: float, 
                  tags: Optional[Dict] = None):
        """Adicionar métrica para alertas baseados em threshold"""
        try:
            with self.SessionLocal() as session:
                metric = AlertMetrics(
                    metric_name=metric_name,
                    metric_value=metric_value,
                    tags=tags or {}
                )
                session.add(metric)
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao adicionar métrica: {e}")
    
    def register_custom_condition(self, name: str, func: Callable):
        """Registrar condição customizada"""
        self.custom_conditions[name] = func
    
    def register_custom_action(self, name: str, func: Callable):
        """Registrar ação customizada"""
        self.custom_actions[name] = func
    
    def add_rule(self, rule: AlertRule) -> bool:
        """Adicionar nova regra"""
        try:
            with self.SessionLocal() as session:
                db_rule = AlertRuleDB(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    category=rule.category.value,
                    enabled=rule.enabled,
                    conditions=rule.conditions,
                    actions=rule.actions,
                    priority=rule.priority.value,
                    cooldown_minutes=rule.cooldown_minutes,
                    metadata=rule.metadata
                )
                session.add(db_rule)
                session.commit()
            
            # Recarregar cache
            self._load_rules()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar regra: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Atualizar regra existente"""
        try:
            with self.SessionLocal() as session:
                rule = session.query(AlertRuleDB).filter(
                    AlertRuleDB.id == rule_id
                ).first()
                
                if rule:
                    for key, value in updates.items():
                        if hasattr(rule, key):
                            setattr(rule, key, value)
                    
                    rule.updated_at = datetime.utcnow()
                    session.commit()
                    
                    # Recarregar cache
                    self._load_rules()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar regra: {e}")
            return False
    
    def get_alert_stats(self, days: int = 7) -> Dict:
        """Obter estatísticas de alertas"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            with self.SessionLocal() as session:
                history = session.query(AlertHistory).filter(
                    AlertHistory.triggered_at >= since
                ).all()
                
                stats = {
                    'total_alerts': len(history),
                    'by_rule': {},
                    'by_hour': {},
                    'success_rate': 0
                }
                
                success_count = 0
                
                for alert in history:
                    # Por regra
                    if alert.rule_id not in stats['by_rule']:
                        stats['by_rule'][alert.rule_id] = 0
                    stats['by_rule'][alert.rule_id] += 1
                    
                    # Por hora
                    hour = alert.triggered_at.hour
                    if hour not in stats['by_hour']:
                        stats['by_hour'][hour] = 0
                    stats['by_hour'][hour] += 1
                    
                    # Taxa de sucesso
                    if alert.success:
                        success_count += 1
                
                if stats['total_alerts'] > 0:
                    stats['success_rate'] = success_count / stats['total_alerts']
                
                return stats
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}


# Worker de processamento
async def alert_processor(engine: AlertEngine, event_queue: asyncio.Queue):
    """Processar eventos da fila"""
    while True:
        try:
            # Obter evento da fila
            event_data = await event_queue.get()
            
            # Processar
            triggered_rules = await engine.process_event(event_data)
            
            if triggered_rules:
                logger.info(f"Regras disparadas: {triggered_rules}")
            
        except Exception as e:
            logger.error(f"Erro no processador de alertas: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    # Exemplo de uso
    async def test_alerts():
        engine = AlertEngine()
        
        # Adicionar métrica
        engine.add_metric("disk_usage_percent", 92.5)
        
        # Simular evento
        event = {
            "event_type": "login_failed",
            "ip_address": "192.168.1.100",
            "username": "admin",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Processar
        triggered = await engine.process_event(event)
        print(f"Alertas disparados: {triggered}")
        
        # Estatísticas
        stats = engine.get_alert_stats()
        print(f"Estatísticas: {stats}")
    
    # Executar teste
    asyncio.run(test_alerts())