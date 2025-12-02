import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
import logging
from utils.intelligent_cache import get_intelligent_cache, cached_method
from utils.structured_logger import get_logger, get_performance_logger, logged_method

class LembreteRepository:
    """Repository para operações com lembretes/promessas."""
    
    def __init__(self, connection):
        self.conn = connection
        self.cursor = connection.cursor()
        self.logger = get_logger("lembrete_repository")
        self.perf_logger = get_performance_logger("lembrete_repository")
        self._intelligent_cache = get_intelligent_cache()
        
    @cached_method(cache_type="search", ttl=300.0, invalidate_on=["lembretes"])
    def get_all_lembretes(self) -> List[Tuple]:
        """Carrega todos os lembretes do banco de dados.
        
        Returns:
            Lista de tuplas (rowid, data_prometida, descricao) ordenadas por data.
        """
        try:
            query = """
                SELECT rowid, data_prometida, descricao 
                FROM promessas 
                ORDER BY date(substr(data_prometida, 7, 4) || '-' || 
                         substr(data_prometida, 4, 2) || '-' || 
                         substr(data_prometida, 1, 2)) DESC
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            # Cache da consulta SQL
            self._intelligent_cache.set_query_result(
                query, (), result, ["promessas"]
            )
            
            return result
            
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao carregar lembretes: {e}")
            return []
            
    @logged_method("create_lembrete", log_args=True, log_performance=True)
    def create_lembrete(self, data_prometida: str, descricao: str) -> bool:
        """Cria um novo lembrete.
        
        Args:
            data_prometida: Data da promessa no formato dd/mm/aaaa.
            descricao: Descrição do lembrete.
            
        Returns:
            True se criado com sucesso, False caso contrário.
        """
        try:
            import time
            from datetime import datetime
            import os
            
            query = "INSERT INTO promessas (data_prometida, descricao) VALUES (?, ?)"
            params = (data_prometida, descricao)
            
            start_time = time.time()
            self.cursor.execute(query, params)
            duration = time.time() - start_time
            
            self.perf_logger.log_database_query(query, params, duration, self.cursor.rowcount)
            
            self.conn.commit()
            
            # Invalidar cache relacionado
            self._intelligent_cache.invalidate_tags(["lembretes"])
            
            # Backup automático após criação de lembrete
            try:
                from services.backup_service import BackupService
                backup_service = BackupService()
                backup_name = f"backup_lembrete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = os.path.join(backup_service.repo_path, backup_name)
                backup_service.exportar_banco("meus_trabalhos.db", backup_path, mostrar_dialogo=False)
                backup_service._limitar_backups(10)
            except Exception as e:
                self.logger.error(f"Erro ao realizar backup automático após criar lembrete: {e}")
            
            self.logger.info(
                f"Lembrete criado com sucesso",
                extra_data={
                    'data_prometida': data_prometida,
                    'descricao': descricao[:50] + '...' if len(descricao) > 50 else descricao
                }
            )
            return True
            
        except sqlite3.Error as e:
            self.logger.error(
                f"Erro ao criar lembrete: {str(e)}",
                extra_data={
                    'data_prometida': data_prometida,
                    'descricao': descricao[:50] + '...' if len(descricao) > 50 else descricao
                }
            )
            self.conn.rollback()
            return False
            
    def update_lembrete(self, rowid: int, data_prometida: str, descricao: str) -> bool:
        """Atualiza um lembrete existente.
        
        Args:
            rowid: ID do lembrete.
            data_prometida: Nova data da promessa.
            descricao: Nova descrição.
            
        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        try:
            from datetime import datetime
            import os
            
            query = "UPDATE promessas SET data_prometida = ?, descricao = ? WHERE rowid = ?"
            self.cursor.execute(query, (data_prometida, descricao, rowid))
            
            if self.cursor.rowcount == 0:
                return False
                
            self.conn.commit()
            
            # Invalidar cache relacionado
            self._intelligent_cache.invalidate_tags(["lembretes"])
            
            # Backup automático após atualização de lembrete
            try:
                from services.backup_service import BackupService
                backup_service = BackupService()
                backup_name = f"backup_lembrete_atualizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = os.path.join(backup_service.repo_path, backup_name)
                backup_service.exportar_banco("meus_trabalhos.db", backup_path, mostrar_dialogo=False)
                backup_service._limitar_backups(10)
            except Exception as e:
                self.logger.error(f"Erro ao realizar backup automático após atualizar lembrete: {e}")
            
            self.logger.info(f"Lembrete {rowid} atualizado com sucesso")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao atualizar lembrete: {e}")
            self.conn.rollback()
            return False
            
    def delete_lembrete(self, rowid: int) -> bool:
        """Exclui um lembrete.
        
        Args:
            rowid: ID do lembrete a ser excluído.
            
        Returns:
            True se excluído com sucesso, False caso contrário.
        """
        try:
            from datetime import datetime
            import os
            
            query = "DELETE FROM promessas WHERE rowid = ?"
            self.cursor.execute(query, (rowid,))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                # Invalidar cache relacionado
                self._intelligent_cache.invalidate_tags(["lembretes"])
                
                # Backup automático após exclusão de lembrete
                try:
                    from services.backup_service import BackupService
                    backup_service = BackupService()
                    backup_name = f"backup_lembrete_exclusao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    backup_path = os.path.join(backup_service.repo_path, backup_name)
                    backup_service.exportar_banco("meus_trabalhos.db", backup_path, mostrar_dialogo=False)
                    backup_service._limitar_backups(10)
                except Exception as e:
                    self.logger.error(f"Erro ao realizar backup automático após excluir lembrete: {e}")
                
                self.logger.info(f"Lembrete {rowid} excluído com sucesso")
                return True
            else:
                self.logger.warning(f"Lembrete {rowid} não encontrado para exclusão")
                return False
                
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao excluir lembrete: {e}")
            self.conn.rollback()
            return False
            
    def get_lembrete_by_id(self, rowid: int) -> Optional[Tuple]:
        """Busca um lembrete pelo ID.
        
        Args:
            rowid: ID do lembrete.
            
        Returns:
            Tupla (rowid, data_prometida, descricao) ou None se não encontrado.
        """
        try:
            query = "SELECT rowid, data_prometida, descricao FROM promessas WHERE rowid = ?"
            self.cursor.execute(query, (rowid,))
            return self.cursor.fetchone()
            
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao buscar lembrete: {e}")
            return None
            
    def count_lembretes(self) -> int:
        """Conta o total de lembretes.
        
        Returns:
            Número total de lembretes.
        """
        try:
            query = "SELECT COUNT(*) FROM promessas"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result[0] if result else 0
            
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao contar lembretes: {e}")
            return 0
            
    @cached_method(cache_type="search", ttl=180.0, invalidate_on=["lembretes"])
    def search_lembretes(self, termo_busca: str) -> List[Tuple]:
        """Busca lembretes por termo.
        
        Args:
            termo_busca: Termo para buscar na descrição ou data.
            
        Returns:
            Lista de tuplas (rowid, data_prometida, descricao) encontradas.
        """
        try:
            query = """
                SELECT rowid, data_prometida, descricao 
                FROM promessas 
                WHERE data_prometida LIKE ? OR descricao LIKE ?
                ORDER BY date(substr(data_prometida, 7, 4) || '-' || 
                         substr(data_prometida, 4, 2) || '-' || 
                         substr(data_prometida, 1, 2)) DESC
            """
            termo_like = f"%{termo_busca}%"
            self.cursor.execute(query, (termo_like, termo_like))
            result = self.cursor.fetchall()
            
            # Cache da consulta SQL
            self._intelligent_cache.set_query_result(
                query, (termo_like, termo_like), result, ["promessas"]
            )
            
            return result
            
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao buscar lembretes: {e}")
            return []