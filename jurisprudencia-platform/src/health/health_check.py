#!/usr/bin/env python3
"""
🏥 SISTEMA DE HEALTH CHECK
Monitora a saúde de todos os componentes do sistema
"""

import os
import asyncio
import aiohttp
import psutil
import platform
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import redis
import psycopg2
from sqlalchemy import create_engine, text
import logging
from functools import wraps
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Status de saúde do componente"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Tipos de componentes do sistema"""
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    API = "api"
    SERVICE = "service"
    EXTERNAL = "external"


@dataclass
class HealthCheckResult:
    """Resultado de um health check"""
    component: str
    type: ComponentType
    status: HealthStatus
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None
    checks: Optional[List[Dict]] = None


@dataclass
class SystemHealth:
    """Saúde geral do sistema"""
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    components: List[HealthCheckResult]
    metrics: Dict[str, Any]
    version: str


class HealthChecker:
    """Verificador de saúde base"""
    
    def __init__(self, name: str, component_type: ComponentType):
        self.name = name
        self.component_type = component_type
        self.timeout = 5  # segundos
    
    async def check(self) -> HealthCheckResult:
        """Executar verificação de saúde"""
        start_time = time.time()
        
        try:
            details = await self._perform_check()
            response_time = (time.time() - start_time) * 1000
            
            status = self._determine_status(details)
            
            return HealthCheckResult(
                component=self.name,
                type=self.component_type,
                status=status,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time,
                details=details
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component=self.name,
                type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time,
                details={},
                error=str(e)
            )
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Implementar verificação específica"""
        raise NotImplementedError
    
    def _determine_status(self, details: Dict[str, Any]) -> HealthStatus:
        """Determinar status baseado nos detalhes"""
        return HealthStatus.HEALTHY


class DatabaseHealthChecker(HealthChecker):
    """Verificador de saúde do banco de dados"""
    
    def __init__(self, db_url: str):
        super().__init__("PostgreSQL", ComponentType.DATABASE)
        self.db_url = db_url
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Verificar saúde do banco"""
        details = {
            'connectable': False,
            'response_time_ms': 0,
            'active_connections': 0,
            'database_size': 0,
            'tables_count': 0
        }
        
        try:
            engine = create_engine(self.db_url)
            
            # Teste de conexão
            start = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            details['response_time_ms'] = (time.time() - start) * 1000
            details['connectable'] = True
            
            # Estatísticas
            with engine.connect() as conn:
                # Conexões ativas
                result = conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state != 'idle'"
                ))
                details['active_connections'] = result.scalar()
                
                # Tamanho do banco
                result = conn.execute(text(
                    "SELECT pg_database_size(current_database())"
                ))
                details['database_size'] = result.scalar()
                
                # Contagem de tabelas
                result = conn.execute(text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                ))
                details['tables_count'] = result.scalar()
                
                # Verificar lag de replicação (se aplicável)
                try:
                    result = conn.execute(text(
                        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as replication_lag"
                    ))
                    lag = result.scalar()
                    if lag is not None:
                        details['replication_lag_seconds'] = lag
                except:
                    pass
            
            return details
            
        except Exception as e:
            details['error'] = str(e)
            raise
    
    def _determine_status(self, details: Dict[str, Any]) -> HealthStatus:
        """Determinar status do banco"""
        if not details.get('connectable'):
            return HealthStatus.UNHEALTHY
        
        # Verificar métricas
        response_time = details.get('response_time_ms', 0)
        active_connections = details.get('active_connections', 0)
        replication_lag = details.get('replication_lag_seconds', 0)
        
        # Critérios de saúde
        if response_time > 1000 or active_connections > 100 or replication_lag > 10:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY


class RedisHealthChecker(HealthChecker):
    """Verificador de saúde do Redis"""
    
    def __init__(self, redis_url: str):
        super().__init__("Redis", ComponentType.CACHE)
        self.redis_url = redis_url
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Verificar saúde do Redis"""
        details = {
            'connectable': False,
            'response_time_ms': 0,
            'used_memory': 0,
            'connected_clients': 0,
            'keyspace_hits': 0,
            'keyspace_misses': 0
        }
        
        try:
            r = redis.from_url(self.redis_url)
            
            # Teste de conexão
            start = time.time()
            r.ping()
            details['response_time_ms'] = (time.time() - start) * 1000
            details['connectable'] = True
            
            # Estatísticas
            info = r.info()
            details['used_memory'] = info.get('used_memory', 0)
            details['used_memory_human'] = info.get('used_memory_human', 'N/A')
            details['connected_clients'] = info.get('connected_clients', 0)
            details['keyspace_hits'] = info.get('keyspace_hits', 0)
            details['keyspace_misses'] = info.get('keyspace_misses', 0)
            
            # Taxa de hit
            total_ops = details['keyspace_hits'] + details['keyspace_misses']
            if total_ops > 0:
                details['hit_rate'] = (details['keyspace_hits'] / total_ops) * 100
            
            return details
            
        except Exception as e:
            details['error'] = str(e)
            raise
    
    def _determine_status(self, details: Dict[str, Any]) -> HealthStatus:
        """Determinar status do Redis"""
        if not details.get('connectable'):
            return HealthStatus.UNHEALTHY
        
        response_time = details.get('response_time_ms', 0)
        hit_rate = details.get('hit_rate', 100)
        
        if response_time > 100 or hit_rate < 80:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY


class APIHealthChecker(HealthChecker):
    """Verificador de saúde de API externa"""
    
    def __init__(self, name: str, url: str, expected_status: int = 200):
        super().__init__(name, ComponentType.EXTERNAL)
        self.url = url
        self.expected_status = expected_status
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Verificar saúde da API"""
        details = {
            'url': self.url,
            'reachable': False,
            'status_code': None,
            'response_time_ms': 0
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(self.url, timeout=self.timeout) as response:
                    details['response_time_ms'] = (time.time() - start) * 1000
                    details['status_code'] = response.status
                    details['reachable'] = response.status == self.expected_status
                    
                    if response.status == self.expected_status:
                        # Tentar parsear resposta JSON
                        try:
                            data = await response.json()
                            if isinstance(data, dict):
                                details['response_sample'] = {k: v for k, v in list(data.items())[:3]}
                        except:
                            pass
            
            return details
            
        except asyncio.TimeoutError:
            details['error'] = 'Timeout'
            raise
        except Exception as e:
            details['error'] = str(e)
            raise
    
    def _determine_status(self, details: Dict[str, Any]) -> HealthStatus:
        """Determinar status da API"""
        if not details.get('reachable'):
            return HealthStatus.UNHEALTHY
        
        response_time = details.get('response_time_ms', 0)
        
        if response_time > 3000:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY


class DiskHealthChecker(HealthChecker):
    """Verificador de saúde do disco"""
    
    def __init__(self, path: str = "/", threshold: float = 90.0):
        super().__init__("Disk Storage", ComponentType.STORAGE)
        self.path = path
        self.threshold = threshold
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Verificar espaço em disco"""
        try:
            usage = psutil.disk_usage(self.path)
            
            details = {
                'path': self.path,
                'total_bytes': usage.total,
                'used_bytes': usage.used,
                'free_bytes': usage.free,
                'percent_used': usage.percent,
                'total_human': self._bytes_to_human(usage.total),
                'used_human': self._bytes_to_human(usage.used),
                'free_human': self._bytes_to_human(usage.free)
            }
            
            # Verificar inodes (Linux)
            if platform.system() == 'Linux':
                try:
                    import subprocess
                    result = subprocess.run(
                        ['df', '-i', self.path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split()
                            if len(parts) >= 5:
                                details['inodes_percent_used'] = float(parts[4].rstrip('%'))
                except:
                    pass
            
            return details
            
        except Exception as e:
            raise Exception(f"Erro ao verificar disco: {e}")
    
    def _determine_status(self, details: Dict[str, Any]) -> HealthStatus:
        """Determinar status do disco"""
        percent_used = details.get('percent_used', 0)
        inodes_used = details.get('inodes_percent_used', 0)
        
        if percent_used > self.threshold or inodes_used > 90:
            return HealthStatus.UNHEALTHY
        elif percent_used > (self.threshold - 10) or inodes_used > 80:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def _bytes_to_human(self, bytes: int) -> str:
        """Converter bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"


class SystemMetricsCollector:
    """Coletor de métricas do sistema"""
    
    @staticmethod
    async def collect() -> Dict[str, Any]:
        """Coletar métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memória
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Processos
            process_count = len(psutil.pids())
            
            # Rede (taxa de transferência)
            net_io = psutil.net_io_counters()
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent
                },
                'processes': {
                    'total': process_count
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                'system': {
                    'platform': platform.platform(),
                    'python_version': platform.python_version(),
                    'boot_time': boot_time.isoformat(),
                    'uptime_seconds': uptime.total_seconds()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
            return {}


class HealthCheckService:
    """Serviço principal de health check"""
    
    def __init__(self):
        self.checkers: List[HealthChecker] = []
        self.cache_duration = 30  # segundos
        self._cache: Optional[Tuple[datetime, SystemHealth]] = None
        self.version = os.getenv('APP_VERSION', '1.0.0')
    
    def register_checker(self, checker: HealthChecker):
        """Registrar um verificador"""
        self.checkers.append(checker)
    
    async def check_health(self, use_cache: bool = True) -> SystemHealth:
        """Verificar saúde completa do sistema"""
        # Verificar cache
        if use_cache and self._cache:
            cache_time, cached_result = self._cache
            if datetime.utcnow() - cache_time < timedelta(seconds=self.cache_duration):
                return cached_result
        
        # Executar todos os checks em paralelo
        tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        components = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Criar resultado de erro
                components.append(HealthCheckResult(
                    component=self.checkers[i].name,
                    type=self.checkers[i].component_type,
                    status=HealthStatus.UNHEALTHY,
                    timestamp=datetime.utcnow(),
                    response_time_ms=0,
                    details={},
                    error=str(result)
                ))
            else:
                components.append(result)
        
        # Coletar métricas do sistema
        metrics = await SystemMetricsCollector.collect()
        
        # Determinar status geral
        overall_status = self._determine_overall_status(components)
        
        # Criar resultado
        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=metrics.get('system', {}).get('uptime_seconds', 0),
            components=components,
            metrics=metrics,
            version=self.version
        )
        
        # Atualizar cache
        self._cache = (datetime.utcnow(), system_health)
        
        return system_health
    
    def _determine_overall_status(self, components: List[HealthCheckResult]) -> HealthStatus:
        """Determinar status geral baseado nos componentes"""
        if not components:
            return HealthStatus.UNKNOWN
        
        # Se algum componente crítico está unhealthy, sistema está unhealthy
        critical_types = [ComponentType.DATABASE, ComponentType.CACHE]
        for component in components:
            if component.type in critical_types and component.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # Se mais de 50% dos componentes estão degraded ou unhealthy
        unhealthy_count = sum(1 for c in components 
                             if c.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED])
        
        if unhealthy_count > len(components) / 2:
            return HealthStatus.UNHEALTHY
        elif unhealthy_count > 0:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Obter status detalhado em formato dict"""
        health = await self.check_health()
        
        # Converter para dict
        result = {
            'status': health.status.value,
            'timestamp': health.timestamp.isoformat(),
            'uptime_seconds': health.uptime_seconds,
            'version': health.version,
            'components': {},
            'metrics': health.metrics
        }
        
        # Agrupar componentes por tipo
        for component in health.components:
            comp_type = component.type.value
            if comp_type not in result['components']:
                result['components'][comp_type] = []
            
            result['components'][comp_type].append({
                'name': component.component,
                'status': component.status.value,
                'response_time_ms': component.response_time_ms,
                'details': component.details,
                'error': component.error,
                'timestamp': component.timestamp.isoformat()
            })
        
        return result
    
    def get_prometheus_metrics(self) -> str:
        """Gerar métricas no formato Prometheus"""
        if not self._cache:
            return ""
        
        _, health = self._cache
        lines = []
        
        # Status geral
        status_value = 1 if health.status == HealthStatus.HEALTHY else 0
        lines.append(f'system_health_status {{status="{health.status.value}"}} {status_value}')
        lines.append(f'system_uptime_seconds {health.uptime_seconds}')
        
        # Status dos componentes
        for component in health.components:
            status_value = 1 if component.status == HealthStatus.HEALTHY else 0
            labels = f'component="{component.component}",type="{component.type.value}"'
            
            lines.append(f'component_health_status {{{labels},status="{component.status.value}"}} {status_value}')
            lines.append(f'component_response_time_ms {{{labels}}} {component.response_time_ms}')
        
        # Métricas do sistema
        if 'cpu' in health.metrics:
            lines.append(f'system_cpu_percent {health.metrics["cpu"]["percent"]}')
        
        if 'memory' in health.metrics:
            lines.append(f'system_memory_percent {health.metrics["memory"]["percent"]}')
            lines.append(f'system_memory_available_bytes {health.metrics["memory"]["available"]}')
        
        return '\n'.join(lines)


# Decorator para health check de funções
def health_check_endpoint(service: HealthCheckService):
    """Decorator para adicionar health check a endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Verificar saúde antes de executar
            health = await service.check_health()
            
            if health.status == HealthStatus.UNHEALTHY:
                raise Exception("Sistema unhealthy, operação não permitida")
            
            # Adicionar header de saúde na resposta
            result = await func(*args, **kwargs)
            
            if hasattr(result, 'headers'):
                result.headers['X-System-Health'] = health.status.value
            
            return result
        
        return wrapper
    return decorator


# Configuração padrão do serviço
def create_health_service(config: Dict[str, Any]) -> HealthCheckService:
    """Criar serviço de health check configurado"""
    service = HealthCheckService()
    
    # Registrar checkers baseado na configuração
    if 'database_url' in config:
        service.register_checker(
            DatabaseHealthChecker(config['database_url'])
        )
    
    if 'redis_url' in config:
        service.register_checker(
            RedisHealthChecker(config['redis_url'])
        )
    
    # APIs externas
    for api_config in config.get('external_apis', []):
        service.register_checker(
            APIHealthChecker(
                name=api_config['name'],
                url=api_config['url'],
                expected_status=api_config.get('expected_status', 200)
            )
        )
    
    # Verificação de disco
    for disk_config in config.get('disk_checks', [{'path': '/', 'threshold': 90}]):
        service.register_checker(
            DiskHealthChecker(
                path=disk_config['path'],
                threshold=disk_config.get('threshold', 90)
            )
        )
    
    return service


if __name__ == "__main__":
    # Exemplo de uso
    async def test_health_check():
        config = {
            'database_url': os.getenv('DATABASE_URL', 'postgresql://localhost/test'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'external_apis': [
                {
                    'name': 'Google DNS',
                    'url': 'https://dns.google/resolve?name=google.com'
                }
            ],
            'disk_checks': [
                {'path': '/', 'threshold': 90}
            ]
        }
        
        service = create_health_service(config)
        
        # Verificar saúde
        health = await service.check_health()
        print(f"Status geral: {health.status.value}")
        print(f"Uptime: {health.uptime_seconds:.0f} segundos")
        
        # Componentes
        for component in health.components:
            print(f"\n{component.component}:")
            print(f"  Status: {component.status.value}")
            print(f"  Response time: {component.response_time_ms:.2f}ms")
            if component.error:
                print(f"  Erro: {component.error}")
        
        # Status detalhado
        detailed = await service.get_detailed_status()
        print(f"\nStatus detalhado: {json.dumps(detailed, indent=2)}")
        
        # Métricas Prometheus
        print("\nMétricas Prometheus:")
        print(service.get_prometheus_metrics())
    
    # Executar teste
    asyncio.run(test_health_check())