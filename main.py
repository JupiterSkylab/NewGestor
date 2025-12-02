#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniGestor - Sistema de Gestão de Processos
Prefeitura de Caucaia

Ponto de entrada principal da aplicação refatorada.
Este arquivo substitui o GESTOR_TESTE.py original com uma arquitetura modular.

Autor: Sistema de Gestão de Processos
Versão: 2.0
Data: 2024
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path do Python
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

try:
    # Importações principais
    from logger_config import setup_logger, log_operation, log_error, app_logger
    from views.main_view import run_application
    
    def main():
        """
        Função principal da aplicação
        """
        try:
            # Configurar logging (já configurado automaticamente)
            log_operation(app_logger, "Iniciando MiniGestor v2.0")
            
            # Verificar dependências
            check_dependencies()
            
            # Executar aplicação
            log_operation(app_logger, "Iniciando interface gráfica")
            run_application()
            
        except KeyboardInterrupt:
            log_operation(app_logger, "Aplicação interrompida pelo usuário")
            sys.exit(0)
        except Exception as e:
            log_error(app_logger, e, "Erro crítico na aplicação")
            print(f"Erro crítico: {e}")
            sys.exit(1)
        finally:
            log_operation(app_logger, "Finalizando MiniGestor")
    
    def check_dependencies():
        """
        Verifica se todas as dependências estão disponíveis
        """
        required_modules = [
            'tkinter',
            'sqlite3',
            'datetime',
            'threading',
            'json',
            'os',
            'sys',
            'pathlib',
            'logging',
            'time',
            'subprocess'
        ]
        
        optional_modules = {
            'openpyxl': 'Exportação para Excel',
            'reportlab': 'Exportação para PDF',
            'git': 'Integração com Git para backups'
        }
        
        missing_required = []
        missing_optional = []
        
        # Verificar módulos obrigatórios
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_required.append(module)
        
        # Verificar módulos opcionais
        for module, description in optional_modules.items():
            try:
                __import__(module)
            except ImportError:
                missing_optional.append(f"{module} ({description})")
        
        # Reportar dependências faltantes
        if missing_required:
            error_msg = f"Módulos obrigatórios não encontrados: {', '.join(missing_required)}"
            app_logger.error(error_msg)
            raise ImportError(error_msg)
        
        if missing_optional:
            warning_msg = f"Módulos opcionais não encontrados: {', '.join(missing_optional)}"
            app_logger.warning(f"AVISO: {warning_msg}")
            print(f"Aviso: {warning_msg}")
        
        log_operation(app_logger, "Verificação de dependências concluída")
    
    def show_help():
        """
        Mostra informações de ajuda
        """
        help_text = """
MiniGestor - Sistema de Gestão de Processos v2.0
Prefeitura de Caucaia

Uso: python main.py [opções]

Opções:
  -h, --help     Mostra esta mensagem de ajuda
  -v, --version  Mostra a versão da aplicação
  --debug        Executa em modo debug
  --check-deps   Verifica dependências e sai

Exemplos:
  python main.py              # Executa a aplicação normalmente
  python main.py --debug      # Executa com logging detalhado
  python main.py --check-deps # Verifica apenas as dependências

Para mais informações, consulte a documentação.
        """
        print(help_text)
    
    def show_version():
        """
        Mostra informações de versão
        """
        version_info = f"""
MiniGestor v2.0
Sistema de Gestão de Processos
Prefeitura de Caucaia

Arquitetura: Modular (MVC)
Python: {sys.version}
Plataforma: {sys.platform}
        """
        print(version_info)
    
    if __name__ == "__main__":
        # Processar argumentos da linha de comando
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()
            
            if arg in ['-h', '--help']:
                show_help()
                sys.exit(0)
            elif arg in ['-v', '--version']:
                show_version()
                sys.exit(0)
            elif arg == '--debug':
                os.environ['DEBUG'] = '1'
                main()
            elif arg == '--check-deps':
                try:
                    check_dependencies()
                    print("✓ Todas as dependências obrigatórias estão disponíveis")
                    sys.exit(0)
                except Exception as e:
                    print(f"✗ Erro na verificação de dependências: {e}")
                    sys.exit(1)
            else:
                print(f"Argumento desconhecido: {arg}")
                print("Use --help para ver as opções disponíveis")
                sys.exit(1)
        else:
            # Execução normal
            main()

except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Verifique se todos os arquivos necessários estão presentes.")
    sys.exit(1)
except Exception as e:
    print(f"Erro crítico durante a inicialização: {e}")
    sys.exit(1)