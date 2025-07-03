#!/usr/bin/env python3
"""
🚦 SISTEMA DE RATE LIMITING
Controla e limita o número de requisições por cliente
"""

import time
import asyncio
import hashlib
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import redis.asyncio as redis
from fastapi import Request, HTTPException, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Estratégias de rate limiting"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Escopos de rate limiting"""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"


@dataclass
class RateLimitRule:
    """Regra de rate limiting"""
    name: str
    limit: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.IP
    burst_size: Optional[int] = None
    block_duration_seconds: Optional[int] = None
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)
    endpoints: Optional[List[str]] = None
    methods: Optional[List[str]] = None
    custom_key_func: Optional[callable] = None


@dataclass
class RateLimitStatus:
    """Status atual do rate limit"""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None
    blocked_until: Optional[datetime] = None


class RateLimiter:
    """Implementação base de rate limiter"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.key_prefix = "rate_limit"
    
    async def check_limit(self, key: str, rule: RateLimitRule) -> RateLimitStatus:
        """Verificar se requisição está dentro do limite"""
        raise NotImplementedError
    
    def _get_redis_key(self, key: str, rule: RateLimitRule) -> str:
        """Gerar chave Redis"""
        return f"{self.key_prefix}:{rule.name}:{key}"
    
    def _get_window_start(self, window_seconds: int) -> int:
        """Obter início da janela atual"""
        now = int(time.time())
        return now - (now % window_seconds)


class FixedWindowRateLimiter(RateLimiter):
    """Rate limiter com janela fixa"""
    
    async def check_limit(self, key: str, rule: RateLimitRule) -> RateLimitStatus:
        redis_key = self._get_redis_key(key, rule)
        window_start = self._get_window_start(rule.window_seconds)
        window_key = f"{redis_key}:{window_start}"
        
        # Pipeline para operação atômica
        async with self.redis.pipeline() as pipe:
            pipe.incr(window_key)
            pipe.expire(window_key, rule.window_seconds)
            results = await pipe.execute()
        
        count = results[0]
        reset_at = datetime.fromtimestamp(window_start + rule.window_seconds)
        
        if count <= rule.limit:
            return RateLimitStatus(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit - count,
                reset_at=reset_at
            )
        else:
            return RateLimitStatus(
                allowed=False,
                limit=rule.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=int((reset_at - datetime.now()).total_seconds())
            )


class SlidingWindowRateLimiter(RateLimiter):
    """Rate limiter com janela deslizante"""
    
    async def check_limit(self, key: str, rule: RateLimitRule) -> RateLimitStatus:
        redis_key = self._get_redis_key(key, rule)
        now = time.time()
        window_start = now - rule.window_seconds
        
        # Script Lua para operação atômica
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])
        
        -- Remover entradas antigas
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- Contar requisições na janela
        local count = redis.call('ZCARD', key)
        
        if count < limit then
            -- Adicionar nova requisição
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window_seconds)
            return {1, count + 1}
        else
            return {0, count}
        end
        """
        
        result = await self.redis.eval(
            lua_script,
            keys=[redis_key],
            args=[now, window_start, rule.limit, rule.window_seconds]
        )
        
        allowed, count = result
        reset_at = datetime.fromtimestamp(now + rule.window_seconds)
        
        if allowed:
            return RateLimitStatus(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit - count,
                reset_at=reset_at
            )
        else:
            # Calcular quando a requisição mais antiga expira
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                retry_after = int(oldest_timestamp + rule.window_seconds - now)
            else:
                retry_after = rule.window_seconds
            
            return RateLimitStatus(
                allowed=False,
                limit=rule.limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=max(1, retry_after)
            )


class TokenBucketRateLimiter(RateLimiter):
    """Rate limiter com token bucket"""
    
    async def check_limit(self, key: str, rule: RateLimitRule) -> RateLimitStatus:
        redis_key = self._get_redis_key(key, rule)
        now = time.time()
        
        # Taxa de reabastecimento
        refill_rate = rule.limit / rule.window_seconds
        burst_size = rule.burst_size or rule.limit
        
        # Script Lua para token bucket
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local burst_size = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])
        
        -- Obter estado atual
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or burst_size
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calcular tokens a adicionar
        local elapsed = now - last_refill
        local tokens_to_add = elapsed * refill_rate
        tokens = math.min(burst_size, tokens + tokens_to_add)
        
        if tokens >= 1 then
            -- Consumir token
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, window_seconds * 2)
            return {1, tokens}
        else
            -- Sem tokens disponíveis
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, window_seconds * 2)
            return {0, tokens}
        end
        """
        
        result = await self.redis.eval(
            lua_script,
            keys=[redis_key],
            args=[now, refill_rate, burst_size, rule.window_seconds]
        )
        
        allowed, tokens = result
        
        # Calcular quando teremos tokens novamente
        if not allowed:
            time_to_token = (1 - tokens) / refill_rate
            retry_after = int(time_to_token) + 1
        else:
            retry_after = None
        
        reset_at = datetime.fromtimestamp(now + rule.window_seconds)
        
        return RateLimitStatus(
            allowed=bool(allowed),
            limit=rule.limit,
            remaining=int(tokens),
            reset_at=reset_at,
            retry_after=retry_after
        )


class RateLimitManager:
    """Gerenciador de rate limiting"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.rules: Dict[str, RateLimitRule] = {}
        self.strategies: Dict[RateLimitStrategy, RateLimiter] = {}
        self.blocked_keys: Dict[str, datetime] = {}
    
    async def initialize(self):
        """Inicializar conexão Redis e estratégias"""
        self.redis = await redis.from_url(self.redis_url)
        
        # Inicializar estratégias
        self.strategies = {
            RateLimitStrategy.FIXED_WINDOW: FixedWindowRateLimiter(self.redis),
            RateLimitStrategy.SLIDING_WINDOW: SlidingWindowRateLimiter(self.redis),
            RateLimitStrategy.TOKEN_BUCKET: TokenBucketRateLimiter(self.redis)
        }
    
    async def close(self):
        """Fechar conexões"""
        if self.redis:
            await self.redis.close()
    
    def add_rule(self, rule: RateLimitRule):
        """Adicionar regra de rate limiting"""
        self.rules[rule.name] = rule
        logger.info(f"Regra de rate limit adicionada: {rule.name}")
    
    def remove_rule(self, name: str):
        """Remover regra de rate limiting"""
        if name in self.rules:
            del self.rules[name]
            logger.info(f"Regra de rate limit removida: {name}")
    
    async def check_request(self, request: Request) -> Tuple[bool, Optional[RateLimitStatus]]:
        """Verificar se requisição deve ser permitida"""
        # Verificar todas as regras aplicáveis
        for rule_name, rule in self.rules.items():
            # Verificar se regra se aplica a este endpoint/método
            if not self._rule_applies(rule, request):
                continue
            
            # Obter chave para o escopo
            key = await self._get_scope_key(rule, request)
            
            # Verificar whitelist/blacklist
            if self._is_whitelisted(key, rule):
                continue
            
            if self._is_blacklisted(key, rule):
                return False, RateLimitStatus(
                    allowed=False,
                    limit=0,
                    remaining=0,
                    reset_at=datetime.max,
                    blocked_until=datetime.max
                )
            
            # Verificar se está bloqueado temporariamente
            if self._is_blocked(key, rule):
                blocked_until = self.blocked_keys.get(f"{rule.name}:{key}")
                return False, RateLimitStatus(
                    allowed=False,
                    limit=rule.limit,
                    remaining=0,
                    reset_at=datetime.now() + timedelta(seconds=rule.window_seconds),
                    blocked_until=blocked_until
                )
            
            # Verificar limite
            strategy = self.strategies.get(rule.strategy)
            if not strategy:
                logger.error(f"Estratégia não encontrada: {rule.strategy}")
                continue
            
            status = await strategy.check_limit(key, rule)
            
            # Se excedeu limite e tem duração de bloqueio
            if not status.allowed and rule.block_duration_seconds:
                await self._block_key(key, rule)
            
            if not status.allowed:
                return False, status
        
        # Todas as regras passaram
        return True, None
    
    def _rule_applies(self, rule: RateLimitRule, request: Request) -> bool:
        """Verificar se regra se aplica à requisição"""
        # Verificar endpoints
        if rule.endpoints:
            path = request.url.path
            if not any(path.startswith(endpoint) for endpoint in rule.endpoints):
                return False
        
        # Verificar métodos
        if rule.methods:
            if request.method not in rule.methods:
                return False
        
        return True
    
    async def _get_scope_key(self, rule: RateLimitRule, request: Request) -> str:
        """Obter chave baseada no escopo"""
        if rule.custom_key_func:
            return await rule.custom_key_func(request)
        
        if rule.scope == RateLimitScope.GLOBAL:
            return "global"
        
        elif rule.scope == RateLimitScope.IP:
            # Obter IP real considerando proxies
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                ip = forwarded_for.split(",")[0].strip()
            else:
                ip = request.client.host if request.client else "unknown"
            return f"ip:{ip}"
        
        elif rule.scope == RateLimitScope.USER:
            # Obter ID do usuário autenticado
            if hasattr(request.state, "user") and request.state.user:
                return f"user:{request.state.user.get('id', 'unknown')}"
            return "user:anonymous"
        
        elif rule.scope == RateLimitScope.API_KEY:
            # Obter API key do header
            api_key = request.headers.get("X-API-Key", "")
            if api_key:
                # Hash da API key para privacidade
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
                return f"api_key:{key_hash}"
            return "api_key:none"
        
        elif rule.scope == RateLimitScope.ENDPOINT:
            # Combinar método e path
            return f"endpoint:{request.method}:{request.url.path}"
        
        return "unknown"
    
    def _is_whitelisted(self, key: str, rule: RateLimitRule) -> bool:
        """Verificar se chave está na whitelist"""
        if not rule.whitelist:
            return False
        
        # Extrair identificador da chave
        _, identifier = key.split(":", 1)
        return identifier in rule.whitelist
    
    def _is_blacklisted(self, key: str, rule: RateLimitRule) -> bool:
        """Verificar se chave está na blacklist"""
        if not rule.blacklist:
            return False
        
        # Extrair identificador da chave
        _, identifier = key.split(":", 1)
        return identifier in rule.blacklist
    
    def _is_blocked(self, key: str, rule: RateLimitRule) -> bool:
        """Verificar se chave está bloqueada temporariamente"""
        block_key = f"{rule.name}:{key}"
        if block_key in self.blocked_keys:
            if datetime.now() < self.blocked_keys[block_key]:
                return True
            else:
                # Remover bloqueio expirado
                del self.blocked_keys[block_key]
        return False
    
    async def _block_key(self, key: str, rule: RateLimitRule):
        """Bloquear chave temporariamente"""
        if rule.block_duration_seconds:
            block_key = f"{rule.name}:{key}"
            blocked_until = datetime.now() + timedelta(seconds=rule.block_duration_seconds)
            self.blocked_keys[block_key] = blocked_until
            
            # Salvar no Redis também
            redis_key = f"rate_limit:blocked:{block_key}"
            await self.redis.setex(
                redis_key,
                rule.block_duration_seconds,
                blocked_until.isoformat()
            )
            
            logger.warning(f"Chave bloqueada: {key} até {blocked_until}")
    
    async def get_usage_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Obter estatísticas de uso"""
        stats = {
            "rules": len(self.rules),
            "blocked_keys": len(self.blocked_keys),
            "usage_by_rule": {}
        }
        
        # Estatísticas por regra
        for rule_name, rule in self.rules.items():
            pattern = f"{self.key_prefix}:{rule_name}:*"
            keys = []
            
            # Buscar chaves
            async for key in self.redis.scan_iter(pattern):
                keys.append(key)
            
            stats["usage_by_rule"][rule_name] = {
                "limit": rule.limit,
                "window_seconds": rule.window_seconds,
                "strategy": rule.strategy.value,
                "active_keys": len(keys)
            }
        
        return stats


# Middleware FastAPI
class RateLimitMiddleware:
    """Middleware para aplicar rate limiting"""
    
    def __init__(self, app, rate_limit_manager: RateLimitManager):
        self.app = app
        self.manager = rate_limit_manager
    
    async def __call__(self, request: Request, call_next):
        # Verificar rate limit
        allowed, status = await self.manager.check_request(request)
        
        if not allowed and status:
            # Adicionar headers de rate limit
            headers = {
                "X-RateLimit-Limit": str(status.limit),
                "X-RateLimit-Remaining": str(status.remaining),
                "X-RateLimit-Reset": str(int(status.reset_at.timestamp()))
            }
            
            if status.retry_after:
                headers["Retry-After"] = str(status.retry_after)
            
            # Retornar erro 429
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "limit": status.limit,
                    "remaining": status.remaining,
                    "reset_at": status.reset_at.isoformat(),
                    "retry_after": status.retry_after
                }),
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
                media_type="application/json"
            )
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de rate limit na resposta
        if status:
            response.headers["X-RateLimit-Limit"] = str(status.limit)
            response.headers["X-RateLimit-Remaining"] = str(status.remaining)
            response.headers["X-RateLimit-Reset"] = str(int(status.reset_at.timestamp()))
        
        return response


# Configurações padrão
def create_default_rules() -> List[RateLimitRule]:
    """Criar regras padrão de rate limiting"""
    return [
        # Limite global por IP
        RateLimitRule(
            name="global_ip_limit",
            limit=100,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=RateLimitScope.IP
        ),
        
        # Limite para endpoints de autenticação
        RateLimitRule(
            name="auth_limit",
            limit=5,
            window_seconds=300,  # 5 tentativas em 5 minutos
            strategy=RateLimitStrategy.FIXED_WINDOW,
            scope=RateLimitScope.IP,
            endpoints=["/auth/login", "/auth/register"],
            block_duration_seconds=1800  # Bloquear por 30 minutos após exceder
        ),
        
        # Limite para API por usuário autenticado
        RateLimitRule(
            name="api_user_limit",
            limit=1000,
            window_seconds=3600,  # 1000 requisições por hora
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            scope=RateLimitScope.USER,
            burst_size=50,  # Permitir burst de 50 requisições
            endpoints=["/api/"]
        ),
        
        # Limite para downloads
        RateLimitRule(
            name="download_limit",
            limit=10,
            window_seconds=3600,  # 10 downloads por hora
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=RateLimitScope.USER,
            endpoints=["/download/", "/export/"]
        )
    ]


if __name__ == "__main__":
    # Exemplo de uso
    async def test_rate_limiter():
        # Criar gerenciador
        manager = RateLimitManager()
        await manager.initialize()
        
        # Adicionar regras
        for rule in create_default_rules():
            manager.add_rule(rule)
        
        # Simular requisições
        from fastapi import FastAPI
        from starlette.requests import Request
        from starlette.datastructures import Headers
        
        # Criar requisição fake
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [(b"host", b"localhost")],
            "server": ("localhost", 8000),
            "client": ("127.0.0.1", 50000),
            "scheme": "http"
        }
        
        # Testar múltiplas requisições
        for i in range(10):
            request = Request(scope)
            allowed, status = await manager.check_request(request)
            
            print(f"Requisição {i+1}: {'Permitida' if allowed else 'Bloqueada'}")
            if status:
                print(f"  Limite: {status.limit}")
                print(f"  Restante: {status.remaining}")
                print(f"  Reset em: {status.reset_at}")
                if status.retry_after:
                    print(f"  Tentar novamente em: {status.retry_after}s")
            
            await asyncio.sleep(0.1)
        
        # Estatísticas
        stats = await manager.get_usage_stats()
        print(f"\nEstatísticas: {json.dumps(stats, indent=2)}")
        
        await manager.close()
    
    # Executar teste
    asyncio.run(test_rate_limiter())