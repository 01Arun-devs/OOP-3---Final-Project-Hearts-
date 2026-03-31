# =============================================================================
# FILE:    gui.py
# PURPOSE: Full graphical user interface for Hearts. Uses tkinter (built-in).
#          Designed like cardgames.io - players around a table.
# AUTHOR:  Group 2 - COSC-2200-03
# =============================================================================
# ACCESSIBILITY REQUIREMENTS MET:
#   - High contrast colours (white text on dark green)
#   - Tooltips on every card button (hover to see card name + point value)
#   - Enter key = play first valid card
#   - Escape key = quit with confirmation
#   - All buttons have clear labels
# CUSTOM CONTROL:
#   - CardButton: a custom styled button that shows a playing card
#     with suit symbol, colour-coded text, and tooltip
# =============================================================================

import tkinter as tk
from tkinter import messagebox
from logic import HeartsGame

# ── Colours ───────────────────────────────────────────────────────────────────
BG_DARK    = "#1b5e20"    # very dark green
BG_TABLE   = "#2e7d32"    # main table green
BG_FELT    = "#1b5e20"    # felt area
BG_SIDEBAR = "#f0f4f0"    # light sidebar
BG_LOG     = "#f9f9f9"    # log panel
BG_HAND    = "#1a1a2e"    # dark hand area
BG_CARD    = "#ffffff"    # card background
BG_VALID   = "#fffde7"    # valid card - warm yellow
BG_INVALID = "#e0e0e0"    # invalid card - grey
BG_TRICK   = "#ffffff"    # trick card box
BG_BTN     = "#4caf50"    # button green

FG_WHITE   = "#ffffff"
FG_DARK    = "#1a1a1a"
FG_GOLD    = "#f9a825"
FG_RED     = "#c62828"    # red suits
FG_MUTED   = "#546e7a"
FG_GREEN   = "#2e7d32"

FONT_TITLE  = ("Helvetica", 28, "bold")
FONT_HEAD   = ("Helvetica", 16, "bold")
FONT_BODY   = ("Helvetica", 13)
FONT_SMALL  = ("Helvetica", 11)
FONT_CARD   = ("Helvetica", 14, "bold")
FONT_SCORE  = ("Helvetica", 13)
FONT_STATUS = ("Helvetica", 11)
FONT_BTN    = ("Helvetica", 12, "bold")
FONT_LOG    = ("Helvetica", 10)


# =============================================================================
# TOOLTIP - shows info when mouse hovers over a widget
# =============================================================================
class Tooltip:
    """
    Shows a small popup when mouse hovers over a widget.
    Used on card buttons to show card name and point value.
    This satisfies the accessibility requirement for tooltips.
    """

    def __init__(self, widget, text):
        self.widget  = widget
        self.text    = text
        self.tip_win = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        """Display the tooltip near the widget."""
        if self.tip_win:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - 30
        self.tip_win = tk.Toplevel(self.widget)
        self.tip_win.wm_overrideredirect(True)
        self.tip_win.wm_geometry("+%d+%d" % (x, y))
        tk.Label(self.tip_win, text=self.text,
                 bg="#333333", fg=FG_WHITE,
                 font=FONT_SMALL,
                 padx=8, pady=4,
                 relief="flat").pack()

    def hide(self, event=None):
        """Remove the tooltip."""
        if self.tip_win:
            self.tip_win.destroy()
            self.tip_win = None


# =============================================================================
# CARD BUTTON - custom control for a playing card
# =============================================================================
class CardButton:
    """
    CUSTOM CONTROL - a styled button that looks like a playing card.
    Shows the card label with correct colour (red for hearts/diamonds).
    Has a tooltip showing the full card name and point value.
    Valid cards are highlighted in warm yellow; invalid are grey.

    This is the custom control required by the project specification.
    """

    def __init__(self, parent, card, is_valid, on_click):
        """
        parent   - the frame to put this button in
        card     - the Card object to display
        is_valid - True = player can click this card
        on_click - function to call when clicked
        """
        # Colour based on suit and validity
        if card.suit in ("H", "D"):
            text_colour = FG_RED
        else:
            text_colour = FG_DARK

        bg_colour = BG_VALID if is_valid else BG_INVALID
        state     = "normal" if is_valid else "disabled"

        # Build the button
        self.btn = tk.Button(
            parent,
            text=card.label(),
            font=FONT_CARD,
            width=4,
            height=2,
            bg=bg_colour,
            fg=text_colour,
            disabledforeground="#999999",
            relief="raised",
            bd=2,
            cursor="hand2" if is_valid else "arrow",
            state=state,
            command=lambda c=card.label(): on_click(c)
        )
        self.btn.pack(side="left", padx=3, pady=4)

        # Add tooltip with full card info
        Tooltip(self.btn, card.tooltip())

        # Gold border highlight on valid cards
        if is_valid:
            self.btn.config(highlightbackground=FG_GOLD, highlightthickness=2)


# =============================================================================
# MAIN GUI CLASS
# =============================================================================
class HeartsUI:
    """
    Main game window. Shows three screens:
      1. Main menu - start, rules, stats, exit
      2. Game table - the actual game
      Switching uses clear_screen() + build the new screen.
    """

    def __init__(self, root):
        self.root    = root
        self.root.title("Hearts Card Game — Group 2")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG_TABLE)

        self.game    = None
        self.screen  = None   # current frame shown

        # Keyboard shortcuts (accessibility requirement)
        self.root.bind("<Return>", self._key_enter)
        self.root.bind("<Escape>", self._key_esc)

        self.show_main_menu()

    # =========================================================================
    # SCREEN MANAGEMENT
    # =========================================================================

    def clear_screen(self):
        """Destroy the current screen frame."""
        if self.screen is not None:
            self.screen.destroy()
            self.screen = None

    # =========================================================================
    # MAIN MENU SCREEN
    # =========================================================================

    def show_main_menu(self):
        """Build the main menu screen."""
        self.clear_screen()
        self.screen = tk.Frame(self.root, bg=BG_TABLE)
        self.screen.pack(fill="both", expand=True)

        # Centre column
        col = tk.Frame(self.screen, bg=BG_TABLE)
        col.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(col, text="♥  HEARTS", font=FONT_TITLE,
                 bg=BG_TABLE, fg=FG_GOLD).pack(pady=(0, 8))
        tk.Label(col, text="4 Players  ·  1 Human vs 3 AI",
                 font=FONT_BODY, bg=BG_TABLE, fg=FG_WHITE).pack(pady=(0, 30))

        # Score limit choice
        tk.Label(col, text="Choose Score Limit:", font=("Helvetica", 13, "bold"),
                 bg=BG_TABLE, fg=FG_WHITE).pack(pady=(0, 8))

        self.score_limit_var = tk.IntVar(value=50)
        rb_row = tk.Frame(col, bg=BG_TABLE)
        rb_row.pack(pady=(0, 20))
        for val, txt in [(50, "50 Points  (shorter)"),
                         (100, "100 Points  (longer)")]:
            tk.Radiobutton(rb_row, text=txt,
                           variable=self.score_limit_var, value=val,
                           bg=BG_TABLE, fg=FG_WHITE,
                           selectcolor=BG_DARK,
                           activebackground=BG_TABLE,
                           font=FONT_BODY).pack(side="left", padx=16)

        # Buttons
        btn_w = 22
        tk.Button(col, text="Start Game", width=btn_w, height=2,
                  font=FONT_BTN,
                  command=self.start_game).pack(pady=8)

        tk.Button(col, text="Rules", width=btn_w, height=2,
                  font=FONT_BTN,
                  command=self.show_rules).pack(pady=8)

        tk.Button(col, text="My Statistics", width=btn_w, height=2,
                  font=FONT_BTN,
                  command=self.show_stats).pack(pady=8)

        tk.Button(col, text="Exit", width=btn_w, height=2,
                  font=FONT_BTN,
                  command=self.root.destroy).pack(pady=8)

        # Keyboard hint
        tk.Label(col, text="Tip: Enter = play card  ·  Esc = quit",
                 font=FONT_SMALL, bg=BG_TABLE, fg=FG_MUTED).pack(pady=(16, 0))

    def show_rules(self):
        """Show rules in a popup."""
        messagebox.showinfo("Hearts Rules",
            "HEARTS — How to Play\n\n"
            "Setup:\n"
            "  • 4 players, 52 cards, 13 each\n"
            "  • Player with 2♣ leads the first trick\n\n"
            "Playing:\n"
            "  • You must follow the lead suit if you can\n"
            "  • If you have no cards of that suit, play anything\n"
            "  • Hearts cannot lead until 'broken'\n"
            "  • Hearts break when someone plays a Heart\n\n"
            "Scoring:\n"
            "  • Each Heart = 1 penalty point\n"
            "  • Queen of Spades (Q♠) = 5 penalty points\n"
            "  • Lowest total score WINS\n\n"
            "Shoot the Moon:\n"
            "  • Collect ALL 13 Hearts + Q♠ (18 pts total)\n"
            "  • You score 0, everyone else gets +18!\n\n"
            "Game ends when someone reaches the score limit."
        )

    def show_stats(self):
        """Show lifetime stats popup."""
        game_temp = HeartsGame()
        stats = game_temp.stats_text()
        buttons_text = "Reset Statistics"

        result = messagebox.askokcancel("My Statistics",
            "Lifetime Statistics:\n\n" + stats + "\n\n"
            "Press OK to reset stats, Cancel to close.")
        if result:
            if messagebox.askyesno("Confirm Reset",
                                   "Are you sure you want to erase all stats?"):
                game_temp.reset_stats()
                messagebox.showinfo("Done", "Statistics have been reset.")

    # =========================================================================
    # START GAME
    # =========================================================================

    def start_game(self):
        """Create a new HeartsGame and show the game screen."""
        limit = self.score_limit_var.get()
        self.game = HeartsGame(score_limit=limit)
        self.show_game_screen()

    # =========================================================================
    # GAME SCREEN
    # =========================================================================

    def show_game_screen(self):
        """Build the main game table screen."""
        self.clear_screen()
        self.screen = tk.Frame(self.root, bg=BG_TABLE)
        self.screen.pack(fill="both", expand=True)

        # ── Top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self.screen, bg=BG_DARK, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="♥  HEARTS", font=("Helvetica", 16, "bold"),
                 bg=BG_DARK, fg=FG_GOLD).pack(side="left", padx=14)

        tk.Button(topbar, text="Main Menu",
                  font=FONT_SMALL, command=self.show_main_menu,
                  cursor="hand2").pack(side="right", padx=8, pady=10)
        tk.Button(topbar, text="New Game",
                  font=FONT_SMALL, command=self.start_game,
                  cursor="hand2").pack(side="right", padx=4, pady=10)

        self.turn_label = tk.Label(topbar, text="", font=("Helvetica", 13, "bold"),
                                   bg=BG_DARK, fg=FG_GOLD)
        self.turn_label.pack(side="left", padx=20)

        # ── Body row ─────────────────────────────────────────────────────────
        body = tk.Frame(self.screen, bg=BG_TABLE)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        # Score sidebar (left)
        self._build_score_panel(body)

        # Table area (centre)
        self._build_table(body)

        # Log panel (right)
        self._build_log_panel(body)

        # ── Bottom hand area ─────────────────────────────────────────────────
        self._build_hand_area()

        self.refresh_all()

    def _build_score_panel(self, parent):
        """Left sidebar with scores and game status."""
        panel = tk.Frame(parent, bg=BG_SIDEBAR, width=200,
                         bd=1, relief="groove")
        panel.pack(side="left", fill="y", padx=(0, 8))
        panel.pack_propagate(False)

        tk.Label(panel, text="Scores", font=FONT_HEAD,
                 bg=BG_SIDEBAR).pack(pady=(14, 8))

        # Score labels
        self.score_labels = {}
        for name in ["You", "AI 1", "AI 2", "AI 3"]:
            display = name + " ★" if name == "AI 2" else name
            lbl = tk.Label(panel, text=display + ": 0",
                           font=FONT_SCORE, bg=BG_SIDEBAR, anchor="w")
            lbl.pack(fill="x", padx=16, pady=4)
            self.score_labels[name] = lbl

        # Divider
        tk.Frame(panel, bg="#cccccc", height=1).pack(fill="x", padx=12, pady=8)

        # Status text
        self.status_lbl = tk.Label(panel, text="",
                                   font=FONT_STATUS, bg=BG_SIDEBAR,
                                   justify="left", anchor="w")
        self.status_lbl.pack(fill="x", padx=16, pady=4)

        # Round penalties
        tk.Frame(panel, bg="#cccccc", height=1).pack(fill="x", padx=12, pady=8)
        tk.Label(panel, text="This Round:", font=("Helvetica", 11, "bold"),
                 bg=BG_SIDEBAR).pack(anchor="w", padx=16)
        self.round_lbl = tk.Label(panel, text="",
                                  font=FONT_STATUS, bg=BG_SIDEBAR,
                                  justify="left", anchor="w")
        self.round_lbl.pack(fill="x", padx=16, pady=4)

        # Legend
        tk.Frame(panel, bg="#cccccc", height=1).pack(fill="x", padx=12, pady=8)
        tk.Label(panel, text="★ = Smart AI\n(tries Shoot the Moon)",
                 font=("Helvetica", 9), bg=BG_SIDEBAR,
                 fg=FG_MUTED, justify="left").pack(padx=16, anchor="w")

    def _build_table(self, parent):
        """Centre area with the game table."""
        centre = tk.Frame(parent, bg=BG_TABLE)
        centre.pack(side="left", fill="both", expand=True)

        # Table felt area
        self.table_frame = tk.Frame(centre, bg=BG_FELT,
                                    bd=4, relief="ridge")
        self.table_frame.pack(fill="both", expand=True,
                              padx=6, pady=6)

        # AI player name labels (fixed positions)
        tk.Label(self.table_frame, text="AI 2 ★",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_FELT, fg=FG_GOLD).place(relx=0.5, rely=0.06, anchor="center")

        tk.Label(self.table_frame, text="AI 1",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_FELT, fg=FG_WHITE).place(relx=0.15, rely=0.5, anchor="center")

        tk.Label(self.table_frame, text="AI 3",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_FELT, fg=FG_WHITE).place(relx=0.85, rely=0.5, anchor="center")

        tk.Label(self.table_frame, text="You",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_FELT, fg=FG_WHITE).place(relx=0.5, rely=0.9, anchor="center")

        # AI card count labels
        self.ai_count_labels = {}
        positions = {"AI 2": (0.5, 0.15), "AI 1": (0.15, 0.65),
                     "AI 3": (0.85, 0.65)}
        for name, pos in positions.items():
            lbl = tk.Label(self.table_frame, text="",
                           font=("Helvetica", 10),
                           bg=BG_FELT, fg=FG_WHITE)
            lbl.place(relx=pos[0], rely=pos[1], anchor="center")
            self.ai_count_labels[name] = lbl

        # Trick card boxes - one per player seat
        self.trick_labels = {}
        trick_positions = {
            "AI 2": (0.5,  0.28),
            "AI 1": (0.3,  0.52),
            "AI 3": (0.7,  0.52),
            "You":  (0.5,  0.72),
        }
        for name, pos in trick_positions.items():
            box = tk.Label(self.table_frame, text="--",
                           width=5, height=2,
                           font=("Helvetica", 18, "bold"),
                           bg=BG_TRICK, fg=FG_DARK,
                           relief="solid", bd=1)
            box.place(relx=pos[0], rely=pos[1], anchor="center")
            self.trick_labels[name] = box

        # Control buttons below table
        ctrl = tk.Frame(centre, bg=BG_TABLE)
        ctrl.pack(fill="x", pady=(0, 4))

        self.next_btn = tk.Button(ctrl, text="Next Round",
                                  font=FONT_SMALL,
                                  command=self.next_round,
                                  cursor="hand2")
        self.next_btn.pack(side="left", padx=6)

        tk.Button(ctrl, text="Show Valid Cards",
                  font=FONT_SMALL,
                  command=self.show_valid,
                  cursor="hand2").pack(side="left", padx=6)

        self.ctrl_msg = tk.Label(ctrl, text="",
                                 font=("Helvetica", 12, "bold"),
                                 bg=BG_TABLE, fg=FG_GOLD)
        self.ctrl_msg.pack(side="left", padx=12)

    def _build_log_panel(self, parent):
        """Right panel with scrolling game log."""
        log_frame = tk.Frame(parent, bg=BG_LOG, width=270,
                             bd=1, relief="groove")
        log_frame.pack(side="right", fill="y", padx=(8, 0))
        log_frame.pack_propagate(False)

        tk.Label(log_frame, text="Game Log",
                 font=FONT_HEAD, bg=BG_LOG).pack(pady=(10, 4))

        self.log_text = tk.Text(log_frame, wrap="word",
                                font=FONT_LOG, height=20,
                                state="disabled", relief="flat")
        scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 4))
        self.log_text.pack(fill="both", expand=True,
                           padx=(8, 0), pady=(0, 8))

    def _build_hand_area(self):
        """Bottom dark area showing the human player's cards."""
        hand_area = tk.Frame(self.screen, bg=BG_HAND, height=160)
        hand_area.pack(fill="x", side="bottom")
        hand_area.pack_propagate(False)

        tk.Label(hand_area, text="Your Hand",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_HAND, fg=FG_WHITE).pack(pady=(8, 2))

        self.cards_frame = tk.Frame(hand_area, bg=BG_HAND)
        self.cards_frame.pack(pady=4)

        self.hand_hint = tk.Label(hand_area,
                                  text="Click a highlighted card to play  ·  or press Enter",
                                  font=FONT_SMALL,
                                  bg=BG_HAND, fg=FG_MUTED)
        self.hand_hint.pack()

    # =========================================================================
    # REFRESH - updates everything on screen
    # =========================================================================

    def refresh_all(self):
        """Redraw the entire game screen to match current game state."""
        if self.game is None:
            return

        self._refresh_scores()
        self._refresh_table()
        self._refresh_hand()
        self._refresh_log()
        self._refresh_controls()

        # Game over check
        if self.game.game_over:
            self.root.after(300, self._show_game_over)

    def _refresh_scores(self):
        """Update score labels and status text."""
        for player in self.game.players:
            name = player.name
            pts  = self.game.total_scores[name]
            display = name + " ★" if name == "AI 2" else name

            lbl = self.score_labels[name]
            lbl.config(text=display + ": " + str(pts))

            # Red when approaching limit
            if pts >= self.game.score_limit * 0.75:
                lbl.config(fg="#c62828")
            elif name == "You":
                lbl.config(fg=FG_GREEN)
            else:
                lbl.config(fg=FG_DARK)

        self.status_lbl.config(text=self.game.status_text())

        # Round penalties
        rs = self.game.round_scores()
        lines = []
        for player in self.game.players:
            lines.append(player.name + ": " + str(rs[player.name]))
        self.round_lbl.config(text="\n".join(lines))

    def _refresh_table(self):
        """Update trick card boxes and AI card counts."""
        # Trick cards
        state = self.game.table_state()
        for name, lbl in self.trick_labels.items():
            text = state[name]
            lbl.config(text=text)
            # Colour trick card text by suit
            if len(text) >= 2 and text[-1] in ("♥", "♦"):
                lbl.config(fg=FG_RED)
            else:
                lbl.config(fg=FG_DARK)

        # AI card counts
        counts = {"AI 1": len(self.game.players[1].hand),
                  "AI 2": len(self.game.players[2].hand),
                  "AI 3": len(self.game.players[3].hand)}
        for name, lbl in self.ai_count_labels.items():
            n = counts[name]
            lbl.config(text=str(n) + " cards  " + ("🂠 " * min(n, 10)))

        # Update turn label in top bar
        turn = self.game.current_turn_name()
        if turn == "You":
            self.turn_label.config(text="▶  Your Turn")
        elif turn in ("Game Over", "Round Over"):
            self.turn_label.config(text=turn)
        else:
            self.turn_label.config(text=turn + " is thinking...")

    def _refresh_hand(self):
        """Rebuild the card buttons in the hand area."""
        # Clear old buttons
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        if self.game.round_over or self.game.game_over:
            return

        # Get valid cards
        is_your_turn = (self.game.current_turn_name() == "You")
        valid_labels = set()
        if is_your_turn:
            lead_suit = self.game.trick_cards[0][1].suit if self.game.trick_cards else None
            valid_labels = self.game.players[0].valid_labels(
                lead_suit, self.game.hearts_broken, self.game.first_trick)

        # Build a CardButton for each card
        for card in self.game.players[0].hand:
            is_valid = (card.label() in valid_labels)
            CardButton(self.cards_frame, card, is_valid, self.play_human_card)

    def _refresh_log(self):
        """Update the scrolling game log text."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        for line in self.game.message_log[-300:]:
            self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_controls(self):
        """Enable/disable Next Round button etc."""
        can_next = self.game.round_over and not self.game.game_over
        self.next_btn.config(state="normal" if can_next else "disabled")

        turn = self.game.current_turn_name()
        if turn == "You":
            self.ctrl_msg.config(text="Your turn — click a card or press Enter")
        elif self.game.round_over and not self.game.game_over:
            self.ctrl_msg.config(text="Round over — click Next Round")
        elif self.game.game_over:
            self.ctrl_msg.config(text="Game over!")
        else:
            self.ctrl_msg.config(text="")

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def play_human_card(self, card_label):
        """Called when human clicks a card button."""
        if self.game.current_turn_name() != "You":
            return
        ok, msg = self.game.human_play_by_label(card_label)
        if not ok:
            messagebox.showwarning("Invalid Move", msg)
        self.refresh_all()

    def next_round(self):
        """Start the next round."""
        if self.game.round_over and not self.game.game_over:
            self.game.start_new_round()
            self.refresh_all()

    def show_valid(self):
        """Show a popup listing valid cards."""
        if self.game.current_turn_name() != "You":
            messagebox.showinfo("Valid Cards", "Wait for your turn.")
            return
        lead_suit = self.game.trick_cards[0][1].suit if self.game.trick_cards else None
        valid_set = self.game.players[0].valid_labels(
            lead_suit, self.game.hearts_broken, self.game.first_trick)
        if valid_set:
            messagebox.showinfo("Valid Cards",
                                "You can play:\n" + ",  ".join(sorted(valid_set)))
        else:
            messagebox.showinfo("Valid Cards", "No valid cards.")

    def _show_game_over(self):
        """Show game over dialog."""
        scores = "\n".join(
            p.name + ":  " + str(self.game.total_scores[p.name]) + " pts"
            for p in self.game.players)

        play_again = messagebox.askyesno(
            "Game Over!",
            "GAME OVER!\n\n"
            "Winner: " + self.game.winner_text + "\n\n"
            "Final Scores:\n" + scores + "\n\n"
            "Play again?")

        if play_again:
            self.show_main_menu()

    # =========================================================================
    # KEYBOARD SHORTCUTS (accessibility requirement)
    # =========================================================================

    def _key_enter(self, event):
        """
        Enter key = automatically play the first valid card.
        Accessibility requirement: keyboard-friendly interface.
        """
        if self.game is None:
            return
        if self.game.current_turn_name() != "You":
            return
        if self.game.round_over or self.game.game_over:
            return
        lead_suit = self.game.trick_cards[0][1].suit if self.game.trick_cards else None
        valid = self.game.players[0].get_valid_cards(
            lead_suit, self.game.hearts_broken, self.game.first_trick)
        if valid:
            self.play_human_card(valid[0].label())

    def _key_esc(self, event):
        """
        Escape key = quit with confirmation.
        Accessibility requirement: default for Escape.
        """
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.root.destroy()

# =============================================================================
# CONCEPTS USED:
#   CardButton class:  custom reusable card control (project requirement)
#   Tooltip class:     accessibility - shows card info on hover
#   clear_screen():    simple screen switching by destroying/rebuilding frames
#   root.bind():       keyboard shortcuts (Enter/Esc) for accessibility
#   tk.Text widget:    scrolling game log panel
# =============================================================================