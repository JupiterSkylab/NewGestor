# -*- coding: utf-8 -*-
"""
Controlador Principal de Processos para o Gestor de Processos
Gerencia a lógica de controle e coordenação entre Model e View
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from tkinter import messagebox

from models.process_model import ProcessModel
from models.database_model import DatabaseManager
from models.validators import ValidationError
from services.cache_service import CacheService
from utils.date_utils import DateUtils
from utils.validation_functions import ValidationUtils
from utils.string_utils import StringUtils
from logger_config import log_operation, log_error, app_logger


class ProcessController:
    """Controlador principal para gerenciamento de processos"""
    
    def __init__(self, db_manager: DatabaseManager = None, cache_service: CacheService = None):
        self.db = db_manager or DatabaseManager()
        self.cache = cache_service or CacheService()
        self.process_model = ProcessModel(self.db, self.cache)
        self._view = None  # Será definido quando a view for conectada
        self._statistics = {
            'registros_cadastrados': 0,
            'registros_atualizados': 0,
            'registros_apagados': 0,
            'registros_exportados': 0,
            'registros_importados': 0,
            'registros_restaurados': 0
        }
    
    def set_view(self, view):
        """Define a view associada ao controlador"""
        self._view = view
    
    def cadastrar_processo(self, dados_formulario: Dict[str, Any]) -> bool:
        """Cadastra um novo processo"""
        try:
            # Extrai dados do formulário
            numero_processo = dados_formulario.get('numero_processo', '').strip()
            secretaria = dados_formulario.get('secretaria', '').split(' - ')[0] if dados_formulario.get('secretaria') else ''
            numero_licitacao = dados_formulario.get('numero_licitacao', '').strip()
            modalidade = dados_formulario.get('modalidade', '')
            situacao = dados_formulario.get('situacao', '')
            data_inicio = dados_formulario.get('data_inicio', '').strip()
            data_entrega = dados_formulario.get('data_entrega', '').strip()
            descricao = dados_formulario.get('descricao', '').strip()
            entregue_por = dados_formulario.get('entregue_por', '').strip().upper()
            devolvido_a = dados_formulario.get('devolvido_a', '').strip().upper()
            contratado = dados_formulario.get('contratado', '').strip()
            
            # Verifica se é um lembrete
            is_lembrete = dados_formulario.get('is_lembrete', False)
            if is_lembrete and descricao:
                return self._registrar_lembrete(descricao)
            
            # Valida campos obrigatórios
            if not ValidationUtils.validar_campos_obrigatorios(
                numero_processo, secretaria, data_inicio, data_entrega
            ):
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return False
            
            # Verifica se o processo já existe
            if self.process_model.exists(numero_processo):
                messagebox.showerror("Erro", f"Processo {numero_processo} já existe!")
                return False
            
            # Prepara dados para criação
            process_data = {
                'numero_processo': numero_processo,
                'secretaria': secretaria,
                'numero_licitacao': numero_licitacao,
                'modalidade': modalidade,
                'situacao': situacao,
                'data_inicio': data_inicio,
                'data_entrega': data_entrega,
                'descricao': descricao,
                'entregue_por': entregue_por,
                'devolvido_a': devolvido_a,
                'contratado': contratado
            }
            
            # Cria o processo
            success = self.process_model.create(process_data)
            
            if success:
                self._statistics['registros_cadastrados'] += 1
                
                # Atualiza autocomplete
                self._atualizar_lista_autocomplete(entregue_por, devolvido_a)
                
                # Feedback para usuário
                messagebox.showinfo("Sucesso", "Processo cadastrado com sucesso!")
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.limpar_campos()
                    self._view.listar_processos()
                    self._view.contar_registros()
                
                log_operation(app_logger, "Process created", True, f"Number: {numero_processo}")
                return True
            
            return False
            
        except ValidationError as e:
            messagebox.showerror("Erro de Validação", str(e))
            return False
        except Exception as e:
            error_msg = f"Erro ao cadastrar processo: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(app_logger, e, "Process creation failed")
            return False
    
    def atualizar_processo(self, numero_processo_original: str, dados_formulario: Dict[str, Any]) -> bool:
        """Atualiza um processo existente"""
        try:
            # Extrai dados do formulário
            numero_processo = dados_formulario.get('numero_processo', '').strip()
            secretaria = dados_formulario.get('secretaria', '').split(' - ')[0] if dados_formulario.get('secretaria') else ''
            numero_licitacao = dados_formulario.get('numero_licitacao', '').strip()
            modalidade = dados_formulario.get('modalidade', '')
            situacao = dados_formulario.get('situacao', '')
            data_inicio = dados_formulario.get('data_inicio', '').strip()
            data_entrega = dados_formulario.get('data_entrega', '').strip()
            descricao = dados_formulario.get('descricao', '').strip()
            entregue_por = dados_formulario.get('entregue_por', '').strip().upper()
            devolvido_a = dados_formulario.get('devolvido_a', '').strip().upper()
            contratado = dados_formulario.get('contratado', '').strip()
            
            # Valida campos obrigatórios
            if not ValidationUtils.validar_campos_obrigatorios(
                numero_processo, secretaria, data_inicio, data_entrega
            ):
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return False
            
            # Prepara dados para atualização
            process_data = {
                'numero_processo': numero_processo,
                'secretaria': secretaria,
                'numero_licitacao': numero_licitacao,
                'modalidade': modalidade,
                'situacao': situacao,
                'data_inicio': data_inicio,
                'data_entrega': data_entrega,
                'descricao': descricao,
                'entregue_por': entregue_por,
                'devolvido_a': devolvido_a,
                'contratado': contratado
            }
            
            # Atualiza o processo
            success = self.process_model.update(numero_processo_original, process_data)
            
            if success:
                self._statistics['registros_atualizados'] += 1
                
                # Atualiza autocomplete
                self._atualizar_lista_autocomplete(entregue_por, devolvido_a)
                
                # Feedback para usuário
                messagebox.showinfo("Sucesso", "Processo atualizado com sucesso!")
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.limpar_campos()
                    self._view.listar_processos()
                    self._view.contar_registros()
                
                log_operation(app_logger, "Process updated", True, 
                             f"Original: {numero_processo_original}, New: {numero_processo}")
                return True
            
            return False
            
        except ValidationError as e:
            messagebox.showerror("Erro de Validação", str(e))
            return False
        except Exception as e:
            error_msg = f"Erro ao atualizar processo: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(app_logger, e, "Process update failed")
            return False
    
    def excluir_processo(self, numero_processo: str) -> bool:
        """Exclui um processo (move para lixeira)"""
        try:
            # Confirma a exclusão
            if not messagebox.askyesno(
                "Confirmar Exclusão", 
                "Tem certeza que deseja excluir este processo?"
            ):
                return False
            
            # Verifica se não é o último registro
            total_processos = self.process_model.count_all()
            if total_processos <= 1:
                messagebox.showwarning("Aviso", "Não é permitido apagar todos os registros!")
                return False
            
            # Exclui o processo
            success = self.process_model.delete(numero_processo)
            
            if success:
                self._statistics['registros_apagados'] += 1
                
                # Feedback para usuário
                messagebox.showinfo("Sucesso", f"Processo {numero_processo} excluído com sucesso!")
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.limpar_campos()
                    self._view.listar_processos()
                    self._view.contar_registros()
                
                log_operation(app_logger, "Process deleted", True, f"Number: {numero_processo}")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Erro ao excluir processo: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(app_logger, e, "Process deletion failed")
            return False
    
    def buscar_processos(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca processos com base nos filtros"""
        try:
            # Extrai filtros
            termo_busca = filtros.get('termo_busca', '').strip().lower()
            secretaria = filtros.get('secretaria', '').strip()
            situacao = filtros.get('situacao', '').strip()
            modalidade = filtros.get('modalidade', '').strip()
            
            # Constrói filtros para o modelo
            search_filters = {}
            
            if secretaria:
                search_filters['secretaria'] = secretaria
            
            if situacao:
                search_filters['situacao'] = situacao
            
            if modalidade:
                search_filters['modalidade'] = modalidade
            
            # Busca processos
            if termo_busca:
                # Verifica se é busca por intervalo de datas
                if 'a' in termo_busca and len(termo_busca.replace('a', '')) >= 8:
                    return self._buscar_por_intervalo_datas(termo_busca, search_filters)
                else:
                    # Busca textual
                    search_filters['search_term'] = termo_busca
            
            processos = self.process_model.search(filters=search_filters)
            
            log_operation(app_logger, "Process search", True, 
                         f"Filters: {search_filters}, Results: {len(processos)}")
            
            return processos
            
        except Exception as e:
            log_error(app_logger, e, "Process search failed")
            return []
    
    def listar_processos(self, order_by: str = "data_registro DESC") -> List[Dict[str, Any]]:
        """Lista todos os processos"""
        try:
            processos = self.process_model.get_all(order_by=order_by)
            return processos
        except Exception as e:
            log_error(app_logger, e, "Process listing failed")
            return []
    
    def obter_processo(self, numero_processo: str) -> Optional[Dict[str, Any]]:
        """Obtém um processo específico"""
        try:
            return self.process_model.get_by_number(numero_processo)
        except Exception as e:
            log_error(app_logger, e, f"Failed to get process {numero_processo}")
            return None
    
    def restaurar_processo(self, numero_processo: str) -> bool:
        """Restaura um processo da lixeira"""
        try:
            success = self.process_model.restore_from_deleted(numero_processo)
            
            if success:
                self._statistics['registros_restaurados'] += 1
                
                # Feedback para usuário
                messagebox.showinfo("Sucesso", f"Processo {numero_processo} restaurado com sucesso!")
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.listar_processos()
                    self._view.contar_registros()
                
                log_operation(app_logger, "Process restored", True, f"Number: {numero_processo}")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Erro ao restaurar processo: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(app_logger, e, "Process restoration failed")
            return False
    
    def contar_registros(self) -> Dict[str, int]:
        """Conta registros por categoria"""
        try:
            return {
                'total': self.process_model.get_count(),
                'concluidos': self.process_model.get_count('Concluído'),
                'andamento': self.process_model.get_count('Em Andamento'),
                'excluidos': self.db.get_process_count('deleted')  # Corrigido: usar get_process_count('deleted')
            }
        except Exception as e:
            log_error(app_logger, e, "Record counting failed")
            return {'total': 0, 'concluidos': 0, 'andamento': 0, 'excluidos': 0}
    
    def obter_valores_unicos(self, campo: str) -> List[str]:
        """Obtém valores únicos de um campo"""
        try:
            return self.db.get_unique_values(campo)
        except Exception as e:
            log_error(app_logger, e, f"Failed to get unique values for {campo}")
            return []
    
    def obter_nomes_autocomplete(self) -> List[str]:
        """Obtém nomes para autocomplete"""
        try:
            # Tenta buscar do cache primeiro
            nomes_cache = self.cache.get('nomes_autocomplete')
            if nomes_cache:
                return nomes_cache
            
            # Busca do banco
            entregues = self.obter_valores_unicos('entregue_por')
            devolvidos = self.obter_valores_unicos('devolvido_a')
            
            # Combina e remove duplicatas
            nomes = list(set(entregues + devolvidos))
            nomes = [nome for nome in nomes if nome and nome.strip()]
            nomes.sort(key=str.lower)
            
            # Armazena no cache
            self.cache.set('nomes_autocomplete', nomes, 1800)  # 30 minutos
            
            return nomes
            
        except Exception as e:
            log_error(app_logger, e, "Failed to get autocomplete names")
            return []
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do controlador"""
        contagens = self.contar_registros()
        return {
            **self._statistics,
            **contagens,
            'cache_stats': self.cache.get_stats()
        }
    
    def _registrar_lembrete(self, descricao: str) -> bool:
        """Registra um lembrete (funcionalidade específica)"""
        try:
            # Implementação específica para lembretes
            # Por enquanto, apenas registra como processo especial
            data_atual = DateUtils.get_current_date_formatted()
            
            lembrete_data = {
                'numero_processo': f"LEMBRETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'secretaria': 'LEMBRETE',
                'numero_licitacao': '',
                'modalidade': 'Lembrete',
                'situacao': 'Em Andamento',
                'data_inicio': data_atual,
                'data_entrega': '',
                'descricao': descricao,
                'entregue_por': '',
                'devolvido_a': '',
                'contratado': ''
            }
            
            success = self.process_model.create(lembrete_data)
            
            if success:
                messagebox.showinfo("Sucesso", "Lembrete cadastrado com sucesso!")
                log_operation(app_logger, "Reminder created", True, f"Description: {descricao[:50]}...")
            
            return success
            
        except Exception as e:
            log_error(app_logger, e, "Reminder creation failed")
            return False
    
    def _atualizar_lista_autocomplete(self, entregue_por: str = None, devolvido_a: str = None):
        """Atualiza a lista de autocompletar com novos nomes"""
        try:
            nomes_atuais = self.obter_nomes_autocomplete()
            atualizado = False
            
            if entregue_por and entregue_por not in nomes_atuais:
                nomes_atuais.append(entregue_por)
                atualizado = True
            
            if devolvido_a and devolvido_a not in nomes_atuais:
                nomes_atuais.append(devolvido_a)
                atualizado = True
            
            if atualizado:
                nomes_atuais.sort(key=str.lower)
                self.cache.set('nomes_autocomplete', nomes_atuais, 1800)
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.atualizar_autocomplete(nomes_atuais)
                    
        except Exception as e:
            log_error(app_logger, e, "Autocomplete update failed")
    
    def _buscar_por_intervalo_datas(self, termo_busca: str, filtros_base: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca processos por intervalo de datas"""
        try:
            # Parse do intervalo (formato: ddmmaaDDMM)
            partes = termo_busca.split('a')
            if len(partes) != 2:
                return []
            
            data_inicio_str = partes[0].strip()
            data_fim_str = partes[1].strip()
            
            # Converte para formato de data
            ano_atual = datetime.now().year
            
            if len(data_inicio_str) == 4:  # ddmm
                data_inicio = f"{data_inicio_str[:2]}/{data_inicio_str[2:]}/{ano_atual}"
            else:
                return []
            
            if len(data_fim_str) == 4:  # ddmm
                data_fim = f"{data_fim_str[:2]}/{data_fim_str[2:]}/{ano_atual}"
            else:
                return []
            
            # Valida datas
            if not DateUtils.validar_data_brasileira(data_inicio) or not DateUtils.validar_data_brasileira(data_fim):
                return []
            
            # Busca por intervalo
            filtros_base['data_inicio_range'] = (data_inicio, data_fim)
            return self.process_model.search(filters=filtros_base)
            
        except Exception as e:
            log_error(app_logger, e, "Date range search failed")
            return []
    
    def close(self):
        """Fecha conexões e limpa recursos"""
        if self.process_model:
            self.process_model.close()
        if self.db:
            self.db.close()


# Instância global do controlador
_process_controller = None

def get_process_controller() -> ProcessController:
    """Retorna a instância global do controlador de processos"""
    global _process_controller
    if _process_controller is None:
        _process_controller = ProcessController()
    return _process_controller

def set_process_controller(controller: ProcessController):
    """Define a instância global do controlador de processos"""
    global _process_controller
    _process_controller = controller