# -*- coding: utf-8 -*-
"""
Validadores de dados para o Gestor de Processos
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any

class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass

class DataValidator:
    """Classe centralizada para todas as validações de dados"""
    
    @staticmethod
    def validar_data(data_str: str) -> bool:
        """Valida se uma data está no formato DD/MM/AAAA e é válida"""
        if not data_str or not data_str.strip():
            return False
        
        try:
            # Verifica o formato DD/MM/AAAA
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', data_str.strip()):
                return False
            
            # Tenta converter para verificar se é uma data válida
            datetime.strptime(data_str.strip(), "%d/%m/%Y")
            return True
            
        except ValueError:
            return False
    
    @staticmethod
    def validar_campos_obrigatorios(data: Dict[str, Any]) -> None:
        """Valida se os campos obrigatórios estão preenchidos"""
        required_fields = {
            'numero_processo': 'Número do processo',
            'secretaria': 'Secretaria',
            'data_inicio': 'Data de recebimento',
            'entregue_por': 'Entregue por'
        }
        
        for field, label in required_fields.items():
            if not data.get(field, '').strip():
                raise ValidationError(f"Campo '{label}' é obrigatório")
    
    @staticmethod
    def validar_numero_processo(numero: str) -> None:
        """Valida formato do número do processo"""
        if not numero or len(numero.strip()) < 3:
            raise ValidationError("Número do processo deve ter pelo menos 3 caracteres")
        
        # Permite números, pontos, hífens e barras
        if not re.match(r'^[0-9.\-/]+$', numero.strip()):
            raise ValidationError("Número do processo contém caracteres inválidos")
    
    @staticmethod
    def validar_datas_logicas(data_inicio: str, data_entrega: Optional[str] = None) -> None:
        """Valida a lógica entre datas de recebimento e devolução"""
        if not DataValidator.validar_data(data_inicio):
            raise ValidationError("Data de recebimento inválida. Use o formato DD/MM/AAAA")
        
        if data_entrega and data_entrega.strip():
            if not DataValidator.validar_data(data_entrega):
                raise ValidationError("Data de devolução inválida. Use o formato DD/MM/AAAA")
            
            try:
                recebimento = datetime.strptime(data_inicio, "%d/%m/%Y")
                devolucao = datetime.strptime(data_entrega, "%d/%m/%Y")
                
                if devolucao < recebimento:
                    raise ValidationError(
                        f"Data de devolução ({data_entrega}) não pode ser anterior "
                        f"à data de recebimento ({data_inicio})"
                    )
            except ValueError as e:
                raise ValidationError(f"Erro ao validar datas: {e}")
    
    @staticmethod
    def validar_processo_completo(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida todos os dados de um processo"""
        # Valida campos obrigatórios
        DataValidator.validar_campos_obrigatorios(data)
        
        # Valida número do processo
        DataValidator.validar_numero_processo(data['numero_processo'])
        
        # Valida datas
        DataValidator.validar_datas_logicas(
            data['data_inicio'], 
            data.get('data_entrega')
        )
        
        # Limpa e formata dados
        cleaned_data = {
            'numero_processo': data['numero_processo'].strip(),
            'secretaria': data['secretaria'].strip(),
            'numero_licitacao': data.get('numero_licitacao', '').strip(),
            'situacao': data.get('situacao', 'Em Andamento'),
            'modalidade': data.get('modalidade', '').strip(),
            'data_inicio': data['data_inicio'].strip(),
            'data_entrega': data.get('data_entrega', '').strip() if data.get('data_entrega') else None,
            'entregue_por': data['entregue_por'].strip(),
            'devolvido_a': data.get('devolvido_a', '').strip(),
            'contratado': data.get('contratado', '').strip().upper(),
            'descricao': data.get('descricao', '').strip()
        }
        
        return cleaned_data

class DateFormatter:
    """Classe para formatação e conversão de datas"""
    
    @staticmethod
    def para_banco(data_str: str) -> Optional[str]:
        """Converte data de DD/MM/AAAA para YYYY-MM-DD (formato do banco)"""
        if not data_str or not data_str.strip():
            return None
        
        try:
            data_obj = datetime.strptime(data_str.strip(), "%d/%m/%Y")
            return data_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None
    
    @staticmethod
    def para_exibicao(data_str: str) -> str:
        """Converte data de YYYY-MM-DD para DD/MM/AAAA (formato de exibição)"""
        if not data_str or not data_str.strip():
            return ""
        
        try:
            data_obj = datetime.strptime(data_str.strip(), "%Y-%m-%d")
            return data_obj.strftime("%d/%m/%Y")
        except ValueError:
            return data_str  # Retorna original se não conseguir converter
    
    @staticmethod
    def formatar_data_hora_str(data_str: str) -> str:
        """Formata string de data/hora para exibição"""
        if not data_str:
            return ""
        
        try:
            # Tenta diferentes formatos
            formatos = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y"
            ]
            
            for formato in formatos:
                try:
                    data_obj = datetime.strptime(data_str, formato)
                    return data_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    continue
            
            return data_str  # Retorna original se não conseguir formatar
        except Exception:
            return data_str