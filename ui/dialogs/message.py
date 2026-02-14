from tkinter import messagebox

def info(title: str, text: str) -> None:
    messagebox.showinfo(title, text)

def warn(title: str, text: str) -> None:
    messagebox.showwarning(title, text)

def error(title: str, text: str) -> None:
    messagebox.showerror(title, text)

def confirm(title: str, text: str) -> bool:
    return messagebox.askyesno(title, text)