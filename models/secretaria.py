"""Modelo de dados para Secretaria."""

from dataclasses import dataclass
from typing import List

from config.settings import SECRETARIAS


@dataclass
class Secretaria:
    """Modelo de dados para uma secretaria."""
    
    sigla: str
    nome: str
    
    def __post_init__(self):
        """Validações pós-inicialização."""
        if not self.sigla:
            raise ValueError("Sigla é obrigatória")
        if not self.nome:
            raise ValueError("Nome é obrigatório")
        
        # Normaliza campos
        self.sigla = self.sigla.strip().upper()
        self.nome = self.nome.strip()
    
    def to_dict(self) -> dict:
        """Converte a secretaria para dicionário."""
        return {
            'sigla': self.sigla,
            'nome': self.nome
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Secretaria':
        """Cria uma secretaria a partir de um dicionário."""
        return cls(
            sigla=data.get('sigla', ''),
            nome=data.get('nome', '')
        )
    
    def get_formatted_name(self) -> str:
        """Retorna nome formatado para exibição."""
        return f"{self.sigla} - {self.nome}"
    
    def is_valid(self) -> bool:
        """Verifica se a secretaria é válida."""
        return bool(self.sigla and self.nome)
    
    @classmethod
    def get_all_secretarias(cls) -> List['Secretaria']:
        """Retorna lista de todas as secretarias disponíveis."""
        return [cls(sigla=sigla, nome=nome) for sigla, nome in SECRETARIAS.items()]
    
    @classmethod
    def get_secretarias_formatadas(cls) -> List[str]:
        """Retorna lista de secretarias formatadas para autocomplete."""
        return [f"{sigla} - {nome}" for sigla, nome in SECRETARIAS.items()]
    
    @classmethod
    def get_by_sigla(cls, sigla: str) -> 'Secretaria':
        """Busca secretaria pela sigla."""
        sigla = sigla.strip().upper()
        if sigla in SECRETARIAS:
            return cls(sigla=sigla, nome=SECRETARIAS[sigla])
        raise ValueError(f"Secretaria com sigla '{sigla}' não encontrada")
    
    @classmethod
    def extract_sigla_from_formatted(cls, formatted_name: str) -> str:
        """Extrai a sigla de um nome formatado."""
        if ' - ' in formatted_name:
            return formatted_name.split(' - ')[0].strip().upper()
        return formatted_name.strip().upper()
    
    @classmethod
    def find_by_name_part(cls, name_part: str) -> List['Secretaria']:
        """Busca secretarias que contenham parte do nome."""
        name_part = name_part.lower()
        results = []
        
        for sigla, nome in SECRETARIAS.items():
            if name_part in nome.lower() or name_part in sigla.lower():
                results.append(cls(sigla=sigla, nome=nome))
        
        return results