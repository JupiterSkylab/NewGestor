"""Sistema de cache avançado com múltiplas estratégias e otimizações."""

import time
import threading
import weakref
import pickle
import hashlib
import psutil
from typing import Any, Dict, List, Optional, Callable, Set, Union
from enum import Enum
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps


class CacheStrategy(Enum):
    """Estratégias de limpeza de cache."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Entrada individual do cache."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: Optional[float]
    size: int
    tags: Set[str]
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Atualiza último acesso."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Estatísticas do cache."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acerto do cache."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def memory_usage_mb(self) -> float:
        """Uso de memória em MB."""
        return self.memory_usage / (1024 * 1024)


class AdvancedCache:
    """Cache avançado com múltiplas estratégias e otimizações."""
    
    def __init__(self, 
                 max_size: int = 1000,
                 max_memory_mb: float = 100.0,
                 default_ttl: Optional[float] = None,
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 cleanup_interval: float = 60.0,
                 enable_stats: bool = True):
        
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.cleanup_interval = cleanup_interval
        self.enable_stats = enable_stats
        
        # Armazenamento principal
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Índices para diferentes estratégias
        self._lru_order = OrderedDict()  # key -> timestamp
        self._lfu_counts = {}  # key -> count
        self._fifo_order = []  # list of keys
        self._tags_index: Dict[str, Set[str]] = {}  # tag -> set of keys
        
        # Estatísticas
        self.stats = CacheStats() if enable_stats else None
        
        # Callbacks
        self._eviction_callbacks: List[Callable[[str, Any], None]] = []
        self._hit_callbacks: List[Callable[[str, Any], None]] = []
        self._miss_callbacks: List[Callable[[str], None]] = []
        
        # Thread de limpeza automática
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        if cleanup_interval > 0:
            self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Inicia thread de limpeza automática."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(self.cleanup_interval):
                try:
                    self._cleanup_expired()
                    self._enforce_memory_limit()
                except Exception as e:
                    print(f"Erro na limpeza do cache: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho aproximado do valor."""
        try:
            return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            # Fallback para estimativa simples
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v) 
                          for k, v in value.items())
            else:
                return 64  # Estimativa padrão
    
    def _generate_key(self, key: Union[str, tuple, list]) -> str:
        """Gera chave string a partir de diferentes tipos."""
        if isinstance(key, str):
            return key
        
        # Para outros tipos, criar hash
        key_str = str(key)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_access_patterns(self, key: str, entry: CacheEntry):
        """Atualiza padrões de acesso para diferentes estratégias."""
        current_time = time.time()
        
        # LRU: atualizar ordem
        if self.strategy == CacheStrategy.LRU:
            self._lru_order[key] = current_time
            self._lru_order.move_to_end(key)
        
        # LFU: incrementar contador
        elif self.strategy == CacheStrategy.LFU:
            self._lfu_counts[key] = self._lfu_counts.get(key, 0) + 1
    
    def _select_eviction_candidate(self) -> Optional[str]:
        """Seleciona candidato para remoção baseado na estratégia."""
        if not self._cache:
            return None
        
        if self.strategy == CacheStrategy.LRU:
            # Remover o menos recentemente usado
            return next(iter(self._lru_order))
        
        elif self.strategy == CacheStrategy.LFU:
            # Remover o menos frequentemente usado
            min_count = min(self._lfu_counts.values())
            for key, count in self._lfu_counts.items():
                if count == min_count and key in self._cache:
                    return key
        
        elif self.strategy == CacheStrategy.FIFO:
            # Remover o primeiro inserido
            return self._fifo_order[0] if self._fifo_order else None
        
        elif self.strategy == CacheStrategy.TTL:
            # Remover o mais antigo
            oldest_key = None
            oldest_time = float('inf')
            for key, entry in self._cache.items():
                if entry.created_at < oldest_time:
                    oldest_time = entry.created_at
                    oldest_key = key
            return oldest_key
        
        return None
    
    def _cleanup_expired(self):
        """Remove entradas expiradas."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove_entry(key, reason="expired")
    
    def _enforce_size_limit(self):
        """Garante que o cache não exceda o tamanho máximo."""
        with self._lock:
            while len(self._cache) > self.max_size:
                candidate = self._select_eviction_candidate()
                if candidate:
                    self._remove_entry(candidate, reason="size_limit")
                else:
                    break
    
    def _enforce_memory_limit(self):
        """Garante que o cache não exceda o limite de memória."""
        with self._lock:
            current_memory = sum(entry.size for entry in self._cache.values())
            
            while current_memory > self.max_memory_bytes and self._cache:
                candidate = self._select_eviction_candidate()
                if candidate:
                    entry = self._cache[candidate]
                    current_memory -= entry.size
                    self._remove_entry(candidate, reason="memory_limit")
                else:
                    break
    
    def _remove_entry(self, key: str, reason: str = "manual"):
        """Remove entrada do cache e limpa índices."""
        if key not in self._cache:
            return
        
        entry = self._cache[key]
        
        # Executar callbacks de remoção
        for callback in self._eviction_callbacks:
            try:
                callback(key, entry.value)
            except Exception as e:
                print(f"Erro no callback de remoção: {e}")
        
        # Remover dos índices
        self._lru_order.pop(key, None)
        self._lfu_counts.pop(key, None)
        if key in self._fifo_order:
            self._fifo_order.remove(key)
        
        # Remover das tags
        for tag in entry.tags:
            if tag in self._tags_index:
                self._tags_index[tag].discard(key)
                if not self._tags_index[tag]:
                    del self._tags_index[tag]
        
        # Remover entrada principal
        del self._cache[key]
        
        # Atualizar estatísticas
        if self.stats:
            self.stats.evictions += 1
            self.stats.memory_usage -= entry.size
            self.stats.entry_count -= 1
    
    def put(self, key: Union[str, tuple, list], value: Any, 
           ttl: Optional[float] = None, tags: Optional[Set[str]] = None) -> bool:
        """Adiciona item ao cache."""
        key_str = self._generate_key(key)
        
        with self._lock:
            # Calcular tamanho
            size = self._calculate_size(value)
            
            # Verificar se cabe na memória
            if size > self.max_memory_bytes:
                return False
            
            # Usar TTL padrão se não especificado
            if ttl is None:
                ttl = self.default_ttl
            
            # Criar entrada
            current_time = time.time()
            entry = CacheEntry(
                key=key_str,
                value=value,
                created_at=current_time,
                last_accessed=current_time,
                access_count=1,
                ttl=ttl,
                size=size,
                tags=tags or set()
            )
            
            # Remover entrada existente se houver
            if key_str in self._cache:
                self._remove_entry(key_str)
            
            # Adicionar nova entrada
            self._cache[key_str] = entry
            
            # Atualizar índices
            if self.strategy == CacheStrategy.LRU:
                self._lru_order[key_str] = current_time
            elif self.strategy == CacheStrategy.LFU:
                self._lfu_counts[key_str] = 1
            elif self.strategy == CacheStrategy.FIFO:
                self._fifo_order.append(key_str)
            
            # Atualizar índice de tags
            for tag in entry.tags:
                if tag not in self._tags_index:
                    self._tags_index[tag] = set()
                self._tags_index[tag].add(key_str)
            
            # Atualizar estatísticas
            if self.stats:
                self.stats.memory_usage += size
                self.stats.entry_count += 1
            
            # Aplicar limites
            self._enforce_size_limit()
            self._enforce_memory_limit()
            
            return True
    
    def get(self, key: Union[str, tuple, list], default: Any = None) -> Any:
        """Recupera item do cache."""
        key_str = self._generate_key(key)
        
        with self._lock:
            if key_str not in self._cache:
                # Cache miss
                if self.stats:
                    self.stats.misses += 1
                
                for callback in self._miss_callbacks:
                    try:
                        callback(key_str)
                    except Exception as e:
                        print(f"Erro no callback de miss: {e}")
                
                return default
            
            entry = self._cache[key_str]
            
            # Verificar expiração
            if entry.is_expired():
                self._remove_entry(key_str, reason="expired")
                if self.stats:
                    self.stats.misses += 1
                return default
            
            # Cache hit
            entry.touch()
            self._update_access_patterns(key_str, entry)
            
            if self.stats:
                self.stats.hits += 1
            
            for callback in self._hit_callbacks:
                try:
                    callback(key_str, entry.value)
                except Exception as e:
                    print(f"Erro no callback de hit: {e}")
            
            return entry.value
    
    def delete(self, key: Union[str, tuple, list]) -> bool:
        """Remove item do cache."""
        key_str = self._generate_key(key)
        
        with self._lock:
            if key_str in self._cache:
                self._remove_entry(key_str, reason="manual")
                return True
            return False
    
    def invalidate_by_tags(self, tags: Union[str, Set[str]]) -> int:
        """Invalida entradas por tags."""
        if isinstance(tags, str):
            tags = {tags}
        
        with self._lock:
            keys_to_remove = set()
            
            for tag in tags:
                if tag in self._tags_index:
                    keys_to_remove.update(self._tags_index[tag])
            
            for key in keys_to_remove:
                self._remove_entry(key, reason="tag_invalidation")
            
            return len(keys_to_remove)
    
    def clear(self):
        """Limpa todo o cache."""
        with self._lock:
            keys = list(self._cache.keys())
            for key in keys:
                self._remove_entry(key, reason="clear")
    
    def exists(self, key: Union[str, tuple, list]) -> bool:
        """Verifica se chave existe no cache."""
        key_str = self._generate_key(key)
        
        with self._lock:
            if key_str not in self._cache:
                return False
            
            entry = self._cache[key_str]
            if entry.is_expired():
                self._remove_entry(key_str, reason="expired")
                return False
            
            return True
    
    def keys(self) -> List[str]:
        """Retorna todas as chaves válidas."""
        with self._lock:
            valid_keys = []
            for key, entry in self._cache.items():
                if not entry.is_expired():
                    valid_keys.append(key)
                else:
                    self._remove_entry(key, reason="expired")
            return valid_keys
    
    def get_stats(self) -> Optional[CacheStats]:
        """Retorna estatísticas do cache."""
        if not self.stats:
            return None
        
        with self._lock:
            # Atualizar uso de memória atual
            self.stats.memory_usage = sum(entry.size for entry in self._cache.values())
            self.stats.entry_count = len(self._cache)
            return self.stats
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Retorna informações detalhadas de uso de memória."""
        with self._lock:
            total_size = sum(entry.size for entry in self._cache.values())
            process = psutil.Process()
            process_memory = process.memory_info().rss
            
            return {
                'cache_size_mb': total_size / (1024 * 1024),
                'cache_size_bytes': total_size,
                'process_memory_mb': process_memory / (1024 * 1024),
                'cache_percentage': (total_size / process_memory * 100) if process_memory > 0 else 0,
                'entry_count': len(self._cache),
                'average_entry_size': total_size / len(self._cache) if self._cache else 0
            }
    
    def add_eviction_callback(self, callback: Callable[[str, Any], None]):
        """Adiciona callback para remoções."""
        self._eviction_callbacks.append(callback)
    
    def add_hit_callback(self, callback: Callable[[str, Any], None]):
        """Adiciona callback para hits."""
        self._hit_callbacks.append(callback)
    
    def add_miss_callback(self, callback: Callable[[str], None]):
        """Adiciona callback para misses."""
        self._miss_callbacks.append(callback)
    
    def close(self):
        """Fecha o cache e para threads."""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5.0)
        
        self.clear()
    
    def __del__(self):
        """Destrutor para limpeza."""
        try:
            self.close()
        except Exception:
            pass


class QueryCache(AdvancedCache):
    """Cache especializado para consultas de banco de dados."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.query_stats = {}
    
    def cache_query(self, sql: str, params: tuple = (), ttl: Optional[float] = None) -> str:
        """Gera chave de cache para consulta SQL."""
        query_key = hashlib.md5(f"{sql}:{params}".encode()).hexdigest()
        return query_key
    
    def get_query(self, sql: str, params: tuple = (), default: Any = None) -> Any:
        """Recupera resultado de consulta do cache."""
        query_key = self.cache_query(sql, params)
        
        # Atualizar estatísticas de consulta
        if sql not in self.query_stats:
            self.query_stats[sql] = {'hits': 0, 'misses': 0}
        
        result = self.get(query_key, default)
        
        if result is not default:
            self.query_stats[sql]['hits'] += 1
        else:
            self.query_stats[sql]['misses'] += 1
        
        return result
    
    def put_query(self, sql: str, params: tuple, result: Any, 
                 ttl: Optional[float] = None, tags: Optional[Set[str]] = None) -> bool:
        """Armazena resultado de consulta no cache."""
        query_key = self.cache_query(sql, params)
        
        # Adicionar tags automáticas baseadas na consulta
        auto_tags = set()
        sql_lower = sql.lower()
        
        # Detectar tabelas mencionadas
        import re
        table_pattern = r'\b(?:from|join|update|into)\s+([a-zA-Z_][a-zA-Z0-9_]*)'  
        tables = re.findall(table_pattern, sql_lower)
        for table in tables:
            auto_tags.add(f"table:{table}")
        
        # Combinar com tags fornecidas
        if tags:
            auto_tags.update(tags)
        
        return self.put(query_key, result, ttl=ttl, tags=auto_tags)
    
    def invalidate_table(self, table_name: str) -> int:
        """Invalida cache de uma tabela específica."""
        return self.invalidate_by_tags(f"table:{table_name}")
    
    def get_query_stats(self) -> Dict[str, Dict[str, int]]:
        """Retorna estatísticas de consultas."""
        return self.query_stats.copy()


class CacheDecorator:
    """Decorador para cache de funções."""
    
    def __init__(self, cache: AdvancedCache, ttl: Optional[float] = None, 
                 tags: Optional[Set[str]] = None, key_func: Optional[Callable] = None):
        self.cache = cache
        self.ttl = ttl
        self.tags = tags
        self.key_func = key_func
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave de cache
            if self.key_func:
                cache_key = self.key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # Tentar recuperar do cache
            result = self.cache.get(cache_key)
            if result is not None:
                return result
            
            # Executar função e armazenar resultado
            result = func(*args, **kwargs)
            self.cache.put(cache_key, result, ttl=self.ttl, tags=self.tags)
            
            return result
        
        return wrapper


# Instância global de cache
_global_cache = None

def get_cache() -> AdvancedCache:
    """Retorna instância global do cache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = AdvancedCache(
            max_size=1000,
            max_memory_mb=50.0,
            strategy=CacheStrategy.LRU,
            cleanup_interval=300.0  # 5 minutos
        )
    return _global_cache


# Exemplo de uso
if __name__ == "__main__":
    # Criar cache
    cache = AdvancedCache(
        max_size=100,
        max_memory_mb=10.0,
        strategy=CacheStrategy.LRU,
        default_ttl=300.0  # 5 minutos
    )
    
    # Adicionar callbacks
    cache.add_eviction_callback(lambda k, v: print(f"Removido: {k}"))
    cache.add_hit_callback(lambda k, v: print(f"Hit: {k}"))
    
    # Usar cache
    cache.put("chave1", "valor1", tags={"grupo1"})
    cache.put("chave2", "valor2", tags={"grupo1", "grupo2"})
    
    print(cache.get("chave1"))  # Hit
    print(cache.get("chave3", "padrão"))  # Miss
    
    # Invalidar por tag
    cache.invalidate_by_tags("grupo1")
    
    # Ver estatísticas
    stats = cache.get_stats()
    if stats:
        print(f"Taxa de acerto: {stats.hit_rate:.2%}")
        print(f"Uso de memória: {stats.memory_usage_mb:.2f} MB")
    
    # Cache de consultas
    query_cache = QueryCache(max_size=50)
    
    # Simular consulta
    sql = "SELECT * FROM usuarios WHERE id = ?"
    params = (123,)
    
    # Primeira vez - miss
    result = query_cache.get_query(sql, params, [])
    if not result:
        result = [(123, "João", "joao@email.com")]  # Simular resultado
        query_cache.put_query(sql, params, result, ttl=600)
    
    # Segunda vez - hit
    result = query_cache.get_query(sql, params, [])
    print(f"Resultado: {result}")
    
    # Decorador de cache
    @CacheDecorator(cache, ttl=60)
    def operacao_custosa(x, y):
        import time
        time.sleep(0.1)  # Simular operação lenta
        return x * y + x ** y
    
    # Primeira chamada - lenta
    start = time.time()
    resultado = operacao_custosa(2, 3)
    print(f"Primeira chamada: {time.time() - start:.3f}s")
    
    # Segunda chamada - rápida (cache)
    start = time.time()
    resultado = operacao_custosa(2, 3)
    print(f"Segunda chamada: {time.time() - start:.3f}s")
    
    # Fechar caches
    cache.close()
    query_cache.close()