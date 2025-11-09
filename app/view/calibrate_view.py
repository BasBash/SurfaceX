from tkinter import ttk, messagebox


class CalibrateGUI(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=20)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self, text="Tela Inicial - Novo Projeto", font=("Arial", 16)) \
            .pack(pady=20)
        ttk.Label(self, text="Aqui você pode iniciar um novo projeto.") \
            .pack(pady=10)
        ttk.Button(
            self, text="Criar Projeto",
            command=lambda: messagebox.showinfo("Novo", "Projeto criado!")
        ).pack(pady=10)


