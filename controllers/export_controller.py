# -*- coding: utf-8 -*-
"""
Controlador de Exportação para o Gestor de Processos
Gerencia a lógica de controle para exportações (PDF, Excel, Banco)
"""

from typing import List, Dict, Any, Optional
from tkinter import messagebox

from models.process_model import ProcessModel
from services.export_service import ExportService
from logger_config import log_operation, log_error, export_logger


class ExportController:
    """Controlador para operações de exportação"""
    
    def __init__(self, process_model: ProcessModel = None, export_service: ExportService = None):
        self.process_model = process_model or ProcessModel()
        self.export_service = export_service or ExportService()
        self._view = None
        self._statistics = {
            'exports_pdf': 0,
            'exports_excel': 0,
            'exports_database': 0
        }
    
    def set_view(self, view):
        """Define a view associada ao controlador"""
        self._view = view
    
    def exportar_pdf_selecionados(self, processos_selecionados: List[str], filtros: Dict[str, str] = None) -> bool:
        """Exporta processos selecionados para PDF"""
        try:
            if not processos_selecionados:
                messagebox.showwarning("Aviso", "Selecione pelo menos um processo para exportar!")
                return False
            
            # Busca dados dos processos selecionados
            dados_processos = []
            for numero_processo in processos_selecionados:
                processo = self.process_model.get_by_number(numero_processo)
                if processo:
                    dados_processos.append(processo)
            
            if not dados_processos:
                messagebox.showerror("Erro", "Nenhum processo válido encontrado para exportação!")
                return False
            
            # Exporta para PDF
            success = self.export_service.exportar_pdf(dados_processos, filtros)
            
            if success:
                self._statistics['exports_pdf'] += 1
                log_operation(export_logger, "PDF export completed", True, 
                             f"Processes: {len(dados_processos)}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar PDF: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "PDF export failed")
            return False
    
    def exportar_excel_selecionados(self, processos_selecionados: List[str], filtros: Dict[str, str] = None) -> bool:
        """Exporta processos selecionados para Excel"""
        try:
            if not processos_selecionados:
                messagebox.showwarning("Aviso", "Selecione pelo menos um processo para exportar!")
                return False
            
            # Busca dados dos processos selecionados
            dados_processos = []
            for numero_processo in processos_selecionados:
                processo = self.process_model.get_by_number(numero_processo)
                if processo:
                    dados_processos.append(processo)
            
            if not dados_processos:
                messagebox.showerror("Erro", "Nenhum processo válido encontrado para exportação!")
                return False
            
            # Exporta para Excel
            success = self.export_service.exportar_excel(dados_processos, filtros)
            
            if success:
                self._statistics['exports_excel'] += 1
                log_operation(export_logger, "Excel export completed", True, 
                             f"Processes: {len(dados_processos)}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar Excel: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Excel export failed")
            return False
    
    def exportar_pdf_todos(self, filtros: Dict[str, str] = None) -> bool:
        """Exporta todos os processos para PDF"""
        try:
            # Busca todos os processos
            todos_processos = self.process_model.get_all()
            
            if not todos_processos:
                messagebox.showwarning("Aviso", "Nenhum processo encontrado para exportação!")
                return False
            
            # Confirma a exportação
            if not messagebox.askyesno(
                "Confirmar Exportação", 
                f"Deseja exportar todos os {len(todos_processos)} processos para PDF?"
            ):
                return False
            
            # Exporta para PDF
            success = self.export_service.exportar_pdf(todos_processos, filtros)
            
            if success:
                self._statistics['exports_pdf'] += 1
                log_operation(export_logger, "Full PDF export completed", True, 
                             f"Processes: {len(todos_processos)}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar PDF: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Full PDF export failed")
            return False
    
    def exportar_excel_todos(self, filtros: Dict[str, str] = None) -> bool:
        """Exporta todos os processos para Excel"""
        try:
            # Busca todos os processos
            todos_processos = self.process_model.get_all()
            
            if not todos_processos:
                messagebox.showwarning("Aviso", "Nenhum processo encontrado para exportação!")
                return False
            
            # Confirma a exportação
            if not messagebox.askyesno(
                "Confirmar Exportação", 
                f"Deseja exportar todos os {len(todos_processos)} processos para Excel?"
            ):
                return False
            
            # Exporta para Excel
            success = self.export_service.exportar_excel(todos_processos, filtros)
            
            if success:
                self._statistics['exports_excel'] += 1
                log_operation(export_logger, "Full Excel export completed", True, 
                             f"Processes: {len(todos_processos)}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar Excel: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Full Excel export failed")
            return False
    
    def exportar_pdf_filtrados(self, filtros_busca: Dict[str, Any]) -> bool:
        """Exporta processos filtrados para PDF"""
        try:
            # Busca processos com filtros
            processos_filtrados = self.process_model.search(filters=filtros_busca)
            
            if not processos_filtrados:
                messagebox.showwarning("Aviso", "Nenhum processo encontrado com os filtros aplicados!")
                return False
            
            # Confirma a exportação
            if not messagebox.askyesno(
                "Confirmar Exportação", 
                f"Deseja exportar os {len(processos_filtrados)} processos filtrados para PDF?"
            ):
                return False
            
            # Prepara informações dos filtros para o relatório
            info_filtros = self._preparar_info_filtros(filtros_busca)
            
            # Exporta para PDF
            success = self.export_service.exportar_pdf(processos_filtrados, info_filtros)
            
            if success:
                self._statistics['exports_pdf'] += 1
                log_operation(export_logger, "Filtered PDF export completed", True, 
                             f"Processes: {len(processos_filtrados)}, Filters: {filtros_busca}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar PDF filtrado: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Filtered PDF export failed")
            return False
    
    def exportar_excel_filtrados(self, filtros_busca: Dict[str, Any]) -> bool:
        """Exporta processos filtrados para Excel"""
        try:
            # Busca processos com filtros
            processos_filtrados = self.process_model.search(filters=filtros_busca)
            
            if not processos_filtrados:
                messagebox.showwarning("Aviso", "Nenhum processo encontrado com os filtros aplicados!")
                return False
            
            # Confirma a exportação
            if not messagebox.askyesno(
                "Confirmar Exportação", 
                f"Deseja exportar os {len(processos_filtrados)} processos filtrados para Excel?"
            ):
                return False
            
            # Prepara informações dos filtros para o relatório
            info_filtros = self._preparar_info_filtros(filtros_busca)
            
            # Exporta para Excel
            success = self.export_service.exportar_excel(processos_filtrados, info_filtros)
            
            if success:
                self._statistics['exports_excel'] += 1
                log_operation(export_logger, "Filtered Excel export completed", True, 
                             f"Processes: {len(processos_filtrados)}, Filters: {filtros_busca}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar Excel filtrado: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Filtered Excel export failed")
            return False
    
    def exportar_banco_dados(self, caminho_banco: str) -> bool:
        """Exporta backup do banco de dados"""
        try:
            success = self.export_service.exportar_banco(caminho_banco)
            
            if success:
                self._statistics['exports_database'] += 1
                log_operation(export_logger, "Database export completed", True, 
                             f"Source: {caminho_banco}")
            
            return success
            
        except Exception as e:
            error_msg = f"Erro ao exportar banco: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(export_logger, e, "Database export failed")
            return False
    
    def obter_processos_selecionados_da_view(self) -> List[str]:
        """Obtém lista de processos selecionados da view"""
        if not self._view:
            return []
        
        try:
            return self._view.obter_processos_selecionados()
        except Exception as e:
            log_error(export_logger, e, "Failed to get selected processes from view")
            return []
    
    def obter_filtros_ativos_da_view(self) -> Dict[str, str]:
        """Obtém filtros ativos da view"""
        if not self._view:
            return {}
        
        try:
            return self._view.obter_filtros_ativos()
        except Exception as e:
            log_error(export_logger, e, "Failed to get active filters from view")
            return {}
    
    def exportar_selecionados_pdf(self) -> bool:
        """Exporta processos selecionados na view para PDF"""
        processos_selecionados = self.obter_processos_selecionados_da_view()
        filtros = self.obter_filtros_ativos_da_view()
        return self.exportar_pdf_selecionados(processos_selecionados, filtros)
    
    def exportar_selecionados_excel(self) -> bool:
        """Exporta processos selecionados na view para Excel"""
        processos_selecionados = self.obter_processos_selecionados_da_view()
        filtros = self.obter_filtros_ativos_da_view()
        return self.exportar_excel_selecionados(processos_selecionados, filtros)
    
    def exportar_todos_pdf(self) -> bool:
        """Exporta todos os processos para PDF"""
        filtros = self.obter_filtros_ativos_da_view()
        return self.exportar_pdf_todos(filtros)
    
    def exportar_todos_excel(self) -> bool:
        """Exporta todos os processos para Excel"""
        filtros = self.obter_filtros_ativos_da_view()
        return self.exportar_excel_todos(filtros)
    
    def exportar_filtrados_pdf(self) -> bool:
        """Exporta processos filtrados para PDF"""
        filtros_busca = self._obter_filtros_busca_da_view()
        return self.exportar_pdf_filtrados(filtros_busca)
    
    def exportar_filtrados_excel(self) -> bool:
        """Exporta processos filtrados para Excel"""
        filtros_busca = self._obter_filtros_busca_da_view()
        return self.exportar_excel_filtrados(filtros_busca)
    
    def obter_estatisticas(self) -> Dict[str, int]:
        """Obtém estatísticas de exportação"""
        return self._statistics.copy()
    
    def _preparar_info_filtros(self, filtros_busca: Dict[str, Any]) -> Dict[str, str]:
        """Prepara informações dos filtros para exibição no relatório"""
        info_filtros = {}
        
        if filtros_busca.get('search_term'):
            info_filtros['Termo de Busca'] = filtros_busca['search_term']
        
        if filtros_busca.get('secretaria'):
            info_filtros['Secretaria'] = filtros_busca['secretaria']
        
        if filtros_busca.get('situacao'):
            info_filtros['Situação'] = filtros_busca['situacao']
        
        if filtros_busca.get('modalidade'):
            info_filtros['Modalidade'] = filtros_busca['modalidade']
        
        if filtros_busca.get('data_inicio_range'):
            data_inicio, data_fim = filtros_busca['data_inicio_range']
            info_filtros['Período'] = f"{data_inicio} a {data_fim}"
        
        return info_filtros
    
    def _obter_filtros_busca_da_view(self) -> Dict[str, Any]:
        """Obtém filtros de busca da view"""
        if not self._view:
            return {}
        
        try:
            return self._view.obter_filtros_busca()
        except Exception as e:
            log_error(export_logger, e, "Failed to get search filters from view")
            return {}
    
    def close(self):
        """Fecha recursos do controlador"""
        if self.process_model:
            self.process_model.close()


# Instância global do controlador
_export_controller = None

def get_export_controller() -> ExportController:
    """Retorna a instância global do controlador de exportação"""
    global _export_controller
    if _export_controller is None:
        _export_controller = ExportController()
    return _export_controller

def set_export_controller(controller: ExportController):
    """Define a instância global do controlador de exportação"""
    global _export_controller
    _export_controller = controller