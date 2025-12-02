"""Sistema de tratamento de erros estruturado para MiniGestor TRAE.

Este módulo implementa um sistema robusto de tratamento de erros com:
- Classificação automática de erros
- Logging estruturado de exceções
- Recuperação automática quando possível
- Notificações de erro para usuários
- Métricas de erro para monitoramento
"""

import traceback
import sys
import functools
import threading
import time
from typing import Dict, Any, Optional, Callable, Type, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

from utils.structured_logger import get_logger, ContextualLogger, LogContext


class ErrorSeverity(Enum):
    """Níveis de severidade de erro."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorias de erro."""
    DATABASE = "database"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Contexto de erro."""
    operation: str
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None
        }


@dataclass
class ErrorInfo:
    """Informações detalhadas de erro."""
    exception_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    timestamp: datetime = field(default_factory=datetime.now)
    traceback_info: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_message: Optional[str] = None
    technical_details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'exception_type': self.exception_type,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'traceback_info': self.traceback_info,
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful,
            'user_message': self.user_message,
            'technical_details': self.technical_details
        }


class ErrorClassifier:
    """Classificador automático de erros."""
    
    # Mapeamento de exceções para categorias
    EXCEPTION_CATEGORIES = {
        # Database errors
        'sqlite3.Error': ErrorCategory.DATABASE,
        'sqlite3.DatabaseError': ErrorCategory.DATABASE,
        'sqlite3.IntegrityError': ErrorCategory.DATABASE,
        'sqlite3.OperationalError': ErrorCategory.DATABASE,
        
        # Validation errors
        'ValueError': ErrorCategory.VALIDATION,
        'TypeError': ErrorCategory.VALIDATION,
        'AttributeError': ErrorCategory.VALIDATION,
        
        # File system errors
        'FileNotFoundError': ErrorCategory.FILE_SYSTEM,
        'PermissionError': ErrorCategory.FILE_SYSTEM,
        'OSError': ErrorCategory.FILE_SYSTEM,
        'IOError': ErrorCategory.FILE_SYSTEM,
        
        # Network errors
        'ConnectionError': ErrorCategory.NETWORK,
        'TimeoutError': ErrorCategory.NETWORK,
        'requests.RequestException': ErrorCategory.NETWORK,
        
        # System errors
        'MemoryError': ErrorCategory.SYSTEM,
        'SystemError': ErrorCategory.SYSTEM,
        'RuntimeError': ErrorCategory.SYSTEM,
    }
    
    # Mapeamento de categorias para severidade
    CATEGORY_SEVERITY = {
        ErrorCategory.DATABASE: ErrorSeverity.HIGH,
        ErrorCategory.VALIDATION: ErrorSeverity.MEDIUM,
        ErrorCategory.BUSINESS_LOGIC: ErrorSeverity.MEDIUM,
        ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
        ErrorCategory.FILE_SYSTEM: ErrorSeverity.MEDIUM,
        ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
        ErrorCategory.AUTHORIZATION: ErrorSeverity.HIGH,
        ErrorCategory.CONFIGURATION: ErrorSeverity.HIGH,
        ErrorCategory.EXTERNAL_SERVICE: ErrorSeverity.MEDIUM,
        ErrorCategory.USER_INPUT: ErrorSeverity.LOW,
        ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
        ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM,
    }
    
    @classmethod
    def classify_exception(cls, exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classifica uma exceção."""
        exception_name = f"{exception.__class__.__module__}.{exception.__class__.__name__}"
        
        # Tentar classificação exata
        category = cls.EXCEPTION_CATEGORIES.get(exception_name)
        
        # Tentar classificação por nome da classe
        if not category:
            class_name = exception.__class__.__name__
            category = cls.EXCEPTION_CATEGORIES.get(class_name)
        
        # Classificação por conteúdo da mensagem
        if not category:
            category = cls._classify_by_message(str(exception))
        
        # Categoria padrão
        if not category:
            category = ErrorCategory.UNKNOWN
        
        # Determinar severidade
        severity = cls.CATEGORY_SEVERITY.get(category, ErrorSeverity.MEDIUM)
        
        return category, severity
    
    @classmethod
    def _classify_by_message(cls, message: str) -> Optional[ErrorCategory]:
        """Classifica erro pela mensagem."""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['database', 'sql', 'table', 'column']):
            return ErrorCategory.DATABASE
        
        if any(keyword in message_lower for keyword in ['validation', 'invalid', 'required']):
            return ErrorCategory.VALIDATION
        
        if any(keyword in message_lower for keyword in ['file', 'directory', 'path']):
            return ErrorCategory.FILE_SYSTEM
        
        if any(keyword in message_lower for keyword in ['connection', 'network', 'timeout']):
            return ErrorCategory.NETWORK
        
        if any(keyword in message_lower for keyword in ['permission', 'access', 'denied']):
            return ErrorCategory.AUTHORIZATION
        
        return None


class ErrorRecovery:
    """Sistema de recuperação automática de erros."""
    
    @staticmethod
    def attempt_database_recovery(error_info: ErrorInfo, operation: Callable) -> bool:
        """Tenta recuperação de erro de banco de dados."""
        try:
            # Tentar reconectar e executar novamente
            time.sleep(0.1)  # Pequena pausa
            operation()
            return True
        except Exception:
            return False
    
    @staticmethod
    def attempt_file_recovery(error_info: ErrorInfo, operation: Callable) -> bool:
        """Tenta recuperação de erro de arquivo."""
        try:
            # Criar diretórios se necessário
            import os
            if 'path' in error_info.technical_details:
                path = error_info.technical_details['path']
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            operation()
            return True
        except Exception:
            return False
    
    @staticmethod
    def attempt_network_recovery(error_info: ErrorInfo, operation: Callable) -> bool:
        """Tenta recuperação de erro de rede."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(2 ** attempt)  # Backoff exponencial
                operation()
                return True
            except Exception:
                if attempt == max_retries - 1:
                    return False
        return False
    
    RECOVERY_STRATEGIES = {
        ErrorCategory.DATABASE: attempt_database_recovery,
        ErrorCategory.FILE_SYSTEM: attempt_file_recovery,
        ErrorCategory.NETWORK: attempt_network_recovery,
    }
    
    @classmethod
    def attempt_recovery(cls, error_info: ErrorInfo, operation: Callable) -> bool:
        """Tenta recuperação automática."""
        strategy = cls.RECOVERY_STRATEGIES.get(error_info.category)
        if strategy:
            return strategy(error_info, operation)
        return False


class StructuredErrorHandler:
    """Handler principal de erros estruturados."""
    
    def __init__(self, logger: ContextualLogger = None):
        self.logger = logger or get_logger("error_handler")
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'recovery_attempts': 0,
            'successful_recoveries': 0
        }
        self._lock = threading.Lock()
    
    def handle_exception(self, exception: Exception, context: ErrorContext,
                        recovery_operation: Callable = None,
                        user_message: str = None) -> ErrorInfo:
        """Manipula uma exceção de forma estruturada."""
        
        # Classificar erro
        category, severity = ErrorClassifier.classify_exception(exception)
        
        # Criar informações de erro
        error_info = ErrorInfo(
            exception_type=exception.__class__.__name__,
            message=str(exception),
            severity=severity,
            category=category,
            context=context,
            traceback_info=traceback.format_exc(),
            user_message=user_message or self._generate_user_message(category, severity),
            technical_details=self._extract_technical_details(exception)
        )
        
        # Tentar recuperação se possível
        if recovery_operation and severity != ErrorSeverity.CRITICAL:
            error_info.recovery_attempted = True
            try:
                error_info.recovery_successful = ErrorRecovery.attempt_recovery(
                    error_info, recovery_operation
                )
            except Exception as recovery_error:
                self.logger.error(
                    f"Falha na recuperação de erro: {str(recovery_error)}",
                    extra_data={'original_error': error_info.to_dict()}
                )
        
        # Log estruturado do erro
        self._log_error(error_info)
        
        # Atualizar estatísticas
        self._update_stats(error_info)
        
        return error_info
    
    def _generate_user_message(self, category: ErrorCategory, severity: ErrorSeverity) -> str:
        """Gera mensagem amigável para o usuário."""
        messages = {
            ErrorCategory.DATABASE: "Erro ao acessar o banco de dados. Tente novamente.",
            ErrorCategory.VALIDATION: "Os dados fornecidos são inválidos. Verifique e tente novamente.",
            ErrorCategory.BUSINESS_LOGIC: "Operação não permitida pelas regras do sistema.",
            ErrorCategory.NETWORK: "Erro de conexão. Verifique sua internet e tente novamente.",
            ErrorCategory.FILE_SYSTEM: "Erro ao acessar arquivo. Verifique as permissões.",
            ErrorCategory.AUTHENTICATION: "Erro de autenticação. Faça login novamente.",
            ErrorCategory.AUTHORIZATION: "Você não tem permissão para esta operação.",
            ErrorCategory.CONFIGURATION: "Erro de configuração do sistema. Contate o suporte.",
            ErrorCategory.EXTERNAL_SERVICE: "Serviço externo indisponível. Tente mais tarde.",
            ErrorCategory.USER_INPUT: "Entrada inválida. Verifique os dados fornecidos.",
            ErrorCategory.SYSTEM: "Erro interno do sistema. Contate o suporte.",
            ErrorCategory.UNKNOWN: "Erro inesperado. Tente novamente ou contate o suporte."
        }
        
        base_message = messages.get(category, messages[ErrorCategory.UNKNOWN])
        
        if severity == ErrorSeverity.CRITICAL:
            return f"CRÍTICO: {base_message} Contate o suporte imediatamente."
        
        return base_message
    
    def _extract_technical_details(self, exception: Exception) -> Dict[str, Any]:
        """Extrai detalhes técnicos da exceção."""
        details = {
            'exception_module': exception.__class__.__module__,
            'exception_class': exception.__class__.__name__,
            'exception_args': exception.args
        }
        
        # Detalhes específicos por tipo de exceção
        if hasattr(exception, 'errno'):
            details['errno'] = exception.errno
        
        if hasattr(exception, 'filename'):
            details['filename'] = exception.filename
        
        if hasattr(exception, 'strerror'):
            details['strerror'] = exception.strerror
        
        return details
    
    def _log_error(self, error_info: ErrorInfo):
        """Faz log estruturado do erro."""
        log_context = LogContext(
            operation=error_info.context.operation,
            component=error_info.context.component,
            user_id=error_info.context.user_id,
            session_id=error_info.context.session_id
        )
        
        with self.logger.context_manager(log_context) as ctx_logger:
            extra_data = {
                'error_info': error_info.to_dict(),
                'recovery_attempted': error_info.recovery_attempted,
                'recovery_successful': error_info.recovery_successful
            }
            
            # Escolher nível de log baseado na severidade
            if error_info.severity == ErrorSeverity.CRITICAL:
                ctx_logger.critical(
                    f"Erro crítico: {error_info.message}",
                    extra_data=extra_data
                )
            elif error_info.severity == ErrorSeverity.HIGH:
                ctx_logger.error(
                    f"Erro de alta severidade: {error_info.message}",
                    extra_data=extra_data
                )
            elif error_info.severity == ErrorSeverity.MEDIUM:
                ctx_logger.warning(
                    f"Erro de média severidade: {error_info.message}",
                    extra_data=extra_data
                )
            else:
                ctx_logger.info(
                    f"Erro de baixa severidade: {error_info.message}",
                    extra_data=extra_data
                )
    
    def _update_stats(self, error_info: ErrorInfo):
        """Atualiza estatísticas de erro."""
        with self._lock:
            self.error_stats['total_errors'] += 1
            
            # Por categoria
            category_key = error_info.category.value
            self.error_stats['errors_by_category'][category_key] = \
                self.error_stats['errors_by_category'].get(category_key, 0) + 1
            
            # Por severidade
            severity_key = error_info.severity.value
            self.error_stats['errors_by_severity'][severity_key] = \
                self.error_stats['errors_by_severity'].get(severity_key, 0) + 1
            
            # Recuperação
            if error_info.recovery_attempted:
                self.error_stats['recovery_attempts'] += 1
                if error_info.recovery_successful:
                    self.error_stats['successful_recoveries'] += 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de erro."""
        with self._lock:
            stats = self.error_stats.copy()
            
            # Calcular taxa de recuperação
            if stats['recovery_attempts'] > 0:
                stats['recovery_rate'] = stats['successful_recoveries'] / stats['recovery_attempts']
            else:
                stats['recovery_rate'] = 0.0
            
            return stats
    
    def reset_stats(self):
        """Reseta estatísticas."""
        with self._lock:
            self.error_stats = {
                'total_errors': 0,
                'errors_by_category': {},
                'errors_by_severity': {},
                'recovery_attempts': 0,
                'successful_recoveries': 0
            }


def handle_errors(component: str, operation: str = None, 
                 user_message: str = None, attempt_recovery: bool = True):
    """Decorador para tratamento automático de erros."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = StructuredErrorHandler()
            
            context = ErrorContext(
                operation=operation or func.__name__,
                component=component,
                request_data={'args': str(args), 'kwargs': kwargs}
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                recovery_op = lambda: func(*args, **kwargs) if attempt_recovery else None
                
                error_info = error_handler.handle_exception(
                    e, context, recovery_op, user_message
                )
                
                # Se a recuperação foi bem-sucedida, retornar resultado
                if error_info.recovery_successful:
                    return func(*args, **kwargs)
                
                # Caso contrário, re-raise a exceção
                raise
        
        return wrapper
    return decorator


@contextmanager
def error_context(component: str, operation: str, user_id: str = None,
                 session_id: str = None, **context_data):
    """Context manager para tratamento de erros."""
    error_handler = StructuredErrorHandler()
    
    context = ErrorContext(
        operation=operation,
        component=component,
        user_id=user_id,
        session_id=session_id,
        system_state=context_data
    )
    
    try:
        yield error_handler
    except Exception as e:
        error_info = error_handler.handle_exception(e, context)
        raise


# Handler global
_global_error_handler: Optional[StructuredErrorHandler] = None


def get_error_handler() -> StructuredErrorHandler:
    """Obtém handler global de erros."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = StructuredErrorHandler()
    
    return _global_error_handler


def setup_global_exception_handler():
    """Configura handler global de exceções não capturadas."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler = get_error_handler()
        context = ErrorContext(
            operation="global_exception",
            component="system"
        )
        
        error_handler.handle_exception(exc_value, context)
    
    sys.excepthook = handle_exception


if __name__ == "__main__":
    # Exemplo de uso
    setup_global_exception_handler()
    
    # Teste com decorador
    @handle_errors("test_component", "test_operation")
    def test_function():
        raise ValueError("Erro de teste")
    
    # Teste com context manager
    try:
        with error_context("test_component", "context_test") as handler:
            raise FileNotFoundError("Arquivo não encontrado")
    except FileNotFoundError:
        pass
    
    # Obter estatísticas
    handler = get_error_handler()
    stats = handler.get_error_stats()
    print(f"Estatísticas de erro: {stats}")