# =============================================================================
# FILE:    card.py
# PURPOSE: Represents one playing card.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHOR:  JEEL — OOP Structure (Core Classes)
# =============================================================================
# OOP CONCEPT — ENCAPSULATION:
#   All card data and behaviour lives inside this class.
#   Other classes ask the card for its value instead of calculating it.
# =============================================================================

class Card:
    """One playing card with a suit and rank."""

    SUITS        = ["C", "D", "S", "H"]
    RANKS        = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    SUIT_NAMES   = {"C": "Clubs", "D": "Diamonds", "S": "Spades", "H": "Hearts"}
    SUIT_SYMBOLS = {"C": "♣", "D": "♦", "S": "♠", "H": "♥"}
    RANK_LABELS  = {11: "J", 12: "Q", 13: "K", 14: "A"}

    def __init__(self, suit, rank):
        """Create a card. Example: Card('H', 14) = Ace of Hearts."""
        self.suit = suit   # 'C', 'D', 'S', or 'H'
        self.rank = rank   # integer 2–14

    def get_value(self):
        """
        Returns penalty points for this card.
          Hearts       = 1 point each
          Queen of Spades = 5 points
          All others   = 0
        """
        if self.suit == "H":
            return 1
        if self.suit == "S" and self.rank == 12:
            return 5
        return 0

    def is_penalty(self):
        """Returns True if this card carries any penalty points."""
        return self.get_value() > 0

    def label(self):
        """Short display text shown on card buttons. Example: 'A♥' or 'Q♠'"""
        rank_str = self.RANK_LABELS.get(self.rank, str(self.rank))
        return rank_str + self.SUIT_SYMBOLS[self.suit]

    def tooltip(self):
        """Full card name + point value shown on mouse hover."""
        val      = self.get_value()
        rank_str = self.RANK_LABELS.get(self.rank, str(self.rank))
        name     = rank_str + " of " + self.SUIT_NAMES[self.suit]
        if val > 0:
            return name + "  (" + str(val) + " penalty pt" + ("s" if val > 1 else "") + ")"
        return name + "  (0 points)"

    def __str__(self):
        """Called by print(card). Example: 'Ace of Hearts'"""
        rank_str = self.RANK_LABELS.get(self.rank, str(self.rank))
        return rank_str + " of " + self.SUIT_NAMES[self.suit]

    def __eq__(self, other):
        """Two cards are equal if they have the same suit and rank."""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        """Needed so Card objects can be used in sets and as dict keys."""
        return hash((self.suit, self.rank))
