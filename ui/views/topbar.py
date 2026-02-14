import customtkinter as ctk
import tkinter as tk


class TopBar(ctk.CTkFrame):
    """
    Studio header: Tk menubar (File/Edit/Help) + CTk toolbar (2 rows).
    Controller (app) owns all state + handlers. This view only wires UI -> app callbacks.
    """

    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=12)
        self.app = app

        # --- menubar (native Tk) ---
        self._build_menubar(app)

        # --- toolbar container ---
        self.grid_columnconfigure(0, weight=1)

        # Row 1: File actions
        row1 = ctk.CTkFrame(self, corner_radius=10)
        row1.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.btn_open_lcap = ctk.CTkButton(row1, text="📂 Open", width=120, command=getattr(app, "on_open_lcap", app.on_open_lcap))
        self.btn_open_lcap.grid(row=0, column=0, padx=6, pady=6)

        self.btn_save = ctk.CTkButton(row1, text="💾 Save", width=120, command=getattr(app, "on_save", app.on_save))
        self.btn_save.grid(row=0, column=1, padx=6, pady=6)

        self.btn_save_as = ctk.CTkButton(row1, text="💾 Save As", width=120, command=getattr(app, "on_save_as", app.on_save_as))
        self.btn_save_as.grid(row=0, column=2, padx=6, pady=6)

        # Spacer
        row1.grid_columnconfigure(6, weight=1)

        # Row 2: Workflow actions
        row2 = ctk.CTkFrame(self, corner_radius=10)
        row2.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.btn_import_srt = ctk.CTkButton(row2, text="📄 Import SRT", width=140, command=app.on_open_srt)
        self.btn_import_srt.grid(row=0, column=0, padx=6, pady=6)

        self.btn_rebuild = ctk.CTkButton(row2, text="🔁 Rebuild", width=140, command=app.on_refresh, state="disabled")
        self.btn_rebuild.grid(row=0, column=1, padx=6, pady=6)

        self.btn_preview = ctk.CTkButton(row2, text="🔎 Preview", width=140, command=app.on_full_preview)
        self.btn_preview.grid(row=0, column=2, padx=6, pady=6)

        self.btn_timeline = ctk.CTkButton(row2, text="🧨 Timeline [WIP]", width=160, command=app.on_timeline_wip)
        self.btn_timeline.grid(row=0, column=3, padx=6, pady=6)

        row2.grid_columnconfigure(6, weight=1)

    # --- public API ---
    def set_refresh_enabled(self, enabled: bool) -> None:
        self.btn_rebuild.configure(state="normal" if enabled else "disabled")

    # --- internals ---
    def _build_menubar(self, app) -> None:
        menubar = tk.Menu(app)
        app.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open…", command=getattr(app, "on_open_lcap", self._todo))
        file_menu.add_command(label="Save", command=getattr(app, "on_save", app.on_save))
        file_menu.add_command(label="Save As…", command=getattr(app, "on_save_as", app.on_save_as))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=app.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Rebuild", command=app.on_refresh)
        edit_menu.add_command(label="Preview", command=app.on_full_preview)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=getattr(app, "on_about", self._todo))
        menubar.add_cascade(label="Help", menu=help_menu)

        self._menubar = menubar

    def _todo(self):
        # placeholder if handler not implemented yet
        try:
            from ui.dialogs import info
            info("Not implemented", "😈 Kommt noch. Aber es kommt.")
        except Exception:
            pass