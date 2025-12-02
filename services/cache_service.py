# -*- coding: utf-8 -*-
"""
Serviço de Cache para o Gestor de Processos
Implementa cache em memória com TTL e funcionalidades avançadas
"""

import time
import threading
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime, timedelta
from config import CACHE_CONFIG
from logger_config import log_performance, log_error

class CacheService:
    """Serviço de cache thread-safe com TTL e estatísticas avançadas"""
    
    def __init__(self, max_size: int = None, default_ttl: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size or CACHE_CONFIG.get('max_cache_size', 1000)
        self._default_ttl = default_ttl
        self._lock = threading.RLock()  # Thread-safe
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'cleanups': 0
        }
        
        # Auto-cleanup em background
        self._cleanup_interval = 300  # 5 minutos
        self._last_cleanup = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Recupera um valor do cache se ainda estiver válido"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Verifica se o cache expirou
            if current_time > entry['expires_at']:
                del self._cache[key]
                self._stats['misses'] += 1
                return default
            
            # Atualiza estatísticas de acesso
            entry['last_accessed'] = current_time
            entry['access_count'] += 1
            self._stats['hits'] += 1
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Armazena um valor no cache com TTL especificado"""
        with self._lock:
            current_time = time.time()
            ttl = ttl or self._default_ttl
            
            # Auto-cleanup se necessário
            self._auto_cleanup()
            
            # Remove entradas antigas se o cache estiver cheio
            if len(self._cache) >= self._max_size:
                self._cleanup_old_entries()
            
            self._cache[key] = {
                'value': value,
                'created_at': current_time,
                'expires_at': current_time + ttl,
                'last_accessed': current_time,
                'access_count': 0,
                'ttl': ttl
            }
            
            self._stats['sets'] += 1
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: int = None) -> Any:
        """Recupera do cache ou executa factory function e armazena o resultado"""
        value = self.get(key)
        if value is not None:
            return value
        
        # Executa factory function e armazena resultado
        try:
            start_time = time.time()
            value = factory()
            execution_time = time.time() - start_time
            
            self.set(key, value, ttl)
            
            # Log de performance para operações demoradas
            if execution_time > 1.0:  # Mais de 1 segundo
                log_performance(f"Cache factory function for key '{key}' took {execution_time:.2f}s")
            
            return value
        except Exception as e:
            log_error(f"Error executing cache factory function for key '{key}': {str(e)}")
            return None
    
    def invalidate(self, key: str) -> bool:
        """Remove uma entrada específica do cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['invalidations'] += 1
                return True
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Remove entradas que correspondem ao padrão (usando * como wildcard)"""
        with self._lock:
            import fnmatch
            keys_to_remove = []
            
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                self._stats['invalidations'] += 1
            
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats['invalidations'] += count
    
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe no cache e ainda é válida"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            current_time = time.time()
            
            if current_time > entry['expires_at']:
                del self._cache[key]
                return False
            
            return True
    
    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """Estende o TTL de uma entrada existente"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            current_time = time.time()
            
            if current_time > entry['expires_at']:
                del self._cache[key]
                return False
            
            entry['expires_at'] += additional_seconds
            return True
    
    def get_keys(self, pattern: str = None) -> List[str]:
        """Retorna lista de chaves válidas, opcionalmente filtradas por padrão"""
        with self._lock:
            current_time = time.time()
            valid_keys = []
            
            for key, entry in self._cache.items():
                if current_time <= entry['expires_at']:
                    if pattern is None:
                        valid_keys.append(key)
                    else:
                        import fnmatch
                        if fnmatch.fnmatch(key, pattern):
                            valid_keys.append(key)
            
            return valid_keys
    
    def _auto_cleanup(self) -> None:
        """Executa limpeza automática se necessário"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired_entries()
            self._last_cleanup = current_time
    
    def _cleanup_old_entries(self) -> None:
        """Remove entradas expiradas e menos acessadas"""
        current_time = time.time()
        
        # Remove entradas expiradas
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        # Se ainda estiver cheio, remove as menos acessadas
        if len(self._cache) >= self._max_size:
            # Ordena por score (combinação de último acesso e contagem de acessos)
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: (x[1]['last_accessed'] + x[1]['access_count'] * 60)  # Peso para acessos frequentes
            )
            
            # Remove 25% das entradas com menor score
            remove_count = max(1, len(sorted_entries) // 4)
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]
        
        self._stats['cleanups'] += 1
    
    def _cleanup_expired_entries(self) -> None:
        """Remove apenas entradas expiradas"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._stats['cleanups'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache"""
        with self._lock:
            current_time = time.time()
            valid_entries = 0
            expired_entries = 0
            total_access_count = 0
            oldest_entry = None
            newest_entry = None
            
            for entry in self._cache.values():
                total_access_count += entry['access_count']
                
                if current_time <= entry['expires_at']:
                    valid_entries += 1
                else:
                    expired_entries += 1
                
                # Encontra entrada mais antiga e mais nova
                if oldest_entry is None or entry['created_at'] < oldest_entry:
                    oldest_entry = entry['created_at']
                
                if newest_entry is None or entry['created_at'] > newest_entry:
                    newest_entry = entry['created_at']
            
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_entries': len(self._cache),
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'max_size': self._max_size,
                'usage_percent': (len(self._cache) / self._max_size) * 100,
                'hit_rate': round(hit_rate, 2),
                'total_hits': self._stats['hits'],
                'total_misses': self._stats['misses'],
                'total_sets': self._stats['sets'],
                'total_invalidations': self._stats['invalidations'],
                'total_cleanups': self._stats['cleanups'],
                'total_access_count': total_access_count,
                'oldest_entry_age': (current_time - oldest_entry) if oldest_entry else 0,
                'newest_entry_age': (current_time - newest_entry) if newest_entry else 0,
                'last_cleanup': self._last_cleanup
            }
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Retorna informações detalhadas sobre uma entrada específica"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            return {
                'key': key,
                'created_at': datetime.fromtimestamp(entry['created_at']).isoformat(),
                'expires_at': datetime.fromtimestamp(entry['expires_at']).isoformat(),
                'last_accessed': datetime.fromtimestamp(entry['last_accessed']).isoformat(),
                'access_count': entry['access_count'],
                'ttl': entry['ttl'],
                'age_seconds': current_time - entry['created_at'],
                'remaining_ttl': max(0, entry['expires_at'] - current_time),
                'is_expired': current_time > entry['expires_at'],
                'value_type': type(entry['value']).__name__,
                'value_size': len(str(entry['value'])) if entry['value'] else 0
            }

# Instância global do cache
_cache_service = CacheService(
    max_size=CACHE_CONFIG.get('max_cache_size', 1000),
    default_ttl=CACHE_CONFIG.get('default_ttl', 3600)
)

# Funções de conveniência para compatibilidade com código existente
def get_cached_secretarias():
    """Recupera secretarias do cache ou None se não existir"""
    return _cache_service.get('secretarias_formatadas')

def set_cached_secretarias(secretarias):
    """Armazena secretarias no cache"""
    ttl = CACHE_CONFIG.get('ttl_secretarias', 3600)
    _cache_service.set('secretarias_formatadas', secretarias, ttl)

def get_cached_modalidades():
    """Recupera modalidades do cache ou None se não existir"""
    return _cache_service.get('modalidades_licitacao')

def set_cached_modalidades(modalidades):
    """Armazena modalidades no cache"""
    ttl = CACHE_CONFIG.get('ttl_modalidades', 3600)
    _cache_service.set('modalidades_licitacao', modalidades, ttl)

def get_cached_nomes_autocomplete():
    """Recupera nomes para autocomplete do cache"""
    return _cache_service.get('nomes_autocomplete')

def set_cached_nomes_autocomplete(nomes):
    """Armazena nomes para autocomplete no cache"""
    _cache_service.set('nomes_autocomplete', nomes, 1800)  # 30 minutos

def get_cached_count_concluidos():
    """Recupera contagem de processos concluídos do cache"""
    return _cache_service.get('count_concluidos')

def set_cached_count_concluidos(count):
    """Armazena contagem de processos concluídos no cache"""
    _cache_service.set('count_concluidos', count, 1800)  # 30 minutos

def get_cached_count_andamento():
    """Recupera contagem de processos em andamento do cache"""
    return _cache_service.get('count_andamento')

def set_cached_count_andamento(count):
    """Armazena contagem de processos em andamento no cache"""
    _cache_service.set('count_andamento', count, 1800)  # 30 minutos

# Funções para acesso direto ao serviço
def get_cache_service() -> CacheService:
    """Retorna a instância do serviço de cache"""
    return _cache_service

def invalidate_process_caches():
    """Invalida todos os caches relacionados a processos"""
    _cache_service.invalidate_pattern('count_*')
    _cache_service.invalidate('nomes_autocomplete')

def get_cache_stats():
    """Retorna estatísticas do cache"""
    return _cache_service.get_stats()