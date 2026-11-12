
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import api
import storage
from flashcard import FlashcardWindow
from widgets import DefinitionText, window_xy

WIDTH = 380            
COLLAPSED_H = 56       
MIN_EXPANDED_H = 300   
BOTTOM_MARGIN = 90     
CORNER_MARGIN = 20     


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()      
        self._req = 0               
        self.current = None         
        self.flash = None           

        root.title("defineIt")
        root.resizable(False, False)            

        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()
        x, y = self._initial_position()
        root.geometry(f"{WIDTH}x{COLLAPSED_H}+{x}+{y}")

        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Escape>", lambda e: self.collapse())
        self._poll()

    
    def _build_ui(self):
        bar = ttk.Frame(self.root, padding=(8, 10))
        bar.pack(fill="x")
        bar.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(bar)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", self.search)
        self.entry.focus_set()
        ttk.Button(bar, text="Search", command=self.search).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(bar, text="Flashcards", command=self.open_flashcards).grid(row=0, column=2, padx=(6, 0))

    
        self.results = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        header = ttk.Frame(self.results)
        header.pack(fill="x")

        self._title_font = tkfont.nametofont("TkDefaultFont").copy()
        self._title_font.configure(size=14, weight="bold")
        self.title_var = tk.StringVar()
        ttk.Label(header, textvariable=self.title_var, font=self._title_font,
                  wraplength=250).pack(side="left")
        self.save_btn = ttk.Button(header, text="Save word", state="disabled",
                                   command=self.save_current)
        self.save_btn.pack(side="right")

        self.defs = DefinitionText(self.results)
        self.defs.pack(fill="both", expand=True, pady=(6, 0))

    
    def _initial_position(self):
        pos = storage.load_config().get("main_window", {})
        x, y = pos.get("x"), pos.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            return self.screen_w - WIDTH - CORNER_MARGIN, CORNER_MARGIN   # first run: top-right
        return x, max(0, y)

    def expand(self):
    
        x, y = window_xy(self.root)
        height = self.screen_h - y - BOTTOM_MARGIN
        if height < MIN_EXPANDED_H:         
            height = MIN_EXPANDED_H         
            y = max(0, self.screen_h - BOTTOM_MARGIN - height)
        self.root.geometry(f"{WIDTH}x{height}+{x}+{y}")
        self.results.pack(fill="both", expand=True)

    def collapse(self):
        x, y = window_xy(self.root)
        self.results.pack_forget()
        self.root.geometry(f"{WIDTH}x{COLLAPSED_H}+{x}+{y}")

    def on_close(self):
        x, y = window_xy(self.root)
        config = storage.load_config()
        config["main_window"] = {"x": x, "y": y}
        storage.save_config(config)
        self.root.destroy()

    
    def search(self, event=None):
        word = self.entry.get().strip().lower()
        if not word:
            return
        self._req += 1
        req_id = self._req

        self.current = None
        self.title_var.set(word)
        self.save_btn.config(text="Save word", state="disabled")
        self.defs.show_message("Looking up…")
        self.expand()
        self.entry.selection_range(0, "end")

        threading.Thread(target=self._worker, args=(req_id, word), daemon=True).start()

    def _worker(self, req_id, word):                     
        try:
            self.q.put((req_id, "ok", api.lookup(word)))
        except api.DictionaryError as e:
            self.q.put((req_id, "error", str(e)))
        except Exception as e:                           
            self.q.put((req_id, "error", f"Something went wrong: {e}"))

    def _poll(self):                                     
        try:
            while True:
                req_id, kind, payload = self.q.get_nowait()
                if req_id != self._req:                  
                    continue
                if kind == "ok":
                    self._show_entry(payload)
                else:
                    self.defs.show_message(payload, error=True)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _show_entry(self, entry):
        self.current = entry
        phonetic = f"   {entry['phonetic']}" if entry.get("phonetic") else ""
        self.title_var.set(entry["word"] + phonetic)
        self.defs.render(entry)
        if storage.is_saved(entry["word"]):
            self.save_btn.config(text="Saved ✓", state="disabled")
        else:
            self.save_btn.config(text="Save word", state="normal")

    
    
    
    def save_current(self):
        if not self.current:
            return
        storage.save_word(self.current)
        self.save_btn.config(text="Saved ✓", state="disabled")

    def open_flashcards(self):
        if self.flash and self.flash.win.winfo_exists():   
            self.flash.win.lift()
            return
        entry = storage.get_random_word()
        if entry is None:
            messagebox.showinfo("defineIt", "No saved words yet.\nSearch for a word and click “Save word” first.",
                                parent=self.root)
            return
        self.flash = FlashcardWindow(self.root, entry)