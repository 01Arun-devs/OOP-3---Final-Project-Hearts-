# =============================================================================
# FILE:    deck.py
# PURPOSE: A full 52-card deck. Builds, shuffles, and deals cards.
# AUTHOR:  Group 2 - COSC-2200-03
# =============================================================================

import random
from card import Card


class Deck:
    """A standard 52-card deck."""

    def __init__(self):
        """Build all 52 cards (4 suits x 13 ranks)."""
        self.cards = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """Randomly mix the deck."""
        random.shuffle(self.cards)

    def deal(self, num_players):
        """
        Deal all 52 cards evenly.
        Returns a list of hands - one list of cards per player.
        Uses % (modulo) to cycle through players evenly.
        """
        hands = []
        for i in range(num_players):
            hands.append([])

        for i in range(len(self.cards)):
            player_index = i % num_players
            hands[player_index].append(self.cards[i])

        return hands

# =============================================================================
# CONCEPTS USED:
#   random.shuffle(): Python built-in, randomly rearranges a list
#   % modulo:         gives remainder after division, used to cycle 0,1,2,3,0,1,2,3
# =============================================================================
