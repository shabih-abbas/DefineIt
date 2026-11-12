import tkinter as tk

import storage
from main_window import MainWindow


def main():
    storage.ensure_files()       
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()