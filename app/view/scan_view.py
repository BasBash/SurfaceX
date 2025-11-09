import threading
from tkinter import ttk, messagebox
import tkinter as tk
from PIL import Image, ImageTk
from app.config.constants import CAMERA_VIEWPORT_WIDTH, CAMERA_VIEWPORT_HEIGHT, BLACK_FRAME
from app.config.logger import logger
from app.core.discovery import get_device_list, get_camera_list
from app.view.datadisplay_gui import DataDisplay
from app.view.camera_gui import CameraModule
from app.core.scanner_config import Scanner


class ScanGUI(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        # region Define os elementos de conteiner.
        self.hardware = Scanner()
        self.controller = controller

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(side="bottom", fill="x")
        # endregion

        # region Define os elementos da status bar
        self.status_bar = ttk.Frame(self, padding=(8, 4))
        self.status_bar = ttk.Frame(self, padding=(8, 4))
        self.status_bar.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(self.status_bar, text="", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.progress_container = ttk.Frame(self.status_bar)
        self.progress_container.pack(side="right", padx=(6, 6))

        self.progress_label = tk.Label(
            self.progress_container,
            text="0%",
            anchor="center",
            width=5,               # largura fixa para alinhar
            foreground="black"
        )
        self.progress_label.pack(side="left", padx=(0, 6))

        self.status_progress = ttk.Progressbar(
            self.progress_container,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            length=700
        )
        self.status_progress.pack(side="left", fill="x", expand=False)
        self.status_progress['value'] = 0

        self.progress_label.pack_forget()
        self.status_progress.pack_forget()

        self.status_bar.pack(side="bottom", fill="x")
        # endregion

        # region Define os elementos do painel de controle lateral
        self.side = ttk.Frame(
            self.main_frame,
            padding=15
        )
        self.side.pack(side="left", fill="y")

        self.datadisplay = DataDisplay(self.side, self)
        self.datadisplay.pack(fill="x", pady=(0, 10))

        self.c_selector = CameraModule(
            self.side, application=self, callback=self.datadisplay.update_params
        )
        self.c_selector.pack(fill="x", pady=(0, 10))

        firmata_frame = ttk.Frame(self.side)
        firmata_frame.pack(fill="x", pady=(0, 10))

        self.combo_var = tk.StringVar()
        self.combo_box = ttk.Combobox(
            firmata_frame,
            textvariable=self.combo_var,
            state="readonly"
        )
        self.combo_box.bind("<<ComboboxSelected>>", self.on_firmata_combobox_change)

        self.button_firmata_refresh = ttk.Button(firmata_frame, text="Atualizar", command=self._update_firmata_devices_list)
        self.label_info = ttk.Label(firmata_frame, text="")

        firmata_frame.columnconfigure(0, weight=1)
        self.combo_box.grid(row=0, column=0, padx=(0, 9), sticky="ew")
        self.button_firmata_refresh.grid(row=0, column=1)
        self.label_info.grid(row=1, column=0, columnspan=2, padx=(0, 9), sticky="ew")

        self.button_connect = ttk.Button(self.side, text="Conectar")
        self.button_connect.pack(fill="x", pady=(0, 5))

        self.button_reference = ttk.Button(self.side, text="Definir Referências")
        self.button_reference.pack(fill="x", pady=(0, 5))

        self.button_scan = ttk.Button(self.side, text="Iniciar Escaneamento")
        self.button_scan.pack(fill="x", pady=(0, 5))
        # endregion

        # region Define os elementos da viewport
        self.viewport = tk.Frame(
            self.main_frame,
            width=CAMERA_VIEWPORT_WIDTH,
            height=CAMERA_VIEWPORT_HEIGHT + 1,
            bg="#D3D3D3"
        )
        self.viewport.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        self.viewport.pack_propagate(False)

        self.black_img = ImageTk.PhotoImage(Image.fromarray(BLACK_FRAME))
        self.label_view = tk.Label(self.viewport, image=self.black_img, bg="white")  # type: ignore
        self.label_view.image = self.black_img # type: ignore
        self.label_view.place(relx=0.5, rely=0.5, anchor="center")
        # endregion

        self.disable_control_buttons()
        self.loop_check_conditions_enable_connect()
        self.loop_check_conditions_enable_ref()
        self._update_firmata_devices_list()

    def loop_check_conditions_enable_connect(self):
        conditions = [
            self.hardware.camera_index is None,
            self.hardware.camera_matrix is None,
            self.hardware.dist_coeffs is None,
            self.hardware.camera_name is None,
            self.hardware.firmata_port is None
        ]
        logger.debug(f"Loop check conditions (all False enables Connect button): {conditions}")
        if any(conditions):
            self.disable_control_buttons()
        else:
            self.button_connect.config(state=tk.NORMAL)

        self.after(1000, self.loop_check_conditions_enable_connect)  # type: ignore

    def loop_check_conditions_enable_ref(self):
        conditions = [
            self.hardware.map_one is None,
            self.hardware.map_two is None,
            self.hardware.camera_instance is None,
            self.hardware.firmata_instance is None,
            self.hardware.camera_matrix is None,
            self.hardware.plane_constants is None
        ]

        logger.debug(f"Loop check conditions (all False enables Reference button): {conditions}")
        if any(conditions):
            self.button_reference.config(state=tk.DISABLED)
        else:
            self.button_reference.config(state=tk.NORMAL)
            self.button_reference.config(command=self.set_references)
        self.after(1000, self.loop_check_conditions_enable_ref) # type: ignore

    def set_status(self, text: str):
        self.after(0, lambda: self.status_label.config(text=text)) # type: ignore

    def set_progress(self, value: int):
        self.progress_label.pack(side="left", padx=(0, 6))
        self.status_progress.pack(side="left", fill="x", expand=False)
        value = max(0, min(100, int(value)))
        self.after(0, lambda: (
            self.status_progress.config(value=value),
            self.progress_label.config(text=f"{value}%")
        )) # type: ignore

    def reset_progress(self):
        self.set_progress(0)
        self.progress_label.pack_forget()
        self.status_progress.pack_forget()

    def _update_firmata_devices_list(self):
        self.combo_box.configure(state=tk.DISABLED)
        self.button_firmata_refresh.configure(state=tk.DISABLED)
        self.button_connect.configure(state=tk.DISABLED)

        def worker():
            try:
                portas = get_device_list()
            except Exception as e:
                portas = []
                logger.error(f"Erro ao buscar dispositivos: {e}")

            def atualizar_ui():
                self.combo_box.set("")
                self.combo_box["values"] = portas

                if portas:
                    self.combo_box.current(0)
                    self.combo_box.event_generate("<<ComboboxSelected>>")
                    self.set_status(text=f"{len(portas)} porta(s) encontrada(s)")
                else:
                    self.set_status(text="Nenhuma porta disponível!")

                self.combo_box.configure(state=tk.NORMAL)
                self.button_firmata_refresh.configure(state=tk.NORMAL)

            self.after(0, atualizar_ui) # type: ignore

        threading.Thread(target=worker, daemon=True).start()

    def _update_camera_list(self):
        self.hardware.release_camera()
        lista = get_camera_list()
        if len(lista) == 0:
            return
        self.camera_dict = {desc: idx for idx, desc in lista}
        descricoes = list(self.camera_dict.keys())

        self.combo_box["values"] = descricoes
        if descricoes:
            self.combo_box.current(0)
            self.combo_box.event_generate("<<ComboboxSelected>>")

    def on_camera_combobox_change(self, event):
        if event is None:
            return

        selected_name = self.combo_box.get()
        selected_index = self.combo_box.current()
        if self.hardware.camera_index == selected_index and selected_name in self.camera_dict:
            return

        self.hardware.release_camera()
        self.hardware.camera_index = selected_index
        self.hardware.camera_name = selected_name
        logger.info(f"Selected camera: {self.hardware.camera_name} :: ID {self.hardware.camera_index}")
        self.datadisplay.update_params()

    def on_firmata_combobox_change(self, event):
        if event is None:
            return
        selected = self.combo_box.get()
        if self.hardware.firmata_port == selected:
            return

        self.hardware.firmata_port = selected
        logger.info(f"Selected port: {self.hardware.firmata_port}")
        self.datadisplay.update_params()

    def disable_control_buttons(self): # TODO: reimplementar ou remover
        # estado inicial do botão 'Conectar'
        self.button_connect.config(text="Conectar")
        self.button_connect.config(command=self.connect_devices) # type: ignore
        self.button_connect.config(state=tk.DISABLED)

        # estado inicial do botão 'Definir Referências'
        self.button_reference.config(text="Definir Referências")
        self.button_reference.config(command=self.set_references)
        self.button_reference.config(state=tk.DISABLED)

        # estado inicial do botão 'Iniciar Escaneamento'
        self.button_scan.config(text="Iniciar Escaneamento")
        self.button_scan.config(command=self.start_scanning)
        self.button_scan.config(state=tk.DISABLED)

    def init_status_bar(self):
        self.status_bar = ttk.Frame(self, padding=(8, 4))
        self.status_bar.pack(side="bottom", fill="x")

        # Label de status (lado esquerdo, expande)
        self.status_label = ttk.Label(self.status_bar, text="", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)

        # Frame para agrupar label percentual + progressbar (lado direito)
        self.progress_container = ttk.Frame(self.status_bar)
        self.progress_container.pack(side="right", padx=(6, 6))

        # Label percentual à esquerda da barra
        self.progress_label = tk.Label(
            self.progress_container,
            text="0%",
            anchor="center",
            width=5,               # largura fixa para alinhar
            foreground="black"
        )
        self.progress_label.pack(side="left", padx=(0, 6))

        # Progressbar com 700 de largura
        self.status_progress = ttk.Progressbar(
            self.progress_container,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            length=700
        )
        self.status_progress.pack(side="left", fill="x", expand=False)
        self.status_progress['value'] = 0

    def set_references(self):
        pass

    def start_scanning(self):
        pass
