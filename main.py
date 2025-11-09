import tkinter as tk
from tkinter import ttk, messagebox
from app.scanner import Scanner
from app.config.constants import APP_TITLE_NAME
from app.view.calibrate_view import CalibrateGUI
from app.config.logger import logger

import sys
if sys.platform.startswith("win"):
    from ctypes import windll
    # noinspection PyUnresolvedReferences
    windll.shcore.SetProcessDpiAwareness(1)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_container()
        self._init_frames()
        (self._create_menu())
        self.show_frame("Scanner")

    def _setup_window(self):
        self.title(APP_TITLE_NAME)
        self.geometry("1450x780")
        self.minsize(1550, 780)

    def _create_container(self):
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

    def _init_frames(self):
        self.frames = {}
        for F in (Scanner, CalibrateGUI):
            name  = F.__name__
            frame = F(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

    def _create_menu(self):
        menu_bar = tk.Menu(self)

        # File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Novo escaneamento", command=lambda: self.show_frame("Scanner"))
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        menu_bar.add_cascade(label="Arquivo", menu=file_menu)

        # Calibrar
        calib_menu = tk.Menu(menu_bar, tearoff=0)
        calib_menu.add_command(label="Calibrar Câmera", command=lambda: self.show_frame("CalibrateGUI"))
        calib_menu.add_command(label="Validar Calibração", command=self._validate_from_menu)
        menu_bar.add_cascade(label="Câmeras", menu=calib_menu)

        # Help
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Sobre", command=self._show_help)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu_bar)

    def show_frame(self, name: str):
        frame = self.frames[name]
        if hasattr(frame, "stop_if_running"):
            frame.stop_if_running()
        frame.tkraise()

    @staticmethod
    def _validate_from_menu():
        messagebox.showwarning("Atenção", "Validação da câmera não implementada ainda.")

    @staticmethod
    def _show_help():
        messagebox.showinfo(
            "Sobre",
            "SurfaceX - 3D Scanner by MITEC\nUse o menu para navegar entre as telas."
        )


if __name__ == "__main__":

    logger.info("Aplicação iniciada")
    app = MainApp()
    app.mainloop()
