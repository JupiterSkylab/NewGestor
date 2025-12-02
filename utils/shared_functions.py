# -*- coding: utf-8 -*-
"""
Funções compartilhadas para evitar duplicação de código entre os módulos principais
"""

import sqlite3
import threading
import subprocess
import os
from datetime import datetime, timedelta
from tkinter import messagebox
from services.backup_service import verificar_mudancas_e_backup as backup_service_func





def verificar_mudancas_e_backup():
    """Verifica mudanças no repositório Git e inicia backup se necessário.
    
    Esta função verifica se há mudanças não commitadas no repositório Git
    e inicia o processo de backup em uma thread separada se houver alterações.
    """
    try:
        # Verifica se há mudanças no repositório
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print("Mudanças detectadas no repositório. Iniciando backup...")
            
            # Inicia o backup em uma thread separada
            backup_thread = threading.Thread(
                target=backup_service_func,
                daemon=True
            )
            backup_thread.start()
            
        else:
            print("Nenhuma mudança detectada no repositório.")
            
    except FileNotFoundError:
        print("Git não encontrado. Backup automático desabilitado.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao verificar status do Git: {e}")
    except Exception as e:
        print(f"Erro inesperado ao verificar mudanças: {e}")


def carregar_nomes_autocomplete(db_path):
    """Carrega nomes únicos do banco de dados para autocompletar.
    
    Args:
        db_path (str): Caminho para o banco de dados
        
    Returns:
        list: Lista de nomes únicos para autocompletar
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT nome FROM (
                SELECT entregue_por AS nome FROM trabalhos_realizados 
                WHERE entregue_por IS NOT NULL AND entregue_por != ''
                UNION
                SELECT devolvido_a AS nome FROM trabalhos_realizados 
                WHERE devolvido_a IS NOT NULL AND devolvido_a != ''
            ) ORDER BY UPPER(nome)
        """)
        
        nomes = [row[0].upper() for row in cursor.fetchall()]
        conn.close()
        
        return nomes
        
    except Exception as e:
        print(f"Erro ao carregar nomes para autocompletar: {e}")
        return []


def validar_data(data_str):
    """Valida se uma string representa uma data válida no formato DD/MM/AAAA.
    
    Args:
        data_str (str): String da data a ser validada
        
    Returns:
        bool: True se a data for válida, False caso contrário
    """
    if not data_str or data_str.strip() == "":
        return True  # Data vazia é considerada válida
    
    try:
        # Remove espaços e verifica formato básico
        data_str = data_str.strip()
        if len(data_str) != 10 or data_str.count('/') != 2:
            return False
            
        # Tenta converter para datetime
        datetime.strptime(data_str, '%d/%m/%Y')
        return True
        
    except ValueError:
        return False





def atualizar_lista_autocomplete(db_path, novo_nome=None):
    """Atualiza a lista de autocompletar com novos nomes.
    
    Args:
        db_path (str): Caminho para o banco de dados
        novo_nome (str, optional): Novo nome para adicionar à lista
        
    Returns:
        list: Lista atualizada de nomes para autocompletar
    """
    nomes = carregar_nomes_autocomplete(db_path)
    
    if novo_nome and novo_nome.strip() and novo_nome not in nomes:
        nomes.append(novo_nome.strip())
        nomes.sort(key=lambda x: x.lower())
    
    return nomes