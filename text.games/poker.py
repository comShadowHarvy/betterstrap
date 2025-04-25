import random
import time
import os
import sys
import enum
import json
import re
from collections import Counter, namedtuple

# --- ANSI Color Codes (Reused) ---
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"       # For Hearts/Diamonds
COLOR_BLACK = "\033[30m"     # For Clubs/Spades
COLOR_WHITE_BG = "\033[107m" # White background for cards
COLOR_GREEN = "\033[92m"     # For wins/positive messages/Check/Call
COLOR_YELLOW = "\033[93m"    # For warnings/bets/Raise
COLOR_BLUE = "\033[94m"      # For info/player names
COLOR_MAGENTA = "\033[95m"   # For title/special events/Pot
COLOR_CYAN = "\033[96m"      # For menu options/Community Cards
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"        # Dim color for folded players/hidden cards

# --- Constants ---
SUITS = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'] # T for 10
# Rank values for sorting and straight checking (Ace low/high handled separately)
RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

# Poker Hand Rankings
HandRanking = enum.IntEnum('HandRanking', [
    'HIGH_CARD', 'ONE_PAIR', 'TWO_PAIR', 'THREE_OF_A_KIND',
    'STRAIGHT', 'FLUSH', 'FULL_HOUSE', 'FOUR_OF_A_KIND',
    'STRAIGHT_FLUSH', 'ROYAL_FLUSH'
])
HAND_NAMES = {
    HandRanking.HIGH_CARD: "High Card", HandRanking.ONE_PAIR: "One Pair", HandRanking.TWO_PAIR: "Two Pair",
    HandRanking.THREE_OF_A_KIND: "Three of a Kind", HandRanking.STRAIGHT: "Straight", HandRanking.FLUSH: "Flush",
    HandRanking.FULL_HOUSE: "Full House", HandRanking.FOUR_OF_A_KIND: "Four of a Kind",
    HandRanking.STRAIGHT_FLUSH: "Straight Flush", HandRanking.ROYAL_FLUSH: "Royal Flush"
}

AI_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah"] # Poker table usually smaller
MIN_PLAYERS = 2 # Including player
MAX_PLAYERS = 6 # Max players at the table
CARD_BACK = "░"
STARTING_CHIPS = 1000 # Typical starting stack for poker
SMALL_BLIND_AMOUNT = 10
BIG_BLIND_AMOUNT = 20
SAVE_FILE = "poker_save.json" # Filename for save/load
DEFAULT_TERMINAL_WIDTH = 80

# --- Global Variable for Terminal Width ---
TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH

# --- Enums ---
class GamePhase(enum.Enum):
    PREFLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"

class PlayerAction(enum.Enum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    BET = 3
    RAISE = 4
    ALL_IN = 5

class AIType(enum.Enum):
    TIGHT_PASSIVE = "Tight Passive (Rock)" # Folds often, calls/checks mostly
    LOOSE_AGGRESSIVE = "Loose Aggressive (Maniac)" # Plays many hands, bets/raises often
    TIGHT_AGGRESSIVE = "Tight Aggressive (Shark)" # Plays few hands, bets/raises strongly
    RANDOM = "Random"

# --- AI Chat Lines (Poker Themed) ---
AI_CHAT = {
    "preflop_raise": ["Let's spice things up.", "Putting pressure on.", "Feeling good about these.", "Raise it up!"],
    "preflop_call": ["I'll see that.", "Worth a look.", "Let's see a flop.", "Calling."],
    "preflop_fold": ["Not this time.", "Too rich for my blood.", "Gotta fold.", "Saving my chips."],
    "flop_hit": ["Nice flop!", "That helped!", "Looking good now.", "Connected!"],
    "flop_miss": ["Brutal flop.", "Didn't help much.", "Nothing there.", "Air ball."],
    "turn_river_bet": ["Value bet.", "Trying to build the pot.", "Think I'm ahead.", "Betting."],
    "turn_river_check": ["Checking it down.", "Pot control.", "Let's see the next card.", "Check."],
    "showdown_win": ["Winner!", "Got lucky!", "Read 'em and weep!", "Ship it!", "Nice pot!"],
    "showdown_loss": ["Darn!", "You got me.", "Close one.", "Good hand.", "Unlucky."],
    "taunt": ["Easy money!", "Feeling confident?", "You gonna call that?", "Is that all you've got?", "Scared money don't make money!"],
    "compliment": ["Nice bet.", "Good call.", "Well played.", "Strong move."],
    "general_insult": ["Are you even trying?", "What was that?", "Seriously?", "..."]
}

# --- Helper Functions (Adapted/Reused) ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.03, color=COLOR_RESET, newline=True):
    """Prints text with a typing effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char); sys.stdout.flush(); time.sleep(delay)
    sys.stdout.write(COLOR_RESET)
    if newline: print()

def get_card_color(suit_name):
    """Determines the color for a card based on its suit."""
    return COLOR_RED if suit_name in ['Hearts', 'Diamonds'] else COLOR_BLACK

def create_deck():
    """Creates a standard 52-card deck."""
    deck = []
    for suit_name in SUITS:
        for rank in RANKS:
            deck.append({'suit': suit_name, 'symbol': SUITS[suit_name], 'rank': rank, 'value': RANK_VALUES[rank]})
    return deck

def display_card(card, hidden=False):
    """Returns the string representation of a card with color."""
    card_width = 11 # Width of the card display
    if hidden:
        back = CARD_BACK * (card_width - 2)
        lines = [f"┌{'─' * (card_width - 2)}┐", f"│{back}│", f"│{back}│", f"│{COLOR_DIM}{' HIDDEN '.center(card_width - 2)}{COLOR_RESET}{COLOR_WHITE_BG}{COLOR_BLACK}│", f"│{back}│", f"│{back}│", f"└{'─' * (card_width - 2)}┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

    if not isinstance(card, dict) or 'suit' not in card or 'symbol' not in card or 'rank' not in card:
        print(f"{COLOR_RED}Error: Invalid card data format: {card}{COLOR_RESET}")
        lines = [f"┌{'─' * (card_width - 2)}┐", f"│ {'ERROR'.center(card_width - 4)} │", f"│ {'INVALID'.center(card_width - 4)} │", f"│ {' CARD '.center(card_width - 4)} │", f"│ {' DATA '.center(card_width - 4)} │", f"│ {' '.center(card_width - 4)} │", f"└{'─' * (card_width - 2)}┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_RED}{line}{COLOR_RESET}" for line in lines]

    suit_name, suit_symbol, rank = card['suit'], card['symbol'], card['rank']
    card_color = get_card_color(suit_name)
    rank_str = rank.ljust(2) # Left-align rank (e.g., 'T ' or 'A ')

    lines = [
        f"┌{'─' * (card_width - 2)}┐",
        f"│ {card_color}{rank_str}{COLOR_BLACK}{' ' * (card_width - 5)}│", # Rank top-left
        f"│ {' ' * (card_width - 2)} │",
        f"│ {card_color}{suit_symbol.center(card_width - 4)}{COLOR_BLACK} │", # Suit centered
        f"│ {' ' * (card_width - 2)} │",
        f"│ {' ' * (card_width - 7)}{card_color}{rank_str}{COLOR_BLACK} │", # Rank bottom-right (adjust spacing)
        f"└{'─' * (card_width - 2)}┘"
    ]
    return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]


def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_visible_width(text):
    """Calculates the visible width of a string after stripping ANSI codes."""
    return len(strip_ansi_codes(text))

def center_text(text, width):
    """Centers text within a given width, accounting for ANSI codes."""
    visible_width = get_visible_width(text)
    padding = (width - visible_width) // 2
    if padding < 0: padding = 0
    return " " * padding + text

def shuffle_animation(duration=1.5):
    """Displays a visual shuffling animation."""
    clear_screen(); print(f"{COLOR_YELLOW}Shuffling Deck...{COLOR_RESET}")
    symbols = ['♠', '♥', '♦', '♣', CARD_BACK, '?']; colors = [COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN]
    width = 40; lines = 5; end_time = time.time() + duration
    while time.time() < end_time:
        output_lines = []
        for _ in range(lines):
            line = "".join(f"{random.choice(colors)}{random.choice(symbols)}{COLOR_RESET}" if random.random() < 0.3 else " " for _ in range(width))
            output_lines.append(line)
        sys.stdout.write(f"\033[{lines}A") # Move cursor up
        for line in output_lines: sys.stdout.write(f"\r{line.ljust(width)}\n") # Overwrite lines
        sys.stdout.flush(); time.sleep(0.05)
    clear_screen(); print(f"{COLOR_GREEN}Deck Shuffled!{COLOR_RESET}"); time.sleep(0.5)

def title_screen():
    """Displays a simplified, animated title screen for Poker."""
    clear_screen(); title = "T E X A S   H O L D ' E M"; author = "Adapted by AI from ShadowHarvy's Blackjack"
    card_width = 11; screen_width = TERMINAL_WIDTH
    print("\n" * 5); typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_GREEN + COLOR_BOLD); print("\n")
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width)); time.sleep(0.5)
    temp_deck = create_deck(); random.shuffle(temp_deck)
    # Deal two iconic poker cards (e.g., Aces)
    dealt_card1 = temp_deck.pop() if temp_deck else {'suit': 'Spades', 'symbol': '♠', 'rank': 'A', 'value': 14}
    dealt_card2 = temp_deck.pop() if temp_deck else {'suit': 'Hearts', 'symbol': '♥', 'rank': 'A', 'value': 14}
    card1_lines = display_card(dealt_card1); card2_lines = display_card(dealt_card2)
    total_card_width = card_width * 2 + 2; left_padding = (screen_width - total_card_width) // 2; padding_str = " " * left_padding
    current_lines = [""] * (5 + 1 + 1 + 7 + 1); line_offset = 6 # Adjust line count based on card height (7)
    for i in range(len(card1_lines)): # Animate deal 1
        clear_screen(); current_lines[5] = center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width)
        current_lines[line_offset] = center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width)
        for j in range(i + 1): current_lines[line_offset + 2 + j] = f"{padding_str}{card1_lines[j]}"
        for k in range(i + 1, len(card1_lines)): current_lines[line_offset + 2 + k] = ""
        print("\n".join(current_lines)); time.sleep(0.1)
    for i in range(len(card2_lines)): # Animate deal 2
        clear_screen(); current_lines[5] = center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width)
        current_lines[line_offset] = center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width)
        for j in range(len(card1_lines)):
            line1_part = card1_lines[j]; line2_part = card2_lines[j] if j <= i else " " * card_width
            current_lines[line_offset + 2 + j] = f"{padding_str}{line1_part}  {line2_part}"
        print("\n".join(current_lines)); time.sleep(0.1)
    clear_screen(); current_lines[5] = center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width)
    current_lines[line_offset] = "";
    for j in range(len(card1_lines)): current_lines[line_offset + 2 + j] = f"{padding_str}{card1_lines[j]}  {card2_lines[j]}"
    current_lines.append(""); current_lines.append(center_text(f"{COLOR_CYAN}{author}{COLOR_RESET}", screen_width)); current_lines.append("\n")
    print("\n".join(current_lines)); time.sleep(2)

def display_menu():
    """Displays the main menu and gets user choice."""
    print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Poker Main Menu ---{COLOR_RESET}")
    print(f"[{COLOR_CYAN}1{COLOR_RESET}] Play Texas Hold'em (vs AI)")
    print(f"[{COLOR_CYAN}2{COLOR_RESET}] View Rules")
    print(f"[{COLOR_CYAN}3{COLOR_RESET}] Settings (Coming Soon)") # Simplified for now
    print(f"[{COLOR_CYAN}4{COLOR_RESET}] View Stats")
    print(f"[{COLOR_CYAN}5{COLOR_RESET}] Save Game")
    print(f"[{COLOR_CYAN}6{COLOR_RESET}] Load Game")
    print(f"[{COLOR_CYAN}7{COLOR_RESET}] Quit")
    print("-" * 30)
    while True:
        choice = input(f"{COLOR_YELLOW}Enter your choice (1-7): {COLOR_RESET}")
        if choice in [str(i) for i in range(1, 8)]: return choice
        else: print(f"{COLOR_RED}Invalid choice. Please enter 1-7.{COLOR_RESET}")

def display_rules():
    """Displays the basic rules of Texas Hold'em."""
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Texas Hold'em Rules ---{COLOR_RESET}")
    rules = [
        "- Goal: Win chips by having the best 5-card poker hand or by getting others to fold.",
        "- The Deck: Standard 52-card deck.",
        "- Blinds: Forced bets (Small and Big Blind) posted before cards are dealt.",
        "- Hole Cards: Each player gets 2 private cards.",
        "- Betting Rounds: Occur Pre-Flop, on the Flop, Turn, and River.",
        "- Community Cards: 5 cards dealt face-up in the middle (Flop=3, Turn=1, River=1).",
        "- Making a Hand: Use any combination of your 2 hole cards and the 5 community cards to make the best 5-card hand.",
        "- Actions: Check (pass if no bet), Bet (start betting), Call (match current bet), Raise (increase current bet), Fold (discard hand).",
        "- Showdown: If multiple players remain after the final betting round, hands are revealed. Best hand wins the pot.",
        "- Hand Rankings (Highest to Lowest): Royal Flush, Straight Flush, 4 of a Kind, Full House, Flush, Straight, 3 of a Kind, Two Pair, One Pair, High Card."
    ]
    for rule in rules: print(f"{COLOR_BLUE} {rule}{COLOR_RESET}"); time.sleep(0.1)
    print("-" * 25); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

def display_settings_menu(settings):
    """Displays settings (placeholder)."""
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Settings ---{COLOR_RESET}")
    print(f"{COLOR_DIM}[ Settings are currently fixed ]{COLOR_RESET}")
    print(f"Starting Chips: {settings['starting_chips']}")
    print(f"Small Blind: {settings['small_blind']}")
    print(f"Big Blind: {settings['big_blind']}")
    print("-" * 30); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

def display_stats(stats):
    """Displays session statistics (adapted for poker)."""
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Session Statistics ---{COLOR_RESET}")
    print(f"Hands Played: {COLOR_CYAN}{stats['hands_played']}{COLOR_RESET}")
    print(f"Hands Won at Showdown: {COLOR_GREEN}{stats['hands_won_showdown']}{COLOR_RESET}")
    print(f"Hands Won by Fold: {COLOR_YELLOW}{stats['hands_won_fold']}{COLOR_RESET}")
    print(f"Total Pots Won: {COLOR_GREEN}{stats['pots_won']}{COLOR_RESET}")
    net_chips = stats['chips_won'] - stats['chips_lost']
    chip_color = COLOR_GREEN if net_chips >= 0 else COLOR_RED
    print(f"Net Chips: {chip_color}{net_chips:+}{COLOR_RESET}")
    print("-" * 30); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

# --- Poker Hand Evaluation ---

# Card namedtuple for convenience in evaluation
Card = namedtuple("Card", ['rank', 'suit', 'value'])

def evaluate_hand(hole_cards, community_cards):
    """
    Evaluates the best 5-card poker hand from 7 cards (2 hole + 5 community).
    Returns a tuple: (HandRanking enum, list of 5 card ranks for kickers/comparison).
    """
    if not hole_cards: return (HandRanking.HIGH_CARD, [0]) # Handle cases with no hole cards gracefully
    all_cards = [Card(c['rank'], c['suit'], c['value']) for c in hole_cards + community_cards]
    best_rank = HandRanking.HIGH_CARD
    best_kickers = [0] * 5 # Store the ranks of the best 5 cards

    # Iterate through all combinations of 5 cards from the 7 available
    from itertools import combinations
    possible_5_card_hands = list(combinations(all_cards, 5))

    if not possible_5_card_hands: # Should not happen if hole_cards exist
         # If only community cards exist (e.g., player folded pre-flop but somehow evaluated)
         if len(all_cards) >= 5:
             return (HandRanking.HIGH_CARD, [c.value for c in sorted(all_cards, key=lambda x: x.value, reverse=True)][:5])
         else: # Not enough cards to make a 5-card hand
             return (HandRanking.HIGH_CARD, [c.value for c in sorted(all_cards, key=lambda x: x.value, reverse=True)] + [0]*(5-len(all_cards)))


    for hand_tuple in possible_5_card_hands:
        hand = list(hand_tuple) # Convert tuple to list for sorting
        hand.sort(key=lambda x: x.value, reverse=True) # Sort by rank descending
        ranks = [c.value for c in hand]
        suits = [c.suit for c in hand]
        rank_counts = Counter(ranks)
        is_flush = len(set(suits)) == 1
        # Check for straight: Difference between max and min rank is 4, and no duplicates
        # Need to handle Ace-low straight (A, 2, 3, 4, 5) -> ranks [14, 5, 4, 3, 2]
        is_straight = False
        straight_high_card = 0 # Initialize straight high card value
        unique_ranks = sorted(list(set(ranks)), reverse=True)
        if len(unique_ranks) >= 5:
            # Normal straight check
            for i in range(len(unique_ranks) - 4):
                if all(unique_ranks[i] - j == unique_ranks[i+j] for j in range(5)):
                    is_straight = True
                    straight_high_card = unique_ranks[i]
                    break
            # Ace-low straight check (5, 4, 3, 2, A)
            # Check if 14 (Ace) and 2,3,4,5 are present in the 7 cards (not just the 5-card combo)
            # Use the original all_cards for this check
            all_card_ranks = {c.value for c in all_cards}
            if {14, 2, 3, 4, 5}.issubset(all_card_ranks):
                 # Now check if the current 5-card hand *is* the A-2-3-4-5 straight
                 if set(ranks) == {14, 2, 3, 4, 5}:
                      is_straight = True
                      straight_high_card = 5 # High card is 5 for A-2-3-4-5

        current_rank = HandRanking.HIGH_CARD
        kickers = sorted(ranks, reverse=True)[:5] # Default kickers are the 5 highest cards

        # --- Determine Hand Rank ---
        is_royal_flush = False
        is_straight_flush = False
        if is_straight and is_flush:
             is_straight_flush = True
             if straight_high_card == 14: # Check if the straight flush is Ace high
                  is_royal_flush = True


        counts = sorted(rank_counts.values(), reverse=True)
        most_common_ranks = sorted([r for r, c in rank_counts.items()], key=lambda item: (rank_counts[item], item), reverse=True)


        is_four_of_a_kind = counts[0] == 4
        is_full_house = counts == [3, 2]
        # is_flush checked above
        # is_straight checked above
        is_three_of_a_kind = counts[0] == 3 and len(counts) > 1 and counts[1] == 1 # Ensure not full house
        is_two_pair = counts == [2, 2, 1]
        is_one_pair = counts == [2, 1, 1, 1]

        # --- Assign Rank and Kickers ---
        if is_royal_flush:
            current_rank = HandRanking.ROYAL_FLUSH
            kickers = [14, 13, 12, 11, 10] # Fixed kickers for Royal Flush
        elif is_straight_flush:
            current_rank = HandRanking.STRAIGHT_FLUSH
            # Kicker is the highest card of the straight flush
            kickers = [straight_high_card] + [0]*4 if straight_high_card != 5 else [5, 4, 3, 2, 1] # Ace-low case
        elif is_four_of_a_kind:
            current_rank = HandRanking.FOUR_OF_A_KIND
            four_rank = most_common_ranks[0]
            kicker = most_common_ranks[1] # The rank with count 1
            kickers = [four_rank] * 4 + [kicker]
        elif is_full_house:
            current_rank = HandRanking.FULL_HOUSE
            three_rank = most_common_ranks[0] # Rank with count 3
            pair_rank = most_common_ranks[1] # Rank with count 2
            kickers = [three_rank] * 3 + [pair_rank] * 2
        elif is_flush:
            current_rank = HandRanking.FLUSH
            kickers = sorted(ranks, reverse=True)[:5] # Top 5 cards of the flush suit
        elif is_straight:
            current_rank = HandRanking.STRAIGHT
            # Kicker is the highest card of the straight
            kickers = [straight_high_card] + [0]*4 if straight_high_card != 5 else [5, 4, 3, 2, 1] # Ace-low case
        elif is_three_of_a_kind:
            current_rank = HandRanking.THREE_OF_A_KIND
            three_rank = most_common_ranks[0] # Rank with count 3
            other_kickers = sorted([r for r in most_common_ranks if rank_counts[r] == 1], reverse=True)
            kickers = [three_rank] * 3 + other_kickers[:2]
        elif is_two_pair:
            current_rank = HandRanking.TWO_PAIR
            pair_ranks = sorted([r for r in most_common_ranks if rank_counts[r] == 2], reverse=True)
            kicker = [r for r in most_common_ranks if rank_counts[r] == 1][0]
            kickers = [pair_ranks[0]]*2 + [pair_ranks[1]]*2 + [kicker]
        elif is_one_pair:
            current_rank = HandRanking.ONE_PAIR
            pair_rank = most_common_ranks[0] # Rank with count 2
            other_kickers = sorted([r for r in most_common_ranks if rank_counts[r] == 1], reverse=True)
            kickers = [pair_rank]*2 + other_kickers[:3]
        else: # High Card
            current_rank = HandRanking.HIGH_CARD
            kickers = sorted(ranks, reverse=True)[:5]

        # --- Update Best Hand Found So Far ---
        current_kickers_filled = (kickers + [0]*5)[:5] # Ensure kickers list has 5 elements

        # Compare current hand rank with the best rank found
        if current_rank > best_rank:
            best_rank = current_rank
            best_kickers = current_kickers_filled # Ensure kickers are sorted high to low and padded
        # If ranks are equal, compare kickers element by element
        elif current_rank == best_rank:
            # Compare padded kicker lists element by element
            for i in range(5):
                if current_kickers_filled[i] > best_kickers[i]:
                    best_kickers = current_kickers_filled
                    break # Found a better kicker, stop comparing this hand
                elif current_kickers_filled[i] < best_kickers[i]:
                    break # Found a worse kicker, stop comparing this hand
                # If kickers at this position are equal, continue to the next

    # Return the best rank found and its corresponding 5 kickers
    return (best_rank, best_kickers)


# --- AI Player Logic (Simplified Poker AI) ---

def get_ai_decision(ai_player, game_state):
    """Determines the AI's action based on its type and the game state."""
    ai_type = ai_player['ai_type']
    hole_cards = ai_player['hand']
    community_cards = game_state['community_cards']
    current_bet = game_state['current_bet']
    ai_bet_this_round = ai_player['bet_this_round']
    pot_size = game_state['pot']
    ai_chips = ai_player['chips']
    players_in_hand = game_state['players_in_hand'] # Count of active players
    phase = game_state['phase']

    # Basic hand strength evaluation (very simplified)
    hand_rank, _ = evaluate_hand(hole_cards, community_cards)
    hand_strength = hand_rank.value # Higher value = better hand rank

    # Calculate amount needed to call
    call_amount = current_bet - ai_bet_this_round
    can_call = ai_chips >= call_amount and call_amount > 0 # Can only call if there's a bet > 0
    can_check = call_amount <= 0 # Can check if no bet to call

    # --- AI Decision Logic ---
    action = PlayerAction.FOLD
    amount = 0 # This will be the amount committed NOW for most actions, or TOTAL bet for RAISE

    # Pre-flop adjustments (based only on hole cards)
    preflop_strength = 0
    if phase == GamePhase.PREFLOP and len(hole_cards) == 2:
        r1, r2 = sorted([RANK_VALUES[c['rank']] for c in hole_cards], reverse=True)
        s1, s2 = [c['suit'] for c in hole_cards]
        is_pair = (r1 == r2)
        is_suited = (s1 == s2)
        is_connector = abs(r1 - r2) == 1 or (r1 == 14 and r2 == 5) # A-5 connector for wheel straight
        is_gapper = abs(r1 - r2) == 2

        if is_pair: preflop_strength += r1 + 5 # Higher pair is much better preflop
        if r1 >= 10 or r2 >= 10: preflop_strength += (r1 + r2) / 4 # High cards help
        if is_suited: preflop_strength += 3
        if is_connector: preflop_strength += 2
        if is_gapper: preflop_strength += 1
        # Normalize strength roughly 0-25
        preflop_strength = min(25, preflop_strength)
        hand_strength = preflop_strength # Use preflop strength before flop

    # --- AI Type Specific Logic ---

    # ** Tight Passive (Rock) **
    if ai_type == AIType.TIGHT_PASSIVE:
        # Slightly lower fold threshold preflop
        fold_threshold = 5 if phase == GamePhase.PREFLOP else HandRanking.ONE_PAIR.value + 1
        call_threshold = 12 if phase == GamePhase.PREFLOP else HandRanking.TWO_PAIR.value
        if hand_strength < fold_threshold:
            action = PlayerAction.FOLD if not can_check else PlayerAction.CHECK
        elif hand_strength < call_threshold:
            action = PlayerAction.CALL if can_call else PlayerAction.CHECK
        else: # Strong hand
            action = PlayerAction.CALL if can_call else PlayerAction.CHECK # Rarely bets/raises

    # ** Loose Aggressive (Maniac) **
    elif ai_type == AIType.LOOSE_AGGRESSIVE:
        aggression_chance = 0.5 if phase != GamePhase.PREFLOP else 0.4
        # Consider calling more often instead of folding weak hands
        fold_condition = True # Assume fold initially
        if hand_strength >= HandRanking.HIGH_CARD.value + 1 or (phase == GamePhase.PREFLOP and hand_strength > 3):
             fold_condition = False # Don't fold marginal hands immediately

        if random.random() < aggression_chance and ai_chips > 0: # Aggressive action
            if can_call and ai_chips > call_amount:
                 action = PlayerAction.RAISE
                 min_raise_increment = max(game_state.get('last_raiser_amount', BIG_BLIND_AMOUNT), BIG_BLIND_AMOUNT)
                 min_raise_total = current_bet + min_raise_increment
                 raise_target = random.randint(min_raise_total, max(min_raise_total, current_bet + pot_size))
                 amount = min(ai_chips + ai_bet_this_round, raise_target)
            elif can_check:
                 action = PlayerAction.BET
                 bet_target = random.randint(BIG_BLIND_AMOUNT, max(BIG_BLIND_AMOUNT, pot_size))
                 amount = min(ai_chips, bet_target)
            elif can_call:
                 action = PlayerAction.CALL
            else:
                 action = PlayerAction.FOLD
        elif not fold_condition: # Passive action with marginal hand
             action = PlayerAction.CALL if can_call else PlayerAction.CHECK
        else: # Weak hand, not bluffing
             action = PlayerAction.FOLD if not can_check else PlayerAction.CHECK

    # ** Tight Aggressive (Shark) **
    elif ai_type == AIType.TIGHT_AGGRESSIVE:
        # Slightly lower fold threshold preflop
        fold_threshold = 7 if phase == GamePhase.PREFLOP else HandRanking.ONE_PAIR.value + 2
        bet_threshold = 14 if phase == GamePhase.PREFLOP else HandRanking.TWO_PAIR.value + 1
        if hand_strength < fold_threshold: # Weak hand
             action = PlayerAction.FOLD if not can_check else PlayerAction.CHECK
        elif hand_strength >= bet_threshold and ai_chips > 0: # Strong hand -> Bet/Raise
             if can_call and ai_chips > call_amount:
                 action = PlayerAction.RAISE
                 min_raise_increment = max(game_state.get('last_raiser_amount', BIG_BLIND_AMOUNT), BIG_BLIND_AMOUNT)
                 min_raise_total = current_bet + min_raise_increment
                 raise_target = current_bet + max(min_raise_increment, int(pot_size * random.uniform(0.5, 1.2)))
                 amount = min(ai_chips + ai_bet_this_round, raise_target)
             elif can_check:
                 action = PlayerAction.BET
                 bet_target = max(BIG_BLIND_AMOUNT, int(pot_size * random.uniform(0.5, 1.0)))
                 amount = min(ai_chips, bet_target)
             elif can_call:
                 action = PlayerAction.CALL
             else:
                 action = PlayerAction.CHECK
        else: # Medium strength hand -> Call/Check
             action = PlayerAction.CALL if can_call else PlayerAction.CHECK

    # ** Random **
    elif ai_type == AIType.RANDOM:
        possible_actions = []
        if can_check: possible_actions.extend([PlayerAction.CHECK, PlayerAction.BET])
        if can_call: possible_actions.extend([PlayerAction.CALL, PlayerAction.RAISE])
        possible_actions.append(PlayerAction.FOLD)
        # Remove impossible actions
        if not can_check: possible_actions = [a for a in possible_actions if a != PlayerAction.CHECK]
        if not can_call: possible_actions = [a for a in possible_actions if a != PlayerAction.CALL]
        if not (can_check and ai_chips > 0) : possible_actions = [a for a in possible_actions if a != PlayerAction.BET]
        min_raise_increment = max(game_state.get('last_raiser_amount', BIG_BLIND_AMOUNT), BIG_BLIND_AMOUNT)
        if not (can_call and ai_chips > call_amount and ai_chips >= call_amount + min_raise_increment):
             possible_actions = [a for a in possible_actions if a != PlayerAction.RAISE]

        if not possible_actions: action = PlayerAction.FOLD
        else: action = random.choice(possible_actions)

        if action == PlayerAction.BET:
             bet_target = random.randint(BIG_BLIND_AMOUNT, max(BIG_BLIND_AMOUNT, pot_size // 2))
             amount = min(ai_chips, bet_target)
        elif action == PlayerAction.RAISE:
             min_raise_total = current_bet + min_raise_increment
             raise_target = random.randint(min_raise_total, max(min_raise_total, current_bet + pot_size // 2))
             amount = min(ai_chips + ai_bet_this_round, raise_target)


    # --- Pot Odds Consideration (Simplified) ---
    # If AI decided to fold based purely on strength, check pot odds
    if action == PlayerAction.FOLD and can_call and ai_type != AIType.TIGHT_PASSIVE:
        required_equity = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1
        # If getting very good odds (e.g., need less than 20% equity), consider calling
        if required_equity < 0.20:
            # Add randomness: sometimes call even with bad odds if LAG
            if ai_type == AIType.LOOSE_AGGRESSIVE and random.random() < 0.3:
                 action = PlayerAction.CALL
                 print(f"{COLOR_DIM}(AI {ai_player.get('name','')} calling based on odds/bluff){COLOR_RESET}")
            elif required_equity < 0.15 : # Call if odds are extremely good
                 action = PlayerAction.CALL
                 print(f"{COLOR_DIM}(AI {ai_player.get('name','')} calling based on pot odds){COLOR_RESET}")


    # --- Final Action Adjustments ---
    # 1. Adjust Amount based on Action and Chips
    if action == PlayerAction.FOLD or action == PlayerAction.CHECK:
        amount = 0
    elif action == PlayerAction.CALL:
        amount = min(ai_chips, call_amount) # Amount committed now
    elif action == PlayerAction.BET:
        amount = min(ai_chips, amount) # Amount committed now
    elif action == PlayerAction.RAISE:
        # 'amount' currently holds the TOTAL target bet. Calculate amount needed now.
        amount_needed_now = amount - ai_bet_this_round
        amount = min(ai_chips, amount_needed_now) # Amount committed now, capped by chips
    # ALL_IN amount is handled below

    # 2. Check for All-In situations
    is_all_in = False
    # Check if committing the 'amount' uses up all chips
    if action != PlayerAction.FOLD and action != PlayerAction.CHECK and amount >= ai_chips:
        is_all_in = True
    elif action == PlayerAction.ALL_IN: # Explicit All-in choice
        is_all_in = True

    if is_all_in:
        action = PlayerAction.ALL_IN # Set action type correctly
        amount = ai_chips # Ensure amount is exactly the remaining chips

    # 3. Validate Raise Amount (if action is still RAISE after all-in check)
    if action == PlayerAction.RAISE:
         total_bet_after_raise = ai_bet_this_round + amount
         actual_raise_increment = total_bet_after_raise - current_bet
         min_raise_increment = max(game_state.get('last_raiser_amount', BIG_BLIND_AMOUNT), BIG_BLIND_AMOUNT)

         # If raise increment is too small (and not an all-in), convert to Call
         if actual_raise_increment < min_raise_increment:
              print(f"{COLOR_DIM}(AI {ai_player.get('name', 'Unknown')} invalid raise increment, converting to call){COLOR_RESET}")
              action = PlayerAction.CALL
              amount = min(ai_chips, call_amount) # Amount committed now is call amount
              if amount >= ai_chips: # Check if call becomes all-in
                   action = PlayerAction.ALL_IN
                   amount = ai_chips


    # --- Return Action and Amount ---
    if action == PlayerAction.RAISE:
         total_bet_target = ai_bet_this_round + amount # Calculate the total bet
         return action, total_bet_target # Return RAISE and the total target amount
    else:
         return action, amount # Return action and chips committed now


# --- Game Class ---
class PokerGame:
    def __init__(self, settings=None, stats=None):
        self.deck = []
        self.players = {} # {name: {hand: [], chips: int, bet_this_round: int, folded: bool, is_ai: bool, ai_type: AIType/None, is_all_in: bool}}
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0 # The highest total bet amount placed in the current round
        self.last_raiser = None # Name of the last player to bet/raise
        self.last_raiser_amount = 0 # Amount of the last bet/raise increment
        self.dealer_button_pos = 0 # Index of the player with the dealer button IN self.player_order
        self.current_player_index = 0 # Index relative to current betting order
        self.phase = GamePhase.PREFLOP
        self.settings = settings if settings is not None else self._default_settings()
        self.session_stats = stats if stats is not None else self._default_stats()
        self.player_order = [] # Initialize player_order list here
        self._initialize_players() # Populate players and player_order
        self._create_and_shuffle_deck()
        # self.player_order = [] # REMOVED: This line caused the error by resetting the order

    def _default_settings(self):
        return {'starting_chips': STARTING_CHIPS, 'small_blind': SMALL_BLIND_AMOUNT, 'big_blind': BIG_BLIND_AMOUNT, 'num_ai': 2}

    def _default_stats(self):
        return {'hands_played': 0, 'hands_won_showdown': 0, 'hands_won_fold': 0,
                'pots_won': 0, 'chips_won': 0, 'chips_lost': 0}

    def _create_and_shuffle_deck(self):
        """Creates and shuffles the deck."""
        self.deck = create_deck()
        random.shuffle(self.deck)

    def _initialize_players(self):
        """Sets up the player and AI opponents."""
        self.players = {}
        player_name = "Player" # Assume player is always named "Player"
        self.players[player_name] = {
            'hand': [], 'chips': self.settings['starting_chips'], 'bet_this_round': 0,
            'folded': False, 'is_ai': False, 'ai_type': None, 'is_all_in': False, 'last_action': None
        }

        num_ai = self.settings.get('num_ai', random.randint(1, MAX_PLAYERS - 1))
        num_ai = min(num_ai, MAX_PLAYERS - 1) # Ensure total players <= MAX_PLAYERS
        available_names = random.sample([name for name in AI_NAMES if name != player_name], k=min(len(AI_NAMES)-1, num_ai))

        for name in available_names:
            ai_type = random.choice(list(AIType))
            self.players[name] = {
                'hand': [], 'chips': self.settings['starting_chips'], 'bet_this_round': 0,
                'folded': False, 'is_ai': True, 'ai_type': ai_type, 'is_all_in': False, 'last_action': None
            }
        # Establish a fixed table order, e.g., Player first then AIs
        self.player_order = [player_name] + available_names # Set player order HERE
        self.dealer_button_pos = random.randint(0, len(self.player_order) - 1)

    def _deal_card(self):
        """Deals a single card, reshuffles if necessary."""
        if not self.deck:
            print(f"{COLOR_YELLOW}Deck empty, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck()
        if not self.deck:
            sys.exit(f"{COLOR_RED}Critical error: Cannot deal from empty deck.{COLOR_RESET}")
        return self.deck.pop()

    def _ai_chat(self, category, player_name=None):
        """Makes an AI player say something based on category."""
        # Only AI players who are still in the hand (not folded) can chat
        ai_players_in_game = [name for name, data in self.players.items() if data['is_ai'] and not data['folded']]
        if not ai_players_in_game: return

        # Allow the specific player who acted to chat, or pick a random active AI
        chatter_name = player_name
        # Ensure chatter_name is an AI and still in the game before chatting
        # Also check if the player exists in self.players dictionary
        if chatter_name not in self.players or chatter_name not in ai_players_in_game or not self.players[chatter_name]['is_ai']:
            chatter_name = random.choice(ai_players_in_game)

        if random.random() < 0.3: # Chance to speak
            chat_list = AI_CHAT.get(category)
            if chat_list:
                message = random.choice(chat_list)
                # Include AI type in chat message for clarity
                print(f"{COLOR_CYAN}[{chatter_name} ({self.players[chatter_name]['ai_type'].value})]: {message}{COLOR_RESET}")
                time.sleep(1.0 + random.random() * 0.5) # Slightly variable delay

    def _get_next_active_player_index(self, current_index, player_list):
        """ Finds the index IN player_list of the next player who has chips > 0. """
        if not player_list: return -1
        num_players = len(player_list)
        next_index = (current_index + 1) % num_players
        start_index = next_index # To detect full circle
        # Loop until an active player is found or we've checked everyone
        # Ensure player exists in self.players before checking chips
        while (player_list[next_index] not in self.players or
               self.players[player_list[next_index]]['chips'] <= 0):
            next_index = (next_index + 1) % num_players
            if next_index == start_index: # Looped all the way around
                return -1 # No other active players found
        return next_index


    def _post_blinds(self):
        """Posts the small and big blinds based on dealer button position."""
        num_players = len(self.player_order)
        # Get players who exist in self.players AND have chips
        active_players_with_chips = [name for name in self.player_order if name in self.players and self.players[name]['chips'] > 0]
        num_active = len(active_players_with_chips)

        if num_active < 2:
            print(f"{COLOR_YELLOW}Not enough players with chips ({num_active}) to post blinds.{COLOR_RESET}")
            return False # Cannot continue hand

        # Find Small Blind position (player after button in self.player_order who has chips)
        sb_index_in_order = self._get_next_active_player_index(self.dealer_button_pos, self.player_order)
        if sb_index_in_order == -1:
             print(f"{COLOR_RED}Error finding Small Blind player.{COLOR_RESET}"); return False
        sb_player_name = self.player_order[sb_index_in_order]

        # Find Big Blind position (player after SB in self.player_order who has chips)
        bb_index_in_order = self._get_next_active_player_index(sb_index_in_order, self.player_order)
        bb_player_name = None # Initialize bb_player_name
        if bb_index_in_order == -1:
             # Heads Up Case: If only two players, the button is SB, other is BB.
             if num_active == 2:
                  button_player_idx = self.dealer_button_pos
                  # Find the index of the *other* active player
                  other_player_idx = -1
                  for i in range(num_players):
                       idx = (button_player_idx + 1 + i) % num_players
                       if self.player_order[idx] in active_players_with_chips and idx != sb_index_in_order:
                            other_player_idx = idx
                            break
                  if other_player_idx != -1:
                       bb_index_in_order = other_player_idx
                       bb_player_name = self.player_order[bb_index_in_order]
                       print(f"{COLOR_DIM}(Heads Up: Button {sb_player_name} is SB, {bb_player_name} is BB){COLOR_RESET}")
                  else: # Should not happen if num_active is 2
                       print(f"{COLOR_RED}Error finding BB player in Heads Up.{COLOR_RESET}"); return False

             else: # More than 2 players, but couldn't find BB after SB
                  print(f"{COLOR_RED}Error finding Big Blind player.{COLOR_RESET}"); return False
        else:
             bb_player_name = self.player_order[bb_index_in_order]


        # Post Small Blind
        # Ensure player still exists (might have been removed if loading broken save?)
        if sb_player_name not in self.players:
             print(f"{COLOR_RED}Error: SB player {sb_player_name} not found.{COLOR_RESET}"); return False
        sb_player = self.players[sb_player_name]
        sb_amount = min(sb_player['chips'], self.settings['small_blind'])
        sb_player['chips'] -= sb_amount
        sb_player['bet_this_round'] = sb_amount
        self.pot += sb_amount
        print(f"{COLOR_BLUE}{sb_player_name}{COLOR_RESET} posts Small Blind: {COLOR_YELLOW}{sb_amount}{COLOR_RESET}")
        # Check if SB is now all-in
        if sb_player['chips'] <= 0:
             sb_player['is_all_in'] = True
             print(f"{COLOR_RED}{sb_player_name} is All-In posting the blind!{COLOR_RESET}")

        # Post Big Blind
        # Ensure BB player was found and exists and has chips
        if bb_player_name and bb_player_name in self.players and self.players[bb_player_name]['chips'] > 0:
            bb_player = self.players[bb_player_name]
            bb_amount = min(bb_player['chips'], self.settings['big_blind'])
            bb_player['chips'] -= bb_amount
            bb_player['bet_this_round'] = bb_amount # This is the total bet for BB so far
            self.pot += bb_amount
            print(f"{COLOR_BLUE}{bb_player_name}{COLOR_RESET} posts Big Blind: {COLOR_YELLOW}{bb_amount}{COLOR_RESET}")
            # Check if BB is now all-in
            if bb_player['chips'] <= 0:
                bb_player['is_all_in'] = True
                print(f"{COLOR_RED}{bb_player_name} is All-In posting the blind!{COLOR_RESET}")

            # Set initial betting state
            self.current_bet = self.settings['big_blind'] # Initial bet to match is the big blind amount
            self.last_raiser = bb_player_name # BB acts as the initial "raiser"
            self.last_raiser_amount = self.settings['big_blind'] # The amount of the "raise" is the BB amount
        elif bb_player_name: # BB player exists but has no chips or couldn't post
            print(f"{COLOR_YELLOW}{bb_player_name} could not post Big Blind (already all-in or no chips).{COLOR_RESET}")
            # Current bet remains the SB amount if posted
            self.current_bet = sb_amount if sb_player_name in self.players and sb_amount > 0 else 0
            self.last_raiser = sb_player_name if sb_player_name in self.players and sb_amount > 0 else None
            self.last_raiser_amount = sb_amount if self.last_raiser else 0
        else: # BB player name was not even found (should have returned False earlier)
             print(f"{COLOR_RED}Critical Error: BB player name not set.{COLOR_RESET}")
             return False


        time.sleep(1)
        return True


    def deal_hole_cards(self):
        """Deals two hole cards to each player who has chips."""
        print(f"\n{COLOR_BLUE}Dealing hole cards...{COLOR_RESET}"); time.sleep(0.5)
        # Deal starting from the player after the button who has chips
        start_deal_index = self._get_next_active_player_index(self.dealer_button_pos, self.player_order)
        if start_deal_index == -1: start_deal_index = 0 # Fallback if only one player

        # Create the dealing order starting from the correct index
        num_players = len(self.player_order)
        dealing_order_names = [self.player_order[(start_deal_index + i) % num_players] for i in range(num_players)]

        for _ in range(2): # Deal two rounds
            for player_name in dealing_order_names:
                 # Only deal to players who exist and have chips
                 if player_name in self.players and self.players[player_name]['chips'] > 0:
                     try:
                         card = self._deal_card()
                         self.players[player_name]['hand'].append(card)
                     except Exception as e:
                         print(f"{COLOR_RED}Error dealing card to {player_name}: {e}{COLOR_RESET}")
                         # Potentially stop the hand here?
                         return False # Indicate dealing error
                     time.sleep(0.1)
        print(f"{COLOR_GREEN}Hole cards dealt.{COLOR_RESET}")
        time.sleep(1)
        return True # Dealing successful


    def deal_community_cards(self, phase):
        """Deals the Flop, Turn, or River."""
        num_cards_to_deal = 0
        phase_name = ""
        if phase == GamePhase.FLOP:
            num_cards_to_deal = 3
            phase_name = "Flop"
            self.phase = GamePhase.FLOP
        elif phase == GamePhase.TURN:
            num_cards_to_deal = 1
            phase_name = "Turn"
            self.phase = GamePhase.TURN
        elif phase == GamePhase.RIVER:
            num_cards_to_deal = 1
            phase_name = "River"
            self.phase = GamePhase.RIVER
        else:
            return # Should not happen

        print(f"\n{COLOR_CYAN}--- Dealing the {phase_name} ---{COLOR_RESET}")
        time.sleep(0.5)
        # Burn card (conceptually)
        try:
            self._deal_card() # Remove one card from deck
            # print(f"{COLOR_DIM}Burning a card...{COLOR_RESET}") # Optional: uncomment to show burn
            # time.sleep(0.3)
        except Exception as e:
             print(f"{COLOR_YELLOW}Warning: Could not burn card (deck empty?): {e}{COLOR_RESET}")

        new_community_cards = []
        for _ in range(num_cards_to_deal):
             try:
                 card = self._deal_card()
                 self.community_cards.append(card)
                 new_community_cards.append(card)
                 time.sleep(0.2)
             except Exception as e:
                  print(f"{COLOR_RED}Could not deal community card (deck empty?): {e}{COLOR_RESET}")
                  break # Stop dealing if deck runs out


        # Display the newly dealt community cards
        if new_community_cards:
             card_lines = [[] for _ in range(7)] # 7 lines high for card display
             for card_data in new_community_cards:
                 card_str_lines = display_card(card_data)
                 for line_num, line in enumerate(card_str_lines):
                     card_lines[line_num].append(line)

             print(f"{COLOR_GREEN}Dealt:{COLOR_RESET}")
             for line_idx in range(7):
                 print("  ".join(card_lines[line_idx]))
             time.sleep(1.5)


    def display_table(self, show_all_hands=False):
        """Displays the current state of the table."""
        clear_screen()
        title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ Texas Hold'em - {self.phase.value} ~~~{COLOR_RESET}"
        pot_info = f"{COLOR_MAGENTA}Pot: {self.pot}{COLOR_RESET}"
        print(center_text(title, TERMINAL_WIDTH))
        print(center_text(pot_info, TERMINAL_WIDTH))

        # --- Community Cards ---
        if self.community_cards:
            print(center_text(f"{COLOR_CYAN}--- Community Cards ({len(self.community_cards)}) ---{COLOR_RESET}", TERMINAL_WIDTH))
            card_lines = [[] for _ in range(7)]
            for card_data in self.community_cards:
                card_str_lines = display_card(card_data)
                for line_num, line in enumerate(card_str_lines):
                    card_lines[line_num].append(line)

            combined_lines = ["  ".join(line) for line in card_lines]
            # Calculate padding to center the community cards block
            block_width = get_visible_width(combined_lines[0]) if combined_lines else 0
            left_padding = max(0, (TERMINAL_WIDTH - block_width) // 2)
            padding_str = " " * left_padding

            for line in combined_lines:
                print(padding_str + line)
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")
        else:
            print(center_text(f"{COLOR_DIM}[ No community cards yet ]{COLOR_RESET}", TERMINAL_WIDTH))
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")


        # --- Players ---
        player_name = "Player" # Assume human player is "Player"
        player_idx = -1
        if player_name in self.player_order:
             player_idx = self.player_order.index(player_name)
        else: player_idx = 0 # Player should exist if game is running, fallback

        # Display players clockwise starting from the human player
        num_p = len(self.player_order)
        if num_p == 0: # Handle case where player_order might be empty
             print(f"{COLOR_RED}Error: No players in player_order.{COLOR_RESET}")
             return

        display_order = [self.player_order[(player_idx + i) % num_p] for i in range(num_p)]

        print(f"{COLOR_BLUE}--- Players ---{COLOR_RESET}")
        for name in display_order:
            if name not in self.players: continue # Skip if player was removed (e.g., broke)
            player_data = self.players[name]
            player_color = COLOR_GREEN if name == player_name else COLOR_BLUE # Highlight human player
            status_color = COLOR_RESET
            status_indicator = ""
            action_text = ""

            if player_data['folded']:
                status_color = COLOR_DIM
                status_indicator = " (Folded)"
            elif player_data['is_all_in']:
                status_color = COLOR_RED + COLOR_BOLD
                status_indicator = " (ALL-IN)"

            # Show last action clearly
            if player_data.get('last_action'):
                 action_enum = player_data['last_action'][0]
                 action_amount = player_data['last_action'][1] # Amount committed in that action
                 action_str = action_enum.name.upper()
                 action_color = COLOR_YELLOW # Default for Bet/Raise
                 if action_enum == PlayerAction.FOLD: action_color = COLOR_RED
                 elif action_enum == PlayerAction.CHECK: action_color = COLOR_GREEN
                 elif action_enum == PlayerAction.CALL: action_color = COLOR_GREEN
                 elif action_enum == PlayerAction.ALL_IN: action_color = COLOR_RED + COLOR_BOLD

                 # Display amount committed for relevant actions
                 if action_enum in [PlayerAction.BET, PlayerAction.CALL, PlayerAction.ALL_IN] and action_amount > 0:
                      action_text = f" ({action_color}{action_str} {action_amount}{status_color})"
                 # For Raise, show the total bet amount for the round
                 elif action_enum == PlayerAction.RAISE:
                      total_bet = player_data['bet_this_round'] # This should reflect the total after the raise
                      action_text = f" ({action_color}{action_str} to {total_bet}{status_color})"
                 elif action_enum != PlayerAction.FOLD: # Don't show amount=0 for check/fold
                      action_text = f" ({action_color}{action_str}{status_color})"


            # Dealer button indicator
            button_indicator = ""
            # Check if player_order is not empty before accessing dealer_button_pos
            if self.player_order and self.dealer_button_pos < len(self.player_order) and self.player_order[self.dealer_button_pos] == name:
                 button_indicator = f" {COLOR_YELLOW}(D){COLOR_RESET}"


            # Player Info Line
            info_line = f"{status_color}{player_color}{name}{status_indicator}{COLOR_RESET}{button_indicator} " \
                        f"| Chips: {COLOR_YELLOW}{player_data['chips']}{COLOR_RESET} "
            # Show current round's bet if > 0
            if player_data['bet_this_round'] > 0:
                 info_line += f"| Bet: {COLOR_YELLOW}{player_data['bet_this_round']}{COLOR_RESET} "
            info_line += f"{status_color}{action_text}{COLOR_RESET}"

            if player_data['is_ai']:
                 info_line += f" ({COLOR_DIM}{player_data['ai_type'].value}{COLOR_RESET})"

            print(info_line)

            # Player Hand Display
            if not player_data['folded']:
                hand = player_data['hand']
                if hand:
                    card_lines_data = [[] for _ in range(7)]
                    is_human_player = (name == player_name)
                    # Show player hand always, show AI hands only at showdown
                    show_this_hand = is_human_player or show_all_hands
                    num_cards = len(hand)

                    for i, card_data in enumerate(hand):
                        # Hide AI hole cards unless showdown
                        is_hidden = not is_human_player and not show_all_hands and i < 2
                        card_str_lines = display_card(card_data, hidden=is_hidden)
                        for line_num, line in enumerate(card_str_lines):
                             # Apply dimming to hidden cards
                             line_to_add = f"{COLOR_DIM}{line}{COLOR_RESET}" if is_hidden else line
                             card_lines_data[line_num].append(line_to_add)

                    # Display the cards side-by-side
                    for line_idx in range(7):
                        print("  ".join(card_lines_data[line_idx]))

                    # Display hand evaluation if showing hand and community cards exist
                    if show_this_hand and self.community_cards:
                         eval_rank, eval_kickers = evaluate_hand(hand, self.community_cards)
                         # Convert numeric kickers back to readable ranks (T, J, Q, K, A)
                         kicker_ranks = []
                         for v in eval_kickers:
                              if v == 14: kicker_ranks.append('A')
                              elif v == 13: kicker_ranks.append('K')
                              elif v == 12: kicker_ranks.append('Q')
                              elif v == 11: kicker_ranks.append('J')
                              elif v == 10: kicker_ranks.append('T')
                              elif v > 1: kicker_ranks.append(str(v))
                              # Handle Ace in A-5 straight kicker list [5, 4, 3, 2, 1] -> [5, 4, 3, 2, A]
                              elif v == 1 and eval_rank == HandRanking.STRAIGHT and eval_kickers[0] == 5: kicker_ranks.append('A')
                              elif v == 0: continue # Don't show padding zeros
                              else: kicker_ranks.append('?') # Should not happen

                         print(f"{status_color}{COLOR_YELLOW}Best Hand: {HAND_NAMES[eval_rank]} ({', '.join(kicker_ranks)}){COLOR_RESET}")

                elif name == player_name: # Only show "no cards yet" for the player if hand is empty
                    print(f"{status_color}[ No cards yet ]{COLOR_RESET}")
            else:
                 print(f"{status_color}[ Hand Folded ]{COLOR_RESET}")

            print("-" * (TERMINAL_WIDTH // 2)) # Separator

        print(f"{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")


    def _get_player_action(self, player_name):
        """Gets the action from the human player."""
        player_data = self.players[player_name]
        chips = player_data['chips']
        bet_this_round = player_data['bet_this_round']
        call_amount = self.current_bet - bet_this_round
        can_check = (call_amount <= 0)
        # Can call if facing a bet and have enough chips (or can go all-in)
        can_call = (call_amount > 0 and chips > 0)
        # Can bet if check is possible and player has chips
        can_bet = (can_check and chips > 0)
        # Can raise if call is possible and player has more chips than the call amount
        # Also need enough chips to make at least a minimum raise
        min_raise_increment = max(self.last_raiser_amount, self.settings['big_blind'])
        can_raise = (can_call and chips >= call_amount + min_raise_increment)


        options = []
        # Should not be called if folded or all-in, but check anyway
        if player_data['folded'] or player_data['is_all_in']: return PlayerAction.FOLD, 0

        options.append(f"{COLOR_RED}(f)old{COLOR_RESET}")
        if can_check: options.append(f"{COLOR_GREEN}(ch)eck{COLOR_RESET}")
        # Show Call option if facing a bet and have chips
        if can_call:
             call_str = f" ({min(chips, call_amount)})" # Show actual amount needed/possible
             options.append(f"{COLOR_GREEN}(c)all{call_str}{COLOR_RESET}")
        # Show Bet option if checking is possible
        if can_bet: options.append(f"{COLOR_YELLOW}(b)et{COLOR_RESET}")
        # Show Raise option if calling is possible and have chips remaining after call for min raise
        if can_raise: options.append(f"{COLOR_YELLOW}(r)aise{COLOR_RESET}")
        # Always allow all-in option if chips > 0
        if chips > 0: options.append(f"{COLOR_RED}(a)ll-in ({chips}){COLOR_RESET}")

        print(f"\n--- {COLOR_GREEN}{player_name}'s Turn{COLOR_RESET} ---")
        print(f"Chips: {chips}, Current Round Bet: {bet_this_round}, To Call: {max(0, call_amount)}, Pot: {self.pot}")
        # Display player's hand clearly during their turn
        print(f"Your hand:")
        hand = player_data['hand']
        if hand:
            card_lines_data = [[] for _ in range(7)]
            for card_data in hand:
                card_str_lines = display_card(card_data)
                for line_num, line in enumerate(card_str_lines):
                    card_lines_data[line_num].append(line)
            for line_idx in range(7): print("  ".join(card_lines_data[line_idx]))
            # Show best possible hand with community cards
            if self.community_cards:
                 eval_rank, eval_kickers = evaluate_hand(hand, self.community_cards)
                 kicker_ranks = []
                 for v in eval_kickers:
                      if v == 14: kicker_ranks.append('A')
                      elif v == 13: kicker_ranks.append('K')
                      elif v == 12: kicker_ranks.append('Q')
                      elif v == 11: kicker_ranks.append('J')
                      elif v == 10: kicker_ranks.append('T')
                      elif v > 1: kicker_ranks.append(str(v))
                      elif v == 1 and eval_rank == HandRanking.STRAIGHT and eval_kickers[0] == 5: kicker_ranks.append('A')
                      elif v == 0 : continue # Don't show padding zeros
                      else: kicker_ranks.append('?')
                 print(f"{COLOR_YELLOW}Best Hand: {HAND_NAMES[eval_rank]} ({', '.join(kicker_ranks)}){COLOR_RESET}")

        while True:
            prompt = f"{COLOR_YELLOW}Choose action: {', '.join(options)}? {COLOR_RESET}"
            action_input = input(prompt).lower().strip()

            if action_input.startswith('f'): return PlayerAction.FOLD, 0

            elif action_input.startswith('ch') and can_check: return PlayerAction.CHECK, 0

            elif action_input.startswith('c') and can_call:
                 # Amount to commit is the call amount, capped by player's chips
                 commit_amount = min(chips, call_amount)
                 # If committing all chips, it's an All-in call
                 if commit_amount >= chips:
                      return PlayerAction.ALL_IN, chips # Return ALL_IN and the amount committed
                 else:
                      return PlayerAction.CALL, commit_amount # Return CALL and amount committed

            elif action_input.startswith('a') and chips > 0:
                 # All-in commits all remaining chips
                 return PlayerAction.ALL_IN, chips

            elif action_input.startswith('b') and can_bet:
                while True:
                    try:
                        # Ensure minimum bet is at least the Big Blind
                        min_bet = max(self.settings['big_blind'], 1) # Min bet is BB, or 1 if BB is 0 somehow
                        bet_amount_str = input(f"{COLOR_YELLOW}Enter bet amount (min {min_bet}, max {chips}): {COLOR_RESET}")
                        bet_amount = int(bet_amount_str)

                        if bet_amount < min_bet: print(f"{COLOR_RED}Minimum bet is {min_bet}.{COLOR_RESET}")
                        elif bet_amount > chips: print(f"{COLOR_RED}Not enough chips (max {chips}).{COLOR_RESET}")
                        else:
                            # If betting all chips, it's an All-in bet
                            if bet_amount >= chips:
                                 return PlayerAction.ALL_IN, chips
                            else:
                                 return PlayerAction.BET, bet_amount
                    except ValueError: print(f"{COLOR_RED}Invalid amount. Please enter a number.{COLOR_RESET}")
                    except EOFError: print(f"\n{COLOR_RED}Input error.{COLOR_RESET}"); return PlayerAction.FOLD, 0 # Fold on input error

            elif action_input.startswith('r') and can_raise:
                while True:
                    try:
                        # Minimum raise increment is the size of the last bet/raise, or BB if first raise
                        min_raise_increment = max(self.last_raiser_amount, self.settings['big_blind'])
                        # Minimum total bet amount after raising
                        min_raise_to = self.current_bet + min_raise_increment
                        # Maximum possible raise makes total bet equal to player's full stack
                        max_raise_to = chips + bet_this_round

                        raise_to_str = input(f"{COLOR_YELLOW}Raise TO amount (min {min_raise_to}, max {max_raise_to}): {COLOR_RESET}")
                        raise_to_total = int(raise_to_str) # The total bet amount the player wants to make

                        # Amount player needs to add to the pot
                        amount_to_commit = raise_to_total - bet_this_round

                        if raise_to_total < min_raise_to:
                            print(f"{COLOR_RED}Minimum raise to {min_raise_to}.{COLOR_RESET}")
                        elif amount_to_commit > chips: # Check if they have enough chips to make the raise amount
                            print(f"{COLOR_RED}Not enough chips (you need to add {amount_to_commit}, have {chips}). Try going all-in?{COLOR_RESET}")
                        elif raise_to_total > max_raise_to: # Should be caught by amount_to_commit > chips, but double check
                             print(f"{COLOR_RED}Cannot raise to more than your stack ({max_raise_to}).{COLOR_RESET}")
                        else:
                            # If raising commits all chips, it's an All-in raise
                            if amount_to_commit >= chips:
                                 return PlayerAction.ALL_IN, chips
                            else:
                                 # Return RAISE with the TOTAL bet amount for this round
                                 return PlayerAction.RAISE, raise_to_total
                    except ValueError: print(f"{COLOR_RED}Invalid amount. Please enter a number.{COLOR_RESET}")
                    except EOFError: print(f"\n{COLOR_RED}Input error.{COLOR_RESET}"); return PlayerAction.FOLD, 0 # Fold on input error

            else: print(f"{COLOR_RED}Invalid action or action not allowed now.{COLOR_RESET}")


    def _get_betting_order(self):
         """ Determines the order of players for the current betting round, including all-in players. """
         num_players = len(self.player_order)
         if num_players == 0: return []

         # Find the starting player index based on phase
         if self.phase == GamePhase.PREFLOP:
              # Action starts after Big Blind
              sb_index = self._get_next_active_player_index(self.dealer_button_pos, self.player_order)
              bb_index = self._get_next_active_player_index(sb_index, self.player_order)
              start_index = self._get_next_active_player_index(bb_index, self.player_order)
         else:
              # Action starts after the Button
              start_index = self._get_next_active_player_index(self.dealer_button_pos, self.player_order)

         # If no active player found after button/BB (e.g., everyone folded), start from button?
         if start_index == -1: start_index = self.dealer_button_pos # Fallback

         # Create the order list including all players who haven't folded
         players_in_hand = [p for p in self.player_order if p in self.players and not self.players[p]['folded']]
         if not players_in_hand: return [] # No one left

         # Find the starting player within the players_in_hand list
         start_player_name = self.player_order[start_index]
         try:
             start_idx_in_hand = players_in_hand.index(start_player_name)
             # Rotate the players_in_hand list to start from the correct player
             betting_order = players_in_hand[start_idx_in_hand:] + players_in_hand[:start_idx_in_hand]
             return betting_order
         except ValueError:
              # If the calculated start player isn't in the hand (e.g., folded), find the next one who is
              current_idx = start_index
              while self.player_order[current_idx] not in players_in_hand:
                   # Safety check: ensure current_idx is valid for self.player_order
                   if current_idx >= len(self.player_order): current_idx = 0
                   # Move to next player
                   current_idx = (current_idx + 1) % num_players
                   if current_idx == start_index: return [] # Should not happen if players_in_hand is not empty
              start_player_name = self.player_order[current_idx]
              # Find the index in the *filtered* list
              try:
                   start_idx_in_hand = players_in_hand.index(start_player_name)
                   betting_order = players_in_hand[start_idx_in_hand:] + players_in_hand[:start_idx_in_hand]
                   return betting_order
              except ValueError: # Fallback if still not found
                   return players_in_hand


    def betting_round(self):
        """Handles a complete round of betting."""
        print(f"\n{COLOR_YELLOW}--- Betting Round: {self.phase.value} ---{COLOR_RESET}")
        time.sleep(0.5) # Shorter pause

        betting_order = self._get_betting_order()
        if not betting_order:
            print(f"{COLOR_DIM}No players eligible for betting round.{COLOR_RESET}")
            return

        # Reset last actions display for the new round
        for name in self.players:
             if name in self.players: # Check player exists
                 self.players[name]['last_action'] = None

        num_in_hand = len(betting_order)
        current_actor_rel_index = 0 # Index within betting_order
        actions_this_round = 0 # Count total actions in the round for safety break

        # Player who made the last aggressive action (bet/raise)
        # If starting a new round (flop, turn, river), reset aggressor if current_bet is 0
        if self.phase != GamePhase.PREFLOP and self.current_bet == 0:
             last_aggressor = None
        else:
             last_aggressor = self.last_raiser


        # Determine the player who closes the action.
        action_closer = None
        if last_aggressor and last_aggressor in betting_order:
             try:
                  aggressor_idx = betting_order.index(last_aggressor)
                  # The closer is the player *before* the aggressor in the order
                  # Find the previous player who is NOT folded or all-in (if possible)
                  closer_idx = (aggressor_idx - 1 + num_in_hand) % num_in_hand
                  # Find the player who actually closes the action (might be aggressor if others folded/all-in)
                  action_closer = last_aggressor # Default to aggressor closing action on themselves
             except ValueError: # Aggressor not in current betting order (e.g. folded)
                  action_closer = betting_order[-1] # Last player in order closes action
        elif self.phase == GamePhase.PREFLOP:
             # BB closes action if no raise before them
             bb_player_name = self._get_bb_player_name()
             if bb_player_name in betting_order: action_closer = bb_player_name
             else: action_closer = betting_order[-1] # Fallback
        else: # Post-flop, no aggressor yet (all checks)
             action_closer = betting_order[-1] # Last player in order closes action


        players_acted_voluntarily = set() # Track players who made a non-forced action (Check, Bet, Call, Raise, Fold)


        while actions_this_round < num_in_hand * 3: # Increased safety break limit slightly
            # Check if only one non-folded player remains before starting the loop iteration
            active_players_now = [p for p in betting_order if not self.players[p]['folded']]
            if len(active_players_now) <= 1:
                 # print(f"{COLOR_DIM}Debug: Only {len(active_players_now)} player left, ending round.{COLOR_RESET}")
                 break

            player_name = betting_order[current_actor_rel_index % num_in_hand]
            player_data = self.players[player_name]
            actions_this_round += 1 # Increment safety counter

            # --- Check if player needs to act ---
            if player_data['folded'] or player_data['is_all_in']:
                current_actor_rel_index += 1
                continue

            # --- Check if round should end ---
            # Condition: All active players have voluntarily acted OR matched the current bet since the last aggression.
            active_non_all_in_players = [p for p in betting_order if not self.players[p]['folded'] and not self.players[p]['is_all_in']]
            all_acted_or_matched = True
            for p_check_name in active_non_all_in_players:
                 # Check if player exists before accessing data
                 if p_check_name in self.players:
                      if p_check_name not in players_acted_voluntarily and self.players[p_check_name]['bet_this_round'] < self.current_bet:
                           all_acted_or_matched = False
                           break
                 else: # Player doesn't exist, something is wrong
                      print(f"{COLOR_RED}Error: Player {p_check_name} not found during betting check.{COLOR_RESET}")
                      all_acted_or_matched = False
                      break


            # If all active players have acted or matched, and the current player is the closer
            if all_acted_or_matched and player_name == action_closer:
                 # Special case: BB check option pre-flop
                 is_bb_check_option = (self.phase == GamePhase.PREFLOP and
                                       player_name == self._get_bb_player_name() and
                                       self.current_bet == self.settings['big_blind'] and
                                       last_aggressor == player_name) # Check if BB was the initial raiser

                 if not is_bb_check_option:
                      # print(f"{COLOR_DIM}Debug: Action closed on {player_name}. All acted/matched.{COLOR_RESET}")
                      break # Betting round is over


            # --- Get Player Action ---
            self.display_table() # Show table before each action
            action = PlayerAction.FOLD
            amount_param = 0 # Amount from AI/Player (meaning depends on action)

            if player_data['is_ai']:
                active_players_count = len(active_non_all_in_players)
                game_state = { 'community_cards': self.community_cards, 'current_bet': self.current_bet, 'pot': self.pot,
                               'players_in_hand': active_players_count, 'phase': self.phase, 'last_raiser_amount': self.last_raiser_amount }
                print(f"{COLOR_DIM}Thinking... ({player_name}){COLOR_RESET}"); time.sleep(0.5 + random.random()*0.5) # Faster AI
                action, amount_param = get_ai_decision(player_data, game_state)
                decision_str = f"{COLOR_BLUE}{player_name}{COLOR_RESET} ({COLOR_DIM}{player_data['ai_type'].value}{COLOR_RESET}) decides to {COLOR_YELLOW}{action.name}{COLOR_RESET}"
                if action == PlayerAction.RAISE: decision_str += f" to {amount_param}"
                elif amount_param > 0: decision_str += f" ({amount_param})"
                print(decision_str)
                time.sleep(0.8)
            else: # Human player
                action, amount_param = self._get_player_action(player_name)

            # --- Process Action ---
            committed_this_action = 0 # Actual chips removed from player

            if action == PlayerAction.FOLD:
                player_data['folded'] = True
                print(f"{COLOR_RED}{player_name} folds.{COLOR_RESET}")
                self._ai_chat("preflop_fold", player_name)
                players_acted_voluntarily.add(player_name)

            elif action == PlayerAction.CHECK:
                if self.current_bet > player_data['bet_this_round']:
                     print(f"{COLOR_RED}Cannot check, current bet is {self.current_bet}. Action invalid (treat as fold).{COLOR_RESET}")
                     player_data['folded'] = True
                else:
                     print(f"{COLOR_GREEN}{player_name} checks.{COLOR_RESET}")
                     self._ai_chat("turn_river_check", player_name)
                players_acted_voluntarily.add(player_name)

            elif action == PlayerAction.CALL:
                committed_this_action = amount_param
                player_data['chips'] -= committed_this_action
                player_data['bet_this_round'] += committed_this_action
                self.pot += committed_this_action
                print(f"{COLOR_GREEN}{player_name} calls {committed_this_action}.{COLOR_RESET}")
                players_acted_voluntarily.add(player_name)

            elif action == PlayerAction.BET:
                committed_this_action = amount_param
                player_data['chips'] -= committed_this_action
                player_data['bet_this_round'] += committed_this_action
                self.pot += committed_this_action
                print(f"{COLOR_YELLOW}{player_name} bets {committed_this_action}.{COLOR_RESET}")
                self.current_bet = player_data['bet_this_round']
                self.last_raiser_amount = committed_this_action
                self.last_raiser = player_name
                action_closer = player_name # This player now closes the action
                players_acted_voluntarily = {player_name}
                self._ai_chat("turn_river_bet", player_name)

            elif action == PlayerAction.RAISE:
                total_bet_target = amount_param
                committed_this_action = total_bet_target - player_data['bet_this_round']
                raise_increment = total_bet_target - self.current_bet
                player_data['chips'] -= committed_this_action
                player_data['bet_this_round'] = total_bet_target
                self.pot += committed_this_action
                print(f"{COLOR_YELLOW}{player_name} raises to {total_bet_target} (added {committed_this_action}).{COLOR_RESET}")
                self.current_bet = total_bet_target
                self.last_raiser_amount = raise_increment
                self.last_raiser = player_name
                action_closer = player_name # This player now closes the action
                players_acted_voluntarily = {player_name}
                self._ai_chat("preflop_raise", player_name)

            elif action == PlayerAction.ALL_IN:
                committed_this_action = amount_param
                player_data['chips'] -= committed_this_action
                player_data['bet_this_round'] += committed_this_action
                self.pot += committed_this_action
                player_data['is_all_in'] = True
                print(f"{COLOR_RED}{player_name} goes ALL-IN for {committed_this_action}!{COLOR_RESET}")
                players_acted_voluntarily.add(player_name) # Going all-in counts as acting

                if player_data['bet_this_round'] > self.current_bet:
                     all_in_raise_increment = player_data['bet_this_round'] - self.current_bet
                     min_raise_increment = max(self.last_raiser_amount, self.settings['big_blind'])
                     if all_in_raise_increment >= min_raise_increment:
                          print(f"{COLOR_YELLOW}(All-in is a valid raise!){COLOR_RESET}")
                          self.last_raiser_amount = all_in_raise_increment
                          self.last_raiser = player_name
                          action_closer = player_name # Re-opens betting
                          players_acted_voluntarily = {player_name} # Reset voluntary actors
                     self.current_bet = player_data['bet_this_round']
                self._ai_chat("taunt", player_name)


            # Store last action for display
            player_data['last_action'] = (action, committed_this_action)

            # --- Check Hand Over After Action ---
            not_folded_players_after = [p for p in betting_order if not self.players[p]['folded']]
            if len(not_folded_players_after) <= 1:
                 break # Exit betting loop immediately

            # --- Move to next player ---
            current_actor_rel_index += 1
            time.sleep(0.3) # Shorter pause


        # --- End of Betting Round ---
        print(f"\n{COLOR_YELLOW}--- Betting Round ({self.phase.value}) Complete ---{COLOR_RESET}")
        # Handle side pots if necessary (Simplified: currently assumes one main pot)
        # TODO: Implement side pot logic if multiple players are all-in for different amounts

        self.display_table() # Show final state of the round
        time.sleep(1.0) # Shorter pause

        # Reset player's bet_this_round for the next street
        # Keep last_raiser_amount for min raise calculation on next street
        for name in self.players:
             if name in self.players: # Check player exists
                 self.players[name]['bet_this_round'] = 0
                 # Don't clear last_action here, clear at the start of the next round

        # Reset current bet level for the start of the next street ONLY if not preflop
        # Preflop current_bet carries over (it's the BB amount initially)
        # Postflop starts with 0 current bet.
        if self.phase != GamePhase.PREFLOP:
             self.current_bet = 0
             self.last_raiser = None # Reset aggressor for the new street


    def _get_bb_player_name(self):
         """ Helper to find the current Big Blind player name """
         num_players = len(self.player_order)
         if num_players < 2: return None

         sb_index = self._get_next_active_player_index(self.dealer_button_pos, self.player_order)
         if sb_index == -1: return None
         bb_index = self._get_next_active_player_index(sb_index, self.player_order)
         if bb_index == -1: return None

         return self.player_order[bb_index]


    def showdown(self):
        """Handles the showdown, evaluates hands, and determines the winner(s)."""
        print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Showdown ---{COLOR_RESET}")
        time.sleep(1)

        # Identify players involved in the showdown (not folded and have cards)
        showdown_contenders = {name: data for name, data in self.players.items() if not data['folded'] and data['hand']}
        if not showdown_contenders:
            print(f"{COLOR_YELLOW}No players eligible for showdown.{COLOR_RESET}")
            # This case should be handled earlier by _check_hand_over awarding the pot
            return

        # If only one player is left, they win automatically (should also be caught earlier)
        if len(showdown_contenders) == 1:
            winner_name = list(showdown_contenders.keys())[0]
            print(f"{COLOR_GREEN}{winner_name} wins the pot of {self.pot} uncontested!{COLOR_RESET}")
            self.players[winner_name]['chips'] += self.pot
            self.session_stats['pots_won'] += 1
            if not self.players[winner_name]['is_ai']:
                 self.session_stats['hands_won_fold'] += 1
                 self.session_stats['chips_won'] += self.pot # Simplification
            self.pot = 0
            return

        print("Revealing hands...")
        self.display_table(show_all_hands=True) # Show everyone's hand
        time.sleep(2)

        player_evaluations = {}
        print("--- Hand Evaluations ---")
        for name, data in showdown_contenders.items():
            rank, kickers = evaluate_hand(data['hand'], self.community_cards)
            player_evaluations[name] = {'rank': rank, 'kickers': kickers, 'name': name}
            # Convert kickers to readable format
            kicker_ranks_str = []
            for v in kickers:
                 if v == 14: kicker_ranks_str.append('A')
                 elif v == 13: kicker_ranks_str.append('K')
                 elif v == 12: kicker_ranks_str.append('Q')
                 elif v == 11: kicker_ranks_str.append('J')
                 elif v == 10: kicker_ranks_str.append('T')
                 elif v > 1: kicker_ranks_str.append(str(v))
                 elif v == 1 and rank == HandRanking.STRAIGHT and kickers[0] == 5: kicker_ranks_str.append('A') # Ace for wheel
                 elif v == 0: continue # Don't show padding zeros
                 else: kicker_ranks_str.append('?') # Should not happen

            print(f"{COLOR_BLUE}{name}{COLOR_RESET}: {COLOR_YELLOW}{HAND_NAMES[rank]}{COLOR_RESET} ({', '.join(kicker_ranks_str)})")
            time.sleep(0.5)

        if not player_evaluations:
             print(f"{COLOR_RED}Error: No hands evaluated at showdown.{COLOR_RESET}")
             return

        # Sort players by hand rank (highest first), then by kickers
        # Ensure kickers are compared correctly as lists/tuples
        sorted_players = sorted(player_evaluations.values(), key=lambda x: (x['rank'], tuple(x['kickers'])), reverse=True)

        # Determine winner(s) - handle ties
        winners = []
        best_rank = sorted_players[0]['rank']
        best_kickers = sorted_players[0]['kickers'] # Keep as list for comparison
        for player_eval in sorted_players:
            # Compare rank and kickers list directly
            if player_eval['rank'] == best_rank and player_eval['kickers'] == best_kickers:
                winners.append(player_eval['name'])
            else:
                break # Stop once a lower hand is found

        # Award pot (Simplified: handles main pot only, assumes no side pots)
        # TODO: Implement side pot logic for all-in scenarios
        num_winners = len(winners)
        if num_winners == 0: # Should not happen if sorted_players is not empty
             print(f"{COLOR_RED}Error: No winners found at showdown?{COLOR_RESET}")
             return

        winnings_per_player = self.pot // num_winners
        remainder = self.pot % num_winners # Handle odd chips

        print("\n--- Results ---")
        if num_winners == 1:
            winner_name = winners[0]
            print(f"{COLOR_GREEN}{winner_name} wins the pot of {self.pot} with {HAND_NAMES[best_rank]}!{COLOR_RESET}")
            self.players[winner_name]['chips'] += self.pot
            self.session_stats['pots_won'] += 1
            if not self.players[winner_name]['is_ai']:
                 self.session_stats['hands_won_showdown'] += 1
                 self.session_stats['chips_won'] += self.pot # Simplification
            self._ai_chat("showdown_win", winner_name)
        else:
            winner_names_str = ", ".join(winners)
            print(f"{COLOR_YELLOW}Split Pot! Winners: {winner_names_str} with {HAND_NAMES[best_rank]}.{COLOR_RESET}")
            print(f"Each winner gets {winnings_per_player} chips.")
            for i, name in enumerate(winners):
                award = winnings_per_player + (1 if i < remainder else 0) # Distribute remainder fairly
                self.players[name]['chips'] += award
                self.session_stats['pots_won'] += 1 # Count split pot win for stats
                if not self.players[name]['is_ai']:
                     self.session_stats['hands_won_showdown'] += 1
                     self.session_stats['chips_won'] += award # Simplification
                self._ai_chat("showdown_win", name) # Each winner chats

        # Chat for losers at showdown
        loser_names = [p['name'] for p in sorted_players if p['name'] not in winners]
        for loser in loser_names:
             # Only chat if the loser is an AI
             if loser in self.players and self.players[loser]['is_ai']:
                  self._ai_chat("showdown_loss", loser)

        self.pot = 0 # Clear pot after awarding
        time.sleep(3)


    def play_hand(self):
        """Plays a single hand of Texas Hold'em."""
        clear_screen()
        self.session_stats['hands_played'] += 1
        hand_num = self.session_stats['hands_played']
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Starting Hand #{hand_num} ---{COLOR_RESET}")

        # --- Reset Hand State ---
        self._create_and_shuffle_deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.last_raiser = None
        self.last_raiser_amount = 0 # Reset last raise increment amount
        self.phase = GamePhase.PREFLOP
        for name in self.players:
             # Check if player exists before accessing data
             if name in self.players:
                 self.players[name]['hand'] = []
                 self.players[name]['bet_this_round'] = 0
                 self.players[name]['folded'] = False
                 self.players[name]['is_all_in'] = False # Reset all-in status
                 self.players[name]['last_action'] = None

        # --- Rotate Button ---
        # Ensure player_order is not empty and players exist
        if not self.player_order or not self.players:
             print(f"{COLOR_RED}Error: Player list empty before rotating button.{COLOR_RESET}")
             return 'game_over'

        active_players_list = [name for name in self.player_order if name in self.players and self.players[name]['chips'] > 0]
        if not active_players_list:
            print(f"{COLOR_RED}No players with chips left!{COLOR_RESET}")
            return 'game_over'

        # Rotate button to the next player *in the original order* who still has chips
        original_button_index = self.dealer_button_pos
        next_button_index = (original_button_index + 1) % len(self.player_order)
        checked_count = 0
        # Ensure the player exists in self.players before checking chips
        while (self.player_order[next_button_index] not in self.players or
               self.players[self.player_order[next_button_index]]['chips'] <= 0) and \
              checked_count < len(self.player_order):
             next_button_index = (next_button_index + 1) % len(self.player_order)
             checked_count += 1

        # Handle case where only one player has chips (should be caught by game over check)
        if checked_count >= len(self.player_order):
             # Find the index of the single active player
             if active_players_list:
                  try:
                       self.dealer_button_pos = self.player_order.index(active_players_list[0])
                  except ValueError: # Should not happen
                       self.dealer_button_pos = 0
             else: # No active players left
                  return 'game_over'
        else:
             self.dealer_button_pos = next_button_index

        # Ensure dealer button pos is valid after potential removals
        if self.dealer_button_pos >= len(self.player_order):
             self.dealer_button_pos = 0 # Reset to first player if index is out of bounds

        # Check again if player_order is valid before accessing
        if not self.player_order:
             print(f"{COLOR_RED}Error: Player list empty after button rotation.{COLOR_RESET}")
             return 'game_over'

        print(f"{COLOR_DIM}Dealer button is on {self.player_order[self.dealer_button_pos]}{COLOR_RESET}")
        time.sleep(1)

        # --- Post Blinds ---
        if not self._post_blinds():
             print(f"{COLOR_RED}Could not post blinds. Ending game.{COLOR_RESET}")
             return 'game_over'

        # --- Deal Hole Cards ---
        if not self.deal_hole_cards(): # Check for dealing errors
             print(f"{COLOR_RED}Error dealing hole cards. Ending hand.{COLOR_RESET}")
             return True # End hand, but not game necessarily

        self.display_table()

        # --- Pre-flop Betting ---
        self.betting_round()
        if self._check_hand_over(): self._remove_broke_players(); return True # Hand ended due to folds

        # --- Flop ---
        # Check if enough players remain for flop
        if len([p for p in self.players if not self.players[p]['folded']]) > 1:
             if len(self.community_cards) < 3:
                  self.deal_community_cards(GamePhase.FLOP)
             self.display_table()
             self.betting_round()
             if self._check_hand_over(): self._remove_broke_players(); return True
        else: print(f"{COLOR_DIM}Skipping remaining rounds as only one player left.{COLOR_RESET}")


        # --- Turn ---
        if len([p for p in self.players if not self.players[p]['folded']]) > 1:
             if len(self.community_cards) < 4:
                  self.deal_community_cards(GamePhase.TURN)
             self.display_table()
             self.betting_round()
             if self._check_hand_over(): self._remove_broke_players(); return True
        else: print(f"{COLOR_DIM}Skipping remaining rounds as only one player left.{COLOR_RESET}")


        # --- River ---
        if len([p for p in self.players if not self.players[p]['folded']]) > 1:
             if len(self.community_cards) < 5:
                  self.deal_community_cards(GamePhase.RIVER)
             self.display_table()
             self.betting_round()
             if self._check_hand_over(): self._remove_broke_players(); return True
        else: print(f"{COLOR_DIM}Skipping remaining rounds as only one player left.{COLOR_RESET}")


        # --- Showdown ---
        # Only go to showdown if more than one player remains unfolded
        if len([p for p in self.players if not self.players[p]['folded']]) > 1:
             self.phase = GamePhase.SHOWDOWN
             self.showdown()
        # else: Hand already awarded by _check_hand_over

        # --- Clean up ---
        self._remove_broke_players()

        return True # Hand completed normally

    def _check_hand_over(self):
        """Checks if the hand is over because only one player remains who isn't folded."""
        # Ensure self.players is not empty before proceeding
        if not self.players:
             print(f"{COLOR_RED}Error in _check_hand_over: self.players is empty.{COLOR_RESET}")
             return True # Consider hand over if no players exist

        not_folded = [name for name, data in self.players.items() if not data['folded']]
        if len(not_folded) <= 1:
            # Pot calculation check: Ensure pot reflects all bets before awarding
            final_pot = self.pot # Capture pot value before potentially modifying
            if not_folded:
                winner_name = not_folded[0]
                # Check if winner still exists in self.players before awarding pot
                if winner_name in self.players:
                     print(f"\n{COLOR_GREEN}{winner_name} wins the pot of {final_pot} as everyone else folded!{COLOR_RESET}")
                     self.players[winner_name]['chips'] += final_pot
                     self.session_stats['pots_won'] += 1
                     if not self.players[winner_name]['is_ai']:
                          self.session_stats['hands_won_fold'] += 1
                          self.session_stats['chips_won'] += final_pot # Simplification
                else:
                     print(f"{COLOR_YELLOW}Winner {winner_name} not found? Pot {final_pot} remains unawarded.{COLOR_RESET}")

            elif final_pot > 0: # Everyone folded, but pot exists? Should not happen.
                 print(f"{COLOR_YELLOW}Everyone folded? Awarding pot back? Pot: {final_pot} (Error case){COLOR_RESET}")

            self.pot = 0 # Reset pot only after awarding
            time.sleep(2)
            # Don't remove broke players here, do it at the very end of play_hand
            return True # Hand is over
        return False # Hand continues


    def _remove_broke_players(self):
         """Removes players with zero chips from the game AFTER a hand concludes."""
         # Operate on a copy of keys to avoid modification issues during iteration
         player_names_at_start = list(self.players.keys())
         original_order = list(self.player_order) # Copy original order
         removed_player = False
         current_button_player = self.player_order[self.dealer_button_pos] if self.player_order else None


         for name in player_names_at_start:
              if name in self.players and self.players[name]['chips'] <= 0:
                   print(f"{COLOR_RED}{name} has run out of chips and leaves the table.{COLOR_RESET}")
                   del self.players[name]
                   removed_player = True
                   # Remove from player_order list
                   if name in self.player_order:
                        self.player_order.remove(name)
                   time.sleep(0.5)

         # Adjust button position *after* all removals are done
         if removed_player and self.player_order: # Only adjust if players remain
              if current_button_player not in self.player_order:
                   # Button player was removed, find the player who *was* before them in the original order
                   try:
                        original_button_idx = original_order.index(current_button_player)
                        # Find the first player before the original button who is STILL in the new order
                        search_idx = (original_button_idx - 1 + len(original_order)) % len(original_order)
                        checked_indices = 0
                        while original_order[search_idx] not in self.player_order and checked_indices < len(original_order):
                             search_idx = (search_idx - 1 + len(original_order)) % len(original_order)
                             checked_indices += 1
                             # if search_idx == original_button_idx: break # Should not happen if players remain

                        if original_order[search_idx] in self.player_order:
                            new_button_player = original_order[search_idx]
                            self.dealer_button_pos = self.player_order.index(new_button_player)
                        else: # Fallback if no previous player found (e.g., only one player left)
                             self.dealer_button_pos = 0


                   except ValueError: # Error finding original button or previous player
                        self.dealer_button_pos = 0 # Default to first player
              else:
                   # Button player still exists, find their new index
                   try:
                        self.dealer_button_pos = self.player_order.index(current_button_player)
                   except ValueError: # Should not happen
                        self.dealer_button_pos = 0

         elif not self.player_order: # No players left
              self.dealer_button_pos = 0


         # Final check for game end conditions
         if removed_player:
              if not self.player_order:
                   print(f"{COLOR_RED}All players are out!{COLOR_RESET}")
              elif "Player" not in self.players:
                   print(f"{COLOR_RED}You ran out of chips!{COLOR_RESET}")


    def run_game(self):
        """Runs the main game loop for playing hands."""
        while True:
            # --- Pre-Hand Checks ---
            # Check if human player exists and has chips
            if "Player" not in self.players or self.players["Player"]['chips'] <= 0:
                 # Message printed by _remove_broke_players if applicable
                 print(f"\n{COLOR_RED}Game Over! Returning to menu.{COLOR_RESET}")
                 time.sleep(3)
                 break

            # Check if enough players remain (at least 2 with chips)
            active_players_with_chips = [name for name in self.player_order if name in self.players and self.players[name]['chips'] > 0]
            if len(active_players_with_chips) < 2:
                 print(f"\n{COLOR_YELLOW}Not enough players ({len(active_players_with_chips)}) with chips to continue. Game ending.{COLOR_RESET}")
                 if "Player" in active_players_with_chips:
                      print(f"{COLOR_GREEN}You are the last one standing! You win!{COLOR_RESET}")
                 time.sleep(3)
                 break

            # --- Play Hand ---
            hand_result = self.play_hand() # Returns True if hand completed, 'game_over' if critical issue

            # --- Post-Hand Checks ---
            if hand_result == 'game_over':
                 print(f"{COLOR_YELLOW}Critical error or no players left. Returning to main menu...{COLOR_RESET}")
                 time.sleep(2)
                 break
            elif hand_result is True: # Hand completed normally (showdown or folds)
                 # Player existence/chip check happens at the START of the loop

                 # Check if enough players remain for the *next* hand
                 active_players_next_hand = [name for name in self.player_order if name in self.players and self.players[name]['chips'] > 0]
                 if len(active_players_next_hand) < 2:
                      # Let the loop start again to print the end game message
                      continue

                 # Prompt for next hand if game continues
                 if "Player" in self.players: # Check if player still exists before printing chips
                      print(f"\n{COLOR_YELLOW}Your current chips: {self.players['Player']['chips']}{COLOR_RESET}")

                 try:
                      next_hand = input(f"Press Enter for next hand, or 'q' to return to menu... ").lower()
                      if next_hand == 'q':
                          break
                 except EOFError: # Handle Ctrl+D or other input errors
                      print(f"\n{COLOR_RED}Input error. Exiting game.{COLOR_RESET}")
                      break
            else: # Unexpected result from play_hand
                 print(f"{COLOR_RED}Unexpected hand result '{hand_result}'. Returning to menu.{COLOR_RESET}")
                 break
        clear_screen()


    def save_game(self):
        """Saves the current game state to a file."""
        # Ensure player data is serializable
        players_serializable = {}
        for name, data in self.players.items():
            players_serializable[name] = data.copy()
            # Convert enums to names for JSON
            if data.get('ai_type'): players_serializable[name]['ai_type'] = data['ai_type'].name
            if data.get('last_action'): players_serializable[name]['last_action'] = (data['last_action'][0].name, data['last_action'][1])
            # Hands (list of dicts) are usually JSON serializable

        state = {
            "players": players_serializable,
            "community_cards": self.community_cards,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "last_raiser": self.last_raiser,
            "last_raiser_amount": self.last_raiser_amount,
            "dealer_button_pos": self.dealer_button_pos,
            # current_player_index is transient, no need to save
            "phase": self.phase.name, # Save phase name
            "session_stats": self.session_stats,
            "settings": self.settings,
            "player_order": self.player_order, # Save the order
            "deck": self.deck # Save remaining deck state
        }
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
            print(f"{COLOR_GREEN}Game saved successfully to {SAVE_FILE}{COLOR_RESET}")
        except TypeError as e:
             print(f"{COLOR_RED}Error saving game (Type Error): {e}{COLOR_RESET}")
             # print("Problematic state:", state) # Debugging - state might be too large
        except IOError as e:
            print(f"{COLOR_RED}Error saving game (IO Error): {e}{COLOR_RESET}")
        time.sleep(1.5)

    def load_game(self):
        """Loads game state from a file."""
        try:
            if not os.path.exists(SAVE_FILE):
                print(f"{COLOR_YELLOW}No save file found ({SAVE_FILE}).{COLOR_RESET}")
                time.sleep(1.5); return False

            with open(SAVE_FILE, 'r') as f:
                state = json.load(f)

            # Restore state carefully
            loaded_players = state.get("players", {})
            self.players = {}
            for name, data in loaded_players.items():
                 self.players[name] = data.copy()
                 # Convert names back to enums
                 if data.get('ai_type'):
                      try: self.players[name]['ai_type'] = AIType[data['ai_type']]
                      except KeyError: self.players[name]['ai_type'] = AIType.RANDOM
                 # Add 'ai_type': None for human player if missing after load
                 elif not data.get('is_ai', False): # Check if it's the human player
                      self.players[name]['ai_type'] = None

                 if data.get('last_action'):
                      try: self.players[name]['last_action'] = (PlayerAction[data['last_action'][0]], data['last_action'][1])
                      except KeyError: self.players[name]['last_action'] = None
                 # Ensure hand is loaded correctly (should be list of dicts)
                 self.players[name]['hand'] = data.get('hand', [])


            self.community_cards = state.get("community_cards", [])
            self.pot = state.get("pot", 0)
            self.current_bet = state.get("current_bet", 0)
            self.last_raiser = state.get("last_raiser")
            self.last_raiser_amount = state.get("last_raiser_amount", 0)
            self.dealer_button_pos = state.get("dealer_button_pos", 0)
            try: self.phase = GamePhase[state.get("phase", "PREFLOP")]
            except KeyError: self.phase = GamePhase.PREFLOP
            self.session_stats = state.get("session_stats", self._default_stats())
            self.settings = state.get("settings", self._default_settings())
            self.player_order = state.get("player_order", list(self.players.keys()))
            self.deck = state.get("deck", []) # Load remaining deck

            # Validate loaded state
            if not self.player_order: # If player order is empty, try to reconstruct
                 self.player_order = list(self.players.keys())
            if self.dealer_button_pos >= len(self.player_order) and len(self.player_order) > 0:
                 self.dealer_button_pos = 0
            if not self.deck: # If deck wasn't saved or is empty, create a new one
                 print(f"{COLOR_YELLOW}Deck state not loaded or empty, creating new shuffled deck.{COLOR_RESET}")
                 self._create_and_shuffle_deck()


            print(f"{COLOR_GREEN}Game loaded successfully from {SAVE_FILE}{COLOR_RESET}")
            if "Player" in self.players:
                 print(f"Loaded Player Chips: {self.players['Player']['chips']}")
            # Display the loaded table state?
            # self.display_table(show_all_hands=(self.phase == GamePhase.SHOWDOWN)) # Show hands if loaded at showdown
            time.sleep(2)
            return True

        except (IOError, json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"{COLOR_RED}Error loading game: {e}{COLOR_RESET}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            time.sleep(1.5)
            return False


# --- Main Application Logic ---
def main():
    """Main function to run the application."""
    global TERMINAL_WIDTH
    try:
        try: TERMINAL_WIDTH = os.get_terminal_size().columns
        except OSError: TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH; print(f"{COLOR_YELLOW}Using default width: {TERMINAL_WIDTH}{COLOR_RESET}")

        game_instance = None
        # Load default settings and stats initially
        current_settings = PokerGame._default_settings(None)
        current_stats = PokerGame._default_stats(None)

        title_screen()
        while True:
            # Pass current stats to display_menu if needed, but stats are managed by game_instance
            choice = display_menu()

            if choice == '1': # Play New Game
                print(f"\n{COLOR_YELLOW}Starting new Poker game...{COLOR_RESET}")
                time.sleep(1)
                # Use current settings, but create new stats for the new game
                current_stats = PokerGame._default_stats(None)
                game_instance = PokerGame(settings=current_settings, stats=current_stats)
                game_instance.run_game()
                # After game finishes, update the persistent stats variable
                if game_instance: current_stats = game_instance.session_stats

            elif choice == '2': display_rules(); continue
            elif choice == '3': display_settings_menu(current_settings); continue # Placeholder
            elif choice == '4': display_stats(current_stats); continue # Display current session/loaded stats
            elif choice == '5': # Save Game
                if game_instance and game_instance.players: # Check if a game is active
                     game_instance.save_game()
                else: print(f"{COLOR_YELLOW}No active game to save.{COLOR_RESET}"); time.sleep(1)
                continue
            elif choice == '6': # Load Game
                 # Create a temporary instance to load into
                 temp_game = PokerGame()
                 if temp_game.load_game():
                      game_instance = temp_game # Replace current instance with loaded one
                      # Update persistent settings and stats from the loaded game
                      current_settings = game_instance.settings
                      current_stats = game_instance.session_stats
                      print(f"{COLOR_GREEN}Resuming loaded game...{COLOR_RESET}"); time.sleep(1)
                      # Run the loaded game
                      game_instance.run_game()
                      # Update stats again after the loaded game finishes
                      if game_instance: current_stats = game_instance.session_stats
                 # No need for 'else', load_game prints error messages
                 continue
            elif choice == '7': # Quit
                print(f"\n{COLOR_MAGENTA}Thanks for playing Poker!{COLOR_RESET}"); break

    except KeyboardInterrupt: print(f"\n{COLOR_RED}Game interrupted. Exiting.{COLOR_RESET}")
    except Exception as e:
         print(f"\n{COLOR_RED}An unexpected error occurred in main loop: {e}{COLOR_RESET}")
         import traceback; traceback.print_exc()
    finally: print(COLOR_RESET) # Reset color on exit


# --- Start Game ---
if __name__ == "__main__":
    # Color Support Check (same as Blackjack)
    can_use_color = sys.stdout.isatty() and os.name == 'posix'
    if os.name == 'nt':
        # Attempt to enable ANSI escape codes on Windows 10+
        os.system('')
        can_use_color = True # Assume it works if os.system('') runs without error
        # A more robust check might involve ctypes, but keep it simple
    if not can_use_color:
        print("Running without color support (or cannot detect).")
        # Define empty strings if colors are not supported
        COLOR_RESET=COLOR_RED=COLOR_BLACK=COLOR_WHITE_BG=COLOR_GREEN=COLOR_YELLOW=COLOR_BLUE=COLOR_MAGENTA=COLOR_BOLD=COLOR_DIM=COLOR_CYAN=""

    main()

