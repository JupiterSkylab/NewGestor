# -*- coding: utf-8 -*-
"""
Gerenciador de banco de dados para o Gestor de Processos
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from logger_config import db_logger, log_error, log_operation
from config import DB_CONFIG
from utils.auto_backup import backup_apos_insercao, backup_apos_alteracao, backup_apos_exclusao

class DatabaseError(Exception):
    """Exceção customizada para erros de banco de dados"""
    pass

class DatabaseManager:
    """Classe centralizada para operações de banco de dados"""
    
    def __init__(self, db_path: str = None):
        # Suporta tanto a chave moderna 'path' quanto a legada 'nome_arquivo'
        default_path = DB_CONFIG.get('path') or DB_CONFIG.get('nome_arquivo')
        # Garante string para o sqlite3
        self.db_path = str(db_path or default_path)
        self.conn = None
        self.cursor = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa o banco de dados e cria tabelas se necessário"""
        try:
            self.connect()
            self._create_tables()
            self._create_indexes()
            log_operation(db_logger, "Database initialized successfully")
        except Exception as e:
            log_error(db_logger, e, "Database initialization failed")
            raise DatabaseError(f"Falha ao inicializar banco de dados: {e}")
    
    def connect(self) -> bool:
        """Estabelece conexão com o banco de dados"""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                timeout=DB_CONFIG['timeout'],
                check_same_thread=DB_CONFIG['check_same_thread']
            )
            self.conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            log_error(db_logger, e, "Database connection failed")
            return False
    
    def _create_tables(self):
        """Cria as tabelas necessárias"""
        # Tabela principal de trabalhos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trabalhos_realizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_registro TEXT DEFAULT (datetime('now', 'localtime')),
                numero_processo TEXT UNIQUE NOT NULL,
                secretaria TEXT NOT NULL,
                numero_licitacao TEXT,
                situacao TEXT DEFAULT 'Em Andamento',
                modalidade TEXT,
                data_inicio TEXT NOT NULL,
                data_entrega TEXT,
                entregue_por TEXT NOT NULL,
                devolvido_a TEXT,
                contratado TEXT,
                descricao TEXT
            )
        ''')
        
        # Tabela de trabalhos excluídos (lixeira)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trabalhos_excluidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_exclusao TEXT DEFAULT (datetime('now', 'localtime')),
                data_registro TEXT,
                numero_processo TEXT,
                secretaria TEXT,
                numero_licitacao TEXT,
                situacao TEXT,
                modalidade TEXT,
                data_inicio TEXT,
                data_entrega TEXT,
                entregue_por TEXT,
                devolvido_a TEXT,
                contratado TEXT,
                descricao TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _create_indexes(self):
        """Cria índices para melhorar performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_numero_processo ON trabalhos_realizados(numero_processo)",
            "CREATE INDEX IF NOT EXISTS idx_data_registro ON trabalhos_realizados(data_registro)",
            "CREATE INDEX IF NOT EXISTS idx_situacao ON trabalhos_realizados(situacao)",
            "CREATE INDEX IF NOT EXISTS idx_secretaria ON trabalhos_realizados(secretaria)",
            "CREATE INDEX IF NOT EXISTS idx_data_inicio ON trabalhos_realizados(data_inicio)",
            "CREATE INDEX IF NOT EXISTS idx_entregue_por ON trabalhos_realizados(entregue_por)",
            "CREATE INDEX IF NOT EXISTS idx_devolvido_a ON trabalhos_realizados(devolvido_a)"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
            except sqlite3.Error as e:
                log_error(db_logger, e, f"Failed to create index: {index_sql}")
        
        self.conn.commit()
    
    def execute_query(self, query: str, params: Tuple = None, 
                     fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """Executa uma query no banco de dados"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if fetch_one:
                return self.cursor.fetchone()
            elif fetch_all:
                return self.cursor.fetchall()
            
            return self.cursor.rowcount
        except Exception as e:
            log_error(db_logger, e, f"Query execution failed: {query}")
            raise DatabaseError(f"Erro ao executar query: {e}")
    
    def insert_process(self, data: Dict[str, Any]) -> int:
        """Insere um novo processo"""
        query = '''
            INSERT INTO trabalhos_realizados (
                numero_processo, secretaria, numero_licitacao, situacao,
                modalidade, data_inicio, data_entrega, entregue_por,
                devolvido_a, contratado, descricao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            data['numero_processo'],
            data['secretaria'],
            data.get('numero_licitacao'),
            data.get('situacao', 'Em Andamento'),
            data.get('modalidade'),
            data['data_inicio'],
            data.get('data_entrega'),
            data['entregue_por'],
            data.get('devolvido_a'),
            data.get('contratado'),
            data.get('descricao')
        )
        
        try:
            self.execute_query(query, params)
            self.commit()
            process_id = self.cursor.lastrowid
            log_operation(db_logger, "Process inserted", True, 
                         f"ID: {process_id}, Number: {data['numero_processo']}")
            
            # Criar backup após inserção
            try:
                backup_apos_insercao("registro")
            except Exception as e:
                log_error(db_logger, e, "Erro ao criar backup após inserção")
                
            return process_id
        except sqlite3.IntegrityError:
            raise DatabaseError(f"Processo {data['numero_processo']} já existe")
        except Exception as e:
            self.rollback()
            raise DatabaseError(f"Erro ao inserir processo: {e}")
    
    def update_process(self, numero_processo: str, data: Dict[str, Any]) -> bool:
        """Atualiza um processo existente"""
        query = '''
            UPDATE trabalhos_realizados SET
                numero_processo = ?, secretaria = ?, numero_licitacao = ?,
                situacao = ?, modalidade = ?, data_inicio = ?, data_entrega = ?,
                entregue_por = ?, devolvido_a = ?, contratado = ?, descricao = ?
            WHERE numero_processo = ?
        '''
        
        params = (
            data['numero_processo'],
            data['secretaria'],
            data.get('numero_licitacao'),
            data.get('situacao', 'Em Andamento'),
            data.get('modalidade'),
            data['data_inicio'],
            data.get('data_entrega'),
            data['entregue_por'],
            data.get('devolvido_a'),
            data.get('contratado'),
            data.get('descricao'),
            numero_processo
        )
        
        try:
            rows_affected = self.execute_query(query, params)
            self.commit()
            success = rows_affected > 0
            log_operation(db_logger, "Process updated", success, 
                         f"Number: {numero_processo}")
            
            # Criar backup após atualização
            try:
                backup_apos_alteracao("registro")
            except Exception as e:
                log_error(db_logger, e, "Erro ao criar backup após atualização")
                
            return success
        except Exception as e:
            self.rollback()
            raise DatabaseError(f"Erro ao atualizar processo: {e}")
    
    def delete_process(self, numero_processo: str) -> bool:
        """Move um processo para a tabela de excluídos"""
        try:
            # Busca o processo
            process = self.get_process_by_number(numero_processo)
            if not process:
                return False
            
            # Move para tabela de excluídos
            insert_query = '''
                INSERT INTO trabalhos_excluidos (
                    data_registro, numero_processo, secretaria, numero_licitacao,
                    situacao, modalidade, data_inicio, data_entrega,
                    entregue_por, devolvido_a, contratado, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            self.execute_query(insert_query, (
                process['data_registro'], process['numero_processo'],
                process['secretaria'], process['numero_licitacao'],
                process['situacao'], process['modalidade'],
                process['data_inicio'], process['data_entrega'],
                process['entregue_por'], process['devolvido_a'],
                process['contratado'], process['descricao']
            ))
            
            # Remove da tabela principal
            delete_query = "DELETE FROM trabalhos_realizados WHERE numero_processo = ?"
            self.execute_query(delete_query, (numero_processo,))
            
            self.commit()
            log_operation(db_logger, "Process deleted", True, f"Number: {numero_processo}")
            
            # Criar backup após exclusão
            try:
                backup_apos_exclusao("registro")
            except Exception as e:
                log_error(db_logger, e, "Erro ao criar backup após exclusão")
                
            return True
            
        except Exception as e:
            self.rollback()
            raise DatabaseError(f"Erro ao excluir processo: {e}")
    
    def get_process_by_number(self, numero_processo: str) -> Optional[Dict[str, Any]]:
        """Busca um processo pelo número"""
        query = "SELECT * FROM trabalhos_realizados WHERE numero_processo = ?"
        result = self.execute_query(query, (numero_processo,), fetch_one=True)
        return dict(result) if result else None
    
    def search_processes(self, filters: Dict[str, Any] = None, 
                       order_by: str = "data_registro DESC") -> List[Dict[str, Any]]:
        """Busca processos com filtros opcionais"""
        query = "SELECT * FROM trabalhos_realizados"
        params = []
        
        if filters:
            conditions = []
            
            if filters.get('termo_busca'):
                termo = f"%{filters['termo_busca']}%"
                conditions.append(
                    "(numero_processo LIKE ? OR numero_licitacao LIKE ? OR "
                    "descricao LIKE ? OR entregue_por LIKE ? OR devolvido_a LIKE ? OR "
                    "UPPER(contratado) LIKE ?)"
                )
                params.extend([termo, termo, termo, termo, termo, termo.upper()])
            
            if filters.get('secretaria'):
                conditions.append("secretaria = ?")
                params.append(filters['secretaria'])
            
            if filters.get('situacao'):
                conditions.append("situacao = ?")
                params.append(filters['situacao'])
            
            if filters.get('modalidade'):
                conditions.append("modalidade = ?")
                params.append(filters['modalidade'])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY {order_by}"
        
        try:
            results = self.execute_query(query, tuple(params), fetch_all=True)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            log_error(db_logger, e, "Search processes failed")
            return []
    
    def get_process_count(self, status: str = None) -> int:
    # """Obtém contagem de processos por status"""
        if status == 'deleted':
            # Conta registros excluídos na tabela trabalhos_excluidos
            query = "SELECT COUNT(*) FROM trabalhos_excluidos"
            result = self.execute_query(query, fetch_one=True)
        elif status:
            query = "SELECT COUNT(*) FROM trabalhos_realizados WHERE situacao = ?"
            result = self.execute_query(query, (status,), fetch_one=True)
        else:
            query = "SELECT COUNT(*) FROM trabalhos_realizados"
            result = self.execute_query(query, fetch_one=True)
        
        return result[0] if result else 0
    
    def get_unique_values(self, column: str) -> List[str]:
        """Obtém valores únicos de uma coluna para autocompletar"""
        query = f"SELECT DISTINCT {column} FROM trabalhos_realizados WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
        try:
            results = self.execute_query(query, fetch_all=True)
            return [row[0] for row in results] if results else []
        except Exception as e:
            log_error(db_logger, e, f"Get unique values failed for column: {column}")
            return []
    
    def cleanup_old_deleted(self, days: int = 30) -> int:
        """Remove registros excluídos com mais de X dias"""
        query = "DELETE FROM trabalhos_excluidos WHERE date(data_exclusao) < date('now', '-{} days')".format(days)
        try:
            rows_affected = self.execute_query(query)
            self.commit()
            log_operation(db_logger, "Old deleted records cleaned", True, f"Removed: {rows_affected}")
            return rows_affected
        except Exception as e:
            log_error(db_logger, e, "Cleanup old deleted records failed")
            return 0
    
    def commit(self):
        """Confirma as alterações no banco"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Desfaz as alterações pendentes"""
        if self.conn:
            self.conn.rollback()
    
    def close(self):
        """Fecha a conexão com o banco"""
        if self.conn:
            self.conn.close()
            log_operation(db_logger, "Database connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()