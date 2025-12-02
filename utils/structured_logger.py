"""Sistema de logging estruturado para MiniGestor TRAE.

Este módulo implementa um sistema de logging avançado com:
- Formatação estruturada (JSON)
- Diferentes níveis de log
- Rotação automática de arquivos
- Contexto de operações
- Métricas de performance
"""

import logging
import logging.handlers
import json
import time
import traceback
import threading
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from functools import wraps
from contextlib import contextmanager


@dataclass
class LogContext:
    """Contexto de logging."""
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredFormatter(logging.Formatter):
    """Formatador de logs estruturados em JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro de log em JSON estruturado."""
        # Dados básicos do log
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': threading.current_thread().name,
            'process': os.getpid()
        }
        
        # Adicionar contexto se disponível
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Adicionar dados extras
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        # Adicionar informações de exceção
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Adicionar métricas de performance se disponível
        if hasattr(record, 'performance'):
            log_data['performance'] = record.performance
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ContextualLogger:
    """Logger com contexto estruturado."""
    
    def __init__(self, name: str, context: Optional[LogContext] = None):
        self.logger = logging.getLogger(name)
        self.context = context
        self._local = threading.local()
    
    def _get_context(self) -> Optional[Dict[str, Any]]:
        """Obtém contexto atual."""
        # Contexto local da thread tem prioridade
        local_context = getattr(self._local, 'context', None)
        if local_context:
            return local_context.to_dict()
        
        # Contexto da instância
        if self.context:
            return self.context.to_dict()
        
        return None
    
    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None,
            performance: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log interno com contexto."""
        extra = {
            'context': self._get_context(),
            'extra_data': extra_data,
            'performance': performance
        }
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log de debug."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de informação."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro."""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico."""
        self._log(logging.CRITICAL, message, exc_info=True, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log de exceção."""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)
    
    @contextmanager
    def context_manager(self, context: LogContext):
        """Context manager para definir contexto temporário."""
        old_context = getattr(self._local, 'context', None)
        self._local.context = context
        try:
            yield self
        finally:
            self._local.context = old_context
    
    def with_context(self, **kwargs) -> 'ContextualLogger':
        """Cria novo logger com contexto adicional."""
        current_context = self.context.to_dict() if self.context else {}
        current_context.update(kwargs)
        
        new_context = LogContext(**current_context)
        return ContextualLogger(self.logger.name, new_context)


class PerformanceLogger:
    """Logger especializado para métricas de performance."""
    
    def __init__(self, logger: ContextualLogger):
        self.logger = logger
    
    @contextmanager
    def measure_time(self, operation: str, **context_kwargs):
        """Mede tempo de execução de uma operação."""
        start_time = time.time()
        context = LogContext(operation=operation, **context_kwargs)
        
        with self.logger.context_manager(context) as ctx_logger:
            ctx_logger.info(f"Iniciando operação: {operation}")
            
            try:
                yield ctx_logger
                
                # Sucesso
                duration = time.time() - start_time
                performance = {
                    'duration_seconds': duration,
                    'status': 'success'
                }
                
                ctx_logger.info(
                    f"Operação concluída: {operation}",
                    performance=performance
                )
                
            except Exception as e:
                # Erro
                duration = time.time() - start_time
                performance = {
                    'duration_seconds': duration,
                    'status': 'error',
                    'error_type': type(e).__name__
                }
                
                ctx_logger.error(
                    f"Erro na operação: {operation} - {str(e)}",
                    performance=performance
                )
                raise
    
    def log_database_query(self, sql: str, params: tuple, duration: float, 
                          rows_affected: int = 0):
        """Log específico para consultas de banco."""
        performance = {
            'duration_seconds': duration,
            'rows_affected': rows_affected,
            'query_type': sql.strip().split()[0].upper()
        }
        
        extra_data = {
            'sql': sql,
            'params': params
        }
        
        self.logger.info(
            f"Consulta SQL executada: {performance['query_type']}",
            extra_data=extra_data,
            performance=performance
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, 
                           duration: float = None):
        """Log específico para operações de cache."""
        extra_data = {
            'cache_key': key,
            'cache_hit': hit
        }
        
        performance = {}
        if duration is not None:
            performance['duration_seconds'] = duration
        
        message = f"Cache {operation}: {key}"
        if hit is not None:
            message += f" ({'HIT' if hit else 'MISS'})"
        
        self.logger.debug(
            message,
            extra_data=extra_data,
            performance=performance if performance else None
        )


def setup_logging(log_dir: str = "logs", 
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True) -> ContextualLogger:
    """Configura o sistema de logging estruturado."""
    
    # Criar diretório de logs se não existir
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatador estruturado
    formatter = StructuredFormatter()
    
    # Handler para arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "minigestor.log"),
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Handler para arquivo de erros
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "errors.log"),
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Handler para console (opcional)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(console_handler)
    
    # Retornar logger contextual principal
    return ContextualLogger("minigestor")


def logged_method(operation: str = None, log_args: bool = False, 
                 log_result: bool = False, log_performance: bool = True):
    """Decorador para logging automático de métodos."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determinar nome da operação
            op_name = operation or f"{func.__module__}.{func.__qualname__}"
            
            # Obter logger do objeto se disponível
            logger = None
            if args and hasattr(args[0], 'logger') and isinstance(args[0].logger, ContextualLogger):
                logger = args[0].logger
            else:
                logger = ContextualLogger(func.__module__)
            
            # Criar performance logger
            perf_logger = PerformanceLogger(logger)
            
            # Preparar contexto
            context_kwargs = {
                'component': func.__module__,
                'operation': op_name
            }
            
            # Log de argumentos se solicitado
            extra_data = {}
            if log_args:
                extra_data['args'] = str(args[1:])  # Pular self
                extra_data['kwargs'] = kwargs
            
            if log_performance:
                with perf_logger.measure_time(op_name, **context_kwargs) as ctx_logger:
                    if extra_data:
                        ctx_logger.debug(f"Executando {op_name}", extra_data=extra_data)
                    
                    result = func(*args, **kwargs)
                    
                    if log_result:
                        ctx_logger.debug(f"Resultado de {op_name}", 
                                       extra_data={'result': str(result)})
                    
                    return result
            else:
                context = LogContext(operation=op_name, **context_kwargs)
                with logger.context_manager(context) as ctx_logger:
                    if extra_data:
                        ctx_logger.debug(f"Executando {op_name}", extra_data=extra_data)
                    
                    result = func(*args, **kwargs)
                    
                    if log_result:
                        ctx_logger.debug(f"Resultado de {op_name}", 
                                       extra_data={'result': str(result)})
                    
                    return result
        
        return wrapper
    return decorator


# Logger global
_global_logger: Optional[ContextualLogger] = None


def get_logger(name: str = None) -> ContextualLogger:
    """Obtém logger contextual."""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = setup_logging()
    
    if name:
        return ContextualLogger(name)
    
    return _global_logger


def get_performance_logger(name: str = None) -> PerformanceLogger:
    """Obtém logger de performance."""
    logger = get_logger(name)
    return PerformanceLogger(logger)


if __name__ == "__main__":
    # Exemplo de uso
    logger = setup_logging(log_level="DEBUG")
    perf_logger = PerformanceLogger(logger)
    
    # Log simples
    logger.info("Aplicação iniciada")
    
    # Log com contexto
    context = LogContext(operation="test_operation", user_id="user123")
    with logger.context_manager(context) as ctx_logger:
        ctx_logger.info("Operação de teste iniciada")
        
        # Simular erro
        try:
            raise ValueError("Erro de teste")
        except ValueError:
            ctx_logger.exception("Erro capturado")
    
    # Log de performance
    with perf_logger.measure_time("operacao_lenta") as ctx_logger:
        import time
        time.sleep(0.1)
        ctx_logger.info("Operação concluída")
    
    # Usar decorador
    @logged_method("exemplo_funcao", log_args=True, log_performance=True)
    def exemplo_funcao(x, y):
        return x + y
    
    resultado = exemplo_funcao(2, 3)
    logger.info(f"Resultado final: {resultado}")