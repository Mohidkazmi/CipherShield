"""
main.py - Entry Point
======================
CipherShield | Information Security Project

Run this file to start the application.
"""

import tkinter as tk
from gui import CipherShieldApp

def main():
    # Initialize the Tkinter root window
    root = tk.Tk()
    
    # Create the application
    app = CipherShieldApp(root)
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()
