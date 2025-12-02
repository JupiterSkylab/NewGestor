"""Configuração centralizada do sistema de logging estruturado.

Este módulo fornece configurações padronizadas para o sistema de logging
do MiniGestor TRAE, incluindo diferentes ambientes e níveis de log.
"""

import os
from typing import Dict, Any
from utils.structured_logger import setup_logging, ContextualLogger


class LoggingConfig:
    """Configuração centralizada de logging."""
    
    # Configurações por ambiente
    ENVIRONMENTS = {
        'development': {
            'log_level': 'DEBUG',
            'enable_console': True,
            'max_file_size': 5 * 1024 * 1024,  # 5MB
            'backup_count': 3,
            'log_performance': True,
            'log_sql_queries': True
        },
        'production': {
            'log_level': 'INFO',
            'enable_console': False,
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'backup_count': 10,
            'log_performance': True,
            'log_sql_queries': False
        },
        'testing': {
            'log_level': 'WARNING',
            'enable_console': True,
            'max_file_size': 1 * 1024 * 1024,  # 1MB
            'backup_count': 2,
            'log_performance': False,
            'log_sql_queries': False
        }
    }
    
    @classmethod
    def get_environment(cls) -> str:
        """Detecta o ambiente atual."""
        env = os.getenv('MINIGESTOR_ENV', 'development').lower()
        if env not in cls.ENVIRONMENTS:
            env = 'development'
        return env
    
    @classmethod
    def get_config(cls, environment: str = None) -> Dict[str, Any]:
        """Obtém configuração para o ambiente especificado."""
        if environment is None:
            environment = cls.get_environment()
        
        return cls.ENVIRONMENTS.get(environment, cls.ENVIRONMENTS['development'])
    
    @classmethod
    def get_log_directory(cls) -> str:
        """Obtém diretório de logs."""
        # Verificar variável de ambiente primeiro
        log_dir = os.getenv('MINIGESTOR_LOG_DIR')
        if log_dir and os.path.isdir(log_dir):
            return log_dir
        
        # Usar diretório padrão
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, 'logs')
    
    @classmethod
    def setup_application_logging(cls, environment: str = None) -> ContextualLogger:
        """Configura logging para a aplicação."""
        config = cls.get_config(environment)
        log_dir = cls.get_log_directory()
        
        return setup_logging(
            log_dir=log_dir,
            log_level=config['log_level'],
            max_file_size=config['max_file_size'],
            backup_count=config['backup_count'],
            enable_console=config['enable_console']
        )


class ComponentLoggers:
    """Loggers específicos para componentes da aplicação."""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, component: str) -> ContextualLogger:
        """Obtém logger para componente específico."""
        if component not in cls._loggers:
            from utils.structured_logger import get_logger
            cls._loggers[component] = get_logger(f"minigestor.{component}")
        
        return cls._loggers[component]
    
    @classmethod
    def get_database_logger(cls) -> ContextualLogger:
        """Logger para operações de banco de dados."""
        return cls.get_logger("database")
    
    @classmethod
    def get_service_logger(cls) -> ContextualLogger:
        """Logger para camada de serviços."""
        return cls.get_logger("services")
    
    @classmethod
    def get_repository_logger(cls) -> ContextualLogger:
        """Logger para repositórios."""
        return cls.get_logger("repositories")
    
    @classmethod
    def get_controller_logger(cls) -> ContextualLogger:
        """Logger para controllers."""
        return cls.get_logger("controllers")
    
    @classmethod
    def get_ui_logger(cls) -> ContextualLogger:
        """Logger para interface de usuário."""
        return cls.get_logger("ui")
    
    @classmethod
    def get_cache_logger(cls) -> ContextualLogger:
        """Logger para sistema de cache."""
        return cls.get_logger("cache")
    
    @classmethod
    def get_export_logger(cls) -> ContextualLogger:
        """Logger para operações de exportação."""
        return cls.get_logger("export")
    
    @classmethod
    def get_backup_logger(cls) -> ContextualLogger:
        """Logger para operações de backup."""
        return cls.get_logger("backup")


class LoggingPatterns:
    """Padrões comuns de logging para a aplicação."""
    
    @staticmethod
    def log_user_action(logger: ContextualLogger, action: str, 
                       user_id: str = None, details: Dict[str, Any] = None):
        """Log de ação do usuário."""
        extra_data = {'action': action}
        if user_id:
            extra_data['user_id'] = user_id
        if details:
            extra_data.update(details)
        
        logger.info(f"Ação do usuário: {action}", extra_data=extra_data)
    
    @staticmethod
    def log_database_operation(logger: ContextualLogger, operation: str,
                             table: str, affected_rows: int = 0,
                             duration: float = None):
        """Log de operação de banco de dados."""
        extra_data = {
            'operation': operation,
            'table': table,
            'affected_rows': affected_rows
        }
        
        performance = {}
        if duration is not None:
            performance['duration_seconds'] = duration
        
        logger.info(
            f"Operação de BD: {operation} em {table}",
            extra_data=extra_data,
            performance=performance if performance else None
        )
    
    @staticmethod
    def log_cache_operation(logger: ContextualLogger, operation: str,
                          cache_key: str, hit: bool = None):
        """Log de operação de cache."""
        extra_data = {
            'cache_operation': operation,
            'cache_key': cache_key
        }
        
        if hit is not None:
            extra_data['cache_hit'] = hit
        
        message = f"Cache {operation}: {cache_key}"
        if hit is not None:
            message += f" ({'HIT' if hit else 'MISS'})"
        
        logger.debug(message, extra_data=extra_data)
    
    @staticmethod
    def log_validation_error(logger: ContextualLogger, field: str,
                           value: Any, error_message: str):
        """Log de erro de validação."""
        logger.warning(
            f"Erro de validação: {field}",
            extra_data={
                'field': field,
                'value': str(value),
                'validation_error': error_message
            }
        )
    
    @staticmethod
    def log_business_rule_violation(logger: ContextualLogger, rule: str,
                                  context: Dict[str, Any] = None):
        """Log de violação de regra de negócio."""
        extra_data = {'business_rule': rule}
        if context:
            extra_data['context'] = context
        
        logger.warning(
            f"Violação de regra de negócio: {rule}",
            extra_data=extra_data
        )
    
    @staticmethod
    def log_performance_metric(logger: ContextualLogger, metric_name: str,
                             value: float, unit: str = 'seconds',
                             context: Dict[str, Any] = None):
        """Log de métrica de performance."""
        performance = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit
        }
        
        extra_data = {}
        if context:
            extra_data.update(context)
        
        logger.info(
            f"Métrica de performance: {metric_name} = {value} {unit}",
            extra_data=extra_data if extra_data else None,
            performance=performance
        )


def initialize_logging(environment: str = None) -> ContextualLogger:
    """Inicializa o sistema de logging da aplicação."""
    return LoggingConfig.setup_application_logging(environment)


def get_component_logger(component: str) -> ContextualLogger:
    """Obtém logger para um componente específico."""
    return ComponentLoggers.get_logger(component)


# Configuração de logging para diferentes módulos
LOGGER_MAPPING = {
    'database': ComponentLoggers.get_database_logger,
    'services': ComponentLoggers.get_service_logger,
    'repositories': ComponentLoggers.get_repository_logger,
    'controllers': ComponentLoggers.get_controller_logger,
    'ui': ComponentLoggers.get_ui_logger,
    'cache': ComponentLoggers.get_cache_logger,
    'export': ComponentLoggers.get_export_logger,
    'backup': ComponentLoggers.get_backup_logger,
}


if __name__ == "__main__":
    # Exemplo de uso
    import time
    
    # Inicializar logging
    main_logger = initialize_logging('development')
    
    # Testar diferentes tipos de log
    main_logger.info("Aplicação iniciada")
    
    # Logger de componente
    db_logger = get_component_logger('database')
    
    # Usar padrões de logging
    LoggingPatterns.log_user_action(
        db_logger, 
        "criar_processo", 
        user_id="user123",
        details={'processo_numero': '12345/2024'}
    )
    
    LoggingPatterns.log_database_operation(
        db_logger,
        "INSERT",
        "trabalhos_realizados",
        affected_rows=1,
        duration=0.05
    )
    
    LoggingPatterns.log_cache_operation(
        get_component_logger('cache'),
        "GET",
        "processos:search:termo",
        hit=True
    )
    
    LoggingPatterns.log_performance_metric(
        main_logger,
        "query_execution_time",
        0.125,
        "seconds",
        {'query_type': 'SELECT', 'table': 'trabalhos_realizados'}
    )
    
    main_logger.info("Teste de logging concluído")