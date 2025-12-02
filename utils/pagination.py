"""Sistema de paginação para consultas SQL otimizadas."""

import sqlite3
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class PaginationResult:
    """Resultado de uma consulta paginada."""
    data: List[Dict[str, Any]]
    total_records: int
    current_page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    start_record: int
    end_record: int
    
    @classmethod
    def create(cls, data: List[Dict[str, Any]], total_records: int, 
               current_page: int, page_size: int) -> 'PaginationResult':
        """Cria um resultado de paginação."""
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1
        start_record = (current_page - 1) * page_size + 1
        end_record = min(current_page * page_size, total_records)
        
        return cls(
            data=data,
            total_records=total_records,
            current_page=current_page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_previous=current_page > 1,
            start_record=start_record,
            end_record=end_record
        )

class PaginatedQuery:
    """Classe para executar consultas paginadas otimizadas."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def paginate_processos(self, page: int = 1, page_size: int = 50, 
                          filters: Optional[Dict[str, Any]] = None,
                          order_by: str = "data_registro",
                          order_direction: str = "DESC") -> PaginationResult:
        """Pagina a consulta de processos com filtros otimizados.
        
        Args:
            page: Número da página (começando em 1)
            page_size: Número de registros por página
            filters: Filtros a serem aplicados
            order_by: Campo para ordenação
            order_direction: Direção da ordenação (ASC/DESC)
            
        Returns:
            Resultado paginado com os processos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Construir a consulta base
            base_query = "FROM trabalhos_realizados"
            where_conditions = []
            params = []
            
            # Aplicar filtros
            if filters:
                if filters.get('secretaria'):
                    where_conditions.append("secretaria = ?")
                    params.append(filters['secretaria'])
                    
                if filters.get('situacao'):
                    where_conditions.append("situacao = ?")
                    params.append(filters['situacao'])
                    
                if filters.get('modalidade'):
                    where_conditions.append("modalidade = ?")
                    params.append(filters['modalidade'])
                    
                if filters.get('numero_processo'):
                    where_conditions.append("numero_processo LIKE ?")
                    params.append(f"%{filters['numero_processo']}%")
                    
                if filters.get('entregue_por'):
                    where_conditions.append("entregue_por LIKE ?")
                    params.append(f"%{filters['entregue_por']}%")
                    
                if filters.get('devolvido_a'):
                    where_conditions.append("devolvido_a LIKE ?")
                    params.append(f"%{filters['devolvido_a']}%")
                    
                if filters.get('data_inicio'):
                    where_conditions.append("data_inicio >= ?")
                    params.append(filters['data_inicio'])
                    
                if filters.get('data_fim'):
                    where_conditions.append("data_inicio <= ?")
                    params.append(filters['data_fim'])
                    
                if filters.get('busca_geral'):
                    # Busca em múltiplos campos
                    search_condition = """(
                        numero_processo LIKE ? OR
                        entregue_por LIKE ? OR
                        devolvido_a LIKE ? OR
                        observacoes LIKE ?
                    )"""
                    where_conditions.append(search_condition)
                    search_term = f"%{filters['busca_geral']}%"
                    params.extend([search_term, search_term, search_term, search_term])
            
            # Construir cláusula WHERE
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Contar total de registros
            count_query = f"SELECT COUNT(*) {base_query} {where_clause}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # Validar parâmetros de paginação
            page = max(1, page)
            page_size = min(max(1, page_size), 1000)  # Máximo 1000 registros por página
            
            # Calcular offset
            offset = (page - 1) * page_size
            
            # Validar campo de ordenação
            valid_order_fields = [
                'numero_processo', 'secretaria', 'situacao', 'modalidade',
                'data_registro', 'data_inicio', 'data_entrega', 'entregue_por',
                'devolvido_a', 'observacoes'
            ]
            
            if order_by not in valid_order_fields:
                order_by = 'data_registro'
                
            if order_direction.upper() not in ['ASC', 'DESC']:
                order_direction = 'DESC'
            
            # Consulta principal com paginação
            main_query = f"""
                SELECT * {base_query} {where_clause}
                ORDER BY {order_by} {order_direction}
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(main_query, params + [page_size, offset])
            rows = cursor.fetchall()
            
            # Converter para dicionários
            data = [dict(row) for row in rows]
            
            conn.close()
            
            return PaginationResult.create(data, total_records, page, page_size)
            
        except Exception as e:
            self.logger.error(f"Erro na paginação de processos: {e}")
            return PaginationResult.create([], 0, page, page_size)
    
    def paginate_trabalhos_excluidos(self, page: int = 1, page_size: int = 50) -> PaginationResult:
        """Pagina a consulta de trabalhos excluídos.
        
        Args:
            page: Número da página
            page_size: Número de registros por página
            
        Returns:
            Resultado paginado com os trabalhos excluídos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Contar total de registros
            cursor.execute("SELECT COUNT(*) FROM trabalhos_excluidos")
            total_records = cursor.fetchone()[0]
            
            # Validar parâmetros
            page = max(1, page)
            page_size = min(max(1, page_size), 1000)
            offset = (page - 1) * page_size
            
            # Consulta paginada
            query = """
                SELECT * FROM trabalhos_excluidos
                ORDER BY data_exclusao DESC
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, (page_size, offset))
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            conn.close()
            
            return PaginationResult.create(data, total_records, page, page_size)
            
        except Exception as e:
            self.logger.error(f"Erro na paginação de trabalhos excluídos: {e}")
            return PaginationResult.create([], 0, page, page_size)
    
    def paginate_lembretes(self, page: int = 1, page_size: int = 50,
                          apenas_pendentes: bool = False) -> PaginationResult:
        """Pagina a consulta de lembretes/promessas.
        
        Args:
            page: Número da página
            page_size: Número de registros por página
            apenas_pendentes: Se deve mostrar apenas lembretes pendentes
            
        Returns:
            Resultado paginado com os lembretes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='promessas'
            """)
            
            if not cursor.fetchone():
                conn.close()
                return PaginationResult.create([], 0, page, page_size)
            
            # Construir consulta
            where_clause = ""
            params = []
            
            if apenas_pendentes:
                where_clause = "WHERE data_prometida >= date('now')"
            
            # Contar total
            count_query = f"SELECT COUNT(*) FROM promessas {where_clause}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # Validar parâmetros
            page = max(1, page)
            page_size = min(max(1, page_size), 1000)
            offset = (page - 1) * page_size
            
            # Consulta paginada
            main_query = f"""
                SELECT * FROM promessas {where_clause}
                ORDER BY data_prometida ASC
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(main_query, params + [page_size, offset])
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            conn.close()
            
            return PaginationResult.create(data, total_records, page, page_size)
            
        except Exception as e:
            self.logger.error(f"Erro na paginação de lembretes: {e}")
            return PaginationResult.create([], 0, page, page_size)
    
    def search_processos_optimized(self, search_term: str, page: int = 1, 
                                  page_size: int = 50) -> PaginationResult:
        """Busca otimizada de processos com paginação.
        
        Args:
            search_term: Termo de busca
            page: Número da página
            page_size: Número de registros por página
            
        Returns:
            Resultado paginado da busca
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Preparar termo de busca
            search_pattern = f"%{search_term}%"
            
            # Consulta otimizada com índices
            search_conditions = """
                WHERE (
                    numero_processo LIKE ? OR
                    entregue_por LIKE ? OR
                    devolvido_a LIKE ? OR
                    observacoes LIKE ? OR
                    secretaria LIKE ? OR
                    situacao LIKE ? OR
                    modalidade LIKE ?
                )
            """
            
            params = [search_pattern] * 7
            
            # Contar resultados
            count_query = f"SELECT COUNT(*) FROM trabalhos_realizados {search_conditions}"
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # Validar parâmetros
            page = max(1, page)
            page_size = min(max(1, page_size), 1000)
            offset = (page - 1) * page_size
            
            # Consulta principal com ranking por relevância
            main_query = f"""
                SELECT *,
                    CASE 
                        WHEN numero_processo LIKE ? THEN 10
                        WHEN entregue_por LIKE ? THEN 8
                        WHEN devolvido_a LIKE ? THEN 8
                        WHEN secretaria LIKE ? THEN 6
                        WHEN situacao LIKE ? THEN 4
                        WHEN modalidade LIKE ? THEN 4
                        ELSE 2
                    END as relevance_score
                FROM trabalhos_realizados {search_conditions}
                ORDER BY relevance_score DESC, data_registro DESC
                LIMIT ? OFFSET ?
            """
            
            # Parâmetros para ranking + parâmetros de busca + paginação
            all_params = params + params + [page_size, offset]
            
            cursor.execute(main_query, all_params)
            rows = cursor.fetchall()
            
            # Converter para dicionários (removendo o score de relevância)
            data = []
            for row in rows:
                row_dict = dict(row)
                row_dict.pop('relevance_score', None)
                data.append(row_dict)
            
            conn.close()
            
            return PaginationResult.create(data, total_records, page, page_size)
            
        except Exception as e:
            self.logger.error(f"Erro na busca otimizada: {e}")
            return PaginationResult.create([], 0, page, page_size)
    
    def get_autocomplete_suggestions(self, field: str, partial_value: str, 
                                   limit: int = 10) -> List[str]:
        """Obtém sugestões de autocompletar otimizadas.
        
        Args:
            field: Campo para buscar sugestões
            partial_value: Valor parcial digitado
            limit: Número máximo de sugestões
            
        Returns:
            Lista de sugestões
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Validar campo
            valid_fields = ['entregue_por', 'devolvido_a', 'secretaria', 'situacao', 'modalidade']
            if field not in valid_fields:
                return []
            
            # Consulta otimizada com índice
            query = f"""
                SELECT DISTINCT {field}
                FROM trabalhos_realizados
                WHERE {field} LIKE ? AND {field} IS NOT NULL AND {field} != ''
                ORDER BY {field}
                LIMIT ?
            """
            
            cursor.execute(query, (f"{partial_value}%", limit))
            results = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao obter sugestões de autocompletar: {e}")
            return []
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas otimizadas para o dashboard.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total de processos
            cursor.execute("SELECT COUNT(*) FROM trabalhos_realizados")
            stats['total_processos'] = cursor.fetchone()[0]
            
            # Processos por situação (usando índice)
            cursor.execute("""
                SELECT situacao, COUNT(*) 
                FROM trabalhos_realizados 
                GROUP BY situacao
                ORDER BY COUNT(*) DESC
            """)
            stats['por_situacao'] = dict(cursor.fetchall())
            
            # Processos por secretaria (usando índice)
            cursor.execute("""
                SELECT secretaria, COUNT(*) 
                FROM trabalhos_realizados 
                GROUP BY secretaria
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            stats['por_secretaria'] = dict(cursor.fetchall())
            
            # Processos recentes (últimos 30 dias)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM trabalhos_realizados 
                WHERE data_registro >= date('now', '-30 days')
            """)
            stats['recentes_30_dias'] = cursor.fetchone()[0]
            
            # Trabalhos excluídos
            cursor.execute("SELECT COUNT(*) FROM trabalhos_excluidos")
            stats['total_excluidos'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do dashboard: {e}")
            return {}