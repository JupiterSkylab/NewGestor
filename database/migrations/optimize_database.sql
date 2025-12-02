-- Script de otimização do banco de dados
-- Adiciona índices para melhorar performance das consultas

-- Índices para a tabela trabalhos_realizados

-- Índice principal para número do processo (usado em buscas e joins)
CREATE INDEX IF NOT EXISTS idx_trabalhos_numero_processo 
ON trabalhos_realizados(numero_processo);

-- Índice para secretaria (usado em filtros)
CREATE INDEX IF NOT EXISTS idx_trabalhos_secretaria 
ON trabalhos_realizados(secretaria);

-- Índice para situação (usado em filtros e ordenação)
CREATE INDEX IF NOT EXISTS idx_trabalhos_situacao 
ON trabalhos_realizados(situacao);

-- Índice para modalidade (usado em filtros)
CREATE INDEX IF NOT EXISTS idx_trabalhos_modalidade 
ON trabalhos_realizados(modalidade);

-- Índice para data de registro (usado em ordenação)
CREATE INDEX IF NOT EXISTS idx_trabalhos_data_registro 
ON trabalhos_realizados(data_registro DESC);

-- Índice para data de início (usado em buscas por período)
CREATE INDEX IF NOT EXISTS idx_trabalhos_data_inicio 
ON trabalhos_realizados(data_inicio);

-- Índice para data de entrega (usado em buscas por período)
CREATE INDEX IF NOT EXISTS idx_trabalhos_data_entrega 
ON trabalhos_realizados(data_entrega);

-- Índice composto para filtros mais comuns (secretaria + situação)
CREATE INDEX IF NOT EXISTS idx_trabalhos_secretaria_situacao 
ON trabalhos_realizados(secretaria, situacao);

-- Índice para nomes (usado em autocompletar)
CREATE INDEX IF NOT EXISTS idx_trabalhos_entregue_por 
ON trabalhos_realizados(entregue_por) 
WHERE entregue_por IS NOT NULL AND entregue_por != '';

CREATE INDEX IF NOT EXISTS idx_trabalhos_devolvido_a 
ON trabalhos_realizados(devolvido_a) 
WHERE devolvido_a IS NOT NULL AND devolvido_a != '';

-- Índices para a tabela trabalhos_excluidos

-- Índice para número do processo (usado em restauração)
CREATE INDEX IF NOT EXISTS idx_excluidos_numero_processo 
ON trabalhos_excluidos(numero_processo);

-- Índice para data de exclusão (usado em ordenação e limpeza)
CREATE INDEX IF NOT EXISTS idx_excluidos_data_exclusao 
ON trabalhos_excluidos(data_exclusao DESC);

-- Índices para a tabela promessas (se existir)

-- Índice para data prometida (usado em ordenação)
CREATE INDEX IF NOT EXISTS idx_promessas_data_prometida 
ON promessas(data_prometida);

-- Índice para busca em descrição (FTS - Full Text Search)
CREATE INDEX IF NOT EXISTS idx_promessas_descricao 
ON promessas(descricao);

-- Análise das tabelas para otimizar o plano de consulta
ANALYZE trabalhos_realizados;
ANALYZE trabalhos_excluidos;
ANALYZE promessas;

-- Configurações de otimização do SQLite
PRAGMA optimize;
PRAGMA journal_mode = WAL;  -- Write-Ahead Logging para melhor concorrência
PRAGMA synchronous = NORMAL;  -- Balanço entre performance e segurança
PRAGMA cache_size = -64000;  -- Cache de 64MB
PRAGMA temp_store = MEMORY;  -- Armazena tabelas temporárias na memória
PRAGMA mmap_size = 268435456;  -- Memory-mapped I/O de 256MB

-- Vacuum para otimizar o arquivo do banco
VACUUM;