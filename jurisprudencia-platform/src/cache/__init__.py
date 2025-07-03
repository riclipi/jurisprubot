"""
Sistema de Cache Distribuído
"""

from .distributed_cache import (
    CacheStrategy,
    SerializationType,
    CacheEntry,
    CacheStats,
    CacheBackend,
    RedisBackend,
    DistributedCache,
    CacheCluster,
    create_distributed_cache
)

from .cache_strategies import (
    CacheItem,
    LRUCache,
    LFUCache,
    AdaptiveReplacementCache,
    RefreshAheadCache,
    TieredCache,
    PredictiveCache
)

__all__ = [
    # Core Cache
    'CacheStrategy',
    'SerializationType',
    'CacheEntry',
    'CacheStats',
    'CacheBackend',
    'RedisBackend',
    'DistributedCache',
    'CacheCluster',
    'create_distributed_cache',
    
    # Strategies
    'CacheItem',
    'LRUCache',
    'LFUCache',
    'AdaptiveReplacementCache',
    'RefreshAheadCache',
    'TieredCache',
    'PredictiveCache'
]