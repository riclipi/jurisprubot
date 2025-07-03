#!/usr/bin/env python3
"""
📊 MONITOR DE SAÚDE CONTÍNUO
Monitora continuamente a saúde do sistema e envia alertas
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging
from collections import deque
import statistics

from .health_check import (
    HealthCheckService,
    HealthStatus,
    SystemHealth,
    create_health_service
)
from ..notifications import NotificationService, NotificationEvent, NotificationType, NotificationPriority

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HealthMetric:
    """Métrica de saúde com timestamp"""
    timestamp: datetime
    status: HealthStatus
    response_time_ms: float
    details: Dict[str, Any]


@dataclass
class HealthTrend:
    """Tendência de saúde"""
    component: str
    period: str
    average_response_time: float
    availability_percent: float
    status_changes: int
    last_failure: Optional[datetime]
    trend: str  # improving, stable, degrading


class HealthMonitor:
    """Monitor contínuo de saúde do sistema"""
    
    def __init__(self, health_service: HealthCheckService, 
                 notification_service: Optional[NotificationService] = None):
        self.health_service = health_service
        self.notification_service = notification_service
        
        # Configurações
        self.check_interval = 60  # segundos
        self.history_size = 1440  # 24 horas com checks de 1 minuto
        self.alert_threshold = 3  # alertar após 3 falhas consecutivas
        
        # Histórico de métricas
        self.metrics_history: Dict[str, deque] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self.consecutive_failures: Dict[str, int] = {}
        
        # Estado
        self.is_running = False
        self.monitor_task = None
    
    async def start(self):
        """Iniciar monitoramento"""
        if self.is_running:
            logger.warning("Monitor já está em execução")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Monitor de saúde iniciado")
    
    async def stop(self):
        """Parar monitoramento"""
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitor de saúde parado")
    
    async def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.is_running:
            try:
                # Executar verificação
                await self._perform_check()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_check(self):
        """Executar verificação de saúde"""
        # Obter status atual
        health = await self.health_service.check_health(use_cache=False)
        
        # Processar cada componente
        for component in health.components:
            # Criar métrica
            metric = HealthMetric(
                timestamp=datetime.utcnow(),
                status=component.status,
                response_time_ms=component.response_time_ms,
                details=component.details
            )
            
            # Adicionar ao histórico
            if component.component not in self.metrics_history:
                self.metrics_history[component.component] = deque(maxlen=self.history_size)
            
            self.metrics_history[component.component].append(metric)
            
            # Verificar alertas
            await self._check_alerts(component.component, component.status)
        
        # Verificar tendências
        if len(list(self.metrics_history.values())[0]) > 60:  # Após 1 hora de dados
            trends = self.analyze_trends()
            await self._check_trend_alerts(trends)
    
    async def _check_alerts(self, component: str, status: HealthStatus):
        """Verificar se deve enviar alertas"""
        # Atualizar contador de falhas
        if status in [HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]:
            self.consecutive_failures[component] = self.consecutive_failures.get(component, 0) + 1
        else:
            self.consecutive_failures[component] = 0
        
        # Verificar threshold
        if self.consecutive_failures[component] >= self.alert_threshold:
            # Verificar cooldown de alerta (1 hora)
            last_alert = self.last_alert_time.get(component)
            if not last_alert or datetime.utcnow() - last_alert > timedelta(hours=1):
                await self._send_alert(component, status)
                self.last_alert_time[component] = datetime.utcnow()
    
    async def _send_alert(self, component: str, status: HealthStatus):
        """Enviar alerta de saúde"""
        if not self.notification_service:
            logger.warning(f"Alerta não enviado (sem serviço de notificação): {component} - {status}")
            return
        
        # Determinar severidade
        if status == HealthStatus.UNHEALTHY:
            notification_type = NotificationType.ERROR
            priority = NotificationPriority.HIGH
        else:
            notification_type = NotificationType.WARNING
            priority = NotificationPriority.MEDIUM
        
        # Obter detalhes recentes
        recent_metrics = list(self.metrics_history.get(component, []))[-5:]
        details = {
            'component': component,
            'current_status': status.value,
            'consecutive_failures': self.consecutive_failures[component],
            'recent_response_times': [m.response_time_ms for m in recent_metrics],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Criar notificação
        event = self.notification_service.create_event(
            type=notification_type,
            title=f"Health Alert: {component}",
            message=f"Component {component} is {status.value}. "
                   f"Failed {self.consecutive_failures[component]} consecutive checks.",
            priority=priority,
            metadata=details
        )
        
        # Enviar
        await self.notification_service.send_notification(event)
        logger.info(f"Alerta enviado para {component}: {status.value}")
    
    async def _check_trend_alerts(self, trends: List[HealthTrend]):
        """Verificar alertas baseados em tendências"""
        for trend in trends:
            # Alertar se tendência está degradando
            if trend.trend == 'degrading' and trend.availability_percent < 95:
                await self._send_trend_alert(trend)
    
    async def _send_trend_alert(self, trend: HealthTrend):
        """Enviar alerta de tendência"""
        if not self.notification_service:
            return
        
        # Verificar cooldown (1 alerta por dia)
        alert_key = f"trend_{trend.component}"
        last_alert = self.last_alert_time.get(alert_key)
        if last_alert and datetime.utcnow() - last_alert < timedelta(days=1):
            return
        
        event = self.notification_service.create_event(
            type=NotificationType.WARNING,
            title=f"Health Trend Alert: {trend.component}",
            message=f"Component {trend.component} showing degrading trend. "
                   f"Availability: {trend.availability_percent:.1f}%, "
                   f"Avg response time: {trend.average_response_time:.0f}ms",
            priority=NotificationPriority.MEDIUM,
            metadata={
                'component': trend.component,
                'trend': trend.trend,
                'availability_percent': trend.availability_percent,
                'average_response_time': trend.average_response_time,
                'status_changes': trend.status_changes,
                'period': trend.period
            }
        )
        
        await self.notification_service.send_notification(event)
        self.last_alert_time[alert_key] = datetime.utcnow()
    
    def analyze_trends(self, period_hours: int = 24) -> List[HealthTrend]:
        """Analisar tendências de saúde"""
        trends = []
        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)
        
        for component, metrics in self.metrics_history.items():
            # Filtrar métricas do período
            period_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            if not period_metrics:
                continue
            
            # Calcular estatísticas
            response_times = [m.response_time_ms for m in period_metrics]
            avg_response_time = statistics.mean(response_times)
            
            # Disponibilidade
            healthy_count = sum(1 for m in period_metrics 
                              if m.status == HealthStatus.HEALTHY)
            availability = (healthy_count / len(period_metrics)) * 100
            
            # Mudanças de status
            status_changes = 0
            last_status = None
            for metric in period_metrics:
                if last_status and metric.status != last_status:
                    status_changes += 1
                last_status = metric.status
            
            # Última falha
            failures = [m for m in period_metrics 
                       if m.status != HealthStatus.HEALTHY]
            last_failure = failures[-1].timestamp if failures else None
            
            # Determinar tendência
            trend_direction = self._calculate_trend(period_metrics)
            
            trends.append(HealthTrend(
                component=component,
                period=f"{period_hours}h",
                average_response_time=avg_response_time,
                availability_percent=availability,
                status_changes=status_changes,
                last_failure=last_failure,
                trend=trend_direction
            ))
        
        return trends
    
    def _calculate_trend(self, metrics: List[HealthMetric]) -> str:
        """Calcular direção da tendência"""
        if len(metrics) < 10:
            return 'stable'
        
        # Dividir em duas metades
        mid = len(metrics) // 2
        first_half = metrics[:mid]
        second_half = metrics[mid:]
        
        # Calcular médias de tempo de resposta
        first_avg = statistics.mean(m.response_time_ms for m in first_half)
        second_avg = statistics.mean(m.response_time_ms for m in second_half)
        
        # Calcular disponibilidade
        first_avail = sum(1 for m in first_half if m.status == HealthStatus.HEALTHY) / len(first_half)
        second_avail = sum(1 for m in second_half if m.status == HealthStatus.HEALTHY) / len(second_half)
        
        # Determinar tendência
        if second_avg > first_avg * 1.2 or second_avail < first_avail * 0.9:
            return 'degrading'
        elif second_avg < first_avg * 0.8 and second_avail > first_avail * 1.1:
            return 'improving'
        else:
            return 'stable'
    
    def get_component_summary(self, component: str) -> Optional[Dict[str, Any]]:
        """Obter resumo de um componente"""
        if component not in self.metrics_history:
            return None
        
        metrics = list(self.metrics_history[component])
        if not metrics:
            return None
        
        # Últimas 24 horas
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not recent_metrics:
            return None
        
        # Estatísticas
        response_times = [m.response_time_ms for m in recent_metrics]
        statuses = [m.status for m in recent_metrics]
        
        return {
            'component': component,
            'current_status': recent_metrics[-1].status.value,
            'metrics_count': len(recent_metrics),
            'response_time': {
                'current': recent_metrics[-1].response_time_ms,
                'average': statistics.mean(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'p95': sorted(response_times)[int(len(response_times) * 0.95)]
            },
            'availability': {
                'percent': (statuses.count(HealthStatus.HEALTHY) / len(statuses)) * 100,
                'uptime_seconds': self._calculate_uptime(recent_metrics),
                'downtime_seconds': self._calculate_downtime(recent_metrics)
            },
            'last_check': recent_metrics[-1].timestamp.isoformat(),
            'consecutive_failures': self.consecutive_failures.get(component, 0)
        }
    
    def _calculate_uptime(self, metrics: List[HealthMetric]) -> float:
        """Calcular tempo de uptime em segundos"""
        if not metrics:
            return 0
        
        uptime = 0
        last_time = metrics[0].timestamp
        last_status = metrics[0].status
        
        for metric in metrics[1:]:
            if last_status == HealthStatus.HEALTHY:
                uptime += (metric.timestamp - last_time).total_seconds()
            
            last_time = metric.timestamp
            last_status = metric.status
        
        # Adicionar tempo final se healthy
        if last_status == HealthStatus.HEALTHY:
            uptime += (datetime.utcnow() - last_time).total_seconds()
        
        return uptime
    
    def _calculate_downtime(self, metrics: List[HealthMetric]) -> float:
        """Calcular tempo de downtime em segundos"""
        if not metrics:
            return 0
        
        total_time = (datetime.utcnow() - metrics[0].timestamp).total_seconds()
        uptime = self._calculate_uptime(metrics)
        
        return total_time - uptime
    
    def export_metrics(self, format: str = 'json') -> str:
        """Exportar métricas históricas"""
        data = {
            'export_time': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        for component, metrics in self.metrics_history.items():
            data['components'][component] = {
                'metrics': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'status': m.status.value,
                        'response_time_ms': m.response_time_ms
                    }
                    for m in metrics
                ],
                'summary': self.get_component_summary(component)
            }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Formato não suportado: {format}")


# Função para criar e iniciar monitor
async def create_health_monitor(config: Dict[str, Any]) -> HealthMonitor:
    """Criar e configurar monitor de saúde"""
    # Criar serviços
    health_service = create_health_service(config)
    
    notification_service = None
    if config.get('enable_notifications', True):
        notification_service = NotificationService()
        await notification_service.initialize()
    
    # Criar monitor
    monitor = HealthMonitor(health_service, notification_service)
    
    # Configurar
    monitor.check_interval = config.get('check_interval', 60)
    monitor.alert_threshold = config.get('alert_threshold', 3)
    
    return monitor


if __name__ == "__main__":
    # Exemplo de uso
    async def test_monitor():
        config = {
            'database_url': os.getenv('DATABASE_URL', 'postgresql://localhost/test'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'check_interval': 10,  # 10 segundos para teste
            'alert_threshold': 2,
            'enable_notifications': False  # Desabilitar para teste
        }
        
        monitor = await create_health_monitor(config)
        
        # Iniciar monitor
        await monitor.start()
        
        # Executar por 1 minuto
        await asyncio.sleep(60)
        
        # Analisar tendências
        trends = monitor.analyze_trends(period_hours=1)
        print("\nTendências:")
        for trend in trends:
            print(f"  {trend.component}: {trend.trend}")
            print(f"    Disponibilidade: {trend.availability_percent:.1f}%")
            print(f"    Tempo médio: {trend.average_response_time:.0f}ms")
        
        # Resumo dos componentes
        print("\nResumo dos componentes:")
        for component in monitor.metrics_history.keys():
            summary = monitor.get_component_summary(component)
            if summary:
                print(f"\n  {component}:")
                print(f"    Status: {summary['current_status']}")
                print(f"    Disponibilidade: {summary['availability']['percent']:.1f}%")
                print(f"    Tempo de resposta médio: {summary['response_time']['average']:.0f}ms")
        
        # Parar monitor
        await monitor.stop()
    
    # Executar teste
    asyncio.run(test_monitor())