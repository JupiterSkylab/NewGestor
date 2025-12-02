"""Pacote de repositories para operações de banco de dados."""

from .processo_repository import ProcessoRepository
from .estatisticas_repository import EstatisticasRepository
from .lembrete_repository import LembreteRepository

__all__ = [
    'ProcessoRepository',
    'EstatisticasRepository',
    'LembreteRepository'
]