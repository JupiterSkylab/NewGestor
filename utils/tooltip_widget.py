"""Widget de tooltip reutilizável para a aplicação."""

import tkinter as tk
import time


class ToolTip:
    """Classe para criar tooltips em widgets tkinter."""
    
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.label = None
        self.x = self.y = 0
        # Controle de atualização suave
        self.last_update_time = 0
        self.update_interval_ms = 16  # ~60 FPS
        self.min_delta_px = 3  # evita atualizações para movimentos muito pequenos

    def show(self, text):
        """Exibe/atualiza o tooltip com o texto especificado ao lado do cursor."""
        if not text:
            self.hide()
            return

        current_time = time.time() * 1000  # Tempo atual em milissegundos
        
        # Posição atual do cursor
        x = self.widget.winfo_pointerx() + 16
        y = self.widget.winfo_pointery() + 16

        if self.tip_window is None:
            # Cria a janela do tooltip
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.attributes("-topmost", True)

            # Label com fundo amarelo
            self.label = tk.Label(
                tw,
                text=text,
                justify=tk.LEFT,
                background="#FFF9C4",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Segoe UI", 9)
            )
            self.label.pack(ipadx=6, ipady=4)
            
            # Inicializa a posição e o tempo
            self.x = x
            self.y = y
            self.last_update_time = current_time
            
            # Posiciona o tooltip
            self.tip_window.wm_geometry(f"+{x}+{y}")
        else:
            # Atualiza texto do tooltip existente
            self.label.config(text=text)

            # Atualiza posição em intervalos suaves para evitar tremores
            dx = abs(x - self.x)
            dy = abs(y - self.y)
            if (current_time - self.last_update_time) >= self.update_interval_ms or (dx + dy) >= self.min_delta_px:
                self.x = x
                self.y = y
                self.last_update_time = current_time
                self.tip_window.wm_geometry(f"+{x}+{y}")

    def hide(self):
        """Esconde o tooltip e reseta estado de posição."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
            self.label = None
        # Reset de controle de atualização
        self.last_update_time = 0
