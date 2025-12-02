"""Inicialização do sistema de logging estruturado para MiniGestor TRAE.

Este módulo deve ser importado no início da aplicação para configurar
o sistema de logging estruturado e tratamento de erros.
"""

import os
import sys
from config.logging_config import initialize_logging, get_component_logger
from utils.error_handler import setup_global_exception_handler, get_error_handler
from utils.structured_logger import LogContext

# Configurar logging baseado no ambiente
ENVIRONMENT = os.getenv('MINIGESTOR_ENV', 'development')

# Inicializar sistema de logging
main_logger = initialize_logging(ENVIRONMENT)

# Configurar handler global de exceções
setup_global_exception_handler()

# Obter loggers específicos para componentes
ui_logger = get_component_logger('ui')
database_logger = get_component_logger('database')
service_logger = get_component_logger('services')
repository_logger = get_component_logger('repositories')
cache_logger = get_component_logger('cache')
export_logger = get_component_logger('export')
backup_logger = get_component_logger('backup')

# Handler de erros global
error_handler = get_error_handler()

def log_application_start():
    """Log do início da aplicação."""
    main_logger.info(
        "MiniGestor TRAE iniciado",
        extra_data={
            'environment': ENVIRONMENT,
            'python_version': sys.version,
            'platform': sys.platform
        }
    )

def log_application_shutdown():
    """Log do encerramento da aplicação."""
    # Obter estatísticas de erro
    error_stats = error_handler.get_error_stats()
    
    main_logger.info(
        "MiniGestor TRAE encerrado",
        extra_data={
            'error_statistics': error_stats,
            'environment': ENVIRONMENT
        }
    )

def get_logger_for_component(component_name: str):
    """Obtém logger para um componente específico."""
    loggers = {
        'ui': ui_logger,
        'database': database_logger,
        'services': service_logger,
        'repositories': repository_logger,
        'cache': cache_logger,
        'export': export_logger,
        'backup': backup_logger,
        'main': main_logger
    }
    
    return loggers.get(component_name, main_logger)

def create_operation_context(operation: str, component: str = 'main', 
                           user_id: str = None, **kwargs):
    """Cria contexto para operação."""
    return LogContext(
        operation=operation,
        component=component,
        user_id=user_id,
        **kwargs
    )

# Configurar logging para módulos específicos
def setup_module_logging():
    """Configura logging para módulos específicos da aplicação."""
    
    # Configurar logging para SQLite
    import logging
    sqlite_logger = logging.getLogger('sqlite3')
    sqlite_logger.setLevel(logging.WARNING)
    
    # Configurar logging para tkinter (reduzir verbosidade)
    tk_logger = logging.getLogger('tkinter')
    tk_logger.setLevel(logging.ERROR)
    
    # Configurar logging para openpyxl
    openpyxl_logger = logging.getLogger('openpyxl')
    openpyxl_logger.setLevel(logging.WARNING)
    
    # Configurar logging para reportlab
    reportlab_logger = logging.getLogger('reportlab')
    reportlab_logger.setLevel(logging.WARNING)

# Executar configuração
setup_module_logging()

# Exportar principais componentes
__all__ = [
    'main_logger',
    'ui_logger', 
    'database_logger',
    'service_logger',
    'repository_logger',
    'cache_logger',
    'export_logger',
    'backup_logger',
    'error_handler',
    'log_application_start',
    'log_application_shutdown',
    'get_logger_for_component',
    'create_operation_context'
]

# Log de inicialização do sistema de logging
main_logger.info(
    "Sistema de logging estruturado inicializado",
    extra_data={
        'environment': ENVIRONMENT,
        'log_level': main_logger.logger.level
    }
)