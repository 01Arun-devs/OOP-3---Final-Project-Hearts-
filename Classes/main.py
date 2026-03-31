# =============================================================================
# FILE:    main.py
# PURPOSE: Entry point. Run this file to start Hearts.
# AUTHOR:  Group 2 - COSC-2200-03
#
# HOW TO RUN:
#   1. Open Terminal
#   2. cd Desktop/Games   (or wherever your files are)
#   3. python3 main.py
#
# KEYBOARD SHORTCUTS:
#   Enter  = play first available card automatically
#   Escape = quit the game
# =============================================================================

import tkinter as tk
from gui import HeartsUI


def main():
    root = tk.Tk()
    HeartsUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
