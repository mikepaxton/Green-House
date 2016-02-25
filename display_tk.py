from Tkinter import *
import ttk
import tkFont

root = Tk()

# Make it cover the entire screen
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.overrideredirect(1)
root.geometry("%dx%d+0+0" % (w, h))
root.focus_set()

myFont = tkFont.Font(family='Helvetica', size=18, weight='bold')

# Creating labels for sensor values to be displayed.
ttk.Label(root, text='Inside Temp:').grid(column=0, row=0)
ttk.Label(root, text='Inside Humidity:').grid(column=0, row=1)

def exitApp():
    root.destroy()

exitButton = Button(root, text='Exit', font=myFont, height=2, width=3, command=exitApp)
exitButton.pack(side=RIGHT, padx=10, pady=10, ipadx=10, ipady=10)
exitButton.bind('<Button-1>', quit)

root.mainloop()