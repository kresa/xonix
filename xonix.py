import tkinter as tk
from tkinter import BOTH

class XonixApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()
        self.bind("<Configure>", self.on_resize)
        self.pack(fill="both", expand=True)
        self.paint()
        self.master.resizable(True, True)
        
    def on_resize(self, event):
        print("OnResize")
        self.canvas.config(width = event.width, height = event.height)
        self.paint()

    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.pack(fill="both", expand=True)

    def paint(self):
        print(self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight())
        for x in range(0, self.canvas.winfo_reqwidth(), 10):
            self.canvas.create_line(x, 0, x, self.canvas.winfo_reqheight())
        for y in range(0, self.canvas.winfo_reqheight(), 10):
            self.canvas.create_line(0, y, self.canvas.winfo_reqwidth(), y)


root = tk.Tk()
app = XonixApplication(master=root)
app.mainloop()
