"""Modelo de dados para Lembrete."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Lembrete:
    """Modelo de dados para um lembrete/promessa."""
    
    descricao: str
    pessoa: str
    data_prometida: str
    notificado: int = 0
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validações pós-inicialização."""
        if not self.descricao:
            raise ValueError("Descrição é obrigatória")
        if not self.pessoa:
            raise ValueError("Pessoa é obrigatória")
        if not self.data_prometida:
            raise ValueError("Data prometida é obrigatória")
        
        # Normaliza campos de texto
        self.descricao = self.descricao.strip()
        self.pessoa = self.pessoa.strip()
    
    def to_dict(self) -> dict:
        """Converte o lembrete para dicionário."""
        return {
            'id': self.id,
            'data_prometida': self.data_prometida,
            'descricao': self.descricao,
            'pessoa': self.pessoa,
            'notificado': self.notificado
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Lembrete':
        """Cria um lembrete a partir de um dicionário."""
        return cls(
            descricao=data.get('descricao', ''),
            pessoa=data.get('pessoa', ''),
            data_prometida=data.get('data_prometida', ''),
            notificado=data.get('notificado', 0),
            id=data.get('id')
        )
    
    @classmethod
    def from_tuple(cls, data: tuple) -> 'Lembrete':
        """Cria um lembrete a partir de uma tupla (resultado do banco)."""
        return cls(
            id=data[0] if len(data) > 0 else None,
            data_prometida=data[1] if len(data) > 1 else '',
            descricao=data[2] if len(data) > 2 else '',
            pessoa=data[3] if len(data) > 3 else '',
            notificado=data[4] if len(data) > 4 else 0
        )
    
    def is_valid(self) -> bool:
        """Verifica se o lembrete é válido."""
        return bool(self.descricao and self.pessoa and self.data_prometida)
    
    def get_display_text(self) -> str:
        """Retorna texto para exibição."""
        return f"{self.data_prometida} - {self.descricao}"
    
    def is_overdue(self) -> bool:
        """Verifica se o lembrete está atrasado."""
        try:
            data_prometida = datetime.strptime(self.data_prometida, '%d/%m/%Y')
            return data_prometida.date() < datetime.now().date()
        except ValueError:
            return False
    
    def mark_as_notified(self) -> None:
        """Marca o lembrete como notificado."""
        self.notificado = 1