#!/usr/bin/env python3
"""
🧠 RATE LIMITER ADAPTATIVO
Sistema inteligente que ajusta limites baseado em padrões de uso
"""

import asyncio
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import numpy as np
from sklearn.ensemble import IsolationForest
import logging

from .rate_limiter import (
    RateLimitRule, RateLimitStrategy, RateLimitScope,
    RateLimitManager, RateLimitStatus
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UsagePattern:
    """Padrão de uso de um cliente"""
    key: str
    requests_per_minute: List[int] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    error_rates: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def add_request(self, response_time: float, is_error: bool):
        """Adicionar dados de requisição"""
        # Manter histórico de 60 minutos
        if len(self.requests_per_minute) >= 60:
            self.requests_per_minute.pop(0)
            self.response_times.pop(0)
            self.error_rates.pop(0)
        
        self.response_times.append(response_time)
        self.error_rates.append(1.0 if is_error else 0.0)
        self.last_updated = datetime.utcnow()


@dataclass
class AnomalyScore:
    """Pontuação de anomalia"""
    score: float
    is_anomaly: bool
    reason: str
    confidence: float


class AdaptiveRateLimiter:
    """Rate limiter que se adapta ao comportamento dos clientes"""
    
    def __init__(self, base_manager: RateLimitManager):
        self.manager = base_manager
        self.usage_patterns: Dict[str, UsagePattern] = {}
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.reputation_scores: Dict[str, float] = {}
        
        # Configurações adaptativas
        self.min_multiplier = 0.5  # Reduzir limite em até 50%
        self.max_multiplier = 2.0  # Aumentar limite em até 200%
        self.reputation_decay = 0.95  # Decaimento da reputação
        self.anomaly_threshold = 0.7
        
        # Histórico para aprendizado
        self.request_history = deque(maxlen=10000)
        self.model_trained = False
    
    async def check_request_adaptive(self, request, rule: RateLimitRule) -> Tuple[bool, Optional[RateLimitStatus]]:
        """Verificar requisição com limites adaptativos"""
        # Obter chave do cliente
        key = await self.manager._get_scope_key(rule, request)
        
        # Obter ou criar padrão de uso
        if key not in self.usage_patterns:
            self.usage_patterns[key] = UsagePattern(key=key)
        
        pattern = self.usage_patterns[key]
        
        # Calcular multiplicador baseado em reputação e anomalias
        multiplier = await self._calculate_multiplier(key, pattern)
        
        # Criar regra adaptada
        adapted_rule = RateLimitRule(
            name=f"{rule.name}_adaptive",
            limit=int(rule.limit * multiplier),
            window_seconds=rule.window_seconds,
            strategy=rule.strategy,
            scope=rule.scope,
            burst_size=int((rule.burst_size or rule.limit) * multiplier) if rule.burst_size else None,
            block_duration_seconds=rule.block_duration_seconds
        )
        
        # Verificar com regra adaptada
        strategy = self.manager.strategies.get(adapted_rule.strategy)
        if not strategy:
            return True, None
        
        status = await strategy.check_limit(key, adapted_rule)
        
        # Registrar requisição para aprendizado
        await self._record_request(key, request, status.allowed)
        
        return status.allowed, status
    
    async def _calculate_multiplier(self, key: str, pattern: UsagePattern) -> float:
        """Calcular multiplicador de limite baseado em comportamento"""
        base_multiplier = 1.0
        
        # 1. Reputação do cliente
        reputation = self.reputation_scores.get(key, 1.0)
        reputation_multiplier = 0.5 + (reputation * 0.5)  # 0.5 a 1.0
        
        # 2. Detecção de anomalias
        anomaly_score = await self._detect_anomaly(pattern)
        if anomaly_score.is_anomaly:
            anomaly_multiplier = 0.5  # Reduzir limite para comportamento anômalo
            logger.warning(f"Anomalia detectada para {key}: {anomaly_score.reason}")
        else:
            anomaly_multiplier = 1.0
        
        # 3. Padrão de uso histórico
        usage_multiplier = self._analyze_usage_pattern(pattern)
        
        # Combinar multiplicadores
        final_multiplier = base_multiplier * reputation_multiplier * anomaly_multiplier * usage_multiplier
        
        # Aplicar limites
        return max(self.min_multiplier, min(self.max_multiplier, final_multiplier))
    
    async def _detect_anomaly(self, pattern: UsagePattern) -> AnomalyScore:
        """Detectar comportamento anômalo"""
        if len(pattern.response_times) < 10:
            return AnomalyScore(score=0.0, is_anomaly=False, reason="Dados insuficientes", confidence=0.0)
        
        # Preparar features
        features = []
        
        # Taxa de requisições
        if pattern.requests_per_minute:
            req_rate = sum(pattern.requests_per_minute[-10:]) / 10
            features.append(req_rate)
        else:
            features.append(0)
        
        # Tempo médio de resposta
        avg_response_time = statistics.mean(pattern.response_times[-10:])
        features.append(avg_response_time)
        
        # Taxa de erro
        error_rate = statistics.mean(pattern.error_rates[-10:])
        features.append(error_rate)
        
        # Variância no tempo de resposta
        response_variance = statistics.variance(pattern.response_times[-10:])
        features.append(response_variance)
        
        # Detectar com modelo se treinado
        if self.model_trained and len(self.request_history) > 100:
            try:
                score = self.anomaly_detector.decision_function([features])[0]
                is_anomaly = score < -self.anomaly_threshold
                
                # Determinar razão
                reason = "Normal"
                if is_anomaly:
                    if error_rate > 0.3:
                        reason = "Taxa de erro alta"
                    elif req_rate > 100:
                        reason = "Taxa de requisições muito alta"
                    elif response_variance > 1000:
                        reason = "Variância alta no tempo de resposta"
                    else:
                        reason = "Padrão anômalo detectado"
                
                confidence = abs(score)
                
                return AnomalyScore(
                    score=score,
                    is_anomaly=is_anomaly,
                    reason=reason,
                    confidence=min(1.0, confidence)
                )
                
            except Exception as e:
                logger.error(f"Erro na detecção de anomalia: {e}")
        
        # Detecção simples baseada em regras
        if error_rate > 0.5:
            return AnomalyScore(
                score=-1.0,
                is_anomaly=True,
                reason="Taxa de erro muito alta",
                confidence=0.8
            )
        
        if req_rate > 200:
            return AnomalyScore(
                score=-0.8,
                is_anomaly=True,
                reason="Taxa de requisições excessiva",
                confidence=0.7
            )
        
        return AnomalyScore(score=0.0, is_anomaly=False, reason="Normal", confidence=0.5)
    
    def _analyze_usage_pattern(self, pattern: UsagePattern) -> float:
        """Analisar padrão de uso e retornar multiplicador"""
        if len(pattern.response_times) < 20:
            return 1.0  # Não há dados suficientes
        
        # Calcular métricas
        avg_response_time = statistics.mean(pattern.response_times)
        error_rate = statistics.mean(pattern.error_rates)
        
        # Cliente com bom comportamento
        if avg_response_time < 100 and error_rate < 0.01:
            return 1.5  # Aumentar limite
        
        # Cliente normal
        if avg_response_time < 500 and error_rate < 0.05:
            return 1.0
        
        # Cliente problemático
        if error_rate > 0.1 or avg_response_time > 1000:
            return 0.7  # Reduzir limite
        
        return 1.0
    
    async def _record_request(self, key: str, request, allowed: bool):
        """Registrar requisição para aprendizado"""
        # Adicionar ao histórico
        self.request_history.append({
            'key': key,
            'timestamp': datetime.utcnow(),
            'path': request.url.path,
            'method': request.method,
            'allowed': allowed
        })
        
        # Atualizar reputação
        if key not in self.reputation_scores:
            self.reputation_scores[key] = 1.0
        
        if allowed:
            # Melhorar reputação ligeiramente
            self.reputation_scores[key] = min(2.0, self.reputation_scores[key] * 1.01)
        else:
            # Degradar reputação
            self.reputation_scores[key] = max(0.1, self.reputation_scores[key] * 0.95)
        
        # Treinar modelo periodicamente
        if len(self.request_history) > 1000 and not self.model_trained:
            await self._train_anomaly_model()
    
    async def _train_anomaly_model(self):
        """Treinar modelo de detecção de anomalias"""
        try:
            # Preparar dados de treino
            training_data = []
            
            for pattern in self.usage_patterns.values():
                if len(pattern.response_times) >= 10:
                    features = [
                        sum(pattern.requests_per_minute[-10:]) / 10 if pattern.requests_per_minute else 0,
                        statistics.mean(pattern.response_times[-10:]),
                        statistics.mean(pattern.error_rates[-10:]),
                        statistics.variance(pattern.response_times[-10:])
                    ]
                    training_data.append(features)
            
            if len(training_data) > 50:
                self.anomaly_detector.fit(training_data)
                self.model_trained = True
                logger.info("Modelo de anomalia treinado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao treinar modelo: {e}")
    
    async def apply_reputation_decay(self):
        """Aplicar decaimento de reputação periodicamente"""
        for key in list(self.reputation_scores.keys()):
            # Decair em direção a 1.0 (neutro)
            current = self.reputation_scores[key]
            if current > 1.0:
                self.reputation_scores[key] = 1.0 + (current - 1.0) * self.reputation_decay
            else:
                self.reputation_scores[key] = 1.0 - (1.0 - current) * self.reputation_decay
            
            # Remover se muito próximo de 1.0
            if abs(self.reputation_scores[key] - 1.0) < 0.01:
                del self.reputation_scores[key]
    
    def get_client_profile(self, key: str) -> Optional[Dict[str, Any]]:
        """Obter perfil detalhado de um cliente"""
        if key not in self.usage_patterns:
            return None
        
        pattern = self.usage_patterns[key]
        reputation = self.reputation_scores.get(key, 1.0)
        
        profile = {
            'key': key,
            'reputation_score': reputation,
            'reputation_level': self._get_reputation_level(reputation),
            'last_activity': pattern.last_updated.isoformat(),
            'statistics': {}
        }
        
        if pattern.response_times:
            profile['statistics']['avg_response_time'] = statistics.mean(pattern.response_times)
            profile['statistics']['p95_response_time'] = np.percentile(pattern.response_times, 95)
        
        if pattern.error_rates:
            profile['statistics']['error_rate'] = statistics.mean(pattern.error_rates)
        
        if pattern.requests_per_minute:
            profile['statistics']['avg_requests_per_minute'] = statistics.mean(pattern.requests_per_minute)
        
        return profile
    
    def _get_reputation_level(self, score: float) -> str:
        """Obter nível de reputação textual"""
        if score >= 1.8:
            return "Excelente"
        elif score >= 1.5:
            return "Muito Bom"
        elif score >= 1.2:
            return "Bom"
        elif score >= 0.8:
            return "Normal"
        elif score >= 0.5:
            return "Suspeito"
        else:
            return "Problemático"
    
    async def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Gerar recomendações baseadas em padrões observados"""
        recommendations = []
        
        # Analisar clientes problemáticos
        problem_clients = [
            (key, score) for key, score in self.reputation_scores.items()
            if score < 0.5
        ]
        
        if problem_clients:
            recommendations.append({
                'type': 'security',
                'severity': 'high',
                'message': f"Detectados {len(problem_clients)} clientes problemáticos",
                'action': 'Considere bloquear permanentemente estes IPs/usuários',
                'details': problem_clients[:5]  # Top 5
            })
        
        # Analisar padrões gerais
        total_patterns = len(self.usage_patterns)
        if total_patterns > 100:
            avg_error_rate = statistics.mean([
                statistics.mean(p.error_rates) 
                for p in self.usage_patterns.values() 
                if p.error_rates
            ])
            
            if avg_error_rate > 0.1:
                recommendations.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'message': f"Taxa de erro média alta: {avg_error_rate:.1%}",
                    'action': 'Investigar problemas de estabilidade da API'
                })
        
        # Recomendar ajustes de limites
        high_reputation_clients = sum(1 for score in self.reputation_scores.values() if score > 1.5)
        if high_reputation_clients > total_patterns * 0.3:
            recommendations.append({
                'type': 'optimization',
                'severity': 'low',
                'message': f"{high_reputation_clients} clientes têm excelente reputação",
                'action': 'Considere aumentar os limites globais de rate limiting'
            })
        
        return recommendations


# Worker para manutenção periódica
async def adaptive_maintenance_worker(limiter: AdaptiveRateLimiter):
    """Worker para manutenção do rate limiter adaptativo"""
    while True:
        try:
            # Aplicar decaimento de reputação
            await limiter.apply_reputation_decay()
            
            # Limpar padrões antigos
            cutoff = datetime.utcnow() - timedelta(hours=24)
            old_keys = [
                key for key, pattern in limiter.usage_patterns.items()
                if pattern.last_updated < cutoff
            ]
            
            for key in old_keys:
                del limiter.usage_patterns[key]
                if key in limiter.reputation_scores:
                    del limiter.reputation_scores[key]
            
            if old_keys:
                logger.info(f"Removidos {len(old_keys)} padrões antigos")
            
            # Re-treinar modelo se necessário
            if len(limiter.usage_patterns) > 100:
                await limiter._train_anomaly_model()
            
            # Aguardar próximo ciclo (1 hora)
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Erro no worker de manutenção: {e}")
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # Exemplo de uso
    async def test_adaptive_limiter():
        from fastapi import Request
        
        # Criar manager base
        manager = RateLimitManager()
        await manager.initialize()
        
        # Criar limiter adaptativo
        adaptive = AdaptiveRateLimiter(manager)
        
        # Regra de teste
        rule = RateLimitRule(
            name="test_adaptive",
            limit=10,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=RateLimitScope.IP
        )
        
        # Simular requisições de diferentes clientes
        clients = [
            ("good_client", 5, 50, 0.0),    # Cliente bom: poucas requisições, rápido, sem erros
            ("normal_client", 8, 200, 0.05), # Cliente normal
            ("bad_client", 15, 800, 0.3),   # Cliente ruim: muitas requisições, lento, muitos erros
        ]
        
        for client_name, req_count, response_time, error_rate in clients:
            print(f"\n=== Testando {client_name} ===")
            
            # Criar requisição fake
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/api/test",
                "headers": [],
                "server": ("localhost", 8000),
                "client": (client_name, 50000),
                "scheme": "http"
            }
            
            request = Request(scope)
            
            # Simular padrão de uso
            pattern = UsagePattern(key=f"ip:{client_name}")
            
            for i in range(20):
                # Adicionar dados históricos
                pattern.add_request(
                    response_time + np.random.normal(0, 50),
                    np.random.random() < error_rate
                )
            
            adaptive.usage_patterns[f"ip:{client_name}"] = pattern
            
            # Testar requisições
            allowed_count = 0
            for i in range(req_count):
                allowed, status = await adaptive.check_request_adaptive(request, rule)
                if allowed:
                    allowed_count += 1
                
                print(f"  Requisição {i+1}: {'✓' if allowed else '✗'}", end="")
                if status:
                    print(f" (limite: {status.limit}, restante: {status.remaining})")
                else:
                    print()
            
            print(f"  Total permitidas: {allowed_count}/{req_count}")
            
            # Mostrar perfil
            profile = adaptive.get_client_profile(f"ip:{client_name}")
            if profile:
                print(f"  Reputação: {profile['reputation_score']:.2f} ({profile['reputation_level']})")
                if 'statistics' in profile:
                    stats = profile['statistics']
                    if 'avg_response_time' in stats:
                        print(f"  Tempo médio: {stats['avg_response_time']:.0f}ms")
                    if 'error_rate' in stats:
                        print(f"  Taxa de erro: {stats['error_rate']:.1%}")
        
        # Gerar recomendações
        print("\n=== Recomendações ===")
        recommendations = await adaptive.generate_recommendations()
        for rec in recommendations:
            print(f"[{rec['severity'].upper()}] {rec['message']}")
            print(f"  Ação: {rec['action']}")
        
        await manager.close()
    
    # Executar teste
    asyncio.run(test_adaptive_limiter())