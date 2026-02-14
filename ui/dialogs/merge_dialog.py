# ui/dialogs/merge_dialog.py
import customtkinter as ctk
import tkinter as tk
from core.merge import merge_groups_smart
from core.models import Group

class MergeDialog(ctk.CTkToplevel):
    def __init__(self, parent, groups: list[Group]):
        super().__init__(parent)
        self.title("Merge Groups 🧬")
        self.geometry("680x520")
        self.minsize(620, 480)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.groups = sorted(groups, key=lambda g: g.t_in)
        self.result: Group | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- basis text selector ---
        ctk.CTkLabel(self, text="Basis-Text wählen:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 6), sticky="w"
        )

        values = [f"#{i+1:03d}  {g.text}" for i, g in enumerate(self.groups)]
        self.base_menu = ctk.CTkOptionMenu(self, values=values, command=self._on_base_change)
        self.base_menu.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
        self.base_menu.set(values[0])

        # --- result text editor ---
        ctk.CTkLabel(self, text="Result-Text (editierbar):", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=14, pady=(0, 6), sticky="w"
        )
        self.txt = ctk.CTkTextbox(self, height=90)
        self.txt.grid(row=3, column=0, padx=14, pady=(0, 10), sticky="nsew")

        # --- steps preview ---
        box = ctk.CTkFrame(self, corner_radius=12)
        box.grid(row=4, column=0, padx=14, pady=(0, 10), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Preview Steps:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self.preview = ctk.CTkTextbox(box)
        self.preview.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # --- buttons ---
        btns = ctk.CTkFrame(self, corner_radius=12)
        btns.grid(row=5, column=0, padx=14, pady=(0, 14), sticky="ew")
        btns.grid_columnconfigure(0, weight=1)

        self.btn_cancel = ctk.CTkButton(btns, text="❌ Abbrechen", command=self._cancel)
        self.btn_cancel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.btn_ok = ctk.CTkButton(btns, text="✅ OK (merge)", command=self._ok)
        self.btn_ok.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # bindings: live preview
        self.txt.bind("<KeyRelease>", lambda _e: self._refresh_preview())
        self.bind("<Escape>", lambda _e: self._cancel())

        # init: choose best default base text (prefer punctuation / longer)
        best_idx = max(range(len(self.groups)), key=lambda i: (len(self.groups[i].text), self.groups[i].text.endswith((".", "!", "?", "…"))))
        self.base_menu.set(values[best_idx])
        self._apply_base_text(best_idx)

    def _base_index(self) -> int:
        current = self.base_menu.get()
        return max(0, min(len(self.groups)-1, [f"#{i+1:03d}  {g.text}" for i,g in enumerate(self.groups)].index(current)))

    def _apply_base_text(self, idx: int):
        self.txt.delete("1.0", tk.END)
        self.txt.insert("1.0", self.groups[idx].text)
        self._refresh_preview()

    def _on_base_change(self, _value: str):
        self._apply_base_text(self._base_index())

    def _refresh_preview(self):
        try:
            merged = merge_groups_smart(self.groups, self.txt.get("1.0", tk.END).rstrip("\n"))
            lines = [f"t={s.t:.3f}  [{s.start},{s.end}]  label='{s.label}'" for s in merged.steps]
        except Exception as e:
            lines = [f"⚠️ Preview error: {e}"]

        self.preview.delete("1.0", tk.END)
        for ln in lines:
            self.preview.insert("end", ln + "\n")

    def _ok(self):
        self.result = merge_groups_smart(self.groups, self.txt.get("1.0", tk.END).rstrip("\n"))
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()