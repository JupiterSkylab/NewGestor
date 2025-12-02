# -*- coding: utf-8 -*-
"""
Configuração de logging estruturado para o Gestor de Processos
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = 'gestor_processos', level: int = logging.INFO) -> logging.Logger:
    """Configura e retorna um logger estruturado"""
    
    # Cria diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configura o logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo com rotação
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console (apenas erros críticos)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Logger principal da aplicação
app_logger = setup_logger('gestor_processos')

# Loggers específicos para diferentes módulos
db_logger = setup_logger('database', logging.DEBUG)
export_logger = setup_logger('export', logging.INFO)
backup_logger = setup_logger('backup', logging.INFO)
ui_logger = setup_logger('interface', logging.WARNING)

def log_error(logger: logging.Logger, error: Exception, context: str = ''):
    """Registra um erro com contexto adicional"""
    error_msg = f"{context}: {type(error).__name__}: {str(error)}"
    logger.error(error_msg, exc_info=True)

def log_operation(logger: logging.Logger, operation: str, success: bool = True, details: str = ''):
    """Registra uma operação com resultado"""
    status = 'SUCCESS' if success else 'FAILED'
    message = f"{operation} - {status}"
    if details:
        message += f" - {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)

def log_performance(logger: logging.Logger, operation: str, duration: float, details: str = ''):
    """Registra métricas de performance"""
    message = f"PERFORMANCE - {operation}: {duration:.3f}s"
    if details:
        message += f" - {details}"
    
    # Log como warning se a operação demorou muito
    if duration > 5.0:  # Mais de 5 segundos
        logger.warning(message)
    else:
        logger.info(message)

def create_audit_log(action: str, user: str = 'system', details: dict = None):
    """Cria log de auditoria para ações importantes"""
    audit_logger = setup_logger('audit', logging.INFO)
    
    audit_data = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'user': user,
        'details': details or {}
    }
    
    audit_logger.info(f"AUDIT: {audit_data}")

# Decorator para logging automático de funções
def log_function_call(logger: logging.Logger = app_logger):
    """Decorator para registrar chamadas de função automaticamente"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = datetime.now()
            
            try:
                logger.debug(f"Iniciando {func_name}")
                result = func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Concluído {func_name} em {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                log_error(logger, e, f"Erro em {func_name} após {duration:.3f}s")
                raise
        
        return wrapper
    return decorator