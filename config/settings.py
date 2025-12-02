"""Configurações gerais da aplicação."""

import os
from pathlib import Path

# Diretório base da aplicação
BASE_DIR = Path(__file__).parent.parent

# Configurações do banco de dados
DATABASE_CONFIG = {
    'path': BASE_DIR / 'meus_trabalhos.db',
    'timeout': 30.0,
    'check_same_thread': False
}

# Configurações da interface
UI_CONFIG = {
    'theme': 'clam',
    'window_size': (860, 650),
    'min_size': (800, 600),
    'font_family': 'Segoe UI',
    'font_size': 10
}

# Configurações de cache
CACHE_CONFIG = {
    'max_cache_size': 1000,
    'default_ttl': 3600,
    'cleanup_interval': 300,
    'max_memory_usage': 100 * 1024 * 1024  # 100MB
}

# Configurações de exportação
EXPORT_CONFIG = {
    'default_format': 'xlsx',
    'max_rows_per_sheet': 1000000,
    'date_format': '%d/%m/%Y',
    'datetime_format': '%d/%m/%Y %H:%M:%S',
    'encoding': 'utf-8',
    'csv_delimiter': ';'
}

# Configurações de backup
BACKUP_CONFIG = {
    'backup_interval': 3600,  # 1 hora em segundos
    'max_backups': 10,
    'backup_directory': 'backups',
    'compress_backups': True,
    'auto_backup': True
}

# Estilos padrão
STYLES = {
    'button': {
        'bg': '#394857',
        'fg': '#66c0f4',
        'activebackground': '#23262e',
        'activeforeground': '#66c0f4',
        'font': ('Segoe UI', 10, 'bold'),
        'relief': 'flat',
        'bd': 0,
        'highlightthickness': 1,
        'highlightbackground': '#394857'
    },
    'treeview': {
        'heading_font': ('Segoe UI', 10, 'bold'),
        'heading_bg': '#607D8B',
        'heading_fg': 'white',
        'font': ('Segoe UI', 10),
        'rowheight': 26,
        'selected_bg': '#B0BEC5'
    },
    'frame': {
        'bg': '#ECEFF1',
        'fg': '#37474F'
    }
}

# Configurações de backup
BACKUP_CONFIG = {
    'auto_backup': True,
    'backup_interval': 3600,  # 1 hora em segundos
    'max_backups': 10
}

# Configurações de exportação
EXPORT_CONFIG = {
    'excel_format': '.xlsx',
    'pdf_format': '.pdf',
    'default_export_dir': BASE_DIR / 'exports'
}

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': BASE_DIR / 'logs' / 'gestor_processos.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}

# Secretarias disponíveis
SECRETARIAS = {
    "ASCOM": "Assessoria de Comunicação",
    "AMT": "Autarquia Municipal de Trânsito",
    "CGM": "Controladoria-Geral do Município",
    "GP": "Gabinete do Prefeito",
    "GVP": "Gabinete do(a) Vice-prefeito(a)",
    "IPMC": "Instituto de Previdência do Município de Caucaia",
    "IMAC": "Instituto do Meio Ambiente do Município de Caucaia",
    "OGM": "Ouvidoria-Geral do Município",
    "PGM": "Procuradoria-Geral do Município",
    "SEAD": "Secretaria de Administração e Recursos Humanos",
    "SEPA": "Secretaria de Proteção Animal",
    "SERGJ": "Secretaria Executiva Regional da Grande Jurema",
    "SERL": "Secretaria Executiva Regional do Litoral",
    "SERS": "Secretaria Executiva Regional do Sertão",
    "SECITEC": "Secretaria Municipal de Ciência, Inovação e Desenvolvimento Tecnológico",
    "SECULT": "Secretaria Municipal de Cultura",
    "SEDEC": "Secretaria Municipal de Desenvolvimento Econômico",
    "SDR": "Secretaria Municipal de Desenvolvimento Rural",
    "SDST": "Secretaria Municipal de Desenvolvimento Social",
    "SME": "Secretaria Municipal de Educação",
    "SEJUV": "Secretaria Municipal de Esporte e Juventude",
    "SEFIN": "Secretaria Municipal de Finanças, Planejamento e Orçamento",
    "SEINFRA": "Secretaria Municipal de Infraestrutura",
    "SPTRAN": "Secretaria Municipal de Patrimônio e Transporte",
    "SEPLAM": "Secretaria Municipal de Planejamento Urbano e Ambiental",
    "SMS": "Secretaria Municipal de Saúde",
    "SSP": "Secretaria Municipal de Segurança Pública",
    "SETUR": "Secretaria Municipal de Turismo",
    "STM": "Secretaria Municipal do Trabalho"
}

# Modalidades de licitação
MODALIDADES_LICITACAO = [
    "Pregão Eletrônico",
    "Pregão Presencial",
    "Concorrência",
    "Tomada de Preços",
    "Convite",
    "Dispensa de Licitação",
    "Inexigibilidade"
]

# Situações possíveis
SITUACOES = ["Em Andamento", "Concluído"]