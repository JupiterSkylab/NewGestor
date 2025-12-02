"""Pacote de configurações da aplicação."""

from .settings import DATABASE_CONFIG, UI_CONFIG, STYLES, CACHE_CONFIG, EXPORT_CONFIG, BACKUP_CONFIG

# Alias para compatibilidade
DB_CONFIG = DATABASE_CONFIG

__all__ = ['DATABASE_CONFIG', 'DB_CONFIG', 'UI_CONFIG', 'STYLES', 'CACHE_CONFIG', 'EXPORT_CONFIG', 'BACKUP_CONFIG']