import customtkinter as ctk
import tkinter as tk

from core.utils import first_two_words

from config.styles import STYLES



class GroupListView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=12)
        self.app = app

        self.grid_rowconfigure(1, weight=1)

        # Header row
        self.grid_columnconfigure(0, weight=1)  # links: Titel wächst
        self.grid_columnconfigure(1, weight=0)  # rechts: Toggle fix

        title = ctk.CTkLabel(self, text="Groups", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        # --- Anzeige Toggle oben rechts ---
        self.view_full_line = tk.BooleanVar(value=False)

        self.sw_view = ctk.CTkSwitch(
            self,
            text="📜 Full",
            variable=self.view_full_line,
            command=lambda: self.app.refresh_group_list()
        )
        self.sw_view.grid(row=0, column=1, padx=12, pady=(12, 8), sticky="e")

        self.lb = tk.Listbox(self, selectmode=tk.EXTENDED, height=20, exportselection=False)
        self.lb.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="nsew")
        self.lb.bind("<<ListboxSelect>>", app.on_group_select)

        batch = ctk.CTkFrame(self, corner_radius=12)
        batch.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")
        batch.grid_columnconfigure(0, weight=0)
        batch.grid_columnconfigure(1, weight=1)
        batch.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(batch, text="Batch Style:").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.batch_style = ctk.CTkOptionMenu(batch, values=STYLES)
        self.batch_style.set("Normal")
        self.batch_style.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.btn_apply_batch = ctk.CTkButton(batch, text="✅ Apply", command=app.on_apply_batch_style)
        self.btn_apply_batch.grid(row=0, column=2, padx=10, pady=10)
                
        # optional: hint label links (nice-to-have)
        self.lbl_merge = ctk.CTkLabel(batch, text="Merge:")
        self.lbl_merge.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        self.lbl_merge_hint = ctk.CTkLabel(batch, text="wähle 2+ aufeinanderfolgende Zeilen", text_color="#999999")
        self.lbl_merge_hint.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")

        self.btn_merge = ctk.CTkButton(batch, text="🧬 Merge", command=app.on_merge_groups, state="disabled")
        self.btn_merge.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="e")

    def set_merge_enabled(self, enabled: bool, n: int = 0) -> None:
        self.btn_merge.configure(
            state="normal" if enabled else "disabled",
            text=f"🧬 Merge ({n})" if enabled else "🧬 Merge"
        )

    # --- API für den Controller (app_window) ---
    def get_selected_indices(self) -> list[int]:
        return list(self.lb.curselection())

    def get_batch_style(self) -> str:
        return self.batch_style.get()

    def clear_selection(self) -> None:
        self.lb.selection_clear(0, tk.END)

    def refresh(self, groups: list, selected_indices: list[int]) -> None:
        """Re-render list based on current groups."""
        # Save scroll position
        y = self.lb.yview()

        self.lb.delete(0, tk.END)
        for i, g in enumerate(groups):
            style = g.style
            if self.view_full_line.get():
                preview = g.text.replace("\n", " ").strip()
            else:
                preview = first_two_words(g.text)
            steps = len(g.steps)
            self.lb.insert(tk.END, f"{i+1:03d}  [{style}]  {preview}  ({steps} steps)")

        # Re-apply selection (multi-select safe)
        self.lb.selection_clear(0, tk.END)
        for idx in selected_indices or []:
            if 0 <= idx < len(groups):
                self.lb.selection_set(idx)

        # Restore scroll position
        self.lb.yview_moveto(y[0])