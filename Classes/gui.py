# =============================================================================
# FILE:    gui.py
# PURPOSE: Hearts GUI — cardgames.io style with full animations.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHOR:  DARSH — GUI (Frontend)
#
# BUG FIXES:
#   1. Trick cards now stay visible until the win animation clears them.
#      _draw_table_bg() no longer touches trick card canvas items.
#   2. Played cards are tracked in self._trick_items dict — only cleared
#      deliberately during the win animation, not on every redraw.
#   3. Sidebar reduced to 160px, log panel to 180px, giving the canvas
#      more room. AI fan positions are computed from actual canvas size
#      with safe margins so nothing gets cut off.
# =============================================================================

import tkinter as tk
from tkinter import messagebox
import os, json, time

from PIL import Image, ImageTk, ImageDraw, ImageFont
from logic import HeartsGame

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, "cards")

# ── Palette ───────────────────────────────────────────────────────────────────
BG_FELT    = "#1a6b2a"
BG_TABLE   = "#145220"
BG_SIDEBAR = "#0f3d1a"
BG_HAND    = "#0d2e14"
BG_LOG     = "#0a2410"
FG_WHITE   = "#ffffff"
FG_GOLD    = "#ffc107"
FG_LIGHT   = "#a5d6a7"
FG_RED     = "#ef5350"
FG_MUTED   = "#66bb6a"

FONT_TITLE = ("Georgia",   24, "bold")
FONT_HEAD  = ("Helvetica", 12, "bold")
FONT_BODY  = ("Helvetica", 11)
FONT_SMALL = ("Helvetica",  9)
FONT_BTN   = ("Helvetica", 10, "bold")
FONT_LOG   = ("Helvetica",  9)
FONT_SCORE = ("Helvetica", 10)
FONT_NAME  = ("Helvetica", 10, "bold")

# Card sizes
CARD_W, CARD_H       = 95, 138
CARD_SM_W, CARD_SM_H = 66,  96
FAN_OFFSET = 20   # pixels between fanned AI cards

# Timing (all in milliseconds — tune here)
MS_AI_THINK   = 800   # AI "thinking" pause before playing
MS_FLY_STEP   = 14    # ms per animation frame
MS_FLIP_PAUSE = 300   # pause after card reveals its face
MS_TRICK_SHOW = 900   # all 4 cards visible before flying to winner
MS_WIN_FLY    = 500   # duration of cards flying to winner
MS_BANNER     = 700   # "X wins the trick!" banner duration
MS_NEXT_PLAY  = 150   # gap before next play begins


# =============================================================================
#  CARD IMAGE GENERATOR
# =============================================================================
def ensure_card_images():
    os.makedirs(CARDS_DIR, exist_ok=True)
    if len(os.listdir(CARDS_DIR)) >= 53:
        return

    FONT_PATH = None
    for f in ["C:/Windows/Fonts/arialbd.ttf",
              "C:/Windows/Fonts/verdanab.ttf",
              "C:/Windows/Fonts/calibrib.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if os.path.exists(f):
            FONT_PATH = f; break

    SUITS = ["C","D","H","S"]
    RANKS = [2,3,4,5,6,7,8,9,10,11,12,13,14]
    SYM   = {"C":"♣","D":"♦","H":"♥","S":"♠"}
    COL   = {"C":"#111111","D":"#cc0000","H":"#cc0000","S":"#111111"}
    RLBL  = {11:"J",12:"Q",13:"K",14:"A"}

    def rs(r): return RLBL.get(r, str(r))
    def fnt(sz):
        if FONT_PATH:
            try: return ImageFont.truetype(FONT_PATH, sz)
            except: pass
        return ImageFont.load_default()

    def make_card(suit, rank):
        W, H = CARD_W, CARD_H
        img = Image.new("RGB", (W, H), "#FFFFFF")
        d   = ImageDraw.Draw(img)
        col = COL[suit]; sym = SYM[suit]; r = rs(rank)
        # rounded border
        d.rounded_rectangle([0,0,W-1,H-1], radius=8, outline="#AAAAAA", width=2)
        d.rounded_rectangle([2,2,W-3,H-3], radius=7, fill="#FFFFFF")
        # top-left corner
        d.text((6, 4),  r,   font=fnt(17), fill=col)
        d.text((6, 22), sym, font=fnt(13), fill=col)
        # bottom-right corner
        bb = d.textbbox((0,0), r, font=fnt(13))
        tw = bb[2]-bb[0]
        d.text((W-tw-6, H-36), r,   font=fnt(13), fill=col)
        d.text((W-18,   H-21), sym, font=fnt(12), fill=col)
        # centre symbol
        bc = d.textbbox((0,0), sym, font=fnt(40))
        bw = bc[2]-bc[0]; bh = bc[3]-bc[1]
        d.text(((W-bw)//2, (H-bh)//2-4), sym, font=fnt(40), fill=col)
        d.rounded_rectangle([0,0,W-1,H-1], radius=8, outline="#CCCCCC", width=1)
        return img

    def make_back():
        W, H = CARD_W, CARD_H
        img = Image.new("RGB", (W,H), "#FFFFFF")
        d   = ImageDraw.Draw(img)
        d.rounded_rectangle([0,0,W-1,H-1], radius=8, fill="#FFFFFF", outline="#AAAAAA", width=2)
        d.rounded_rectangle([3,3,W-4,H-4], radius=6, fill="#1565C0")
        d.rounded_rectangle([7,7,W-8,H-8], radius=4, outline="#FFFFFF", width=2)
        for i in range(-H, W+H, 8):
            d.line([(i,0),(i+H,H)], fill="#1976D2", width=1)
        d.rounded_rectangle([7,7,W-8,H-8], radius=4, outline="#90CAF9", width=1)
        return img

    for suit in SUITS:
        for rank in RANKS:
            make_card(suit, rank).save(
                os.path.join(CARDS_DIR, rs(rank)+suit+".png"))
    make_back().save(os.path.join(CARDS_DIR, "back.png"))


# =============================================================================
#  IMAGE CACHE
# =============================================================================
class CardImages:
    RANK_LBL = {11:"J", 12:"Q", 13:"K", 14:"A"}

    def __init__(self):
        ensure_card_images()
        self._pil   = {}
        self._cache = {}
        for fname in os.listdir(CARDS_DIR):
            if fname.endswith(".png"):
                key = fname[:-4]
                try:
                    self._pil[key] = Image.open(
                        os.path.join(CARDS_DIR, fname)).convert("RGBA")
                except Exception:
                    pass

    def get(self, name, w=CARD_W, h=CARD_H):
        k = (name, w, h)
        if k not in self._cache:
            pil = self._pil.get(name, Image.new("RGBA",(w,h),(80,80,80,255)))
            self._cache[k] = ImageTk.PhotoImage(pil.resize((w,h), Image.LANCZOS))
        return self._cache[k]

    def get_squeezed(self, name, squeeze, w=CARD_W, h=CARD_H):
        """Horizontally squeezed card for flip animation."""
        new_w = max(2, int(w * squeeze))
        k = (name, "sq", new_w, h)
        if k not in self._cache:
            pil = self._pil.get(name, Image.new("RGBA",(w,h),(80,80,80,255)))
            self._cache[k] = ImageTk.PhotoImage(pil.resize((new_w,h), Image.LANCZOS))
        return self._cache[k]

    def card_name(self, card):
        return self.RANK_LBL.get(card.rank, str(card.rank)) + card.suit

    def get_card(self, card, w=CARD_W, h=CARD_H):
        return self.get(self.card_name(card), w, h)

    def get_back(self, w=CARD_W, h=CARD_H):
        return self.get("back", w, h)

    def label_to_name(self, label):
        sym = {"♣":"C","♦":"D","♥":"H","♠":"S"}
        if not label or label == "--":
            return None
        s = sym.get(label[-1])
        return (label[:-1] + s) if s else None


# =============================================================================
#  TOOLTIP
# =============================================================================
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget; self.text = text; self.win = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, e=None):
        if self.win: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() - 34
        self.win = tk.Toplevel(self.widget)
        self.win.wm_overrideredirect(True)
        self.win.wm_geometry("+%d+%d" % (x, y))
        tk.Label(self.win, text=self.text, bg="#333333", fg=FG_WHITE,
                 font=FONT_SMALL, padx=8, pady=3).pack()

    def hide(self, e=None):
        if self.win:
            self.win.destroy(); self.win = None


# =============================================================================
#  MAIN UI CLASS
# =============================================================================
class HeartsUI:

    def __init__(self, root):
        self.root   = root
        self.root.title("Hearts  —  Group 2  |  COSC-2200-03")
        self.root.geometry("1280x860")
        self.root.minsize(1100, 780)
        self.root.configure(bg=BG_TABLE)

        self.game         = None
        self.screen       = None
        self.images       = CardImages()
        self._refs        = []       # keep PhotoImages alive
        self._busy        = False    # True while any animation runs
        self._paused      = False    # True when game is paused
        # FIX 1 & 2: track canvas item IDs for trick cards separately
        # key = player_name, value = canvas item id of the face-up trick card
        self._trick_items = {}

        self.root.bind("<Return>", self._key_enter)
        self.root.bind("<Escape>", self._key_esc)
        self.root.bind("<space>",  self._key_space)
        self.show_main_menu()

    # ── helpers ───────────────────────────────────────────────────────────────
    def clear_screen(self):
        if self.screen:
            self.screen.destroy()
            self.screen = None
        self._refs.clear()
        self._trick_items.clear()

    def _k(self, img):
        self._refs.append(img)
        return img

    # ── geometry helpers (based on live canvas size) ──────────────────────────
    def _canvas_size(self):
        cv = self.canvas
        W  = cv.winfo_width()  or 700
        H  = cv.winfo_height() or 480
        return W, H

    def _seat_coords(self):
        """Pixel centre of each player's seat on the canvas."""
        W, H = self._canvas_size()
        cx, cy = W//2, H//2
        return {
            self.game.player_name:     (cx,    H - 20),   # bottom
            self.game.players[1].name: (80,    cy),        # left
            self.game.players[2].name: (cx,    24),        # top
            self.game.players[3].name: (W-80,  cy),        # right
        }

    def _trick_slot(self, pname):
        """Centre-table position where each player's trick card lands."""
        W, H = self._canvas_size()
        cx, cy = W//2, H//2
        G = CARD_W//2 + 18   # gap from centre
        return {
            self.game.player_name:     (cx,    cy + G),
            self.game.players[1].name: (cx-G,  cy),
            self.game.players[2].name: (cx,    cy - G),
            self.game.players[3].name: (cx+G,  cy),
        }.get(pname, (cx, cy))

    # =========================================================================
    #  MAIN MENU
    # =========================================================================
    def show_main_menu(self):
        self.clear_screen()
        self.game   = None
        self.screen = tk.Frame(self.root, bg=BG_TABLE)
        self.screen.pack(fill="both", expand=True)

        col = tk.Frame(self.screen, bg=BG_TABLE)
        col.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(col, text="♥  HEARTS", font=FONT_TITLE,
                 bg=BG_TABLE, fg=FG_GOLD).pack(pady=(0,6))
        tk.Label(col, text="4 Players  ·  1 Human vs 3 AI",
                 font=FONT_BODY, bg=BG_TABLE, fg=FG_LIGHT).pack(pady=(0,22))

        # Player name
        tk.Label(col, text="Your Name:",
                 font=("Helvetica",11,"bold"), bg=BG_TABLE, fg=FG_WHITE).pack(pady=(0,4))
        self.name_var = tk.StringVar(value="Player")
        e = tk.Entry(col, textvariable=self.name_var, font=FONT_BODY,
                     width=20, justify="center", relief="flat", bd=4)
        e.pack(pady=(0,14))
        e.focus_set()
        e.select_range(0, "end")

        # Score limit
        tk.Label(col, text="Score Limit:",
                 font=("Helvetica",11,"bold"), bg=BG_TABLE, fg=FG_WHITE).pack(pady=(0,5))
        self.score_limit_var = tk.IntVar(value=50)
        rb = tk.Frame(col, bg=BG_TABLE)
        rb.pack(pady=(0,18))
        for v, t in [(50,"50 pts  (shorter)"), (100,"100 pts  (longer)")]:
            tk.Radiobutton(rb, text=t, variable=self.score_limit_var, value=v,
                           bg=BG_TABLE, fg=FG_WHITE, selectcolor=BG_TABLE,
                           activebackground=BG_TABLE,
                           font=FONT_BODY).pack(side="left", padx=16)

        bs = dict(width=20, height=2, font=FONT_BTN, bg="#2e7d32", fg=FG_WHITE,
                  activebackground="#388e3c", relief="flat", cursor="hand2")
        tk.Button(col, text="▶  Start Game",  command=self.start_game,    **bs).pack(pady=5)
        tk.Button(col, text="📋  Rules",       command=self.show_rules,    **bs).pack(pady=5)
        tk.Button(col, text="📊  Statistics",  command=self.show_stats,    **bs).pack(pady=5)
        tk.Button(col, text="✕  Exit",         command=self.root.destroy,  **bs).pack(pady=5)
        tk.Label(col, text="Enter = Start  ·  Esc = Quit",
                 font=FONT_SMALL, bg=BG_TABLE, fg=FG_MUTED).pack(pady=(10,0))

    def show_rules(self):
        messagebox.showinfo("Hearts — How to Play",
            "HEARTS  |  Group 2  |  COSC-2200-03\n\n"
            "SETUP:\n"
            "  • 4 players, 52 cards, 13 each\n"
            "  • Player with 2♣ leads trick 1\n"
            "  • Dealer rotates clockwise each round\n\n"
            "PLAYING:\n"
            "  • Must follow lead suit if you can\n"
            "  • No matching suit? Play anything\n"
            "  • Hearts can't lead until broken\n\n"
            "SCORING:\n"
            "  • Each Heart = 1 pt   ·   Q♠ = 5 pts\n"
            "  • Lowest total score WINS\n\n"
            "SHOOT THE MOON:\n"
            "  • Collect ALL Hearts + Q♠ (18 pts total)\n"
            "  • You score 0 — everyone else gets +18!\n\n"
            "KEYBOARD:\n"
            "  • Enter = auto-play first valid card\n"
            "  • Esc   = quit")

    def show_stats(self):
        sf = HeartsGame.STATS_FILE
        if os.path.exists(sf):
            try:
                with open(sf,"r",encoding="utf-8") as f:
                    s = json.load(f)
                txt = ("Player    : " + s.get("last_player","—")      + "\n"
                       "Played    : " + str(s.get("games_played",0))  + "\n"
                       "Won       : " + str(s.get("games_won",0))     + "\n"
                       "Lost      : " + str(s.get("games_lost",0))    + "\n"
                       "Best score: " + str(s.get("best_score","—")))
            except Exception:
                txt = "Could not read statistics."
        else:
            txt = "No stats yet. Play a full game first."
        if messagebox.askokcancel("Statistics",
                "Lifetime Statistics:\n\n" + txt +
                "\n\nOK = reset all stats  ·  Cancel = close"):
            if messagebox.askyesno("Confirm", "Erase all statistics?"):
                if os.path.exists(sf):
                    os.remove(sf)
                messagebox.showinfo("Done", "Statistics reset.")

    # =========================================================================
    #  START GAME  →  shuffle animation  →  deal animation  →  game screen
    # =========================================================================
    def start_game(self):
        raw   = self.name_var.get().strip()
        pname = raw if raw else "Player"
        limit = self.score_limit_var.get()
        self.game = HeartsGame(player_name=pname, score_limit=limit)
        self._run_shuffle_deal(on_done=self.show_game_screen)

    # ── Shuffle + Deal animation ──────────────────────────────────────────────
    def _run_shuffle_deal(self, on_done):
        self.clear_screen()
        self.screen = tk.Frame(self.root, bg=BG_TABLE)
        self.screen.pack(fill="both", expand=True)

        cv = tk.Canvas(self.screen, bg=BG_FELT, highlightthickness=0)
        cv.pack(fill="both", expand=True)
        self.screen.update_idletasks()
        W = cv.winfo_width()  or 1100
        H = cv.winfo_height() or 680
        cx, cy = W//2, H//2

        back_lg = self.images.get_back(CARD_W, CARD_H)
        back_sm = self.images.get_back(CARD_SM_W, CARD_SM_H)
        self._k(back_lg); self._k(back_sm)

        sid = cv.create_text(cx, cy + CARD_H//2 + 40, text="Shuffling…",
                             font=("Helvetica",18,"bold"),
                             fill=FG_GOLD, anchor="center")

        # Stacked deck
        deck_ids = []
        for i in range(14):
            iid = cv.create_image(cx - i + 6, cy - i,
                                  image=back_lg, anchor="center")
            deck_ids.append(iid)
        cv.update(); time.sleep(0.2)

        # Shuffle bounce
        half = len(deck_ids)//2
        lp = deck_ids[:half]; rp = deck_ids[half:]
        for _ in range(7):
            for iid in lp: cv.move(iid, -44, 0)
            for iid in rp: cv.move(iid,  44, 0)
            cv.update(); time.sleep(0.07)
            for iid in lp: cv.move(iid,  44, 0)
            for iid in rp: cv.move(iid, -44, 0)
            cv.update(); time.sleep(0.07)
        time.sleep(0.2)

        cv.itemconfig(sid, text="Dealing…"); cv.update(); time.sleep(0.15)

        # Deal: cards fly to 4 seats
        #   seat 0 = top (AI 2), seat 1 = right (AI 3),
        #   seat 2 = bottom (Human), seat 3 = left (AI 1)
        seats  = [(cx, 60), (W-80, cy), (cx, H-60), (80, cy)]
        counts = [0, 0, 0, 0]
        for card_num in range(52):
            si = card_num % 4
            tx, ty = seats[si]
            c = counts[si]
            if si == 0:   tx = tx - (12-c)*7 + c*7      # top: horizontal fan
            elif si == 2: tx = tx - (12-c)*8 + c*8      # bottom: horizontal fan
            elif si == 3: ty = ty - (12-c)*5 + c*5      # left: vertical fan
            elif si == 1: ty = ty - (12-c)*5 + c*5      # right: vertical fan

            fly = cv.create_image(cx, cy, image=back_sm, anchor="center")
            STEPS = 10
            dx = (tx - cx) / STEPS
            dy = (ty - cy) / STEPS
            for _ in range(STEPS):
                cv.move(fly, dx, dy)
                cv.update()
            counts[si] += 1
            if card_num % 4 == 3:
                time.sleep(0.04)

        cv.itemconfig(sid, text="Ready!"); cv.update(); time.sleep(0.45)
        on_done()

    # =========================================================================
    #  GAME SCREEN
    # =========================================================================
    def show_game_screen(self):
        self.clear_screen()
        self._busy   = False
        self._paused = False
        self._trick_items.clear()

        self.screen = tk.Frame(self.root, bg=BG_TABLE)
        self.screen.pack(fill="both", expand=True)

        # FIX 3: narrower sidebar and log panel so canvas gets enough width
        left = tk.Frame(self.screen, bg=BG_SIDEBAR, width=160)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(self.screen, bg=BG_LOG, width=180)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        centre = tk.Frame(self.screen, bg=BG_TABLE)
        centre.pack(side="left", fill="both", expand=True)

        self._build_sidebar(left)
        self._build_log_panel(right)
        self._build_centre(centre)

        # _busy must be False before refresh so valid cards highlight immediately
        self._busy = False
        self.refresh_all()
        self.root.after(400, self._game_step)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, p):
        tk.Label(p, text="♥ HEARTS", font=("Helvetica",12,"bold"),
                 bg=BG_SIDEBAR, fg=FG_GOLD).pack(pady=(12,3))
        tk.Label(p, text="Scores", font=FONT_HEAD,
                 bg=BG_SIDEBAR, fg=FG_LIGHT).pack(pady=(4,3))

        self.score_labels = {}
        for pl in self.game.players:
            n = pl.name
            d = n + " ★" if n == "AI 2" else n
            row = tk.Frame(p, bg=BG_SIDEBAR)
            row.pack(fill="x", padx=6, pady=2)
            tk.Label(row, text=d, font=FONT_SCORE,
                     bg=BG_SIDEBAR, fg=FG_WHITE, anchor="w").pack(side="left")
            v = tk.Label(row, text="0", font=FONT_SCORE,
                         bg=BG_SIDEBAR, fg=FG_GOLD, anchor="e")
            v.pack(side="right")
            self.score_labels[n] = v

        tk.Frame(p, bg="#2e5c36", height=1).pack(fill="x", padx=6, pady=6)

        self.status_lbl = tk.Label(p, text="", font=FONT_SMALL,
                                   bg=BG_SIDEBAR, fg=FG_LIGHT,
                                   justify="left", anchor="w")
        self.status_lbl.pack(fill="x", padx=8, pady=2)

        tk.Frame(p, bg="#2e5c36", height=1).pack(fill="x", padx=6, pady=6)
        tk.Label(p, text="This Round:", font=FONT_SMALL,
                 bg=BG_SIDEBAR, fg=FG_LIGHT).pack(anchor="w", padx=8)

        self.rnd_labels = {}
        for pl in self.game.players:
            row = tk.Frame(p, bg=BG_SIDEBAR)
            row.pack(fill="x", padx=6, pady=1)
            tk.Label(row, text=pl.name, font=FONT_SMALL,
                     bg=BG_SIDEBAR, fg=FG_WHITE, anchor="w").pack(side="left")
            v = tk.Label(row, text="0", font=FONT_SMALL,
                         bg=BG_SIDEBAR, fg=FG_GOLD, anchor="e")
            v.pack(side="right")
            self.rnd_labels[pl.name] = v

        tk.Frame(p, bg="#2e5c36", height=1).pack(fill="x", padx=6, pady=6)
        tk.Label(p, text="★ Smart AI\nShoots the Moon",
                 font=("Helvetica",7), bg=BG_SIDEBAR,
                 fg=FG_MUTED, justify="left").pack(padx=8, anchor="w")

        tk.Frame(p, bg="#2e5c36", height=1).pack(fill="x", padx=6, pady=6)
        bs = dict(font=FONT_SMALL, bg="#1b5e20", fg=FG_WHITE,
                  activebackground="#2e7d32", relief="flat",
                  cursor="hand2", width=16)
        tk.Button(p, text="New Game",
                  command=self._new_game, **bs).pack(pady=3, padx=6)
        tk.Button(p, text="Main Menu",
                  command=self.show_main_menu, **bs).pack(pady=3, padx=6)
        tk.Button(p, text="Valid Cards",
                  command=self.show_valid, **bs).pack(pady=3, padx=6)

    def _build_log_panel(self, p):
        tk.Label(p, text="Game Log", font=FONT_HEAD,
                 bg=BG_LOG, fg=FG_LIGHT).pack(pady=(10,3))
        self.log_text = tk.Text(p, wrap="word", font=FONT_LOG,
                                bg="#0a2410", fg="#c8e6c9",
                                state="disabled", relief="flat")
        sb = tk.Scrollbar(p, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True, padx=3, pady=(0,6))

    def _build_centre(self, p):
        # Bottom control bar
        ctrl = tk.Frame(p, bg=BG_TABLE, height=36)
        ctrl.pack(fill="x", side="bottom")
        ctrl.pack_propagate(False)

        self.next_btn = tk.Button(ctrl, text="Next Round ▶",
                                  font=FONT_SMALL, bg="#1565C0", fg=FG_WHITE,
                                  activebackground="#1976D2", relief="flat",
                                  cursor="hand2", command=self.next_round)
        self.next_btn.pack(side="left", padx=8, pady=4)

        self.pause_btn = tk.Button(ctrl, text="⏸  Pause",
                                   font=FONT_SMALL, bg="#e65100", fg=FG_WHITE,
                                   activebackground="#bf360c", relief="flat",
                                   cursor="hand2", width=9,
                                   command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=4, pady=4)

        self.ctrl_msg = tk.Label(ctrl, text="",
                                 font=("Helvetica",10,"bold"),
                                 bg=BG_TABLE, fg=FG_GOLD)
        self.ctrl_msg.pack(side="left", padx=6)

        self.hearts_lbl = tk.Label(ctrl, text="", font=FONT_SMALL,
                                   bg=BG_TABLE, fg=FG_RED)
        self.hearts_lbl.pack(side="right", padx=10)

        # Hand strip — fixed height
        self.hand_strip = tk.Frame(p, bg=BG_HAND, height=168)
        self.hand_strip.pack(fill="x", side="bottom")
        self.hand_strip.pack_propagate(False)

        tk.Label(self.hand_strip,
                 text=self.game.player_name + "'s Hand",
                 font=FONT_HEAD, bg=BG_HAND, fg=FG_GOLD).pack(pady=(5,1))
        self.cards_frame = tk.Frame(self.hand_strip, bg=BG_HAND)
        self.cards_frame.pack()
        tk.Label(self.hand_strip,
                 text="Click a highlighted card  ·  Enter = auto-play",
                 font=FONT_SMALL, bg=BG_HAND, fg=FG_MUTED).pack(pady=(2,0))

        # Canvas — gets all remaining space
        self.canvas = tk.Canvas(p, bg=BG_FELT, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_table_bg())

    # =========================================================================
    #  ANIMATED GAME LOOP
    # =========================================================================
    def _game_step(self):
        if (not self.game or self.game.game_over
                or self.game.round_over or self._busy or self._paused):
            return
        turn = self.game.current_turn_name()
        if turn == self.game.player_name:
            return   # waiting for human click
        # AI's turn
        self._busy = True
        self.ctrl_msg.config(text=turn + " is thinking…")
        self.root.after(MS_AI_THINK, self._ai_play)

    def _ai_play(self):
        if not self.game or self.game.game_over or self.game.round_over:
            self._busy = False; return
        # If paused while AI was "thinking", release busy and stop
        if self._paused:
            self._busy = False; return
        player_index = self.game.current_index
        card = self.game.ai_choose_card()
        self._animate_play(player_index, card, on_done=self._after_any_play)

    def _after_any_play(self, player_index, card):
        """Called after each card finishes its fly+flip animation."""
        result = self.game.resolve_trick_if_done()
        self._refresh_scores()
        self._refresh_log()
        # FIX 1: only redraw the background oval + AI fans, NOT trick cards
        self._draw_table_bg()

        if result == "continue":
            self._busy = False          # must be False BEFORE building buttons
            self._build_hand_buttons()  # so valid cards get highlighted
            self._refresh_controls()
            self.root.after(MS_NEXT_PLAY, self._game_step)

        elif result == "trick_done":
            # FIX 2: trick cards stay on canvas — wait, then animate win
            self.root.after(MS_TRICK_SHOW, self._animate_trick_win)

        else:  # round_done
            self.root.after(MS_TRICK_SHOW, self._on_round_done)

    # ── Fly + flip animation ──────────────────────────────────────────────────
    def _animate_play(self, player_index, card, on_done):
        """
        Fly card face-down from seat → trick slot, then flip to show face.
        The face-up card stays on the canvas in self._trick_items[pname].
        """
        ok, msg = self.game.play_card(player_index, card)
        if not ok:
            self._busy = False; return

        pname = self.game.players[player_index].name
        sx, sy = self._seat_coords()[pname]
        tx, ty = self._trick_slot(pname)

        back_img = self.images.get_back(CARD_W, CARD_H)
        self._k(back_img)

        cv = self.canvas
        fly_id = cv.create_image(sx, sy, image=back_img, anchor="center")
        cv.tag_raise(fly_id)

        STEPS = 20
        dx = (tx - sx) / STEPS
        dy = (ty - sy) / STEPS

        def do_fly(step=0):
            if step < STEPS:
                cv.move(fly_id, dx, dy)
                self.root.after(MS_FLY_STEP, lambda: do_fly(step+1))
            else:
                cv.delete(fly_id)
                do_flip(phase=0)

        def do_flip(phase=0):
            FLIP_STEPS = 7
            tag = "flip_" + pname

            if phase < FLIP_STEPS:
                # Squeeze back → 0 width
                squeeze = 1.0 - (phase / FLIP_STEPS)
                img = self.images.get_squeezed("back", squeeze, CARD_W, CARD_H)
                self._k(img)
                cv.delete(tag)
                cv.create_image(tx, ty, image=img, anchor="center", tags=tag)
                self.root.after(MS_FLY_STEP,
                                lambda: do_flip(phase+1))

            elif phase < FLIP_STEPS * 2:
                # Expand face → full width
                p2 = phase - FLIP_STEPS
                squeeze = p2 / FLIP_STEPS
                cname = self.images.card_name(card)
                img = self.images.get_squeezed(cname, squeeze, CARD_W, CARD_H)
                self._k(img)
                cv.delete(tag)
                cv.create_image(tx, ty, image=img, anchor="center", tags=tag)
                self.root.after(MS_FLY_STEP,
                                lambda: do_flip(phase+1))

            else:
                # Flip complete — place permanent face-up card
                cv.delete(tag)
                face_img = self.images.get_card(card, CARD_W, CARD_H)
                self._k(face_img)
                # FIX 2: delete previous card at this slot (if re-played)
                if pname in self._trick_items:
                    cv.delete(self._trick_items[pname])
                item_id = cv.create_image(tx, ty, image=face_img,
                                          anchor="center")
                self._trick_items[pname] = item_id
                self.root.after(MS_FLIP_PAUSE,
                                lambda: on_done(player_index, card))

        do_fly()

    # ── Trick win animation ───────────────────────────────────────────────────
    def _animate_trick_win(self):
        """All 4 face-up cards fly together to the winner's seat."""
        wi    = self.game.trick_winner_index
        wname = self.game.players[wi].name
        wx, wy = self._seat_coords()[wname]
        cv = self.canvas

        # Gather existing canvas items (face-up trick cards)
        fly_list = []
        for idx, card in self.game.last_trick_cards:
            pn = self.game.players[idx].name
            iid = self._trick_items.pop(pn, None)
            if iid is not None:
                tx, ty = self._trick_slot(pn)
                fly_list.append((iid, tx, ty))

        if not fly_list:
            self._after_trick_win(None); return

        STEPS = 22
        step_ms = MS_WIN_FLY // STEPS

        def fly_all(step=0):
            if step < STEPS:
                for iid, ox, oy in fly_list:
                    dx = (wx - ox) / STEPS
                    dy = (wy - oy) / STEPS
                    cv.move(iid, dx, dy)
                self.root.after(step_ms, lambda: fly_all(step+1))
            else:
                for iid, _, _ in fly_list:
                    cv.delete(iid)
                # Winner banner
                W, H = self._canvas_size()
                bid = cv.create_text(
                    W//2, H//2,
                    text=wname + " wins the trick!",
                    font=("Helvetica", 15, "bold"),
                    fill=FG_GOLD, anchor="center")
                self.root.after(MS_BANNER, lambda: self._after_trick_win(bid))

        fly_all()

    def _after_trick_win(self, banner_id):
        if banner_id is not None:
            self.canvas.delete(banner_id)
        self._busy = False              # reset BEFORE rebuilding buttons
        self._draw_table_bg()
        self._build_hand_buttons()
        self._refresh_controls()
        self.root.after(MS_NEXT_PLAY, self._game_step)

    def _on_round_done(self):
        # Clear any remaining trick items
        for iid in self._trick_items.values():
            self.canvas.delete(iid)
        self._trick_items.clear()
        self._draw_table_bg()
        self._build_hand_buttons()
        self._refresh_scores()
        self._refresh_controls()
        self._refresh_log()
        self._busy = False
        if self.game.game_over:
            self.root.after(700, self._show_game_over)

    # =========================================================================
    #  PAUSE / RESUME
    # =========================================================================
    def toggle_pause(self):
        """Toggle the paused state. Works at any point during the game."""
        if not self.game or self.game.game_over:
            return

        self._paused = not self._paused

        if self._paused:
            # Update button to show Resume
            self.pause_btn.config(text="▶  Resume", bg="#2e7d32",
                                  activebackground="#388e3c")
            self._show_pause_overlay()
            # Also block human from clicking cards
            for w in self.cards_frame.winfo_children():
                try: w.config(state="disabled")
                except Exception: pass
        else:
            # Update button back to Pause
            self.pause_btn.config(text="⏸  Pause", bg="#e65100",
                                  activebackground="#bf360c")
            self._hide_pause_overlay()
            # Rebuild hand buttons so valid cards are re-enabled
            self._build_hand_buttons()
            self._refresh_controls()
            # Restart the AI game loop if it's an AI's turn
            self.root.after(200, self._game_step)

    def _show_pause_overlay(self):
        """Draw a semi-transparent overlay on the canvas with PAUSED text."""
        cv = self.canvas
        W, H = self._canvas_size()
        # Dark semi-transparent rectangle across the whole canvas
        self._pause_overlay_ids = []
        # Simulate transparency with a dark rectangle + text
        rid = cv.create_rectangle(0, 0, W, H,
                                   fill="#000000", stipple="gray50",
                                   outline="", tags="pause_overlay")
        tid = cv.create_text(W//2, H//2 - 18,
                              text="⏸  PAUSED",
                              font=("Helvetica", 28, "bold"),
                              fill=FG_GOLD, anchor="center",
                              tags="pause_overlay")
        sid = cv.create_text(W//2, H//2 + 22,
                              text="Press  ▶ Resume  to continue",
                              font=("Helvetica", 13),
                              fill=FG_LIGHT, anchor="center",
                              tags="pause_overlay")
        self._pause_overlay_ids = [rid, tid, sid]

    def _hide_pause_overlay(self):
        """Remove the pause overlay from the canvas."""
        self.canvas.delete("pause_overlay")
        self._pause_overlay_ids = []

    # =========================================================================
    #  HUMAN PLAYS
    # =========================================================================
    def play_human_card(self, label):
        if self._busy or self._paused:
            return
        if self.game.current_turn_name() != self.game.player_name:
            return
        card = next(
            (c for c in self.game.players[0].hand if c.label() == label),
            None)
        if card is None:
            return
        self._busy = True
        # Disable all hand buttons during animation
        for w in self.cards_frame.winfo_children():
            try: w.config(state="disabled")
            except Exception: pass
        self._animate_play(0, card, on_done=self._after_any_play)

    # =========================================================================
    #  DRAW TABLE BACKGROUND
    #  IMPORTANT: this only draws the felt oval, AI card fans, empty slots,
    #  and player labels. It never touches self._trick_items.
    # =========================================================================
    def _draw_table_bg(self):
        if not self.game:
            return
        cv = self.canvas
        # FIX 1: only delete items tagged "bg" — trick card items have no "bg" tag
        cv.delete("bg")
        W, H = self._canvas_size()
        if W < 50 or H < 50:
            return
        cx, cy = W//2, H//2
        G = CARD_W//2 + 18

        # Oval felt
        PAD = 22
        cv.create_oval(PAD, PAD, W-PAD, H-PAD,
                       fill="#1a7a2e", outline="#145220", width=7, tags="bg")
        cv.create_oval(PAD+9, PAD+9, W-PAD-9, H-PAD-9,
                       fill="", outline="#2e9c45", width=2, tags="bg")

        # Dashed empty trick slots — only for players who haven't played yet
        played_names = {self.game.players[i].name
                        for i, _ in self.game.trick_cards}
        slots = {
            self.game.player_name:     (cx,    cy+G),
            self.game.players[1].name: (cx-G,  cy),
            self.game.players[2].name: (cx,    cy-G),
            self.game.players[3].name: (cx+G,  cy),
        }
        for pname, (tx, ty) in slots.items():
            if pname not in played_names and pname not in self._trick_items:
                x0, y0 = tx - CARD_W//2, ty - CARD_H//2
                x1, y1 = tx + CARD_W//2, ty + CARD_H//2
                cv.create_rectangle(x0, y0, x1, y1,
                                    outline="#3a9c50", width=2,
                                    dash=(5,4), tags="bg")

        # FIX 3: AI fan positions use actual canvas width with safe margins
        # Top (AI 2) — horizontal fan
        ai2 = self.game.players[2]
        self._draw_fan_h(cv, ai2, cx, 20, W)

        # Left (AI 1) — vertical fan, safe x with margin
        ai1 = self.game.players[1]
        fan_x_left = max(CARD_SM_W//2 + 6, 72)
        self._draw_fan_v(cv, ai1, fan_x_left, cy, "left")

        # Right (AI 3) — vertical fan, safe x with margin
        ai3 = self.game.players[3]
        fan_x_right = min(W - CARD_SM_W//2 - 6, W - 72)
        self._draw_fan_v(cv, ai3, fan_x_right, cy, "right")

        # Player name at bottom
        cv.create_text(cx, H - 10,
                       text=self.game.player_name,
                       font=FONT_NAME, fill=FG_GOLD,
                       anchor="center", tags="bg")

        # Dealer badge
        cv.create_text(cx, cy + G + CARD_H//2 + 16,
                       text="Dealer: " + self.game.dealer_name(),
                       font=("Helvetica", 8), fill="#81c784",
                       anchor="center", tags="bg")

        # Turn indicator
        turn = self.game.current_turn_name()
        if turn == self.game.player_name:
            tt = "▶ Your turn!"
        elif turn in ("Round Over", "Game Over"):
            tt = turn
        else:
            tt = turn + " thinking…"
        cv.create_text(cx, cy + G + CARD_H//2 + 30,
                       text=tt, font=("Helvetica",9,"bold"),
                       fill=FG_GOLD, anchor="center", tags="bg")

        # Raise trick items above the background (so oval doesn't cover them)
        for iid in self._trick_items.values():
            cv.tag_raise(iid)

    def _draw_fan_h(self, cv, player, cx, top_y, canvas_w):
        n    = len(player.hand)
        show = min(n, 13)
        if show == 0:
            return
        back = self.images.get_back(CARD_SM_W, CARD_SM_H)
        self._k(back)
        total_w = (show - 1) * FAN_OFFSET + CARD_SM_W
        # Clamp fan so it doesn't overflow canvas edges
        sx = max(CARD_SM_W//2 + 4,
                 min(cx - total_w//2 + CARD_SM_W//2,
                     canvas_w - total_w + CARD_SM_W//2 - 4))
        fy = top_y + CARD_SM_H//2 + 6
        for i in range(show):
            cv.create_image(sx + i*FAN_OFFSET, fy,
                            image=back, anchor="center", tags="bg")
        is_s = (player.name == "AI 2")
        lbl  = player.name + " ★" if is_s else player.name
        cv.create_text(cx, fy + CARD_SM_H//2 + 13,
                       text=lbl + "  (" + str(n) + " cards)",
                       font=FONT_NAME,
                       fill=FG_GOLD if is_s else FG_WHITE,
                       anchor="center", tags="bg")

    def _draw_fan_v(self, cv, player, x, cy, side):
        n    = len(player.hand)
        show = min(n, 10)
        if show == 0:
            return
        back = self.images.get_back(CARD_SM_W, CARD_SM_H)
        self._k(back)
        VG      = 13
        total_h = (show - 1) * VG + CARD_SM_H
        sy      = cy - total_h//2 + CARD_SM_H//2
        for i in range(show):
            cv.create_image(x, sy + i*VG,
                            image=back, anchor="center", tags="bg")
        # Label positioned outside the fan, not cut off
        lbl_x  = x - CARD_SM_W//2 - 4 if side == "left" else x + CARD_SM_W//2 + 4
        anchor = "e" if side == "left" else "w"
        cv.create_text(lbl_x, sy + total_h//2 + 14,
                       text=player.name + "  (" + str(n) + ")",
                       font=FONT_NAME, fill=FG_WHITE,
                       anchor=anchor, tags="bg")

    # =========================================================================
    #  HUMAN HAND BUTTONS
    # =========================================================================
    def _build_hand_buttons(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        if self.game.round_over or self.game.game_over:
            return

        is_my_turn   = (self.game.current_turn_name() == self.game.player_name)
        valid_labels = set()
        # FIX 1: only highlight valid cards when it is actually the human's turn
        # AND no animation is running
        if is_my_turn and not self._busy:
            ls = (self.game.trick_cards[0][1].suit
                  if self.game.trick_cards else None)
            valid_labels = self.game.players[0].valid_labels(
                ls, self.game.hearts_broken, self.game.first_trick)

        for card in self.game.players[0].hand:
            valid   = card.label() in valid_labels
            img     = self.images.get_card(card, CARD_W, CARD_H)
            self._k(img)
            pad_top = 4  if valid else 18
            pad_bot = 18 if valid else 4

            btn = tk.Button(
                self.cards_frame,
                image=img,
                relief="flat", bd=0,
                bg=BG_HAND, activebackground=BG_HAND,
                cursor="hand2" if valid else "arrow",
                state="normal" if valid else "disabled",
                command=lambda lbl=card.label(): self.play_human_card(lbl)
            )
            btn.pack(side="left", padx=2, pady=(pad_top, pad_bot))

            if valid:
                btn.config(highlightbackground=FG_GOLD,
                           highlightthickness=3,
                           highlightcolor=FG_GOLD)
            Tooltip(btn, card.tooltip())

    # =========================================================================
    #  REFRESH
    # =========================================================================
    def refresh_all(self):
        if not self.game:
            return
        self._refresh_scores()
        self._draw_table_bg()
        self._build_hand_buttons()
        self._refresh_log()
        self._refresh_controls()

    def _refresh_scores(self):
        for pl in self.game.players:
            pts = self.game.total_scores[pl.name]
            lbl = self.score_labels[pl.name]
            lbl.config(text=str(pts),
                       fg="#ef5350" if pts >= self.game.score_limit*0.75
                       else FG_GOLD)
        self.status_lbl.config(text=self.game.status_text())
        rs = self.game.round_scores()
        for pl in self.game.players:
            self.rnd_labels[pl.name].config(text=str(rs[pl.name]))

    def _refresh_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        for line in self.game.message_log[-400:]:
            self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_controls(self):
        can_next = self.game.round_over and not self.game.game_over
        self.next_btn.config(state="normal" if can_next else "disabled")
        turn = self.game.current_turn_name()
        if turn == self.game.player_name and not self._busy:
            self.ctrl_msg.config(text="▶ Your turn — click a card")
        elif self.game.round_over and not self.game.game_over:
            self.ctrl_msg.config(text="Round over — click Next Round")
        elif self.game.game_over:
            self.ctrl_msg.config(text="Game over!")
        else:
            self.ctrl_msg.config(text="")
        hb = self.game.hearts_broken
        self.hearts_lbl.config(
            text="❤ Hearts Broken!" if hb else "Hearts not broken",
            fg=FG_RED if hb else FG_MUTED)

    # ── Actions ───────────────────────────────────────────────────────────────
    def next_round(self):
        if (self.game.round_over and not self.game.game_over
                and not self._busy):
            self._run_shuffle_deal(on_done=self._after_deal_new_round)

    def _after_deal_new_round(self):
        self.game.start_new_round()
        self.show_game_screen()

    def _new_game(self):
        raw   = self.name_var.get().strip() if hasattr(self,"name_var") else "Player"
        pname = raw if raw else "Player"
        limit = self.score_limit_var.get() if hasattr(self,"score_limit_var") else 50
        self.game = HeartsGame(player_name=pname, score_limit=limit)
        self._run_shuffle_deal(on_done=self.show_game_screen)

    def show_valid(self):
        if not self.game or self._busy:
            return
        if self.game.current_turn_name() != self.game.player_name:
            messagebox.showinfo("Valid Cards", "Wait for your turn.")
            return
        ls = (self.game.trick_cards[0][1].suit
              if self.game.trick_cards else None)
        vs = self.game.players[0].valid_labels(
            ls, self.game.hearts_broken, self.game.first_trick)
        if vs:
            messagebox.showinfo("Valid Cards",
                                "You can play:\n" + ",  ".join(sorted(vs)))
        else:
            messagebox.showinfo("Valid Cards", "No valid cards.")

    def _show_game_over(self):
        sc = "\n".join(
            p.name + ":  " + str(self.game.total_scores[p.name]) + " pts"
            for p in self.game.players)
        if messagebox.askyesno("Game Over!",
                "GAME OVER!\n\nWinner: " + self.game.winner_text +
                "\n\nFinal Scores:\n" + sc + "\n\nPlay again?"):
            self.show_main_menu()

    # ── Keyboard ──────────────────────────────────────────────────────────────
    def _key_enter(self, event):
        if self.game is None:
            self.start_game(); return
        if self._busy:
            return
        if self.game.round_over and not self.game.game_over:
            self.next_round(); return
        if self.game.game_over:
            return
        if self.game.current_turn_name() != self.game.player_name:
            return
        ls = (self.game.trick_cards[0][1].suit
              if self.game.trick_cards else None)
        valid = self.game.players[0].get_valid_cards(
            ls, self.game.hearts_broken, self.game.first_trick)
        if valid:
            self.play_human_card(valid[0].label())

    def _key_esc(self, event):
        if messagebox.askyesno("Quit", "Quit Hearts?"):
            self.root.destroy()

    def _key_space(self, event):
        """Space bar = pause / resume."""
        if self.game and not self.game.game_over:
            self.toggle_pause()
