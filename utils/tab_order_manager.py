"""Gerenciador de ordem de tabulação para interfaces Tkinter."""

import tkinter as tk
from typing import List, Tuple, Optional, Union, Callable
from dataclasses import dataclass
import logging


@dataclass
class TabStop:
    """Representa um ponto de parada de tabulação."""
    order: int
    widget: tk.Widget
    enabled: bool = True
    skip_condition: Optional[Callable[[], bool]] = None
    focus_callback: Optional[Callable[[tk.Widget], None]] = None
    
    def should_skip(self) -> bool:
        """Verifica se este tab stop deve ser pulado."""
        if not self.enabled:
            return True
        
        # Verificar se o widget está habilitado e visível
        try:
            if not self.widget.winfo_viewable():
                return True
            
            # Para widgets que têm estado
            if hasattr(self.widget, 'cget'):
                state = self.widget.cget('state')
                if state == 'disabled':
                    return True
        except tk.TclError:
            return True
        
        # Verificar condição personalizada
        if self.skip_condition and self.skip_condition():
            return True
        
        return False


class TabOrderManager:
    """Gerenciador avançado de ordem de tabulação."""
    
    def __init__(self, root: tk.Widget = None):
        self.root = root
        self.tab_stops: List[TabStop] = []
        self.current_index = -1
        self.circular_navigation = True
        self.auto_focus_first = True
        self.logger = logging.getLogger(__name__)
        
        # Callbacks
        self.on_focus_change: Optional[Callable[[tk.Widget, tk.Widget], None]] = None
        self.on_cycle_complete: Optional[Callable[[], None]] = None
        
        # Configurar bindings se root foi fornecido
        if self.root:
            self._setup_bindings()
    
    def _setup_bindings(self):
        """Configura os bindings de teclado."""
        if not self.root:
            return
        
        # Tab para próximo
        self.root.bind_all('<Tab>', self._handle_tab_forward)
        # Shift+Tab para anterior
        self.root.bind_all('<Shift-Tab>', self._handle_tab_backward)
        # Enter como Tab em alguns casos
        self.root.bind_all('<Return>', self._handle_enter)
        # Escape para sair do foco
        self.root.bind_all('<Escape>', self._handle_escape)
    
    def add_widget(self, widget: tk.Widget, order: int, 
                   enabled: bool = True,
                   skip_condition: Optional[Callable[[], bool]] = None,
                   focus_callback: Optional[Callable[[tk.Widget], None]] = None):
        """Adiciona um widget à ordem de tabulação."""
        tab_stop = TabStop(
            order=order,
            widget=widget,
            enabled=enabled,
            skip_condition=skip_condition,
            focus_callback=focus_callback
        )
        
        self.tab_stops.append(tab_stop)
        self._sort_tab_stops()
        
        # Configurar foco automático no primeiro widget
        if self.auto_focus_first and len(self.tab_stops) == 1:
            self.focus_first()
    
    def remove_widget(self, widget: tk.Widget):
        """Remove um widget da ordem de tabulação."""
        self.tab_stops = [ts for ts in self.tab_stops if ts.widget != widget]
        self._sort_tab_stops()
        
        # Ajustar índice atual se necessário
        if self.current_index >= len(self.tab_stops):
            self.current_index = len(self.tab_stops) - 1
    
    def _sort_tab_stops(self):
        """Ordena os tab stops por ordem."""
        self.tab_stops.sort(key=lambda ts: ts.order)
    
    def enable_widget(self, widget: tk.Widget, enabled: bool = True):
        """Habilita/desabilita um widget na ordem de tabulação."""
        for tab_stop in self.tab_stops:
            if tab_stop.widget == widget:
                tab_stop.enabled = enabled
                break
    
    def set_skip_condition(self, widget: tk.Widget, 
                          condition: Optional[Callable[[], bool]]):
        """Define condição de pulo para um widget."""
        for tab_stop in self.tab_stops:
            if tab_stop.widget == widget:
                tab_stop.skip_condition = condition
                break
    
    def focus_next(self) -> bool:
        """Move o foco para o próximo widget."""
        if not self.tab_stops:
            return False
        
        start_index = self.current_index
        attempts = 0
        max_attempts = len(self.tab_stops) + 1
        
        while attempts < max_attempts:
            self.current_index = (self.current_index + 1) % len(self.tab_stops)
            
            # Se voltou ao início e não é navegação circular
            if not self.circular_navigation and self.current_index <= start_index:
                return False
            
            tab_stop = self.tab_stops[self.current_index]
            
            if not tab_stop.should_skip():
                return self._focus_widget(tab_stop)
            
            attempts += 1
        
        return False
    
    def focus_previous(self) -> bool:
        """Move o foco para o widget anterior."""
        if not self.tab_stops:
            return False
        
        start_index = self.current_index
        attempts = 0
        max_attempts = len(self.tab_stops) + 1
        
        while attempts < max_attempts:
            self.current_index = (self.current_index - 1) % len(self.tab_stops)
            
            # Se voltou ao final e não é navegação circular
            if not self.circular_navigation and self.current_index >= start_index:
                return False
            
            tab_stop = self.tab_stops[self.current_index]
            
            if not tab_stop.should_skip():
                return self._focus_widget(tab_stop)
            
            attempts += 1
        
        return False
    
    def focus_first(self) -> bool:
        """Move o foco para o primeiro widget disponível."""
        if not self.tab_stops:
            return False
        
        self.current_index = -1
        return self.focus_next()
    
    def focus_last(self) -> bool:
        """Move o foco para o último widget disponível."""
        if not self.tab_stops:
            return False
        
        self.current_index = len(self.tab_stops)
        return self.focus_previous()
    
    def focus_widget(self, widget: tk.Widget) -> bool:
        """Move o foco para um widget específico."""
        for i, tab_stop in enumerate(self.tab_stops):
            if tab_stop.widget == widget and not tab_stop.should_skip():
                self.current_index = i
                return self._focus_widget(tab_stop)
        
        return False
    
    def _focus_widget(self, tab_stop: TabStop) -> bool:
        """Foca um widget e executa callbacks."""
        try:
            # Obter widget com foco atual
            old_focus = self.root.focus_get() if self.root else None
            
            # Focar novo widget
            tab_stop.widget.focus_set()
            
            # Executar callback específico do widget
            if tab_stop.focus_callback:
                tab_stop.focus_callback(tab_stop.widget)
            
            # Executar callback global
            if self.on_focus_change:
                self.on_focus_change(old_focus, tab_stop.widget)
            
            self.logger.debug(f"Foco movido para widget: {tab_stop.widget}")
            return True
            
        except tk.TclError as e:
            self.logger.error(f"Erro ao focar widget: {e}")
            return False
    
    def _handle_tab_forward(self, event):
        """Handler para Tab."""
        if self.focus_next():
            return 'break'
        return None
    
    def _handle_tab_backward(self, event):
        """Handler para Shift+Tab."""
        # Prioriza foco no botão "Selecionar Todos" da popup de Autocomplete, se existir
        try:
            from utils.autocomplete_widget import AutocompleteEntry
        except Exception:
            AutocompleteEntry = None

        try:
            owner = getattr(AutocompleteEntry, 'current_popup_owner', None) if AutocompleteEntry else None
            if owner and getattr(owner, 'select_all_btn', None):
                btn = owner.select_all_btn
                if btn and btn.winfo_exists():
                    btn.focus_set()
                    return 'break'
        except tk.TclError:
            pass

        if self.focus_previous():
            return 'break'
        return None
    
    def _handle_enter(self, event):
        """Handler para Enter."""
        # Enter como Tab apenas para Entry widgets
        focused = event.widget
        if isinstance(focused, tk.Entry):
            if self.focus_next():
                return 'break'
        return None
    
    def _handle_escape(self, event):
        """Handler para Escape."""
        # Remove foco do widget atual
        if self.root:
            self.root.focus_set()
        return 'break'
    
    def get_current_widget(self) -> Optional[tk.Widget]:
        """Retorna o widget com foco atual."""
        if 0 <= self.current_index < len(self.tab_stops):
            return self.tab_stops[self.current_index].widget
        return None
    
    def get_widget_order(self, widget: tk.Widget) -> Optional[int]:
        """Retorna a ordem de um widget."""
        for tab_stop in self.tab_stops:
            if tab_stop.widget == widget:
                return tab_stop.order
        return None
    
    def set_widget_order(self, widget: tk.Widget, new_order: int):
        """Altera a ordem de um widget."""
        for tab_stop in self.tab_stops:
            if tab_stop.widget == widget:
                tab_stop.order = new_order
                self._sort_tab_stops()
                break
    
    def clear(self):
        """Remove todos os widgets da ordem de tabulação."""
        self.tab_stops.clear()
        self.current_index = -1
    
    def get_tab_order(self) -> List[Tuple[int, tk.Widget]]:
        """Retorna lista com ordem e widgets."""
        return [(ts.order, ts.widget) for ts in self.tab_stops]
    
    def validate_tab_order(self) -> List[str]:
        """Valida a ordem de tabulação e retorna problemas encontrados."""
        issues = []
        
        if not self.tab_stops:
            issues.append("Nenhum widget na ordem de tabulação")
            return issues
        
        # Verificar widgets duplicados
        widgets = [ts.widget for ts in self.tab_stops]
        if len(widgets) != len(set(widgets)):
            issues.append("Widgets duplicados na ordem de tabulação")
        
        # Verificar ordens duplicadas
        orders = [ts.order for ts in self.tab_stops]
        if len(orders) != len(set(orders)):
            issues.append("Ordens duplicadas na tabulação")
        
        # Verificar widgets inválidos
        for i, tab_stop in enumerate(self.tab_stops):
            try:
                tab_stop.widget.winfo_exists()
            except tk.TclError:
                issues.append(f"Widget inválido na posição {i}")
        
        return issues
    
    def create_navigation_group(self, widgets: List[tk.Widget], 
                               start_order: int = 0) -> 'TabOrderManager':
        """Cria um grupo de navegação para widgets relacionados."""
        group = TabOrderManager(self.root)
        
        for i, widget in enumerate(widgets):
            group.add_widget(widget, start_order + i)
        
        return group
    
    def merge_group(self, other_group: 'TabOrderManager', insert_at: int = None):
        """Mescla outro grupo de tabulação neste."""
        if insert_at is None:
            # Adicionar no final
            max_order = max([ts.order for ts in self.tab_stops], default=-1)
            offset = max_order + 1
        else:
            offset = insert_at
        
        for tab_stop in other_group.tab_stops:
            new_tab_stop = TabStop(
                order=tab_stop.order + offset,
                widget=tab_stop.widget,
                enabled=tab_stop.enabled,
                skip_condition=tab_stop.skip_condition,
                focus_callback=tab_stop.focus_callback
            )
            self.tab_stops.append(new_tab_stop)
        
        self._sort_tab_stops()
    
    @property
    def widgets(self) -> List[Tuple[int, tk.Widget]]:
        """Propriedade para compatibilidade - retorna lista de (ordem, widget)."""
        return [(ts.order, ts.widget) for ts in self.tab_stops]


# Exemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Teste Tab Order Manager")
    
    # Criar gerenciador
    tab_manager = TabOrderManager(root)
    
    # Criar widgets de teste
    tk.Label(root, text="Nome:").grid(row=0, column=0, sticky="w")
    entry1 = tk.Entry(root)
    entry1.grid(row=0, column=1, padx=5, pady=2)
    
    tk.Label(root, text="Email:").grid(row=1, column=0, sticky="w")
    entry2 = tk.Entry(root)
    entry2.grid(row=1, column=1, padx=5, pady=2)
    
    tk.Label(root, text="Telefone:").grid(row=2, column=0, sticky="w")
    entry3 = tk.Entry(root)
    entry3.grid(row=2, column=1, padx=5, pady=2)
    
    button1 = tk.Button(root, text="Salvar")
    button1.grid(row=3, column=0, padx=5, pady=10)
    
    button2 = tk.Button(root, text="Cancelar")
    button2.grid(row=3, column=1, padx=5, pady=10)
    
    # Adicionar à ordem de tabulação
    tab_manager.add_widget(entry1, 1)
    tab_manager.add_widget(entry2, 2)
    tab_manager.add_widget(entry3, 3)
    tab_manager.add_widget(button1, 4)
    tab_manager.add_widget(button2, 5)
    
    # Callback de mudança de foco
    def on_focus_change(old_widget, new_widget):
        print(f"Foco mudou de {old_widget} para {new_widget}")
    
    tab_manager.on_focus_change = on_focus_change
    
    root.mainloop()