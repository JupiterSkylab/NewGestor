# MiniGestor - Sistema de Gestão de Processos v2.0

## Descrição

O MiniGestor é um sistema de gestão de processos desenvolvido para a Prefeitura de Caucaia. Esta versão 2.0 representa uma refatoração completa do código original, implementando uma arquitetura modular baseada no padrão MVC (Model-View-Controller).

## Características Principais

- **Interface Gráfica Intuitiva**: Interface desenvolvida em Tkinter com design moderno
- **Gestão Completa de Processos**: Cadastro, edição, exclusão e busca de processos
- **Exportação de Dados**: Suporte para exportação em PDF, Excel e backup de banco de dados
- **Sistema de Cache**: Cache inteligente com TTL para melhor performance
- **Backup Automático**: Integração com Git para versionamento automático
- **Logging Avançado**: Sistema de logs detalhado para auditoria e debugging
- **Validação de Dados**: Validação robusta de entradas e datas
- **Autocompletar**: Campos com sugestões automáticas para agilizar o cadastro

## Estrutura do Projeto

```
VSCODE TESTE/
├── main.py                 # Ponto de entrada da aplicação
├── config.py              # Configurações gerais
├── logger_config.py       # Configuração de logging
├── cache_manager.py       # Gerenciador de cache (legado)
├── GESTOR_TESTE.py       # Arquivo original (mantido para referência)
├── 
├── controllers/           # Controladores (lógica de negócio)
│   ├── __init__.py
│   ├── process_controller.py    # Controle de processos
│   ├── export_controller.py     # Controle de exportações
│   └── backup_controller.py     # Controle de backups
├── 
├── models/               # Modelos de dados
│   ├── __init__.py
│   ├── database_model.py       # Modelo do banco de dados
│   ├── process_model.py        # Modelo de processos
│   └── validators.py           # Validadores de dados
├── 
├── services/             # Serviços (lógica de aplicação)
│   ├── __init__.py
│   ├── cache_service.py        # Serviço de cache
│   ├── export_service.py       # Serviço de exportação
│   └── backup_service.py       # Serviço de backup
├── 
├── utils/                # Utilitários
│   ├── __init__.py
│   ├── date_utils.py           # Utilitários de data
│   ├── string_utils.py         # Utilitários de string
│   └── validation_utils.py     # Utilitários de validação
├── 
├── views/                # Interface gráfica
│   ├── __init__.py
│   └── main_view.py            # View principal
├── 
└── logs/                 # Arquivos de log
    ├── gestor_processos.log
    ├── database.log
    ├── export.log
    ├── backup.log
    └── interface.log
```

## Requisitos

### Dependências Obrigatórias
- Python 3.7+
- tkinter (geralmente incluído com Python)
- sqlite3 (incluído com Python)

### Dependências Opcionais
- `openpyxl`: Para exportação Excel
- `reportlab`: Para exportação PDF
- `git`: Para funcionalidades de backup automático

## Instalação

1. **Clone ou baixe o projeto**:
   ```bash
   git clone <repositorio>
   cd "VSCODE TESTE"
   ```

2. **Instale as dependências opcionais** (recomendado):
   ```bash
   pip install openpyxl reportlab
   ```

3. **Verifique as dependências**:
   ```bash
   python main.py --check-deps
   ```

## Uso

### Execução Normal
```bash
python main.py
```

### Opções de Linha de Comando
```bash
python main.py --help          # Mostra ajuda
python main.py --version       # Mostra versão
python main.py --debug         # Executa em modo debug
python main.py --check-deps    # Verifica dependências
```

## Funcionalidades

### Gestão de Processos
- **Cadastro**: Adicione novos processos com validação automática
- **Edição**: Modifique processos existentes
- **Exclusão**: Remova processos com confirmação
- **Busca**: Pesquise por múltiplos critérios
- **Visualização**: Veja detalhes completos dos processos

### Exportação
- **PDF**: Relatórios formatados em PDF
- **Excel**: Planilhas com formatação avançada
- **Backup**: Exportação completa do banco de dados

### Sistema de Cache
- Cache automático de secretarias e modalidades
- TTL configurável para diferentes tipos de dados
- Limpeza automática de cache expirado
- Estatísticas de uso do cache

### Backup e Versionamento
- Backup automático com Git
- Exportação/importação de banco de dados
- Histórico de alterações
- Restauração de versões anteriores

## Configuração

As configurações principais estão no arquivo `config.py`:

```python
# Exemplo de configurações
APP_CONFIG = {
    'database_path': 'meus_trabalhos.db',
    'backup_interval': 3600,  # 1 hora
    'cache_ttl': 1800,        # 30 minutos
    'log_level': 'INFO'
}
```

## Logs

O sistema gera logs detalhados em diferentes categorias:

- **gestor_processos.log**: Log geral da aplicação
- **database.log**: Operações de banco de dados
- **export.log**: Operações de exportação
- **backup.log**: Operações de backup
- **interface.log**: Eventos da interface gráfica

## Migração da Versão Anterior

A nova versão é compatível com o banco de dados existente. O arquivo `GESTOR_TESTE.py` original foi mantido para referência, mas a nova aplicação deve ser executada através do `main.py`.

## Desenvolvimento

### Arquitetura

A aplicação segue o padrão MVC:

- **Models**: Gerenciam dados e lógica de negócio
- **Views**: Interface gráfica e interação com usuário
- **Controllers**: Coordenam Models e Views
- **Services**: Lógica de aplicação reutilizável
- **Utils**: Funções utilitárias

### Adicionando Novas Funcionalidades

1. **Novo Model**: Adicione em `models/`
2. **Novo Service**: Adicione em `services/`
3. **Novo Controller**: Adicione em `controllers/`
4. **Nova View**: Adicione em `views/`
5. **Utilitários**: Adicione em `utils/`

### Testes

Para testar componentes específicos:

```bash
# Teste do cache
python test_cache_integration.py

# Teste com debug
python main.py --debug
```

## Solução de Problemas

### Problemas Comuns

1. **Erro de importação**: Verifique se todos os arquivos estão presentes
2. **Banco não encontrado**: Será criado automaticamente na primeira execução
3. **Erro de permissão**: Execute com permissões adequadas
4. **Cache não funciona**: Verifique configurações de TTL

### Debug

Para debug detalhado:
```bash
python main.py --debug
```

Verifique os logs em `logs/` para informações detalhadas.

## Contribuição

Para contribuir com o projeto:

1. Mantenha a estrutura modular
2. Adicione logs apropriados
3. Documente novas funcionalidades
4. Teste antes de submeter alterações

## Licença

Este software foi desenvolvido para uso interno da Prefeitura de Caucaia.

## Suporte

Para suporte técnico, consulte os logs da aplicação e a documentação do código.

---

**Versão**: 2.0  
**Data**: 2024  
**Desenvolvido para**: Prefeitura de Caucaia