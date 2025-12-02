#!/usr/bin/env python3
"""Script para aplicar otimizações no banco de dados do MiniGestor TRAE."""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Adiciona o diretório pai ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database_optimizer import QueryOptimizer

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_optimization.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_database_path():
    """Obtém o caminho do banco de dados."""
    # Procura pelo arquivo do banco na estrutura do projeto
    possible_paths = [
        'meus_trabalhos.db',
        'trabalhos_realizados.db',
        'database/meus_trabalhos.db',
        'database/trabalhos_realizados.db',
        '../meus_trabalhos.db',
        'data/meus_trabalhos.db'
    ]
    
    base_dir = Path(__file__).parent.parent
    
    for path in possible_paths:
        full_path = base_dir / path
        if full_path.exists():
            return str(full_path)
    
    # Se não encontrar, usa o caminho padrão do MiniGestor
    return str(base_dir / 'meus_trabalhos.db')

def apply_sql_optimizations(db_path: str):
    """Aplica as otimizações SQL definidas no arquivo de migração."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Aplicando otimizações SQL...")
        
        # Índices para a tabela trabalhos_realizados
        indexes = [
            ("idx_trabalhos_numero_processo", "trabalhos_realizados", "numero_processo"),
            ("idx_trabalhos_secretaria", "trabalhos_realizados", "secretaria"),
            ("idx_trabalhos_situacao", "trabalhos_realizados", "situacao"),
            ("idx_trabalhos_modalidade", "trabalhos_realizados", "modalidade"),
            ("idx_trabalhos_data_registro", "trabalhos_realizados", "data_registro DESC"),
            ("idx_trabalhos_data_inicio", "trabalhos_realizados", "data_inicio"),
            ("idx_trabalhos_data_entrega", "trabalhos_realizados", "data_entrega"),
        ]
        
        # Índices compostos
        composite_indexes = [
            ("idx_trabalhos_secretaria_situacao", "trabalhos_realizados", "secretaria, situacao"),
        ]
        
        # Índices condicionais
        conditional_indexes = [
            ("idx_trabalhos_entregue_por", "trabalhos_realizados", "entregue_por", 
             "entregue_por IS NOT NULL AND entregue_por != ''"),
            ("idx_trabalhos_devolvido_a", "trabalhos_realizados", "devolvido_a", 
             "devolvido_a IS NOT NULL AND devolvido_a != ''"),
        ]
        
        # Criar índices simples
        for index_name, table, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                logger.info(f"Índice criado: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao criar índice {index_name}: {e}")
        
        # Criar índices compostos
        for index_name, table, columns in composite_indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns})")
                logger.info(f"Índice composto criado: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao criar índice composto {index_name}: {e}")
        
        # Criar índices condicionais
        for index_name, table, column, condition in conditional_indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column}) WHERE {condition}")
                logger.info(f"Índice condicional criado: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao criar índice condicional {index_name}: {e}")
        
        # Índices para trabalhos_excluidos
        excluded_indexes = [
            ("idx_excluidos_numero_processo", "trabalhos_excluidos", "numero_processo"),
            ("idx_excluidos_data_exclusao", "trabalhos_excluidos", "data_exclusao DESC"),
        ]
        
        for index_name, table, column in excluded_indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                logger.info(f"Índice para excluídos criado: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao criar índice para excluídos {index_name}: {e}")
        
        # Verificar se a tabela promessas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promessas'")
        if cursor.fetchone():
            promessas_indexes = [
                ("idx_promessas_data_prometida", "promessas", "data_prometida"),
                ("idx_promessas_descricao", "promessas", "descricao"),
            ]
            
            for index_name, table, column in promessas_indexes:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                    logger.info(f"Índice para promessas criado: {index_name}")
                except sqlite3.Error as e:
                    logger.warning(f"Erro ao criar índice para promessas {index_name}: {e}")
        
        # Analisar tabelas
        tables_to_analyze = ['trabalhos_realizados', 'trabalhos_excluidos']
        if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promessas'").fetchone():
            tables_to_analyze.append('promessas')
        
        for table in tables_to_analyze:
            try:
                cursor.execute(f"ANALYZE {table}")
                logger.info(f"Tabela analisada: {table}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao analisar tabela {table}: {e}")
        
        # Configurações de otimização
        optimizations = [
            "PRAGMA optimize",
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -64000",  # 64MB
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",  # 256MB
        ]
        
        for optimization in optimizations:
            try:
                cursor.execute(optimization)
                logger.info(f"Otimização aplicada: {optimization}")
            except sqlite3.Error as e:
                logger.warning(f"Erro ao aplicar otimização {optimization}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info("Otimizações SQL aplicadas com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao aplicar otimizações SQL: {e}")
        return False

def run_vacuum(db_path: str):
    """Executa VACUUM para otimizar o arquivo do banco."""
    try:
        logger.info("Executando VACUUM...")
        conn = sqlite3.connect(db_path)
        conn.isolation_level = None  # Autocommit mode para VACUUM
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.close()
        logger.info("VACUUM executado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao executar VACUUM: {e}")
        return False

def generate_performance_report(db_path: str):
    """Gera relatório de performance usando o QueryOptimizer."""
    try:
        logger.info("Gerando relatório de performance...")
        optimizer = QueryOptimizer(db_path)
        
        # Executar otimização automática
        optimization_results = optimizer.optimize_database()
        logger.info(f"Otimização automática concluída em {optimization_results['total_time']:.3f}s")
        
        # Analisar consultas lentas
        slow_queries = optimizer.analyze_slow_queries()
        if slow_queries:
            logger.info(f"Encontradas {len(slow_queries)} consultas lentas")
            for query in slow_queries[:5]:  # Mostrar apenas as 5 piores
                logger.info(f"  - {query['avg_time']:.3f}s: {query['sql'][:100]}...")
        
        # Gerar relatório completo
        report = optimizer.get_performance_report()
        logger.info(f"Relatório: {report['summary']['total_queries']} consultas executadas")
        logger.info(f"Cache hit rate: {report['cache']['hit_rate']:.1%}")
        
        # Criar índices recomendados
        index_results = optimizer.create_recommended_indexes()
        created_indexes = sum(index_results.values())
        if created_indexes > 0:
            logger.info(f"Índices adicionais criados: {created_indexes}")
        
        optimizer.close()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de performance: {e}")
        return False

def main():
    """Função principal do script."""
    logger.info("Iniciando otimização do banco de dados...")
    
    # Obter caminho do banco
    db_path = get_database_path()
    logger.info(f"Banco de dados: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"Banco de dados não encontrado: {db_path}")
        return False
    
    # Fazer backup do banco antes das otimizações
    backup_path = f"{db_path}.backup_{int(time.time())}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backup criado: {backup_path}")
    except Exception as e:
        logger.warning(f"Erro ao criar backup: {e}")
    
    success = True
    
    # Aplicar otimizações SQL
    if not apply_sql_optimizations(db_path):
        success = False
    
    # Executar VACUUM
    if not run_vacuum(db_path):
        success = False
    
    # Gerar relatório de performance
    if not generate_performance_report(db_path):
        success = False
    
    if success:
        logger.info("Otimização do banco de dados concluída com sucesso!")
    else:
        logger.error("Otimização concluída com alguns erros. Verifique os logs.")
    
    return success

if __name__ == "__main__":
    import time
    start_time = time.time()
    
    success = main()
    
    end_time = time.time()
    logger.info(f"Tempo total de execução: {end_time - start_time:.2f}s")
    
    sys.exit(0 if success else 1)