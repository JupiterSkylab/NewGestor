"""Configurações de interface do usuário para componentes Tkinter.

Inclui utilitários para aplicar um tema escuro harmonioso, suave e discreto
de forma centralizada, afetando widgets Tk e estilos ttk.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font
from typing import Dict, Any, Optional


class UIColors:
    """Paleta de cores para a interface."""
    
    # Cores principais
    PRIMARY = "#007bff"
    SECONDARY = "#6c757d"
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    INFO = "#17a2b8"
    LIGHT = "#f8f9fa"
    DARK = "#343a40"
    
    # Cores de fundo
    BACKGROUND_WHITE = "#ffffff"
    BACKGROUND_LIGHT = "#f8f9fa"
    BACKGROUND_DARK = "#343a40"
    BACKGROUND_SECONDARY = "#e9ecef"
    
    # Cores de texto
    TEXT_PRIMARY = "#212529"
    TEXT_SECONDARY = "#6c757d"
    TEXT_WHITE = "#ffffff"
    TEXT_MUTED = "#6c757d"
    
    # Cores de borda
    BORDER_LIGHT = "#dee2e6"
    BORDER_DARK = "#495057"
    BORDER_PRIMARY = "#007bff"
    
    # Estados de hover
    PRIMARY_HOVER = "#0056b3"
    SECONDARY_HOVER = "#545b62"
    SUCCESS_HOVER = "#1e7e34"
    WARNING_HOVER = "#d39e00"
    DANGER_HOVER = "#bd2130"
    
    # Estados de foco
    FOCUS_SHADOW = "rgba(0, 123, 255, 0.25)"
    
    @classmethod
    def get_color_variants(cls, base_color: str) -> Dict[str, str]:
        """Retorna variações de uma cor base."""
        # Implementação simplificada - em produção usaria biblioteca de cores
        variants = {
            'base': base_color,
            'light': base_color,  # Seria uma versão mais clara
            'dark': base_color,   # Seria uma versão mais escura
            'hover': base_color,  # Seria uma versão para hover
        }
        return variants


class UIFonts:
    """Configurações de fontes."""
    
    @staticmethod
    def get_default_font() -> font.Font:
        """Retorna fonte padrão do sistema."""
        return font.nametofont("TkDefaultFont")
    
    @staticmethod
    def get_heading_font(size: int = 14, weight: str = "bold") -> font.Font:
        """Retorna fonte para cabeçalhos."""
        return font.Font(family="Segoe UI", size=size, weight=weight)
    
    @staticmethod
    def get_body_font(size: int = 10) -> font.Font:
        """Retorna fonte para corpo de texto."""
        return font.Font(family="Segoe UI", size=size)
    
    @staticmethod
    def get_monospace_font(size: int = 10) -> font.Font:
        """Retorna fonte monoespaçada."""
        return font.Font(family="Consolas", size=size)


class UIButtonConfig:
    """Configurações para botões."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para botões."""
        return {
            'font': UIFonts.get_body_font(),
            'relief': 'flat',
            'borderwidth': 1,
            'padx': 12,
            'pady': 6,
            'cursor': 'hand2'
        }
    
    @classmethod
    def get_primary_config(cls) -> Dict[str, Any]:
        """Configuração para botão primário."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.PRIMARY,
            'fg': UIColors.TEXT_WHITE,
            'activebackground': UIColors.PRIMARY_HOVER,
            'activeforeground': UIColors.TEXT_WHITE
        })
        return config
    
    @classmethod
    def get_secondary_config(cls) -> Dict[str, Any]:
        """Configuração para botão secundário."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.SECONDARY,
            'fg': UIColors.TEXT_WHITE,
            'activebackground': UIColors.SECONDARY_HOVER,
            'activeforeground': UIColors.TEXT_WHITE
        })
        return config
    
    @classmethod
    def get_success_config(cls) -> Dict[str, Any]:
        """Configuração para botão de sucesso."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.SUCCESS,
            'fg': UIColors.TEXT_WHITE,
            'activebackground': UIColors.SUCCESS_HOVER,
            'activeforeground': UIColors.TEXT_WHITE
        })
        return config
    
    @classmethod
    def get_warning_config(cls) -> Dict[str, Any]:
        """Configuração para botão de aviso."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.WARNING,
            'fg': UIColors.TEXT_PRIMARY,
            'activebackground': UIColors.WARNING_HOVER,
            'activeforeground': UIColors.TEXT_PRIMARY
        })
        return config
    
    @classmethod
    def get_danger_config(cls) -> Dict[str, Any]:
        """Configuração para botão de perigo."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.DANGER,
            'fg': UIColors.TEXT_WHITE,
            'activebackground': UIColors.DANGER_HOVER,
            'activeforeground': UIColors.TEXT_WHITE
        })
        return config
    
    @classmethod
    def get_outline_config(cls, color: str = None) -> Dict[str, Any]:
        """Configuração para botão com contorno."""
        if color is None:
            color = UIColors.PRIMARY
        
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.BACKGROUND_WHITE,
            'fg': color,
            'relief': 'solid',
            'borderwidth': 1,
            'highlightbackground': color,
            'activebackground': color,
            'activeforeground': UIColors.TEXT_WHITE
        })
        return config


class UIInputConfig:
    """Configurações para campos de entrada."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para campos de entrada."""
        return {
            'font': UIFonts.get_body_font(),
            'relief': 'solid',
            'borderwidth': 1,
            'highlightthickness': 2,
            'highlightcolor': UIColors.PRIMARY,
            'highlightbackground': UIColors.BORDER_LIGHT,
            'bg': UIColors.BACKGROUND_WHITE,
            'fg': UIColors.TEXT_PRIMARY,
            'insertbackground': UIColors.TEXT_PRIMARY
        }
    
    @classmethod
    def get_readonly_config(cls) -> Dict[str, Any]:
        """Configuração para campos somente leitura."""
        config = cls.get_base_config()
        config.update({
            'state': 'readonly',
            'bg': UIColors.BACKGROUND_LIGHT,
            'fg': UIColors.TEXT_SECONDARY
        })
        return config
    
    @classmethod
    def get_error_config(cls) -> Dict[str, Any]:
        """Configuração para campos com erro."""
        config = cls.get_base_config()
        config.update({
            'highlightcolor': UIColors.DANGER,
            'highlightbackground': UIColors.DANGER
        })
        return config
    
    @classmethod
    def get_success_config(cls) -> Dict[str, Any]:
        """Configuração para campos válidos."""
        config = cls.get_base_config()
        config.update({
            'highlightcolor': UIColors.SUCCESS,
            'highlightbackground': UIColors.SUCCESS
        })
        return config


class UILabelConfig:
    """Configurações para labels."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para labels."""
        return {
            'font': UIFonts.get_body_font(),
            'bg': UIColors.BACKGROUND_WHITE,
            'fg': UIColors.TEXT_PRIMARY
        }
    
    @classmethod
    def get_title_config(cls) -> Dict[str, Any]:
        """Configuração para títulos."""
        config = cls.get_base_config()
        config.update({
            'font': UIFonts.get_heading_font(size=16, weight="bold"),
            'fg': UIColors.TEXT_PRIMARY
        })
        return config
    
    @classmethod
    def get_subtitle_config(cls) -> Dict[str, Any]:
        """Configuração para subtítulos."""
        config = cls.get_base_config()
        config.update({
            'font': UIFonts.get_heading_font(size=12, weight="normal"),
            'fg': UIColors.TEXT_SECONDARY
        })
        return config
    
    @classmethod
    def get_secondary_config(cls) -> Dict[str, Any]:
        """Configuração para texto secundário."""
        config = cls.get_base_config()
        config.update({
            'fg': UIColors.TEXT_SECONDARY
        })
        return config
    
    @classmethod
    def get_muted_config(cls) -> Dict[str, Any]:
        """Configuração para texto esmaecido."""
        config = cls.get_base_config()
        config.update({
            'fg': UIColors.TEXT_MUTED
        })
        return config
    
    @classmethod
    def get_error_config(cls) -> Dict[str, Any]:
        """Configuração para mensagens de erro."""
        config = cls.get_base_config()
        config.update({
            'fg': UIColors.DANGER
        })
        return config
    
    @classmethod
    def get_success_config(cls) -> Dict[str, Any]:
        """Configuração para mensagens de sucesso."""
        config = cls.get_base_config()
        config.update({
            'fg': UIColors.SUCCESS
        })
        return config


class UITableConfig:
    """Configurações para tabelas (Treeview)."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para tabelas."""
        return {
            'background': UIColors.BACKGROUND_WHITE,
            'foreground': UIColors.TEXT_PRIMARY,
            'fieldbackground': UIColors.BACKGROUND_WHITE,
            'borderwidth': 1,
            'relief': 'solid'
        }
    
    @classmethod
    def get_header_config(cls) -> Dict[str, Any]:
        """Configuração para cabeçalho da tabela."""
        return {
            'background': UIColors.BACKGROUND_LIGHT,
            'foreground': UIColors.TEXT_PRIMARY,
            'font': UIFonts.get_body_font(weight="bold")
        }
    
    @classmethod
    def get_row_config(cls) -> Dict[str, Any]:
        """Configuração para linhas da tabela."""
        return {
            'background': UIColors.BACKGROUND_WHITE,
            'foreground': UIColors.TEXT_PRIMARY
        }
    
    @classmethod
    def get_alternating_row_config(cls) -> Dict[str, Any]:
        """Configuração para linhas alternadas."""
        return {
            'background': UIColors.BACKGROUND_LIGHT,
            'foreground': UIColors.TEXT_PRIMARY
        }
    
    @classmethod
    def get_selection_config(cls) -> Dict[str, Any]:
        """Configuração para seleção na tabela."""
        return {
            'selectbackground': UIColors.PRIMARY,
            'selectforeground': UIColors.TEXT_WHITE
        }
    
    @classmethod
    def get_style_config(cls) -> Dict[str, Any]:
        """Configuração completa de estilo para Treeview."""
        return {
            'Treeview': cls.get_base_config(),
            'Treeview.Heading': cls.get_header_config(),
            'Treeview.Item': cls.get_row_config(),
            'Treeview.Selection': cls.get_selection_config()
        }
    
    @classmethod
    def get_heading_config(cls) -> Dict[str, Any]:
        """Configuração específica para cabeçalhos."""
        return {
            'background': UIColors.BACKGROUND_SECONDARY,
            'foreground': UIColors.TEXT_PRIMARY,
            'relief': 'flat',
            'font': UIFonts.get_body_font(weight="bold")
        }


class UIFrameConfig:
    """Configurações para frames e containers."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para frames."""
        return {
            'bg': UIColors.BACKGROUND_WHITE,
            'relief': 'flat',
            'borderwidth': 0
        }
    
    @classmethod
    def get_card_config(cls) -> Dict[str, Any]:
        """Configuração para frames tipo card."""
        config = cls.get_base_config()
        config.update({
            'relief': 'solid',
            'borderwidth': 1,
            'highlightbackground': UIColors.BORDER_LIGHT
        })
        return config
    
    @classmethod
    def get_panel_config(cls) -> Dict[str, Any]:
        """Configuração para painéis."""
        config = cls.get_base_config()
        config.update({
            'bg': UIColors.BACKGROUND_LIGHT,
            'relief': 'sunken',
            'borderwidth': 1
        })
        return config


class UIScrollbarConfig:
    """Configurações para scrollbars."""
    
    @classmethod
    def get_base_config(cls) -> Dict[str, Any]:
        """Configuração base para scrollbars."""
        return {
            'bg': UIColors.BACKGROUND_LIGHT,
            'troughcolor': UIColors.BACKGROUND_SECONDARY,
            'activebackground': UIColors.SECONDARY,
            'width': 12,
            'relief': 'flat',
            'borderwidth': 0
        }


class UITheme:
    """Gerenciador de temas da interface."""
    
    def __init__(self, root: tk.Tk = None):
        self.root = root
        self.current_theme = "light"
        self._themes = {
            'light': self._get_light_theme(),
            'dark': self._get_dark_theme()
        }
    
    def _get_light_theme(self) -> Dict[str, Any]:
        """Retorna configurações do tema claro."""
        return {
            'colors': UIColors,
            'button': UIButtonConfig,
            'input': UIInputConfig,
            'label': UILabelConfig,
            'table': UITableConfig,
            'frame': UIFrameConfig,
            'scrollbar': UIScrollbarConfig
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Retorna configurações do tema escuro."""
        # Implementação simplificada - seria uma versão escura das cores
        dark_colors = type('UIColors', (), {
            'PRIMARY': "#0d6efd",
            'SECONDARY': "#6c757d",
            'SUCCESS': "#198754",
            'WARNING': "#ffc107",
            'DANGER': "#dc3545",
            'BACKGROUND_WHITE': "#212529",
            'BACKGROUND_LIGHT': "#343a40",
            'TEXT_PRIMARY': "#ffffff",
            'TEXT_SECONDARY': "#adb5bd",
            'BORDER_LIGHT': "#495057"
        })
        
        return {
            'colors': dark_colors,
            'button': UIButtonConfig,
            'input': UIInputConfig,
            'label': UILabelConfig,
            'table': UITableConfig,
            'frame': UIFrameConfig,
            'scrollbar': UIScrollbarConfig
        }
    
    def apply_theme(self, theme_name: str = "light"):
        """Aplica um tema à interface."""
        if theme_name not in self._themes:
            raise ValueError(f"Tema '{theme_name}' não encontrado")
        
        self.current_theme = theme_name
        theme = self._themes[theme_name]
        
        if self.root:
            # Aplicar configurações globais
            self.root.configure(bg=theme['colors'].BACKGROUND_WHITE)

            # Ajustes globais suaves para widgets Tk via option_add
            try:
                base_bg = getattr(theme['colors'], 'BACKGROUND_WHITE', '#212529')
                surface_bg = getattr(theme['colors'], 'BACKGROUND_LIGHT', '#2b3036')
                text_primary = getattr(theme['colors'], 'TEXT_PRIMARY', '#e6edf3')

                # Defaults para componentes comuns
                self.root.option_add('*Background', base_bg)
                self.root.option_add('*Foreground', text_primary)
                self.root.option_add('*Label.Background', base_bg)
                self.root.option_add('*Label.Foreground', text_primary)
                self.root.option_add('*Frame.Background', base_bg)
                self.root.option_add('*Entry.Background', surface_bg)
                self.root.option_add('*Entry.Foreground', text_primary)
                self.root.option_add('*Text.Background', surface_bg)
                self.root.option_add('*Text.Foreground', text_primary)
                self.root.option_add('*Listbox.Background', surface_bg)
                self.root.option_add('*Listbox.Foreground', text_primary)
            except Exception:
                pass

            # Estilo ttk para componentes estruturais
            try:
                style = ttk.Style(self.root)
                style.theme_use('clam')

                border = '#3c424a'
                selected_bg = '#394857'
                style.configure('Treeview',
                                background=surface_bg,
                                fieldbackground=surface_bg,
                                foreground=text_primary,
                                bordercolor=border)
                style.configure('Treeview.Heading',
                                background=base_bg,
                                foreground=text_primary,
                                bordercolor=border)
                style.map('Treeview',
                          background=[('selected', selected_bg)],
                          foreground=[('selected', text_primary)])

                style.configure('TLabel', background=base_bg, foreground=text_primary)
                style.configure('TEntry', fieldbackground=surface_bg, foreground=text_primary)
                style.configure('TButton', background=selected_bg, foreground=text_primary)
                style.map('TButton', background=[('active', '#23262e'), ('pressed', '#23262e')])
                style.configure('TScrollbar', background=surface_bg)
            except Exception:
                pass
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Retorna o tema atual."""
        return self._themes[self.current_theme]
    
    def register_theme(self, name: str, theme_config: Dict[str, Any]):
        """Registra um novo tema."""
        self._themes[name] = theme_config
    
    def get_available_themes(self) -> list:
        """Retorna lista de temas disponíveis."""
        return list(self._themes.keys())


# Instância global do tema
_global_theme = UITheme()

def get_theme() -> UITheme:
    """Retorna a instância global do tema."""
    return _global_theme

def apply_widget_config(widget: tk.Widget, config: Dict[str, Any]):
    """Aplica configuração a um widget."""
    try:
        widget.configure(**config)
    except tk.TclError as e:
        # Ignorar configurações não suportadas pelo widget
        pass


def apply_dark_theme_to_all_widgets(root: tk.Tk):
    """Aplica um tema escuro harmonioso a todos os widgets existentes.

    - Fundo base: escuro suave
    - Texto: claro sutil
    - Componentes de entrada e listas: superfície levemente mais clara
    - Mantém cores de alerta (vermelhos/amarelos/verde) já definidos
    """
    try:
        bg_base = '#212529'
        bg_surface = '#2b3036'
        text_primary = '#e6edf3'
        text_muted = '#9aa7b0'
        selected_bg = '#394857'
        border = '#3c424a'

        light_backgrounds = {
            '#ECEFF1', '#F5F7FA', '#FFFFFF', '#ffffff', '#f0f0f0', '#E8EBF0', '#DDE7F0', '#f7f7f7'
        }

        def _apply(widget: tk.Widget):
            # Atualiza widget atual
            try:
                wclass = widget.winfo_class()
                current_bg = widget.cget('bg') if 'bg' in widget.keys() else None

                if wclass in ('Frame', 'LabelFrame'):
                    if current_bg in light_backgrounds or current_bg is None:
                        widget.configure(bg=bg_base)
                elif wclass == 'Label':
                    if current_bg in light_backgrounds or current_bg is None:
                        widget.configure(bg=bg_base, fg=text_primary)
                elif wclass == 'Entry':
                    widget.configure(bg=bg_surface, fg=text_primary, insertbackground=text_primary)
                elif wclass == 'Text':
                    widget.configure(bg=bg_surface, fg=text_primary, insertbackground=text_primary)
                elif wclass == 'Button':
                    widget.configure(bg=selected_bg, fg=text_primary,
                                     activebackground='#23262e', activeforeground=text_primary,
                                     highlightbackground=selected_bg)
                elif wclass in ('Checkbutton', 'Radiobutton'):
                    widget.configure(bg=bg_base, fg=text_primary,
                                     activebackground=bg_base, selectcolor=border)
                elif wclass == 'Canvas':
                    if current_bg in light_backgrounds or current_bg is None:
                        widget.configure(bg=bg_base)
                elif wclass == 'Listbox':
                    widget.configure(bg=bg_surface, fg=text_primary,
                                     selectbackground=selected_bg, selectforeground=text_primary)
            except Exception:
                pass

            # Recurse nos filhos
            for child in widget.winfo_children():
                _apply(child)

        _apply(root)

        # Ajustar estilo ttk ao final
        try:
            style = ttk.Style(root)
            style.theme_use('clam')

            style.configure('Treeview', background=bg_surface, fieldbackground=bg_surface,
                            foreground=text_primary, bordercolor=border)
            style.configure('Treeview.Heading', background=bg_base, foreground=text_primary,
                            bordercolor=border)
            style.map('Treeview', background=[('selected', selected_bg)],
                      foreground=[('selected', text_primary)])

            style.configure('TLabel', background=bg_base, foreground=text_primary)
            style.configure('TEntry', fieldbackground=bg_surface, foreground=text_primary)
            style.configure('TButton', background=selected_bg, foreground=text_primary)
            style.map('TButton', background=[('active', '#23262e'), ('pressed', '#23262e')])
            style.configure('TScrollbar', background=bg_surface)
        except Exception:
            pass
    except Exception:
        # Não quebra a aplicação caso algum widget específico falhe
        pass


# Exemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Teste UI Config")
    
    # Aplicar tema
    theme = get_theme()
    theme.apply_theme("light")
    
    # Criar widgets com configurações
    frame = tk.Frame(root)
    apply_widget_config(frame, UIFrameConfig.get_base_config())
    frame.pack(padx=20, pady=20, fill="both", expand=True)
    
    # Label título
    title_label = tk.Label(frame, text="Exemplo de Configuração UI")
    apply_widget_config(title_label, UILabelConfig.get_title_config())
    title_label.pack(pady=(0, 10))
    
    # Campo de entrada
    entry = tk.Entry(frame)
    apply_widget_config(entry, UIInputConfig.get_base_config())
    entry.pack(pady=5, fill="x")
    
    # Botões
    button_frame = tk.Frame(frame)
    apply_widget_config(button_frame, UIFrameConfig.get_base_config())
    button_frame.pack(pady=10, fill="x")
    
    primary_btn = tk.Button(button_frame, text="Primário")
    apply_widget_config(primary_btn, UIButtonConfig.get_primary_config())
    primary_btn.pack(side="left", padx=(0, 5))
    
    secondary_btn = tk.Button(button_frame, text="Secundário")
    apply_widget_config(secondary_btn, UIButtonConfig.get_secondary_config())
    secondary_btn.pack(side="left", padx=5)
    
    success_btn = tk.Button(button_frame, text="Sucesso")
    apply_widget_config(success_btn, UIButtonConfig.get_success_config())
    success_btn.pack(side="left", padx=5)
    
    root.mainloop()
