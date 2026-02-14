import customtkinter as ctk
import json

def open_json_preview(parent: ctk.CTk, payload: dict, title: str = "Full Preview 🔎") -> None:
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("900x600")

    # Bring window to front (Windows-friendly)
    win.lift()
    win.focus_force()
    win.attributes("-topmost", True)
    win.after(200, lambda: win.attributes("-topmost", False))

    box = ctk.CTkTextbox(win)
    box.pack(fill="both", expand=True, padx=12, pady=12)

    box.insert("1.0", json.dumps(payload, ensure_ascii=False, indent=2))
    box.configure(state="disabled")  # read-only