# -*- coding: utf-8 -*-
"""
Serviço de Backup para o Gestor de Processos
Implementa backup automático via Git e importação/exportação de banco
"""

import os
import shutil
import sqlite3
import subprocess
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from tkinter import filedialog, messagebox

from config import BACKUP_CONFIG
from logger_config import log_operation, log_error, backup_logger


class BackupService:
    """Serviço para gerenciar backups automáticos e manuais"""
    
    def __init__(self):
        self.repo_path = BACKUP_CONFIG.get('repo_path', '')
        self.branch = BACKUP_CONFIG.get('branch', 'master')
        self.auto_backup_enabled = BACKUP_CONFIG.get('auto_backup', True)
        self.backup_interval = BACKUP_CONFIG.get('backup_interval', 300)
        self._backup_thread = None
        self._stop_backup = False
    
    def backup_git(self) -> bool:
        """Realiza backup automático para o repositório Git"""
        try:
            if not self.repo_path or not os.path.isdir(self.repo_path):
                log_error(f"Diretório do projeto não encontrado: {self.repo_path}")
                return False
            
            # Salva o diretório atual
            diretorio_atual = os.getcwd()
            
            try:
                # Muda para o diretório do projeto
                os.chdir(self.repo_path)
                
                # Verifica se é um repositório Git
                if not os.path.isdir(os.path.join(self.repo_path, ".git")):
                    log_error(f"Repositório Git não encontrado em: {self.repo_path}")
                    return False
                
                # Adicionar arquivos ao git
                result_add = subprocess.run(
                    ["git", "add", "."], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
                if result_add.returncode != 0:
                    log_error(f"Erro ao adicionar arquivos ao Git: {result_add.stderr}")
                    return False
                
                # Criar commit
                commit_message = f"Backup automático - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                result_commit = subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
                # Se não há mudanças, não é erro
                if "nothing to commit" in result_commit.stdout:
                    log_operation("Nenhuma mudança para fazer commit")
                    return True
                
                if result_commit.returncode != 0:
                    log_error(f"Erro ao fazer commit: {result_commit.stderr}")
                    return False
                
                # Enviar para o repositório remoto
                result_push = subprocess.run(
                    ["git", "push", "origin", self.branch],
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
                if result_push.returncode != 0:
                    log_error(f"Erro ao fazer push: {result_push.stderr}")
                    return False
                
                log_operation(f"Backup Git realizado com sucesso: {commit_message}")
                return True
                
            finally:
                # Restaura o diretório original
                os.chdir(diretorio_atual)
                
        except FileNotFoundError:
            log_error("Git não encontrado. Verifique se o Git está instalado e no PATH.")
            return False
        except PermissionError:
            log_error(f"Sem permissão para acessar o diretório: {self.repo_path}")
            return False
        except Exception as e:
            log_error(f"Erro durante backup Git: {e}")
            return False
    
    def backup_git_async(self) -> None:
        """Executa backup Git em thread separada"""
        def _backup_thread():
            try:
                self.backup_git()
            except Exception as e:
                log_error(f"Erro no backup Git assíncrono: {e}")
        
        thread = threading.Thread(target=_backup_thread, daemon=True)
        thread.start()
    
    def verificar_mudancas_e_backup(self) -> bool:
        """Verifica se há mudanças no repositório Git e inicia backup se necessário"""
        try:
            if not self.repo_path or not os.path.isdir(self.repo_path):
                log_error(f"Diretório do projeto não encontrado: {self.repo_path}")
                return False
            
            # Salva o diretório atual
            diretorio_atual = os.getcwd()
            
            try:
                # Muda para o diretório do projeto
                os.chdir(self.repo_path)
                
                # Verifica se há um repositório Git
                if not os.path.isdir(os.path.join(self.repo_path, ".git")):
                    log_error(f"Repositório Git não encontrado em: {self.repo_path}")
                    return False
                
                # Verifica o status do Git
                result_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Verifica se há mudanças
                if result_status.returncode == 0 and result_status.stdout.strip():
                    log_operation("Mudanças detectadas. Iniciando backup Git...")
                    self.backup_git_async()
                    return True
                else:
                    log_operation("Nenhuma mudança detectada. Backup Git não necessário.")
                    return False
                    
            finally:
                # Restaura o diretório original
                os.chdir(diretorio_atual)
                
        except FileNotFoundError:
            log_error("Git não encontrado. Verifique se o Git está instalado e no PATH.")
            return False
        except Exception as e:
            log_error(f"Erro ao verificar mudanças Git: {e}")
            return False
    
    def _limitar_backups(self, max_backups=10):
        """Limita o número de backups mantidos no diretório de backup"""
        try:
            if not os.path.exists(self.repo_path):
                return
                
            # Lista todos os arquivos de backup
            arquivos = [os.path.join(self.repo_path, f) for f in os.listdir(self.repo_path) 
                       if f.endswith('.db') and os.path.isfile(os.path.join(self.repo_path, f))]
            
            # Ordena por data de modificação (mais antigo primeiro)
            arquivos.sort(key=lambda x: os.path.getmtime(x))
            
            # Remove os backups mais antigos se exceder o limite
            while len(arquivos) >= max_backups:
                if arquivos:
                    os.remove(arquivos[0])
                    log_operation(f"Backup antigo removido: {arquivos[0]}")
                    arquivos.pop(0)
                    
        except Exception as e:
            log_error(f"Erro ao limitar backups: {e}")
    
    def exportar_banco(self, caminho_banco_origem: str, arquivo_destino: str = None, mostrar_dialogo=True) -> bool:
        """Exporta backup do banco de dados"""
        try:
            if not arquivo_destino:
                data_hora_atual = datetime.now()
                nome_padrao = f"banco_dados_{data_hora_atual.strftime('%H%M%S_%d%m%Y')}.db"
                
                if mostrar_dialogo:
                    arquivo_destino = filedialog.asksaveasfilename(
                        defaultextension=".db",
                        filetypes=[("Banco de Dados SQLite", "*.db")],
                        title="Exportar banco de dados",
                        initialfile=nome_padrao
                    )
                    
                    if not arquivo_destino:
                        return False
                else:
                    # Backup automático para o diretório configurado
                    arquivo_destino = os.path.join(self.repo_path, nome_padrao)
            
            # Copia o arquivo do banco
            shutil.copy2(caminho_banco_origem, arquivo_destino)
            
            log_operation(f"Banco de dados exportado: {arquivo_destino}")
            
            # Limita o número de backups se for um backup automático
            if not mostrar_dialogo:
                self._limitar_backups(10)
            
            # Pergunta se deseja abrir o arquivo (apenas para backups manuais)
            if mostrar_dialogo:
                resposta = messagebox.askyesno(
                    "Exportação Concluída",
                    f"Banco de dados exportado com sucesso:\n{arquivo_destino}\n\nDeseja abrir o arquivo agora?"
                )
                
                if resposta:
                    import os
                    os.startfile(arquivo_destino)
            
            return True
            
        except Exception as e:
            error_msg = f"Erro ao exportar banco: {e}"
            if mostrar_dialogo:
                messagebox.showerror("Erro", error_msg)
            log_error(f"Erro na exportação do banco: {e}")
            return False
    
    def importar_banco(self, caminho_banco_destino: str, arquivo_origem: str = None) -> bool:
        """Importa banco de dados de backup"""
        try:
            if not arquivo_origem:
                arquivo_origem = filedialog.askopenfilename(
                    filetypes=[("Banco de Dados SQLite", "*.db")],
                    title="Importar banco de dados"
                )
                
                if not arquivo_origem:
                    return False
            
            # Confirma a operação
            if not messagebox.askyesno(
                "Confirmar", 
                "Isto irá substituir TODOS os dados atuais. Continuar?"
            ):
                return False
            
            # Copia o arquivo
            shutil.copy2(arquivo_origem, caminho_banco_destino)
            
            log_operation(f"Banco de dados importado de: {arquivo_origem}")
            messagebox.showinfo("Sucesso", "Banco importado com sucesso!")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao importar banco: {e}"
            messagebox.showerror("Erro", error_msg)
            log_error(f"Erro na importação do banco: {e}")
            return False
    
    def criar_backup_completo(self, caminho_banco: str, incluir_git: bool = True) -> Dict[str, bool]:
        """Cria backup completo (banco + git se habilitado)"""
        resultados = {
            'banco': False,
            'git': False
        }
        
        try:
            # Backup do banco
            resultados['banco'] = self.exportar_banco(caminho_banco)
            
            # Backup Git se habilitado
            if incluir_git and self.auto_backup_enabled:
                resultados['git'] = self.backup_git()
            
            return resultados
            
        except Exception as e:
            log_error(f"Erro no backup completo: {e}")
            return resultados
    
    def configurar_backup_automatico(self, habilitado: bool, intervalo: int = None):
        """Configura backup automático"""
        self.auto_backup_enabled = habilitado
        
        if intervalo:
            self.backup_interval = intervalo
        
        log_operation(f"Backup automático {'habilitado' if habilitado else 'desabilitado'}")
    
    def get_status_repositorio(self) -> Dict[str, Any]:
        """Retorna status do repositório Git"""
        try:
            if not self.repo_path or not os.path.isdir(self.repo_path):
                return {'erro': 'Diretório não encontrado'}
            
            diretorio_atual = os.getcwd()
            
            try:
                os.chdir(self.repo_path)
                
                if not os.path.isdir(os.path.join(self.repo_path, ".git")):
                    return {'erro': 'Não é um repositório Git'}
                
                # Status
                result_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True, text=True, check=False
                )
                
                # Branch atual
                result_branch = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True, text=True, check=False
                )
                
                # Último commit
                result_commit = subprocess.run(
                    ["git", "log", "-1", "--format=%H %s %ad", "--date=short"],
                    capture_output=True, text=True, check=False
                )
                
                return {
                    'mudancas_pendentes': bool(result_status.stdout.strip()),
                    'branch_atual': result_branch.stdout.strip(),
                    'ultimo_commit': result_commit.stdout.strip(),
                    'repo_path': self.repo_path
                }
                
            finally:
                os.chdir(diretorio_atual)
                
        except Exception as e:
            return {'erro': str(e)}


# Instância global do serviço
_backup_service = BackupService()

# Funções de conveniência
def backup_git() -> bool:
    """Realiza backup Git"""
    return _backup_service.backup_git()

def backup_git_async() -> None:
    """Realiza backup Git assíncrono"""
    _backup_service.backup_git_async()

def verificar_mudancas_e_backup() -> bool:
    """Verifica mudanças e faz backup se necessário"""
    return _backup_service.verificar_mudancas_e_backup()

def exportar_banco(caminho_banco: str) -> bool:
    """Exporta banco de dados"""
    return _backup_service.exportar_banco(caminho_banco)

def importar_banco(caminho_banco: str) -> bool:
    """Importa banco de dados"""
    return _backup_service.importar_banco(caminho_banco)

def get_backup_service() -> BackupService:
    """Retorna a instância do serviço de backup"""
    return _backup_service

def get_status_repositorio() -> Dict[str, Any]:
    """Retorna status do repositório Git"""
    return _backup_service.get_status_repositorio()