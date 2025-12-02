# -*- coding: utf-8 -*-
"""
Utilitários para manipulação de datas
"""

import re
from datetime import datetime, date
from typing import Optional, Union

class DateUtils:
    """Utilitários para manipulação e validação de datas"""
    
    # Formatos de data suportados
    FORMATO_EXIBICAO = "%d/%m/%Y"
    FORMATO_BANCO = "%Y-%m-%d"
    FORMATO_DATETIME_BANCO = "%Y-%m-%d %H:%M:%S"
    FORMATO_DATETIME_EXIBICAO = "%d/%m/%Y %H:%M"
    
    @staticmethod
    def validar_formato_brasileiro(data_str: str) -> bool:
        """Valida se uma data está no formato DD/MM/AAAA"""
        if not data_str or not data_str.strip():
            return False
        
        # Verifica o padrão regex
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', data_str.strip()):
            return False
        
        try:
            datetime.strptime(data_str.strip(), DateUtils.FORMATO_EXIBICAO)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def para_banco(data_str: str) -> Optional[str]:
        """Converte data de DD/MM/AAAA para YYYY-MM-DD"""
        if not data_str or not data_str.strip():
            return None
        
        try:
            data_obj = datetime.strptime(data_str.strip(), DateUtils.FORMATO_EXIBICAO)
            return data_obj.strftime(DateUtils.FORMATO_BANCO)
        except ValueError:
            return None
    
    @staticmethod
    def para_exibicao(data_str: str) -> str:
        """Converte data de YYYY-MM-DD para DD/MM/AAAA"""
        if not data_str or not data_str.strip():
            return ""
        
        # Se já está no formato de exibição, retorna como está
        if '/' in data_str:
            return data_str
        
        try:
            data_obj = datetime.strptime(data_str.strip(), DateUtils.FORMATO_BANCO)
            return data_obj.strftime(DateUtils.FORMATO_EXIBICAO)
        except ValueError:
            return data_str  # Retorna original se não conseguir converter
    
    @staticmethod
    def formatar_data_hora(data_str: str) -> str:
        """Formata string de data/hora para exibição"""
        if not data_str or not data_str.strip():
            return ""
        
        # Lista de formatos possíveis de entrada
        formatos_entrada = [
            DateUtils.FORMATO_DATETIME_BANCO,
            DateUtils.FORMATO_BANCO,
            DateUtils.FORMATO_DATETIME_EXIBICAO,
            DateUtils.FORMATO_EXIBICAO,
            "%Y-%m-%d %H:%M:%S.%f",  # Com microssegundos
            "%d/%m/%Y %H:%M:%S",     # Brasileiro com segundos
        ]
        
        for formato in formatos_entrada:
            try:
                data_obj = datetime.strptime(data_str.strip(), formato)
                # Se tem informação de hora, inclui na saída
                if data_obj.hour != 0 or data_obj.minute != 0 or data_obj.second != 0:
                    return data_obj.strftime(DateUtils.FORMATO_DATETIME_EXIBICAO)
                else:
                    return data_obj.strftime(DateUtils.FORMATO_EXIBICAO)
            except ValueError:
                continue
        
        # Se não conseguiu converter, retorna original
        return data_str
    
    @staticmethod
    def comparar_datas(data1: str, data2: str) -> int:
        """Compara duas datas. Retorna -1 se data1 < data2, 0 se iguais, 1 se data1 > data2"""
        try:
            # Converte ambas para objetos datetime
            dt1 = DateUtils._parse_data_flexivel(data1)
            dt2 = DateUtils._parse_data_flexivel(data2)
            
            if dt1 is None or dt2 is None:
                return 0  # Se não conseguir converter, considera iguais
            
            if dt1 < dt2:
                return -1
            elif dt1 > dt2:
                return 1
            else:
                return 0
        except Exception:
            return 0
    
    @staticmethod
    def data_eh_futura(data_str: str) -> bool:
        """Verifica se uma data é futura"""
        try:
            data_obj = DateUtils._parse_data_flexivel(data_str)
            if data_obj is None:
                return False
            
            hoje = datetime.now().date()
            return data_obj.date() > hoje
        except Exception:
            return False
    
    @staticmethod
    def data_eh_passada(data_str: str) -> bool:
        """Verifica se uma data é passada"""
        try:
            data_obj = DateUtils._parse_data_flexivel(data_str)
            if data_obj is None:
                return False
            
            hoje = datetime.now().date()
            return data_obj.date() < hoje
        except Exception:
            return False
    
    @staticmethod
    def calcular_dias_diferenca(data_inicio: str, data_fim: str) -> Optional[int]:
        """Calcula a diferença em dias entre duas datas"""
        try:
            dt_inicio = DateUtils._parse_data_flexivel(data_inicio)
            dt_fim = DateUtils._parse_data_flexivel(data_fim)
            
            if dt_inicio is None or dt_fim is None:
                return None
            
            diferenca = dt_fim.date() - dt_inicio.date()
            return diferenca.days
        except Exception:
            return None
    
    @staticmethod
    def obter_data_atual() -> str:
        """Obtém a data atual no formato brasileiro"""
        return datetime.now().strftime(DateUtils.FORMATO_EXIBICAO)
    
    @staticmethod
    def obter_data_hora_atual() -> str:
        """Obtém a data e hora atual no formato brasileiro"""
        return datetime.now().strftime(DateUtils.FORMATO_DATETIME_EXIBICAO)
    
    @staticmethod
    def obter_data_atual_banco() -> str:
        """Obtém a data atual no formato do banco"""
        return datetime.now().strftime(DateUtils.FORMATO_BANCO)
    
    @staticmethod
    def obter_data_hora_atual_banco() -> str:
        """Obtém a data e hora atual no formato do banco"""
        return datetime.now().strftime(DateUtils.FORMATO_DATETIME_BANCO)
    
    @staticmethod
    def _parse_data_flexivel(data_str: str) -> Optional[datetime]:
        """Tenta fazer parse de uma data em vários formatos"""
        if not data_str or not data_str.strip():
            return None
        
        formatos = [
            DateUtils.FORMATO_EXIBICAO,
            DateUtils.FORMATO_BANCO,
            DateUtils.FORMATO_DATETIME_EXIBICAO,
            DateUtils.FORMATO_DATETIME_BANCO,
            "%Y-%m-%d %H:%M:%S.%f",
            "%d/%m/%Y %H:%M:%S",
        ]
        
        for formato in formatos:
            try:
                return datetime.strptime(data_str.strip(), formato)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def validar_periodo(data_inicio: str, data_fim: str) -> bool:
        """Valida se um período é válido (data_fim >= data_inicio)"""
        try:
            dt_inicio = DateUtils._parse_data_flexivel(data_inicio)
            dt_fim = DateUtils._parse_data_flexivel(data_fim)
            
            if dt_inicio is None or dt_fim is None:
                return False
            
            return dt_fim.date() >= dt_inicio.date()
        except Exception:
            return False
    
    @staticmethod
    def formatar_para_ordenacao(data_str: str) -> str:
        """Formata uma data para ordenação (YYYY-MM-DD)"""
        try:
            data_obj = DateUtils._parse_data_flexivel(data_str)
            if data_obj is None:
                return "0000-00-00"  # Data mínima para ordenação
            
            return data_obj.strftime(DateUtils.FORMATO_BANCO)
        except Exception:
            return "0000-00-00"