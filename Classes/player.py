# =============================================================================
# FILE:    player.py
# PURPOSE: All player types — base class, human, and AI players.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHORS: JEEL  — Player base class, HumanPlayer
#          SUJAY — AIPlayer (basic strategy), SmartAIPlayer (Shoot the Moon)
# =============================================================================
# OOP CONCEPTS:
#   ABSTRACTION  — Player defines what all players must do (the interface)
#   INHERITANCE  — HumanPlayer, AIPlayer, SmartAIPlayer all extend Player
#   POLYMORPHISM — choose_card() works differently for each player type
#
# CLASS HIERARCHY:
#   Player (base — JEEL)
#     ├── HumanPlayer   (JEEL  — GUI handles card selection)
#     ├── AIPlayer      (SUJAY — basic defensive strategy)
#     └── SmartAIPlayer (SUJAY — tries Shoot the Moon)
# =============================================================================

from card import Card


# =============================================================================
# BASE CLASS — Player  |  AUTHOR: JEEL
# =============================================================================
class Player:
    """
    Abstract base class for all players.
    Defines shared data and shared behaviour every player needs.
    choose_card() raises NotImplementedError — every subclass must override it.
    """

    def __init__(self, name):
        self.name     = name
        self.is_human = False   # overridden to True in HumanPlayer
        self.hand     = []      # list of Card objects currently held
        self.taken    = []      # cards collected in tricks this round

    def receive_cards(self, cards):
        """Give player a fresh hand at the start of each round."""
        self.hand  = cards
        self.taken = []

    def sort_hand(self):
        """Sort hand by suit then rank — makes the hand easier to read."""
        suit_order = {"C": 0, "D": 1, "S": 2, "H": 3}
        self.hand.sort(key=lambda c: (suit_order[c.suit], c.rank))

    def remove_card(self, card):
        """Remove a played card from the hand."""
        self.hand.remove(card)

    def get_valid_cards(self, lead_suit, hearts_broken, first_trick):
        """
        Returns the list of cards this player is LEGALLY allowed to play.

        Rules enforced:
          Leading (lead_suit is None):
            - First trick: player with 2♣ must play it
            - Hearts not broken: cannot lead with a Heart (unless only Hearts left)
            - Hearts broken: any card is valid
          Following (lead_suit is set):
            - Must follow lead suit if possible
            - Cannot follow: may play anything
            - First trick exception: prefer non-penalty cards when discarding
        """
        if not self.hand:
            return []

        # ── LEADING a trick ───────────────────────────────────────────────────
        if lead_suit is None:
            two_clubs = Card("C", 2)
            if first_trick and two_clubs in self.hand:
                return [two_clubs]               # must play 2♣ on first trick

            if not hearts_broken:
                non_hearts = [c for c in self.hand if c.suit != "H"]
                if non_hearts:
                    return non_hearts            # cannot lead hearts until broken
            return list(self.hand)

        # ── FOLLOWING a trick ─────────────────────────────────────────────────
        same_suit = [c for c in self.hand if c.suit == lead_suit]
        if same_suit:
            return same_suit                     # must follow lead suit

        # Cannot follow suit — can play anything
        if first_trick:
            safe = [c for c in self.hand if not c.is_penalty()]
            if safe:
                return safe                      # avoid dumping penalties on trick 1

        return list(self.hand)

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """
        Abstract — every AI subclass must override this.
        HumanPlayer does not use this; the GUI handles human input.
        """
        raise NotImplementedError("Subclass must implement choose_card()")

    def hand_labels(self):
        """Returns list of label strings for every card in hand (sorted)."""
        self.sort_hand()
        return [c.label() for c in self.hand]

    def valid_labels(self, lead_suit, hearts_broken, first_trick):
        """Returns a set of label strings for all valid cards."""
        return set(c.label() for c in self.get_valid_cards(lead_suit, hearts_broken, first_trick))


# =============================================================================
# HUMAN PLAYER  |  AUTHOR: JEEL
# =============================================================================
class HumanPlayer(Player):
    """
    Human-controlled player.
    INHERITANCE: Gets everything from Player.
    Card selection is handled by GUI clicks, not choose_card().
    """

    def __init__(self, name):
        Player.__init__(self, name)
        self.is_human = True


# =============================================================================
# BASIC AI PLAYER  |  AUTHOR: SUJAY
# =============================================================================
class AIPlayer(Player):
    """
    Computer player using a basic defensive strategy.

    STRATEGY:
      Leading   — play lowest non-penalty card
      Discarding — dump Queen of Spades first, then highest Heart
      Following  — play highest card that still loses the trick;
                   if forced to win, play lowest

    INHERITANCE:  extends Player
    POLYMORPHISM: choose_card() overrides the base class version
    """

    def __init__(self, name):
        Player.__init__(self, name)

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Pick the best defensive card to play."""
        valid = self.get_valid_cards(lead_suit, hearts_broken, first_trick)

        # ── Leading ──────────────────────────────────────────────────────────
        if lead_suit is None:
            safe = [c for c in valid if c.get_value() == 0]
            pool = safe if safe else valid
            return min(pool, key=lambda c: c.rank)

        # ── Cannot follow suit — discard ─────────────────────────────────────
        can_follow = any(c.suit == lead_suit for c in valid)
        if not can_follow:
            for c in valid:                          # dump Q♠ first (5 pts)
                if c.suit == "S" and c.rank == 12:
                    return c
            hearts = [c for c in valid if c.suit == "H"]
            if hearts:
                return max(hearts, key=lambda c: c.rank)   # dump highest heart
            return max(valid, key=lambda c: c.rank)         # dump highest card

        # ── Following suit ───────────────────────────────────────────────────
        lead_in_trick = [c for c in trick_cards if c.suit == lead_suit]
        if lead_in_trick:
            current_winner = max(lead_in_trick, key=lambda c: c.rank)
            losing = [c for c in valid if c.rank < current_winner.rank]
            if losing:
                return max(losing, key=lambda c: c.rank)   # highest losing card

        return min(valid, key=lambda c: c.rank)             # forced to win — play lowest


# =============================================================================
# SMART AI PLAYER  |  AUTHOR: SUJAY  |  Optional Feature: Advanced A.I.
# =============================================================================
class SmartAIPlayer(AIPlayer):
    """
    Advanced AI that attempts to Shoot the Moon when holding many penalty cards.

    SHOOT THE MOON:
      If holding 8+ penalty cards, switch to aggressive mode:
      try to WIN every trick to collect all 18 penalty points.
      Result: shooter scores 0, everyone else gets +18.

    INHERITANCE:  extends AIPlayer (which extends Player)
    POLYMORPHISM: choose_card() overrides AIPlayer's version
    """

    THRESHOLD = 8   # penalty cards in hand before attempting Shoot the Moon

    def __init__(self, name):
        AIPlayer.__init__(self, name)
        self.shooting = False

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Decide: attempt Shoot the Moon (aggressive) or play defensively."""
        penalty_count = sum(1 for c in self.hand if c.is_penalty())
        self.shooting = (penalty_count >= self.THRESHOLD)

        if self.shooting:
            return self._aggressive_card(lead_suit, hearts_broken, first_trick, trick_cards)

        # Fewer than 8 penalty cards — fall back to parent (AIPlayer) strategy
        return AIPlayer.choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards)

    def _aggressive_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Aggressive mode: play to WIN every trick."""
        valid = self.get_valid_cards(lead_suit, hearts_broken, first_trick)

        if lead_suit is None:
            return max(valid, key=lambda c: c.rank)    # lead with highest card

        same_suit = [c for c in valid if c.suit == lead_suit]
        if same_suit:
            return max(same_suit, key=lambda c: c.rank)  # win with highest of suit

        # Cannot follow — dump lowest non-penalty card (save high cards)
        safe = [c for c in valid if c.get_value() == 0]
        if safe:
            return min(safe, key=lambda c: c.rank)
        return min(valid, key=lambda c: c.rank)
