import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json

from core.parser import parse_srt
from core.grouping import build_groups
from core.protect import toggle_protect
from core.lcap import save_lcap, build_lcap_payload
from core.utils import first_two_words, normalize_plain_for_key

STYLES = ["Normal", "Chorus", "Emphasis", "Bridge", "Verse", "Spoken", "!"] + [chr(c) for c in range(ord("A"), ord("Z")+1)]

class LumiCapStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LumiCap Studio 💜")
        self.geometry("1200x720")
        self.minsize(1050, 650)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.srt_path = None
        self.entries = []
        self.groups = []
        self.selected_indices = []

        # options (kannst du später als UI-Toggles hinzufügen)
        self.normalize_punct_spacing = True
        self.disable_highlight_at_out = True
        self.default_style = "Normal"

        # Layout: Top bar + Content (sidebar + detail) + status
        self.grid_columnconfigure(0, weight=0)   # sidebar
        self.grid_columnconfigure(1, weight=1)   # detail
        self.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_sidebar()
        self._build_detail()
        self._build_statusbar()

        self.refresh_group_list()

    def _build_topbar(self):
        self.top = ctk.CTkFrame(self, corner_radius=12)
        self.top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        self.top.grid_columnconfigure(5, weight=1)

        self.btn_open = ctk.CTkButton(self.top, text="📄 SRT öffnen", command=self.on_open_srt)
        self.btn_open.grid(row=0, column=0, padx=10, pady=10)

        self.btn_refresh = ctk.CTkButton(self.top, text="🧪 Preview aktualisieren", command=self.on_refresh)
        self.btn_refresh.grid(row=0, column=1, padx=10, pady=10)

        self.btn_export = ctk.CTkButton(self.top, text="💾 Export LumiCap (.lcap)", command=self.on_export)
        self.btn_export.grid(row=0, column=2, padx=10, pady=10)

        self.btn_full_preview = ctk.CTkButton(self.top, text="🔎 Full Preview", command=self.on_full_preview)
        self.btn_full_preview.grid(row=0, column=3, padx=10, pady=10)

        self.btn_timeline = ctk.CTkButton(self.top, text="🧨 Timeline Edit [WIP] 😈", command=self.on_timeline_wip)
        self.btn_timeline.grid(row=0, column=4, padx=10, pady=10)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, corner_radius=12)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(12, 8), pady=(0, 8))
        self.sidebar.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self.sidebar, text="Groups", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self.lb = tk.Listbox(self.sidebar, selectmode=tk.EXTENDED, height=20)
        self.lb.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.lb.bind("<<ListboxSelect>>", self.on_group_select)

        batch = ctk.CTkFrame(self.sidebar, corner_radius=12)
        batch.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        batch.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(batch, text="Batch Style:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.batch_style = ctk.CTkOptionMenu(batch, values=STYLES)
        self.batch_style.set("Normal")
        self.batch_style.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.btn_apply_batch = ctk.CTkButton(batch, text="✅ Apply", command=self.on_apply_batch_style)
        self.btn_apply_batch.grid(row=0, column=2, padx=10, pady=10)

    def _build_detail(self):
        self.detail = ctk.CTkFrame(self, corner_radius=12)
        self.detail.grid(row=1, column=1, sticky="nsew", padx=(8, 12), pady=(0, 8))
        self.detail.grid_columnconfigure(0, weight=1)
        self.detail.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self.detail, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        header.grid_columnconfigure(1, weight=1)

        self.detail_title = ctk.CTkLabel(header, text="—", font=ctk.CTkFont(size=18, weight="bold"))
        self.detail_title.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        self.detail_style = ctk.CTkOptionMenu(header, values=STYLES)
        self.detail_style.set("Normal")
        self.detail_style.grid(row=0, column=1, padx=12, pady=12, sticky="e")

        self.txt_label = ctk.CTkLabel(self.detail, text="Text:")
        self.txt_label.grid(row=1, column=0, padx=12, pady=(8, 0), sticky="w")

        self.txt_text = ctk.CTkTextbox(self.detail, height=90)
        self.txt_text.grid(row=2, column=0, padx=12, pady=(6, 12), sticky="ew")

        steps_frame = ctk.CTkFrame(self.detail, corner_radius=12)
        steps_frame.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(steps_frame, text="Steps (t / start-end / label):", font=ctk.CTkFont(weight="bold"))\
            .grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.steps_box = ctk.CTkTextbox(steps_frame)
        self.steps_box.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        footer = ctk.CTkFrame(self.detail, corner_radius=12)
        footer.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))

        self.btn_save_detail = ctk.CTkButton(footer, text="💾 Save Changes", command=self.on_save_detail)
        self.btn_save_detail.grid(row=0, column=0, padx=10, pady=10)

        self.btn_apply_same_text = ctk.CTkButton(footer, text="🔥 Style → alle gleichen Texte", command=self.on_apply_style_same_text)
        self.btn_apply_same_text.grid(row=0, column=1, padx=10, pady=10)

        self.btn_protect = ctk.CTkButton(footer, text="🛡️ Toggle Protect (!)", command=self.on_toggle_protect)
        self.btn_protect.grid(row=0, column=2, padx=10, pady=10)

    def _build_statusbar(self):
        self.status = ctk.CTkLabel(self, text="Bereit. 😈", anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))

    # ---------------------------
    # Data/UI sync
    # ---------------------------
    def refresh_group_list(self):
        self.lb.delete(0, tk.END)
        for i, g in enumerate(self.groups):
            style = g.style
            preview = first_two_words(g.text)
            steps = len(g.steps)
            self.lb.insert(tk.END, f"{i+1:03d}  [{style}]  {preview}  ({steps} steps)")
        self.status.configure(text=f"Groups: {len(self.groups)} | Selected: {len(self.selected_indices)}")

    def show_detail_for_index(self, idx: int):
        g = self.groups[idx]
        self.detail_title.configure(text=f"#{idx+1:03d}  [{g.style}]  {first_two_words(g.text)}")
        self.detail_style.set(g.style)

        self.txt_text.delete("1.0", tk.END)
        self.txt_text.insert("1.0", g.text)

        self.steps_box.delete("1.0", tk.END)
        for s in g.steps:
            self.steps_box.insert("end", f"t={s.t:.3f}  [{s.start},{s.end}]  label='{s.label}'\n")

    # ---------------------------
    # Actions
    # ---------------------------
    def on_open_srt(self):
        path = filedialog.askopenfilename(
            title="SRT auswählen",
            filetypes=[("SubRip (*.srt)", "*.srt"), ("All files", "*.*")]
        )
        if not path:
            return
        self.srt_path = path
        self.status.configure(text=f"SRT geladen: {path}")

    def on_refresh(self):
        if not self.srt_path:
            return messagebox.showinfo("Preview", "Bitte zuerst ein SRT öffnen 🙂")

        try:
            with open(self.srt_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(self.srt_path, "r", encoding="utf-8-sig") as f:
                text = f.read()

        self.entries = parse_srt(text, normalize_punct_spacing=self.normalize_punct_spacing)
        self.groups = build_groups(
            self.entries,
            default_style=self.default_style,
            disable_highlight_at_out=self.disable_highlight_at_out
        )

        self.selected_indices = []
        self.refresh_group_list()
        self.detail_title.configure(text="—")
        self.txt_text.delete("1.0", tk.END)
        self.steps_box.delete("1.0", tk.END)

        messagebox.showinfo("Preview", f"✅ Gruppen gebaut: {len(self.groups)} (aus {len(self.entries)} SRT-Einträgen)")

    def on_export(self):
        if not self.groups:
            return messagebox.showinfo("Export", "Erst Preview aktualisieren 🙂")

        out_path = filedialog.asksaveasfilename(
            title="LumiCap speichern",
            defaultextension=".lcap",
            filetypes=[("LumiCap (*.lcap)", "*.lcap")]
        )
        if not out_path:
            return

        save_lcap(self.groups, out_path, source_path=self.srt_path, settings=settings, meta=meta)
        messagebox.showinfo("Export", f"✅ Exportiert:\n{out_path}")

    def on_full_preview(self):
        settings = {
            "normalize_punct_spacing": self.normalize_punct_spacing,
            "disable_highlight_at_out": self.disable_highlight_at_out,
            "default_style": self.default_style,
        }

        payload = build_lcap_payload(
            self.groups,
            source_path=self.srt_path,
            settings=settings
        )

        win = ctk.CTkToplevel(self)
        win.title("Full Preview 🔎")
        win.geometry("900x600")

        box = ctk.CTkTextbox(win)
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", json.dumps(payload, ensure_ascii=False, indent=2))

    def on_timeline_wip(self):
        messagebox.showinfo(
            "Timeline Edit [WIP] 😈",
            "😈 Timeline Edit ist aktuell ein Placebo.\n\n"
            "Nebenwirkungen:\n"
            "• plötzliche Produktivität\n"
            "• Zeitcodes, die sich beobachtet fühlen\n"
            "• und das leise Gefühl, dass du gleich ein echtes Tool baust.\n\n"
            "Komm später wieder. Oder klick trotzdem. Ich urteile nicht. 🖤"
        )

    def on_group_select(self, _evt=None):
        self.selected_indices = list(self.lb.curselection())
        if not self.selected_indices:
            self.detail_title.configure(text="—")
            return

        self.show_detail_for_index(self.selected_indices[0])
        self.status.configure(text=f"Groups: {len(self.groups)} | Selected: {len(self.selected_indices)}")

    def on_apply_batch_style(self):
        if not self.selected_indices:
            return messagebox.showinfo("Batch", "Bitte Gruppen markieren 🙂")

        style = self.batch_style.get()
        for idx in self.selected_indices:
            if self.groups[idx].style == "!":
                continue
            self.groups[idx].style = style

        self.refresh_group_list()

    def on_save_detail(self):
        if not self.selected_indices:
            return messagebox.showinfo("Save", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        g = self.groups[idx]

        g.text = self.txt_text.get("1.0", tk.END).rstrip("\n")
        g.style = self.detail_style.get()

        # key updaten (damit 'apply same text' nach edits weiter stimmt)
        g.key = normalize_plain_for_key(g.text.replace("\r", "\n"), self.normalize_punct_spacing)

        self.refresh_group_list()
        self.show_detail_for_index(idx)
        self.status.configure(text=f"💾 Saved group {idx+1:03d}")

    def on_apply_style_same_text(self):
        if not self.selected_indices:
            return messagebox.showinfo("Apply", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        key = self.groups[idx].key
        style = self.detail_style.get()

        count = 0
        for g in self.groups:
            if g.key == key and g.style != "!":
                g.style = style
                count += 1

        self.refresh_group_list()
        messagebox.showinfo("Apply", f"🔥 '{style}' auf {count} Gruppen mit gleichem Text (key) angewendet.")

    def on_toggle_protect(self):
        if not self.selected_indices:
            return messagebox.showinfo("Protect", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        g = self.groups[idx]

        toggle_protect(g, fallback_style=self.default_style)

        self.refresh_group_list()
        self.show_detail_for_index(idx)