import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging

logger = logging.getLogger(__name__)


class DataDisplay(ttk.Frame):
    def __init__(self, parent, application):
        super().__init__(parent, padding=10)
        self.app = application

        self.param_names = [
            "Índice de Câmera", "Porta do Arduino",
            "Dist. Focal em X", "Dist. Focal em Y",
            "Ponto Principal em X", "Ponto Principal em Y"
        ]

        self.param_vars = {
            name: tk.StringVar(value="")
            for name in self.param_names
        }

        self.btn_open_file = ttk.Button(
            self,
            text="Abrir arquivo de calibração…",
            command=self._open_file
        )
        self.btn_open_file.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.columnconfigure(0, weight=1)

        table = ttk.Frame(self)
        table.grid(row=1, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.columnconfigure(1, weight=1)

        for i, name in enumerate(self.param_names):
            lbl = ttk.Label(table, text=f"{name}:", anchor="w")
            val = ttk.Label(table, textvariable=self.param_vars[name], anchor="e")
            lbl.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            val.grid(row=i, column=1, sticky="ew", padx=5, pady=2)

        self.update_params()

    def _open_file(self):
        """ Abre um diálogo para selecionar o arquivo de calibração e carrega os parâmetros da câmera. """
        path = filedialog.askopenfilename(
            title="Selecione o arquivo de calibração",
            filetypes=[("NumPy", "*.npy"), ("Todos", "*.*")]
        )

        if not path:
            return

        try:
            self.app.hardware.set_calibration(path)
            logger.info(f"Camera matrix loaded: {self.app.hardware.camera_matrix}")
            logger.info(f"Distortion coefficients loaded: {self.app.hardware.dist_coeffs}")
            self.update_params()
        except Exception as e:
            logger.exception("Falha ao carregar arquivo de calibração")
            messagebox.showerror("Erro", f"Não foi possível carregar o arquivo:\n{e}")

    def update_params(self):
        vals = {
            "Índice de Câmera": str(self.app.hardware.camera_index),
            "Porta do Arduino": str(self.app.hardware.firmata_port),
        }

        if self.app.hardware.camera_matrix is not None:
            m = self.app.hardware.camera_matrix
            vals.update({
                "Dist. Focal em X": f"{m[0, 0]:.3f}",
                "Dist. Focal em Y": f"{m[1, 1]:.3f}",
                "Ponto Principal em X": f"{m[0, 2]:.3f}",
                "Ponto Principal em Y": f"{m[1, 2]:.3f}"
            })

        for key, var in self.param_vars.items():
            var.set(vals.get(key, ""))

    def disable_elements(self):
        self.btn_open_file.configure(state=tk.DISABLED)

    def enable_elements(self):
        self.btn_open_file.configure(state=tk.NORMAL)