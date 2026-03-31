# =============================================================================
# FILE:    player.py
# PURPOSE: Defines all player types used in the game.
# AUTHOR:  Group 2 - COSC-2200-03
# =============================================================================
# OOP CONCEPTS IN THIS FILE:
#
#   ABSTRACTION  - Player is a base class that defines WHAT players must do
#   INHERITANCE  - HumanPlayer, AIPlayer, SmartAIPlayer all extend Player
#   POLYMORPHISM - choose_card() works differently for each player type
#
# CLASS HIERARCHY:
#   Player (base)
#     ├── HumanPlayer   (human - GUI handles card selection)
#     ├── AIPlayer      (basic AI - defensive strategy)
#     └── SmartAIPlayer (advanced AI - tries Shoot the Moon)
# =============================================================================

from card import Card


# =============================================================================
# BASE CLASS - Player
# =============================================================================
class Player:
    """
    Base class for all players.
    Defines what every player must have (name, hand, score).
    Cannot be used directly - subclasses fill in the details.
    """

    def __init__(self, name):
        self.name     = name
        self.is_human = False  # overridden in HumanPlayer shown on screen
        self.hand  = []     # list of Card objects in hand
        self.taken = []     # cards won in tricks this hand
        self.score = 0      # total penalty points this game

    def receive_cards(self, cards):
        """Give player a new hand of 13 cards."""
        self.hand  = cards
        self.taken = []

    def sort_hand(self):
        """Sort hand by suit then rank - makes it easier to read."""
        suit_order = {"C": 0, "D": 1, "S": 2, "H": 3}
        self.hand.sort(key=lambda c: (suit_order[c.suit], c.rank))

    def remove_card(self, card):
        """Remove a played card from the hand."""
        self.hand.remove(card)

    def get_valid_cards(self, lead_suit, hearts_broken, first_trick):
        """
        Returns only the cards this player is ALLOWED to play.

        Rules:
          Leading (no lead suit yet):
            - First trick: must play 2 of Clubs if you have it
            - Cannot lead Hearts until broken (unless only Hearts left)
          Following:
            - Must follow lead suit if possible
            - First trick: avoid penalty cards if possible
        """
        if not self.hand:
            return []

        # Leading a trick
        if lead_suit is None:
            # First trick: player with 2 of Clubs must play it
            two_clubs = Card("C", 2)
            if first_trick and two_clubs in self.hand:
                return [two_clubs]
            # Cannot lead Hearts unless broken
            if not hearts_broken:
                non_hearts = [c for c in self.hand if c.suit != "H"]
                if non_hearts:
                    return non_hearts
            return list(self.hand)

        # Following a trick - must match lead suit if possible
        same_suit = [c for c in self.hand if c.suit == lead_suit]
        if same_suit:
            return same_suit

        # Cannot follow suit - play anything
        # First trick: try to avoid penalty cards
        if first_trick:
            safe = [c for c in self.hand if not c.is_penalty()]
            if safe:
                return safe

        return list(self.hand)

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """
        ABSTRACT METHOD - subclasses must override this.
        Raises error if called on base class directly.
        """
        raise NotImplementedError("Subclass must implement choose_card()")

    def hand_labels(self):
        """Returns list of label strings for each card in hand."""
        self.sort_hand()
        return [c.label() for c in self.hand]

    def valid_labels(self, lead_suit, hearts_broken, first_trick):
        """Returns set of label strings for valid cards."""
        valid = self.get_valid_cards(lead_suit, hearts_broken, first_trick)
        return set(c.label() for c in valid)


# =============================================================================
# HUMAN PLAYER
# =============================================================================
class HumanPlayer(Player):
    """
    Human player controlled by GUI clicks.
    INHERITANCE: Gets everything from Player.
    choose_card() is handled by the GUI, not here.
    """

    def __init__(self, name):
        Player.__init__(self, name)
        self.is_human = True   # this player is human


# =============================================================================
# BASIC AI PLAYER
# =============================================================================
class AIPlayer(Player):
    """
    Computer player with basic defensive strategy.

    STRATEGY:
      Leading:   play lowest safe (non-penalty) card
      Discard:   dump Queen of Spades first, then highest Heart
      Following: play highest card that still loses the trick

    INHERITANCE:  extends Player
    POLYMORPHISM: choose_card() overrides the base class version
    """

    def __init__(self, name):
        Player.__init__(self, name)

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Pick the best card using defensive strategy."""
        valid = self.get_valid_cards(lead_suit, hearts_broken, first_trick)

        # --- Leading ---
        if lead_suit is None:
            safe = [c for c in valid if c.get_value() == 0]
            pool = safe if safe else valid
            return min(pool, key=lambda c: c.rank)

        # --- Can't follow suit - discard ---
        can_follow = any(c.suit == lead_suit for c in valid)
        if not can_follow:
            # Dump Queen of Spades first (5 pts)
            for c in valid:
                if c.suit == "S" and c.rank == 12:
                    return c
            # Then highest Heart
            hearts = [c for c in valid if c.suit == "H"]
            if hearts:
                return max(hearts, key=lambda c: c.rank)
            # Otherwise highest card
            return max(valid, key=lambda c: c.rank)

        # --- Following suit ---
        lead_in_trick = [c for c in trick_cards if c.suit == lead_suit]
        if lead_in_trick:
            current_winner = max(lead_in_trick, key=lambda c: c.rank)
            # Play highest card that still loses
            losing = [c for c in valid if c.rank < current_winner.rank]
            if losing:
                return max(losing, key=lambda c: c.rank)

        # Forced to win or no choice - play lowest
        return min(valid, key=lambda c: c.rank)


# =============================================================================
# SMART AI PLAYER - ADVANCED AI (Optional Feature)
# =============================================================================
class SmartAIPlayer(AIPlayer):
    """
    Advanced AI that can attempt to Shoot the Moon.
    Extends AIPlayer - uses defensive play as fallback.

    SHOOT THE MOON STRATEGY:
      If holding 8+ penalty cards, switch to aggressive mode:
      try to WIN every trick to collect all 18 penalty points.
      This gives everyone else +18 and this player scores 0.

    INHERITANCE:  extends AIPlayer (which extends Player)
    POLYMORPHISM: choose_card() overrides AIPlayer's version
    """

    THRESHOLD = 8   # how many penalty cards before trying to shoot

    def __init__(self, name):
        AIPlayer.__init__(self, name)
        self.shooting = False   # True when trying to shoot the moon

    def choose_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Decide: shoot the moon or play defensively."""
        # Count penalty cards in hand
        penalty_count = sum(1 for c in self.hand if c.is_penalty())
        self.shooting = (penalty_count >= self.THRESHOLD)

        if self.shooting:
            return self._aggressive_card(lead_suit, hearts_broken,
                                         first_trick, trick_cards)
        # Fall back to parent (AIPlayer) strategy
        return AIPlayer.choose_card(self, lead_suit, hearts_broken,
                                    first_trick, trick_cards)

    def _aggressive_card(self, lead_suit, hearts_broken, first_trick, trick_cards):
        """Play to WIN the trick - play highest card possible."""
        valid = self.get_valid_cards(lead_suit, hearts_broken, first_trick)

        # Leading - play highest card to take control
        if lead_suit is None:
            return max(valid, key=lambda c: c.rank)

        # Following - play highest of lead suit to win
        same_suit = [c for c in valid if c.suit == lead_suit]
        if same_suit:
            return max(same_suit, key=lambda c: c.rank)

        # Can't follow - dump lowest safe card (save high cards)
        safe = [c for c in valid if c.get_value() == 0]
        if safe:
            return min(safe, key=lambda c: c.rank)
        return min(valid, key=lambda c: c.rank)

# =============================================================================
# CONCEPTS SUMMARY:
#   Abstraction:  Player defines the interface (what players must do)
#   Inheritance:  HumanPlayer(Player), AIPlayer(Player), SmartAI(AIPlayer)
#   Polymorphism: All three types have choose_card() - called the same way
#   NotImplementedError: Python way of saying "subclass must override this"
# =============================================================================
