"""Repository para consultas de estatísticas e relatórios."""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date

from database.connection import DatabaseManager


class EstatisticasRepository:
    """Repository para gerenciar consultas de estatísticas e relatórios."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Inicializa o repository.
        
        Args:
            db_manager: Instância do gerenciador de banco de dados.
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_processos_por_situacao(self) -> Dict[str, int]:
        """Retorna contagem de processos por situação.
        
        Returns:
            Dicionário com situação como chave e contagem como valor.
        """
        try:
            query = "SELECT situacao, COUNT(*) FROM trabalhos_realizados GROUP BY situacao"
            results = self.db_manager.fetch_all(query)
            
            stats = {'Em Andamento': 0, 'Concluído': 0}
            for situacao, count in results:
                stats[situacao] = count
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas por situação: {e}")
            return {'Em Andamento': 0, 'Concluído': 0}
    
    def get_processos_por_secretaria(self) -> Dict[str, int]:
        """Retorna contagem de processos por secretaria.
        
        Returns:
            Dicionário com secretaria como chave e contagem como valor.
        """
        try:
            query = """
                SELECT secretaria, COUNT(*) 
                FROM trabalhos_realizados 
                GROUP BY secretaria 
                ORDER BY COUNT(*) DESC
            """
            results = self.db_manager.fetch_all(query)
            
            return {secretaria: count for secretaria, count in results}
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas por secretaria: {e}")
            return {}
    
    def get_processos_por_modalidade(self) -> Dict[str, int]:
        """Retorna contagem de processos por modalidade.
        
        Returns:
            Dicionário com modalidade como chave e contagem como valor.
        """
        try:
            query = """
                SELECT modalidade, COUNT(*) 
                FROM trabalhos_realizados 
                GROUP BY modalidade 
                ORDER BY COUNT(*) DESC
            """
            results = self.db_manager.fetch_all(query)
            
            return {modalidade: count for modalidade, count in results}
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas por modalidade: {e}")
            return {}
    
    def get_processos_por_mes(self, ano: Optional[int] = None) -> Dict[str, int]:
        """Retorna contagem de processos por mês.
        
        Args:
            ano: Ano específico para filtrar (opcional).
            
        Returns:
            Dicionário com mês como chave e contagem como valor.
        """
        try:
            if ano:
                query = """
                    SELECT strftime('%m', data_registro) as mes, COUNT(*) 
                    FROM trabalhos_realizados 
                    WHERE strftime('%Y', data_registro) = ?
                    GROUP BY mes 
                    ORDER BY mes
                """
                results = self.db_manager.fetch_all(query, (str(ano),))
            else:
                query = """
                    SELECT strftime('%Y-%m', data_registro) as mes, COUNT(*) 
                    FROM trabalhos_realizados 
                    GROUP BY mes 
                    ORDER BY mes DESC
                    LIMIT 12
                """
                results = self.db_manager.fetch_all(query)
            
            return {mes: count for mes, count in results}
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas por mês: {e}")
            return {}
    
    def get_total_processos(self) -> int:
        """Retorna o total de processos.
        
        Returns:
            Número total de processos.
        """
        try:
            query = "SELECT COUNT(*) FROM trabalhos_realizados"
            result = self.db_manager.fetch_one(query)
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Erro ao obter total de processos: {e}")
            return 0
    
    def get_total_excluidos(self) -> int:
        """Retorna o total de processos excluídos.
        
        Returns:
            Número total de processos excluídos.
        """
        try:
            query = "SELECT COUNT(*) FROM trabalhos_excluidos"
            result = self.db_manager.fetch_one(query)
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Erro ao obter total de processos excluídos: {e}")
            return 0
    
    def get_processos_recentes(self, limite: int = 10) -> List[Tuple]:
        """Retorna os processos mais recentes.
        
        Args:
            limite: Número máximo de processos a retornar.
            
        Returns:
            Lista de tuplas com dados dos processos recentes.
        """
        try:
            query = """
                SELECT numero_processo, secretaria, situacao, data_registro
                FROM trabalhos_realizados
                ORDER BY data_registro DESC
                LIMIT ?
            """
            
            return self.db_manager.fetch_all(query, (limite,))
            
        except Exception as e:
            self.logger.error(f"Erro ao obter processos recentes: {e}")
            return []
    
    def get_tempo_medio_conclusao(self) -> Optional[float]:
        """Calcula o tempo médio de conclusão dos processos.
        
        Returns:
            Tempo médio em dias ou None se não houver dados.
        """
        try:
            query = """
                SELECT AVG(julianday(data_entrega) - julianday(data_inicio)) as tempo_medio
                FROM trabalhos_realizados
                WHERE situacao = 'Concluído' 
                AND data_inicio IS NOT NULL 
                AND data_entrega IS NOT NULL
            """
            
            result = self.db_manager.fetch_one(query)
            return result[0] if result and result[0] else None
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tempo médio de conclusão: {e}")
            return None
    
    def get_processos_em_atraso(self) -> List[Tuple]:
        """Retorna processos que podem estar em atraso.
        
        Returns:
            Lista de tuplas com processos em andamento há mais de 30 dias.
        """
        try:
            query = """
                SELECT numero_processo, secretaria, data_inicio,
                       julianday('now') - julianday(data_inicio) as dias_decorridos
                FROM trabalhos_realizados
                WHERE situacao = 'Em Andamento'
                AND data_inicio IS NOT NULL
                AND julianday('now') - julianday(data_inicio) > 30
                ORDER BY dias_decorridos DESC
            """
            
            return self.db_manager.fetch_all(query)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter processos em atraso: {e}")
            return []
    
    def get_ranking_pessoas(self) -> Dict[str, Dict[str, int]]:
        """Retorna ranking de pessoas por entregas e devoluções.
        
        Returns:
            Dicionário com estatísticas por pessoa.
        """
        try:
            # Entregas
            query_entregas = """
                SELECT entregue_por, COUNT(*) 
                FROM trabalhos_realizados 
                WHERE entregue_por IS NOT NULL AND entregue_por != ''
                GROUP BY entregue_por 
                ORDER BY COUNT(*) DESC
            """
            
            # Devoluções
            query_devolucoes = """
                SELECT devolvido_a, COUNT(*) 
                FROM trabalhos_realizados 
                WHERE devolvido_a IS NOT NULL AND devolvido_a != ''
                GROUP BY devolvido_a 
                ORDER BY COUNT(*) DESC
            """
            
            entregas = self.db_manager.fetch_all(query_entregas)
            devolucoes = self.db_manager.fetch_all(query_devolucoes)
            
            ranking = {}
            
            # Processa entregas
            for pessoa, count in entregas:
                if pessoa not in ranking:
                    ranking[pessoa] = {'entregas': 0, 'devolucoes': 0}
                ranking[pessoa]['entregas'] = count
            
            # Processa devoluções
            for pessoa, count in devolucoes:
                if pessoa not in ranking:
                    ranking[pessoa] = {'entregas': 0, 'devolucoes': 0}
                ranking[pessoa]['devolucoes'] = count
            
            return ranking
            
        except Exception as e:
            self.logger.error(f"Erro ao obter ranking de pessoas: {e}")
            return {}
    
    def get_resumo_geral(self) -> Dict[str, any]:
        """Retorna um resumo geral das estatísticas.
        
        Returns:
            Dicionário com resumo geral.
        """
        try:
            resumo = {
                'total_processos': self.get_total_processos(),
                'total_excluidos': self.get_total_excluidos(),
                'por_situacao': self.get_processos_por_situacao(),
                'tempo_medio_conclusao': self.get_tempo_medio_conclusao(),
                'processos_em_atraso': len(self.get_processos_em_atraso())
            }
            
            return resumo
            
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo geral: {e}")
            return {}
    
    def get_dados_exportacao(self, filtros: Optional[Dict] = None) -> List[Tuple]:
        """Retorna dados formatados para exportação.
        
        Args:
            filtros: Filtros opcionais para aplicar.
            
        Returns:
            Lista de tuplas com dados para exportação.
        """
        try:
            query = """
                SELECT data_registro, numero_processo, secretaria, numero_licitacao,
                       situacao, modalidade, data_inicio, data_entrega,
                       entregue_por, devolvido_a, contratado, descricao
                FROM trabalhos_realizados
                WHERE 1=1
            """
            params = []
            
            # Aplica filtros se fornecidos
            if filtros:
                if filtros.get('secretaria'):
                    query += " AND secretaria = ?"
                    params.append(filtros['secretaria'])
                
                if filtros.get('situacao'):
                    query += " AND situacao = ?"
                    params.append(filtros['situacao'])
                
                if filtros.get('data_inicio') and filtros.get('data_fim'):
                    query += " AND data_registro BETWEEN ? AND ?"
                    params.extend([filtros['data_inicio'], filtros['data_fim']])
            
            query += " ORDER BY data_registro DESC"
            
            return self.db_manager.fetch_all(query, tuple(params) if params else None)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados para exportação: {e}")
            return []