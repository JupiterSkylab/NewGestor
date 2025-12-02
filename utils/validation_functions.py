"""Funções de validação reutilizáveis para a aplicação."""

import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from utils.shared_functions import validar_data


def validar_campos_obrigatorios(numero_processo, secretaria, data_inicio, data_entrega=None, entrada_recebimento=None, entrada_devolucao=None, entrada_entregue_por=None):
    """
    Verifica se os campos obrigatórios estão preenchidos e se as datas são válidas e lógicas.
    - Campos obrigatórios: número_processo, secretaria, data_inicio
    - Formato das datas: DD/MM/AAAA
    - Lógica das datas: devolução não pode ser antes do recebimento nem no futuro
    - Datas não podem ser em fins de semana (sábado ou domingo)
    """
    # Função auxiliar para verificar se é fim de semana
    def eh_fim_de_semana(data_obj):
        return data_obj.weekday() >= 5  # 5=sábado, 6=domingo
    
    # Lista para acumular erros
    erros = []
    
    # Verifica campos obrigatórios
    if not numero_processo.strip():
        erros.append("Número do processo é obrigatório")
    if not secretaria.strip():
        erros.append("Secretaria é obrigatória")
    if not data_inicio.strip():
        erros.append("Data de recebimento é obrigatória")
    
    # Se há erros básicos, mostra todos de uma vez
    if erros:
        messagebox.showwarning("Campos obrigatórios", "\n".join(erros))
        return False

    # Valida data de início
    if not validar_data(data_inicio):
        messagebox.showerror("Data inválida", "Data de recebimento inválida. Use o formato DD/MM/AAAA.")
        if entrada_recebimento:
            entrada_recebimento.focus_set()
        return False
    
    # Verifica se data de recebimento é fim de semana
    try:
        data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y")
        if eh_fim_de_semana(data_inicio_dt):
            dia_semana = "sábado" if data_inicio_dt.weekday() == 5 else "domingo"
            messagebox.showwarning("Data inválida", f"A data de recebimento não pode ser em {dia_semana}.")
            if entrada_recebimento:
                entrada_recebimento.focus_set()
            return False
    except ValueError:
        # Se chegou aqui, a data já foi validada acima, então não deveria dar erro
        pass

    # Verifica campo "Entregue por" se o widget foi fornecido
    if entrada_entregue_por and not entrada_entregue_por.get().strip():
        messagebox.showwarning("Campo obrigatório", "Preencha o campo 'Entregue por'.")
        entrada_entregue_por.focus_set()
        return False

    # Valida data de entrega se fornecida
    if data_entrega and data_entrega.strip():
        if not validar_data(data_entrega):
            messagebox.showerror("Data inválida", "Data de devolução inválida. Use o formato DD/MM/AAAA.")
            if entrada_devolucao:
                entrada_devolucao.focus_set()
            return False
        
        # Verifica se data de devolução é fim de semana
        try:
            data_entrega_dt = datetime.strptime(data_entrega, "%d/%m/%Y")
            if eh_fim_de_semana(data_entrega_dt):
                dia_semana = "sábado" if data_entrega_dt.weekday() == 5 else "domingo"
                messagebox.showwarning("Data inválida", f"A data de devolução não pode ser em {dia_semana}.")
                if entrada_devolucao:
                    entrada_devolucao.focus_set()
                return False
        except ValueError:
            pass
        
        # Verifica se data de devolução não é anterior à data de recebimento
        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y")
            data_entrega_dt = datetime.strptime(data_entrega, "%d/%m/%Y")
            
            if data_entrega_dt < data_inicio_dt:
                messagebox.showwarning("Data inválida", "A data de devolução não pode ser anterior à data de recebimento.")
                if entrada_devolucao:
                    entrada_devolucao.focus_set()
                return False
        except ValueError:
            pass
        
        # Verifica se data de devolução não é no futuro
        try:
            data_entrega_dt = datetime.strptime(data_entrega, "%d/%m/%Y")
            hoje = datetime.now().date()
            
            if data_entrega_dt.date() > hoje:
                messagebox.showwarning("Data inválida", "A data de devolução não pode ser no futuro.")
                if entrada_devolucao:
                    entrada_devolucao.focus_set()
                return False
        except ValueError:
            pass

    return True


def checar_data_entry(entry_widget):
    """
    Verifica se a data inserida no widget está no formato correto (DD/MM/AAAA)
    e destaca o campo em vermelho se inválida.
    """
    data = entry_widget.get().strip()
    
    if data:  # Só valida se há algo digitado
        if validar_data(data):
            # Data válida - remove destaque vermelho
            entry_widget.config(bg="white")
            
            # Chama validação em tempo real se disponível
            try:
                validar_periodo_datas_tempo_real()
            except:
                pass  # Ignora se a função não estiver disponível
        else:
            # Data inválida - destaca em vermelho
            entry_widget.config(bg="#ffcccc")
            
            # Mostra tooltip com formato esperado
            try:
                # Remove tooltip anterior se existir
                if hasattr(entry_widget, '_tooltip'):
                    entry_widget._tooltip.destroy()
                
                # Cria novo tooltip
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.configure(bg="#ffffe0")
                
                label = tk.Label(tooltip, text="Formato: DD/MM/AAAA", 
                               bg="#ffffe0", fg="black", font=("Arial", 8))
                label.pack()
                
                # Posiciona o tooltip
                x = entry_widget.winfo_rootx() + entry_widget.winfo_width() + 5
                y = entry_widget.winfo_rooty()
                tooltip.geometry(f"+{x}+{y}")
                
                # Remove tooltip após 3 segundos
                tooltip.after(3000, tooltip.destroy)
                entry_widget._tooltip = tooltip
                
            except:
                pass  # Ignora erros de tooltip
    else:
        # Campo vazio - remove destaque
        entry_widget.config(bg="white")


def formatar_data_hora(event):
    """
    Formata automaticamente a entrada de data/hora enquanto o usuário digita.
    Adiciona barras automaticamente no formato DD/MM/AAAA.
    """
    widget = event.widget
    texto = widget.get()
    
    # Remove caracteres não numéricos exceto barras
    texto_limpo = re.sub(r'[^0-9/]', '', texto)
    
    # Adiciona barras automaticamente
    if len(texto_limpo) >= 2 and texto_limpo[2] != '/':
        texto_limpo = texto_limpo[:2] + '/' + texto_limpo[2:]
    if len(texto_limpo) >= 5 and texto_limpo[5] != '/':
        texto_limpo = texto_limpo[:5] + '/' + texto_limpo[5:]
    
    # Limita o tamanho
    texto_limpo = texto_limpo[:10]
    
    # Atualiza o widget
    widget.delete(0, tk.END)
    widget.insert(0, texto_limpo)


def formatar_data_hora_str(data):
    """
    Formata uma string de data/hora para exibição.
    Converte de formato ISO para DD/MM/AAAA HH:MM ou DD/MM/AAAA.
    """
    if not data:
        return ""

    try:
        return datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except Exception:
        # Tenta outros formatos comuns de data
        try:
            if '-' in data and len(data) >= 10:
                return datetime.strptime(data[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            pass
        return data


class ValidationUtils:
    """Classe utilitária para validações."""
    
    @staticmethod
    def validar_periodo_datas(data_inicio, data_fim, nome_inicio="Data de início", nome_fim="Data de fim"):
        """Valida se o período entre duas datas é válido.
        
        Args:
            data_inicio (str): Data de início no formato DD/MM/AAAA
            data_fim (str): Data de fim no formato DD/MM/AAAA
            nome_inicio (str): Nome do campo de início para mensagens de erro
            nome_fim (str): Nome do campo de fim para mensagens de erro
            
        Returns:
            tuple: (bool, str) - (é_válido, mensagem_erro)
        """
        try:
            # Converte as datas para objetos datetime
            dt_inicio = datetime.strptime(data_inicio, "%d/%m/%Y")
            dt_fim = datetime.strptime(data_fim, "%d/%m/%Y")
            
            # Verifica se a data de fim não é anterior à data de início
            if dt_fim < dt_inicio:
                return False, f"{nome_fim} não pode ser anterior a {nome_inicio.lower()}."
            
            # Verifica se a data de fim não é no futuro
            hoje = datetime.now().date()
            if dt_fim.date() > hoje:
                return False, f"{nome_fim} não pode ser no futuro."
            
            return True, ""
            
        except ValueError:
            return False, "Formato de data inválido. Use DD/MM/AAAA."
