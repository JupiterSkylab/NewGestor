"""Repository para operações CRUD de processos."""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from database.connection import DatabaseManager
from models.processo import Processo
from utils.intelligent_cache import get_intelligent_cache, cached_method
from utils.structured_logger import get_logger, get_performance_logger, logged_method


class ProcessoRepository:
    """Repository para gerenciar operações de processos no banco de dados."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Inicializa o repository.
        
        Args:
            db_manager: Instância do gerenciador de banco de dados.
        """
        self.db_manager = db_manager
        self.logger = get_logger("processo_repository")
        self.perf_logger = get_performance_logger("processo_repository")
        self._intelligent_cache = get_intelligent_cache()
    
    @logged_method("create", log_args=True, log_performance=True)
    def create(self, processo: Processo) -> bool:
        """Cria um novo processo no banco de dados.
        
        Args:
            processo: Instância do processo a ser criado.
            
        Returns:
            True se criado com sucesso, False caso contrário.
        """
        try:
            import time
            
            # Verifica se o processo já existe
            if self.exists_by_numero(processo.numero_processo):
                self.logger.warning(
                    f"Tentativa de criar processo já existente: {processo.numero_processo}",
                    extra_data={'processo_id': processo.numero_processo}
                )
                return False
                
            query = """
                INSERT INTO trabalhos_realizados (
                    numero_processo, secretaria, numero_licitacao, situacao,
                    modalidade, data_inicio, data_entrega, entregue_por,
                    devolvido_a, contratado, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                processo.numero_processo,
                processo.secretaria,
                processo.numero_licitacao,
                processo.situacao,
                processo.modalidade,
                processo.data_inicio,
                processo.data_entrega,
                processo.entregue_por,
                processo.devolvido_a,
                processo.contratado,
                processo.descricao
            )
            
            start_time = time.time()
            cursor = self.db_manager.execute_query(query, params)
            duration = time.time() - start_time
            
            self.perf_logger.log_database_query(query, params, duration, cursor.rowcount)
            
            self.db_manager.commit()
            
            self.logger.info(
                f"Processo criado com sucesso: {processo.numero_processo}",
                extra_data={'processo_id': processo.numero_processo}
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Erro ao criar processo: {str(e)}",
                extra_data={'processo': processo.numero_processo}
            )
            self.db_manager.rollback()
            return False
    
    def exists_by_numero(self, numero_processo: str) -> bool:
        """Verifica se um processo já existe pelo número.
        
        Args:
            numero_processo: Número do processo a ser verificado.
            
        Returns:
            True se existe, False caso contrário.
        """
        try:
            query = "SELECT 1 FROM trabalhos_realizados WHERE numero_processo = ?"
            result = self.db_manager.fetch_one(query, (numero_processo,))
            return result is not None
        except Exception as e:
            self.logger.error(f"Erro ao verificar existência do processo: {e}")
            return False
    
    def get_by_numero(self, numero_processo: str) -> Optional[Processo]:
        """Busca um processo pelo número.
        
        Args:
            numero_processo: Número do processo a ser buscado.
            
        Returns:
            Instância do processo ou None se não encontrado.
        """
        try:
            query = """
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_realizados
                WHERE numero_processo = ?
            """
            
            result = self.db_manager.fetch_one(query, (numero_processo,))
            
            if result:
                return Processo.from_tuple(result)
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar processo {numero_processo}: {e}")
            return None
    
    def get_all(self) -> List[Processo]:
        """Retorna todos os processos.
        
        Returns:
            Lista de processos.
        """
        try:
            query = """
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_realizados
                ORDER BY data_registro DESC
            """
            
            results = self.db_manager.fetch_all(query)
            return [Processo.from_tuple(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar todos os processos: {e}")
            return []
    
    def update(self, processo: Processo, numero_processo_original: str = None) -> bool:
        """Atualiza um processo existente.
        
        Args:
            processo: Objeto Processo com os dados atualizados.
            numero_processo_original: Número original do processo (para casos de alteração do número)
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário.
        """
        try:
            numero_ref = numero_processo_original or processo.numero_processo
            query = """
                UPDATE trabalhos_realizados SET
                    numero_processo = ?, secretaria = ?, numero_licitacao = ?, situacao = ?,
                    modalidade = ?, data_inicio = ?, data_entrega = ?,
                    entregue_por = ?, devolvido_a = ?, contratado = ?, descricao = ?
                WHERE numero_processo = ?
            """
            params = (
                processo.numero_processo, processo.secretaria, processo.numero_licitacao, processo.situacao,
                processo.modalidade, processo.data_inicio, processo.data_entrega,
                processo.entregue_por, processo.devolvido_a, processo.contratado,
                processo.descricao, numero_ref
            )
            
            cursor = self.db_manager.execute_query(query, params)
            self.db_manager.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"Processo {numero_ref} atualizado com sucesso")
                return True
            else:
                self.logger.warning(f"Processo {numero_ref} não encontrado para atualização")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar processo: {e}")
            self.db_manager.rollback()
            return False
            
    def delete_and_backup(self, numero_processo: str) -> bool:
        """Exclui um processo e salva no backup.
        
        Args:
            numero_processo: Número do processo a ser excluído.
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário.
        """
        try:
            # Busca o processo antes de excluir
            processo = self.get_by_numero(numero_processo)
            if not processo:
                return False
                
            # Salva no backup
            data_exclusao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            backup_query = """
                INSERT INTO trabalhos_excluidos (
                    data_exclusao, data_registro, numero_processo, secretaria, numero_licitacao,
                    situacao, modalidade, data_inicio, data_entrega, entregue_por, devolvido_a, contratado, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            backup_params = (
                data_exclusao, processo.data_registro, processo.numero_processo, processo.secretaria,
                processo.numero_licitacao, processo.situacao, processo.modalidade,
                processo.data_inicio, processo.data_entrega, processo.entregue_por,
                processo.devolvido_a, processo.contratado, processo.descricao
            )
            
            self.db_manager.execute_query(backup_query, backup_params)
            
            # Exclui do banco principal
            delete_query = "DELETE FROM trabalhos_realizados WHERE numero_processo = ?"
            cursor = self.db_manager.execute_query(delete_query, (numero_processo,))
            self.db_manager.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"Processo {numero_processo} excluído com sucesso")
                return True
            else:
                self.logger.warning(f"Processo {numero_processo} não encontrado para exclusão")
                return False
            
        except Exception as e:
             self.logger.error(f"Erro ao excluir processo: {e}")
             self.db_manager.rollback()
             return False
             
    @cached_method(cache_type="search", ttl=180.0, invalidate_on=["processos"])
    def search_processos(self, termo_busca: str = None, filtro_secretaria: str = None, 
                        filtro_situacao: str = None, filtro_modalidade: str = None) -> List[Processo]:
        """Busca processos com filtros.
        
        Args:
            termo_busca: Termo de busca livre ou intervalo de datas.
            filtro_secretaria: Filtro por secretaria.
            filtro_situacao: Filtro por situação.
            filtro_modalidade: Filtro por modalidade.
            
        Returns:
            Lista de processos encontrados.
        """
        try:
            query = '''
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_realizados WHERE 1=1
            '''
            params = []
            
            # Aplica filtros
            if filtro_secretaria:
                query += ' AND secretaria LIKE ?'
                params.append(f'%{filtro_secretaria}%')
                
            if filtro_situacao:
                query += ' AND situacao = ?'
                params.append(filtro_situacao)
                
            if filtro_modalidade:
                query += ' AND modalidade LIKE ?'
                params.append(f'%{filtro_modalidade}%')
                
            if termo_busca:
                # Verifica se é busca por intervalo de datas (formato ddmmaDDMM)
                if 'a' in termo_busca and len(termo_busca.replace('a', '')) == 8:
                    try:
                        partes = termo_busca.split('a')
                        if len(partes) == 2 and len(partes[0]) == 4 and len(partes[1]) == 4:
                            data_inicio = f"{partes[0][:2]}/{partes[0][2:]}"
                            data_fim = f"{partes[1][:2]}/{partes[1][2:]}"
                            query += ''' AND (
                                (data_inicio LIKE ? OR data_inicio LIKE ?) OR
                                (data_entrega LIKE ? OR data_entrega LIKE ?)
                            )'''
                            params.extend([f'%{data_inicio}%', f'%{data_fim}%', f'%{data_inicio}%', f'%{data_fim}%'])
                    except:
                        # Se falhar, trata como busca normal
                        query += ''' AND (
                            numero_processo LIKE ? OR secretaria LIKE ? OR
                            numero_licitacao LIKE ? OR situacao LIKE ? OR
                            modalidade LIKE ? OR entregue_por LIKE ? OR
                            devolvido_a LIKE ? OR contratado LIKE ? OR descricao LIKE ?
                        )'''
                        termo_like = f'%{termo_busca}%'
                        params.extend([termo_like] * 9)
                else:
                    # Busca normal em todos os campos
                    query += ''' AND (
                        numero_processo LIKE ? OR secretaria LIKE ? OR
                        numero_licitacao LIKE ? OR situacao LIKE ? OR
                        modalidade LIKE ? OR entregue_por LIKE ? OR
                        devolvido_a LIKE ? OR contratado LIKE ? OR descricao LIKE ?
                    )'''
                    termo_like = f'%{termo_busca}%'
                    params.extend([termo_like] * 9)
                    
            query += ' ORDER BY data_registro DESC'
            
            results = self.db_manager.fetch_all(query, params)
            result = [self._row_to_processo(row) for row in results]
            
            # Cache da consulta SQL também
            self._intelligent_cache.set_query_result(
                query, tuple(params), result, ["trabalhos_realizados"]
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar processos: {e}")
            return []
            
    @cached_method(cache_type="autocomplete", ttl=300.0)
    def get_nomes_autocomplete(self) -> List[str]:
        """Carrega nomes únicos para autocompletar.
        
        Returns:
            Lista de nomes únicos em maiúsculas.
        """
        try:
            query = '''
                SELECT DISTINCT nome FROM (
                    SELECT entregue_por AS nome FROM trabalhos_realizados 
                    WHERE entregue_por IS NOT NULL AND entregue_por != ''
                    UNION
                    SELECT devolvido_a AS nome FROM trabalhos_realizados 
                    WHERE devolvido_a IS NOT NULL AND devolvido_a != ''
                ) ORDER BY UPPER(nome)
            '''
            results = self.db_manager.fetch_all(query)
            result = [row[0].upper() for row in results]
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar nomes para autocomplete: {e}")
            return []
            
    def get_trabalhos_excluidos(self) -> List[Tuple]:
        """Busca trabalhos excluídos para restauração.
        
        Returns:
            Lista de tuplas com dados dos trabalhos excluídos.
        """
        try:
            query = '''
                SELECT id, numero_processo, secretaria, data_exclusao
                FROM trabalhos_excluidos
                ORDER BY data_exclusao DESC
            '''
            return self.db_manager.fetch_all(query)
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar trabalhos excluídos: {e}")
            return []
            
    def restore_from_backup(self, id_registro: int) -> bool:
        """Restaura um registro excluído pelo ID.
        
        Args:
            id_registro: ID do registro no backup.
            
        Returns:
            True se restaurado com sucesso, False caso contrário.
        """
        try:
            # Busca o registro no backup
            backup_query = '''
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_excluidos
                WHERE id = ?
            '''
            registro = self.db_manager.fetch_one(backup_query, (id_registro,))
            
            if not registro:
                return False
                
            # Restaura o registro
            restore_query = '''
                INSERT INTO trabalhos_realizados (
                    data_registro, numero_processo, secretaria, numero_licitacao,
                    situacao, modalidade, data_inicio, data_entrega,
                    entregue_por, devolvido_a, contratado, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            self.db_manager.execute_query(restore_query, registro)
            
            # Remove do backup
            delete_backup_query = 'DELETE FROM trabalhos_excluidos WHERE id = ?'
            self.db_manager.execute_query(delete_backup_query, (id_registro,))
            
            self.db_manager.commit()
            self.logger.info(f"Registro {registro[1]} restaurado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar registro: {e}")
            self.db_manager.rollback()
            return False
    
    def delete(self, numero_processo: str) -> bool:
        """Move um processo para a tabela de excluídos.
        
        Args:
            numero_processo: Número do processo a ser excluído.
            
        Returns:
            True se excluído com sucesso, False caso contrário.
        """
        try:
            # Busca o processo antes de excluir
            processo = self.get_by_numero(numero_processo)
            if not processo:
                return False
            
            with self.db_manager.transaction():
                # Move para tabela de excluídos
                insert_query = """
                    INSERT INTO trabalhos_excluidos (
                        data_exclusao, data_registro, numero_processo, secretaria,
                        numero_licitacao, situacao, modalidade, data_inicio,
                        data_entrega, entregue_por, devolvido_a, descricao, contratado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                insert_params = (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    processo.data_registro,
                    processo.numero_processo,
                    processo.secretaria,
                    processo.numero_licitacao,
                    processo.situacao,
                    processo.modalidade,
                    processo.data_inicio,
                    processo.data_entrega,
                    processo.entregue_por,
                    processo.devolvido_a,
                    processo.descricao,
                    processo.contratado
                )
                
                self.db_manager.execute_query(insert_query, insert_params)
                
                # Remove da tabela principal
                delete_query = "DELETE FROM trabalhos_realizados WHERE numero_processo = ?"
                self.db_manager.execute_query(delete_query, (numero_processo,))
            
            self.logger.info(f"Processo {numero_processo} excluído com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao excluir processo {numero_processo}: {e}")
            return False
    
    def search(self, filters: dict) -> List[Processo]:
        """Busca processos com filtros.
        
        Args:
            filters: Dicionário com filtros de busca.
            
        Returns:
            Lista de processos que atendem aos filtros.
        """
        try:
            query = """
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_realizados WHERE 1=1
            """
            params = []
            
            # Aplica filtros
            if filters.get('secretaria'):
                query += " AND secretaria = ?"
                params.append(filters['secretaria'])
            
            if filters.get('situacao'):
                query += " AND situacao = ?"
                params.append(filters['situacao'])
            
            if filters.get('modalidade'):
                query += " AND modalidade = ?"
                params.append(filters['modalidade'])
            
            if filters.get('termo_busca'):
                query += " AND (numero_processo LIKE ? OR descricao LIKE ?)"
                termo = f"%{filters['termo_busca']}%"
                params.extend([termo, termo])
            
            query += " ORDER BY data_registro DESC"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            return [Processo.from_tuple(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar processos com filtros: {e}")
            return []
    
    def count_by_situacao(self) -> dict:
        """Conta processos por situação.
        
        Returns:
            Dicionário com contagem por situação.
        """
        try:
            query = "SELECT situacao, COUNT(*) FROM trabalhos_realizados GROUP BY situacao"
            results = self.db_manager.fetch_all(query)
            
            counts = {'Em Andamento': 0, 'Concluído': 0}
            for situacao, count in results:
                counts[situacao] = count
            
            return counts
            
        except Exception as e:
            self.logger.error(f"Erro ao contar processos por situação: {e}")
            return {'Em Andamento': 0, 'Concluído': 0}
    
    def get_nomes_autocomplete(self) -> List[str]:
        """Retorna nomes únicos para autocomplete.
        
        Returns:
            Lista de nomes únicos.
        """
        try:
            query = """
                SELECT DISTINCT nome FROM (
                    SELECT entregue_por AS nome FROM trabalhos_realizados 
                    WHERE entregue_por IS NOT NULL AND entregue_por != ''
                    UNION
                    SELECT devolvido_a AS nome FROM trabalhos_realizados 
                    WHERE devolvido_a IS NOT NULL AND devolvido_a != ''
                ) ORDER BY UPPER(nome)
            """
            
            results = self.db_manager.fetch_all(query)
            return [row[0].upper() for row in results]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar nomes para autocomplete: {e}")
            return []