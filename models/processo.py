"""Modelo de dados para Processo."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Processo:
    """Modelo de dados para um processo."""
    
    numero_processo: str
    secretaria: str
    situacao: str = "Em Andamento"
    numero_licitacao: Optional[str] = None
    modalidade: Optional[str] = None
    data_inicio: Optional[str] = None
    data_entrega: Optional[str] = None
    entregue_por: Optional[str] = None
    devolvido_a: Optional[str] = None
    contratado: Optional[str] = None
    descricao: Optional[str] = None
    data_registro: Optional[str] = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    def __post_init__(self):
        """Validações pós-inicialização."""
        if not self.numero_processo:
            raise ValueError("Número do processo é obrigatório")
        if not self.secretaria:
            raise ValueError("Secretaria é obrigatória")
        
        # Normaliza o número do processo
        self.numero_processo = self.numero_processo.strip().upper()
        
        # Normaliza campos de texto
        if self.entregue_por:
            self.entregue_por = self.entregue_por.strip().upper()
        if self.devolvido_a:
            self.devolvido_a = self.devolvido_a.strip().upper()
        if self.contratado:
            self.contratado = self.contratado.strip().upper()
    
    def to_dict(self) -> dict:
        """Converte o processo para dicionário."""
        return {
            'data_registro': self.data_registro,
            'numero_processo': self.numero_processo,
            'secretaria': self.secretaria,
            'numero_licitacao': self.numero_licitacao,
            'situacao': self.situacao,
            'modalidade': self.modalidade,
            'data_inicio': self.data_inicio,
            'data_entrega': self.data_entrega,
            'entregue_por': self.entregue_por,
            'devolvido_a': self.devolvido_a,
            'contratado': self.contratado,
            'descricao': self.descricao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Processo':
        """Cria um processo a partir de um dicionário."""
        return cls(
            numero_processo=data.get('numero_processo', ''),
            secretaria=data.get('secretaria', ''),
            situacao=data.get('situacao', 'Em Andamento'),
            numero_licitacao=data.get('numero_licitacao'),
            modalidade=data.get('modalidade'),
            data_inicio=data.get('data_inicio'),
            data_entrega=data.get('data_entrega'),
            entregue_por=data.get('entregue_por'),
            devolvido_a=data.get('devolvido_a'),
            contratado=data.get('contratado'),
            descricao=data.get('descricao'),
            data_registro=data.get('data_registro')
        )
    
    @classmethod
    def from_tuple(cls, data: tuple) -> 'Processo':
        """Cria um processo a partir de uma tupla (resultado do banco)."""
        return cls(
            data_registro=data[0] if len(data) > 0 else None,
            numero_processo=data[1] if len(data) > 1 else '',
            secretaria=data[2] if len(data) > 2 else '',
            numero_licitacao=data[3] if len(data) > 3 else None,
            situacao=data[4] if len(data) > 4 else 'Em Andamento',
            modalidade=data[5] if len(data) > 5 else None,
            data_inicio=data[6] if len(data) > 6 else None,
            data_entrega=data[7] if len(data) > 7 else None,
            entregue_por=data[8] if len(data) > 8 else None,
            devolvido_a=data[9] if len(data) > 9 else None,
            contratado=data[10] if len(data) > 10 else None,
            descricao=data[11] if len(data) > 11 else None
        )
    
    def is_valid(self) -> bool:
        """Verifica se o processo é válido."""
        return bool(self.numero_processo and self.secretaria)
    
    def get_display_name(self) -> str:
        """Retorna nome para exibição."""
        return f"{self.numero_processo} - {self.secretaria}"