import logging
import tkinter as tk
from tkinter import ttk
from app.core.discovery import get_camera_list

class CameraModule(ttk.Frame):
    def __init__(self, parent, application, callback):
        super().__init__(parent)
        self.app = application

        self.display_callback = callback

        self.camera_dict = {}
        self.combo_var = tk.StringVar()
        self.combo_box = ttk.Combobox(
            self,
            textvariable=self.combo_var,
            state="readonly"
        )
        self.combo_box.bind("<<ComboboxSelected>>", self.on_combobox_change)
        self.btn_refresh = ttk.Button(self, text="Atualizar", command=self.update_camera_list)

        self.columnconfigure(0, weight=1)
        self.combo_box.grid(row=0, column=0, padx=(0, 9), sticky="ew")
        self.btn_refresh.grid(row=0, column=1)

        self.update_camera_list()

    def on_combobox_change(self, event):
        if event is None:
            return

        selected_name = self.combo_box.get()
        selected_index = self.combo_box.current()
        if self.app.hardware.camera_index == selected_index and selected_name in self.camera_dict:
            return

        self.app.hardware.release_camera()
        self.app.hardware.camera_index = selected_index
        self.app.hardware.camera_name = selected_name
        logging.info(f"Selected camera: {self.app.hardware.camera_name} :: ID {self.app.hardware.camera_index}")
        if callable(self.display_callback):
            self.display_callback()

    def update_camera_list(self):
        self.app.hardware.release_camera()
        lista = get_camera_list()
        if len(lista) == 0:
            return
        self.camera_dict = {desc: idx for idx, desc in lista}
        descricoes = list(self.camera_dict.keys())

        self.combo_box["values"] = descricoes
        if descricoes:
            self.combo_box.current(0)
            self.combo_box.event_generate("<<ComboboxSelected>>")

    def disable_elements(self):
        self.combo_box.configure(state=tk.DISABLED)
        self.btn_refresh.configure(state=tk.DISABLED)

    def enable_elements(self):
        self.combo_box.configure(state=tk.NORMAL)
        self.btn_refresh.configure(state=tk.NORMAL)