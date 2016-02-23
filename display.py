import Tkinter as tk
import ttk
win = tk.Tk()

# Creating labels for sensor values to be displayed.
ttk.Label(win, text='Inside Temp:').grid(column=0, row=0)
ttk.Label(win, text='Inside Humidity:').grid(column=0, row=1)


win.title("Greenhouse Control")
win.mainloop()