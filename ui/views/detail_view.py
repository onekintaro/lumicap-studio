import customtkinter as ctk
import tkinter as tk

from config.styles import STYLES
class DetailView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=12)
        self.app = app

        if not hasattr(self.app, "on_save_detail"):
            raise TypeError(
                f"DetailView expected controller with on_save_detail; got {type(self.app)}"
            )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- header (title + style) ---
        header = ctk.CTkFrame(self, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        self.detail_title = ctk.CTkLabel(header, text="—", font=ctk.CTkFont(size=18, weight="bold"))
        self.detail_title.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        self.detail_style = ctk.CTkOptionMenu(header, values=STYLES)
        self.detail_style.set("Normal")
        self.detail_style.grid(row=0, column=1, padx=12, pady=12, sticky="e")

        # --- text ---
        self.txt_label = ctk.CTkLabel(self, text="Text:")
        self.txt_label.grid(row=1, column=0, padx=12, pady=(8, 0), sticky="w")

        self.txt_text = ctk.CTkTextbox(self, height=90)
        self.txt_text.grid(row=2, column=0, padx=12, pady=(6, 12), sticky="ew")

        # --- steps ---
        steps_frame = ctk.CTkFrame(self, corner_radius=12)
        steps_frame.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            steps_frame,
            text="Steps (t / start-end / label):",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.steps_box = ctk.CTkTextbox(steps_frame)
        self.steps_box.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # --- footer buttons ---
        footer = ctk.CTkFrame(self, corner_radius=12)
        footer.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))

        self.btn_save_detail = ctk.CTkButton(
            footer, text="💾 Save Changes", command=self.app.on_save_detail
        )
        self.btn_save_detail.grid(row=0, column=0, padx=10, pady=10)

        self.btn_apply_same_text = ctk.CTkButton(
            footer, text="🔥 Style → alle gleichen Texte", command=self.app.on_apply_style_same_text
        )
        self.btn_apply_same_text.grid(row=0, column=1, padx=10, pady=10)

        self.btn_protect = ctk.CTkButton(
            footer, text="🛡️ Toggle Protect (!)", command=self.app.on_toggle_protect
        )
        self.btn_protect.grid(row=0, column=2, padx=10, pady=10)

    # --- API für Controller ---
    def clear(self) -> None:
        self.detail_title.configure(text="—")
        self.detail_style.set("Normal")
        self.txt_text.delete("1.0", tk.END)
        self.steps_box.delete("1.0", tk.END)

    def set_title(self, text: str) -> None:
        self.detail_title.configure(text=text)

    def set_style(self, style: str) -> None:
        self.detail_style.set(style)

    def get_style(self) -> str:
        return self.detail_style.get()

    def set_text(self, text: str) -> None:
        self.txt_text.delete("1.0", tk.END)
        self.txt_text.insert("1.0", text)

    def get_text(self) -> str:
        return self.txt_text.get("1.0", tk.END).rstrip("\n")

    def set_steps_lines(self, lines: list[str]) -> None:
        self.steps_box.delete("1.0", tk.END)
        for line in lines:
            self.steps_box.insert("end", line + "\n")