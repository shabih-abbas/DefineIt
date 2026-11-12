
import re
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def window_xy(win):

    nums = re.findall(r"-?\d+", win.geometry())
    return int(nums[2]), int(nums[3])


class DefinitionText(ttk.Frame):


    def __init__(self, parent):
        super().__init__(parent)
        base = tkfont.nametofont("TkDefaultFont")
        family, size = base.actual("family"), abs(base.actual("size"))

        self.text = tk.Text(
            self, wrap="word", state="disabled", relief="flat", borderwidth=0,
            highlightthickness=0, padx=6, pady=4, cursor="arrow", font=(family, size),
        )
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        t = self.text
        t.tag_configure("pos", font=(family, size + 1, "bold italic"),
                        foreground="#1a5fb4", spacing1=10, spacing3=3)
        # lmargin1 = first line, lmargin2 = wrapped lines -> hanging indent under "1."
        t.tag_configure("definition", lmargin1=8, lmargin2=26, spacing1=4)
        t.tag_configure("example", lmargin1=26, lmargin2=26,
                        foreground="#666666", font=(family, size, "italic"))
        t.tag_configure("message", foreground="#555555", spacing1=8)
        t.tag_configure("error", foreground="#b00020", spacing1=8)

    def _set(self, fill):
        t = self.text
        t.configure(state="normal")     
        t.delete("1.0", "end")
        fill(t)
        t.configure(state="disabled")
        t.yview_moveto(0)

    def show_message(self, message, error=False):
        self._set(lambda t: t.insert("end", message, "error" if error else "message"))

    def render(self, entry):
        meanings = entry.get("meanings") or []
        if not meanings:
            self.show_message("No definitions available.")
            return

        def fill(t):
            for meaning in meanings:
                t.insert("end", meaning["partOfSpeech"] + "\n", "pos")
                for i, d in enumerate(meaning["definitions"], 1):
                    t.insert("end", f"{i}. {d['definition']}\n", "definition")
                    if d.get("example"):
                        t.insert("end", f"“{d['example']}”\n", "example")

        self._set(fill)