"""Sistema de logging estruturado avançado."""

import json
import logging
import threading
import queue
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum


class LogLevel(Enum):
    """Níveis de log personalizados."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    PERFORMANCE = 25
    SECURITY = 45


class LogContext:
    """Contexto thread-local para logging."""
    
    def __init__(self):
        self._local = threading.local()
    
    def bind(self, **kwargs):
        """Vincula dados ao contexto atual."""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        self._local.context.update(kwargs)
    
    def unbind(self, *keys):
        """Remove chaves do contexto."""
        if hasattr(self._local, 'context'):
            for key in keys:
                self._local.context.pop(key, None)
    
    def clear(self):
        """Limpa todo o contexto."""
        if hasattr(self._local, 'context'):
            self._local.context.clear()
    
    def get_context(self) -> Dict[str, Any]:
        """Retorna o contexto atual."""
        if hasattr(self._local, 'context'):
            return self._local.context.copy()
        return {}


class LogMetrics:
    """Coleta métricas de logging."""
    
    def __init__(self):
        self.counters = {}
        self.timers = {}
        self.lock = threading.Lock()
    
    def increment(self, metric: str, value: int = 1):
        """Incrementa um contador."""
        with self.lock:
            self.counters[metric] = self.counters.get(metric, 0) + value
    
    def time_operation(self, operation: str, duration: float):
        """Registra tempo de operação."""
        with self.lock:
            if operation not in self.timers:
                self.timers[operation] = []
            self.timers[operation].append(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas coletadas."""
        with self.lock:
            return {
                'counters': self.counters.copy(),
                'timers': {
                    op: {
                        'count': len(times),
                        'total': sum(times),
                        'avg': sum(times) / len(times) if times else 0,
                        'min': min(times) if times else 0,
                        'max': max(times) if times else 0
                    }
                    for op, times in self.timers.items()
                }
            }


class StructuredFormatter(logging.Formatter):
    """Formatador para logs estruturados em JSON."""
    
    def __init__(self, include_extra=True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record):
        """Formata o registro como JSON estruturado."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.threadName,
            'process': record.process
        }
        
        # Adicionar contexto extra
        if self.include_extra:
            extra = {}
            
            # Adicionar campos extras do record
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }:
                    extra[key] = value
            
            log_data['extra'] = extra
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class AsyncLogHandler(logging.Handler):
    """Handler assíncrono para melhor performance."""
    
    def __init__(self, handler, max_queue_size=1000):
        """Inicializa o handler assíncrono."""
        super().__init__()
        self.handler = handler
        self.queue = queue.Queue(maxsize=max_queue_size)
        self._stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def emit(self, record):
        """Adiciona registro à fila."""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # Se a fila estiver cheia, descarta o log mais antigo
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def _worker(self):
        """Worker thread que processa logs da fila."""
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=1.0)
                self.handler.emit(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Em caso de erro, tenta continuar
                print(f"Erro no AsyncLogHandler: {e}")
    
    def close(self):
        """Fecha o handler e para a thread worker."""
        self._stop_event.set()
        self.worker_thread.join(timeout=5.0)
        self.handler.close()
        super().close()


class StructuredLogger:
    """Logger estruturado principal."""
    
    def __init__(self, name: str = "structured_logger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.context = LogContext()
        self.metrics = LogMetrics()
        self._handlers = []
        
        # Adicionar níveis customizados
        for level in LogLevel:
            logging.addLevelName(level.value, level.name)
    
    def add_console_handler(self, level=logging.INFO, structured=True):
        """Adiciona handler para console."""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        
        # Usar handler assíncrono
        async_handler = AsyncLogHandler(handler)
        self.logger.addHandler(async_handler)
        self._handlers.append(async_handler)
        
        return async_handler
    
    def add_file_handler(self, filename: str, level=logging.DEBUG, 
                        structured=True, max_bytes=10*1024*1024, backup_count=5):
        """Adiciona handler para arquivo com rotação."""
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            filename, maxBytes=max_bytes, backupCount=backup_count
        )
        handler.setLevel(level)
        
        if structured:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        
        # Usar handler assíncrono
        async_handler = AsyncLogHandler(handler)
        self.logger.addHandler(async_handler)
        self._handlers.append(async_handler)
        
        return async_handler
    
    def bind(self, **kwargs):
        """Vincula contexto ao logger."""
        self.context.bind(**kwargs)
        return self
    
    def unbind(self, *keys):
        """Remove chaves do contexto."""
        self.context.unbind(*keys)
        return self
    
    def _log(self, level: int, message: str, **kwargs):
        """Método interno de logging."""
        # Adicionar contexto atual
        context = self.context.get_context()
        
        # Mesclar com kwargs fornecidos
        extra_data = {**context, **kwargs}
        
        # Incrementar métrica
        level_name = logging.getLevelName(level)
        self.metrics.increment(f"log_{level_name.lower()}")
        
        # Fazer log
        self.logger.log(level, message, extra=extra_data)
    
    def trace(self, message: str, **kwargs):
        """Log de trace."""
        self._log(LogLevel.TRACE.value, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug."""
        self._log(LogLevel.DEBUG.value, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de informação."""
        self._log(LogLevel.INFO.value, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso."""
        self._log(LogLevel.WARNING.value, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro."""
        self._log(LogLevel.ERROR.value, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico."""
        self._log(LogLevel.CRITICAL.value, message, **kwargs)
    
    def performance(self, message: str, duration: float = None, **kwargs):
        """Log de performance."""
        if duration is not None:
            kwargs['duration_ms'] = duration * 1000
            self.metrics.time_operation(message, duration)
        self._log(LogLevel.PERFORMANCE.value, message, **kwargs)
    
    def security(self, message: str, **kwargs):
        """Log de segurança."""
        self._log(LogLevel.SECURITY.value, message, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas coletadas."""
        return self.metrics.get_metrics()
    
    def close(self):
        """Fecha todos os handlers."""
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()


def logged(logger: StructuredLogger = None, level: str = "info", 
          include_args: bool = False, include_result: bool = False):
    """Decorador para logging automático de funções."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Log de entrada
            log_data = {'function': func_name, 'action': 'enter'}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)
            
            getattr(logger, level)(f"Entering {func_name}", **log_data)
            
            # Executar função com timing
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log de saída com sucesso
                log_data = {
                    'function': func_name, 
                    'action': 'exit',
                    'duration_ms': duration * 1000,
                    'status': 'success'
                }
                if include_result:
                    log_data['result'] = str(result)
                
                logger.performance(f"Completed {func_name}", duration, **log_data)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log de erro
                log_data = {
                    'function': func_name,
                    'action': 'error',
                    'duration_ms': duration * 1000,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
                
                logger.error(f"Error in {func_name}", **log_data)
                raise
        
        return wrapper
    return decorator


# Instância global
_global_logger = None

def get_logger(name: str = "app") -> StructuredLogger:
    """Retorna instância global do logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
        # Configuração padrão
        _global_logger.add_console_handler(level=logging.INFO, structured=False)
    return _global_logger


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logger
    logger = get_logger("test_logger")
    logger.add_file_handler("app.log", structured=True)
    
    # Usar contexto
    logger.bind(user_id=123, session="abc123")
    
    # Logs básicos
    logger.info("Aplicação iniciada")
    logger.warning("Aviso de teste")
    logger.error("Erro de teste", error_code=500)
    
    # Log de performance
    import time
    start = time.time()
    time.sleep(0.1)
    logger.performance("Operação teste", time.time() - start)
    
    # Usar decorador
    @logged(logger, include_args=True, include_result=True)
    def exemplo_funcao(x, y):
        return x + y
    
    resultado = exemplo_funcao(2, 3)
    
    # Ver métricas
    print("Métricas:", logger.get_metrics())
    
    # Limpar contexto
    logger.context.clear()
    
    # Fechar logger
    logger.close()