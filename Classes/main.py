# =============================================================================
# FILE:    main.py
# PURPOSE: Entry point — run this file to start Hearts.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHOR:  ARUN — Integration + Game Controller
#
# HOW TO RUN:
#   1. Put all files in the same folder:
#        main.py  gui.py  login.py  logic.py  player.py  deck.py  card.py
#   2. Open Terminal / Command Prompt
#   3. Navigate: cd path/to/folder
#   4. Run:      python3 main.py
#
# REQUIREMENTS: Python 3.8+, tkinter, Pillow  (pip install pillow)
#
# KEYBOARD SHORTCUTS:
#   Enter  = submit login / start game / play first valid card
#   Escape = quit with confirmation
#   Tab    = move between login fields
# =============================================================================

import tkinter as tk
from login import LoginScreen
from gui   import HeartsUI


def main():
    """
    Start the app.
    1.  Show the Login / Sign-Up screen.
    2.  On success, hand the authenticated display_name to HeartsUI so
        the game's player-name field is pre-filled with the real username.
    """
    root = tk.Tk()
    root.title("Hearts  —  Group 2  |  COSC-2200-03")
    root.geometry("1280x860")
    root.minsize(1100, 780)
    root.configure(bg="#145220")

    def on_login(display_name: str):
        """Called by LoginScreen when the user authenticates successfully."""
        ui = HeartsUI(root)
        # Pre-fill the player-name field with the logged-in username
        if hasattr(ui, "name_var"):
            ui.name_var.set(display_name)

    LoginScreen(root, on_success=on_login)
    root.mainloop()


if __name__ == "__main__":
    main()
