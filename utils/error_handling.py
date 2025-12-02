"""Sistema avançado de tratamento de erros."""

import logging
import traceback
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import tkinter as tk
from tkinter import messagebox


class ErrorType(Enum):
    """Tipos de erro do sistema."""
    DATABASE = "database"
    VALIDATION = "validation"
    FILE_IO = "file_io"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Níveis de severidade dos erros."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserMessage:
    """Mensagem amigável para o usuário."""
    title: str
    message: str
    suggestion: str
    show_details: bool = False


class ErrorMessages:
    """Mensagens de erro categorizadas por tipo."""
    
    DATABASE = {
        "connection_failed": UserMessage(
            "Erro de Conexão",
            "Não foi possível conectar ao banco de dados.",
            "Verifique se o arquivo de banco existe e tente novamente."
        ),
        "query_failed": UserMessage(
            "Erro na Consulta",
            "Ocorreu um erro ao consultar os dados.",
            "Tente novamente. Se o problema persistir, contate o suporte."
        ),
        "constraint_violation": UserMessage(
            "Dados Inválidos",
            "Os dados fornecidos violam as regras do sistema.",
            "Verifique se todos os campos obrigatórios estão preenchidos corretamente."
        ),
        "table_locked": UserMessage(
            "Banco Ocupado",
            "O banco de dados está temporariamente ocupado.",
            "Aguarde alguns segundos e tente novamente."
        )
    }
    
    VALIDATION = {
        "required_field": UserMessage(
            "Campo Obrigatório",
            "Um ou mais campos obrigatórios não foram preenchidos.",
            "Preencha todos os campos marcados como obrigatórios."
        ),
        "invalid_format": UserMessage(
            "Formato Inválido",
            "O formato dos dados inseridos não é válido.",
            "Verifique o formato dos dados e tente novamente."
        ),
        "invalid_date": UserMessage(
            "Data Inválida",
            "A data inserida não é válida.",
            "Use o formato DD/MM/AAAA para datas."
        ),
        "invalid_number": UserMessage(
            "Número Inválido",
            "O valor numérico inserido não é válido.",
            "Insira apenas números válidos."
        )
    }
    
    FILE_IO = {
        "file_not_found": UserMessage(
            "Arquivo Não Encontrado",
            "O arquivo especificado não foi encontrado.",
            "Verifique se o caminho do arquivo está correto."
        ),
        "permission_denied": UserMessage(
            "Acesso Negado",
            "Não há permissão para acessar o arquivo.",
            "Verifique as permissões do arquivo ou execute como administrador."
        ),
        "disk_full": UserMessage(
            "Espaço Insuficiente",
            "Não há espaço suficiente no disco.",
            "Libere espaço no disco e tente novamente."
        ),
        "file_in_use": UserMessage(
            "Arquivo em Uso",
            "O arquivo está sendo usado por outro programa.",
            "Feche o arquivo em outros programas e tente novamente."
        )
    }
    
    EXPORT = {
        "pdf_generation_failed": UserMessage(
            "Erro na Geração de PDF",
            "Não foi possível gerar o arquivo PDF.",
            "Verifique se há espaço suficiente no disco e tente novamente."
        ),
        "excel_generation_failed": UserMessage(
            "Erro na Geração de Excel",
            "Não foi possível gerar o arquivo Excel.",
            "Verifique se o Excel não está aberto com o arquivo e tente novamente."
        ),
        "no_data_to_export": UserMessage(
            "Nenhum Dado para Exportar",
            "Não há dados disponíveis para exportação.",
            "Realize uma consulta primeiro para obter dados."
        )
    }


class ErrorHandler:
    """Manipulador centralizado de erros."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self.lock = threading.Lock()
        
        # Callbacks para diferentes tipos de erro
        self.error_callbacks: Dict[ErrorType, List[Callable]] = {
            error_type: [] for error_type in ErrorType
        }
    
    def handle_error(self, 
                    error: Exception,
                    error_type: ErrorType = ErrorType.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Optional[Dict[str, Any]] = None,
                    show_user_message: bool = True,
                    user_message: Optional[UserMessage] = None) -> Dict[str, Any]:
        """Manipula um erro de forma centralizada."""
        
        with self.lock:
            # Preparar informações do erro
            error_info = {
                'timestamp': time.time(),
                'error_type': error_type.value,
                'severity': severity.value,
                'exception_type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'context': context or {},
                'thread_id': threading.get_ident()
            }
            
            # Registrar no histórico
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
            
            # Contar ocorrências
            error_key = f"{error_type.value}:{type(error).__name__}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Log do erro
            log_level = self._get_log_level(severity)
            self.logger.log(
                log_level,
                f"[{error_type.value.upper()}] {type(error).__name__}: {error}",
                extra={
                    'error_type': error_type.value,
                    'severity': severity.value,
                    'context': context,
                    'error_count': self.error_counts[error_key]
                }
            )
            
            # Executar callbacks específicos
            for callback in self.error_callbacks.get(error_type, []):
                try:
                    callback(error, error_info)
                except Exception as cb_error:
                    self.logger.error(f"Erro no callback: {cb_error}")
            
            # Mostrar mensagem ao usuário se solicitado
            if show_user_message:
                self._show_user_message(error, error_type, user_message, error_info)
            
            return error_info
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Converte severidade para nível de log."""
        mapping = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.ERROR)
    
    def _show_user_message(self, 
                          error: Exception,
                          error_type: ErrorType,
                          user_message: Optional[UserMessage],
                          error_info: Dict[str, Any]):
        """Exibe mensagem amigável ao usuário."""
        try:
            if user_message:
                msg = user_message
            else:
                msg = self._get_default_message(error, error_type)
            
            # Determinar tipo de messagebox baseado na severidade
            severity = ErrorSeverity(error_info['severity'])
            
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(msg.title, f"{msg.message}\n\n{msg.suggestion}")
            elif severity == ErrorSeverity.HIGH:
                messagebox.showerror(msg.title, f"{msg.message}\n\n{msg.suggestion}")
            elif severity == ErrorSeverity.MEDIUM:
                messagebox.showwarning(msg.title, f"{msg.message}\n\n{msg.suggestion}")
            else:
                messagebox.showinfo(msg.title, f"{msg.message}\n\n{msg.suggestion}")
                
        except Exception as e:
            # Fallback se não conseguir mostrar messagebox
            print(f"Erro: {error}")
            self.logger.error(f"Erro ao mostrar messagebox: {e}")
    
    def _get_default_message(self, error: Exception, error_type: ErrorType) -> UserMessage:
        """Obtém mensagem padrão baseada no tipo de erro."""
        error_name = type(error).__name__.lower()
        
        # Tentar encontrar mensagem específica
        if error_type == ErrorType.DATABASE:
            messages = ErrorMessages.DATABASE
            if "connection" in str(error).lower():
                return messages.get("connection_failed", messages["query_failed"])
            elif "constraint" in str(error).lower():
                return messages["constraint_violation"]
            elif "locked" in str(error).lower():
                return messages["table_locked"]
            else:
                return messages["query_failed"]
        
        elif error_type == ErrorType.VALIDATION:
            messages = ErrorMessages.VALIDATION
            if "required" in str(error).lower():
                return messages["required_field"]
            elif "date" in str(error).lower():
                return messages["invalid_date"]
            elif "number" in str(error).lower():
                return messages["invalid_number"]
            else:
                return messages["invalid_format"]
        
        elif error_type == ErrorType.FILE_IO:
            messages = ErrorMessages.FILE_IO
            if "not found" in str(error).lower():
                return messages["file_not_found"]
            elif "permission" in str(error).lower():
                return messages["permission_denied"]
            elif "space" in str(error).lower():
                return messages["disk_full"]
            else:
                return messages["file_in_use"]
        
        # Mensagem genérica
        return UserMessage(
            "Erro do Sistema",
            f"Ocorreu um erro inesperado: {type(error).__name__}",
            "Tente novamente. Se o problema persistir, contate o suporte."
        )
    
    def add_error_callback(self, error_type: ErrorType, callback: Callable):
        """Adiciona callback para tipo específico de erro."""
        self.error_callbacks[error_type].append(callback)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de erros."""
        with self.lock:
            total_errors = sum(self.error_counts.values())
            
            # Agrupar por tipo
            type_counts = {}
            for error_key, count in self.error_counts.items():
                error_type = error_key.split(':')[0]
                type_counts[error_type] = type_counts.get(error_type, 0) + count
            
            # Erros recentes (última hora)
            recent_threshold = time.time() - 3600
            recent_errors = [
                err for err in self.error_history 
                if err['timestamp'] > recent_threshold
            ]
            
            return {
                'total_errors': total_errors,
                'error_counts': self.error_counts.copy(),
                'type_counts': type_counts,
                'recent_errors_count': len(recent_errors),
                'most_common_error': max(self.error_counts.items(), 
                                       key=lambda x: x[1]) if self.error_counts else None,
                'error_history_size': len(self.error_history)
            }
    
    def get_recent_errors(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Retorna erros recentes."""
        threshold = time.time() - (hours * 3600)
        with self.lock:
            return [
                err for err in self.error_history 
                if err['timestamp'] > threshold
            ]
    
    def clear_history(self):
        """Limpa histórico de erros."""
        with self.lock:
            self.error_history.clear()
            self.error_counts.clear()


# Decoradores para tratamento automático de erros
def handle_database_errors(handler: ErrorHandler = None, 
                          show_message: bool = True,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorador para tratamento de erros de banco de dados."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = handler or get_error_handler()
                error_handler.handle_error(
                    e, 
                    ErrorType.DATABASE, 
                    severity,
                    context={'function': func.__name__, 'args': str(args)},
                    show_user_message=show_message
                )
                raise
        return wrapper
    return decorator


def handle_validation_errors(handler: ErrorHandler = None,
                           show_message: bool = True,
                           severity: ErrorSeverity = ErrorSeverity.LOW):
    """Decorador para tratamento de erros de validação."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = handler or get_error_handler()
                error_handler.handle_error(
                    e,
                    ErrorType.VALIDATION,
                    severity,
                    context={'function': func.__name__, 'args': str(args)},
                    show_user_message=show_message
                )
                raise
        return wrapper
    return decorator


def handle_file_errors(handler: ErrorHandler = None,
                      show_message: bool = True,
                      severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorador para tratamento de erros de arquivo."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = handler or get_error_handler()
                error_handler.handle_error(
                    e,
                    ErrorType.FILE_IO,
                    severity,
                    context={'function': func.__name__, 'args': str(args)},
                    show_user_message=show_message
                )
                raise
        return wrapper
    return decorator


# Instância global
_global_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Retorna instância global do manipulador de erros."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


# Funções de conveniência
def show_error_message(title: str, message: str, suggestion: str = ""):
    """Exibe mensagem de erro ao usuário."""
    full_message = f"{message}\n\n{suggestion}" if suggestion else message
    messagebox.showerror(title, full_message)


def show_warning_message(title: str, message: str, suggestion: str = ""):
    """Exibe mensagem de aviso ao usuário."""
    full_message = f"{message}\n\n{suggestion}" if suggestion else message
    messagebox.showwarning(title, full_message)


def show_info_message(title: str, message: str):
    """Exibe mensagem informativa ao usuário."""
    messagebox.showinfo(title, message)


# Exemplo de uso
if __name__ == "__main__":
    # Configurar handler
    handler = ErrorHandler()
    
    # Adicionar callback personalizado
    def on_database_error(error, error_info):
        print(f"Callback: Erro de banco detectado - {error}")
    
    handler.add_error_callback(ErrorType.DATABASE, on_database_error)
    
    # Simular erros
    try:
        raise ValueError("Teste de erro de validação")
    except Exception as e:
        handler.handle_error(e, ErrorType.VALIDATION, ErrorSeverity.LOW)
    
    try:
        raise FileNotFoundError("Arquivo não encontrado")
    except Exception as e:
        handler.handle_error(e, ErrorType.FILE_IO, ErrorSeverity.MEDIUM)
    
    # Ver estatísticas
    stats = handler.get_error_stats()
    print(f"Total de erros: {stats['total_errors']}")
    print(f"Erros por tipo: {stats['type_counts']}")
    
    # Usar decoradores
    @handle_database_errors()
    def operacao_banco():
        raise ConnectionError("Falha na conexão")
    
    @handle_validation_errors()
    def validar_dados(valor):
        if not valor:
            raise ValueError("Valor obrigatório")
        return valor
    
    # Testar decoradores
    try:
        validar_dados("")
    except ValueError:
        pass
    
    try:
        operacao_banco()
    except ConnectionError:
        pass
    
    # Ver estatísticas finais
    final_stats = handler.get_error_stats()
    print(f"Estatísticas finais: {final_stats}")