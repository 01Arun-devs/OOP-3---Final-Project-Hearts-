# =============================================================================
# FILE:    logic.py
# PURPOSE: All Hearts game rules, flow control, and scoring.
#          _play_ai_turns() removed — GUI now drives each AI step one at a time
#          via step_ai_one() so animations can run between each play.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHORS: ARUN  — Game controller, round flow, dealer rotation, stats/logging
#          RUDRA — Rule enforcement, trick resolution, scoring, Shoot the Moon
# =============================================================================

import json, os, datetime
from card   import Card
from deck   import Deck
from player import HumanPlayer, AIPlayer, SmartAIPlayer


class HeartsGame:
    LOG_FILE   = "game_log.txt"
    STATS_FILE = "scores.json"

    def __init__(self, player_name="You", score_limit=50):
        self.player_name = player_name
        self.score_limit = score_limit
        self.players = [
            HumanPlayer(player_name),
            AIPlayer("AI 1"),
            SmartAIPlayer("AI 2"),
            AIPlayer("AI 3"),
        ]
        self.total_scores      = {p.name: 0 for p in self.players}
        self.round_number      = 0
        self.message_log       = []
        self.round_over        = False
        self.game_over         = False
        self.winner_text       = ""
        self.shoot_moon_player = None
        self.dealer_index      = 0
        # trick_winner: set by _resolve_trick, read by GUI for win animation
        self.trick_winner_index = None
        self.last_trick_cards   = []   # snapshot of the 4 cards before clearing
        self._log_game_start()
        self.start_new_round()

    # ── Round setup ───────────────────────────────────────────────────────────
    def start_new_round(self):
        self.round_number += 1
        if self.round_number > 1:
            self.dealer_index = (self.dealer_index + 1) % 4
        self.hearts_broken      = False
        self.first_trick        = True
        self.trick_number       = 1
        self.lead_suit          = None
        self.trick_cards        = []
        self.round_over         = False
        self.shoot_moon_player  = None
        self.trick_winner_index = None
        self.last_trick_cards   = []

        deck = Deck(); deck.shuffle(); hands = deck.deal(4)
        for i, p in enumerate(self.players):
            p.receive_cards(hands[i]); p.sort_hand()

        two_clubs = Card("C", 2)
        self.current_index = 0
        for i, p in enumerate(self.players):
            if two_clubs in p.hand:
                self.current_index = i; break

        self.message_log = []
        self._log_hand_dealt()
        self.log("Round " + str(self.round_number) +
                 " — Dealer: " + self.players[self.dealer_index].name)
        self.log(self.players[self.current_index].name + " leads with 2♣.")

    # ── Validation ───────────────────────────────────────────────────────────
    def get_valid_for_player(self, player_index):
        player    = self.players[player_index]
        lead_suit = self.trick_cards[0][1].suit if self.trick_cards else None
        return player.get_valid_cards(lead_suit, self.hearts_broken, self.first_trick)

    def is_valid(self, player_index, card):
        return card in self.get_valid_for_player(player_index)

    # ── Play one card (called by GUI for BOTH human and AI) ───────────────────
    def play_card(self, player_index, card):
        """
        Play one card. Returns (True, 'OK') or (False, error).
        Does NOT resolve trick or advance turn — GUI calls resolve_trick_if_done()
        after animating the card landing.
        """
        if not self.is_valid(player_index, card):
            return False, "That card is not valid."
        player = self.players[player_index]
        player.remove_card(card)
        self.trick_cards.append((player_index, card))
        if self.lead_suit is None:
            self.lead_suit = card.suit
        if card.suit == "H":
            self.hearts_broken = True
        self.log(player.name + " played " + card.label() + ".")
        return True, "OK"

    def resolve_trick_if_done(self):
        """
        Call after each play_card(). Returns:
          'continue'   — trick still in progress, advance to next player
          'trick_done' — trick resolved, trick_winner_index set, next player set
          'round_done' — all 13 tricks played, round scored
        """
        if len(self.trick_cards) < 4:
            self.current_index = (self.trick_cards[-1][0] + 1) % 4
            return "continue"
        return self._resolve_trick()

    def _resolve_trick(self):
        lead_plays = [(i, c) for i, c in self.trick_cards if c.suit == self.lead_suit]
        winner_index, winning_card = max(lead_plays, key=lambda x: x[1].rank)

        # Snapshot before clearing (GUI needs it for win animation)
        self.last_trick_cards   = list(self.trick_cards)
        self.trick_winner_index = winner_index

        for _, card in self.trick_cards:
            self.players[winner_index].taken.append(card)

        winner_name = self.players[winner_index].name
        self.log(winner_name + " wins the trick with " + winning_card.label() + ".")

        self.trick_cards   = []
        self.lead_suit     = None
        self.current_index = winner_index
        self.first_trick   = False
        self.trick_number += 1

        if all(len(p.hand) == 0 for p in self.players):
            self._finish_round()
            return "round_done"
        return "trick_done"

    # ── AI pick (called by GUI one step at a time) ────────────────────────────
    def ai_choose_card(self):
        """Ask the current AI player to pick a card. Returns the Card."""
        player      = self.players[self.current_index]
        lead_suit   = self.trick_cards[0][1].suit if self.trick_cards else None
        trick_cards = [c for _, c in self.trick_cards]
        return player.choose_card(lead_suit, self.hearts_broken,
                                  self.first_trick, trick_cards)

    # ── Human play entry point ────────────────────────────────────────────────
    def human_play_by_label(self, label):
        if self.current_turn_name() != self.player_name:
            return False, "Not your turn."
        if self.round_over or self.game_over:
            return False, "Round or game is over."
        selected = next((c for c in self.players[0].hand if c.label() == label), None)
        if selected is None:
            return False, "Card not found."
        return self.play_card(0, selected)

    # ── Scoring ───────────────────────────────────────────────────────────────
    def round_scores(self):
        return {p.name: sum(c.get_value() for c in p.taken) for p in self.players}

    def _finish_round(self):
        self.round_over = True
        rs = self.round_scores()
        self.log("Round " + str(self.round_number) + " finished!")
        shooter = next((n for n, pts in rs.items() if pts == 18), None)
        if shooter:
            self.shoot_moon_player = shooter
            self.log("★ SHOOT THE MOON by " + shooter + "! Everyone else +18!")
            for p in self.players:
                rs[p.name] = 0 if p.name == shooter else 18
        for p in self.players:
            self.total_scores[p.name] += rs[p.name]
            self.log(p.name + "  +" + str(rs[p.name]) +
                     "  →  total: " + str(self.total_scores[p.name]))
        if max(self.total_scores.values()) >= self.score_limit:
            self.game_over   = True
            low              = min(self.total_scores.values())
            winners          = [n for n, s in self.total_scores.items() if s == low]
            self.winner_text = ", ".join(winners)
            self.log("GAME OVER!  Winner: " + self.winner_text)
            self._save_stats(self.winner_text)
        else:
            self.log("Click 'Next Round' to continue.")

    # ── Logging / Stats ───────────────────────────────────────────────────────
    def _log_game_start(self):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write("[" + ts + "] === NEW GAME | Player: " + self.player_name +
                        " | Limit: " + str(self.score_limit) + " ===\n")
        except OSError: pass

    def _log_hand_dealt(self):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write("[" + ts + "] Round " + str(self.round_number) + " dealt.\n")
                for p in self.players:
                    f.write("  " + p.name + ": " +
                            " ".join(c.label() for c in p.hand) + "\n")
        except OSError: pass

    def log(self, text):
        self.message_log.append(text)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write("[" + ts + "] " + text + "\n")
        except OSError: pass

    def _save_stats(self, winner_name):
        stats = self._load_stats_raw()
        stats["games_played"] = stats.get("games_played", 0) + 1
        if self.player_name in winner_name:
            stats["games_won"]  = stats.get("games_won",  0) + 1
        else:
            stats["games_lost"] = stats.get("games_lost", 0) + 1
        my_score = self.total_scores[self.player_name]
        if my_score < stats.get("best_score", 9999):
            stats["best_score"] = my_score
        stats["last_player"] = self.player_name
        try:
            with open(self.STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
        except OSError: pass

    def _load_stats_raw(self):
        if os.path.exists(self.STATS_FILE):
            try:
                with open(self.STATS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {}

    def reset_stats(self):
        if os.path.exists(self.STATS_FILE):
            try: os.remove(self.STATS_FILE)
            except OSError: pass

    def stats_text(self):
        s = self._load_stats_raw()
        if not s:
            return "No stats yet."
        return ("Player    : " + s.get("last_player","—")       + "\n"
                "Played    : " + str(s.get("games_played",0))   + "\n"
                "Won       : " + str(s.get("games_won",0))      + "\n"
                "Lost      : " + str(s.get("games_lost",0))     + "\n"
                "Best score: " + str(s.get("best_score","—")))

    # ── GUI helpers ───────────────────────────────────────────────────────────
    def table_state(self):
        state = {p.name: "--" for p in self.players}
        for idx, card in self.trick_cards:
            state[self.players[idx].name] = card.label()
        return state

    def current_turn_name(self):
        if self.game_over:  return "Game Over"
        if self.round_over: return "Round Over"
        return self.players[self.current_index].name

    def dealer_name(self):
        return self.players[self.dealer_index].name

    def status_text(self):
        return ("Round  : " + str(self.round_number) + "\n"
                "Dealer : " + self.dealer_name()     + "\n"
                "Trick  : " + str(min(self.trick_number,13)) + " / 13\n"
                "Hearts : " + ("Broken ♥" if self.hearts_broken else "Not broken") + "\n"
                "Turn   : " + self.current_turn_name())
