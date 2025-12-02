import redis
import json
import hashlib
import os
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Инициализация Redis (опционально)
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Проверяем подключение
    redis_client.ping()
    REDIS_ENABLED = True
    print("✅ Redis connected successfully")
except Exception as e:
    print(f"⚠️  Redis not available: {e}. Caching disabled.")
    redis_client = None
    REDIS_ENABLED = False


def normalize_query(query: str) -> str:
    """
    Нормализация запроса для кэширования
    - lowercase
    - удаление лишних пробелов
    - trim
    """
    return ' '.join(query.lower().strip().split())


def get_cache_key(query: str, prefix: str = "search") -> str:
    """
    Генерация ключа кэша из запроса
    """
    normalized = normalize_query(query)
    hash_key = hashlib.md5(normalized.encode('utf-8')).hexdigest()
    return f"{prefix}:{hash_key}"


def get_cached_result(query: str) -> Optional[Any]:
    """
    Получить результат из кэша
    Returns: dict с результатами поиска или None
    """
    if not REDIS_ENABLED:
        return None

    try:
        cache_key = get_cache_key(query)
        cached_data = redis_client.get(cache_key)

        if cached_data:
            print(f"✅ Cache HIT for query: '{query[:50]}...'")
            return json.loads(cached_data)
        else:
            print(f"⚠️  Cache MISS for query: '{query[:50]}...'")
            return None
    except Exception as e:
        print(f"❌ Cache get error: {e}")
        return None


def set_cached_result(query: str, result: Any, ttl: int = 3600) -> bool:
    """
    Сохранить результат в кэш
    Args:
        query: поисковый запрос
        result: результаты поиска (будут сериализованы в JSON)
        ttl: время жизни кэша в секундах (по умолчанию 1 час)
    Returns: True если сохранено, False иначе
    """
    if not REDIS_ENABLED:
        return False

    try:
        cache_key = get_cache_key(query)
        serialized = json.dumps(result, ensure_ascii=False)
        redis_client.setex(cache_key, ttl, serialized)
        print(f"✅ Cached result for query: '{query[:50]}...' (TTL: {ttl}s)")
        return True
    except Exception as e:
        print(f"❌ Cache set error: {e}")
        return False


def invalidate_cache(pattern: str = "search:*") -> int:
    """
    Удалить все ключи кэша по паттерну
    Args:
        pattern: паттерн для удаления (например, "search:*")
    Returns: количество удаленных ключей
    """
    if not REDIS_ENABLED:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            print(f"✅ Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted
        return 0
    except Exception as e:
        print(f"❌ Cache invalidation error: {e}")
        return 0


def get_cache_stats() -> dict:
    """
    Получить статистику кэша
    """
    if not REDIS_ENABLED:
        return {
            "enabled": False,
            "message": "Redis caching is disabled"
        }

    try:
        info = redis_client.info("stats")
        search_keys = len(redis_client.keys("search:*"))

        return {
            "enabled": True,
            "total_keys": redis_client.dbsize(),
            "search_cache_keys": search_keys,
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(
                info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
            ) * 100
        }
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e)
        }
