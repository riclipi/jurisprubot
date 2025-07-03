#!/usr/bin/env python3
"""
💾 SISTEMA DE CACHE DISTRIBUÍDO
Cache de alto desempenho com suporte a múltiplas estratégias
"""

import asyncio
import json
import pickle
import hashlib
import time
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import redis.asyncio as redis
from redis.asyncio.lock import Lock
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy(Enum):
    """Estratégias de cache"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


class SerializationType(Enum):
    """Tipos de serialização"""
    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"
    BYTES = "bytes"


@dataclass
class CacheEntry:
    """Entrada no cache"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Estatísticas do cache"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    keys_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0


class CacheBackend:
    """Backend base para cache"""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    async def clear(self) -> bool:
        raise NotImplementedError
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        raise NotImplementedError


class RedisBackend(CacheBackend):
    """Backend Redis para cache distribuído"""
    
    def __init__(self, redis_client: redis.Redis, 
                 serialization: SerializationType = SerializationType.PICKLE):
        self.redis = redis_client
        self.serialization = serialization
    
    def _serialize(self, value: Any) -> bytes:
        """Serializar valor para armazenamento"""
        if self.serialization == SerializationType.JSON:
            return json.dumps(value).encode('utf-8')
        elif self.serialization == SerializationType.PICKLE:
            return pickle.dumps(value)
        elif self.serialization == SerializationType.STRING:
            return str(value).encode('utf-8')
        else:  # BYTES
            return value if isinstance(value, bytes) else str(value).encode('utf-8')
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserializar valor do armazenamento"""
        if data is None:
            return None
            
        if self.serialization == SerializationType.JSON:
            return json.loads(data.decode('utf-8'))
        elif self.serialization == SerializationType.PICKLE:
            return pickle.loads(data)
        elif self.serialization == SerializationType.STRING:
            return data.decode('utf-8')
        else:  # BYTES
            return data
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        try:
            data = await self.redis.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Erro ao obter do cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir valor no cache"""
        try:
            data = self._serialize(value)
            if ttl:
                return await self.redis.setex(key, ttl, data)
            else:
                return await self.redis.set(key, data)
        except Exception as e:
            logger.error(f"Erro ao definir no cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Deletar do cache"""
        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Erro ao deletar do cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Verificar se chave existe"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar existência: {e}")
            return False
    
    async def clear(self) -> bool:
        """Limpar todo o cache"""
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Obter múltiplos valores"""
        try:
            values = await self.redis.mget(keys)
            return {
                key: self._deserialize(value) 
                for key, value in zip(keys, values) 
                if value is not None
            }
        except Exception as e:
            logger.error(f"Erro ao obter múltiplos valores: {e}")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Definir múltiplos valores"""
        try:
            # Pipeline para eficiência
            async with self.redis.pipeline() as pipe:
                for key, value in mapping.items():
                    data = self._serialize(value)
                    if ttl:
                        pipe.setex(key, ttl, data)
                    else:
                        pipe.set(key, data)
                
                results = await pipe.execute()
                return all(results)
        except Exception as e:
            logger.error(f"Erro ao definir múltiplos valores: {e}")
            return False


class DistributedCache:
    """Sistema de cache distribuído principal"""
    
    def __init__(self, backend: CacheBackend, 
                 default_ttl: int = 3600,
                 namespace: str = "cache"):
        self.backend = backend
        self.default_ttl = default_ttl
        self.namespace = namespace
        self.stats = CacheStats()
        self._local_cache: Dict[str, Tuple[Any, float]] = {}  # Cache L1 local
        self._local_cache_ttl = 60  # 1 minuto
        self._lock_manager = {}
    
    def _make_key(self, key: str) -> str:
        """Criar chave com namespace"""
        return f"{self.namespace}:{key}"
    
    def _hash_key(self, key: str) -> str:
        """Hash de chave longa"""
        if len(key) > 250:  # Limite do Redis
            return hashlib.sha256(key.encode()).hexdigest()
        return key
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Obter valor do cache"""
        full_key = self._make_key(self._hash_key(key))
        
        # Verificar cache local primeiro (L1)
        if full_key in self._local_cache:
            value, expiry = self._local_cache[full_key]
            if time.time() < expiry:
                self.stats.hits += 1
                return value
            else:
                del self._local_cache[full_key]
        
        # Buscar do backend (L2)
        value = await self.backend.get(full_key)
        
        if value is not None:
            self.stats.hits += 1
            # Atualizar cache local
            self._local_cache[full_key] = (value, time.time() + self._local_cache_ttl)
            return value
        else:
            self.stats.misses += 1
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  tags: Optional[List[str]] = None) -> bool:
        """Definir valor no cache"""
        full_key = self._make_key(self._hash_key(key))
        ttl = ttl or self.default_ttl
        
        # Salvar no backend
        success = await self.backend.set(full_key, value, ttl)
        
        if success:
            self.stats.sets += 1
            # Atualizar cache local
            self._local_cache[full_key] = (value, time.time() + min(ttl, self._local_cache_ttl))
            
            # Salvar tags se fornecidas
            if tags:
                await self._save_tags(key, tags)
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Deletar do cache"""
        full_key = self._make_key(self._hash_key(key))
        
        # Remover do cache local
        if full_key in self._local_cache:
            del self._local_cache[full_key]
        
        # Remover do backend
        success = await self.backend.delete(full_key)
        
        if success:
            self.stats.deletes += 1
        
        return success
    
    async def get_or_set(self, key: str, func: Callable[[], T], 
                        ttl: Optional[int] = None) -> T:
        """Obter do cache ou calcular e armazenar"""
        value = await self.get(key)
        
        if value is None:
            # Usar lock para evitar stampede
            async with self.lock(f"compute:{key}", timeout=30):
                # Verificar novamente após obter o lock
                value = await self.get(key)
                
                if value is None:
                    # Calcular valor
                    if asyncio.iscoroutinefunction(func):
                        value = await func()
                    else:
                        value = func()
                    
                    # Armazenar no cache
                    await self.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidar chaves por padrão"""
        count = 0
        
        # Limpar cache local
        keys_to_remove = [k for k in self._local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self._local_cache[key]
            count += 1
        
        # TODO: Implementar invalidação por padrão no backend
        return count
    
    async def invalidate_tags(self, tags: List[str]) -> int:
        """Invalidar chaves por tags"""
        count = 0
        
        for tag in tags:
            tag_key = f"{self.namespace}:tags:{tag}"
            keys = await self.backend.get(tag_key)
            
            if keys:
                for key in keys:
                    if await self.delete(key):
                        count += 1
                
                await self.backend.delete(tag_key)
        
        return count
    
    async def _save_tags(self, key: str, tags: List[str]):
        """Salvar associação de tags"""
        for tag in tags:
            tag_key = f"{self.namespace}:tags:{tag}"
            existing = await self.backend.get(tag_key) or []
            
            if key not in existing:
                existing.append(key)
                await self.backend.set(tag_key, existing, 86400)  # 24 horas
    
    @asynccontextmanager
    async def lock(self, name: str, timeout: int = 10):
        """Lock distribuído para operações críticas"""
        if hasattr(self.backend, 'redis'):
            lock_key = f"{self.namespace}:lock:{name}"
            lock = Lock(self.backend.redis, lock_key, timeout=timeout)
            
            try:
                await lock.acquire()
                yield lock
            finally:
                try:
                    await lock.release()
                except:
                    pass
        else:
            # Sem suporte a lock, apenas yield
            yield None
    
    def cache(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None,
             tags: Optional[List[str]] = None):
        """Decorator para cache de funções"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Gerar chave
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Chave padrão baseada em função e argumentos
                    key_parts = [func.__module__, func.__name__]
                    if args:
                        key_parts.extend(str(arg) for arg in args)
                    if kwargs:
                        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)
                
                # Buscar ou calcular
                return await self.get_or_set(
                    cache_key,
                    lambda: func(*args, **kwargs),
                    ttl=ttl
                )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Versão síncrona
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    key_parts = [func.__module__, func.__name__]
                    if args:
                        key_parts.extend(str(arg) for arg in args)
                    if kwargs:
                        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)
                
                # Para funções síncronas, usar asyncio.run
                return asyncio.run(self.get_or_set(
                    cache_key,
                    lambda: func(*args, **kwargs),
                    ttl=ttl
                ))
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    async def warm_up(self, keys: List[Tuple[str, Callable]], parallel: int = 10):
        """Aquecer cache com valores pré-calculados"""
        semaphore = asyncio.Semaphore(parallel)
        
        async def warm_key(key: str, func: Callable):
            async with semaphore:
                value = await self.get(key)
                if value is None:
                    if asyncio.iscoroutinefunction(func):
                        value = await func()
                    else:
                        value = func()
                    
                    await self.set(key, value)
        
        tasks = [warm_key(key, func) for key, func in keys]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'hit_rate': f"{self.stats.hit_rate:.2%}",
            'sets': self.stats.sets,
            'deletes': self.stats.deletes,
            'evictions': self.stats.evictions,
            'local_cache_size': len(self._local_cache)
        }
    
    async def clear(self) -> bool:
        """Limpar todo o cache"""
        self._local_cache.clear()
        self.stats = CacheStats()
        return await self.backend.clear()


class CacheCluster:
    """Cluster de cache com sharding"""
    
    def __init__(self, nodes: List[CacheBackend], 
                 replication_factor: int = 1):
        self.nodes = nodes
        self.replication_factor = replication_factor
        self.ring_size = 150  # Pontos virtuais por nó
        self._hash_ring = self._build_hash_ring()
    
    def _build_hash_ring(self) -> List[Tuple[int, int]]:
        """Construir anel de hash consistente"""
        ring = []
        
        for node_idx, node in enumerate(self.nodes):
            for i in range(self.ring_size):
                virtual_key = f"{node_idx}:{i}"
                hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                ring.append((hash_value, node_idx))
        
        return sorted(ring)
    
    def _get_node(self, key: str) -> int:
        """Obter nó responsável pela chave"""
        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # Busca binária no anel
        left, right = 0, len(self._hash_ring) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if self._hash_ring[mid][0] == key_hash:
                return self._hash_ring[mid][1]
            elif self._hash_ring[mid][0] < key_hash:
                left = mid + 1
            else:
                right = mid - 1
        
        # Se não encontrou exato, usar o próximo
        return self._hash_ring[left % len(self._hash_ring)][1]
    
    def _get_replicas(self, key: str) -> List[int]:
        """Obter nós de réplica"""
        primary = self._get_node(key)
        replicas = [primary]
        
        # Adicionar réplicas
        for i in range(1, self.replication_factor):
            replica_idx = (primary + i) % len(self.nodes)
            if replica_idx not in replicas:
                replicas.append(replica_idx)
        
        return replicas
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter do cluster"""
        replicas = self._get_replicas(key)
        
        # Tentar obter de qualquer réplica
        for node_idx in replicas:
            try:
                value = await self.nodes[node_idx].get(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning(f"Erro ao obter do nó {node_idx}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir no cluster"""
        replicas = self._get_replicas(key)
        
        # Definir em todas as réplicas
        results = []
        for node_idx in replicas:
            try:
                success = await self.nodes[node_idx].set(key, value, ttl)
                results.append(success)
            except Exception as e:
                logger.warning(f"Erro ao definir no nó {node_idx}: {e}")
                results.append(False)
        
        # Sucesso se pelo menos uma réplica foi atualizada
        return any(results)
    
    async def delete(self, key: str) -> bool:
        """Deletar do cluster"""
        replicas = self._get_replicas(key)
        
        # Deletar de todas as réplicas
        results = []
        for node_idx in replicas:
            try:
                success = await self.nodes[node_idx].delete(key)
                results.append(success)
            except Exception as e:
                logger.warning(f"Erro ao deletar do nó {node_idx}: {e}")
                results.append(False)
        
        return any(results)


# Função helper para criar cache
async def create_distributed_cache(redis_url: str = "redis://localhost:6379",
                                 **kwargs) -> DistributedCache:
    """Criar instância de cache distribuído"""
    redis_client = await redis.from_url(redis_url)
    backend = RedisBackend(redis_client, **kwargs)
    
    return DistributedCache(backend, **kwargs)


if __name__ == "__main__":
    # Exemplo de uso
    async def test_cache():
        # Criar cache
        cache = await create_distributed_cache()
        
        # Operações básicas
        print("=== Teste de operações básicas ===")
        
        # Set/Get
        await cache.set("user:123", {"name": "João", "age": 30}, ttl=300)
        user = await cache.get("user:123")
        print(f"Usuário: {user}")
        
        # Get com default
        missing = await cache.get("user:999", default={"name": "Unknown"})
        print(f"Usuário não encontrado: {missing}")
        
        # Delete
        await cache.delete("user:123")
        
        # Get or set
        async def expensive_computation():
            print("Calculando...")
            await asyncio.sleep(1)
            return {"result": 42}
        
        result1 = await cache.get_or_set("computation", expensive_computation, ttl=60)
        print(f"Resultado 1: {result1}")
        
        result2 = await cache.get_or_set("computation", expensive_computation, ttl=60)
        print(f"Resultado 2 (do cache): {result2}")
        
        # Usar decorator
        @cache.cache(ttl=120)
        async def fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return await fibonacci(n-1) + await fibonacci(n-2)
        
        print("\n=== Teste com decorator ===")
        start = time.time()
        fib10 = await fibonacci(10)
        print(f"Fibonacci(10) = {fib10} (tempo: {time.time()-start:.3f}s)")
        
        start = time.time()
        fib10_cached = await fibonacci(10)
        print(f"Fibonacci(10) cached = {fib10_cached} (tempo: {time.time()-start:.3f}s)")
        
        # Estatísticas
        print(f"\n=== Estatísticas ===")
        print(cache.get_stats())
        
        # Limpar
        await cache.clear()
    
    # Executar teste
    asyncio.run(test_cache())