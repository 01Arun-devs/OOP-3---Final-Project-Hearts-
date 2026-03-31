# =============================================================================
# FILE:    logic.py
# PURPOSE: All Hearts game rules and logic. No GUI code here.
#          The GUI talks to this class to play the game.
# AUTHOR:  Group 2 - COSC-2200-03
# =============================================================================
# OOP CONCEPT - ENCAPSULATION + COMPOSITION:
#   HeartsGame owns the players, deck, and score manager.
#   All rules are in this one class - GUI never calculates scores.
# =============================================================================

import json
import os
import datetime
from card   import Card
from deck   import Deck
from player import HumanPlayer, AIPlayer, SmartAIPlayer

TARGET_SCORE = 50   # default - can be changed to 100


class HeartsGame:
    """
    Main game controller. Manages all Hearts rules, scoring, and game flow.
    The GUI reads from this class and calls play_card() / next_round().
    """

    LOG_FILE   = "game_log.txt"
    STATS_FILE = "scores.json"

    def __init__(self, score_limit=50):
        # Create players - 1 Human + 2 AI + 1 Smart AI
        self.players = [
            HumanPlayer("You"),
            AIPlayer("AI 1"),
            SmartAIPlayer("AI 2"),   # Smart AI - tries Shoot the Moon
            AIPlayer("AI 3"),
        ]

        self.score_limit   = score_limit
        self.total_scores  = {p.name: 0 for p in self.players}
        self.round_number  = 0
        self.message_log   = []
        self.round_over    = False
        self.game_over     = False
        self.winner_text   = ""
        self.shoot_moon_player = None   # name of player who shot the moon

        self._log_game_start()
        self.start_new_round()

    # =========================================================================
    # ROUND SETUP
    # =========================================================================

    def start_new_round(self):
        """Shuffle, deal, and start a new round of 13 tricks."""
        self.round_number      += 1
        self.hearts_broken      = False
        self.first_trick        = True
        self.trick_number       = 1
        self.lead_suit          = None
        self.trick_cards        = []   # list of (player_index, card)
        self.round_over         = False
        self.shoot_moon_player  = None

        # Deal cards
        deck = Deck()
        deck.shuffle()
        hands = deck.deal(4)
        for i, player in enumerate(self.players):
            player.receive_cards(hands[i])
            player.sort_hand()

        # Find who has 2 of Clubs - they lead first
        two_clubs = Card("C", 2)
        self.current_index = 0
        for i, player in enumerate(self.players):
            if two_clubs in player.hand:
                self.current_index = i
                break

        self.message_log = []
        self._log_hand_dealt()
        self.log("Round " + str(self.round_number) + " started.")
        self.log(self.players[self.current_index].name + " leads with 2♣.")

        # Let AI play until it is human's turn
        if not self.players[self.current_index].is_human:
            self._play_ai_turns()

    # =========================================================================
    # CARD VALIDATION
    # =========================================================================

    def get_valid_for_player(self, player_index):
        """Get valid cards for any player."""
        player = self.players[player_index]
        lead_suit = self.trick_cards[0][1].suit if self.trick_cards else None
        return player.get_valid_cards(lead_suit, self.hearts_broken, self.first_trick)

    def is_valid(self, player_index, card):
        """Check if a card is a valid play."""
        return card in self.get_valid_for_player(player_index)

    # =========================================================================
    # PLAYING CARDS
    # =========================================================================

    def play_card(self, player_index, card):
        """
        Play a card for a player.
        Returns (True, message) if valid, (False, error) if not.
        """
        player = self.players[player_index]

        if not self.is_valid(player_index, card):
            return False, "That card is not valid to play right now."

        # Remove from hand and add to trick
        player.remove_card(card)
        self.trick_cards.append((player_index, card))

        # Set lead suit if this is first card
        if self.lead_suit is None:
            self.lead_suit = card.suit

        # Track hearts broken
        if card.suit == "H":
            self.hearts_broken = True

        self.log(player.name + " played " + card.label() + ".")

        # If trick is complete (4 cards played)
        if len(self.trick_cards) == 4:
            self._resolve_trick()
        else:
            # Move to next player
            self.current_index = (player_index + 1) % 4

        return True, "OK"

    def _resolve_trick(self):
        """Find trick winner, award cards, check if round is over."""
        # Winner = highest card of lead suit
        lead_plays = [(i, c) for i, c in self.trick_cards if c.suit == self.lead_suit]
        winner_index, winning_card = max(lead_plays, key=lambda x: x[1].rank)

        # Give all trick cards to winner
        for _, card in self.trick_cards:
            self.players[winner_index].taken.append(card)

        winner_name = self.players[winner_index].name
        self.log(winner_name + " wins the trick with " + winning_card.label() + ".")

        # Reset for next trick
        self.trick_cards   = []
        self.lead_suit     = None
        self.current_index = winner_index
        self.first_trick   = False
        self.trick_number += 1

        # Check if all 13 tricks are done
        if all(len(p.hand) == 0 for p in self.players):
            self._finish_round()
        elif not self.players[self.current_index].is_human:
            self._play_ai_turns()

    def _play_ai_turns(self):
        """Keep playing AI turns until it is the human's turn or round ends."""
        while not self.round_over and not self.game_over:
            player = self.players[self.current_index]
            if player.is_human:
                break

            # Get lead suit for this trick
            lead_suit   = self.trick_cards[0][1].suit if self.trick_cards else None
            trick_cards = [c for _, c in self.trick_cards]

            card = player.choose_card(lead_suit, self.hearts_broken,
                                      self.first_trick, trick_cards)
            self.play_card(self.current_index, card)

    # =========================================================================
    # HUMAN PLAYS
    # =========================================================================

    def human_play_by_label(self, label):
        """Called by GUI when human clicks a card button."""
        # Find the card matching this label
        selected = None
        for card in self.players[0].hand:
            if card.label() == label:
                selected = card
                break

        if selected is None:
            return False, "Card not found."

        ok, msg = self.play_card(0, selected)
        if ok:
            self._play_ai_turns()
        return ok, msg

    # =========================================================================
    # SCORING
    # =========================================================================

    def round_scores(self):
        """Count penalty cards each player collected this round."""
        scores = {}
        for player in self.players:
            total = 0
            for card in player.taken:
                total += card.get_value()
            scores[player.name] = total
        return scores

    def _finish_round(self):
        """Score the round, check for Shoot the Moon, check game over."""
        self.round_over = True
        rs = self.round_scores()

        self.log("Round " + str(self.round_number) + " finished!")

        # Check Shoot the Moon - one player got all 18 points
        shooter = None
        for name, pts in rs.items():
            if pts == 18:
                shooter = name
                break

        if shooter:
            # Reverse scores - shooter gets 0, everyone else gets 18
            self.shoot_moon_player = shooter
            self.log("SHOOT THE MOON by " + shooter + "! Everyone else +18!")
            for player in self.players:
                if player.name == shooter:
                    rs[player.name] = 0
                else:
                    rs[player.name] = 18

        # Add to total scores
        for player in self.players:
            self.total_scores[player.name] += rs[player.name]
            self.log(player.name + " round: +" + str(rs[player.name]) +
                     "  total: " + str(self.total_scores[player.name]))

        # Check game over
        if max(self.total_scores.values()) >= self.score_limit:
            self.game_over  = True
            low = min(self.total_scores.values())
            winners = [n for n, s in self.total_scores.items() if s == low]
            self.winner_text = ", ".join(winners)
            self.log("GAME OVER! Winner: " + self.winner_text)
            self._save_stats(self.winner_text)
        else:
            self.log("Click 'Next Round' to continue.")

    # =========================================================================
    # STATS - Persistent save/load (Optional Feature: Logging & Statistics)
    # =========================================================================

    def _log_game_start(self):
        """Write game start to log file."""
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = "[" + ts + "] === NEW GAME STARTED (limit: " + str(self.score_limit) + ") ===\n"
        with open(self.LOG_FILE, "a") as f:
            f.write(line)

    def _log_hand_dealt(self):
        """Write dealt hands to log file."""
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.LOG_FILE, "a") as f:
            f.write("[" + ts + "] Round " + str(self.round_number) + " dealt.\n")
            for player in self.players:
                hand_str = " ".join(c.label() for c in player.hand)
                f.write("  " + player.name + ": " + hand_str + "\n")

    def _save_stats(self, winner_name):
        """Save game result to scores.json."""
        stats = self.load_stats()
        stats["games_played"] = stats.get("games_played", 0) + 1
        if winner_name == "You":
            stats["games_won"]  = stats.get("games_won",  0) + 1
            stats["games_lost"] = stats.get("games_lost", 0)
        else:
            stats["games_won"]  = stats.get("games_won",  0)
            stats["games_lost"] = stats.get("games_lost", 0) + 1
        best = stats.get("best_score", 9999)
        my_score = self.total_scores["You"]
        if my_score < best:
            stats["best_score"] = my_score
        with open(self.STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)

    def load_stats(self):
        """Load saved stats. Returns empty dict if no file yet."""
        if os.path.exists(self.STATS_FILE):
            with open(self.STATS_FILE, "r") as f:
                return json.load(f)
        return {}

    def reset_stats(self):
        """Erase all saved statistics."""
        if os.path.exists(self.STATS_FILE):
            os.remove(self.STATS_FILE)

    # =========================================================================
    # HELPERS for GUI
    # =========================================================================

    def log(self, text):
        """Add a line to the message log shown in GUI."""
        self.message_log.append(text)
        # Also write to file
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with open(self.LOG_FILE, "a") as f:
            f.write("[" + ts + "] " + text + "\n")

    def table_state(self):
        """Returns dict of what each player has played this trick."""
        state = {"AI 2": "--", "AI 1": "--", "AI 3": "--", "You": "--"}
        for idx, card in self.trick_cards:
            state[self.players[idx].name] = card.label()
        return state

    def current_turn_name(self):
        """Returns whose turn it is."""
        if self.game_over:
            return "Game Over"
        if self.round_over:
            return "Round Over"
        return self.players[self.current_index].name

    def status_text(self):
        """Status string shown in sidebar."""
        return (
            "Round:  " + str(self.round_number) + "\n"
            "Trick:  " + str(min(self.trick_number, 13)) + " / 13\n"
            "Hearts: " + ("Broken!" if self.hearts_broken else "Not Broken") + "\n"
            "Turn:   " + self.current_turn_name()
        )

    def stats_text(self):
        """Formatted lifetime stats string."""
        s = self.load_stats()
        if not s:
            return "No stats yet."
        return (
            "Games played: " + str(s.get("games_played", 0)) + "\n"
            "Won: "          + str(s.get("games_won",    0)) + "\n"
            "Lost: "         + str(s.get("games_lost",   0)) + "\n"
            "Best score: "   + str(s.get("best_score",   "--"))
        )

# =============================================================================
# CONCEPTS USED:
#   Composition:  HeartsGame owns Player objects and Deck
#   json module:  saves stats as a text file between sessions
#   os module:    checks if files exist before opening them
#   datetime:     timestamps for the game log
# =============================================================================
