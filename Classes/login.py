# =============================================================================
# FILE:    login.py
# PURPOSE: Login / Sign-Up screen for Hearts.
#          Stores user accounts in users.json (hashed passwords).
#          Only authenticated users can proceed to the game.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# =============================================================================

import tkinter as tk
from tkinter import messagebox
import json, os, hashlib, re

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# ── Palette (matches gui.py) ──────────────────────────────────────────────────
BG_TABLE   = "#145220"
BG_FELT    = "#1a6b2a"
BG_CARD    = "#0f3d1a"
FG_WHITE   = "#ffffff"
FG_GOLD    = "#ffc107"
FG_LIGHT   = "#a5d6a7"
FG_RED     = "#ef5350"
FG_MUTED   = "#66bb6a"
FG_SUBTLE  = "#4caf50"

FONT_TITLE  = ("Georgia", 28, "bold")
FONT_HEAD   = ("Helvetica", 13, "bold")
FONT_BODY   = ("Helvetica", 11)
FONT_SMALL  = ("Helvetica", 9)
FONT_BTN    = ("Helvetica", 11, "bold")
FONT_LABEL  = ("Helvetica", 10, "bold")
FONT_ERROR  = ("Helvetica", 10)


# =============================================================================
#  PASSWORD HASHING
# =============================================================================
def _hash(password: str) -> str:
    """SHA-256 hash of the password (hex digest)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# =============================================================================
#  USER STORE  —  thin JSON wrapper
# =============================================================================
def _load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    Create a new account.
    Returns (True, "") on success or (False, reason) on failure.
    """
    username = username.strip()
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 2:
        return False, "Username must be at least 2 characters."
    if len(username) > 20:
        return False, "Username must be 20 characters or fewer."
    if not re.match(r"^[A-Za-z0-9_\- ]+$", username):
        return False, "Username: letters, numbers, spaces, _ or - only."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    users = _load_users()
    key   = username.lower()   # case-insensitive uniqueness
    if key in users:
        return False, f'Username "{username}" is already taken.'

    users[key] = {
        "display_name": username,   # preserves original capitalisation
        "password_hash": _hash(password),
    }
    _save_users(users)
    return True, ""


def authenticate(username: str, password: str) -> tuple[bool, str, str]:
    """
    Verify credentials.
    Returns (True, display_name, "") on success
         or (False, "", reason)   on failure.
    """
    username = username.strip()
    users    = _load_users()
    key      = username.lower()
    if key not in users:
        return False, "", "Username not found."
    record = users[key]
    if record["password_hash"] != _hash(password):
        return False, "", "Incorrect password."
    return True, record["display_name"], ""


# =============================================================================
#  LOGIN SCREEN  —  tkinter widget
# =============================================================================
class LoginScreen:
    """
    Shown before HeartsUI.  Calls on_success(display_name) when the user
    successfully logs in.
    """

    def __init__(self, root: tk.Tk, on_success):
        self.root       = root
        self.on_success = on_success
        self._mode      = "login"   # "login" or "signup"
        self._build()

    # ── build / destroy ───────────────────────────────────────────────────────
    def _build(self):
        self.frame = tk.Frame(self.root, bg=BG_TABLE)
        self.frame.pack(fill="both", expand=True)

        # ── decorative card-suit strip across the top ─────────────────────────
        top_bar = tk.Frame(self.frame, bg=BG_CARD, height=48)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        suits_text = "  ♠  ♥  ♦  ♣  " * 12
        tk.Label(top_bar, text=suits_text,
                 font=("Helvetica", 16), bg=BG_CARD,
                 fg=FG_SUBTLE).place(relx=0.5, rely=0.5, anchor="center")

        # ── centre card ───────────────────────────────────────────────────────
        outer = tk.Frame(self.frame, bg=BG_TABLE)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(outer, bg=BG_CARD,
                        highlightbackground=FG_SUBTLE,
                        highlightthickness=2,
                        padx=42, pady=32)
        card.pack()

        # Title
        tk.Label(card, text="♥  HEARTS",
                 font=FONT_TITLE, bg=BG_CARD, fg=FG_GOLD).pack(pady=(0, 4))
        tk.Label(card, text="Durham College  ·  COSC-2200-03  ·  Group 2",
                 font=FONT_SMALL, bg=BG_CARD, fg=FG_MUTED).pack()

        tk.Frame(card, bg=FG_SUBTLE, height=1).pack(fill="x", pady=16)

        # Tab row  (Login / Sign Up)
        tab_row = tk.Frame(card, bg=BG_CARD)
        tab_row.pack(pady=(0, 16))

        self._tab_login  = self._make_tab(tab_row, "Login",   "login")
        self._tab_signup = self._make_tab(tab_row, "Sign Up", "signup")
        self._tab_login.pack(side="left",  padx=4)
        self._tab_signup.pack(side="left", padx=4)

        # ── form fields ───────────────────────────────────────────────────────
        form = tk.Frame(card, bg=BG_CARD)
        form.pack()

        # Username
        tk.Label(form, text="Username", font=FONT_LABEL,
                 bg=BG_CARD, fg=FG_LIGHT, anchor="w").grid(
                     row=0, column=0, sticky="w", pady=(0, 3))
        self._user_var = tk.StringVar()
        self._user_entry = tk.Entry(form, textvariable=self._user_var,
                                    font=FONT_BODY, width=24,
                                    relief="flat", bd=6,
                                    bg="#1a5c26", fg=FG_WHITE,
                                    insertbackground=FG_GOLD)
        self._user_entry.grid(row=1, column=0, pady=(0, 10), ipady=4)

        # Password
        tk.Label(form, text="Password", font=FONT_LABEL,
                 bg=BG_CARD, fg=FG_LIGHT, anchor="w").grid(
                     row=2, column=0, sticky="w", pady=(0, 3))
        self._pass_var = tk.StringVar()
        self._pass_entry = tk.Entry(form, textvariable=self._pass_var,
                                     font=FONT_BODY, width=24,
                                     show="●", relief="flat", bd=6,
                                     bg="#1a5c26", fg=FG_WHITE,
                                     insertbackground=FG_GOLD)
        self._pass_entry.grid(row=3, column=0, pady=(0, 10), ipady=4)

        # Confirm Password  (signup only — hidden in login mode)
        self._confirm_lbl = tk.Label(form, text="Confirm Password",
                                      font=FONT_LABEL, bg=BG_CARD,
                                      fg=FG_LIGHT, anchor="w")
        self._confirm_var = tk.StringVar()
        self._confirm_entry = tk.Entry(form, textvariable=self._confirm_var,
                                        font=FONT_BODY, width=24,
                                        show="●", relief="flat", bd=6,
                                        bg="#1a5c26", fg=FG_WHITE,
                                        insertbackground=FG_GOLD)

        # Error label
        self._err_var = tk.StringVar()
        self._err_lbl = tk.Label(card, textvariable=self._err_var,
                                  font=FONT_ERROR, bg=BG_CARD,
                                  fg=FG_RED, wraplength=280, justify="center")
        self._err_lbl.pack(pady=(0, 4))

        # Submit button
        self._submit_btn = tk.Button(card, font=FONT_BTN,
                                      bg="#2e7d32", fg=FG_WHITE,
                                      activebackground="#388e3c",
                                      relief="flat", cursor="hand2",
                                      width=22, height=2,
                                      command=self._submit)
        self._submit_btn.pack(pady=(6, 4))

        # Toggle hint
        self._hint_var = tk.StringVar()
        self._hint_lbl = tk.Label(card, textvariable=self._hint_var,
                                   font=FONT_SMALL, bg=BG_CARD,
                                   fg=FG_MUTED, cursor="hand2")
        self._hint_lbl.pack(pady=(2, 0))
        self._hint_lbl.bind("<Button-1>", lambda e: self._toggle_mode())

        # ── decorative bottom strip ───────────────────────────────────────────
        bot_bar = tk.Frame(self.frame, bg=BG_CARD, height=48)
        bot_bar.pack(fill="x", side="bottom")
        bot_bar.pack_propagate(False)
        tk.Label(bot_bar, text=suits_text,
                 font=("Helvetica", 16), bg=BG_CARD,
                 fg=FG_SUBTLE).place(relx=0.5, rely=0.5, anchor="center")

        # Keyboard shortcuts
        self.root.bind("<Return>",  lambda e: self._submit())
        self.root.bind("<Tab>",     self._focus_next)

        self._apply_mode()
        self._user_entry.focus_set()

    def destroy(self):
        self.root.unbind("<Return>")
        self.root.unbind("<Tab>")
        self.frame.destroy()

    # ── tab helpers ───────────────────────────────────────────────────────────
    def _make_tab(self, parent, text, mode):
        return tk.Button(
            parent, text=text, font=FONT_HEAD,
            relief="flat", cursor="hand2",
            padx=16, pady=6,
            command=lambda m=mode: self._set_mode(m))

    def _apply_mode(self):
        login  = self._mode == "login"
        signup = not login

        # Tab highlight
        self._tab_login.config(
            bg=FG_GOLD    if login  else BG_CARD,
            fg=BG_TABLE   if login  else FG_MUTED,
            activebackground=FG_GOLD if login else BG_CARD)
        self._tab_signup.config(
            bg=FG_GOLD    if signup else BG_CARD,
            fg=BG_TABLE   if signup else FG_MUTED,
            activebackground=FG_GOLD if signup else BG_CARD)

        # Confirm field visibility
        if signup:
            self._confirm_lbl.grid(row=4, column=0, sticky="w", pady=(0, 3))
            self._confirm_entry.grid(row=5, column=0, pady=(0, 10), ipady=4)
        else:
            self._confirm_lbl.grid_remove()
            self._confirm_entry.grid_remove()

        self._submit_btn.config(
            text="▶  Login"   if login else "✔  Create Account")
        self._hint_var.set(
            "No account? Sign up →" if login else "Already have an account? Login →")
        self._err_var.set("")

    def _set_mode(self, mode):
        self._mode = mode
        self._confirm_var.set("")
        self._apply_mode()
        self._user_entry.focus_set()

    def _toggle_mode(self):
        self._set_mode("signup" if self._mode == "login" else "login")

    # ── focus cycling ─────────────────────────────────────────────────────────
    def _focus_next(self, event):
        entries = [self._user_entry, self._pass_entry]
        if self._mode == "signup":
            entries.append(self._confirm_entry)
        try:
            idx = entries.index(event.widget)
            entries[(idx + 1) % len(entries)].focus_set()
        except ValueError:
            entries[0].focus_set()
        return "break"

    # ── submit ────────────────────────────────────────────────────────────────
    def _submit(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get()
        self._err_var.set("")

        if self._mode == "login":
            ok, display, reason = authenticate(username, password)
            if ok:
                self._on_login_success(display)
            else:
                self._err_var.set("⚠  " + reason)
                self._pass_entry.focus_set()
                self._pass_entry.select_range(0, "end")
        else:
            confirm = self._confirm_var.get()
            if password != confirm:
                self._err_var.set("⚠  Passwords do not match.")
                self._confirm_entry.focus_set()
                return
            ok, reason = register_user(username, password)
            if ok:
                messagebox.showinfo(
                    "Account Created",
                    f'Welcome, {username}!\n\nYour account has been created.\nYou are now logged in.')
                self._on_login_success(username.strip())
            else:
                self._err_var.set("⚠  " + reason)

    def _on_login_success(self, display_name: str):
        self.destroy()
        self.on_success(display_name)
