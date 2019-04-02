import sys
from tkinter import *
from AtomicDatabase.eav_database import EAVDatabase

DB = EAVDatabase()
DB.load_examples()

def main(args=None):
    """Start up Atomic Database"""
    if args is None:
        args = sys.argv[1:]

    print("Starting up Atomic Database 2.0...")
    window = Tk()
    window.title("Atomic Database 2.0")

    split_panel = PanedWindow(window)
    split_panel.pack(fill=BOTH, expand=1)

    text1 = Text(m, height=15, width =15)
    m.add(text1)

    text2=Text(m, height=15, width=15)
    m.add(text2)

    return window

def run():
    main().mainloop()

if __name__ == "__main__":
    run()
