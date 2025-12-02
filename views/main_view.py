# -*- coding: utf-8 -*-
"""
View Principal para o Gestor de Processos
Implementa a interface gráfica principal da aplicação
"""

import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Callable

from config.settings import UI_CONFIG
from config.settings import SECRETARIAS, MODALIDADES_LICITACAO
from controllers.process_controller import ProcessController
from controllers.export_controller import ExportController
from controllers.backup_controller import BackupController
from services.cache_service import get_cached_secretarias, get_cached_modalidades
from utils.string_utils import StringUtils
from utils.date_utils import DateUtils
from utils.validation_functions import ValidationUtils
from logger_config import log_operation, log_error, ui_logger


class AutocompleteEntry(Entry):
    """
    Widget Entry com funcionalidade de autocompletar
    """
    def __init__(self, parent, completion_list, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.completion_list = completion_list
        self.listbox = None
        self.listbox_aberta = False
        self.deslocamento_x = 0
        self.deslocamento_y = 0
        self.largura_listbox = None
        self.altura_maxima = 8
        
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focusout)
        self.bind('<Button-1>', self._on_click)
        
    def set_listbox_properties(self, x_offset=0, y_offset=0, width=None, max_height=8):
        """Configura propriedades da listbox de sugestões"""
        self.deslocamento_x = x_offset
        self.deslocamento_y = y_offset
        self.largura_listbox = width
        self.altura_maxima = max_height
        
    def _on_keyrelease(self, event):
        """Manipula eventos de tecla para mostrar sugestões"""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Tab', 'Return']:
            return
            
        text = self.get().lower()
        if len(text) < 1:
            self._close_listbox()
            return
            
        matches = [item for item in self.completion_list if text in item.lower()]
        
        if matches:
            self._show_listbox(matches)
        else:
            self._close_listbox()
            
    def _show_listbox(self, matches):
        """Mostra a listbox com sugestões"""
        if not self.listbox:
            self.listbox = Listbox(
                self.master,
                bg="#FFFFFF",
                fg="black",
                selectbackground="#0078d4",
                selectforeground="white"
            )
            self.listbox.bind('<Double-Button-1>', self._on_listbox_select)
            self.listbox.bind('<Return>', self._on_listbox_select)
            
        self.listbox.delete(0, END)
        for match in matches[:self.altura_maxima]:
            self.listbox.insert(END, match)
            
        x = self.winfo_rootx() + self.deslocamento_x
        y = self.winfo_rooty() + self.winfo_height() + self.deslocamento_y
        width = self.largura_listbox or self.winfo_width()
        height = min(len(matches), self.altura_maxima) * 20 + 5
        
        self.listbox.place(x=x, y=y, width=width, height=height)
        self.listbox_aberta = True
        
    def _close_listbox(self):
        """Fecha a listbox de sugestões"""
        if self.listbox:
            self.listbox.place_forget()
            self.listbox_aberta = False
            
    def _on_listbox_select(self, event):
        """Manipula seleção na listbox"""
        if self.listbox and self.listbox.curselection():
            selection = self.listbox.get(self.listbox.curselection()[0])
            self.delete(0, END)
            self.insert(0, selection)
            self._close_listbox()
            
    def _on_focusout(self, event):
        """Fecha listbox quando perde foco"""
        self.master.after(100, self._close_listbox)
        
    def _on_click(self, event):
        """Mostra sugestões ao clicar"""
        if self.get():
            self._on_keyrelease(event)


class ToolTip:
    """
    Classe para criar tooltips em widgets
    """
    def __init__(self, widget):
        self.widget = widget
        self.tooltip = None
        
    def show(self, text):
        """Mostra o tooltip"""
        if self.tooltip:
            return
            
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip = Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = Label(self.tooltip, text=text, background="#ffffe0",
                     relief="solid", borderwidth=1, font=("Arial", 8))
        label.pack()
        
    def hide(self):
        """Esconde o tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MainView:
    """
    View principal da aplicação
    """
    
    def __init__(self):
        self.janela = None
        self.widgets = {}
        self.variables = {}
        self.controllers = {}
        self.tooltip = None
        self.janela_lembretes_aberta = None
        self.ids_lembrete = {}
        
        # Estatísticas
        self.stats = {
            'registros_concluidos': 0,
            'registros_andamento': 0,
            'registros_editados': 0,
            'registros_apagados': 0,
            'registros_cadastrados': 0,
            'registros_exportados': 0,
            'registros_importados': 0,
            'registros_restaurados': 0
        }
        
        # Configurações da tabela
        self.colunas = (
            'data_registro', 'numero_processo', 'secretaria', 'numero_licitacao',
            'modalidade', 'contratado', 'data_inicio', 'data_entrega',
            'entregue_por', 'devolvido_a', 'situacao', 'descricao'
        )
        
        self.cabecalhos = {
            'data_registro': 'Data Registro',
            'numero_processo': 'Nº Processo',
            'secretaria': 'Secretaria',
            'numero_licitacao': 'Nº Licitação',
            'situacao': 'Situação',
            'modalidade': 'Modalidade',
            'contratado': 'Contratado',
            'data_inicio': 'Recebimento',
            'data_entrega': 'Devolução',
            'entregue_por': 'Entregue por',
            'devolvido_a': 'Devolvido para',
            'descricao': 'Descrição'
        }
        
        self.larguras_fixas = {
            'data_registro': 115,
            'numero_processo': 130,
            'secretaria': 70,
            'numero_licitacao': 115,
            'modalidade': 100,
            'contratado': 120,
            'situacao': 99,
            'data_inicio': 90,
            'data_entrega': 80,
            'entregue_por': 120,
            'devolvido_a': 120,
            'descricao': 250
        }
        
        self.ordem_colunas_reversa = {col: False for col in self.colunas}
        
    def setup_controllers(self):
        """Configura os controladores"""
        self.controllers['process'] = ProcessController()
        self.controllers['export'] = ExportController()
        self.controllers['backup'] = BackupController()
        
    def create_main_window(self):
        """Cria a janela principal"""
        self.janela = tk.Tk()
        self.janela.title("MiniGestor - Prefeitura de Caucaia")
        self.janela.configure(bg="#ECEFF1")

        # Aplicar tema escuro harmonioso
        try:
            from utils.ui_config import get_theme, apply_dark_theme_to_all_widgets
            theme = get_theme()
            theme.root = self.janela
            theme.apply_theme("dark")
            # Após construir os widgets, aplica uma passagem de estilização
            self.janela.after(0, lambda: apply_dark_theme_to_all_widgets(self.janela))
        except Exception:
            pass
        
        # Centralizar janela
        self._center_window()
        
        # Configurar estilo
        self._setup_styles()
        
        # Configurar variáveis
        self._setup_variables()
        
        # Criar widgets
        self._create_widgets()
        
        # Configurar bindings
        self._setup_bindings()
        
        # Configurar protocolo de fechamento
        self.janela.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        return self.janela
        
    def _center_window(self):
        """Centraliza a janela na tela"""
        width, height = UI_CONFIG.get('window_size', (860, 650))
        
        screen_width = self.janela.winfo_screenwidth()
        screen_height = self.janela.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.janela.geometry(f"{width}x{height}+{x}+{y}")
        
    def _setup_styles(self):
        """Configura os estilos da interface"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configurações do Treeview
        style.configure("Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"), 
                       background="#607D8B", 
                       foreground="white")
        style.configure("Treeview", 
                       font=("Segoe UI", 10), 
                       rowheight=26)
        style.map("Treeview", background=[("selected", "#B0BEC5")])
        style.map("Treeview.Heading", 
                 background=[("active", "#455A64")], 
                 foreground=[("active", "white")])
        style.map("Treeview", foreground=[("selected", "black")])
        
        # Outros estilos
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TLabelframe", font=("Segoe UI", 11, "bold"))
        style.configure("TLabelframe.Label", 
                       font=("Segoe UI", 10, "bold"), 
                       foreground="#37474F")
        
    def _setup_variables(self):
        """Configura as variáveis da interface"""
        self.variables = {
            'selecionar_todos': tk.BooleanVar(),
            'situacao': StringVar(value="Em Andamento"),
            'toggle': BooleanVar(value=False),
            'lembretes': BooleanVar(value=False)
        }
        
    def _create_widgets(self):
        """Cria todos os widgets da interface"""
        # Barra superior removida (botão MeuGestor removido)

        # Frame de cadastro
        self._create_form_frame()
        
        # Frame de busca
        self._create_search_frame()
        
        # Frame da tabela
        self._create_table_frame()
        
    def _create_form_frame(self):
        """Cria o frame do formulário de cadastro"""
        frame_cadastro = LabelFrame(self.janela, text="Novo Processo", 
                                   padx=5, pady=3, bg="#ECEFF1", fg="#37474F")
        frame_cadastro.pack(padx=20, pady=10, anchor="center")
        
        # Campos do formulário
        self._create_form_fields(frame_cadastro)
        
        # Botões
        self._create_form_buttons(frame_cadastro)
        
        self.widgets['frame_cadastro'] = frame_cadastro
        
    def _create_form_fields(self, parent):
        """Cria os campos do formulário"""
        # Obter listas para autocomplete
        secretarias_formatadas = self._get_formatted_secretarias()
        modalidades_licitacao = MODALIDADES_LICITACAO
        nomes_autocomplete = self._load_autocomplete_names()
        
        # Configuração das colunas do grid
        parent.grid_columnconfigure(0, weight=0)  # Labels
        parent.grid_columnconfigure(1, weight=0)  # Campos (8cm = 302px)
        parent.grid_columnconfigure(2, weight=0)  # Espaçamento
        parent.grid_columnconfigure(3, weight=0)  # Labels
        parent.grid_columnconfigure(4, weight=0)  # Campos (8cm = 302px)
        parent.grid_columnconfigure(5, weight=0)  # Campos
        parent.grid_columnconfigure(6, weight=1)  # Espaço restante
        
        # Largura fixa de 8cm (302 pixels) para os campos solicitados
        largura_campo_8cm = 302
        
        # Linha 0: Número do contrato | Número da Licitação | Lembretes
        Label(parent, text="Número do contrato:*", bg="#ECEFF1", anchor="e", width=15).grid(row=0, column=0, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_numero_contrato'] = Entry(parent, font=("Segoe UI", 10), width=35)
        self.widgets['entrada_numero_contrato'].grid(row=0, column=1, sticky=W, pady=5)
        self.widgets['entrada_numero_contrato'].bind("<KeyRelease>", self._convert_to_uppercase)
        
        Label(parent, text="Número da Licitação:", bg="#ECEFF1", anchor="e", width=15).grid(row=0, column=3, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_numero_licitacao'] = Entry(parent, font=("Segoe UI", 10), width=35)
        self.widgets['entrada_numero_licitacao'].grid(row=0, column=4, sticky=W, pady=5)
        self.widgets['entrada_numero_licitacao'].bind("<KeyRelease>", self._convert_to_uppercase)
        
        Label(parent, text="Lembretes:", bg="#ECEFF1", anchor="e", width=8).grid(row=0, column=5, sticky=E, padx=(0, 5), pady=5)
        self.widgets['check_lembretes'] = Checkbutton(
            parent, 
            variable=self.variables['lembretes'],
            bg="#ECEFF1", 
            activebackground="#ECEFF1",
            command=self._toggle_reminder
        )
        self.widgets['check_lembretes'].grid(row=0, column=6, sticky=W, pady=5)
        
        # Linha 1: Secretaria | Modalidade
        Label(parent, text="Secretaria:*", bg="#ECEFF1", anchor="e", width=15).grid(row=1, column=0, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_secretaria'] = AutocompleteEntry(parent, secretarias_formatadas, 
                                                              font=("Segoe UI", 10), width=35)
        self.widgets['entrada_secretaria'].grid(row=1, column=1, sticky=W, pady=5)
        
        Label(parent, text="Modalidade:", bg="#ECEFF1", anchor="e", width=15).grid(row=1, column=3, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_modalidade'] = AutocompleteEntry(parent, modalidades_licitacao,
                                                              font=("Segoe UI", 10), width=35)
        self.widgets['entrada_modalidade'].set_listbox_properties(x_offset=-10, y_offset=-25, width=250, max_height=10)
        self.widgets['entrada_modalidade'].grid(row=1, column=4, sticky=W, pady=5)
        
        # Linha 2: Recebimento | Devolução
        Label(parent, text="Recebimento:*", bg="#ECEFF1", anchor="e", width=15).grid(row=2, column=0, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_recebimento'] = Entry(parent, font=("Segoe UI", 10), width=35)
        self.widgets['entrada_recebimento'].grid(row=2, column=1, sticky=W, pady=5)
        self.widgets['entrada_recebimento'].bind("<KeyRelease>", self._format_date_auto)
        self.widgets['entrada_recebimento'].bind("<FocusOut>", 
                                               lambda e: self._check_date_entry(self.widgets['entrada_recebimento']))
        
        Label(parent, text="Devolução:", bg="#ECEFF1", anchor="e", width=15).grid(row=2, column=3, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_devolucao'] = Entry(parent, font=("Segoe UI", 10), width=35)
        self.widgets['entrada_devolucao'].grid(row=2, column=4, sticky=W, pady=5)
        self.widgets['entrada_devolucao'].bind("<KeyRelease>", self._format_date_auto)
        self.widgets['entrada_devolucao'].bind("<FocusOut>", 
                                             lambda e: self._check_date_entry(self.widgets['entrada_devolucao'], 
                                                                             permitir_futuras=False))
        
        # Linha 3: Entregue por | Devolvido a
        Label(parent, text="Entregue por:", bg="#ECEFF1", anchor="e", width=15).grid(row=3, column=0, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_entregue_por'] = AutocompleteEntry(parent, nomes_autocomplete,
                                                               font=("Segoe UI", 10), width=35)
        self.widgets['entrada_entregue_por'].grid(row=3, column=1, sticky=W, pady=5)
        
        Label(parent, text="Devolvido a:", bg="#ECEFF1", anchor="e", width=15).grid(row=3, column=3, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_devolvido_a'] = AutocompleteEntry(parent, nomes_autocomplete,
                                                              font=("Segoe UI", 10), width=35)
        self.widgets['entrada_devolvido_a'].grid(row=3, column=4, sticky=W, pady=5)
        
        # Linha 4: Contratado | Situação
        Label(parent, text="Contratado:", bg="#ECEFF1", anchor="e", width=15).grid(row=4, column=0, sticky=E, padx=(0, 5), pady=5)
        self.widgets['entrada_contratado'] = Entry(parent, font=("Segoe UI", 10), width=35)
        self.widgets['entrada_contratado'].grid(row=4, column=1, sticky=W, pady=5)
        self.widgets['entrada_contratado'].bind("<KeyRelease>", self._convert_to_uppercase)
        
        Label(parent, text="Situação:", bg="#ECEFF1", anchor="e", width=15).grid(row=4, column=3, sticky=E, padx=(0, 5), pady=5)
        frame_situacao = Frame(parent, bg="#ECEFF1")
        frame_situacao.grid(row=4, column=4, sticky=W, pady=5)
        
        Radiobutton(frame_situacao, text="Em Andamento", 
                   variable=self.variables['situacao'], value="Em Andamento", 
                   bg="#ECEFF1", font=("Segoe UI", 10)).pack(side=LEFT)
        Radiobutton(frame_situacao, text="Concluído", 
                   variable=self.variables['situacao'], value="Concluído", 
                   bg="#ECEFF1", font=("Segoe UI", 10)).pack(side=LEFT, padx=5)
        
        # Linha 5: Observações
        Label(parent, text="Observações:", bg="#ECEFF1", anchor="e", width=15).grid(row=5, column=0, sticky=NE, padx=(0, 5), pady=5)
        self.widgets['entrada_descricao'] = Text(parent, height=3, 
                                                font=("Segoe UI", 10), wrap="word", width=35)
        self.widgets['entrada_descricao'].grid(row=5, column=1, columnspan=4, sticky=W, pady=5)
        
    def _create_form_buttons(self, parent):
        """Cria os botões do formulário"""
        # Frame para os botões usando grid para manter consistência
        frame_botoes = Frame(parent, bg="#ECEFF1")
        frame_botoes.grid(row=6, column=0, columnspan=7, pady=10)

        # Frame interno para centralizar o conjunto de botões
        row_frame = Frame(frame_botoes, bg="#ECEFF1")
        row_frame.pack(anchor="center")
        
        # Centralizar o frame dos botões
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(6, weight=1)
        
        # Estilo padrão dos botões
        estilo_botao_padrao = {
            "bg": "#394857",
            "fg": "#66c0f4",
            "activebackground": "#23262e",
            "activeforeground": "#66c0f4",
            "font": ("Segoe UI", 10, "bold"),
            "relief": FLAT,
            "bd": 0,
            "highlightthickness": 1,
            "highlightbackground": "#394857"
        }
        
        # Botões principais
        self.widgets['botao_cadastrar'] = Button(row_frame, text="Cadastrar", 
                                               command=self._register_process, 
                                               width=8, **estilo_botao_padrao)
        self.widgets['botao_cadastrar'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_limpar'] = Button(row_frame, text="Limpar", 
                                            command=self._clear_fields, 
                                            width=6, **estilo_botao_padrao)
        self.widgets['botao_limpar'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_editar'] = Button(row_frame, text="Editar", 
                                            command=self._edit_process, 
                                            width=5, **estilo_botao_padrao)
        self.widgets['botao_editar'].pack(side=LEFT, padx=4)
        
        # Botão excluir (estilo diferente)
        self.widgets['botao_excluir'] = Button(
            row_frame, text="Excluir", command=self._delete_process, width=6,
            bg="#e74c3c", fg="white",
            activebackground="#c0392b", activeforeground="white",
            font=("Segoe UI", 10, "bold"), relief=FLAT, bd=0, 
            highlightthickness=2, highlightbackground="#e74c3c"
        )
        self.widgets['botao_excluir'].pack(side=LEFT, padx=4)
        
        # Botões de exportação
        self.widgets['botao_exportar_pdf'] = Button(row_frame, text="Exportar PDF", 
                                                  command=self._export_pdf, 
                                                  width=11, **estilo_botao_padrao)
        self.widgets['botao_exportar_pdf'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_exportar_excel'] = Button(row_frame, text="Exportar Excel", 
                                                    command=self._export_excel, 
                                                    width=11, **estilo_botao_padrao)
        self.widgets['botao_exportar_excel'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_exportar_banco'] = Button(row_frame, text="Exportar dados", 
                                                    command=self._export_database, 
                                                    width=12, **estilo_botao_padrao)
        self.widgets['botao_exportar_banco'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_importar_banco'] = Button(row_frame, text="Importar dados", 
                                                    command=self._import_database, 
                                                    width=12, **estilo_botao_padrao)
        self.widgets['botao_importar_banco'].pack(side=LEFT, padx=4)
        
        self.widgets['botao_restaurar'] = Button(row_frame, text="Restaurar Excluídos", 
                                               command=self._open_restore_window, 
                                               width=20, **estilo_botao_padrao)
        self.widgets['botao_restaurar'].pack(side=LEFT, padx=4)
        
    def _create_search_frame(self):
        """Cria o frame de busca"""
        container_busca = Frame(self.janela, bg="#ECEFF1")
        container_busca.pack(fill="x", pady=0)
        
        frame_busca = LabelFrame(container_busca, text="Buscar Processos", 
                               padx=4, pady=2, bg="#ECEFF1", fg="#37474F")
        frame_busca.pack(fill="x", expand=True, pady=0)

        # Permite que os campos cresçam com a janela
        frame_busca.grid_columnconfigure(0, weight=2)  # Buscar
        frame_busca.grid_columnconfigure(1, weight=3)  # Secretaria
        frame_busca.grid_columnconfigure(2, weight=1)  # Situação
        frame_busca.grid_columnconfigure(3, weight=3)  # Modalidade
        frame_busca.grid_columnconfigure(4, weight=0)  # Botão Buscar
        frame_busca.grid_columnconfigure(5, weight=0)  # Botão Limpar
        
        # Obter listas para autocomplete
        secretarias_formatadas = self._get_formatted_secretarias()
        modalidades_licitacao = MODALIDADES_LICITACAO
        
        # Labels
        Label(frame_busca, text="Buscar:", bg="#ECEFF1").grid(row=0, column=0, sticky=W, padx=5)
        Label(frame_busca, text="Secretaria:", bg="#ECEFF1").grid(row=0, column=1, sticky=W, padx=5)
        Label(frame_busca, text="Situação:", bg="#ECEFF1").grid(row=0, column=2, sticky=W, padx=5)
        Label(frame_busca, text="Modalidade:", bg="#ECEFF1").grid(row=0, column=3, sticky=W, padx=5)
        
        # Campos de busca
        self.widgets['entrada_busca'] = Entry(frame_busca, width=22, font=("Segoe UI", 10))
        self.widgets['entrada_busca'].grid(row=1, column=0, sticky=E+W, padx=5, pady=2)
        self.widgets['entrada_busca'].bind("<Return>", lambda event: self._search_processes())
        
        self.widgets['entrada_filtro_secretaria'] = AutocompleteEntry(
            frame_busca, secretarias_formatadas, width=33, font=("Segoe UI", 10)
        )
        self.widgets['entrada_filtro_secretaria'].set_listbox_properties(max_height=10)
        self.widgets['entrada_filtro_secretaria'].grid(row=1, column=1, sticky=E+W, padx=5, pady=2)
        
        self.widgets['entrada_filtro_situacao'] = AutocompleteEntry(
            frame_busca, ["Em Andamento", "Concluído"], width=14, font=("Segoe UI", 10)
        )
        self.widgets['entrada_filtro_situacao'].set_listbox_properties(max_height=2)
        self.widgets['entrada_filtro_situacao'].grid(row=1, column=2, sticky=E+W, padx=5, pady=2)
        
        self.widgets['entrada_filtro_modalidade'] = AutocompleteEntry(
            frame_busca, modalidades_licitacao, width=22, font=("Segoe UI", 10)
        )
        self.widgets['entrada_filtro_modalidade'].set_listbox_properties(max_height=10)
        self.widgets['entrada_filtro_modalidade'].grid(row=1, column=3, sticky=E+W, padx=5, pady=2)
        
        # Botões de busca
        estilo_botao_busca = {
            "bg": "#394857",
            "fg": "#66c0f4",
            "activebackground": "#23262e",
            "activeforeground": "#66c0f4",
            "font": ("Segoe UI", 10, "bold"),
            "relief": FLAT,
            "bd": 0,
            "highlightthickness": 1,
            "highlightbackground": "#394857"
        }
        
        self.widgets['botao_buscar'] = Button(frame_busca, text="Buscar", 
                                            command=self._search_processes, 
                                            width=6, **estilo_botao_busca)
        self.widgets['botao_buscar'].grid(row=1, column=4, padx=4, sticky=W)
        
        self.widgets['botao_limpar_filtros'] = Button(frame_busca, text="Limpar", 
                                                    command=self._clear_filters, 
                                                    width=6, **estilo_botao_busca)
        self.widgets['botao_limpar_filtros'].grid(row=1, column=5, padx=(5, 4), sticky=W)
        
        self.widgets['frame_busca'] = frame_busca
        
    def _create_table_frame(self):
        """Cria o frame da tabela"""
        frame_lista = LabelFrame(self.janela, text="Processos Cadastrados", 
                               padx=4, pady=2, bg="#ECEFF1", fg="#37474F")
        frame_lista.pack(fill="both", expand=True, padx=4, pady=(0, 2))
        
        # Frame do topo com seleção e estatísticas
        self._create_table_header(frame_lista)
        
        # Frame da tabela com scrollbars
        frame_tabela = Frame(frame_lista, bg="#ECEFF1")
        frame_tabela.pack(fill="both", expand=True)
        
        # Scrollbars
        scrollbar_y = Scrollbar(frame_tabela)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        
        scrollbar_x = Scrollbar(frame_tabela, orient=HORIZONTAL)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        
        # Tabela
        self.widgets['tabela'] = ttk.Treeview(
            frame_tabela,
            columns=self.colunas,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            style="Treeview"
        )
        
        # Definir colunas visíveis padrão
        colunas_visiveis_padrao = (
            'data_registro', 'numero_processo', 'secretaria',
            'numero_licitacao', 'situacao', 'modalidade',
            'data_inicio', 'data_entrega'
        )
        self.widgets['tabela']['displaycolumns'] = colunas_visiveis_padrao
        
        # Configurar colunas
        for col in self.colunas:
            self.widgets['tabela'].heading(col, text=self.cabecalhos[col], 
                                         command=lambda c=col: self._sort_column(c))
            self.widgets['tabela'].column(col, width=self.larguras_fixas.get(col, 120), 
                                        anchor="center")
        
        self.widgets['tabela'].pack(fill="both", expand=True)
        
        # Configurar tags de cores
        self.widgets['tabela'].tag_configure('concluido', background="#C8E6C9")  # Verde claro
        self.widgets['tabela'].tag_configure('andamento', background="#FFCDD2")  # Vermelho claro
        
        # Configurar scrollbars
        scrollbar_y.config(command=self.widgets['tabela'].yview)
        scrollbar_x.config(command=self.widgets['tabela'].xview)
        
        # Tooltip
        self.tooltip = ToolTip(self.widgets['tabela'])
        
        self.widgets['frame_lista'] = frame_lista
        self.widgets['scrollbar_y'] = scrollbar_y
        self.widgets['scrollbar_x'] = scrollbar_x

    def _open_manual(self):
        """Abre a janela com o manual de uso do MeuGestor."""
        try:
            # Criar janela do manual
            manual_window = Toplevel(self.janela)
            manual_window.title("Manual de Uso - MeuGestor")
            manual_window.geometry("780x560")
            manual_window.transient(self.janela)
            manual_window.attributes("-topmost", True)

            # Estrutura com scrollbar
            frame = Frame(manual_window, bg="#f0f0f0")
            frame.pack(fill="both", expand=True)

            scrollbar = Scrollbar(frame)
            scrollbar.pack(side=RIGHT, fill=Y)

            text = Text(frame, wrap="word", font=("Segoe UI", 10))
            text.pack(fill="both", expand=True)
            text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text.yview)

            # Carrega conteúdo do manual
            import os
            project_root = os.path.dirname(os.path.abspath(__file__))
            candidate_files = [
                os.path.join(project_root, "..", "MANUAL.md"),
                os.path.join(project_root, "..", "README.md")
            ]

            content = None
            for path in candidate_files:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        break
                except Exception:
                    continue

            if not content:
                content = (
                    "Manual não encontrado. Crie um arquivo MANUAL.md na raiz do projeto "
                    "ou utilize o README.md como referência."
                )

            text.insert("1.0", content)
            text.config(state="disabled")

            # Rodapé com botão fechar
            footer = Frame(manual_window, bg="#f0f0f0")
            footer.pack(fill="x")
            Button(
                footer,
                text="Fechar",
                command=manual_window.destroy,
                bg="#e1e1e1",
                fg="black",
                activebackground="#d1d1d1",
                activeforeground="black",
                font=("Segoe UI", 9, "bold"),
                relief="raised",
                bd=1,
                width=10
            ).pack(pady=8)
        except Exception as e:
            try:
                messagebox.showerror("Erro", f"Não foi possível abrir o manual: {e}")
            except Exception:
                pass
        
    def _create_table_header(self, parent):
        """Cria o cabeçalho da tabela com seleção e estatísticas"""
        frame_topo_lista = Frame(parent, bg="#ECEFF1")
        frame_topo_lista.pack(fill="x", padx=0, pady=(0, 5))
        
        # Checkbox de seleção
        self.widgets['toggle_btn'] = Checkbutton(
            frame_topo_lista,
            variable=self.variables['toggle'],
            command=self._toggle_select_all,
            indicatoron=True,
            width=2,
            bg="#ECEFF1",
            selectcolor="#95CCC9",
            activebackground="#ECEFF1",
            bd=0,
            highlightthickness=0
        )
        self.widgets['toggle_btn'].pack(side=LEFT, padx=0)
        
        # Label "Selecionar Todos"
        Label(frame_topo_lista, text="Selecionar Todos", 
              font=("Segoe UI", 8), bg="#ECEFF1", fg="#706E6E").pack(side=LEFT, padx=(0, 20))
        
        # Labels de estatísticas
        self.widgets['label_concluidos'] = Label(frame_topo_lista, text="Concluídos: 0", 
                                               font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_concluidos'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_andamento'] = Label(frame_topo_lista, text="Em Andamento: 0", 
                                              font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_andamento'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_editados'] = Label(frame_topo_lista, text="Editados: 0", 
                                             font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_editados'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_apagados'] = Label(frame_topo_lista, text="Apagados: 0", 
                                             font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_apagados'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_exportados'] = Label(frame_topo_lista, text="Exportações: 0", 
                                               font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_exportados'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_importados'] = Label(frame_topo_lista, text="Importações: 0", 
                                               font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_importados'].pack(side=LEFT, padx=(0, 15))
        
        self.widgets['label_restaurados'] = Label(frame_topo_lista, text="Restaurados: 0", 
                                                font=("Segoe UI", 8), bg="#ECEFF1", fg="#37474F")
        self.widgets['label_restaurados'].pack(side=LEFT, padx=(0, 0))
        
    def _setup_bindings(self):
        """Configura os bindings de eventos"""
        # Bindings da janela principal
        self.janela.bind('<Return>', self._handle_global_enter)
        self.janela.bind('<Configure>', self._on_window_configure)
        self.janela.bind('<Escape>', self._handle_global_escape)
        
        # Bindings da tabela
        self.widgets['tabela'].bind('<Motion>', self._show_tooltip_description)
        self.widgets['tabela'].bind('<Leave>', self._on_leave)
        self.widgets['tabela'].bind("<Double-1>", lambda e: self._view_process())

        # Garantir seleção estendida e habilitar Shift+Seta para seleção de faixas
        self.widgets['tabela'].configure(selectmode='extended')

        def _set_anchor_on_click(event):
            try:
                region = self.widgets['tabela'].identify_region(event.x, event.y)
                if region not in ("cell", "tree"):
                    return
                row = self.widgets['tabela'].identify_row(event.y)
                if row:
                    self.widgets['tabela'].focus(row)
                    setattr(self.widgets['tabela'], 'anchor_item', row)
            except Exception:
                pass

        def _shift_select(direction):
            try:
                tv = self.widgets['tabela']
                items = tv.get_children("")
                if not items:
                    return "break"

                cur = tv.focus()
                if not cur:
                    sel = tv.selection()
                    cur = sel[0] if sel else items[0]

                idx = items.index(cur)
                new_idx = max(0, idx - 1) if direction == 'up' else min(len(items) - 1, idx + 1)
                new_item = items[new_idx]

                anchor = getattr(tv, 'anchor_item', None)
                if anchor is None:
                    anchor = cur
                    setattr(tv, 'anchor_item', anchor)

                a_idx = items.index(anchor)
                start = min(a_idx, new_idx)
                end = max(a_idx, new_idx)

                tv.selection_set(items[start:end + 1])
                tv.focus(new_item)
                tv.see(new_item)
                return "break"
            except Exception:
                return "break"

        self.widgets['tabela'].bind('<Button-1>', _set_anchor_on_click, add='+')
        self.widgets['tabela'].bind('<Shift-Up>', lambda e: _shift_select('up'))
        self.widgets['tabela'].bind('<Shift-Down>', lambda e: _shift_select('down'))
        
        # Bindings dos campos para edição
        form_widgets = [
            'entrada_numero', 'entrada_secretaria', 'entrada_licitacao', 'entrada_modalidade',
            'entrada_recebimento', 'entrada_devolucao', 'entrada_entregue_por', 'entrada_devolvido_a',
            'entrada_contratado', 'entrada_descricao'
        ]
        
        for widget_name in form_widgets:
            if widget_name in self.widgets:
                self.widgets[widget_name].bind("<Double-1>", self._activate_field_editing)
        
        # Bindings especiais para campos de texto
        self._setup_text_field_bindings()
        
        # Bindings de escape para filtros
        filter_widgets = ['entrada_busca', 'entrada_filtro_secretaria', 
                         'entrada_filtro_situacao', 'entrada_filtro_modalidade']
        
        for widget_name in filter_widgets:
            if widget_name in self.widgets:
                self.widgets[widget_name].bind("<Escape>", lambda event: self._clear_filters())
        
    def _setup_text_field_bindings(self):
        """Configura bindings especiais para campos de texto"""
        # Tab e Shift+Tab para campo de observações
        def exit_text_tab(event):
            event.widget.tk_focusNext().focus()
            return "break"
            
        def exit_text_shift_tab(event):
            event.widget.tk_focusPrev().focus()
            return "break"
            
        # Bindings de Tab removidos para permitir TabOrderManager funcionar
        # if 'entrada_descricao' in self.widgets:
        #     self.widgets['entrada_descricao'].bind("<Tab>", exit_text_tab)
        #     self.widgets['entrada_descricao'].bind("<Shift-Tab>", exit_text_shift_tab)
        
        # Enter como Tab para campos de entrada (exceto busca)
        def enter_as_tab(event):
            event.widget.tk_focusNext().focus()
            return "break"
            
        text_fields = [
            'entrada_numero', 'entrada_licitacao', 'entrada_secretaria', 'entrada_modalidade',
            'entrada_recebimento', 'entrada_devolucao', 'entrada_entregue_por', 'entrada_devolvido_a'
        ]
        
        for field_name in text_fields:
            if field_name in self.widgets:
                self.widgets[field_name].bind("<Return>", enter_as_tab)
        
    # === MÉTODOS DE CALLBACK ===
    
    def _register_process(self):
        """Registra um novo processo"""
        try:
            # Coletar dados do formulário
            data = self._collect_form_data()
            
            # Validar dados
            if not self._validate_form_data(data):
                return
                
            # Registrar através do controlador
            if self.controllers['process'].create_process(data):
                self._clear_fields()
                self._refresh_table()
                self._update_statistics()
                messagebox.showinfo("Sucesso", "Processo cadastrado com sucesso!")
            else:
                messagebox.showerror("Erro", "Erro ao cadastrar processo")
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao registrar processo")
            messagebox.showerror("Erro", f"Erro ao registrar processo: {e}")
            
    def _edit_process(self):
        """Edita o processo selecionado"""
        try:
            selection = self.widgets['tabela'].selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione um processo para editar")
                return
                
            # Obter dados do processo selecionado
            item = self.widgets['tabela'].item(selection[0])
            values = item.get('values', [])
            process_data = {col: (values[idx] if idx < len(values) else '') for idx, col in enumerate(self.colunas)}
            
            # Preencher formulário com dados do processo
            self._populate_form(process_data)
            
            # Alterar botão para modo de atualização
            self.widgets['botao_cadastrar'].config(text="Atualizar", 
                                                 command=self._update_process)
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao editar processo")
            messagebox.showerror("Erro", f"Erro ao editar processo: {e}")
            
    def _update_process(self):
        """Atualiza o processo em edição"""
        try:
            # Coletar dados do formulário
            data = self._collect_form_data()
            
            # Validar dados
            if not self._validate_form_data(data):
                return
                
            # Obter ID do processo selecionado
            selection = self.widgets['tabela'].selection()
            if not selection:
                messagebox.showwarning("Aviso", "Nenhum processo selecionado")
                return
                
            item = self.widgets['tabela'].item(selection[0])
            process_id = item['values'][0]  # Assumindo que o ID está na primeira coluna
            
            # Atualizar através do controlador
            if self.controllers['process'].atualizar_processo(process_id, data):
                self._clear_fields()
                self._refresh_table()
                self._update_statistics()
                
                # Restaurar botão para modo de cadastro
                self.widgets['botao_cadastrar'].config(text="Cadastrar", 
                                                     command=self._register_process)
                
                messagebox.showinfo("Sucesso", "Processo atualizado com sucesso!")
            else:
                messagebox.showerror("Erro", "Erro ao atualizar processo")
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao atualizar processo")
            messagebox.showerror("Erro", f"Erro ao atualizar processo: {e}")
            
    def _delete_process(self):
        """Exclui o processo selecionado"""
        try:
            selection = self.widgets['tabela'].selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione um processo para excluir")
                return
                
            # Confirmar exclusão
            if not messagebox.askyesno("Confirmar", "Deseja realmente excluir o processo selecionado?"):
                return
                
            # Obter ID do processo
            item = self.widgets['tabela'].item(selection[0])
            process_id = item['values'][0]  # Assumindo que o ID está na primeira coluna
            
            # Excluir através do controlador
            if self.controllers['process'].delete_process(process_id):
                self._refresh_table()
                self._update_statistics()
                messagebox.showinfo("Sucesso", "Processo excluído com sucesso!")
            else:
                messagebox.showerror("Erro", "Erro ao excluir processo")
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao excluir processo")
            messagebox.showerror("Erro", f"Erro ao excluir processo: {e}")
            
    def _search_processes(self):
        """Busca processos com base nos filtros"""
        try:
            # Coletar critérios de busca
            criteria = {
                'search_text': self.widgets['entrada_busca'].get().strip(),
                'secretaria': self.widgets['entrada_filtro_secretaria'].get().strip(),
                'situacao': self.widgets['entrada_filtro_situacao'].get().strip(),
                'modalidade': self.widgets['entrada_filtro_modalidade'].get().strip()
            }
            
            # Buscar através do controlador
            results = self.controllers['process'].search_processes(criteria)
            
            # Atualizar tabela com resultados
            self._populate_table(results)
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao buscar processos")
            messagebox.showerror("Erro", f"Erro ao buscar processos: {e}")
            
    def _clear_fields(self):
        """Limpa todos os campos do formulário"""
        try:
            # Limpar campos de entrada
            text_fields = [
                'entrada_numero', 'entrada_licitacao', 'entrada_secretaria', 'entrada_modalidade',
                'entrada_recebimento', 'entrada_devolucao', 'entrada_entregue_por', 'entrada_devolvido_a',
                'entrada_contratado'
            ]
            
            for field_name in text_fields:
                if field_name in self.widgets:
                    self.widgets[field_name].delete(0, tk.END)
            
            # Limpar campo de observações
            if 'entrada_descricao' in self.widgets:
                self.widgets['entrada_descricao'].delete("1.0", tk.END)
            
            # Resetar situação
            self.variables['situacao'].set("Em Andamento")
            
            # Resetar lembrete
            self.variables['lembrete'].set(False)
            
            # Restaurar botão para modo de cadastro
            self.widgets['botao_cadastrar'].config(text="Cadastrar", 
                                                 command=self._register_process,
                                                 state='normal')
            
            # Remover seleção da tabela
            if self.widgets['tabela'].selection():
                self.widgets['tabela'].selection_remove(self.widgets['tabela'].selection())
            
            # Restaurar cores padrão
            self.widgets['entrada_recebimento'].config(bg="white")
            self.widgets['entrada_devolucao'].config(bg="white")
            
            # Atualizar lista
            self._refresh_table()
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao limpar campos")
            
    def _clear_filters(self):
        """Limpa os filtros de busca"""
        try:
            filter_fields = [
                'entrada_busca', 'entrada_filtro_secretaria', 
                'entrada_filtro_situacao', 'entrada_filtro_modalidade'
            ]
            
            for field_name in filter_fields:
                if field_name in self.widgets:
                    self.widgets[field_name].delete(0, tk.END)
            
            # Atualizar tabela
            self._refresh_table()
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao limpar filtros")
            
    def _view_process(self):
        """Visualiza detalhes do processo selecionado"""
        try:
            selection = self.widgets['tabela'].selection()
            if not selection:
                return
                
            item = self.widgets['tabela'].item(selection[0])
            process_data = item['values']
            
            # Criar janela de visualização
            self._create_view_window(process_data)
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao visualizar processo")
            
    def _export_pdf(self):
        """Exporta processos para PDF"""
        try:
            selected_items = self.widgets['tabela'].selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Selecione pelo menos um processo para exportar")
                return
                
            # Exportar através do controlador
            if self.controllers['export'].export_pdf(selected_items):
                self.stats['registros_exportados'] += 1
                self._update_statistics()
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao exportar PDF")
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {e}")
            
    def _export_excel(self):
        """Exporta processos para Excel"""
        try:
            selected_items = self.widgets['tabela'].selection()
            if not selected_items:
                messagebox.showwarning("Aviso", "Selecione pelo menos um processo para exportar")
                return
                
            # Exportar através do controlador
            if self.controllers['export'].export_excel(selected_items):
                self.stats['registros_exportados'] += 1
                self._update_statistics()
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao exportar Excel")
            messagebox.showerror("Erro", f"Erro ao exportar Excel: {e}")
            
    def _export_database(self):
        """Exporta banco de dados"""
        try:
            if self.controllers['export'].export_database():
                self.stats['registros_exportados'] += 1
                self._update_statistics()
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao exportar banco")
            messagebox.showerror("Erro", f"Erro ao exportar banco: {e}")
            
    def _import_database(self):
        """Importa banco de dados"""
        try:
            if self.controllers['backup'].import_database():
                self.stats['registros_importados'] += 1
                self._update_statistics()
                self._refresh_table()
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao importar banco")
            messagebox.showerror("Erro", f"Erro ao importar banco: {e}")
            
    def _open_restore_window(self):
        """Abre janela de restauração de processos excluídos"""
        try:
            # Variáveis para controle da janela
            if hasattr(self, 'janela_restaurar_aberta') and self.janela_restaurar_aberta and self.janela_restaurar_aberta.winfo_exists():
                self.janela_restaurar_aberta.destroy()
            
            self.backup_ids = {}
            
            # Criar janela
            janela_restaurar = Toplevel(self.janela)
            self.janela_restaurar_aberta = janela_restaurar
            janela_restaurar.title("🔄 Restaurar Registros")
            # Reduzir largura em ~20% para ajustar mais ao meio
            janela_restaurar.geometry("320x400")
            janela_restaurar.minsize(333, 300)
            janela_restaurar.configure(bg="#f0f0f0")
            janela_restaurar.resizable(True, True)
            janela_restaurar.attributes("-topmost", True)  # Manter sempre em primeiro plano
            # Garantir ordenação acima da janela principal e foco imediato
            try:
                janela_restaurar.transient(self.janela)
                janela_restaurar.lift()
                janela_restaurar.focus_force()
            except Exception:
                pass
            
            # Funções para fechar
            def ao_fechar_restaurar_escape():
                # Fechar janela de detalhes também ao pressionar ESC
                try:
                    if hasattr(self, 'janela_detalhes_aberta') and self.janela_detalhes_aberta and self.janela_detalhes_aberta.winfo_exists():
                        self.janela_detalhes_aberta.destroy()
                except Exception:
                    pass
                try:
                    self.lista_restaurar = None
                except Exception:
                    pass
                self.janela_restaurar_aberta = None
                janela_restaurar.destroy()

            def ao_fechar_restaurar_x():
                # Fechar apenas a janela de restauração; manter detalhes abertos
                try:
                    self.lista_restaurar = None
                except Exception:
                    pass
                self.janela_restaurar_aberta = None
                janela_restaurar.destroy()

            # Bindings
            janela_restaurar.bind("<Escape>", lambda e: ao_fechar_restaurar_escape())
            janela_restaurar.protocol("WM_DELETE_WINDOW", ao_fechar_restaurar_x)
            
            # Layout
            frame_principal = Frame(janela_restaurar, bg="#f0f0f0")
            frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
            
            frame_lista = Frame(frame_principal, bg="#f0f0f0")
            frame_lista.pack(fill="both", expand=True)
            
            frame_botoes = Frame(janela_restaurar, bg="#f0f0f0", height=50)
            frame_botoes.pack(side="bottom", fill="x", padx=10, pady=10)
            frame_botoes.pack_propagate(False)
            
            frame_botoes_centro = Frame(frame_botoes, bg="#f0f0f0")
            frame_botoes_centro.pack(expand=True)
            
            # Scrollbar e lista
            scrollbar = Scrollbar(frame_lista)
            scrollbar.pack(side="right", fill="y")
            
            lista = Listbox(
                frame_lista,
                yscrollcommand=scrollbar.set,
                selectmode="extended",
                width=56,
                height=15,
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="black",
                selectbackground="#0078d4",
                selectforeground="white"
            )
            lista.pack(fill="both", expand=True)
            scrollbar.config(command=lista.yview)
            # Guardar referência para foco posterior
            try:
                self.lista_restaurar = lista
            except Exception:
                pass
            
            # Menu de contexto
            menu_contexto = tk.Menu(janela_restaurar, tearoff=0)
            menu_contexto.add_command(
                label="↑ Restaurar",
                command=lambda: restaurar_selecionados()
            )
            menu_contexto.add_command(
                label="🔍 Visualizar",
                command=lambda: self._visualizar_registro_excluido(lista)
            )
            menu_contexto.add_separator()
            menu_contexto.add_command(
                label="✓ Selecionar Todos",
                command=lambda: toggle_selecao()
            )
            
            # Função para atualizar cores dos itens selecionados
            def atualizar_cores_selecao():
                """Atualiza as cores dos itens para destacar seleção"""
                for i in range(lista.size()):
                    if i in lista.curselection():
                        # Item selecionado - cor destacada
                        lista.itemconfig(i, bg="#e3f2fd", fg="#1565c0")
                    else:
                        # Item não selecionado - cores alternadas normais
                        if i % 2 == 1:
                            lista.itemconfig(i, bg="#f0f0f0", fg="black")
                        else:
                            lista.itemconfig(i, bg="#ffffff", fg="black")

            # Função para mostrar menu de contexto
            def mostrar_menu_contexto(event):
                try:
                    # Seleciona o item clicado se não estiver selecionado
                    index = lista.nearest(event.y)
                    if index >= 0 and index not in lista.curselection():
                        lista.selection_clear(0, "end")
                        lista.selection_set(index)
                        lista.activate(index)
                        atualizar_cores_selecao()
                    
                    menu_contexto.tk_popup(event.x_root, event.y_root)
                finally:
                    menu_contexto.grab_release()
            
            # Função para duplo clique
            def on_double_click(event):
                # Seleciona o item clicado se não estiver selecionado
                index = lista.nearest(event.y)
                if index >= 0:
                    lista.selection_clear(0, "end")
                    lista.selection_set(index)
                    lista.activate(index)
                    atualizar_cores_selecao()
                    
                # Mostra o menu de contexto na posição do clique
                try:
                    menu_contexto.tk_popup(event.x_root, event.y_root)
                finally:
                    menu_contexto.grab_release()
            
            # Função para quando a seleção mudar
            def on_selection_change(event):
                atualizar_cores_selecao()
            
            # Bindings para clique direito, duplo clique e mudança de seleção
            lista.bind("<Button-3>", mostrar_menu_contexto)  # Clique direito
            lista.bind("<Double-Button-1>", on_double_click)  # Duplo clique esquerdo
            lista.bind("<<ListboxSelect>>", on_selection_change)  # Mudança de seleção

            # Seleção múltipla com teclado (Shift+Seta e Ctrl+Espaço)
            def _set_anchor_on_click(event):
                try:
                    idx = lista.nearest(event.y)
                    lista.selection_anchor(idx)
                except Exception:
                    pass

            def _shift_select(direction):
                try:
                    current = lista.index("active")
                    size = lista.size()
                    if size <= 0:
                        return None
                    new_index = max(0, current - 1) if direction == -1 else min(size - 1, current + 1)
                    anchor = lista.index("anchor")
                    start = min(anchor, new_index)
                    end = max(anchor, new_index)
                    lista.selection_clear(0, "end")
                    lista.selection_set(start, end)
                    lista.activate(new_index)
                    lista.see(new_index)
                    return 'break'
                except Exception:
                    return None

            def _on_shift_up(event):
                return _shift_select(-1)

            def _on_shift_down(event):
                return _shift_select(1)

            def _ctrl_toggle_active(event):
                try:
                    idx = lista.index("active")
                    if idx in lista.curselection():
                        lista.selection_clear(idx)
                    else:
                        lista.selection_set(idx)
                    return 'break'
                except Exception:
                    return None

            lista.configure(exportselection=False)
            lista.bind("<Button-1>", _set_anchor_on_click)
            lista.bind("<Shift-Up>", _on_shift_up)
            lista.bind("<Shift-Down>", _on_shift_down)
            lista.bind("<Control-space>", _ctrl_toggle_active)
            
            # Carregar dados
            from models.database_model import DatabaseModel
            db = DatabaseModel()
            
            registros = db.execute_query("""
                SELECT id, numero_processo, secretaria, data_exclusao
                FROM trabalhos_excluidos
                ORDER BY data_exclusao DESC
            """)
            
            self.backup_ids = {idx: row[0] for idx, row in enumerate(registros)}
            
            for idx, (id_proc, proc, sec, data_exc) in enumerate(registros):
                lista.insert("end", f"{idx+1}. {proc} | {sec} | Excluído em: {data_exc}")
                if idx % 2 == 1:
                    lista.itemconfig(idx, bg="#f0f0f0")
                else:
                    lista.itemconfig(idx, bg="#ffffff")

            # Ajuste dinâmico de largura para caber o conteúdo e manter botões visíveis
            try:
                janela_restaurar.update_idletasks()
                itens = [lista.get(i) for i in range(lista.size())]
                import tkinter.font as tkfont
                fonte_lista = tkfont.Font(font=("Segoe UI", 9))
                largura_max_itens = max((fonte_lista.measure(t) for t in itens), default=0)
                largura_scroll = scrollbar.winfo_reqwidth() if scrollbar.winfo_ismapped() else 16
                padding_px = 40
                largura_conteudo = largura_max_itens + largura_scroll + padding_px

                largura_botoes = frame_botoes_centro.winfo_reqwidth() + padding_px
                largura_minima = max(largura_botoes, 333)

                largura_tela = janela_restaurar.winfo_screenwidth() - 40
                largura_final = max(largura_conteudo, largura_minima)
                largura_final = min(largura_final, largura_tela)

                altura_atual = max(janela_restaurar.winfo_height(), 300)
                janela_restaurar.geometry(f"{int(largura_final)}x{int(altura_atual)}")
                janela_restaurar.minsize(int(largura_minima), 300)
            except Exception:
                pass
            
            # Funções dos botões
            def restaurar_selecionados():
                indices = lista.curselection()
                if not indices:
                    messagebox.showwarning("Aviso", "Selecione pelo menos um registro para restaurar.", parent=janela_restaurar)
                    return
                
                if len(indices) > 1:
                    if not messagebox.askyesno("Confirmar", f"Deseja restaurar {len(indices)} registros selecionados?", parent=janela_restaurar):
                        return
                
                count = 0
                for idx in sorted(indices, reverse=True):
                    id_registro = self.backup_ids[idx]
                    try:
                        self._restaurar_registro_por_id(id_registro)
                        count += 1
                        lista.delete(idx)
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao restaurar registro: {str(e)}", parent=janela_restaurar)
                        break
                
                # Atualiza as cores após deletar itens
                atualizar_cores_selecao()
                
                if count > 0:
                    messagebox.showinfo("Sucesso", f"{count} registro(s) restaurado(s) com sucesso!", parent=janela_restaurar)
                    self._refresh_table()
                    self._update_statistics()
                
                if lista.size() == 0:
                    janela_restaurar.destroy()
            
            def toggle_selecao():
                total_items = lista.size()
                selecionados = len(lista.curselection())
                
                if selecionados == total_items:
                    lista.selection_clear(0, "end")
                else:
                    lista.selection_set(0, "end")
                
                # Atualiza as cores após mudar a seleção
                atualizar_cores_selecao()
            
            # Estilo dos botões
            estilo_botao = {
                "bg": "#e1e1e1",
                "fg": "black",
                "activebackground": "#d1d1d1",
                "activeforeground": "black",
                "font": ("Segoe UI", 9, "bold"),
                "relief": "raised",
                "bd": 1,
                "width": 12,
                "height": 1
            }
            
            # Botões
            Button(
                frame_botoes_centro,
                text="↑ Restaurar",
                command=restaurar_selecionados,
                **estilo_botao
            ).pack(side="left", padx=(0, 10))
            
            Button(
                frame_botoes_centro,
                text="🔍 Visualizar",
                command=lambda: self._visualizar_registro_excluido(lista),
                **estilo_botao
            ).pack(side="left", padx=(0, 10))
            
            Button(
                frame_botoes_centro,
                text="✓ Selecionar",
                command=toggle_selecao,
                **estilo_botao
            ).pack(side="left")

            # Botão Fechar
            Button(
                frame_botoes_centro,
                text="Fechar",
                command=ao_fechar_restaurar_x,
                **estilo_botao
            ).pack(side="left", padx=(10, 0))
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao abrir janela de restauração")
    
    def _visualizar_registro_excluido(self, lista):
        """Visualiza detalhes completos de um registro excluído"""
        try:
            indices = lista.curselection()
            # Se não houver seleção e existir apenas um registro, visualiza o único
            if not indices:
                if lista.size() == 1:
                    indices = (0,)
                else:
                    messagebox.showwarning("Aviso", "Selecione um registro para visualizar.", parent=self.janela_restaurar_aberta)
                    return
            
            if len(indices) > 1:
                messagebox.showwarning("Aviso", "Selecione apenas um registro para visualizar.", parent=self.janela_restaurar_aberta)
                return
            
            idx = indices[0]
            id_registro = self.backup_ids[idx]
            
            # Fechar janela anterior se existir
            if hasattr(self, 'janela_detalhes_aberta') and self.janela_detalhes_aberta and self.janela_detalhes_aberta.winfo_exists():
                self.janela_detalhes_aberta.destroy()

            # Fechar a janela de restauração ao abrir a janela de detalhes
            if hasattr(self, 'janela_restaurar_aberta') and self.janela_restaurar_aberta and self.janela_restaurar_aberta.winfo_exists():
                try:
                    self.janela_restaurar_aberta.destroy()
                except Exception:
                    pass
                self.janela_restaurar_aberta = None
            
            # Buscar dados completos
            from models.database_model import DatabaseModel
            db = DatabaseModel()
            
            registro = db.execute_query("""
                SELECT 
                    data_registro,
                    numero_processo,
                    secretaria,
                    numero_licitacao,
                    modalidade,
                    situacao,
                    data_inicio,
                    data_entrega,
                    entregue_por,
                    devolvido_a,
                    contratado,
                    data_exclusao
                FROM trabalhos_excluidos 
                WHERE id = ?
            """, (id_registro,))
            
            if not registro:
                messagebox.showerror("Erro", "Registro não encontrado.", parent=self.janela_restaurar_aberta)
                return
            
            dados = registro[0]
            
            # Criar janela de detalhes
            janela_detalhes = Toplevel(self.janela)
            self.janela_detalhes_aberta = janela_detalhes
            janela_detalhes.title(f"📋 Detalhes - {dados[1]}")
            janela_detalhes.configure(bg="#f0f0f0")
            janela_detalhes.resizable(False, False)
            # Tornar a janela de detalhes modal em relação à janela principal
            janela_detalhes.transient(self.janela)
            janela_detalhes.grab_set()
            janela_detalhes.attributes("-topmost", True)  # Manter sempre em primeiro plano
            
            # Função para fechar
            def fechar_detalhes():
                self.janela_detalhes_aberta = None
                try:
                    janela_detalhes.grab_release()  # Liberar o grab antes de fechar
                except Exception:
                    pass
                janela_detalhes.destroy()
            
            # Bindings
            janela_detalhes.bind("<Escape>", lambda e: fechar_detalhes())
            janela_detalhes.protocol("WM_DELETE_WINDOW", fechar_detalhes)
            
            # Frame principal
            frame_principal = Frame(janela_detalhes, bg="#f0f0f0", padx=20, pady=20)
            frame_principal.pack(fill="both", expand=True)
            
            # Formatação de datas para padrão brasileiro
            def _fmt_data(valor):
                try:
                    return DateUtils.formatar_data_hora(valor) if valor else "N/A"
                except Exception:
                    return valor or "N/A"

            # Campos na ordem solicitada
            campos = [
                ("Data de registro:", _fmt_data(dados[0])),
                ("Número do processo:", dados[1] or "N/A"),
                ("Secretaria:", dados[2] or "N/A"),
                ("Número da licitação:", dados[3] or "N/A"),
                ("Modalidade:", dados[4] or "N/A"),
                ("Situação:", dados[5] or "N/A"),
                ("Data de recebimento:", _fmt_data(dados[6])),
                ("Entregue por:", dados[8] or "N/A"),
                ("Data de devolução:", _fmt_data(dados[7])),
                ("Devolvido a:", dados[9] or "N/A"),
                ("Contratado:", dados[10] or "N/A"),
                ("Data de exclusão:", _fmt_data(dados[11]))
            ]
            
            for i, (label, valor) in enumerate(campos):
                Label(
                    frame_principal,
                    text=label,
                    font=("Segoe UI", 9, "bold"),
                    bg="#f0f0f0",
                    fg="#333333",
                    anchor="w"
                ).grid(row=i, column=0, sticky="w", pady=2)
                
                Label(
                    frame_principal,
                    text=str(valor),
                    font=("Segoe UI", 9),
                    bg="#f0f0f0",
                    fg="black",
                    anchor="w",
                    wraplength=300
                ).grid(row=i, column=1, sticky="w", padx=(10, 0), pady=2)

            # Ações: Restaurar, Excluir definitivamente e Reabrir janela Restaurar
            def restaurar_e_fechar():
                try:
                    self._restaurar_registro_por_id(id_registro)
                    messagebox.showinfo("Restaurado", "Registro restaurado com sucesso.", parent=janela_detalhes)
                    # Atualiza tabela principal
                    try:
                        self._refresh_table()
                    except Exception:
                        pass
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao restaurar: {str(e)}", parent=janela_detalhes)
                finally:
                    fechar_detalhes()

            def excluir_e_fechar():
                try:
                    if messagebox.askyesno("Confirmar Exclusão", "Excluir definitivamente este registro?", parent=janela_detalhes):
                        self._excluir_registro_excluido_por_id(id_registro)
                        messagebox.showinfo("Excluído", "Registro excluído definitivamente.", parent=janela_detalhes)
                        try:
                            self._refresh_table()
                        except Exception:
                            pass
                        fechar_detalhes()
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao excluir: {str(e)}", parent=janela_detalhes)

            def reabrir_restaurar():
                try:
                    self._open_restore_window()
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao reabrir janela Restaurar: {str(e)}", parent=janela_detalhes)
                finally:
                    fechar_detalhes()

            frame_botoes = Frame(janela_detalhes, bg="#f0f0f0", padx=20, pady=10)
            frame_botoes.pack(fill="x")
            Button(frame_botoes, text="Restaurar Registro", command=restaurar_e_fechar,
                   font=("Segoe UI", 9, "bold"), bg="#d4f7d4").pack(side="left", padx=5)
            Button(frame_botoes, text="Excluir Registro", command=excluir_e_fechar,
                   font=("Segoe UI", 9, "bold"), bg="#f7d4d4").pack(side="left", padx=5)
            Button(frame_botoes, text="Reabrir Restaurar", command=reabrir_restaurar,
                   font=("Segoe UI", 9, "bold"), bg="#d4e6f7").pack(side="right", padx=5)
            
            # Ajuste de tamanho da janela
            janela_detalhes.geometry("500x360")
            
            # Centralizar janela
            janela_detalhes.update_idletasks()
            x = (janela_detalhes.winfo_screenwidth() // 2) - (janela_detalhes.winfo_width() // 2)
            y = (janela_detalhes.winfo_screenheight() // 2) - (janela_detalhes.winfo_height() // 2)
            janela_detalhes.geometry(f"+{x}+{y}")
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao visualizar registro excluído")
            messagebox.showerror("Erro", f"Erro ao visualizar registro: {str(e)}", parent=self.janela_restaurar_aberta)
    
    def _restaurar_registro_por_id(self, id_registro):
        """Restaura um registro excluído pelo ID"""
        try:
            from models.database_model import DatabaseModel
            db = DatabaseModel()
            
            # Buscar dados do registro excluído
            registro = db.execute_query("""
                SELECT numero_processo, secretaria, situacao, modalidade, 
                       objeto, valor, data_inicio, data_fim, observacoes
                FROM trabalhos_excluidos 
                WHERE id = ?
            """, (id_registro,))
            
            if not registro:
                raise Exception("Registro não encontrado")
            
            dados = registro[0]
            
            # Inserir de volta na tabela principal
            db.execute_query("""
                INSERT INTO trabalhos (numero_processo, secretaria, situacao, modalidade, 
                                     objeto, valor, data_inicio, data_fim, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dados)
            
            # Remover da tabela de excluídos
            db.execute_query("DELETE FROM trabalhos_excluidos WHERE id = ?", (id_registro,))
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao restaurar registro")
            raise e
            
    def _excluir_registro_excluido_por_id(self, id_registro):
        """Exclui definitivamente um registro da tabela de trabalhos_excluidos"""
        try:
            from models.database_model import DatabaseModel
            db = DatabaseModel()
            db.execute_query("DELETE FROM trabalhos_excluidos WHERE id = ?", (id_registro,))
        except Exception as e:
            log_error(ui_logger, e, "Erro ao excluir registro definitivamente")
            raise e
            
    def _open_reminders(self):
        """Abre janela de lembretes"""
        try:
            # Implementar janela de lembretes
            pass
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao abrir lembretes")
            
    def _toggle_reminder(self):
        """Alterna estado do lembrete"""
        try:
            # Implementar lógica de lembrete
            pass
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao alternar lembrete")
            
    def _toggle_select_all(self):
        """Alterna seleção de todos os itens"""
        try:
            if self.variables['toggle'].get():
                self.widgets['tabela'].selection_set(self.widgets['tabela'].get_children())
            else:
                self.widgets['tabela'].selection_remove(self.widgets['tabela'].get_children())
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao alternar seleção")
            
    def _sort_column(self, col):
        """Ordena coluna da tabela"""
        try:
            # Implementar ordenação
            reverse = self.ordem_colunas_reversa.get(col, False)
            
            # Obter dados da tabela
            data = [(self.widgets['tabela'].set(child, col), child) 
                   for child in self.widgets['tabela'].get_children('')]
            
            # Ordenar dados
            data.sort(reverse=reverse)
            
            # Reorganizar itens na tabela
            for index, (val, child) in enumerate(data):
                self.widgets['tabela'].move(child, '', index)
            
            # Alternar ordem para próxima vez
            self.ordem_colunas_reversa[col] = not reverse
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao ordenar coluna")
            
    # === MÉTODOS DE EVENTO ===
    
    def _handle_global_enter(self, event):
        """Manipula Enter global"""
        try:
            widget_com_foco = self.janela.focus_get()
            if widget_com_foco and hasattr(widget_com_foco, 'invoke'):
                if widget_com_foco.winfo_class() in ['Button', 'Checkbutton', 'Radiobutton']:
                    widget_com_foco.invoke()
                    return "break"
        except Exception as e:
            log_error(ui_logger, e, "Erro em handle_global_enter")
        return None
        
    def _handle_global_escape(self, event):
        """Manipula Escape global - executa as funções dos dois botões Limpar"""
        try:
            self._clear_fields()
            self._clear_filters()
            return "break"
        except Exception as e:
            log_error(ui_logger, e, "Erro em handle_global_escape")
        return None
        
    def _on_window_configure(self, event):
        """Manipula redimensionamento da janela"""
        try:
            if event.widget == self.janela:
                # Ajustar colunas da tabela conforme tamanho da janela
                self._adjust_table_columns()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao configurar janela")
            
    def _show_tooltip_description(self, event):
        """Mostra tooltip com Observações do processo quando em andamento."""
        try:
            tabela = self.widgets.get('tabela')
            if not tabela or not self.tooltip:
                return

            # Evitar tooltip sobre o cabeçalho ou fora das células
            region = tabela.identify_region(event.x, event.y)
            if region != 'cell':
                self.tooltip.hide()
                return

            # Identificar a linha sob o cursor
            item_id = tabela.identify_row(event.y)
            if not item_id:
                self.tooltip.hide()
                return

            # Obter valores do item e mapear pelos nomes de colunas
            item = tabela.item(item_id)
            values = item.get('values', [])
            colunas = list(self.colunas)

            # Índices das colunas necessárias
            try:
                idx_situacao = colunas.index('situacao')
                idx_descricao = colunas.index('descricao')
            except ValueError:
                self.tooltip.hide()
                return

            situacao = values[idx_situacao] if len(values) > idx_situacao else ''
            descricao = values[idx_descricao] if len(values) > idx_descricao else ''

            # Mostrar Observações somente para registros "Em Andamento"
            if isinstance(situacao, str) and situacao.strip() == 'Em Andamento' and descricao:
                texto = str(descricao).strip()
                if not texto:
                    self.tooltip.hide()
                    return
                # Limitar a 300 caracteres para evitar tooltips muito grandes
                if len(texto) > 300:
                    texto = texto[:300] + '...'
                # Atualizar tooltip: esconder antes para permitir refresh do conteúdo
                self.tooltip.hide()
                self.tooltip.show(f"📋 Observações:\n{texto}")
            else:
                self.tooltip.hide()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao mostrar tooltip")
            
    def _on_leave(self, event):
        """Esconde tooltip ao sair do widget"""
        try:
            if self.tooltip:
                self.tooltip.hide()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao esconder tooltip")
            
    def _activate_field_editing(self, event):
        """Ativa edição de campo"""
        try:
            # Implementar ativação de edição
            pass
        except Exception as e:
            log_error(ui_logger, e, "Erro ao ativar edição")
            
    def _format_date_auto(self, event):
        """Formata data automaticamente"""
        try:
            widget = event.widget
            text = widget.get()
            
            # Implementar formatação automática de data
            formatted_date = DateUtils.format_date_input(text)
            if formatted_date != text:
                widget.delete(0, tk.END)
                widget.insert(0, formatted_date)
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao formatar data")
            
    def _check_date_entry(self, widget, permitir_futuras=True):
        """Verifica entrada de data"""
        try:
            date_text = widget.get().strip()
            if not date_text:
                widget.config(bg="white")
                return
                
            if DateUtils.validate_brazilian_date(date_text):
                if not permitir_futuras and DateUtils.is_future_date(date_text):
                    widget.config(bg="#ffcccc")  # Vermelho claro para datas futuras
                else:
                    widget.config(bg="white")
            else:
                widget.config(bg="#ffcccc")  # Vermelho claro para datas inválidas
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao verificar data")
            
    def _convert_to_uppercase(self, event):
        """Converte texto para maiúsculas"""
        try:
            widget = event.widget
            text = widget.get()
            widget.delete(0, tk.END)
            widget.insert(0, text.upper())
        except Exception as e:
            log_error(ui_logger, e, "Erro ao converter para maiúsculas")
            
    def _on_closing(self):
        """Manipula fechamento da aplicação"""
        try:
            # Salvar configurações se necessário
            # Fechar conexões
            self.janela.destroy()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao fechar aplicação")
            
    def run(self):
        """Executa a aplicação"""
        try:
            self.setup_controllers()
            self.create_main_window()
            self._refresh_table()
            self.janela.mainloop()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao executar aplicação")
            raise

    # === MÉTODOS AUXILIARES ===
    
    def _get_formatted_secretarias(self):
        """Obtém secretarias formatadas do cache"""
        try:
            secretarias = get_cached_secretarias()
            if secretarias is None:
                # Inicializa cache com dados do config
                from services.cache_service import set_cached_secretarias
                set_cached_secretarias(SECRETARIAS)
                secretarias = SECRETARIAS
            return [f"{codigo} - {nome}" for codigo, nome in secretarias.items()]
        except Exception as e:
            log_error(ui_logger, e, "Erro ao obter secretarias")
            # Fallback para dados do config
            return [f"{codigo} - {nome}" for codigo, nome in SECRETARIAS.items()]
            
    def _load_autocomplete_names(self):
        """Carrega nomes para autocomplete"""
        try:
            return self.controllers['process'].obter_nomes_autocomplete()
        except Exception as e:
            log_error(ui_logger, e, "Erro ao carregar nomes")
            return []
            
    def _collect_form_data(self):
        """Coleta dados do formulário"""
        try:
            data = {
                'numero_processo': self.widgets['entrada_numero'].get().strip(),
                'numero_licitacao': self.widgets['entrada_licitacao'].get().strip(),
                'secretaria': self.widgets['entrada_secretaria'].get().strip(),
                'modalidade': self.widgets['entrada_modalidade'].get().strip(),
                'data_inicio': self.widgets['entrada_recebimento'].get().strip(),
                'data_entrega': self.widgets['entrada_devolucao'].get().strip(),
                'entregue_por': self.widgets['entrada_entregue_por'].get().strip(),
                'devolvido_a': self.widgets['entrada_devolvido_a'].get().strip(),
                'contratado': self.widgets['entrada_contratado'].get().strip(),
                'situacao': self.variables['situacao'].get(),
                'observacoes': self.widgets['entrada_descricao'].get("1.0", tk.END).strip(),
                'lembrete': self.variables['lembrete'].get()
            }
            return data
        except Exception as e:
            log_error(ui_logger, e, "Erro ao coletar dados do formulário")
            return {}
            
    def _validate_form_data(self, data):
        """Valida dados do formulário"""
        try:
            # Campos obrigatórios
            if not data.get('numero_processo'):
                messagebox.showerror("Erro", "Número do processo é obrigatório")
                return False
                
            if not data.get('secretaria'):
                messagebox.showerror("Erro", "Secretaria é obrigatória")
                return False
                
            if not data.get('data_inicio'):
                messagebox.showerror("Erro", "Data de recebimento é obrigatória")
                return False
                
            # Validar datas
            if data.get('data_inicio') and not DateUtils.validate_brazilian_date(data['data_inicio']):
                messagebox.showerror("Erro", "Data de recebimento inválida")
                return False
                
            if data.get('data_entrega') and not DateUtils.validate_brazilian_date(data['data_entrega']):
                messagebox.showerror("Erro", "Data de devolução inválida")
                return False
                
            return True
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao validar dados")
            return False
            
    def _populate_form(self, process_data):
        """Preenche formulário com dados do processo"""
        try:
            # Mapear dados para campos
            field_mapping = {
                'entrada_numero': 'numero_processo',
                'entrada_licitacao': 'numero_licitacao',
                'entrada_secretaria': 'secretaria',
                'entrada_modalidade': 'modalidade',
                'entrada_recebimento': 'data_inicio',
                'entrada_devolucao': 'data_entrega',
                'entrada_entregue_por': 'entregue_por',
                'entrada_devolvido_a': 'devolvido_a',
                'entrada_contratado': 'contratado'
            }
            
            # Preencher campos de texto
            for widget_name, data_key in field_mapping.items():
                if widget_name in self.widgets and data_key in process_data:
                    self.widgets[widget_name].delete(0, tk.END)
                    valor = process_data[data_key]
                    if isinstance(valor, str) and valor.strip().lower() == 'none':
                        valor = ''
                    self.widgets[widget_name].insert(0, str(valor or ''))
            
            # Preencher situação
            if 'situacao' in process_data:
                self.variables['situacao'].set(process_data['situacao'])
            
            # Preencher observações
            if 'entrada_descricao' in self.widgets:
                valor = None
                if 'observacoes' in process_data:
                    valor = process_data['observacoes']
                elif 'descricao' in process_data:
                    valor = process_data['descricao']
                self.widgets['entrada_descricao'].delete("1.0", tk.END)
                self.widgets['entrada_descricao'].insert("1.0", str(valor or ''))
            
            # Preencher lembrete
            if 'lembrete' in process_data:
                self.variables['lembrete'].set(bool(process_data['lembrete']))
                
        except Exception as e:
            log_error(ui_logger, e, "Erro ao preencher formulário")
            
    def _refresh_table(self):
        """Atualiza dados da tabela"""
        try:
            # Obter todos os processos
            processes = self.controllers['process'].listar_processos()
            self._populate_table(processes)
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao atualizar tabela")
            
    def _populate_table(self, processes):
        """Popula tabela com lista de processos"""
        try:
            # Limpar tabela
            for item in self.widgets['tabela'].get_children():
                self.widgets['tabela'].delete(item)
            
            # Adicionar processos
            for process in processes:
                # Determinar tag baseada na situação
                tag = 'concluido' if process.get('situacao') == 'Concluído' else 'andamento'
                
                # Inserir na tabela
                values = [process.get(col, '') for col in self.colunas]
                self.widgets['tabela'].insert('', 'end', values=values, tags=(tag,))
            
            # Atualizar estatísticas
            self._update_statistics()
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao popular tabela")
            
    def _update_statistics(self):
        """Atualiza estatísticas na interface"""
        try:
            # Obter estatísticas do controlador
            stats = self.controllers['process'].obter_estatisticas()
            
            # Atualizar labels
            self.widgets['label_concluidos'].config(text=f"Concluídos: {stats.get('concluidos', 0)}")
            self.widgets['label_andamento'].config(text=f"Em Andamento: {stats.get('andamento', 0)}")
            self.widgets['label_editados'].config(text=f"Editados: {stats.get('editados', 0)}")
            self.widgets['label_apagados'].config(text=f"Apagados: {stats.get('apagados', 0)}")
            self.widgets['label_exportados'].config(text=f"Exportações: {self.stats['registros_exportados']}")
            self.widgets['label_importados'].config(text=f"Importações: {self.stats['registros_importados']}")
            self.widgets['label_restaurados'].config(text=f"Restaurados: {stats.get('restaurados', 0)}")
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao atualizar estatísticas")
            
    def _adjust_table_columns(self):
        """Ajusta colunas da tabela conforme tamanho da janela"""
        try:
            # Obter largura atual da janela
            window_width = self.janela.winfo_width()
            
            # Definir colunas visíveis baseado no tamanho da janela
            if window_width > 1200:
                # Janela maximizada - mostrar colunas especificadas
                visible_columns = (
                    'data_registro', 'numero_processo', 'secretaria',
                    'numero_licitacao', 'situacao', 'modalidade',
                    'contratado', 'data_inicio', 'data_entrega', 'descricao'
                )
            else:
                # Janela normal - mostrar colunas essenciais
                visible_columns = (
                    'data_registro', 'numero_processo', 'secretaria',
                    'numero_licitacao', 'situacao', 'modalidade',
                    'data_inicio', 'data_entrega'
                )
            
            self.widgets['tabela']['displaycolumns'] = visible_columns
            
        except Exception as e:
            log_error(ui_logger, e, "Erro ao ajustar colunas")
            
def _create_view_window(self, process_data):
    """Cria janela de visualização de processo"""
    try:
        # Criar janela modal
        view_window = Toplevel(self.janela)
        view_window.title("Visualizar Processo")
        view_window.geometry("600x400")
        view_window.transient(self.janela)
        view_window.grab_set()
        view_window.attributes("-topmost", True)  # Manter sempre em primeiro plano
        
        # Centralizar janela
        view_window.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + 50,
            self.janela.winfo_rooty() + 50
        ))
        
        # Criar conteúdo da janela
        frame = Frame(view_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Adicionar informações do processo
        row = 0
        for i, header in enumerate(self.cabecalhos.values()):
            if i < len(process_data) and process_data[i] is not None:
                # Obter o valor do campo
                valor = process_data[i]
                
                # Converter sigla da secretaria para nome completo
                if header == 'Secretaria' and valor:
                    try:
                        from config.settings import SECRETARIAS
                        sigla = str(valor).strip().upper()
                        if sigla in SECRETARIAS:
                            valor = f"{sigla} - {SECRETARIAS[sigla]}"
                    except Exception:
                        pass  # Mantém o valor original em caso de erro
                
                Label(frame, text=f"{header}:", font=("Segoe UI", 10, "bold")).grid(
                    row=row, column=0, sticky=W, pady=2
                )
                Label(frame, text=str(valor or ''), font=("Segoe UI", 10)).grid(
                    row=row, column=1, sticky=W, padx=(10, 0), pady=2
                )
                row += 1
        
        # Botão fechar
        Button(frame, text="Fechar", command=view_window.destroy,
              font=("Segoe UI", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=20)
        
    except Exception as e:
        log_error(ui_logger, e, "Erro ao criar janela de visualização")
            
    


# Instância global da view
main_view = None

def get_main_view():
    """Obtém instância global da view principal"""
    global main_view
    if main_view is None:
        main_view = MainView()
    return main_view

def run_application():
    """Executa a aplicação principal"""
    try:
        view = get_main_view()
        view.run()
    except Exception as e:
        log_error(ui_logger, e, "Erro ao executar aplicação")
        raise
