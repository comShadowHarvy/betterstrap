"""
This module defines the Card class and related constants for a card game.
"""

# --- ANSI Color Codes ---
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"       # For Hearts/Diamonds
COLOR_BLACK = "\033[30m"     # For Clubs/Spades
COLOR_WHITE_BG = "\033[107m" # White background for cards
COLOR_GREEN = "\033[92m"     # For wins/positive messages
COLOR_YELLOW = "\033[93m"    # For warnings/bets
COLOR_BLUE = "\033[94m"      # For info/player names
COLOR_MAGENTA = "\033[95m"   # For title/special events
COLOR_CYAN = "\033[96m"      # For menu options
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"        # Dim color for hidden card text

# --- Constants ---
SUITS = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
CARD_BACK = "░"

def get_card_color(suit_name):
    """Determines the color for a card based on its suit."""
    return COLOR_RED if suit_name in ['Hearts', 'Diamonds'] else COLOR_BLACK

class Card:
    """Represents a single playing card."""
    def __init__(self, suit_name, rank):
        if suit_name not in SUITS or rank not in RANKS:
            raise ValueError("Invalid suit or rank")
        self.suit_name = suit_name
        self.suit_symbol = SUITS[suit_name]
        self.rank = rank
        self.value = VALUES[rank]
        self.color = get_card_color(suit_name)

    def __str__(self):
        return f"{self.rank}{self.suit_symbol}"

    def is_ace(self):
        return self.rank == 'A'

    def is_face_card(self):
        return self.rank in ['J', 'Q', 'K']

    def get_value(self, is_soft=False):
        if self.is_ace():
            return 11 if is_soft else 1
        return self.value
