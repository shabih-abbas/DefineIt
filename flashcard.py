import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

import storage
from widgets import DefinitionText, window_xy

RIGHT_CLICKS = ("<Button-2>", "<Button-3>") if sys.platform == "darwin" else ("<Button-3>",)


class FlashcardWindow:
    W, H = 400, 340

    def __init__(self, root, entry):
        self.entry = entry
        self.revealed = False

        self.win = win = tk.Toplevel(root)
        win.title("defineIt · Flashcard")
        win.resizable(False, False)

        rx, ry = window_xy(root)
        x = rx - self.W - 10
        if x < 0:
            x = rx + root.winfo_width() + 10
        win.geometry(f"{self.W}x{self.H}+{x}+{ry}")

        base = tkfont.nametofont("TkDefaultFont")
        self._big = base.copy()
        self._big.configure(size=26, weight="bold")
        self._mid = base.copy()
        self._mid.configure(size=14, weight="bold")


        self.front = ttk.Frame(win)
        self.word_label = ttk.Label(self.front, font=self._big, anchor="center",
                                    justify="center", wraplength=self.W - 40)
        self.word_label.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(self.front, text="Left-click: show definitions    Right-click: next word",
                  foreground="#888888").place(relx=0.5, rely=0.96, anchor="s")


        self.back = ttk.Frame(win, padding=8)
        self.back_title = ttk.Label(self.back, font=self._mid, wraplength=self.W - 30)
        self.back_title.pack(anchor="w")
        self.defs = DefinitionText(self.back)
        self.defs.pack(fill="both", expand=True, pady=(6, 0))


        win.bind("<Button-1>", self.reveal)
        for seq in RIGHT_CLICKS:
            win.bind(seq, self.next_word)
        win.bind("<Escape>", lambda e: win.destroy())

        self.show(entry)
        win.focus_set()

    def show(self, entry):
        self.entry = entry
        self.revealed = False

        phonetic = f"   {entry['phonetic']}" if entry.get("phonetic") else ""
        self.word_label.config(text=entry["word"])
        self.back_title.config(text=entry["word"] + phonetic)
        self.defs.render(entry)                 # prepared now so revealing is instant

        self.back.pack_forget()
        self.front.pack(fill="both", expand=True)

    def reveal(self, event=None):
        if self.revealed:
            return
        self.revealed = True
        self.front.pack_forget()
        self.back.pack(fill="both", expand=True)

    def next_word(self, event=None):
        nxt = storage.get_random_word(exclude=self.entry["word"])
        if nxt:
            self.show(nxt)