# -*- coding: utf-8 -*-
"""
Modelo de dados para processos do Gestor de Processos
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .database_model import DatabaseManager, DatabaseError
from .validators import DataValidator, DateFormatter, ValidationError
from logger_config import app_logger, log_operation, log_error
from services.cache_service import CacheService

class ProcessModel:
    """Modelo principal para gerenciamento de processos"""
    
    def __init__(self, db_manager: DatabaseManager = None, cache_service: CacheService = None):
        self.db = db_manager or DatabaseManager()
        self.cache = cache_service or CacheService()
        self.validator = DataValidator()
        self.date_formatter = DateFormatter()
    
    def create(self, data: Dict[str, Any]) -> int:
        """Cria um novo processo"""
        try:
            # Valida e limpa os dados
            validated_data = self.validator.validar_processo_completo(data)
            
            # Converte datas para formato do banco
            validated_data['data_inicio'] = self.date_formatter.para_banco(
                validated_data['data_inicio']
            )
            
            if validated_data['data_entrega']:
                validated_data['data_entrega'] = self.date_formatter.para_banco(
                    validated_data['data_entrega']
                )
            
            # Verifica se o processo já existe
            if self.exists(validated_data['numero_processo']):
                raise ValidationError(f"Processo {validated_data['numero_processo']} já existe")
            
            # Insere no banco
            process_id = self.db.insert_process(validated_data)
            
            # Invalida caches relacionados
            self._invalidate_related_caches()
            
            # Atualiza cache de autocompletar
            self._update_autocomplete_cache(
                validated_data.get('entregue_por'),
                validated_data.get('devolvido_a')
            )
            
            log_operation(app_logger, "Process created", True, 
                         f"ID: {process_id}, Number: {validated_data['numero_processo']}")
            
            return process_id
            
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            log_error(app_logger, e, "Process creation failed")
            raise ValidationError(f"Erro interno ao criar processo: {e}")
    
    def update(self, numero_processo: str, data: Dict[str, Any]) -> bool:
        """Atualiza um processo existente"""
        try:
            # Valida e limpa os dados
            validated_data = self.validator.validar_processo_completo(data)
            
            # Converte datas para formato do banco
            validated_data['data_inicio'] = self.date_formatter.para_banco(
                validated_data['data_inicio']
            )
            
            if validated_data['data_entrega']:
                validated_data['data_entrega'] = self.date_formatter.para_banco(
                    validated_data['data_entrega']
                )
            
            # Verifica se está tentando alterar para um número que já existe
            if (validated_data['numero_processo'] != numero_processo and 
                self.exists(validated_data['numero_processo'])):
                raise ValidationError(f"Processo {validated_data['numero_processo']} já existe")
            
            # Atualiza no banco
            success = self.db.update_process(numero_processo, validated_data)
            
            if success:
                # Invalida caches relacionados
                self._invalidate_related_caches()
                
                # Atualiza cache de autocompletar
                self._update_autocomplete_cache(
                    validated_data.get('entregue_por'),
                    validated_data.get('devolvido_a')
                )
                
                log_operation(app_logger, "Process updated", True, 
                             f"Number: {numero_processo} -> {validated_data['numero_processo']}")
            
            return success
            
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            log_error(app_logger, e, "Process update failed")
            raise ValidationError(f"Erro interno ao atualizar processo: {e}")
    
    def delete(self, numero_processo: str) -> bool:
        """Exclui um processo (move para lixeira)"""
        try:
            success = self.db.delete_process(numero_processo)
            
            if success:
                # Invalida caches relacionados
                self._invalidate_related_caches()
                
                log_operation(app_logger, "Process deleted", True, 
                             f"Number: {numero_processo}")
            
            return success
            
        except DatabaseError:
            raise
        except Exception as e:
            log_error(app_logger, e, "Process deletion failed")
            raise ValidationError(f"Erro interno ao excluir processo: {e}")
    
    def get_by_number(self, numero_processo: str) -> Optional[Dict[str, Any]]:
        """Busca um processo pelo número"""
        try:
            # Tenta buscar no cache primeiro
            cache_key = f"process_{numero_processo}"
            cached_process = self.cache.get(cache_key)
            
            if cached_process:
                return cached_process
            
            # Busca no banco
            process = self.db.get_process_by_number(numero_processo)
            
            if process:
                # Formata datas para exibição
                process = self._format_process_for_display(process)
                
                # Armazena no cache
                self.cache.set(cache_key, process, ttl=300)  # 5 minutos
            
            return process
            
        except Exception as e:
            log_error(app_logger, e, f"Get process by number failed: {numero_processo}")
            return None
    
    def search(self, filters: Dict[str, Any] = None, order_by: str = "data_registro DESC") -> List[Dict[str, Any]]:
        """Busca processos com filtros opcionais"""
        try:
            # Gera chave de cache baseada nos filtros
            cache_key = f"search_{hash(str(sorted((filters or {}).items())))}"
            cached_results = self.cache.get(cache_key)
            
            if cached_results:
                return cached_results
            
            # Busca no banco
            processes = self.db.search_processes(filters, order_by)
            
            # Formata datas para exibição
            formatted_processes = [
                self._format_process_for_display(process) 
                for process in processes
            ]
            
            # Armazena no cache por 2 minutos (busca é mais volátil)
            self.cache.set(cache_key, formatted_processes, ttl=120)
            
            return formatted_processes
            
        except Exception as e:
            log_error(app_logger, e, "Search processes failed")
            return []
    
    def get_all(self, order_by: str = "data_registro DESC") -> List[Dict[str, Any]]:
        """Obtém todos os processos"""
        return self.search(order_by=order_by)
    
    def exists(self, numero_processo: str) -> bool:
        """Verifica se um processo existe"""
        try:
            process = self.db.get_process_by_number(numero_processo)
            return process is not None
        except Exception:
            return False
    
    def get_count(self, status: str = None) -> int:
        """Obtém contagem de processos por status"""
        try:
            # Tenta buscar no cache primeiro
            cache_key = f"count_{status or 'all'}"
            cached_count = self.cache.get(cache_key)
            
            if cached_count is not None:
                return cached_count
            
            # Busca no banco
            count = self.db.get_process_count(status)
            
            # Armazena no cache por 5 minutos
            self.cache.set(cache_key, count, ttl=300)
            
            return count
            
        except Exception as e:
            log_error(app_logger, e, f"Get count failed for status: {status}")
            return 0
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas dos processos"""
        try:
            cache_key = "statistics"
            cached_stats = self.cache.get(cache_key)
            
            if cached_stats:
                return cached_stats
            
            stats = {
                'total': self.get_count(),
                'em_andamento': self.get_count('Em Andamento'),
                'concluido': self.get_count('Concluído')
            }
            
            # Cache por 5 minutos
            self.cache.set(cache_key, stats, ttl=300)
            
            return stats
            
        except Exception as e:
            log_error(app_logger, e, "Get statistics failed")
            return {'total': 0, 'em_andamento': 0, 'concluido': 0}
    
    def get_autocomplete_data(self, field: str) -> List[str]:
        """Obtém dados para autocompletar"""
        try:
            cache_key = f"autocomplete_{field}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            # Busca valores únicos no banco
            values = self.db.get_unique_values(field)
            
            # Cache por 10 minutos
            self.cache.set(cache_key, values, ttl=600)
            
            return values
            
        except Exception as e:
            log_error(app_logger, e, f"Get autocomplete data failed for field: {field}")
            return []
    
    def cleanup_old_deleted(self, days: int = 30) -> int:
        """Remove registros excluídos antigos"""
        try:
            return self.db.cleanup_old_deleted(days)
        except Exception as e:
            log_error(app_logger, e, "Cleanup old deleted records failed")
            return 0
    
    def _format_process_for_display(self, process: Dict[str, Any]) -> Dict[str, Any]:
        """Formata um processo para exibição"""
        if not process:
            return process
        
        formatted = dict(process)
        
        # Formata datas
        if formatted.get('data_registro'):
            formatted['data_registro'] = self.date_formatter.formatar_data_hora_str(
                formatted['data_registro']
            )
        
        if formatted.get('data_inicio'):
            formatted['data_inicio'] = self.date_formatter.para_exibicao(
                formatted['data_inicio']
            )
        
        if formatted.get('data_entrega'):
            formatted['data_entrega'] = self.date_formatter.para_exibicao(
                formatted['data_entrega']
            )
        
        # Garante que contratado está em maiúsculas
        if formatted.get('contratado'):
            formatted['contratado'] = formatted['contratado'].upper()
        
        return formatted
    
    def _invalidate_related_caches(self):
        """Invalida caches relacionados a processos"""
        cache_keys = [
            'count_all', 'count_Em Andamento', 'count_Concluído',
            'statistics', 'autocomplete_entregue_por', 'autocomplete_devolvido_a'
        ]
        
        for key in cache_keys:
            self.cache.invalidate(key)
        
        # Invalida caches de busca (mais complexo, limpa tudo que começa com 'search_')
        self.cache.clear_pattern('search_*')
    
    def _update_autocomplete_cache(self, entregue_por: str = None, devolvido_a: str = None):
        """Atualiza cache de autocompletar com novos valores"""
        if entregue_por:
            self.cache.invalidate('autocomplete_entregue_por')
        
        if devolvido_a:
            self.cache.invalidate('autocomplete_devolvido_a')
    
    def close(self):
        """Fecha conexões e limpa recursos"""
        if self.db:
            self.db.close()