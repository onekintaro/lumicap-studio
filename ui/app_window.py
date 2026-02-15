import customtkinter as ctk
from tkinter import filedialog

from ui.views import TopBar, GroupListView, DetailView, StatusBar
from ui.dialogs import open_json_preview, info, MergeDialog

from core.parser import parse_srt
from core.grouping import build_groups
from core.timing_normalize import normalize_timings
from core.merge import merge_groups_smart
from core.protect import toggle_protect
from core.lcap import save_lcap, build_lcap_payload, load_lcap_project
from core.utils import first_two_words, normalize_plain_for_key

class LumiCapStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LumiCap Studio 💜")
        self.geometry("1200x720")
        self.minsize(1050, 650)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.project_path: str | None = None
        self.is_dirty = False

        # --- state ---
        self.srt_path: str | None = None
        self.entries = []
        self.groups = []
        self.selected_indices: list[int] = []

        # --- options (später UI-Toggles) ---
        self.normalize_punct_spacing = True
        self.disable_highlight_at_out = True
        self.default_style = "Normal"

        # --- layout ---
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # detail
        self.grid_rowconfigure(1, weight=1)

        # --- views ---
        self.topbar = TopBar(self, self)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        self.topbar.set_refresh_enabled(False)

        self.sidebar = GroupListView(self, self)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(12, 8), pady=(0, 8))

        self.detail = DetailView(self, self)
        self.detail.grid(row=1, column=1, sticky="nsew", padx=(8, 12), pady=(0, 8))
        self.detail.clear()

        self.statusbar = StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))

        self.refresh_group_list()

    # ---------------------------
    # Helpers
    # ---------------------------
    def _current_settings(self) -> dict:
        return {
            "normalize_punct_spacing": self.normalize_punct_spacing,
            "disable_highlight_at_out": self.disable_highlight_at_out,
            "default_style": self.default_style,
        }

    def _current_meta(self) -> dict:
        # später: draft False beim "Release Export"
        return {"draft": True}

    # ---------------------------
    # Data/UI sync
    # ---------------------------
    def refresh_group_list(self):
        self.sidebar.refresh(self.groups, self.selected_indices)
        self.statusbar.set(f"Groups: {len(self.groups)} | Selected: {len(self.selected_indices)}")

    def show_detail_for_index(self, idx: int):
        g = self.groups[idx]
        self.detail.set_title(f"#{idx+1:03d}  [{g.style}]  {first_two_words(g.text)}")
        self.detail.set_style(g.style)
        self.detail.set_text(g.text)

        lines = [f"t={s.t:.3f}  [{s.start},{s.end}]  label='{s.label}'" for s in g.steps]
        self.detail.set_steps_lines(lines)

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
        self.statusbar.set(f"SRT geladen: {path}")
        self.topbar.set_refresh_enabled(True)

        # Auto-import
        self.on_refresh()

    def on_refresh(self):
        if not self.srt_path:
            return info("Import", "Bitte zuerst ein SRT importieren 🙂")

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
            disable_highlight_at_out=self.disable_highlight_at_out,
        )

        normalize_timings(self.groups)

        self.selected_indices = []
        self.refresh_group_list()
        self.detail.clear()

        info("Import", f"✅ Gruppen gebaut: {len(self.groups)} (aus {len(self.entries)} SRT-Einträgen)")
        self.statusbar.set(f"Import ok ✅ | Groups: {len(self.groups)}")

    def on_export(self):
        if not self.groups:
            return info("Export", "Erst ein SRT importieren 🙂")

        out_path = filedialog.asksaveasfilename(
            title="LumiCap speichern",
            defaultextension=".lcap",
            filetypes=[("LumiCap (*.lcap)", "*.lcap")]
        )
        if not out_path:
            return

        save_lcap(
            self.groups,
            out_path,
            source_path=self.srt_path,
            settings=self._current_settings(),
            meta=self._current_meta(),
        )
        info("Export", f"✅ Exportiert:\n{out_path}")
        self.statusbar.set(f"Saved ✅  {out_path}")

    def on_full_preview(self):
        payload = build_lcap_payload(
            self.groups,
            source_path=self.srt_path,
            settings=self._current_settings(),
            meta=self._current_meta(),
        )
        open_json_preview(self, payload)

    def on_timeline_wip(self):
        info(
            "Timeline Edit [WIP] 😈",
            "😈 Timeline Edit ist aktuell ein Placebo.\n\n"
            "Nebenwirkungen:\n"
            "• plötzliche Produktivität\n"
            "• Zeitcodes, die sich beobachtet fühlen\n"
            "• und das leise Gefühl, dass du gleich ein echtes Tool baust.\n\n"
            "Komm später wieder. Oder klick trotzdem. Ich urteile nicht. 🖤"
        )

    def _selection_is_consecutive(self, indices: list[int]) -> bool:
        if len(indices) < 2:
            return False
        s = sorted(indices)
        return all(s[i] + 1 == s[i+1] for i in range(len(s)-1))

    def on_group_select(self, _evt=None):
        self.selected_indices = self.sidebar.get_selected_indices()
        if not self.selected_indices:
            self.detail.clear()
            self.refresh_group_list()
            self.sidebar.set_merge_enabled(False, 0)
            return

        self.show_detail_for_index(self.selected_indices[0])
        self.refresh_group_list()

        can_merge = self._selection_is_consecutive(self.selected_indices)
        self.sidebar.set_merge_enabled(can_merge, len(self.selected_indices) if can_merge else 0)

    def on_apply_batch_style(self):
        if not self.selected_indices:
            return info("Batch", "Bitte Gruppen markieren 🙂")

        style = self.sidebar.get_batch_style()
        for idx in self.selected_indices:
            if self.groups[idx].style == "!":
                continue
            self.groups[idx].style = style

        self.refresh_group_list()

    def on_merge_groups(self):
        if not self._selection_is_consecutive(self.selected_indices):
            return info("Merge", "Bitte 2+ aufeinanderfolgende Gruppen markieren 🙂")

        # Collect selected groups (in order)
        sel_idx = sorted(self.selected_indices)
        sel_groups = [self.groups[i] for i in sel_idx]

        # Optional: protect block
        if any(g.style == "!" for g in sel_groups):
            return info("Merge", "🛡️ Mindestens eine Gruppe ist geschützt (!). Erst ent-protecten 🙂")

        dlg = MergeDialog(self, sel_groups)
        self.wait_window(dlg)

        if dlg.result is None:
            self.statusbar.set("Merge abgebrochen 🙂")
            return

        merged = dlg.result

        # IMPORTANT: key should match your system (normalize)
        merged.key = normalize_plain_for_key(merged.text.replace("\r", "\n"), self.normalize_punct_spacing)

        # Replace in list: remove old, insert merged at first index
        first = sel_idx[0]
        for i in reversed(sel_idx):
            del self.groups[i]
        self.groups.insert(first, merged)

        # Update selection to merged
        self.selected_indices = [first]
        self.is_dirty = True

        self.refresh_group_list()
        self.show_detail_for_index(first)

        # merge button off now (only 1 selected)
        self.sidebar.set_merge_enabled(False, 0)

        self.statusbar.set(f"🧬 Merged {len(sel_idx)} → 1 (#{first+1:03d}) ✅")

    def on_save_detail(self):
        if not self.selected_indices:
            return info("Save", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        g = self.groups[idx]

        g.text = self.detail.get_text()
        g.style = self.detail.get_style()

        # key updaten, damit apply_same_text nach edits weiter stimmt
        g.key = normalize_plain_for_key(g.text.replace("\r", "\n"), self.normalize_punct_spacing)

        self.is_dirty = True
        self.refresh_group_list()
        self.show_detail_for_index(idx)
        self.statusbar.set(f"💾 Saved group {idx+1:03d}")

    def on_save(self):
        if not self.project_path:
            return self.on_save_as()

        save_lcap(
            self.groups,
            self.project_path,
            source_path=self.srt_path,
            settings=self._current_settings(),
            meta={"draft": False},
        )

        self.is_dirty = False
        self.statusbar.set(f"Saved ✅ {self.project_path}")

    def on_save_as(self):
        path = filedialog.asksaveasfilename(
            title="LumiCap speichern",
            defaultextension=".lcap",
            filetypes=[("LumiCap (*.lcap)", "*.lcap")],
        )
        if not path:
            return

        self.project_path = path
        self.on_save()

    

    def on_open_lcap(self):
        path = filedialog.askopenfilename(
            title="LumiCap öffnen",
            filetypes=[("LumiCap (*.lcap)", "*.lcap")]
        )
        if not path:
            return

        self.groups, meta, settings, self.srt_path = load_lcap_project(path)

        # Apply stored settings back into UI options
        self.normalize_punct_spacing = settings.get("normalize_punct_spacing", True)
        self.disable_highlight_at_out = settings.get("disable_highlight_at_out", True)
        self.default_style = settings.get("default_style", "Normal")

        self.project_path = path
        self.selected_indices = []
        self.is_dirty = False

        self.refresh_group_list()
        self.detail.clear()

        # Rebuild enabled because we have a source (optional)
        self.topbar.set_refresh_enabled(bool(self.srt_path))

        if meta.get("draft"):
            info("Draft geladen", "⚠️ Dieses Projekt ist als Entwurf markiert.")

        self.statusbar.set(f"Projekt geladen ✅ {path}")
        

    def on_apply_style_same_text(self):
        if not self.selected_indices:
            return info("Apply", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        key = self.groups[idx].key
        style = self.detail.get_style()

        count = 0
        for g in self.groups:
            if g.key == key and g.style != "!":
                g.style = style
                count += 1

        self.refresh_group_list()
        info("Apply", f"🔥 '{style}' auf {count} Gruppen mit gleichem Text (key) angewendet.")

    def on_toggle_protect(self):
        if not self.selected_indices:
            return info("Protect", "Keine Gruppe ausgewählt 🙂")

        idx = self.selected_indices[0]
        g = self.groups[idx]

        toggle_protect(g, fallback_style=self.default_style)

        self.refresh_group_list()
        self.show_detail_for_index(idx)