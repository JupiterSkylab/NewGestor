# -*- coding: utf-8 -*-
"""
Controlador de Backup para o Gestor de Processos
Gerencia a lógica de controle para operações de backup (Git, Banco)
"""

from typing import Dict, Any, Optional
from tkinter import messagebox
import threading
import time

from services.backup_service import BackupService
from logger_config import log_operation, log_error, backup_logger


class BackupController:
    """Controlador para operações de backup"""
    
    def __init__(self, backup_service: BackupService = None):
        self.backup_service = backup_service or BackupService()
        self._view = None
        self._auto_backup_thread = None
        self._stop_auto_backup = False
        self._statistics = {
            'git_backups': 0,
            'database_exports': 0,
            'database_imports': 0,
            'auto_backups': 0,
            'failed_backups': 0
        }
    
    def set_view(self, view):
        """Define a view associada ao controlador"""
        self._view = view
    
    def realizar_backup_git(self, mostrar_feedback: bool = True) -> bool:
        """Realiza backup Git manual"""
        try:
            success = self.backup_service.backup_git()
            
            if success:
                self._statistics['git_backups'] += 1
                if mostrar_feedback:
                    messagebox.showinfo("Sucesso", "Backup Git realizado com sucesso!")
                log_operation(backup_logger, "Manual Git backup completed", True)
            else:
                self._statistics['failed_backups'] += 1
                if mostrar_feedback:
                    messagebox.showerror("Erro", "Falha ao realizar backup Git. Verifique os logs.")
                log_error(backup_logger, "Manual Git backup failed", "Git backup operation failed")
            
            return success
            
        except Exception as e:
            self._statistics['failed_backups'] += 1
            error_msg = f"Erro ao realizar backup Git: {str(e)}"
            if mostrar_feedback:
                messagebox.showerror("Erro", error_msg)
            log_error(backup_logger, e, "Manual Git backup failed")
            return False
    
    def realizar_backup_git_async(self) -> None:
        """Realiza backup Git assíncrono"""
        try:
            self.backup_service.backup_git_async()
            log_operation(backup_logger, "Async Git backup initiated", True)
        except Exception as e:
            log_error(backup_logger, e, "Failed to initiate async Git backup")
    
    def verificar_e_backup_automatico(self) -> bool:
        """Verifica mudanças e realiza backup automático se necessário"""
        try:
            mudancas_detectadas = self.backup_service.verificar_mudancas_e_backup()
            
            if mudancas_detectadas:
                self._statistics['auto_backups'] += 1
                log_operation(backup_logger, "Auto backup triggered", True)
            
            return mudancas_detectadas
            
        except Exception as e:
            self._statistics['failed_backups'] += 1
            log_error(backup_logger, e, "Auto backup check failed")
            return False
    
    def exportar_banco_dados(self, caminho_banco: str, arquivo_destino: str = None) -> bool:
        """Exporta backup do banco de dados"""
        try:
            success = self.backup_service.exportar_banco(caminho_banco, arquivo_destino)
            
            if success:
                self._statistics['database_exports'] += 1
                log_operation(backup_logger, "Database export completed", True, 
                             f"Source: {caminho_banco}")
            else:
                self._statistics['failed_backups'] += 1
            
            return success
            
        except Exception as e:
            self._statistics['failed_backups'] += 1
            error_msg = f"Erro ao exportar banco: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(backup_logger, e, "Database export failed")
            return False
    
    def importar_banco_dados(self, caminho_banco: str, arquivo_origem: str = None) -> bool:
        """Importa banco de dados de backup"""
        try:
            success = self.backup_service.importar_banco(caminho_banco, arquivo_origem)
            
            if success:
                self._statistics['database_imports'] += 1
                
                # Atualiza interface se disponível
                if self._view:
                    self._view.listar_processos()
                    self._view.contar_registros()
                
                log_operation(backup_logger, "Database import completed", True, 
                             f"Destination: {caminho_banco}")
            else:
                self._statistics['failed_backups'] += 1
            
            return success
            
        except Exception as e:
            self._statistics['failed_backups'] += 1
            error_msg = f"Erro ao importar banco: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(backup_logger, e, "Database import failed")
            return False
    
    def import_database(self) -> bool:
        """Método wrapper para importação de banco de dados"""
        try:
            # Obtém o caminho do banco da view se disponível
            if hasattr(self._view, 'caminho_banco'):
                caminho_banco = self._view.caminho_banco
            else:
                # Fallback para caminho padrão
                caminho_banco = "banco_dados.db"
            
            return self.importar_banco_dados(caminho_banco)
            
        except Exception as e:
            error_msg = f"Erro ao importar banco: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(backup_logger, e, "Import database wrapper failed")
            return False

    def criar_backup_completo(self, caminho_banco: str, incluir_git: bool = True) -> Dict[str, bool]:
        """Cria backup completo (banco + git)"""
        try:
            resultados = self.backup_service.criar_backup_completo(caminho_banco, incluir_git)
            
            # Atualiza estatísticas
            if resultados.get('banco'):
                self._statistics['database_exports'] += 1
            
            if resultados.get('git'):
                self._statistics['git_backups'] += 1
            
            if not any(resultados.values()):
                self._statistics['failed_backups'] += 1
            
            # Feedback para usuário
            sucessos = [k for k, v in resultados.items() if v]
            falhas = [k for k, v in resultados.items() if not v]
            
            if sucessos and not falhas:
                messagebox.showinfo("Sucesso", f"Backup completo realizado: {', '.join(sucessos)}")
            elif sucessos and falhas:
                messagebox.showwarning(
                    "Parcial", 
                    f"Backup parcial:\nSucesso: {', '.join(sucessos)}\nFalha: {', '.join(falhas)}"
                )
            else:
                messagebox.showerror("Erro", "Falha no backup completo. Verifique os logs.")
            
            log_operation(backup_logger, "Complete backup attempted", True, 
                         f"Results: {resultados}")
            
            return resultados
            
        except Exception as e:
            self._statistics['failed_backups'] += 1
            error_msg = f"Erro no backup completo: {str(e)}"
            messagebox.showerror("Erro", error_msg)
            log_error(backup_logger, e, "Complete backup failed")
            return {'banco': False, 'git': False}
    
    def iniciar_backup_automatico(self, intervalo_segundos: int = 300) -> bool:
        """Inicia backup automático em thread separada"""
        try:
            if self._auto_backup_thread and self._auto_backup_thread.is_alive():
                log_operation(backup_logger, "Auto backup already running", False)
                return False
            
            self._stop_auto_backup = False
            self._auto_backup_thread = threading.Thread(
                target=self._auto_backup_worker,
                args=(intervalo_segundos,),
                daemon=True
            )
            self._auto_backup_thread.start()
            
            log_operation(backup_logger, "Auto backup started", True, 
                         f"Interval: {intervalo_segundos}s")
            return True
            
        except Exception as e:
            log_error(backup_logger, e, "Failed to start auto backup")
            return False
    
    def parar_backup_automatico(self) -> bool:
        """Para o backup automático"""
        try:
            self._stop_auto_backup = True
            
            if self._auto_backup_thread and self._auto_backup_thread.is_alive():
                # Aguarda até 5 segundos para a thread terminar
                self._auto_backup_thread.join(timeout=5)
            
            log_operation(backup_logger, "Auto backup stopped", True)
            return True
            
        except Exception as e:
            log_error(backup_logger, e, "Failed to stop auto backup")
            return False
    
    def configurar_backup_automatico(self, habilitado: bool, intervalo: int = None) -> bool:
        """Configura backup automático"""
        try:
            self.backup_service.configurar_backup_automatico(habilitado, intervalo)
            
            if habilitado:
                if intervalo:
                    return self.iniciar_backup_automatico(intervalo)
                else:
                    return self.iniciar_backup_automatico()
            else:
                return self.parar_backup_automatico()
                
        except Exception as e:
            log_error(backup_logger, e, "Failed to configure auto backup")
            return False
    
    def obter_status_repositorio(self) -> Dict[str, Any]:
        """Obtém status do repositório Git"""
        try:
            return self.backup_service.get_status_repositorio()
        except Exception as e:
            log_error(backup_logger, e, "Failed to get repository status")
            return {'erro': str(e)}
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas de backup"""
        status_repo = self.obter_status_repositorio()
        
        return {
            **self._statistics,
            'auto_backup_ativo': self._auto_backup_thread and self._auto_backup_thread.is_alive(),
            'repositorio_status': status_repo
        }
    
    def testar_configuracao_git(self) -> Dict[str, Any]:
        """Testa a configuração do Git"""
        try:
            status = self.obter_status_repositorio()
            
            if 'erro' in status:
                return {
                    'sucesso': False,
                    'erro': status['erro'],
                    'sugestoes': [
                        "Verifique se o Git está instalado",
                        "Verifique se o caminho do repositório está correto",
                        "Verifique as permissões de acesso"
                    ]
                }
            
            return {
                'sucesso': True,
                'status': status,
                'mensagem': 'Configuração Git OK'
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e),
                'sugestoes': ["Verifique a configuração do Git"]
            }
    
    def _auto_backup_worker(self, intervalo_segundos: int):
        """Worker para backup automático"""
        while not self._stop_auto_backup:
            try:
                # Aguarda o intervalo ou até ser interrompido
                for _ in range(intervalo_segundos):
                    if self._stop_auto_backup:
                        break
                    time.sleep(1)
                
                if not self._stop_auto_backup:
                    self.verificar_e_backup_automatico()
                    
            except Exception as e:
                log_error(backup_logger, e, "Auto backup worker error")
                # Continua executando mesmo com erro
                time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente
    
    def close(self):
        """Fecha recursos do controlador"""
        self.parar_backup_automatico()


# Instância global do controlador
_backup_controller = None

def get_backup_controller() -> BackupController:
    """Retorna a instância global do controlador de backup"""
    global _backup_controller
    if _backup_controller is None:
        _backup_controller = BackupController()
    return _backup_controller

def set_backup_controller(controller: BackupController):
    """Define a instância global do controlador de backup"""
    global _backup_controller
    _backup_controller = controller