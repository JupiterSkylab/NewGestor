"""Otimizador de banco de dados com análise de performance e cache."""

import sqlite3
import threading
import time
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import logging


@dataclass
class QueryStats:
    """Estatísticas de uma consulta."""
    sql: str
    normalized_sql: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_executed: float = 0.0
    slow_queries: List[float] = field(default_factory=list)
    
    def add_execution(self, execution_time: float):
        """Adiciona uma execução às estatísticas."""
        self.execution_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.execution_count
        self.last_executed = time.time()
        
        # Registrar consultas lentas (> 100ms)
        if execution_time > 0.1:
            self.slow_queries.append(execution_time)
            # Manter apenas as 10 mais recentes
            if len(self.slow_queries) > 10:
                self.slow_queries.pop(0)
    
    def is_slow_query(self, threshold: float = 0.1) -> bool:
        """Verifica se é uma consulta lenta."""
        return self.avg_time > threshold


class ConnectionPool:
    """Pool de conexões SQLite otimizado."""
    
    def __init__(self, database_path: str, max_connections: int = 5):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connections = deque()
        self.active_connections = 0
        self.lock = threading.Lock()
        
        # Criar conexões iniciais
        for _ in range(min(2, max_connections)):
            conn = self._create_connection()
            if conn:
                self.connections.append(conn)
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Cria uma nova conexão otimizada."""
        try:
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Otimizações SQLite
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            conn.execute("PRAGMA optimize")
            
            conn.row_factory = sqlite3.Row
            return conn
            
        except Exception as e:
            logging.error(f"Erro ao criar conexão: {e}")
            return None
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Obtém uma conexão do pool."""
        with self.lock:
            if self.connections:
                conn = self.connections.popleft()
                self.active_connections += 1
                return conn
            
            # Criar nova conexão se possível
            if self.active_connections < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self.active_connections += 1
                    return conn
            
            return None
    
    def return_connection(self, conn: sqlite3.Connection):
        """Retorna uma conexão ao pool."""
        with self.lock:
            if conn and self.active_connections > 0:
                self.connections.append(conn)
                self.active_connections -= 1
    
    def close_all(self):
        """Fecha todas as conexões."""
        with self.lock:
            while self.connections:
                conn = self.connections.popleft()
                try:
                    conn.close()
                except Exception:
                    pass
            self.active_connections = 0


class QueryOptimizer:
    """Otimizador principal de consultas e banco de dados."""
    
    def __init__(self, database_path: str, enable_cache: bool = True):
        self.database_path = database_path
        self.enable_cache = enable_cache
        
        # Pool de conexões
        self.connection_pool = ConnectionPool(database_path)
        
        # Estatísticas de consultas
        self.query_stats: Dict[str, QueryStats] = {}
        self.stats_lock = threading.Lock()
        
        # Cache de resultados
        self.result_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = 300  # 5 minutos
        self.cache_lock = threading.Lock()
        
        # Configurações
        self.slow_query_threshold = 0.1  # 100ms
        self.cache_max_size = 1000
        
        # Índices recomendados
        self.recommended_indexes: Set[str] = set()
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def _normalize_query(self, sql: str) -> str:
        """Normaliza consulta SQL para agrupamento de estatísticas."""
        # Remover comentários
        sql = re.sub(r'--.*?\n', ' ', sql)
        sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        
        # Normalizar espaços
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # Substituir valores literais por placeholders
        sql = re.sub(r"'[^']*'", "?", sql)
        sql = re.sub(r'\b\d+\b', "?", sql)
        
        return sql.upper()
    
    def _generate_cache_key(self, sql: str, params: tuple = ()) -> str:
        """Gera chave de cache para consulta."""
        key_data = f"{sql}:{params}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Verifica se entrada do cache ainda é válida."""
        return time.time() - timestamp < self.cache_ttl
    
    def _clean_cache(self):
        """Remove entradas expiradas do cache."""
        with self.cache_lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.result_cache.items()
                if current_time - timestamp > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.result_cache[key]
    
    def _should_cache_query(self, sql: str) -> bool:
        """Determina se uma consulta deve ser cacheada."""
        sql_upper = sql.upper().strip()
        
        # Cachear apenas SELECTs
        if not sql_upper.startswith('SELECT'):
            return False
        
        # Não cachear consultas com funções temporais
        temporal_functions = ['NOW()', 'CURRENT_TIMESTAMP', 'DATETIME()', 'DATE()']
        for func in temporal_functions:
            if func in sql_upper:
                return False
        
        return True
    
    def execute_query(self, sql: str, params: tuple = (), 
                     use_cache: bool = None) -> List[sqlite3.Row]:
        """Executa consulta com otimizações e cache."""
        if use_cache is None:
            use_cache = self.enable_cache
        
        # Verificar cache primeiro
        if use_cache and self._should_cache_query(sql):
            cache_key = self._generate_cache_key(sql, params)
            
            with self.cache_lock:
                if cache_key in self.result_cache:
                    result, timestamp = self.result_cache[cache_key]
                    if self._is_cache_valid(timestamp):
                        self.logger.debug(f"Cache hit para consulta: {sql[:50]}...")
                        return result
        
        # Executar consulta
        start_time = time.time()
        conn = self.connection_pool.get_connection()
        
        if not conn:
            raise Exception("Não foi possível obter conexão do pool")
        
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            result = cursor.fetchall()
            
            execution_time = time.time() - start_time
            
            # Registrar estatísticas
            self._record_query_stats(sql, execution_time)
            
            # Armazenar no cache se apropriado
            if use_cache and self._should_cache_query(sql):
                with self.cache_lock:
                    # Limpar cache se muito grande
                    if len(self.result_cache) >= self.cache_max_size:
                        self._clean_cache()
                    
                    cache_key = self._generate_cache_key(sql, params)
                    self.result_cache[cache_key] = (result, time.time())
            
            return result
            
        finally:
            self.connection_pool.return_connection(conn)
    
    def execute_batch(self, operations: List[Tuple[str, tuple]]) -> List[Any]:
        """Executa múltiplas operações em lote."""
        conn = self.connection_pool.get_connection()
        if not conn:
            raise Exception("Não foi possível obter conexão do pool")
        
        results = []
        start_time = time.time()
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            for sql, params in operations:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                
                if sql.strip().upper().startswith('SELECT'):
                    results.append(cursor.fetchall())
                else:
                    results.append(cursor.rowcount)
            
            conn.commit()
            
            # Registrar estatísticas do lote
            total_time = time.time() - start_time
            self.logger.info(f"Lote de {len(operations)} operações executado em {total_time:.3f}s")
            
            return results
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.return_connection(conn)
    
    def _record_query_stats(self, sql: str, execution_time: float):
        """Registra estatísticas da consulta."""
        normalized_sql = self._normalize_query(sql)
        
        with self.stats_lock:
            if normalized_sql not in self.query_stats:
                self.query_stats[normalized_sql] = QueryStats(
                    sql=sql,
                    normalized_sql=normalized_sql
                )
            
            self.query_stats[normalized_sql].add_execution(execution_time)
            
            # Log de consultas lentas
            if execution_time > self.slow_query_threshold:
                self.logger.warning(
                    f"Consulta lenta detectada ({execution_time:.3f}s): {sql[:100]}..."
                )
    
    def invalidate_cache(self, pattern: str = None):
        """Invalida cache baseado em padrão."""
        with self.cache_lock:
            if pattern is None:
                self.result_cache.clear()
                self.logger.info("Cache completamente invalidado")
            else:
                # Invalidar chaves que correspondem ao padrão
                keys_to_remove = []
                for key in self.result_cache.keys():
                    # Aqui você pode implementar lógica mais sofisticada
                    # Por simplicidade, vamos usar substring
                    if pattern.lower() in key.lower():
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.result_cache[key]
                
                self.logger.info(f"Invalidadas {len(keys_to_remove)} entradas do cache")
    
    def optimize_database(self) -> Dict[str, Any]:
        """Executa otimizações no banco de dados."""
        conn = self.connection_pool.get_connection()
        if not conn:
            raise Exception("Não foi possível obter conexão do pool")
        
        optimization_results = {}
        
        try:
            start_time = time.time()
            
            # VACUUM para compactar banco
            self.logger.info("Executando VACUUM...")
            vacuum_start = time.time()
            conn.execute("VACUUM")
            optimization_results['vacuum_time'] = time.time() - vacuum_start
            
            # ANALYZE para atualizar estatísticas
            self.logger.info("Executando ANALYZE...")
            analyze_start = time.time()
            conn.execute("ANALYZE")
            optimization_results['analyze_time'] = time.time() - analyze_start
            
            # Verificar integridade
            self.logger.info("Verificando integridade...")
            integrity_start = time.time()
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            optimization_results['integrity_check'] = integrity_result
            optimization_results['integrity_time'] = time.time() - integrity_start
            
            # Otimizar configurações
            conn.execute("PRAGMA optimize")
            
            optimization_results['total_time'] = time.time() - start_time
            optimization_results['timestamp'] = time.time()
            
            self.logger.info(f"Otimização concluída em {optimization_results['total_time']:.3f}s")
            
            return optimization_results
            
        finally:
            self.connection_pool.return_connection(conn)
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analisa consultas lentas e sugere otimizações."""
        with self.stats_lock:
            slow_queries = []
            
            for normalized_sql, stats in self.query_stats.items():
                if stats.is_slow_query(self.slow_query_threshold):
                    analysis = {
                        'sql': stats.sql,
                        'normalized_sql': normalized_sql,
                        'avg_time': stats.avg_time,
                        'max_time': stats.max_time,
                        'execution_count': stats.execution_count,
                        'total_time': stats.total_time,
                        'suggestions': self._generate_optimization_suggestions(stats.sql)
                    }
                    slow_queries.append(analysis)
            
            # Ordenar por tempo médio decrescente
            slow_queries.sort(key=lambda x: x['avg_time'], reverse=True)
            
            return slow_queries
    
    def _generate_optimization_suggestions(self, sql: str) -> List[str]:
        """Gera sugestões de otimização para uma consulta."""
        suggestions = []
        sql_upper = sql.upper()
        
        # Verificar se há WHERE clause
        if 'WHERE' not in sql_upper:
            suggestions.append("Considere adicionar cláusula WHERE para filtrar resultados")
        
        # Verificar JOINs sem índices
        if 'JOIN' in sql_upper:
            suggestions.append("Verifique se há índices nas colunas de JOIN")
        
        # Verificar ORDER BY sem índices
        if 'ORDER BY' in sql_upper:
            suggestions.append("Considere criar índice nas colunas de ORDER BY")
        
        # Verificar SELECT *
        if 'SELECT *' in sql_upper:
            suggestions.append("Evite SELECT *, especifique apenas colunas necessárias")
        
        # Verificar subconsultas
        if sql_upper.count('SELECT') > 1:
            suggestions.append("Considere otimizar subconsultas ou usar JOINs")
        
        return suggestions
    
    def create_recommended_indexes(self) -> Dict[str, bool]:
        """Cria índices recomendados baseados nas consultas analisadas."""
        conn = self.connection_pool.get_connection()
        if not conn:
            raise Exception("Não foi possível obter conexão do pool")
        
        results = {}
        
        try:
            # Analisar consultas para recomendar índices
            index_recommendations = self._analyze_index_needs()
            
            for index_sql in index_recommendations:
                try:
                    conn.execute(index_sql)
                    results[index_sql] = True
                    self.logger.info(f"Índice criado: {index_sql}")
                except Exception as e:
                    results[index_sql] = False
                    self.logger.error(f"Erro ao criar índice {index_sql}: {e}")
            
            conn.commit()
            
        finally:
            self.connection_pool.return_connection(conn)
        
        return results
    
    def _analyze_index_needs(self) -> List[str]:
        """Analisa necessidades de índices baseado nas consultas."""
        index_recommendations = []
        
        with self.stats_lock:
            for stats in self.query_stats.values():
                if stats.is_slow_query() and stats.execution_count > 5:
                    # Análise simples para recomendar índices
                    sql = stats.sql.upper()
                    
                    # Extrair tabelas e colunas WHERE
                    where_match = re.search(r'WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)', sql)
                    if where_match:
                        where_clause = where_match.group(1)
                        
                        # Procurar por condições de igualdade
                        equality_matches = re.findall(r'(\w+)\s*=\s*\?', where_clause)
                        for column in equality_matches:
                            # Extrair nome da tabela (simplificado)
                            table_match = re.search(r'FROM\s+(\w+)', sql)
                            if table_match:
                                table = table_match.group(1)
                                index_name = f"idx_{table}_{column}"
                                index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"
                                
                                if index_sql not in index_recommendations:
                                    index_recommendations.append(index_sql)
        
        return index_recommendations
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório completo de performance."""
        with self.stats_lock:
            total_queries = sum(stats.execution_count for stats in self.query_stats.values())
            total_time = sum(stats.total_time for stats in self.query_stats.values())
            
            slow_queries = [stats for stats in self.query_stats.values() 
                          if stats.is_slow_query(self.slow_query_threshold)]
            
            # Top 10 consultas mais executadas
            most_executed = sorted(
                self.query_stats.values(),
                key=lambda x: x.execution_count,
                reverse=True
            )[:10]
            
            # Top 10 consultas mais lentas
            slowest_queries = sorted(
                self.query_stats.values(),
                key=lambda x: x.avg_time,
                reverse=True
            )[:10]
            
            with self.cache_lock:
                cache_stats = {
                    'size': len(self.result_cache),
                    'max_size': self.cache_max_size,
                    'hit_rate': 0  # Seria necessário implementar contadores
                }
            
            return {
                'summary': {
                    'total_queries': total_queries,
                    'total_execution_time': total_time,
                    'avg_query_time': total_time / total_queries if total_queries > 0 else 0,
                    'slow_queries_count': len(slow_queries),
                    'unique_queries': len(self.query_stats)
                },
                'slow_queries': [
                    {
                        'sql': stats.sql[:100] + '...' if len(stats.sql) > 100 else stats.sql,
                        'avg_time': stats.avg_time,
                        'execution_count': stats.execution_count,
                        'total_time': stats.total_time
                    }
                    for stats in slowest_queries
                ],
                'most_executed': [
                    {
                        'sql': stats.sql[:100] + '...' if len(stats.sql) > 100 else stats.sql,
                        'execution_count': stats.execution_count,
                        'avg_time': stats.avg_time
                    }
                    for stats in most_executed
                ],
                'cache_stats': cache_stats,
                'recommendations': self._generate_general_recommendations()
            }
    
    def _generate_general_recommendations(self) -> List[str]:
        """Gera recomendações gerais de otimização."""
        recommendations = []
        
        with self.stats_lock:
            slow_queries_count = len([s for s in self.query_stats.values() 
                                    if s.is_slow_query(self.slow_query_threshold)])
            
            if slow_queries_count > 0:
                recommendations.append(f"Há {slow_queries_count} consultas lentas que precisam de otimização")
            
            total_queries = sum(stats.execution_count for stats in self.query_stats.values())
            if total_queries > 1000:
                recommendations.append("Considere implementar paginação para consultas com muitos resultados")
            
            # Verificar uso de cache
            with self.cache_lock:
                if len(self.result_cache) < self.cache_max_size * 0.1:
                    recommendations.append("Cache está subutilizado, considere ajustar TTL")
        
        return recommendations
    
    def close(self):
        """Fecha o otimizador e libera recursos."""
        self.connection_pool.close_all()
        with self.cache_lock:
            self.result_cache.clear()
        with self.stats_lock:
            self.query_stats.clear()


# Decorador para otimização automática
def optimize_query(optimizer: QueryOptimizer = None, use_cache: bool = True):
    """Decorador para otimização automática de consultas."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Se não há otimizador, executar função normalmente
            if optimizer is None:
                return func(*args, **kwargs)
            
            # Tentar extrair SQL dos argumentos
            sql = None
            params = ()
            
            if args:
                sql = args[0]
                if len(args) > 1:
                    params = args[1] if isinstance(args[1], tuple) else (args[1],)
            
            if sql and isinstance(sql, str) and sql.strip().upper().startswith('SELECT'):
                # Usar otimizador
                return optimizer.execute_query(sql, params, use_cache=use_cache)
            else:
                # Executar função original
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Instância global
_global_optimizer = None

def get_optimizer(database_path: str = None) -> QueryOptimizer:
    """Retorna instância global do otimizador."""
    global _global_optimizer
    if _global_optimizer is None and database_path:
        _global_optimizer = QueryOptimizer(database_path)
    return _global_optimizer


# Exemplo de uso
if __name__ == "__main__":
    # Criar otimizador
    optimizer = QueryOptimizer("exemplo.db")
    
    # Executar algumas consultas
    try:
        # Consulta simples
        results = optimizer.execute_query("SELECT * FROM usuarios WHERE id = ?", (1,))
        print(f"Resultado: {len(results)} registros")
        
        # Consulta em lote
        operations = [
            ("SELECT COUNT(*) FROM usuarios", ()),
            ("SELECT * FROM usuarios WHERE ativo = ?", (1,)),
        ]
        batch_results = optimizer.execute_batch(operations)
        print(f"Lote executado: {len(batch_results)} operações")
        
        # Otimizar banco
        optimization_results = optimizer.optimize_database()
        print(f"Otimização concluída em {optimization_results['total_time']:.3f}s")
        
        # Analisar consultas lentas
        slow_queries = optimizer.analyze_slow_queries()
        print(f"Encontradas {len(slow_queries)} consultas lentas")
        
        # Gerar relatório
        report = optimizer.get_performance_report()
        print(f"Relatório: {report['summary']['total_queries']} consultas executadas")
        
        # Criar índices recomendados
        index_results = optimizer.create_recommended_indexes()
        print(f"Índices criados: {sum(index_results.values())}")
        
    except Exception as e:
        print(f"Erro: {e}")
    
    finally:
        optimizer.close()