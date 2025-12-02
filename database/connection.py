"""Gerenciador de conexão com banco de dados."""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, List, Optional, Tuple, Union
from pathlib import Path

from config.settings import DATABASE_CONFIG


class DatabaseManager:
    """Gerenciador de conexão e operações do banco de dados."""
    
    def __init__(self, db_path: Union[str, Path] = None):
        """Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados.
        """
        self.db_path = db_path or DATABASE_CONFIG['path']
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> None:
        """Estabelece conexão com o banco de dados."""
        try:
            self.conn = sqlite3.connect(
                str(self.db_path),
                timeout=DATABASE_CONFIG['timeout'],
                check_same_thread=DATABASE_CONFIG['check_same_thread'],
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.cursor = self.conn.cursor()
            self.logger.info(f"Conexão estabelecida com {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao conectar com banco: {e}")
            raise
    
    def disconnect(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Conexão com banco fechada")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """Executa uma query no banco de dados.
        
        Args:
            query: Query SQL a ser executada.
            params: Parâmetros para a query.
            
        Returns:
            Cursor com o resultado da query.
        """
        if not self.cursor:
            raise RuntimeError("Conexão não estabelecida")
        
        try:
            if params:
                return self.cursor.execute(query, params)
            else:
                return self.cursor.execute(query)
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao executar query: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """Executa uma query múltiplas vezes com diferentes parâmetros.
        
        Args:
            query: Query SQL a ser executada.
            params_list: Lista de tuplas com parâmetros.
            
        Returns:
            Cursor com o resultado da operação.
        """
        if not self.cursor:
            raise RuntimeError("Conexão não estabelecida")
        
        try:
            return self.cursor.executemany(query, params_list)
        except sqlite3.Error as e:
            self.logger.error(f"Erro ao executar query múltipla: {e}")
            raise
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Executa query e retorna um resultado.
        
        Args:
            query: Query SQL a ser executada.
            params: Parâmetros para a query.
            
        Returns:
            Primeira linha do resultado ou None.
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Executa query e retorna todos os resultados.
        
        Args:
            query: Query SQL a ser executada.
            params: Parâmetros para a query.
            
        Returns:
            Lista com todas as linhas do resultado.
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def commit(self) -> None:
        """Confirma as transações pendentes."""
        if self.conn:
            self.conn.commit()
    
    def rollback(self) -> None:
        """Desfaz as transações pendentes."""
        if self.conn:
            self.conn.rollback()
    
    @contextmanager
    def transaction(self):
        """Context manager para transações."""
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            self.logger.error(f"Erro na transação: {e}")
            raise
    
    def create_tables(self) -> None:
        """Cria as tabelas necessárias no banco de dados."""
        tables = [

            """
            CREATE TABLE IF NOT EXISTS trabalhos_realizados (
                data_registro TEXT DEFAULT (datetime('now', 'localtime')),
                numero_processo TEXT NOT NULL UNIQUE,
                secretaria TEXT,
                numero_licitacao TEXT,
                situacao TEXT,
                data_inicio TEXT,
                data_entrega TEXT,
                entregue_por TEXT,
                devolvido_a TEXT,
                modalidade TEXT,
                descricao TEXT,
                contratado TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trabalhos_excluidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_exclusao TEXT,
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
                descricao TEXT,
                contratado TEXT
            )
            """
        ]
        
        for table_sql in tables:
            try:
                self.execute_query(table_sql)
                self.commit()
            except sqlite3.Error as e:
                self.logger.error(f"Erro ao criar tabela: {e}")
                raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()