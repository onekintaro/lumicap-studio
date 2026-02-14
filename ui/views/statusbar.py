import customtkinter as ctk

class StatusBar(ctk.CTkLabel):
    def __init__(self, parent):
        super().__init__(parent, text="Bereit. 😈", anchor="w")

    def set(self, text: str):
        self.configure(text=text)