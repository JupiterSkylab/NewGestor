# -*- coding: utf-8 -*-
"""
Widget de autocompletar compartilhado para evitar duplicação de código
"""

import tkinter as tk
from tkinter import END


class AutocompleteEntry(tk.Entry):
    """Widget de entrada com funcionalidade de autocompletar.
    
    Fornece sugestões baseadas em uma lista de completions conforme o usuário digita.
    """
    
    def __init__(self, master, completion_list,
                 listbox_x_offset=-14, listbox_y_offset=-27,
                 listbox_width=300, listbox_max_height=10,
                 escape_callback=None,
                 *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # Mantém referência global ao dono da popup atual para facilitar foco externo
        if not hasattr(AutocompleteEntry, 'current_popup_owner'):
            AutocompleteEntry.current_popup_owner = None
        self.completion_list = sorted(completion_list, key=lambda x: str(x).lower())

        self.listbox = None
        self.select_all_btn = None
        self.listbox_max_height = listbox_max_height
        self._custom_listbox_settings = {
            'x_offset': listbox_x_offset,
            'y_offset': listbox_y_offset,
            'width': listbox_width,
            'max_height': listbox_max_height
        }
        
        # Callback para ESC - se fornecido, será chamado ao invés de limpar apenas este campo
        self.escape_callback = escape_callback
        
        # Vincula eventos
        self.bind('<KeyRelease>', self.on_keyrelease)
        self.bind('<FocusOut>', self.hide_suggestions)
        self.bind('<Up>', self.on_arrow_up)
        self.bind('<Down>', self.on_arrow_down)
        self.bind('<Escape>', self.limpar_campo)
        self.bind('<Tab>', self.on_enter)
        self.bind('<Return>', self.on_enter)
        self.bind('<Double-Button-1>', self.ativar_edicao)

    def set_listbox_properties(self, x_offset=None, y_offset=None, width=None, max_height=None):
        """Configura propriedades da listbox de sugestões."""
        if not hasattr(self, '_custom_listbox_settings'):
            self._custom_listbox_settings = {}
        if x_offset is not None:
            self._custom_listbox_settings['x_offset'] = x_offset
        if y_offset is not None:
            self._custom_listbox_settings['y_offset'] = y_offset
        if width is not None:
            self._custom_listbox_settings['width'] = width
        if max_height is not None:
            self._custom_listbox_settings['max_height'] = max_height
            self.listbox_max_height = max_height

    def show_suggestions(self, matches):
        """Exibe a listbox com sugestões."""
        if self.listbox:
            self.listbox.destroy()

        x = self.winfo_x() + self._custom_listbox_settings['x_offset']
        y = self.winfo_y() + self.winfo_height() + self._custom_listbox_settings['y_offset']
        width = self._custom_listbox_settings['width']

        # Listbox em modo múltiplo para permitir selecionar todos
        self.listbox = tk.Listbox(
            self.master,
            selectmode=tk.MULTIPLE,
            bg="#FFFFFF",
            fg="#000000",
            selectbackground="#0078d4",
            selectforeground="white"
        )
        self.listbox.place(x=x, y=y, width=width)

        for item in matches[:self.listbox_max_height]:
            self.listbox.insert(tk.END, item)

        self.adjust_listbox_height()

        # Botão "Selecionar Todos" abaixo da listbox
        try:
            self.listbox.update_idletasks()
            height_px = self.listbox.winfo_height()
        except Exception:
            height_px = 0

        btn_y = y + height_px + 2
        if self.select_all_btn:
            try:
                self.select_all_btn.destroy()
            except Exception:
                pass
        # Botão focável para permitir navegação via teclado
        self.select_all_btn = tk.Button(
            self.master,
            text="Selecionar Todos",
            command=self._on_select_all_click,
            takefocus=1
        )
        self.select_all_btn.place(x=x, y=btn_y, width=width)

        # Marca o dono atual da popup para permitir foco externo (ex.: Shift+Tab em outro campo)
        AutocompleteEntry.current_popup_owner = self

        # Vincula eventos da listbox
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind('<Return>', self.on_enter)
        self.listbox.bind('<Tab>', self.on_enter)
        self.listbox.bind('<Escape>', self.limpar_campo)
        self.listbox.bind('<Up>', self.on_arrow_up)
        self.listbox.bind('<Down>', self.on_arrow_down)

    def adjust_listbox_height(self):
        """Ajusta a altura da listbox baseada no número de itens."""
        if self.listbox:
            item_count = self.listbox.size()
            height = min(item_count, self.listbox_max_height)
            self.listbox.config(height=height)

    def hide_suggestions(self, event=None):
        """Esconde a listbox de sugestões quando o foco sai para fora da popup."""
        # Se o foco atual está dentro dos componentes da popup, não esconder
        try:
            current_focus = self.master.focus_get()
        except Exception:
            current_focus = None

        if current_focus is not None:
            if current_focus == self.listbox or current_focus == self.select_all_btn:
                return  # mantém popup aberta ao focar listbox ou botão Selecionar Todos

        # Caso contrário, esconde os componentes
        if self.listbox:
            try:
                self.listbox.destroy()
            except Exception:
                pass
            self.listbox = None
        if self.select_all_btn:
            try:
                self.select_all_btn.destroy()
            except Exception:
                pass
            self.select_all_btn = None
        # Limpa a referência global se for deste dono
        if getattr(AutocompleteEntry, 'current_popup_owner', None) is self:
            AutocompleteEntry.current_popup_owner = None

    def on_arrow_up(self, event):
        """Navega para cima na listbox."""
        if self.listbox:
            current_selection = self.listbox.curselection()
            if current_selection:
                index = current_selection[0]
                if index > 0:
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(index - 1)
                    self.listbox.activate(index - 1)
            return 'break'

    def on_arrow_down(self, event):
        """Navega para baixo na listbox."""
        if self.listbox:
            current_selection = self.listbox.curselection()
            if current_selection:
                index = current_selection[0]
                if index < self.listbox.size() - 1:
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(index + 1)
                    self.listbox.activate(index + 1)
            else:
                # Se nada estiver selecionado, seleciona o primeiro item
                if self.listbox.size() > 0:
                    self.listbox.selection_set(0)
                    self.listbox.activate(0)
            return 'break'

    def on_enter(self, event):
        """Confirma a seleção atual."""
        if self.listbox and self.listbox.winfo_viewable():
            current_selection = self.listbox.curselection()
            if current_selection:
                selected_item = self.listbox.get(current_selection[0])
                self.delete(0, tk.END)
                self.insert(0, selected_item)
            self.hide_suggestions()
            return 'break'
        # Se não há listbox visível, permite que o evento continue (para TabOrderManager)
        return None

    def on_listbox_select(self, event):
        """Manipula seleção na listbox."""
        if self.listbox:
            current_selection = self.listbox.curselection()
            if current_selection:
                selected_item = self.listbox.get(current_selection[0])
                self.delete(0, tk.END)
                self.insert(0, selected_item)
                self.hide_suggestions()

    def on_keyrelease(self, event):
        """Manipula liberação de teclas para mostrar sugestões."""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Tab', 'Escape']:
            return

        typed_text = self.get().upper()
        if typed_text:
            matches = [item for item in self.completion_list if typed_text in item.upper()]
            if matches:
                self.show_suggestions(matches)
            else:
                self.hide_suggestions()
        else:
            self.hide_suggestions()

    def limpar_campo(self, event=None):
        """Limpa o campo e esconde sugestões."""
        if self.escape_callback:
            # Se há callback definido, chama ele ao invés de apenas limpar este campo
            self.escape_callback()
        else:
            # Comportamento padrão: limpa apenas este campo
            self.delete(0, tk.END)
        self.hide_suggestions()
        return 'break'

    def ativar_edicao(self, event=None):
        """Ativa modo de edição (placeholder para funcionalidade específica)."""
        pass

    def _on_select_all_click(self):
        """Seleciona todos os itens visíveis na listbox de sugestões."""
        if self.listbox and self.listbox.size() > 0:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0, tk.END)