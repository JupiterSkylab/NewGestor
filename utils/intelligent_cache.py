"""Sistema de cache inteligente para MiniGestor TRAE.

Este módulo implementa um cache específico para a aplicação, otimizando
operações frequentes como autocomplete, estatísticas e consultas de processos.
"""

import time
import threading
import hashlib
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass
from functools import wraps
from .advanced_cache import AdvancedCache, CacheStrategy, QueryCache
import logging


@dataclass
class CacheConfig:
    """Configuração do cache inteligente."""
    autocomplete_ttl: float = 300.0  # 5 minutos
    statistics_ttl: float = 600.0    # 10 minutos
    search_ttl: float = 180.0        # 3 minutos
    process_ttl: float = 900.0       # 15 minutos
    max_memory_mb: float = 50.0
    max_entries: int = 1000
    cleanup_interval: float = 120.0  # 2 minutos


class IntelligentCache:
    """Cache inteligente para operações da aplicação."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        
        # Cache principal para dados da aplicação
        self.app_cache = AdvancedCache(
            max_size=self.config.max_entries,
            max_memory_mb=self.config.max_memory_mb,
            strategy=CacheStrategy.LRU,
            cleanup_interval=self.config.cleanup_interval,
            enable_stats=True
        )
        
        # Cache específico para consultas SQL
        self.query_cache = QueryCache(
            max_size=500,
            max_memory_mb=20.0,
            strategy=CacheStrategy.LRU,
            cleanup_interval=self.config.cleanup_interval
        )
        
        # Controle de invalidação por dependências
        self.dependencies: Dict[str, Set[str]] = {
            'processos': set(),
            'lembretes': set(),
            'estatisticas': set(),
            'autocomplete': set()
        }
        
        # Callbacks para invalidação automática
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Configura callbacks para monitoramento."""
        self.app_cache.add_eviction_callback(self._on_eviction)
        self.app_cache.add_hit_callback(self._on_hit)
        self.app_cache.add_miss_callback(self._on_miss)
    
    def _on_eviction(self, key: str, value: Any):
        """Callback executado quando uma entrada é removida."""
        self.logger.debug(f"Cache eviction: {key}")
    
    def _on_hit(self, key: str, value: Any):
        """Callback executado em cache hit."""
        self.logger.debug(f"Cache hit: {key}")
    
    def _on_miss(self, key: str):
        """Callback executado em cache miss."""
        self.logger.debug(f"Cache miss: {key}")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Gera chave única para cache."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    # Métodos para cache de autocomplete
    def get_autocomplete(self, field: str, query: str = "") -> Optional[List[str]]:
        """Recupera dados de autocomplete do cache."""
        key = self._generate_key("autocomplete", field, query)
        return self.app_cache.get(key)
    
    def set_autocomplete(self, field: str, query: str, data: List[str]):
        """Armazena dados de autocomplete no cache."""
        key = self._generate_key("autocomplete", field, query)
        tags = {"autocomplete", f"autocomplete_{field}"}
        self.app_cache.put(key, data, ttl=self.config.autocomplete_ttl, tags=tags)
        self.dependencies['autocomplete'].add(key)
    
    # Métodos para cache de estatísticas
    def get_statistics(self, stat_type: str, **filters) -> Optional[Dict[str, Any]]:
        """Recupera estatísticas do cache."""
        key = self._generate_key("stats", stat_type, **filters)
        return self.app_cache.get(key)
    
    def set_statistics(self, stat_type: str, data: Dict[str, Any], **filters):
        """Armazena estatísticas no cache."""
        key = self._generate_key("stats", stat_type, **filters)
        tags = {"statistics", f"stats_{stat_type}"}
        self.app_cache.put(key, data, ttl=self.config.statistics_ttl, tags=tags)
        self.dependencies['estatisticas'].add(key)
    
    # Métodos para cache de processos
    def get_process(self, process_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Recupera processo do cache."""
        key = self._generate_key("process", process_id)
        return self.app_cache.get(key)
    
    def set_process(self, process_id: Union[int, str], data: Dict[str, Any]):
        """Armazena processo no cache."""
        key = self._generate_key("process", process_id)
        tags = {"processos", f"process_{process_id}"}
        self.app_cache.put(key, data, ttl=self.config.process_ttl, tags=tags)
        self.dependencies['processos'].add(key)
    
    def get_process_search(self, **filters) -> Optional[List[Dict[str, Any]]]:
        """Recupera resultados de busca do cache."""
        key = self._generate_key("search", **filters)
        return self.app_cache.get(key)
    
    def set_process_search(self, data: List[Dict[str, Any]], **filters):
        """Armazena resultados de busca no cache."""
        key = self._generate_key("search", **filters)
        tags = {"processos", "search"}
        self.app_cache.put(key, data, ttl=self.config.search_ttl, tags=tags)
        self.dependencies['processos'].add(key)
    
    # Métodos para cache de lembretes
    def get_reminders(self, **filters) -> Optional[List[Dict[str, Any]]]:
        """Recupera lembretes do cache."""
        key = self._generate_key("reminders", **filters)
        return self.app_cache.get(key)
    
    def set_reminders(self, data: List[Dict[str, Any]], **filters):
        """Armazena lembretes no cache."""
        key = self._generate_key("reminders", **filters)
        tags = {"lembretes", "reminders"}
        self.app_cache.put(key, data, ttl=self.config.process_ttl, tags=tags)
        self.dependencies['lembretes'].add(key)
    
    # Métodos para cache de consultas SQL
    def get_query_result(self, sql: str, params: tuple = ()) -> Optional[Any]:
        """Recupera resultado de consulta SQL do cache."""
        return self.query_cache.get_query(sql, params)
    
    def set_query_result(self, sql: str, params: tuple, result: Any, 
                        table_names: Optional[List[str]] = None):
        """Armazena resultado de consulta SQL no cache."""
        tags = set()
        if table_names:
            tags.update(f"table_{table}" for table in table_names)
        
        # Determina TTL baseado no tipo de consulta
        ttl = self.config.search_ttl
        if "COUNT" in sql.upper() or "SUM" in sql.upper():
            ttl = self.config.statistics_ttl
        elif "SELECT DISTINCT" in sql.upper():
            ttl = self.config.autocomplete_ttl
        
        self.query_cache.put_query(sql, params, result, ttl=ttl, tags=tags)
    
    # Métodos de invalidação
    def invalidate_processes(self):
        """Invalida cache relacionado a processos."""
        self.app_cache.invalidate_by_tags({"processos", "search"})
        self.query_cache.invalidate_table("trabalhos_realizados")
        self.dependencies['processos'].clear()
        self.logger.info("Cache de processos invalidado")
    
    def invalidate_reminders(self):
        """Invalida cache relacionado a lembretes."""
        self.app_cache.invalidate_by_tags({"lembretes", "reminders"})
        self.query_cache.invalidate_table("promessas")
        self.dependencies['lembretes'].clear()
        self.logger.info("Cache de lembretes invalidado")
    
    def invalidate_statistics(self):
        """Invalida cache de estatísticas."""
        self.app_cache.invalidate_by_tags({"statistics"})
        self.dependencies['estatisticas'].clear()
        self.logger.info("Cache de estatísticas invalidado")
    
    def invalidate_autocomplete(self, field: Optional[str] = None):
        """Invalida cache de autocomplete."""
        if field:
            self.app_cache.invalidate_by_tags({f"autocomplete_{field}"})
        else:
            self.app_cache.invalidate_by_tags({"autocomplete"})
            self.dependencies['autocomplete'].clear()
        self.logger.info(f"Cache de autocomplete invalidado: {field or 'todos'}")
    
    def invalidate_all(self):
        """Invalida todo o cache."""
        self.app_cache.clear()
        self.query_cache.clear()
        for dep_set in self.dependencies.values():
            dep_set.clear()
        self.logger.info("Todo o cache foi invalidado")
    
    # Métodos de monitoramento
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        app_stats = self.app_cache.get_stats()
        query_stats = self.query_cache.get_stats()
        
        return {
            'app_cache': {
                'hit_rate': app_stats.hit_rate if app_stats else 0,
                'memory_usage_mb': app_stats.memory_usage_mb if app_stats else 0,
                'entry_count': app_stats.entry_count if app_stats else 0,
                'hits': app_stats.hits if app_stats else 0,
                'misses': app_stats.misses if app_stats else 0
            },
            'query_cache': {
                'hit_rate': query_stats.hit_rate if query_stats else 0,
                'memory_usage_mb': query_stats.memory_usage_mb if query_stats else 0,
                'entry_count': query_stats.entry_count if query_stats else 0,
                'hits': query_stats.hits if query_stats else 0,
                'misses': query_stats.misses if query_stats else 0
            },
            'dependencies': {k: len(v) for k, v in self.dependencies.items()}
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Retorna uso de memória detalhado."""
        app_memory = self.app_cache.get_memory_usage()
        query_memory = self.query_cache.get_memory_usage()
        
        return {
            'app_cache_mb': app_memory.get('total_mb', 0),
            'query_cache_mb': query_memory.get('total_mb', 0),
            'total_mb': app_memory.get('total_mb', 0) + query_memory.get('total_mb', 0)
        }
    
    def close(self):
        """Fecha o cache e libera recursos."""
        self.app_cache.close()
        self.query_cache.close()
        self.logger.info("Cache inteligente fechado")
    
    def __del__(self):
        """Destrutor para garantir limpeza."""
        try:
            self.close()
        except:
            pass


# Decorador para cache automático
def cached_method(cache_type: str = "general", ttl: Optional[float] = None, 
                 invalidate_on: Optional[List[str]] = None):
    """Decorador para cache automático de métodos.
    
    Args:
        cache_type: Tipo de cache (autocomplete, statistics, search, process)
        ttl: Time to live em segundos
        invalidate_on: Lista de eventos que invalidam este cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Verifica se o objeto tem cache inteligente
            if not hasattr(self, '_intelligent_cache'):
                return func(self, *args, **kwargs)
            
            cache: IntelligentCache = self._intelligent_cache
            
            # Gera chave baseada na função e argumentos
            key = cache._generate_key(f"{func.__name__}_{cache_type}", *args, **kwargs)
            
            # Tenta recuperar do cache
            result = cache.app_cache.get(key)
            if result is not None:
                return result
            
            # Executa função e armazena resultado
            result = func(self, *args, **kwargs)
            
            # Determina TTL
            if ttl is None:
                if cache_type == "autocomplete":
                    ttl = cache.config.autocomplete_ttl
                elif cache_type == "statistics":
                    ttl = cache.config.statistics_ttl
                elif cache_type == "search":
                    ttl = cache.config.search_ttl
                else:
                    ttl = cache.config.process_ttl
            
            # Armazena no cache
            tags = {cache_type}
            if invalidate_on:
                tags.update(invalidate_on)
            
            cache.app_cache.put(key, result, ttl=ttl, tags=tags)
            
            return result
        return wrapper
    return decorator


# Instância global do cache
_global_intelligent_cache: Optional[IntelligentCache] = None


def get_intelligent_cache() -> IntelligentCache:
    """Retorna instância global do cache inteligente."""
    global _global_intelligent_cache
    if _global_intelligent_cache is None:
        _global_intelligent_cache = IntelligentCache()
    return _global_intelligent_cache


def close_intelligent_cache():
    """Fecha a instância global do cache."""
    global _global_intelligent_cache
    if _global_intelligent_cache is not None:
        _global_intelligent_cache.close()
        _global_intelligent_cache = None