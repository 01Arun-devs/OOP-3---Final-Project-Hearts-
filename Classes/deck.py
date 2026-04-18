# =============================================================================
# FILE:    deck.py
# PURPOSE: A full 52-card deck. Builds, shuffles, and deals cards.
# COURSE:  COSC-2200-03 | Durham College | Group 2
# AUTHOR:  JEEL — OOP Structure (Core Classes)
# =============================================================================
# OOP CONCEPT — COMPOSITION:
#   Deck "has" Card objects inside it. Deck is composed of Cards.
# =============================================================================

import random
from card import Card


class Deck:
    """A standard 52-card deck."""

    def __init__(self):
        """Build all 52 cards (4 suits × 13 ranks)."""
        self.cards = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """Randomly mix the deck using Fisher-Yates algorithm."""
        random.shuffle(self.cards)

    def deal(self, num_players):
        """
        Deal all 52 cards evenly to num_players players.
        Returns a list of hands — one list of Card objects per player.
        Uses modulo to cycle through players like dealing around a real table.
        """
        hands = [[] for _ in range(num_players)]
        for i, card in enumerate(self.cards):
            hands[i % num_players].append(card)
        return hands
