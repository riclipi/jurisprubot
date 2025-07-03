#!/usr/bin/env python3
"""
🎯 ESTRATÉGIAS AVANÇADAS DE CACHE
Implementações de diferentes estratégias de cache
"""

import asyncio
import time
import heapq
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
import logging

from .distributed_cache import CacheBackend, CacheEntry

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CacheItem:
    """Item no cache com metadados"""
    key: str
    value: Any
    size: int
    ttl: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 1
    priority: float = 0.0


class LRUCache:
    """Cache com política Least Recently Used"""
    
    def __init__(self, backend: CacheBackend, max_size: int = 1000):
        self.backend = backend
        self.max_size = max_size
        self.access_order = OrderedDict()
        self.cache_size = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor e atualizar ordem de acesso"""
        value = await self.backend.get(key)
        
        if value is not None:
            # Mover para o final (mais recente)
            if key in self.access_order:
                self.access_order.move_to_end(key)
            else:
                self.access_order[key] = time.time()
        
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir valor com política LRU"""
        # Verificar se precisa fazer eviction
        if len(self.access_order) >= self.max_size:
            await self._evict_lru()
        
        # Adicionar ao cache
        success = await self.backend.set(key, value, ttl)
        
        if success:
            self.access_order[key] = time.time()
            self.cache_size = len(self.access_order)
        
        return success
    
    async def _evict_lru(self):
        """Remover item menos recentemente usado"""
        if self.access_order:
            # Remover o primeiro (mais antigo)
            lru_key, _ = self.access_order.popitem(last=False)
            await self.backend.delete(lru_key)
            logger.info(f"LRU eviction: {lru_key}")


class LFUCache:
    """Cache com política Least Frequently Used"""
    
    def __init__(self, backend: CacheBackend, max_size: int = 1000):
        self.backend = backend
        self.max_size = max_size
        self.frequency_count = defaultdict(int)
        self.frequency_lists = defaultdict(OrderedDict)
        self.key_to_freq = {}
        self.min_frequency = 0
        self.cache_size = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor e atualizar frequência"""
        value = await self.backend.get(key)
        
        if value is not None:
            await self._update_frequency(key)
        
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir valor com política LFU"""
        # Verificar se precisa fazer eviction
        if self.cache_size >= self.max_size:
            await self._evict_lfu()
        
        # Adicionar ao cache
        success = await self.backend.set(key, value, ttl)
        
        if success:
            # Inicializar frequência
            self.frequency_count[key] = 1
            self.frequency_lists[1][key] = time.time()
            self.key_to_freq[key] = 1
            self.min_frequency = 1
            self.cache_size += 1
        
        return success
    
    async def _update_frequency(self, key: str):
        """Atualizar frequência de acesso"""
        if key not in self.key_to_freq:
            return
        
        freq = self.key_to_freq[key]
        
        # Remover da lista de frequência atual
        del self.frequency_lists[freq][key]
        if not self.frequency_lists[freq] and freq == self.min_frequency:
            self.min_frequency += 1
        
        # Adicionar à próxima frequência
        freq += 1
        self.frequency_count[key] = freq
        self.frequency_lists[freq][key] = time.time()
        self.key_to_freq[key] = freq
    
    async def _evict_lfu(self):
        """Remover item menos frequentemente usado"""
        if self.min_frequency in self.frequency_lists:
            freq_list = self.frequency_lists[self.min_frequency]
            if freq_list:
                # Remover o mais antigo da frequência mínima
                lfu_key, _ = freq_list.popitem(last=False)
                await self.backend.delete(lfu_key)
                
                del self.key_to_freq[lfu_key]
                del self.frequency_count[lfu_key]
                self.cache_size -= 1
                
                logger.info(f"LFU eviction: {lfu_key} (freq: {self.min_frequency})")


class AdaptiveReplacementCache:
    """Cache ARC (Adaptive Replacement Cache)"""
    
    def __init__(self, backend: CacheBackend, max_size: int = 1000):
        self.backend = backend
        self.max_size = max_size
        self.p = 0  # Target size for T1
        
        # Listas do algoritmo ARC
        self.t1 = OrderedDict()  # Recent cache entries
        self.t2 = OrderedDict()  # Frequent cache entries
        self.b1 = OrderedDict()  # Ghost entries recently evicted from T1
        self.b2 = OrderedDict()  # Ghost entries recently evicted from T2
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor com política ARC"""
        # Caso 1: Hit em T1 ou T2
        if key in self.t1:
            # Promover para T2
            self.t1.pop(key)
            self.t2[key] = time.time()
            value = await self.backend.get(key)
            return value
        
        elif key in self.t2:
            # Mover para o final de T2
            self.t2.move_to_end(key)
            value = await self.backend.get(key)
            return value
        
        # Caso 2: Hit em ghost lists
        elif key in self.b1:
            # Adaptar e mover para T2
            self.p = min(self.max_size, self.p + max(1, len(self.b2) / len(self.b1)))
            await self._replace(key, self.b1)
            
            value = await self.backend.get(key)
            if value is not None:
                self.t2[key] = time.time()
            return value
        
        elif key in self.b2:
            # Adaptar e mover para T2
            self.p = max(0, self.p - max(1, len(self.b1) / len(self.b2)))
            await self._replace(key, self.b2)
            
            value = await self.backend.get(key)
            if value is not None:
                self.t2[key] = time.time()
            return value
        
        # Caso 3: Miss completo
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir valor com política ARC"""
        # Se já existe, apenas atualizar
        if key in self.t1 or key in self.t2:
            return await self.backend.set(key, value, ttl)
        
        # Verificar espaço
        if len(self.t1) + len(self.t2) >= self.max_size:
            await self._replace(key, None)
        
        # Adicionar a T1
        success = await self.backend.set(key, value, ttl)
        if success:
            self.t1[key] = time.time()
        
        return success
    
    async def _replace(self, key: str, from_list: Optional[OrderedDict]):
        """Substituir entrada no cache"""
        if len(self.t1) + len(self.b1) == self.max_size:
            # Remover de B1
            if self.b1:
                self.b1.popitem(last=False)
        elif len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2) >= 2 * self.max_size:
            # Remover de B2
            if self.b2:
                self.b2.popitem(last=False)
        
        # Decidir de onde evictar
        if len(self.t1) > max(self.p, 1) and self.t1:
            # Evictar de T1
            old_key, _ = self.t1.popitem(last=False)
            self.b1[old_key] = time.time()
            await self.backend.delete(old_key)
        else:
            # Evictar de T2
            if self.t2:
                old_key, _ = self.t2.popitem(last=False)
                self.b2[old_key] = time.time()
                await self.backend.delete(old_key)


class RefreshAheadCache:
    """Cache que atualiza valores antes de expirar"""
    
    def __init__(self, backend: CacheBackend, refresh_threshold: float = 0.8):
        self.backend = backend
        self.refresh_threshold = refresh_threshold
        self.refresh_callbacks: Dict[str, Callable] = {}
        self.ttls: Dict[str, Tuple[float, int]] = {}  # key -> (created_at, ttl)
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor e verificar se precisa refresh"""
        value = await self.backend.get(key)
        
        if value is not None and key in self.ttls:
            created_at, ttl = self.ttls[key]
            age = time.time() - created_at
            
            # Verificar se está próximo de expirar
            if age > ttl * self.refresh_threshold:
                await self._schedule_refresh(key)
        
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  refresh_callback: Optional[Callable] = None) -> bool:
        """Definir valor com callback de refresh"""
        success = await self.backend.set(key, value, ttl)
        
        if success and ttl:
            self.ttls[key] = (time.time(), ttl)
            
            if refresh_callback:
                self.refresh_callbacks[key] = refresh_callback
        
        return success
    
    async def _schedule_refresh(self, key: str):
        """Agendar refresh do valor"""
        if key in self._refresh_tasks and not self._refresh_tasks[key].done():
            return  # Já está agendado
        
        if key in self.refresh_callbacks:
            self._refresh_tasks[key] = asyncio.create_task(self._refresh_value(key))
    
    async def _refresh_value(self, key: str):
        """Executar refresh do valor"""
        try:
            callback = self.refresh_callbacks.get(key)
            if callback:
                logger.info(f"Refreshing cache value for key: {key}")
                
                # Obter novo valor
                if asyncio.iscoroutinefunction(callback):
                    new_value = await callback()
                else:
                    new_value = callback()
                
                # Atualizar cache
                if key in self.ttls:
                    _, ttl = self.ttls[key]
                    await self.set(key, new_value, ttl, callback)
                    
        except Exception as e:
            logger.error(f"Error refreshing cache for key {key}: {e}")
        finally:
            # Limpar task
            if key in self._refresh_tasks:
                del self._refresh_tasks[key]


class TieredCache:
    """Cache em múltiplas camadas (L1, L2, L3...)"""
    
    def __init__(self, tiers: List[Tuple[CacheBackend, Dict[str, Any]]]):
        """
        tiers: Lista de tuplas (backend, config)
        config pode incluir: max_size, ttl_multiplier, etc
        """
        self.tiers = []
        for backend, config in tiers:
            self.tiers.append({
                'backend': backend,
                'config': config,
                'stats': {'hits': 0, 'misses': 0}
            })
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor percorrendo as camadas"""
        value = None
        hit_tier = -1
        
        # Procurar em cada camada
        for i, tier in enumerate(self.tiers):
            value = await tier['backend'].get(key)
            
            if value is not None:
                tier['stats']['hits'] += 1
                hit_tier = i
                break
            else:
                tier['stats']['misses'] += 1
        
        # Promover para camadas superiores se encontrado em camada inferior
        if value is not None and hit_tier > 0:
            for i in range(hit_tier):
                ttl = self._calculate_ttl(i, tier['config'].get('base_ttl', 300))
                await self.tiers[i]['backend'].set(key, value, ttl)
        
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Definir valor em todas as camadas apropriadas"""
        success = True
        
        for i, tier in enumerate(self.tiers):
            # Cada camada pode ter TTL diferente
            tier_ttl = self._calculate_ttl(i, ttl or tier['config'].get('base_ttl', 300))
            
            # Verificar se deve armazenar nesta camada
            if self._should_store_in_tier(i, value):
                result = await tier['backend'].set(key, value, tier_ttl)
                success = success and result
        
        return success
    
    def _calculate_ttl(self, tier_index: int, base_ttl: int) -> int:
        """Calcular TTL para cada camada"""
        # Camadas inferiores têm TTL maior
        multiplier = self.tiers[tier_index]['config'].get('ttl_multiplier', tier_index + 1)
        return int(base_ttl * multiplier)
    
    def _should_store_in_tier(self, tier_index: int, value: Any) -> bool:
        """Decidir se deve armazenar valor em determinada camada"""
        config = self.tiers[tier_index]['config']
        
        # Verificar tamanho mínimo
        min_size = config.get('min_value_size', 0)
        value_size = len(str(value).encode('utf-8'))
        
        if value_size < min_size:
            return False
        
        # Verificar tamanho máximo
        max_size = config.get('max_value_size', float('inf'))
        if value_size > max_size:
            return False
        
        return True
    
    def get_stats(self) -> List[Dict[str, Any]]:
        """Obter estatísticas de cada camada"""
        stats = []
        
        for i, tier in enumerate(self.tiers):
            tier_stats = tier['stats'].copy()
            total = tier_stats['hits'] + tier_stats['misses']
            
            if total > 0:
                tier_stats['hit_rate'] = tier_stats['hits'] / total
            else:
                tier_stats['hit_rate'] = 0.0
            
            stats.append({
                'tier': i,
                'stats': tier_stats,
                'config': tier['config']
            })
        
        return stats


class PredictiveCache:
    """Cache que prevê quais valores serão necessários"""
    
    def __init__(self, backend: CacheBackend, prediction_model: Optional[Any] = None):
        self.backend = backend
        self.prediction_model = prediction_model
        self.access_history: List[Tuple[str, float]] = []
        self.prefetch_queue: asyncio.Queue = asyncio.Queue()
        self._prefetch_task = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor e registrar acesso"""
        # Registrar acesso
        self.access_history.append((key, time.time()))
        
        # Limitar histórico
        if len(self.access_history) > 10000:
            self.access_history = self.access_history[-5000:]
        
        # Obter valor
        value = await self.backend.get(key)
        
        # Prever próximos acessos
        if value is not None:
            await self._predict_next_access(key)
        
        return value
    
    async def _predict_next_access(self, current_key: str):
        """Prever e pré-carregar próximos valores"""
        if not self.prediction_model:
            # Modelo simples baseado em padrões
            predictions = self._simple_prediction(current_key)
        else:
            # Usar modelo ML se disponível
            predictions = self.prediction_model.predict(current_key, self.access_history)
        
        # Adicionar à fila de prefetch
        for predicted_key, confidence in predictions:
            if confidence > 0.5:  # Threshold de confiança
                await self.prefetch_queue.put(predicted_key)
    
    def _simple_prediction(self, current_key: str) -> List[Tuple[str, float]]:
        """Predição simples baseada em padrões históricos"""
        predictions = []
        
        # Encontrar padrões sequenciais
        for i in range(len(self.access_history) - 1):
            if self.access_history[i][0] == current_key:
                next_key = self.access_history[i + 1][0]
                predictions.append((next_key, 0.7))  # Confiança fixa
        
        # Retornar únicos com maior confiança
        unique_predictions = {}
        for key, conf in predictions:
            if key not in unique_predictions or conf > unique_predictions[key]:
                unique_predictions[key] = conf
        
        return list(unique_predictions.items())[:5]  # Top 5
    
    async def start_prefetching(self, fetch_callback: Callable):
        """Iniciar processo de prefetching"""
        if self._prefetch_task is None or self._prefetch_task.done():
            self._prefetch_task = asyncio.create_task(
                self._prefetch_worker(fetch_callback)
            )
    
    async def _prefetch_worker(self, fetch_callback: Callable):
        """Worker para prefetching"""
        while True:
            try:
                key = await asyncio.wait_for(self.prefetch_queue.get(), timeout=60)
                
                # Verificar se já está no cache
                exists = await self.backend.exists(key)
                
                if not exists:
                    logger.info(f"Prefetching key: {key}")
                    
                    # Buscar valor
                    if asyncio.iscoroutinefunction(fetch_callback):
                        value = await fetch_callback(key)
                    else:
                        value = fetch_callback(key)
                    
                    # Armazenar no cache
                    if value is not None:
                        await self.backend.set(key, value, ttl=300)
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in prefetch worker: {e}")


if __name__ == "__main__":
    # Exemplo de uso
    async def test_strategies():
        from .distributed_cache import RedisBackend
        import redis.asyncio as redis
        
        # Criar backend
        redis_client = await redis.from_url("redis://localhost:6379")
        backend = RedisBackend(redis_client)
        
        print("=== Testando LRU Cache ===")
        lru = LRUCache(backend, max_size=3)
        
        # Adicionar itens
        await lru.set("a", "valor_a")
        await lru.set("b", "valor_b")
        await lru.set("c", "valor_c")
        
        # Acessar 'a' para torná-lo mais recente
        await lru.get("a")
        
        # Adicionar novo item (deve evictar 'b')
        await lru.set("d", "valor_d")
        
        # Verificar
        print(f"a: {await lru.get('a')}")  # Deve existir
        print(f"b: {await lru.get('b')}")  # Deve ser None (evicted)
        print(f"c: {await lru.get('c')}")  # Deve existir
        print(f"d: {await lru.get('d')}")  # Deve existir
        
        print("\n=== Testando Refresh-Ahead Cache ===")
        refresh_cache = RefreshAheadCache(backend, refresh_threshold=0.5)
        
        # Função de refresh
        async def get_current_time():
            return datetime.now().isoformat()
        
        # Definir com TTL curto
        await refresh_cache.set("time", await get_current_time(), ttl=10, 
                              refresh_callback=get_current_time)
        
        # Primeira leitura
        print(f"Time 1: {await refresh_cache.get('time')}")
        
        # Esperar um pouco
        await asyncio.sleep(6)
        
        # Segunda leitura (deve triggerar refresh)
        print(f"Time 2: {await refresh_cache.get('time')}")
        
        # Esperar refresh completar
        await asyncio.sleep(2)
        
        # Terceira leitura (deve ter valor atualizado)
        print(f"Time 3: {await refresh_cache.get('time')}")
    
    # Executar teste
    asyncio.run(test_strategies())