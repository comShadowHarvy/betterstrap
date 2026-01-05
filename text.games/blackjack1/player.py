"""
This module defines the Player, HumanPlayer, and AIPlayer classes.
"""
import random
import enum
from card import VALUES

class AIType(enum.Enum):
    BASIC = "Basic Strategy"
    CONSERVATIVE = "Conservative"
    AGGRESSIVE = "Aggressive"
    RANDOM = "Random"
    COUNTER = "Card Counter Lite"

class Player:
    """Base class for a player in the game."""
    def __init__(self, name, chips=0):
        self.name = name
        self.chips = chips
        self.hands = []
        self.current_bet = 0

    def __str__(self):
        return self.name

class HumanPlayer(Player):
    """Represents a human player."""
    def __init__(self, name, chips=100):
        super().__init__(name, chips)

class AIPlayer(Player):
    """Represents an AI player."""
    def __init__(self, name, ai_type, chips=100):
        super().__init__(name, chips)
        self.ai_type = ai_type

    def get_decision(self, hand, dealer_up_card_value, true_count=0):
        """Selects the appropriate AI decision function based on type and count."""
        if self.ai_type == AIType.COUNTER:
            return self._ai_decision_counter(hand, dealer_up_card_value, true_count)
        elif self.ai_type == AIType.BASIC:
            return self._ai_decision_basic(hand, dealer_up_card_value)
        elif self.ai_type == AIType.CONSERVATIVE:
            return self._ai_decision_conservative(hand, dealer_up_card_value)
        elif self.ai_type == AIType.AGGRESSIVE:
            return self._ai_decision_aggressive(hand, dealer_up_card_value)
        elif self.ai_type == AIType.RANDOM:
            return random.choice(["hit", "stand"])
        else:
            return self._ai_decision_basic(hand, dealer_up_card_value)

    def _ai_decision_basic(self, hand, dealer_up_card_value):
        """Standard Basic Strategy AI logic."""
        hand_value = self._calculate_hand_value(hand)
        num_aces = sum(1 for card in hand if card.rank == 'A')
        is_soft = num_aces > 0 and hand_value - 10 < 11
        if hand_value < 12: return "hit"
        if is_soft:
            if hand_value == 18 and dealer_up_card_value >= 9: return "hit"
            if hand_value >= 19: return "stand"
            if hand_value <= 17: return "hit"
            return "stand"
        else:
            if hand_value >= 17: return "stand"
            if 13 <= hand_value <= 16: return "stand" if 2 <= dealer_up_card_value <= 6 else "hit"
            if hand_value == 12: return "stand" if 4 <= dealer_up_card_value <= 6 else "hit"
            return "hit"

    def _ai_decision_conservative(self, hand, dealer_up_card_value):
        """Conservative AI: Stands earlier."""
        hand_value = self._calculate_hand_value(hand)
        num_aces = sum(1 for card in hand if card.rank == 'A')
        is_soft = num_aces > 0 and hand_value - 10 < 11
        if hand_value < 11: return "hit"
        if is_soft: return "stand" if hand_value >= 18 else "hit"
        else:
            if hand_value >= 15: return "stand"
            if hand_value >= 12 and dealer_up_card_value <= 6: return "stand"
            return "hit"

    def _ai_decision_aggressive(self, hand, dealer_up_card_value):
        """Aggressive AI: Hits more often."""
        hand_value = self._calculate_hand_value(hand)
        num_aces = sum(1 for card in hand if card.rank == 'A')
        is_soft = num_aces > 0 and hand_value - 10 < 11
        if hand_value < 13: return "hit"
        if is_soft:
            if hand_value == 18 and dealer_up_card_value not in [2, 7, 8]: return "hit"
            if hand_value >= 19: return "stand"
            return "hit"
        else:
            if hand_value >= 17: return "stand"
            if hand_value == 16 and dealer_up_card_value <= 6 and random.random() < 0.4: return "hit"
            if hand_value >= 12 and dealer_up_card_value >= 7: return "hit"
            if 13 <= hand_value <= 16: return "stand"
            if hand_value == 12: return "stand" if dealer_up_card_value >= 4 else "hit"
            return "hit"

    def _ai_decision_counter(self, hand, dealer_up_card_value, true_count):
        """Card Counter Lite AI: Modifies basic strategy based on true count."""
        decision = self._ai_decision_basic(hand, dealer_up_card_value)
        hand_value = self._calculate_hand_value(hand)
        if true_count >= 2:
            if decision == "stand" and hand_value in [15, 16] and dealer_up_card_value >= 7: decision = "hit"
        elif true_count <= -1:
            if decision == "hit" and hand_value == 12 and dealer_up_card_value <= 6: decision = "stand"
            elif decision == "hit" and hand_value == 13 and dealer_up_card_value <= 3: decision = "stand"
        return decision

    def _calculate_hand_value(self, hand):
        """Calculates the value of a hand in Blackjack."""
        if not hand: return 0
        value = 0
        num_aces = 0
        for card in hand:
            value += card.value
            if card.rank == 'A': num_aces += 1
        while value > 21 and num_aces:
            value -= 10
            num_aces -= 1
        return value
