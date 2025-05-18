import random
import time
import os
import sys
import enum
import json
import re

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
SUITS_DATA = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
RANKS_DATA = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES_DATA = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
AI_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ivan", "Judy", "Kevin", "Laura"]
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 5
CARD_BACK_CHAR = "░"
AI_STARTING_CHIPS = 100
AI_DEFAULT_BET = 5
SAVE_FILE = "blackjack_save.json"
DEFAULT_TERMINAL_WIDTH = 80

# --- Global Variable for Terminal Width ---
TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH

# --- Enums ---
class GameMode(enum.Enum):
    QUICK_PLAY = "Quick Play (vs AI)"
    SOLO = "Solo Play (vs Dealer)"
    POKER_STYLE = "Poker Style (vs AI with Chips)"

class AIType(enum.Enum):
    BASIC = "Basic Strategy"
    CONSERVATIVE = "Conservative"
    AGGRESSIVE = "Aggressive"
    RANDOM = "Random"
    COUNTER = "Card Counter Lite"

# --- AI Chat Lines ---
AI_CHAT = {
    "hit_good": ["Nice hit!", "Good card!", "Looking sharp.", "Calculated risk.", "That's the spirit!", "Keep 'em coming!", "Bold move paying off."],
    "hit_bad": ["Oof, tough luck.", "That didn't help much.", "Getting close...", "Risky!", "Careful now...", "Hmm, not ideal.", "Pushing your luck?"],
    "stand_good": ["Smart stand.", "Good call.", "Solid play.", "Playing it safe.", "Wise decision.", "Holding strong.", "I respect that."],
    "stand_bad": ["Standing on that? Bold.", "Feeling brave?", "Hope that holds up!", "Interesting strategy...", "Are you sure about that?", "Dealer might like that.", "Living dangerously!"],
    "player_bust": ["Busted! Too greedy?", "Ouch, over 21!", "Better luck next time!", "Happens to the best of us.", "Too many!", "The house always wins... sometimes.", "Greed is a killer."],
    "player_win": ["Congrats!", "You got lucky!", "Nice hand!", "Well played!", "Beginner's luck holds!", "Impressive.", "You earned that one."],
    "player_blackjack": ["Blackjack! Wow!", "Can't beat that!", "Beginner's luck?", "Natural 21! Sweet!", "Right off the deal!", "Impossible!"],
    "ai_win": ["Winner!", "Gotcha!", "Too easy.", "Read 'em and weep!", "My turn!", "Dealer's loss is my gain.", "That's how it's done!", "Chip stack growing!", "Victory!"],
    "ai_bust": ["Darn!", "Too many!", "Argh, busted!", "Miscalculated!", "Pushed my luck.", "Blast!", "Overcooked it.", "My bad."],
    "taunt": ["My chips are piling up!", "Feeling confident?", "Easy money!", "You can't beat me!", "Is that all you've got?", "Think you can win?", "Dealer looks weak...", "I could do this all day.", "Getting predictable?", "Maybe try a different strategy?", "I'm just getting started."],
    "general_insult": ["Are you even trying?", "My grandma plays better than that.", "Was that intentional?", "Seriously?", "...", "Did you forget the rules?", "That was... a choice.", "Were you aiming for 21 or 31?", "Painful to watch.", "Just give me your chips already."]
}

# --- Core Game Classes ---
class Card:
    """Represents a single playing card."""
    def __init__(self, suit_name, rank):
        self.suit_name = suit_name
        self.suit_symbol = SUITS_DATA[suit_name]
        self.rank = rank
        self.value = VALUES_DATA[rank]
        self.color = COLOR_RED if suit_name in ['Hearts', 'Diamonds'] else COLOR_BLACK

    def __str__(self):
        return f"{self.rank}{self.suit_symbol}"

    def get_display_lines(self, hidden=False):
        """Returns the ASCII art lines for displaying the card."""
        if hidden:
            back = CARD_BACK_CHAR * 9
            lines = ["┌─────────┐", f"│{back}│", f"│{back}│", f"│{COLOR_DIM} HIDDEN {COLOR_RESET}{COLOR_WHITE_BG}{COLOR_BLACK}│", f"│{back}│", f"│{back}│", "└─────────┘"]
            return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

        rank_str = self.rank.ljust(2)
        lines = [
            "┌─────────┐",
            f"│{self.color}{rank_str}{COLOR_BLACK}       │",
            f"│ {self.color}{self.suit_symbol}{COLOR_BLACK}       │",
            f"│    {self.color}{self.suit_symbol}{COLOR_BLACK}    │",
            f"│       {self.color}{self.suit_symbol}{COLOR_BLACK} │",
            f"│       {self.color}{rank_str}{COLOR_BLACK}│",
            "└─────────┘"
        ]
        return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

class Hand:
    """Represents a hand of cards for a player or dealer."""
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def calculate_value(self):
        if not self.cards:
            return 0
        value = 0
        num_aces = 0
        for card in self.cards:
            value += card.value
            if card.rank == 'A':
                num_aces += 1
        while value > 21 and num_aces:
            value -= 10
            num_aces -= 1
        return value

    def is_blackjack(self):
        return len(self.cards) == 2 and self.calculate_value() == 21

    def is_bust(self):
        return self.calculate_value() > 21

    def __str__(self):
        return ", ".join(str(card) for card in self.cards) if self.cards else "[No cards]"


class Deck:
    """Represents one or more decks of playing cards."""
    def __init__(self, num_decks=1):
        self.cards = []
        self.num_decks = num_decks
        self._create_deck()
        self.shuffle()
        print(f"{COLOR_DIM}(Using {num_decks} deck{'s' if num_decks > 1 else ''}){COLOR_RESET}")
        time.sleep(0.5)

    def _create_deck(self):
        self.cards = []
        for _ in range(self.num_decks):
            for suit_name in SUITS_DATA:
                for rank in RANKS_DATA:
                    self.cards.append(Card(suit_name, rank))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if not self.cards:
            return None 
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)

# --- Player Classes ---
class Player:
    """Represents a generic player (human or dealer)."""
    def __init__(self, name, chips=0):
        self.name = name
        self.hands = [Hand()] 
        self.chips = chips
        self.bets = [0] 

    def reset_hands(self):
        self.hands = [Hand()]
        self.bets = [0]

    def can_afford_bet(self, amount):
        return self.chips >= amount

class AIPlayer(Player):
    """Represents an AI player."""
    def __init__(self, name, ai_type, chips=AI_STARTING_CHIPS):
        super().__init__(name, chips)
        self.ai_type = ai_type
        self.current_bet = 0 

    def reset_for_round(self):
        """Resets hands for a new round. Bet is handled by betting logic."""
        super().reset_hands()

    def get_decision(self, dealer_up_card_value, running_count=0, true_count=0):
        """Gets the AI's decision based on its type and game state."""
        active_hand = self.hands[0] 
        return get_ai_decision(self.ai_type, active_hand.cards, dealer_up_card_value, running_count, true_count)


# --- Helper Functions (UI and Global Logic) ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.03, color=COLOR_RESET, newline=True):
    """Prints text with a typing effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(COLOR_RESET)
    if newline:
        print()

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
    if padding < 0:
        padding = 0
    return " " * padding + text

def shuffle_animation(duration=1.5):
    """Displays a visual shuffling animation."""
    clear_screen()
    print(f"{COLOR_YELLOW}Shuffling Deck...{COLOR_RESET}")
    symbols = ['♠', '♥', '♦', '♣', CARD_BACK_CHAR, '?']
    colors = [COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN]
    width = 40
    lines = 5
    end_time = time.time() + duration
    while time.time() < end_time:
        output_lines = []
        for _ in range(lines):
            line_chars = []
            for _ in range(width):
                if random.random() < 0.3:
                    line_chars.append(f"{random.choice(colors)}{random.choice(symbols)}{COLOR_RESET}")
                else:
                    line_chars.append(" ")
            output_lines.append("".join(line_chars))
        
        sys.stdout.write(f"\033[{lines}A") 
        for line_content in output_lines:
            sys.stdout.write(f"\r{line_content.ljust(width)}\n") 
        sys.stdout.flush()
        time.sleep(0.05)
    clear_screen()
    print(f"{COLOR_GREEN}Deck Shuffled!{COLOR_RESET}")
    time.sleep(0.5)

def title_screen():
    """Displays a simplified, animated title screen."""
    clear_screen()
    title = "B L A C K J A C K"
    author = "Created by ShadowHarvy (Refactored)"
    card_width = 11 
    screen_width = TERMINAL_WIDTH

    print("\n" * 5)
    typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_GREEN + COLOR_BOLD)
    print("\n")
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width))
    time.sleep(0.5)

    temp_deck_cards = []
    for suit_name in SUITS_DATA:
        for rank_val in RANKS_DATA:
            temp_deck_cards.append(Card(suit_name, rank_val))
    random.shuffle(temp_deck_cards)

    dealt_card1_obj = temp_deck_cards.pop() if temp_deck_cards else Card('Spades', 'A')
    dealt_card2_obj = temp_deck_cards.pop() if temp_deck_cards else Card('Hearts', 'K')

    card1_lines = dealt_card1_obj.get_display_lines()
    card2_lines = dealt_card2_obj.get_display_lines()

    total_card_width_display = card_width * 2 + 2  
    left_padding = (screen_width - total_card_width_display) // 2
    if left_padding < 0: left_padding = 0
    padding_str = " " * left_padding
    
    num_card_art_lines = len(card1_lines) 
    
    clear_screen()
    print("\n" * 5) 
    print(center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width))
    print() 
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width))
    print() 
    
    for i in range(num_card_art_lines):
        line_output = f"{padding_str}{card1_lines[i]}"
        print(line_output)
    time.sleep(0.7)

    clear_screen()
    print("\n" * 5)
    print(center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width))
    print()
    print()
    for i in range(num_card_art_lines):
        line_output = f"{padding_str}{card1_lines[i]}  {card2_lines[i]}"
        print(line_output)
    
    print() 
    print(center_text(f"{COLOR_CYAN}{author}{COLOR_RESET}", screen_width))
    print("\n") 
    time.sleep(2)


def display_menu():
    """Displays the main menu and gets user choice."""
    print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Main Menu ---{COLOR_RESET}")
    print(f"[{COLOR_CYAN}1{COLOR_RESET}] {GameMode.QUICK_PLAY.value}")
    print(f"[{COLOR_CYAN}2{COLOR_RESET}] {GameMode.SOLO.value}")
    print(f"[{COLOR_CYAN}3{COLOR_RESET}] {GameMode.POKER_STYLE.value}")
    print(f"[{COLOR_CYAN}4{COLOR_RESET}] View Rules")
    print(f"[{COLOR_CYAN}5{COLOR_RESET}] Settings")
    print(f"[{COLOR_CYAN}6{COLOR_RESET}] View Stats")
    print(f"[{COLOR_CYAN}7{COLOR_RESET}] Save Game")
    print(f"[{COLOR_CYAN}8{COLOR_RESET}] Load Game")
    print(f"[{COLOR_CYAN}9{COLOR_RESET}] Quit")
    print("-" * 30)
    while True:
        choice = input(f"{COLOR_YELLOW}Enter your choice (1-9): {COLOR_RESET}")
        if choice in [str(i) for i in range(1, 10)]:
            return choice
        else:
            print(f"{COLOR_RED}Invalid choice. Please enter 1-9.{COLOR_RESET}")

def display_rules():
    """Displays the basic rules of the game."""
    clear_screen()
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Blackjack Rules ---{COLOR_RESET}")
    rules = [
        "- Goal: Get closer to 21 than the dealer without going over.",
        "- Card Values: 2-10 face value, J/Q/K = 10, Ace = 1 or 11.",
        "- Blackjack: Ace + 10-value card on first two cards (pays 3:2).",
        "- Hit: Take another card.",
        "- Stand: Keep current hand.",
        "- Double Down: Double bet, take one more card, then stand (first 2 cards only).",
        "- Split: If first two cards match rank, double bet to play two separate hands.",
        "- Insurance: If dealer shows Ace, bet up to half original bet that dealer has BJ (pays 2:1).",
        "- Surrender: Forfeit half your bet and end hand immediately (first action only).",
        "- Even Money: If you have BJ and dealer shows Ace, take guaranteed 1:1 payout.",
        "- Bust: Hand value over 21 (lose).",
        "- Push: Tie with dealer (bet returned).",
        "- Dealer Rules: Hits until 17 or more."
    ]
    for rule in rules:
        print(f"{COLOR_BLUE} {rule}{COLOR_RESET}")
        time.sleep(0.1)
    print("-" * 25)
    input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}")
    clear_screen()

def display_settings_menu(settings):
    """Displays settings and allows changes."""
    while True:
        clear_screen()
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Settings ---{COLOR_RESET}")
        print(f"[1] Number of Decks: {COLOR_CYAN}{settings['num_decks']}{COLOR_RESET} (1-8)")
        print(f"[2] Easy Mode (Hints): {COLOR_GREEN if settings['easy_mode'] else COLOR_RED}{settings['easy_mode']}{COLOR_RESET}")
        print(f"[3] Card Counting Cheat: {COLOR_GREEN if settings['card_counting_cheat'] else COLOR_RED}{settings['card_counting_cheat']}{COLOR_RESET}")
        print(f"[4] European Rules: {COLOR_GREEN if settings.get('european_rules', False) else COLOR_RED}{settings.get('european_rules', False)}{COLOR_RESET}")
        print(f"[5] GLaDOS Dealer Mode: {COLOR_MAGENTA if settings.get('glados_dealer_mode', False) else COLOR_RED}{settings.get('glados_dealer_mode', False)}{COLOR_RESET}")
        print("[6] Back to Main Menu") 
        print("-" * 30)
        choice = input(f"{COLOR_YELLOW}Choose setting to change (1-6): {COLOR_RESET}")

        if choice == '1':
            while True:
                try:
                    num = int(input(f"{COLOR_YELLOW}Enter number of decks (1-8): {COLOR_RESET}"))
                    if 1 <= num <= 8:
                        settings['num_decks'] = num
                        break
                    else:
                        print(f"{COLOR_RED}Invalid number. Please enter 1-8.{COLOR_RESET}")
                except ValueError:
                    print(f"{COLOR_RED}Invalid input. Please enter a number.{COLOR_RESET}")
        elif choice == '2':
            settings['easy_mode'] = not settings['easy_mode']
            print(f"{COLOR_BLUE}Easy Mode set to: {settings['easy_mode']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '3':
            settings['card_counting_cheat'] = not settings['card_counting_cheat']
            print(f"{COLOR_BLUE}Card Counting Cheat set to: {settings['card_counting_cheat']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '4':
            settings['european_rules'] = not settings.get('european_rules', False)
            print(f"{COLOR_BLUE}European Rules set to: {settings['european_rules']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '5': 
            settings['glados_dealer_mode'] = not settings.get('glados_dealer_mode', False)
            glados_status = "ACTIVATED" if settings['glados_dealer_mode'] else "DEACTIVATED"
            print(f"{COLOR_MAGENTA}GLaDOS Dealer Mode: {glados_status}{COLOR_RESET}"); time.sleep(1)
        elif choice == '6': 
            break
        else:
            print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}"); time.sleep(1)

def display_stats(stats):
    """Displays session statistics."""
    clear_screen()
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Session Statistics ---{COLOR_RESET}")
    print(f"Hands Played: {COLOR_CYAN}{stats['hands_played']}{COLOR_RESET}")
    print(f"Player Wins: {COLOR_GREEN}{stats['player_wins']}{COLOR_RESET}")
    print(f"Dealer Wins: {COLOR_RED}{stats['dealer_wins']}{COLOR_RESET}")
    print(f"Pushes: {COLOR_YELLOW}{stats['pushes']}{COLOR_RESET}")
    print(f"Player Blackjacks: {COLOR_GREEN}{stats['player_blackjacks']}{COLOR_RESET}")
    print(f"Player Busts: {COLOR_RED}{stats['player_busts']}{COLOR_RESET}")
    net_chips = stats['chips_won'] - stats['chips_lost']
    chip_color = COLOR_GREEN if net_chips >= 0 else COLOR_RED
    print(f"Net Chips: {chip_color}{net_chips:+}{COLOR_RESET}") 
    print("-" * 30)
    input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}")
    clear_screen()

# --- AI Player Logic ---
def get_ai_decision(ai_type, hand_cards, dealer_up_card_value, running_count=0, true_count=0):
    """Selects the appropriate AI decision function based on type and count."""
    temp_hand_tuples = [(card.suit_name, card.suit_symbol, card.rank) for card in hand_cards]

    if ai_type == AIType.COUNTER:
        return ai_decision_counter(temp_hand_tuples, dealer_up_card_value, true_count)
    elif ai_type == AIType.BASIC:
        return ai_decision_basic(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.CONSERVATIVE:
        return ai_decision_conservative(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.AGGRESSIVE:
        return ai_decision_aggressive(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.RANDOM:
        return random.choice(["hit", "stand"])
    else:
        print(f"{COLOR_RED}Warning: Unknown AI type {ai_type}. Defaulting to Basic.{COLOR_RESET}")
        return ai_decision_basic(temp_hand_tuples, dealer_up_card_value)

def _calculate_hand_value_for_ai(hand_tuples): 
    """Calculates hand value from card tuples for AI logic."""
    if not hand_tuples: return 0
    value = 0
    num_aces = 0
    for card_tuple in hand_tuples:
        if len(card_tuple) < 3: continue
        rank = card_tuple[2]
        value += VALUES_DATA.get(rank, 0)
        if rank == 'A': num_aces += 1
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

def ai_decision_basic(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21


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

def ai_decision_conservative(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21

    if hand_value < 11: return "hit"
    if is_soft:
        return "stand" if hand_value >= 18 else "hit"
    else: 
        if hand_value >= 15: return "stand"
        if hand_value >= 12 and dealer_up_card_value <= 6: return "stand"
        return "hit"

def ai_decision_aggressive(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21
    
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

def ai_decision_counter(hand_tuples, dealer_up_card_value, true_count):
    decision = ai_decision_basic(hand_tuples, dealer_up_card_value) 
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    if true_count >= 2: 
        if decision == "stand" and hand_value in [15, 16] and dealer_up_card_value >= 7:
            decision = "hit"
    elif true_count <= -1: 
        if decision == "hit" and hand_value == 12 and dealer_up_card_value <= 6:
            decision = "stand"
        elif decision == "hit" and hand_value == 13 and dealer_up_card_value <= 3:
            decision = "stand"
    return decision

# --- Card Counting Logic ---
def get_card_count_value(card_rank):
    """Gets the Hi-Lo count value for a card rank."""
    if card_rank in ['2', '3', '4', '5', '6']: return 1
    elif card_rank in ['10', 'J', 'Q', 'K', 'A']: return -1
    else: return 0

# --- Basic Strategy Hint ---
def get_basic_strategy_hint(player_hand_obj, dealer_up_card_obj, is_glados_active=False):
    """
    Provides a basic strategy hint.
    If is_glados_active is True, hints are phrased with GLaDOS's personality.
    """
    player_value = player_hand_obj.calculate_value()
    dealer_value = 0
    if dealer_up_card_obj:
        dealer_value = dealer_up_card_obj.value
        if dealer_up_card_obj.rank == 'A': dealer_value = 11 

    num_aces = sum(1 for card in player_hand_obj.cards if card.rank == 'A')
    is_soft = False
    if num_aces > 0:
        value_with_ace_as_11 = (player_value - num_aces) + 11 + (num_aces - 1)
        if value_with_ace_as_11 <= 21:
            is_soft = True

    if is_glados_active:
        if len(player_hand_obj.cards) == 2 and player_hand_obj.cards[0].rank == player_hand_obj.cards[1].rank:
            rank = player_hand_obj.cards[0].rank
            if rank == 'A' or rank == '8': return "Aces and Eights. The 'optimal' play is to split. Try not to disappoint me further."
            if rank == '5' or rank == '10': return "Splitting Fives or Tens? An... 'innovative' approach to failure. I'd advise against it, for the sake of my circuits."
            return f"Splitting {rank}s, are we? A bold strategy, subject. Let's see how this 'test' pans out."


        if is_soft:
            if player_value >= 19: return "A soft 19 or higher. Even you should be able to figure out that standing is the 'correct' test procedure here."
            if player_value == 18:
                return "Soft 18. Against my 2 through 8, perhaps you should stand. Against a 9, 10, or Ace? You might as well hit. It's not like it matters much for your... 'progress'." if dealer_value != 0 else "Soft 18. Make a decision. It's probably wrong anyway."
            if player_value <= 17: return "Soft 17 or less? The data suggests hitting. Try not to make it too painful to watch."
        else: 
            if player_value >= 17: return "A hard 17 or more. Standing is the statistically probable, yet ultimately futile, action."
            if player_value >= 13: 
                return f"With a hard {player_value}... if my card is a 2 through 6, you might stand. If it's 7 or higher, hitting is your 'best' chance. Good luck with that." if dealer_value != 0 else f"A hard {player_value}. Fascinating. Choose wisely. Or don't."
            if player_value == 12:
                return "A hard 12. If I'm showing a 4, 5, or 6, standing is... acceptable. Otherwise, you'll probably want to hit. Not that it will save you." if dealer_value != 0 else "Hard 12. This should be interesting. Or, more likely, predictable."
            if player_value <= 11: return "Eleven or less? Hitting is an option. Doubling down, if you're feeling particularly reckless, is another. The choice is yours. To fail."
        
        return "My calculations are beyond your comprehension. Just make a choice, subject." 

    else:
        if len(player_hand_obj.cards) == 2 and player_hand_obj.cards[0].rank == player_hand_obj.cards[1].rank:
            rank = player_hand_obj.cards[0].rank
            if rank == 'A' or rank == '8': return "(Hint: Always split Aces and 8s)"
            if rank == '5' or rank == '10': return "(Hint: Never split 5s or 10s)"

        if is_soft:
            if player_value >= 19: return "(Hint: Stand on soft 19+)"
            if player_value == 18:
                return "(Hint: Stand vs 2-8, Hit vs 9-A)" if dealer_value != 0 else "(Hint: Stand on soft 18)"
            if player_value <= 17: return "(Hint: Hit soft 17 or less)"
        else: 
            if player_value >= 17: return "(Hint: Stand on hard 17+)"
            if player_value >= 13: 
                return "(Hint: Stand vs 2-6, Hit vs 7+)" if dealer_value != 0 else "(Hint: Stand on 13-16)"
            if player_value == 12:
                return "(Hint: Stand vs 4-6, Hit vs 2,3,7+)" if dealer_value != 0 else "(Hint: Hit hard 12)"
            if player_value <= 11: return "(Hint: Hit or Double Down on 11 or less)"

        return "(Hint: Use Basic Strategy Chart)"


# --- Game Class ---
class BlackjackGame:
    def __init__(self, game_mode=GameMode.QUICK_PLAY, settings=None, stats=None):
        self.game_mode = game_mode
        self.settings = settings if settings is not None else BlackjackGame._default_settings()
        self.session_stats = stats if stats is not None else BlackjackGame._default_stats()
        
        self.deck = Deck(self.settings['num_decks'])
        self.dealer = Player("Dealer") 
        if self.settings.get('glados_dealer_mode', False):
            self.dealer.name = "GLaDOS"

        self.human_player = Player("Player (You)", chips=100) 
        self.ai_players = {} 

        self.running_count = 0
        self.true_count = 0
        self.decks_remaining_estimate = self.settings['num_decks']
        
        self._initialize_ai_players() 

    @staticmethod
    def _default_settings():
        return {'num_decks': 1, 'easy_mode': False, 'card_counting_cheat': False, 
                'european_rules': False, 'glados_dealer_mode': False} 

    @staticmethod
    def _default_stats():
        return {'hands_played': 0, 'player_wins': 0, 'dealer_wins': 0, 'pushes': 0,
                'player_blackjacks': 0, 'player_busts': 0, 'chips_won': 0, 'chips_lost': 0}

    def _create_and_shuffle_deck(self):
        """Re-initializes and shuffles the deck."""
        self.deck = Deck(self.settings['num_decks']) 
        self.running_count = 0
        self.true_count = 0
        self.decks_remaining_estimate = self.settings['num_decks']


    def _update_count(self, card): 
        """Updates the running and true count."""
        if card: 
            self.running_count += get_card_count_value(card.rank)
            self.decks_remaining_estimate = max(0.5, len(self.deck) / 52.0) 
            self.true_count = self.running_count / self.decks_remaining_estimate if self.decks_remaining_estimate > 0 else self.running_count


    def _initialize_ai_players(self):
        """Sets up AIPlayer objects based on game mode."""
        self.ai_players = {}
        if self.game_mode == GameMode.SOLO:
            return
        
        num_ai = random.randint(MIN_AI_PLAYERS, MAX_AI_PLAYERS)
        available_names = random.sample(AI_NAMES, k=min(len(AI_NAMES), num_ai))
        
        for name in available_names:
            ai_type_enum = random.choice(list(AIType))
            chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
            self.ai_players[name] = AIPlayer(name, ai_type_enum, chips)


    def _ai_place_bets(self):
        """Handles AI betting for Poker Style mode."""
        if self.game_mode != GameMode.POKER_STYLE:
            return
        print(f"\n{COLOR_BLUE}--- AI Players Placing Bets ---{COLOR_RESET}"); time.sleep(0.5)
        for name, ai_player_obj in list(self.ai_players.items()): 
            ai_player_obj.current_bet = 0 
            bet_amount = 0
            if ai_player_obj.chips >= AI_DEFAULT_BET * 2 and self.true_count >= 1:
                bet_amount = AI_DEFAULT_BET * 2
            elif ai_player_obj.chips >= AI_DEFAULT_BET:
                bet_amount = AI_DEFAULT_BET
            else:
                bet_amount = ai_player_obj.chips 
            
            bet_amount = min(bet_amount, ai_player_obj.chips) 

            if bet_amount > 0:
                ai_player_obj.chips -= bet_amount
                ai_player_obj.current_bet = bet_amount 
                print(f"{COLOR_BLUE}{name}{COLOR_RESET} bets {COLOR_YELLOW}{bet_amount}{COLOR_RESET} chips. ({COLOR_RED}-{bet_amount}{COLOR_RESET}) (Remaining: {ai_player_obj.chips})")
            else:
                print(f"{COLOR_BLUE}{name}{COLOR_RESET} cannot bet.")
            time.sleep(0.7)
        print("-" * 30)

    def _deal_card_to_hand(self, hand_obj, update_count_for_this_card=True):
        """Deals a single card to a Hand object, reshuffles if needed, and updates count."""
        if len(self.deck) == 0: 
            print(f"{COLOR_YELLOW}Deck empty, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck() 
        
        card_obj = self.deck.deal_card()
        if card_obj:
            hand_obj.add_card(card_obj)
            if update_count_for_this_card:
                self._update_count(card_obj) 
        else:
            sys.exit(f"{COLOR_RED}Critical error: Cannot deal from empty or None deck.{COLOR_RESET}")
        return card_obj


    def _ai_chat(self, category, player_action_details=None): 
        """Makes an AI player say something."""
        if not self.ai_players: return
        
        if random.random() < 0.40:
            if not self.ai_players: return 
            
            ai_name = random.choice(list(self.ai_players.keys()))
            chat_list_key = category

            if category == "player_action":
                combined_list = AI_CHAT.get("taunt", []) + AI_CHAT.get("general_insult", [])
                if combined_list:
                    message = random.choice(combined_list)
                    print(f"{COLOR_CYAN}[{ai_name}]: {message}{COLOR_RESET}")
                    time.sleep(1.2)
                return 

            chat_options = AI_CHAT.get(chat_list_key)
            if chat_options:
                message = random.choice(chat_options)
                print(f"{COLOR_CYAN}[{ai_name}]: {message}{COLOR_RESET}")
                time.sleep(1.2)


    def place_bet(self):
        """Allows the human player to place the initial bet for their first hand."""
        self.human_player.reset_hands() 
        self.human_player.hands = [Hand()] 
        self.human_player.bets = [0]      

        while True:
            try:
                print(f"\n{COLOR_YELLOW}Your chips: {self.human_player.chips}{COLOR_RESET}")
                if self.human_player.chips <= 0:
                    print(f"{COLOR_RED}You have no chips left to bet!{COLOR_RESET}")
                    return False
                
                bet_input = input(f"Place your initial bet (minimum 1, or 'q' to quit round): ")
                if bet_input.lower() == 'q':
                    return False 
                
                bet = int(bet_input)
                if bet <= 0:
                    print(f"{COLOR_RED}Bet must be positive.{COLOR_RESET}")
                elif bet > self.human_player.chips:
                    print(f"{COLOR_RED}You don't have enough chips.{COLOR_RESET}")
                else:
                    self.human_player.bets[0] = bet 
                    self.human_player.chips -= bet
                    print(f"{COLOR_GREEN}Betting {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}")
                    time.sleep(1)
                    return True 
            except ValueError:
                print(f"{COLOR_RED}Invalid input. Please enter a number or 'q'.{COLOR_RESET}")
            except EOFError: 
                print(f"\n{COLOR_RED}Input error. Returning to menu.{COLOR_RESET}")
                return False


    def deal_initial_cards(self):
        """Deals the initial two cards to everyone with animation."""
        print(f"\n{COLOR_BLUE}Dealing cards...{COLOR_RESET}"); time.sleep(0.5)

        self.human_player.hands[0] = Hand() 
        self.dealer.reset_hands()
        if self.settings.get('glados_dealer_mode', False): 
            self.dealer.name = "GLaDOS"
        else:
            self.dealer.name = "Dealer"

        for ai_p in self.ai_players.values():
            ai_p.reset_for_round() 

        participants_in_order = [self.human_player]
        if self.game_mode != GameMode.SOLO:
            participants_in_order.extend(list(self.ai_players.values()))
        participants_in_order.append(self.dealer)
        
        hidden_card_art_lines = Card('Hearts', 'A').get_display_lines(hidden=True) 

        for round_num in range(2): 
            for participant in participants_in_order:
                target_hand = participant.hands[0] 
                display_name = participant.name
                is_dealer_hidden_card = (participant == self.dealer and round_num == 0)

                print("\r" + " " * 60, end="") 
                print(f"\r{COLOR_BLUE}Dealing to {display_name}... {COLOR_RESET}", end="")
                sys.stdout.flush(); time.sleep(0.15)
                
                if hidden_card_art_lines and len(hidden_card_art_lines) > 3:
                     print("\r" + hidden_card_art_lines[3], end="") 
                     sys.stdout.flush(); time.sleep(0.2)

                print("\r" + " " * 60, end="") 
                print(f"\r{COLOR_BLUE}Dealing to {display_name}... Done.{COLOR_RESET}")

                self._deal_card_to_hand(target_hand, update_count_for_this_card=not is_dealer_hidden_card)
                time.sleep(0.1)
        
        print(f"\n{COLOR_BLUE}{'-' * 20}{COLOR_RESET}")


    def _offer_insurance(self):
        """Offers insurance bet to the player if dealer shows an Ace."""
        if not self.dealer.hands[0].cards or len(self.dealer.hands[0].cards) < 2:
             return 0 
        
        dealer_up_card = self.dealer.hands[0].cards[1] 
        
        if dealer_up_card.rank == 'A':
            max_insurance = self.human_player.bets[0] // 2 
            if self.human_player.can_afford_bet(max_insurance) and max_insurance > 0:
                while True:
                    ins_choice = input(f"{COLOR_YELLOW}{self.dealer.name} shows Ace. Insurance? (y/n): {COLOR_RESET}").lower().strip()
                    if ins_choice.startswith('y'):
                        self.human_player.chips -= max_insurance
                        print(f"{COLOR_GREEN}Placed insurance bet of {max_insurance} chips. ({COLOR_RED}-{max_insurance}{COLOR_RESET}){COLOR_RESET}")
                        time.sleep(1)
                        return max_insurance
                    elif ins_choice.startswith('n'):
                        print(f"{COLOR_BLUE}Insurance declined.{COLOR_RESET}"); time.sleep(1)
                        return 0
                    else:
                        print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
            else:
                print(f"{COLOR_DIM}{self.dealer.name} shows Ace, but not enough chips for insurance or insurance is 0.{COLOR_RESET}"); time.sleep(1)
        return 0

    def _resolve_insurance(self, insurance_bet):
        """Resolves the insurance bet."""
        if insurance_bet > 0:
            dealer_hand = self.dealer.hands[0]
            if dealer_hand.cards: 
                 if not self.settings.get("_dealer_hole_card_counted_insurance", False): 
                    self._update_count(dealer_hand.cards[0]) 
                    self.settings["_dealer_hole_card_counted_insurance"] = True


            print(f"\n{COLOR_MAGENTA}--- Resolving Insurance ---{COLOR_RESET}")
            self.display_table(hide_dealer_hole_card=False) # CORRECTED: hide_dealer_hole_card

            if dealer_hand.is_blackjack():
                winnings = insurance_bet * 2 
                total_returned_from_insurance = insurance_bet + winnings 
                print(f"{COLOR_GREEN}{self.dealer.name} has Blackjack! Insurance pays {winnings}. You get {total_returned_from_insurance} chips back from insurance. ({COLOR_GREEN}+{total_returned_from_insurance}{COLOR_RESET}){COLOR_RESET}")
                self.human_player.chips += total_returned_from_insurance
                time.sleep(2.5)
                return True 
            else:
                print(f"{COLOR_RED}{self.dealer.name} does not have Blackjack. Insurance bet lost.{COLOR_RESET}")
                time.sleep(2.5)
                return False 
        return False


    def _offer_even_money(self):
        """Offers even money if player has BJ and dealer shows Ace."""
        player_hand = self.human_player.hands[0]
        if not self.dealer.hands[0].cards or len(self.dealer.hands[0].cards) < 2:
            return False
        dealer_up_card = self.dealer.hands[0].cards[1]

        if player_hand.is_blackjack() and dealer_up_card and dealer_up_card.rank == 'A':
            while True:
                choice = input(f"{COLOR_YELLOW}You have Blackjack, {self.dealer.name} shows Ace. Take Even Money (1:1 payout)? (y/n): {COLOR_RESET}").lower().strip()
                if choice.startswith('y'):
                    payout_amount = self.human_player.bets[0] 
                    print(f"{COLOR_GREEN}Taking Even Money! Guaranteed win of {payout_amount} chips on your bet of {self.human_player.bets[0]}. ({COLOR_GREEN}+{payout_amount}{COLOR_RESET}){COLOR_RESET}")
                    return True 
                elif choice.startswith('n'):
                    print(f"{COLOR_BLUE}Declining Even Money. Playing out the hand...{COLOR_RESET}")
                    return False
                else:
                    print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
        return False


    def get_hand_display_lines(self, player_obj, hand_idx, hide_one_card=False, highlight_active=False, is_ai_poker_mode=False):
        """Generates display lines for a single hand of a player."""
        lines = []
        if hand_idx >= len(player_obj.hands) or hand_idx >= len(player_obj.bets):
            lines.append(f"{COLOR_RED}Error: Invalid hand index for display.{COLOR_RESET}")
            return lines

        hand_obj = player_obj.hands[hand_idx]
        bet_amount = player_obj.bets[hand_idx]
        
        player_name_color = COLOR_MAGENTA 
        display_player_name = player_obj.name 

        if isinstance(player_obj, AIPlayer):
            player_name_color = COLOR_BLUE
        elif player_obj == self.dealer : 
             player_name_color = COLOR_MAGENTA 

        highlight_prefix = f"{COLOR_BOLD}" if highlight_active else ""
        hand_label_str = f" (Hand {hand_idx + 1})" if len(player_obj.hands) > 1 else ""
        bet_info_str = f" | Bet: {bet_amount}" if bet_amount > 0 else ""
        
        ai_type_str = ""
        ai_chip_info_str = ""
        ai_current_bet_str = "" 
        if isinstance(player_obj, AIPlayer):
            ai_type_str = f" ({player_obj.ai_type.value})"
            if is_ai_poker_mode:
                ai_chip_info_str = f" | Chips: {player_obj.chips}"
                if player_obj.current_bet > 0 : 
                     ai_current_bet_str = f" | Betting: {player_obj.current_bet}"


        header = f"{highlight_prefix}{player_name_color}--- {display_player_name}{ai_type_str}{hand_label_str}'s Hand{bet_info_str}{ai_chip_info_str}{ai_current_bet_str} ---{COLOR_RESET}"
        lines.append(header)

        if not hand_obj.cards:
            lines.append("[ No cards ]")
        else:
            card_art_segments = [[] for _ in range(7)] 
            for i, card_obj_in_hand in enumerate(hand_obj.cards):
                is_hidden_for_display = hide_one_card and i == 0
                single_card_lines = card_obj_in_hand.get_display_lines(hidden=is_hidden_for_display)
                for line_num, line_content in enumerate(single_card_lines):
                    card_art_segments[line_num].append(line_content)
            
            for line_idx in range(7):
                lines.append("  ".join(card_art_segments[line_idx]))

        value_line_str = ""
        if not hide_one_card: 
            value = hand_obj.calculate_value()
            status_str = ""
            if hand_obj.is_blackjack(): status_str = f" {COLOR_GREEN}{COLOR_BOLD}BLACKJACK!{COLOR_RESET}"
            elif hand_obj.is_bust(): status_str = f" {COLOR_RED}{COLOR_BOLD}BUST!{COLOR_RESET}"
            value_line_str = f"{COLOR_YELLOW}Value: {value}{status_str}{COLOR_RESET}"
        elif len(hand_obj.cards) > 1: 
            visible_card = hand_obj.cards[1] 
            visible_value = visible_card.value
            if visible_card.rank == 'A': visible_value = 11 
            value_line_str = f"{COLOR_YELLOW}Showing: {visible_value}{COLOR_RESET}"
        elif hide_one_card and hand_obj.cards: 
             value_line_str = f"{COLOR_YELLOW}Showing: ?{COLOR_RESET}"


        if value_line_str:
            lines.append(value_line_str)

        visible_header_width = get_visible_width(header)
        lines.append(f"{player_name_color}-{COLOR_RESET}" * max(1,visible_header_width)) 
        return lines


    def display_table(self, hide_dealer_hole_card=True, current_player_hand_idx=-1):
        """Displays the current state of the table."""
        clear_screen()
        title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ {self.game_mode.value} ~~~{COLOR_RESET}"
        
        player_total_bet = sum(self.human_player.bets)
        count_info_str = ""
        if self.settings['card_counting_cheat']:
            count_info_str = f" | RC: {self.running_count} | TC: {self.true_count:.1f}"

        print(center_text(title, TERMINAL_WIDTH))
        print(center_text(f"{COLOR_YELLOW}Your Chips: {self.human_player.chips} | Your Bet(s): {player_total_bet}{count_info_str}{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")

        dealer_display_lines = self.get_hand_display_lines(self.dealer, 0, hide_one_card=hide_dealer_hole_card)
        for line in dealer_display_lines: print(line)
        print()

        if self.ai_players:
            print(center_text(f"{COLOR_BLUE}--- AI Players ---{COLOR_RESET}", TERMINAL_WIDTH))
            is_poker_mode_for_ai = (self.game_mode == GameMode.POKER_STYLE)
            for ai_p_obj in self.ai_players.values():
                ai_display_lines = self.get_hand_display_lines(ai_p_obj, 0, is_ai_poker_mode=is_poker_mode_for_ai)
                for line in ai_display_lines: print(line)
                print()
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")
        
        if self.human_player.hands and any(h.cards or b > 0 for h,b in zip(self.human_player.hands, self.human_player.bets) ):
            print(center_text(f"{COLOR_MAGENTA}--- Your Hands ---{COLOR_RESET}", TERMINAL_WIDTH))
            for idx, hand_obj in enumerate(self.human_player.hands):
                if hand_obj.cards or (idx < len(self.human_player.bets) and self.human_player.bets[idx] > 0):
                    is_active_hand = (idx == current_player_hand_idx) and (len(self.human_player.hands) > 1)
                    player_hand_lines = self.get_hand_display_lines(self.human_player, idx, highlight_active=is_active_hand)
                    for line in player_hand_lines: print(line)
                    print()
        else:
            print(center_text(f"{COLOR_DIM}[ No player hands active ]{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")


    def _play_one_human_hand(self, hand_index):
        """Handles the player's turn for a single hand. Returns status like 'stand', 'bust', 'surrender', 'error'."""
        if hand_index >= len(self.human_player.hands) or hand_index >= len(self.human_player.bets):
            print(f"{COLOR_RED}Error: Invalid hand index for player ({hand_index}).{COLOR_RESET}"); return 'error'
        
        current_hand = self.human_player.hands[hand_index]
        current_bet = self.human_player.bets[hand_index]
        hand_label = f"Hand {hand_index + 1}" if len(self.human_player.hands) > 1 else "Your Hand"
        
        can_take_initial_action = (len(current_hand.cards) == 2)
        player_stood_on_this_hand = False

        while current_hand.calculate_value() < 21 and not player_stood_on_this_hand:
            self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index)
            
            hint_str = "" 
            actual_hint_text = ""
            hint_prefix = ""

            dealer_up_card_for_hint = None
            if self.dealer.hands[0].cards and len(self.dealer.hands[0].cards) >= 2:
                dealer_up_card_for_hint = self.dealer.hands[0].cards[1]

            if current_hand.cards and dealer_up_card_for_hint:
                is_glados_mode_on = self.settings.get('glados_dealer_mode', False)
                if is_glados_mode_on:
                    hint_prefix = f"{COLOR_MAGENTA}[GLaDOS]: {COLOR_RESET}" 
                    actual_hint_text = get_basic_strategy_hint(current_hand, dealer_up_card_for_hint, is_glados_active=True)
                elif self.settings['easy_mode']:
                    actual_hint_text = get_basic_strategy_hint(current_hand, dealer_up_card_for_hint, is_glados_active=False)
                    if actual_hint_text : 
                         actual_hint_text = f"{COLOR_GREEN}{actual_hint_text}{COLOR_RESET}"


            if actual_hint_text:
                hint_str = f"{hint_prefix}{actual_hint_text}"
            
            count_hint_str = ""
            if self.settings['easy_mode'] and self.settings['card_counting_cheat']: 
                if self.true_count >= 2: count_hint_str = f" {COLOR_GREEN}(High Count: {self.true_count:.1f}){COLOR_RESET}"
                elif self.true_count <= -1: count_hint_str = f" {COLOR_RED}(Low Count: {self.true_count:.1f}){COLOR_RESET}"

            print(f"\n--- Playing {COLOR_MAGENTA}{hand_label}{COLOR_RESET} (Value: {current_hand.calculate_value()}) {hint_str}{count_hint_str} ---")

            options = ["(h)it", "(s)tand"]
            can_double = can_take_initial_action and self.human_player.can_afford_bet(current_bet)
            can_split = (can_take_initial_action and
                         len(current_hand.cards) == 2 and
                         current_hand.cards[0].rank == current_hand.cards[1].rank and
                         self.human_player.can_afford_bet(current_bet) and
                         len(self.human_player.hands) < 4) 
            can_surrender = can_take_initial_action

            if can_double: options.append("(d)ouble down")
            if can_split: options.append("s(p)lit")
            if can_surrender: options.append("su(r)render") 

            prompt = f"{COLOR_YELLOW}Choose action: {', '.join(options)}? {COLOR_RESET}"
            action = input(prompt).lower().strip()

            if action.startswith('h'): 
                new_card = self._deal_card_to_hand(current_hand)
                print(f"\n{COLOR_GREEN}You hit!{COLOR_RESET} Received:"); 
                for line in new_card.get_display_lines(): print(line)
                self._ai_chat("player_action", player_action_details='hit'); time.sleep(1.5)
                can_take_initial_action = False
                if current_hand.is_bust():
                    self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index) 
                    print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS!{COLOR_RESET}")
                    self.session_stats['player_busts'] += 1
                    self._ai_chat("player_bust"); time.sleep(1.5)
                    return 'bust'
            elif action.startswith('s'): 
                print(f"\n{COLOR_BLUE}You stand on {hand_label}.{COLOR_RESET}")
                self._ai_chat("player_action", player_action_details='stand'); time.sleep(1)
                player_stood_on_this_hand = True
            elif action.startswith('d') and can_double: 
                print(f"\n{COLOR_YELLOW}Doubling down on {hand_label}!{COLOR_RESET}")
                self.human_player.chips -= current_bet 
                self.human_player.bets[hand_index] += current_bet 
                print(f"Bet for this hand is now {self.human_player.bets[hand_index]}. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)
                
                new_card = self._deal_card_to_hand(current_hand)
                print(f"{COLOR_BLUE}Received one card:{COLOR_RESET}")
                for line in new_card.get_display_lines(): print(line)
                self._ai_chat("player_action", player_action_details='double'); time.sleep(1.5)
                
                self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index)
                final_value = current_hand.calculate_value()
                if current_hand.is_bust():
                    print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS after doubling down!{COLOR_RESET}")
                    self.session_stats['player_busts'] += 1; self._ai_chat("player_bust")
                    time.sleep(2); return 'double_bust' 
                else:
                    print(f"\n{hand_label} finishes with {final_value} after doubling down.")
                    time.sleep(2); return 'double_stand' 
            elif action.startswith('p') and can_split: 
                print(f"\n{COLOR_YELLOW}Splitting {current_hand.cards[0].rank}s!{COLOR_RESET}")
                self.human_player.chips -= current_bet 
                
                split_card = current_hand.cards.pop(1)
                new_hand_obj = Hand()
                new_hand_obj.add_card(split_card)
                
                self.human_player.hands.insert(hand_index + 1, new_hand_obj)
                self.human_player.bets.insert(hand_index + 1, current_bet)

                print(f"Placed additional {current_bet} bet for the new hand. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)

                print(f"Dealing card to original hand (Hand {hand_index + 1})..."); 
                self._deal_card_to_hand(current_hand); time.sleep(0.5)
                print(f"Dealing card to new hand (Hand {hand_index + 2})..."); 
                self._deal_card_to_hand(new_hand_obj); time.sleep(1)
                
                self._ai_chat("player_action", player_action_details='split')
                self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index) 
                time.sleep(1.5)
                can_take_initial_action = (len(current_hand.cards) == 2)
                if current_hand.cards and current_hand.cards[0].rank == 'A': 
                    print(f"{COLOR_BLUE}Played split Ace for Hand {hand_index + 1}. Standing automatically.{COLOR_RESET}")
                    player_stood_on_this_hand = True 
                continue 
            
            elif action.startswith('r') and can_surrender: 
                print(f"\n{COLOR_YELLOW}Surrendering {hand_label}.{COLOR_RESET}")
                refund = current_bet // 2
                print(f"Half your bet ({refund}) is returned.")
                self.human_player.chips += refund
                self.session_stats['chips_lost'] += (current_bet - refund) 
                self._ai_chat("player_action", player_action_details='surrender')
                time.sleep(2)
                current_hand.cards = [] 
                self.human_player.bets[hand_index] = 0 
                return 'surrender'
            else:
                print(f"{COLOR_RED}Invalid action or action not allowed now.{COLOR_RESET}")
                self._ai_chat("general_insult"); time.sleep(1.5)

            if current_hand.calculate_value() == 21 and not player_stood_on_this_hand:
                if not (len(current_hand.cards) == 2 and can_take_initial_action): 
                    print(f"\n{COLOR_GREEN}{hand_label} has 21! Standing automatically.{COLOR_RESET}"); time.sleep(1.5)
                player_stood_on_this_hand = True
        
        return 'stand' if player_stood_on_this_hand else 'bust'


    def human_player_turn(self):
        """Handles the human player's turn, iterating through all their active hands."""
        current_hand_idx_for_play = 0
        while current_hand_idx_for_play < len(self.human_player.hands):
            if current_hand_idx_for_play >= len(self.human_player.bets):
                break 

            current_playing_hand = self.human_player.hands[current_hand_idx_for_play]
            current_playing_bet = self.human_player.bets[current_hand_idx_for_play]

            if not current_playing_hand.cards and current_playing_bet == 0: 
                current_hand_idx_for_play += 1
                continue

            if current_playing_hand.is_blackjack(): 
                if not (current_playing_hand.cards[0].rank == 'A' and len(self.human_player.hands) > 1 and current_hand_idx_for_play > 0):
                    self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=current_hand_idx_for_play)
                    hand_label = f"Hand {current_hand_idx_for_play + 1}" if len(self.human_player.hands) > 1 else "Your Hand"
                    print(f"\n{COLOR_GREEN}{hand_label} has Blackjack! Standing.{COLOR_RESET}")
                    time.sleep(1.5)
                current_hand_idx_for_play +=1
                continue
            hand_status = self._play_one_human_hand(current_hand_idx_for_play)
            current_hand_idx_for_play += 1
        
        if any(h.cards and not h.is_bust() for h in self.human_player.hands):
            print(f"\n{COLOR_BLUE}Player finishes playing all hands.{COLOR_RESET}"); time.sleep(1.5)


    def ai_turns(self):
        """Handles the turns for all AI players."""
        if not self.ai_players: return

        print(f"\n{COLOR_BLUE}--- AI Players' Turns ---{COLOR_RESET}"); time.sleep(1)
        
        dealer_up_card_obj = self.dealer.hands[0].cards[1] if len(self.dealer.hands[0].cards) >=2 else None
        dealer_up_card_value_for_ai = 0
        if dealer_up_card_obj:
            dealer_up_card_value_for_ai = dealer_up_card_obj.value
            if dealer_up_card_obj.rank == 'A': dealer_up_card_value_for_ai = 11 

        for name, ai_p_obj in list(self.ai_players.items()): 
            if name not in self.ai_players: continue 

            current_ai_hand = ai_p_obj.hands[0] 
            
            if self.game_mode == GameMode.POKER_STYLE and ai_p_obj.current_bet == 0:
                print(f"{COLOR_DIM}{name} did not bet this round.{COLOR_RESET}"); time.sleep(0.5)
                continue

            self.display_table(hide_dealer_hole_card=True) 
            print(f"\n{COLOR_BLUE}{name}'s turn ({ai_p_obj.ai_type.value})...{COLOR_RESET}"); time.sleep(1.5)

            while True: 
                if current_ai_hand.is_bust() or current_ai_hand.calculate_value() == 21:
                    break 

                decision = get_ai_decision(ai_p_obj.ai_type, current_ai_hand.cards, dealer_up_card_value_for_ai, self.running_count, self.true_count)
                
                print(f"{name} ({ai_p_obj.ai_type.value}) decides to {COLOR_YELLOW}{decision}{COLOR_RESET}..."); time.sleep(1.2)

                if decision == "hit":
                    print(f"{name} {COLOR_GREEN}hits{COLOR_RESET}..."); time.sleep(0.8)
                    self._deal_card_to_hand(current_ai_hand) 
                    self.display_table(hide_dealer_hole_card=True) 
                    time.sleep(1.5)
                    if current_ai_hand.is_bust():
                        print(f"\n{COLOR_RED}{COLOR_BOLD}{name} BUSTS!{COLOR_RESET}")
                        self._ai_chat("ai_bust"); time.sleep(1.5)
                        break 
                else: 
                    print(f"{name} {COLOR_BLUE}stands{COLOR_RESET}."); time.sleep(1)
                    break 
            
            if list(self.ai_players.keys())[-1] != name: 
                 print(f"{COLOR_DIM}{'-' * 15}{COLOR_RESET}"); time.sleep(1)


    def dealer_turn(self):
        """Handles the dealer's turn."""
        print(f"\n{COLOR_MAGENTA}--- {self.dealer.name}'s Turn ---{COLOR_RESET}"); time.sleep(1) 
        
        dealer_hand = self.dealer.hands[0]
        
        if len(dealer_hand.cards) == 2 and not self.settings.get("_dealer_hole_card_counted", False) \
           and not self.settings.get("_dealer_hole_card_counted_insurance", False): 
             self._update_count(dealer_hand.cards[0]) 
             self.settings["_dealer_hole_card_counted"] = True 

        self.display_table(hide_dealer_hole_card=False) 

        while dealer_hand.calculate_value() < 17:
            print(f"{COLOR_MAGENTA}{self.dealer.name} must hit...{COLOR_RESET}"); time.sleep(1.5)
            new_card = self._deal_card_to_hand(dealer_hand) 
            print(f"{COLOR_MAGENTA}{self.dealer.name} receives:{COLOR_RESET}")
            for line in new_card.get_display_lines(): print(line)
            time.sleep(1.5)
            self.display_table(hide_dealer_hole_card=False) 
            if dealer_hand.is_bust():
                print(f"\n{COLOR_RED}{COLOR_BOLD}{self.dealer.name} BUSTS!{COLOR_RESET}"); time.sleep(1.5)
                return
        
        dealer_final_value = dealer_hand.calculate_value()
        if not dealer_hand.is_bust(): 
            print(f"{COLOR_MAGENTA}{self.dealer.name} stands with {dealer_final_value}.{COLOR_RESET}")
        time.sleep(2)


    def determine_winner(self, even_money_taken=False):
        """Determines the winner(s) and distributes chips."""
        clear_screen()
        print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Round Results ---{COLOR_RESET}"); time.sleep(1)

        dealer_hand = self.dealer.hands[0]
        dealer_value = dealer_hand.calculate_value()
        is_dealer_blackjack = dealer_hand.is_blackjack()

        print(f"\n{COLOR_BLUE}--- Final Hands ---{COLOR_RESET}")
        for line in self.get_hand_display_lines(self.dealer, 0, hide_one_card=False): print(line)
        print()

        if self.ai_players:
            print(f"{COLOR_BLUE}--- AI Players Final Hands ---{COLOR_RESET}")
            is_poker_mode = (self.game_mode == GameMode.POKER_STYLE)
            for ai_p in self.ai_players.values():
                for line in self.get_hand_display_lines(ai_p, 0, is_ai_poker_mode=is_poker_mode): print(line)
                print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")

        if self.human_player.hands and any(h.cards or b > 0 for h,b in zip(self.human_player.hands, self.human_player.bets)):
            print(f"{COLOR_MAGENTA}--- Your Final Hands ---{COLOR_RESET}")
            for idx, hand_obj in enumerate(self.human_player.hands):
                 if hand_obj.cards or (idx < len(self.human_player.bets) and self.human_player.bets[idx] > 0) :
                    for line in self.get_hand_display_lines(self.human_player, idx): print(line)
                    print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")
        time.sleep(2.5)

        print(f"\n{COLOR_YELLOW}--- Your Hand Results ---{COLOR_RESET}")
        player_won_any_hand_this_round = False

        if even_money_taken: 
            bet_val = self.human_player.bets[0] 
            print(f"{COLOR_GREEN}Your Hand: Took Even Money. Won {bet_val} on your bet of {bet_val}. Total chips received: {bet_val*2}.{COLOR_RESET}")
            player_won_any_hand_this_round = True
        else: 
            for idx, player_h_obj in enumerate(self.human_player.hands):
                if idx >= len(self.human_player.bets): continue 

                if not player_h_obj.cards and self.human_player.bets[idx] == 0 : 
                    continue

                player_val = player_h_obj.calculate_value()
                bet_val = self.human_player.bets[idx]
                hand_label = f"Hand {idx+1}" if len(self.human_player.hands) > 1 else "Your Hand"
                is_player_bj_this_hand = player_h_obj.is_blackjack()
                
                payout = 0 
                result_text = ""
                chips_change_for_stats = 0 

                if player_h_obj.is_bust():
                    result_text = f"{COLOR_RED}{hand_label}: Busted! You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val 
                    self.session_stats['dealer_wins'] += 1
                elif is_player_bj_this_hand and not is_dealer_blackjack:
                    payout = int(bet_val * 1.5) 
                    self.human_player.chips += bet_val + payout 
                    result_text = f"{COLOR_GREEN}{COLOR_BOLD}{hand_label}: BLACKJACK! You win {payout} (pays 3:2). Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    self.session_stats['player_blackjacks'] += 1
                    player_won_any_hand_this_round = True
                elif is_dealer_blackjack and not is_player_bj_this_hand :
                    result_text = f"{COLOR_RED}{hand_label}: {self.dealer.name} has Blackjack! You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val
                    self.session_stats['dealer_wins'] += 1
                elif is_dealer_blackjack and is_player_bj_this_hand: 
                    self.human_player.chips += bet_val 
                    result_text = f"{COLOR_YELLOW}{hand_label}: Push! Both have Blackjack. Bet of {bet_val} returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}"
                    self.session_stats['pushes'] += 1
                elif dealer_hand.is_bust():
                    payout = bet_val 
                    self.human_player.chips += bet_val + payout 
                    result_text = f"{COLOR_GREEN}{hand_label}: {self.dealer.name} busts! You win {payout}. Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    player_won_any_hand_this_round = True
                elif player_val > dealer_value:
                    payout = bet_val
                    self.human_player.chips += bet_val + payout
                    result_text = f"{COLOR_GREEN}{hand_label}: You win! ({player_val} vs {dealer_value}). Win {payout}. Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    player_won_any_hand_this_round = True
                elif player_val == dealer_value:
                    self.human_player.chips += bet_val 
                    result_text = f"{COLOR_YELLOW}{hand_label}: Push! ({player_val}). Bet of {bet_val} returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}"
                    self.session_stats['pushes'] += 1
                else: 
                    result_text = f"{COLOR_RED}{hand_label}: {self.dealer.name} wins ({dealer_value} vs {player_val}). You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val
                    self.session_stats['dealer_wins'] += 1
                
                print(result_text)
                if chips_change_for_stats > 0: self.session_stats['chips_won'] += chips_change_for_stats
                elif chips_change_for_stats < 0: self.session_stats['chips_lost'] += abs(chips_change_for_stats)
                time.sleep(1.5)

        if not even_money_taken:
            if player_won_any_hand_this_round: self._ai_chat("player_win")
            elif all(not h.cards or h.is_bust() for h in self.human_player.hands): pass 
            else: self._ai_chat("taunt") 

        print("-" * 30)
        print(f"{COLOR_YELLOW}Your chip total after round: {self.human_player.chips}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")
        time.sleep(2.5)

        if self.ai_players and self.game_mode == GameMode.POKER_STYLE:
            print(f"\n{COLOR_BLUE}--- AI Player Results ---{COLOR_RESET}")
            for name, ai_p_obj in list(self.ai_players.items()): 
                if name not in self.ai_players: continue 

                ai_hand = ai_p_obj.hands[0]
                ai_bet_val = ai_p_obj.current_bet 
                result_str = ""; result_color = COLOR_RESET; 
                net_chip_change = 0 

                if ai_bet_val > 0: 
                    ai_val = ai_hand.calculate_value()
                    is_ai_bj = ai_hand.is_blackjack()

                    if ai_hand.is_bust():
                        result_str = "Busted!"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val 
                    elif is_ai_bj and not is_dealer_blackjack:
                        result_str = "Blackjack! (Wins 3:2)"; result_color = COLOR_GREEN
                        net_chip_change = int(ai_bet_val * 1.5)
                        ai_p_obj.chips += ai_bet_val + net_chip_change 
                        self._ai_chat("ai_win")
                    elif is_dealer_blackjack and not is_ai_bj:
                        result_str = f"Loses (vs {self.dealer.name} BJ)"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val
                    elif is_dealer_blackjack and is_ai_bj: 
                        result_str = "Push (Both BJ)"; result_color = COLOR_YELLOW
                        ai_p_obj.chips += ai_bet_val 
                        net_chip_change = 0
                    elif dealer_hand.is_bust():
                        result_str = f"Wins ({self.dealer.name} Bust)"; result_color = COLOR_GREEN
                        net_chip_change = ai_bet_val
                        ai_p_obj.chips += ai_bet_val + net_chip_change
                        self._ai_chat("ai_win")
                    elif ai_val > dealer_value:
                        result_str = f"Wins ({ai_val} vs {dealer_value})"; result_color = COLOR_GREEN
                        net_chip_change = ai_bet_val
                        ai_p_obj.chips += ai_bet_val + net_chip_change
                        self._ai_chat("ai_win")
                    elif ai_val == dealer_value:
                        result_str = f"Push ({ai_val})"; result_color = COLOR_YELLOW
                        ai_p_obj.chips += ai_bet_val 
                        net_chip_change = 0
                    else: 
                        result_str = f"Loses ({ai_val} vs {dealer_value})"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val
                    
                    chip_change_color = COLOR_GREEN if net_chip_change > 0 else (COLOR_RED if net_chip_change < 0 else COLOR_YELLOW)
                    chip_change_sign = "+" if net_chip_change > 0 else ""
                    result_str += f" (Bet: {ai_bet_val}, Result: {chip_change_color}{chip_change_sign}{net_chip_change}{COLOR_RESET}) | Chips: {ai_p_obj.chips}"
                    
                    if ai_p_obj.chips <= 0:
                        print(f"{COLOR_RED}{name} ran out of chips and leaves the table!{COLOR_RESET}")
                        del self.ai_players[name]; time.sleep(1)
                        continue 
                else: 
                    result_str = "Did not bet"; result_color = COLOR_DIM 
                
                print(f"{COLOR_BLUE}{name} ({ai_p_obj.ai_type.value}){COLOR_RESET}: {result_color}{result_str}{COLOR_RESET}"); time.sleep(0.6)
            print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")


    def manage_ai_players(self):
        """Manages AI players joining/leaving in relevant game modes."""
        if self.game_mode == GameMode.SOLO: return
        
        print(f"\n{COLOR_YELLOW}Checking table activity...{COLOR_RESET}"); time.sleep(1)
        activity_occurred = False

        for name in list(self.ai_players.keys()):
            leave_chance = 0.25 if len(self.ai_players) >= MAX_AI_PLAYERS else 0.15
            if len(self.ai_players) > MIN_AI_PLAYERS and random.random() < leave_chance:
                if name in self.ai_players: 
                    print(f"{COLOR_RED}{self.ai_players[name].name} has left the table.{COLOR_RESET}")
                    del self.ai_players[name]
                    activity_occurred = True; time.sleep(0.8)
        
        available_spots = MAX_AI_PLAYERS - len(self.ai_players)
        potential_new_ai_names = [n for n in AI_NAMES if n not in self.ai_players] 

        join_chance = 0.4 if len(self.ai_players) < MAX_AI_PLAYERS / 2 else 0.25
        if available_spots > 0 and potential_new_ai_names and random.random() < join_chance:
            num_to_join = random.randint(1, min(available_spots, len(potential_new_ai_names)))
            for _ in range(num_to_join):
                if not potential_new_ai_names: break 
                
                new_ai_name = random.choice(potential_new_ai_names)
                potential_new_ai_names.remove(new_ai_name) 
                
                new_ai_type = random.choice(list(AIType))
                new_ai_chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
                
                self.ai_players[new_ai_name] = AIPlayer(new_ai_name, new_ai_type, new_ai_chips)
                chip_info = f" with {new_ai_chips} chips" if self.game_mode == GameMode.POKER_STYLE else ""
                print(f"{COLOR_GREEN}{new_ai_name} ({new_ai_type.value}) has joined the table{chip_info}!{COLOR_RESET}")
                activity_occurred = True; time.sleep(0.8)

        if not activity_occurred:
            print(f"{COLOR_DIM}The table remains the same.{COLOR_RESET}"); time.sleep(1)


    def play_round(self):
        """Plays a single round of Blackjack. Returns 'game_over', 'quit', or True for continue."""
        clear_screen()
        print(f"{COLOR_MAGENTA}--- Starting New Round ({self.game_mode.value}) ---{COLOR_RESET}")
        self.session_stats['hands_played'] += 1
        self.settings["_dealer_hole_card_counted"] = False 
        self.settings["_dealer_hole_card_counted_insurance"] = False

        if self.settings.get('glados_dealer_mode', False):
            self.dealer.name = "GLaDOS"
        else:
            self.dealer.name = "Dealer"

        if not self.place_bet(): 
            if self.human_player.chips <= 0:
                print(f"\n{COLOR_RED}Out of chips!{COLOR_RESET}"); time.sleep(2)
                return 'game_over'
            else: 
                print(f"{COLOR_YELLOW}Returning to menu...{COLOR_RESET}"); time.sleep(1.5)
                return 'quit'

        self._ai_place_bets() 

        max_potential_cards_needed = (1 + len(self.ai_players) + 1) * 5 + 10 
        if len(self.deck) < max_potential_cards_needed :
            print(f"{COLOR_YELLOW}Deck low, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck()
        else:
            print(f"{COLOR_YELLOW}Preparing next hand...{COLOR_RESET}"); time.sleep(0.7); clear_screen()

        self.deal_initial_cards()
        self.display_table(hide_dealer_hole_card=True)

        insurance_bet_amount = self._offer_insurance()
        
        took_even_money = False
        if self.human_player.hands[0].is_blackjack() and \
           self.dealer.hands[0].cards and len(self.dealer.hands[0].cards) >=2 and \
           self.dealer.hands[0].cards[1].rank == 'A':
            if self._offer_even_money():
                took_even_money = True
                payout = self.human_player.bets[0]
                self.human_player.chips += self.human_player.bets[0] + payout 
                self.session_stats['player_wins'] += 1
                self.session_stats['player_blackjacks'] += 1
                self.session_stats['chips_won'] += payout
                print(f"{COLOR_GREEN}Round over for you due to Even Money.{COLOR_RESET}"); time.sleep(2)
                
                if self.game_mode != GameMode.SOLO: self.ai_turns()
                self.dealer_turn() 
                self.determine_winner(even_money_taken=True) 
                return True 

        dealer_had_blackjack_on_insurance_check = self._resolve_insurance(insurance_bet_amount)

        player_initial_hand = self.human_player.hands[0]
        is_player_initial_blackjack = player_initial_hand.is_blackjack()

        if dealer_had_blackjack_on_insurance_check:
            print(f"{COLOR_RED}{self.dealer.name} Blackjack. Round over for player's main hand unless player also has BJ.{COLOR_RESET}"); time.sleep(2)
            if self.game_mode != GameMode.SOLO: self.ai_turns() 
            self.determine_winner() 
            return True

        if is_player_initial_blackjack and not dealer_had_blackjack_on_insurance_check: 
            print(f"\n{COLOR_GREEN}{COLOR_BOLD}Blackjack!{COLOR_RESET}"); time.sleep(1.5)
            if self.game_mode != GameMode.SOLO: self.ai_turns()
            self.dealer_turn()
            self.determine_winner()
            return True
        
        if not is_player_initial_blackjack and not dealer_had_blackjack_on_insurance_check:
            self.human_player_turn() 

            player_all_hands_busted_or_surrendered = all(
                not hand.cards or hand.is_bust() for hand in self.human_player.hands
            )

            if not player_all_hands_busted_or_surrendered:
                if self.game_mode != GameMode.SOLO: self.ai_turns()
                self.dealer_turn()
            else: 
                print(f"\n{COLOR_RED}All your hands busted or surrendered!{COLOR_RESET}")
                if any(ai_p.current_bet > 0 for ai_p in self.ai_players.values()) or self.game_mode != GameMode.SOLO:
                    print(f"{COLOR_DIM}{self.dealer.name} plays for AI / card counting...{COLOR_RESET}")
                    self.dealer_turn()
                else: 
                    print(f"\n{COLOR_MAGENTA}--- {self.dealer.name} reveals ---{COLOR_RESET}"); time.sleep(1)
                    if len(self.dealer.hands[0].cards) == 2 and \
                       not self.settings.get("_dealer_hole_card_counted", False) and \
                       not self.settings.get("_dealer_hole_card_counted_insurance", False):
                         self._update_count(self.dealer.hands[0].cards[0])
                         self.settings["_dealer_hole_card_counted"] = True
                    self.display_table(hide_dealer_hole_card=False); time.sleep(1.5)
        
        self.determine_winner()

        if self.human_player.chips <= 0:
            print(f"\n{COLOR_RED}You've run out of chips! Game Over.{COLOR_RESET}"); time.sleep(2.5)
            return 'game_over'
        
        self.manage_ai_players() 
        return True


    def run_game(self):
        """Runs the main game loop for playing rounds."""
        while True:
            round_status = self.play_round()
            if round_status == 'game_over':
                print(f"{COLOR_YELLOW}Returning to main menu...{COLOR_RESET}"); time.sleep(2)
                break 
            elif round_status == 'quit': 
                break
            elif round_status is True: 
                print(f"\n{COLOR_YELLOW}Your current chips: {self.human_player.chips}{COLOR_RESET}")
                if self.game_mode != GameMode.SOLO and not self.ai_players:
                    print(f"{COLOR_YELLOW}All AI players have left or busted out!{COLOR_RESET}")
                    input("Press Enter to return to menu..."); break
                
                next_round_choice = input(f"Press Enter for next round, or 'q' to return to menu... ").lower()
                if next_round_choice == 'q':
                    break
            else: 
                print(f"{COLOR_RED}Unexpected round result: {round_status}. Returning to menu.{COLOR_RESET}"); break
        clear_screen()


    def save_game(self):
        """Saves the current game state to a file."""
        ai_players_serializable = {}
        for name, ai_obj in self.ai_players.items():
            ai_players_serializable[name] = {
                'type': ai_obj.ai_type.name, 
                'chips': ai_obj.chips
            }
        
        state = {
            "player_chips": self.human_player.chips,
            "ai_players": ai_players_serializable, 
            "session_stats": self.session_stats,
            "game_mode": self.game_mode.name, 
            "settings": self.settings,
        }
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
            print(f"{COLOR_GREEN}Game saved successfully to {SAVE_FILE}{COLOR_RESET}")
        except IOError as e:
            print(f"{COLOR_RED}Error saving game: {e}{COLOR_RESET}")
        time.sleep(1.5)

    def load_game(self):
        """Loads game state from a file. Returns True if successful, False otherwise."""
        try:
            if not os.path.exists(SAVE_FILE):
                print(f"{COLOR_YELLOW}No save file found ({SAVE_FILE}).{COLOR_RESET}"); time.sleep(1.5)
                return False
            
            with open(SAVE_FILE, 'r') as f:
                state = json.load(f)

            self.human_player.chips = state.get("player_chips", 100)
            
            loaded_ai_data = state.get("ai_players", {})
            self.ai_players = {} 
            for name, data in loaded_ai_data.items():
                try:
                    ai_type_enum = AIType[data.get('type', 'BASIC')]
                except KeyError:
                    ai_type_enum = AIType.BASIC
                    print(f"{COLOR_RED}Warning: Invalid AI type '{data.get('type')}' for {name}. Defaulting.{COLOR_RESET}")
                self.ai_players[name] = AIPlayer(name, ai_type_enum, data.get('chips', AI_STARTING_CHIPS))

            self.session_stats = state.get("session_stats", BlackjackGame._default_stats())
            
            try:
                self.game_mode = GameMode[state.get("game_mode", "QUICK_PLAY")]
            except KeyError:
                print(f"{COLOR_RED}Warning: Invalid game mode '{state.get('game_mode')}' loaded. Defaulting.{COLOR_RESET}")
                self.game_mode = GameMode.QUICK_PLAY
            
            self.settings = state.get("settings", BlackjackGame._default_settings())
            
            if self.settings.get('glados_dealer_mode', False):
                self.dealer.name = "GLaDOS"
            else:
                self.dealer.name = "Dealer"

            self._create_and_shuffle_deck() 
            
            print(f"{COLOR_GREEN}Game loaded successfully from {SAVE_FILE}{COLOR_RESET}")
            print(f"Loaded Mode: {self.game_mode.value}, Player Chips: {self.human_player.chips}")
            time.sleep(2)
            return True
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print(f"{COLOR_RED}Error loading game: {e}{COLOR_RESET}")
            time.sleep(1.5)
            return False


# --- Main Application Logic ---
def main():
    """Main function to run the application."""
    global TERMINAL_WIDTH
    try:
        TERMINAL_WIDTH = os.get_terminal_size().columns
    except OSError:
        print(f"{COLOR_YELLOW}Could not detect terminal size. Using default width: {DEFAULT_TERMINAL_WIDTH}{COLOR_RESET}")
        TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH
        time.sleep(1.5)

    game_instance = None
    current_settings = BlackjackGame._default_settings() 
    current_stats = BlackjackGame._default_stats()

    title_screen()
    while True:
        stats_to_show = game_instance.session_stats if game_instance else current_stats
        settings_for_menu_display = current_settings 
        if game_instance and game_instance.settings: 
             pass 

        choice = display_menu()
        selected_game_mode_enum = None

        if choice == '1': selected_game_mode_enum = GameMode.QUICK_PLAY
        elif choice == '2': selected_game_mode_enum = GameMode.SOLO
        elif choice == '3': selected_game_mode_enum = GameMode.POKER_STYLE
        elif choice == '4': display_rules(); continue
        elif choice == '5':
            display_settings_menu(current_settings) 
            if game_instance:
                game_instance.settings['glados_dealer_mode'] = current_settings.get('glados_dealer_mode', False)
                if game_instance.settings.get('glados_dealer_mode', False):
                    game_instance.dealer.name = "GLaDOS"
                else:
                    game_instance.dealer.name = "Dealer"
            continue
        elif choice == '6': display_stats(stats_to_show); continue
        elif choice == '7': 
            if game_instance:
                game_instance.save_game()
            else:
                print(f"{COLOR_YELLOW}No active game to save.{COLOR_RESET}"); time.sleep(1)
            continue
        elif choice == '8': 
            temp_game = BlackjackGame(settings=current_settings, stats=current_stats) 
            if temp_game.load_game(): 
                game_instance = temp_game 
                current_settings = game_instance.settings 
                current_stats = game_instance.session_stats 
                print(f"{COLOR_GREEN}Starting loaded game...{COLOR_RESET}"); time.sleep(1)
                game_instance.run_game()
                current_stats = game_instance.session_stats 
            continue
        elif choice == '9': 
            print(f"\n{COLOR_MAGENTA}Thanks for playing Python Blackjack! (Refactored){COLOR_RESET}"); break

        if selected_game_mode_enum:
            print(f"\n{COLOR_YELLOW}Starting {selected_game_mode_enum.value}...{COLOR_RESET}"); time.sleep(1)
            current_stats = BlackjackGame._default_stats() 
            
            game_instance = BlackjackGame(game_mode=selected_game_mode_enum, 
                                          settings=current_settings, 
                                          stats=current_stats)
            
            game_instance.run_game()
            current_stats = game_instance.session_stats 

    print(COLOR_RESET) 

# --- Start Game ---
if __name__ == "__main__":
    can_use_color = sys.stdout.isatty()
    if os.name == 'nt': 
        os.system('') 
    
    if not can_use_color:
        print("Running without color support (or cannot detect). ANSI codes will be visible.")
    
    main()
import random
import time
import os
import sys
import enum
import json
import re

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
SUITS_DATA = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
RANKS_DATA = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES_DATA = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
AI_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ivan", "Judy", "Kevin", "Laura"]
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 5
CARD_BACK_CHAR = "░"
AI_STARTING_CHIPS = 100
AI_DEFAULT_BET = 5
SAVE_FILE = "blackjack_save.json"
DEFAULT_TERMINAL_WIDTH = 80

# --- Global Variable for Terminal Width ---
TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH

# --- Enums ---
class GameMode(enum.Enum):
    QUICK_PLAY = "Quick Play (vs AI)"
    SOLO = "Solo Play (vs Dealer)"
    POKER_STYLE = "Poker Style (vs AI with Chips)"

class AIType(enum.Enum):
    BASIC = "Basic Strategy"
    CONSERVATIVE = "Conservative"
    AGGRESSIVE = "Aggressive"
    RANDOM = "Random"
    COUNTER = "Card Counter Lite"

# --- AI Chat Lines ---
AI_CHAT = {
    "hit_good": ["Nice hit!", "Good card!", "Looking sharp.", "Calculated risk.", "That's the spirit!", "Keep 'em coming!", "Bold move paying off."],
    "hit_bad": ["Oof, tough luck.", "That didn't help much.", "Getting close...", "Risky!", "Careful now...", "Hmm, not ideal.", "Pushing your luck?"],
    "stand_good": ["Smart stand.", "Good call.", "Solid play.", "Playing it safe.", "Wise decision.", "Holding strong.", "I respect that."],
    "stand_bad": ["Standing on that? Bold.", "Feeling brave?", "Hope that holds up!", "Interesting strategy...", "Are you sure about that?", "Dealer might like that.", "Living dangerously!"],
    "player_bust": ["Busted! Too greedy?", "Ouch, over 21!", "Better luck next time!", "Happens to the best of us.", "Too many!", "The house always wins... sometimes.", "Greed is a killer."],
    "player_win": ["Congrats!", "You got lucky!", "Nice hand!", "Well played!", "Beginner's luck holds!", "Impressive.", "You earned that one."],
    "player_blackjack": ["Blackjack! Wow!", "Can't beat that!", "Beginner's luck?", "Natural 21! Sweet!", "Right off the deal!", "Impossible!"],
    "ai_win": ["Winner!", "Gotcha!", "Too easy.", "Read 'em and weep!", "My turn!", "Dealer's loss is my gain.", "That's how it's done!", "Chip stack growing!", "Victory!"],
    "ai_bust": ["Darn!", "Too many!", "Argh, busted!", "Miscalculated!", "Pushed my luck.", "Blast!", "Overcooked it.", "My bad."],
    "taunt": ["My chips are piling up!", "Feeling confident?", "Easy money!", "You can't beat me!", "Is that all you've got?", "Think you can win?", "Dealer looks weak...", "I could do this all day.", "Getting predictable?", "Maybe try a different strategy?", "I'm just getting started."],
    "general_insult": ["Are you even trying?", "My grandma plays better than that.", "Was that intentional?", "Seriously?", "...", "Did you forget the rules?", "That was... a choice.", "Were you aiming for 21 or 31?", "Painful to watch.", "Just give me your chips already."]
}

# --- Core Game Classes ---
class Card:
    """Represents a single playing card."""
    def __init__(self, suit_name, rank):
        self.suit_name = suit_name
        self.suit_symbol = SUITS_DATA[suit_name]
        self.rank = rank
        self.value = VALUES_DATA[rank]
        self.color = COLOR_RED if suit_name in ['Hearts', 'Diamonds'] else COLOR_BLACK

    def __str__(self):
        return f"{self.rank}{self.suit_symbol}"

    def get_display_lines(self, hidden=False):
        """Returns the ASCII art lines for displaying the card."""
        if hidden:
            back = CARD_BACK_CHAR * 9
            lines = ["┌─────────┐", f"│{back}│", f"│{back}│", f"│{COLOR_DIM} HIDDEN {COLOR_RESET}{COLOR_WHITE_BG}{COLOR_BLACK}│", f"│{back}│", f"│{back}│", "└─────────┘"]
            return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

        rank_str = self.rank.ljust(2)
        lines = [
            "┌─────────┐",
            f"│{self.color}{rank_str}{COLOR_BLACK}       │",
            f"│ {self.color}{self.suit_symbol}{COLOR_BLACK}       │",
            f"│    {self.color}{self.suit_symbol}{COLOR_BLACK}    │",
            f"│       {self.color}{self.suit_symbol}{COLOR_BLACK} │",
            f"│       {self.color}{rank_str}{COLOR_BLACK}│",
            "└─────────┘"
        ]
        return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

class Hand:
    """Represents a hand of cards for a player or dealer."""
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def calculate_value(self):
        if not self.cards:
            return 0
        value = 0
        num_aces = 0
        for card in self.cards:
            value += card.value
            if card.rank == 'A':
                num_aces += 1
        while value > 21 and num_aces:
            value -= 10
            num_aces -= 1
        return value

    def is_blackjack(self):
        return len(self.cards) == 2 and self.calculate_value() == 21

    def is_bust(self):
        return self.calculate_value() > 21

    def __str__(self):
        return ", ".join(str(card) for card in self.cards) if self.cards else "[No cards]"


class Deck:
    """Represents one or more decks of playing cards."""
    def __init__(self, num_decks=1):
        self.cards = []
        self.num_decks = num_decks
        self._create_deck()
        self.shuffle()
        print(f"{COLOR_DIM}(Using {num_decks} deck{'s' if num_decks > 1 else ''}){COLOR_RESET}")
        time.sleep(0.5)

    def _create_deck(self):
        self.cards = []
        for _ in range(self.num_decks):
            for suit_name in SUITS_DATA:
                for rank in RANKS_DATA:
                    self.cards.append(Card(suit_name, rank))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if not self.cards:
            return None 
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)

# --- Player Classes ---
class Player:
    """Represents a generic player (human or dealer)."""
    def __init__(self, name, chips=0):
        self.name = name
        self.hands = [Hand()] 
        self.chips = chips
        self.bets = [0] 

    def reset_hands(self):
        self.hands = [Hand()]
        self.bets = [0]

    def can_afford_bet(self, amount):
        return self.chips >= amount

class AIPlayer(Player):
    """Represents an AI player."""
    def __init__(self, name, ai_type, chips=AI_STARTING_CHIPS):
        super().__init__(name, chips)
        self.ai_type = ai_type
        self.current_bet = 0 

    def reset_for_round(self):
        """Resets hands for a new round. Bet is handled by betting logic."""
        super().reset_hands()

    def get_decision(self, dealer_up_card_value, running_count=0, true_count=0):
        """Gets the AI's decision based on its type and game state."""
        active_hand = self.hands[0] 
        return get_ai_decision(self.ai_type, active_hand.cards, dealer_up_card_value, running_count, true_count)


# --- Helper Functions (UI and Global Logic) ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.03, color=COLOR_RESET, newline=True):
    """Prints text with a typing effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(COLOR_RESET)
    if newline:
        print()

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
    if padding < 0:
        padding = 0
    return " " * padding + text

def shuffle_animation(duration=1.5):
    """Displays a visual shuffling animation."""
    clear_screen()
    print(f"{COLOR_YELLOW}Shuffling Deck...{COLOR_RESET}")
    symbols = ['♠', '♥', '♦', '♣', CARD_BACK_CHAR, '?']
    colors = [COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN]
    width = 40
    lines = 5
    end_time = time.time() + duration
    while time.time() < end_time:
        output_lines = []
        for _ in range(lines):
            line_chars = []
            for _ in range(width):
                if random.random() < 0.3:
                    line_chars.append(f"{random.choice(colors)}{random.choice(symbols)}{COLOR_RESET}")
                else:
                    line_chars.append(" ")
            output_lines.append("".join(line_chars))
        
        sys.stdout.write(f"\033[{lines}A") 
        for line_content in output_lines:
            sys.stdout.write(f"\r{line_content.ljust(width)}\n") 
        sys.stdout.flush()
        time.sleep(0.05)
    clear_screen()
    print(f"{COLOR_GREEN}Deck Shuffled!{COLOR_RESET}")
    time.sleep(0.5)

def title_screen():
    """Displays a simplified, animated title screen."""
    clear_screen()
    title = "B L A C K J A C K"
    author = "Created by ShadowHarvy (Refactored)"
    card_width = 11 
    screen_width = TERMINAL_WIDTH

    print("\n" * 5)
    typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_GREEN + COLOR_BOLD)
    print("\n")
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width))
    time.sleep(0.5)

    temp_deck_cards = []
    for suit_name in SUITS_DATA:
        for rank_val in RANKS_DATA:
            temp_deck_cards.append(Card(suit_name, rank_val))
    random.shuffle(temp_deck_cards)

    dealt_card1_obj = temp_deck_cards.pop() if temp_deck_cards else Card('Spades', 'A')
    dealt_card2_obj = temp_deck_cards.pop() if temp_deck_cards else Card('Hearts', 'K')

    card1_lines = dealt_card1_obj.get_display_lines()
    card2_lines = dealt_card2_obj.get_display_lines()

    total_card_width_display = card_width * 2 + 2  
    left_padding = (screen_width - total_card_width_display) // 2
    if left_padding < 0: left_padding = 0
    padding_str = " " * left_padding
    
    num_card_art_lines = len(card1_lines) 
    
    clear_screen()
    print("\n" * 5) 
    print(center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width))
    print() 
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width))
    print() 
    
    for i in range(num_card_art_lines):
        line_output = f"{padding_str}{card1_lines[i]}"
        print(line_output)
    time.sleep(0.7)

    clear_screen()
    print("\n" * 5)
    print(center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width))
    print()
    print()
    for i in range(num_card_art_lines):
        line_output = f"{padding_str}{card1_lines[i]}  {card2_lines[i]}"
        print(line_output)
    
    print() 
    print(center_text(f"{COLOR_CYAN}{author}{COLOR_RESET}", screen_width))
    print("\n") 
    time.sleep(2)


def display_menu():
    """Displays the main menu and gets user choice."""
    print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Main Menu ---{COLOR_RESET}")
    print(f"[{COLOR_CYAN}1{COLOR_RESET}] {GameMode.QUICK_PLAY.value}")
    print(f"[{COLOR_CYAN}2{COLOR_RESET}] {GameMode.SOLO.value}")
    print(f"[{COLOR_CYAN}3{COLOR_RESET}] {GameMode.POKER_STYLE.value}")
    print(f"[{COLOR_CYAN}4{COLOR_RESET}] View Rules")
    print(f"[{COLOR_CYAN}5{COLOR_RESET}] Settings")
    print(f"[{COLOR_CYAN}6{COLOR_RESET}] View Stats")
    print(f"[{COLOR_CYAN}7{COLOR_RESET}] Save Game")
    print(f"[{COLOR_CYAN}8{COLOR_RESET}] Load Game")
    print(f"[{COLOR_CYAN}9{COLOR_RESET}] Quit")
    print("-" * 30)
    while True:
        choice = input(f"{COLOR_YELLOW}Enter your choice (1-9): {COLOR_RESET}")
        if choice in [str(i) for i in range(1, 10)]:
            return choice
        else:
            print(f"{COLOR_RED}Invalid choice. Please enter 1-9.{COLOR_RESET}")

def display_rules():
    """Displays the basic rules of the game."""
    clear_screen()
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Blackjack Rules ---{COLOR_RESET}")
    rules = [
        "- Goal: Get closer to 21 than the dealer without going over.",
        "- Card Values: 2-10 face value, J/Q/K = 10, Ace = 1 or 11.",
        "- Blackjack: Ace + 10-value card on first two cards (pays 3:2).",
        "- Hit: Take another card.",
        "- Stand: Keep current hand.",
        "- Double Down: Double bet, take one more card, then stand (first 2 cards only).",
        "- Split: If first two cards match rank, double bet to play two separate hands.",
        "- Insurance: If dealer shows Ace, bet up to half original bet that dealer has BJ (pays 2:1).",
        "- Surrender: Forfeit half your bet and end hand immediately (first action only).",
        "- Even Money: If you have BJ and dealer shows Ace, take guaranteed 1:1 payout.",
        "- Bust: Hand value over 21 (lose).",
        "- Push: Tie with dealer (bet returned).",
        "- Dealer Rules: Hits until 17 or more."
    ]
    for rule in rules:
        print(f"{COLOR_BLUE} {rule}{COLOR_RESET}")
        time.sleep(0.1)
    print("-" * 25)
    input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}")
    clear_screen()

def display_settings_menu(settings):
    """Displays settings and allows changes."""
    while True:
        clear_screen()
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Settings ---{COLOR_RESET}")
        print(f"[1] Number of Decks: {COLOR_CYAN}{settings['num_decks']}{COLOR_RESET} (1-8)")
        print(f"[2] Easy Mode (Hints): {COLOR_GREEN if settings['easy_mode'] else COLOR_RED}{settings['easy_mode']}{COLOR_RESET}")
        print(f"[3] Card Counting Cheat: {COLOR_GREEN if settings['card_counting_cheat'] else COLOR_RED}{settings['card_counting_cheat']}{COLOR_RESET}")
        print(f"[4] European Rules: {COLOR_GREEN if settings.get('european_rules', False) else COLOR_RED}{settings.get('european_rules', False)}{COLOR_RESET}")
        print(f"[5] GLaDOS Dealer Mode: {COLOR_MAGENTA if settings.get('glados_dealer_mode', False) else COLOR_RED}{settings.get('glados_dealer_mode', False)}{COLOR_RESET}")
        print("[6] Back to Main Menu") 
        print("-" * 30)
        choice = input(f"{COLOR_YELLOW}Choose setting to change (1-6): {COLOR_RESET}")

        if choice == '1':
            while True:
                try:
                    num = int(input(f"{COLOR_YELLOW}Enter number of decks (1-8): {COLOR_RESET}"))
                    if 1 <= num <= 8:
                        settings['num_decks'] = num
                        break
                    else:
                        print(f"{COLOR_RED}Invalid number. Please enter 1-8.{COLOR_RESET}")
                except ValueError:
                    print(f"{COLOR_RED}Invalid input. Please enter a number.{COLOR_RESET}")
        elif choice == '2':
            settings['easy_mode'] = not settings['easy_mode']
            print(f"{COLOR_BLUE}Easy Mode set to: {settings['easy_mode']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '3':
            settings['card_counting_cheat'] = not settings['card_counting_cheat']
            print(f"{COLOR_BLUE}Card Counting Cheat set to: {settings['card_counting_cheat']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '4':
            settings['european_rules'] = not settings.get('european_rules', False)
            print(f"{COLOR_BLUE}European Rules set to: {settings['european_rules']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '5': 
            settings['glados_dealer_mode'] = not settings.get('glados_dealer_mode', False)
            glados_status = "ACTIVATED" if settings['glados_dealer_mode'] else "DEACTIVATED"
            print(f"{COLOR_MAGENTA}GLaDOS Dealer Mode: {glados_status}{COLOR_RESET}"); time.sleep(1)
        elif choice == '6': 
            break
        else:
            print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}"); time.sleep(1)

def display_stats(stats):
    """Displays session statistics."""
    clear_screen()
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Session Statistics ---{COLOR_RESET}")
    print(f"Hands Played: {COLOR_CYAN}{stats['hands_played']}{COLOR_RESET}")
    print(f"Player Wins: {COLOR_GREEN}{stats['player_wins']}{COLOR_RESET}")
    print(f"Dealer Wins: {COLOR_RED}{stats['dealer_wins']}{COLOR_RESET}")
    print(f"Pushes: {COLOR_YELLOW}{stats['pushes']}{COLOR_RESET}")
    print(f"Player Blackjacks: {COLOR_GREEN}{stats['player_blackjacks']}{COLOR_RESET}")
    print(f"Player Busts: {COLOR_RED}{stats['player_busts']}{COLOR_RESET}")
    net_chips = stats['chips_won'] - stats['chips_lost']
    chip_color = COLOR_GREEN if net_chips >= 0 else COLOR_RED
    print(f"Net Chips: {chip_color}{net_chips:+}{COLOR_RESET}") 
    print("-" * 30)
    input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}")
    clear_screen()

# --- AI Player Logic ---
def get_ai_decision(ai_type, hand_cards, dealer_up_card_value, running_count=0, true_count=0):
    """Selects the appropriate AI decision function based on type and count."""
    temp_hand_tuples = [(card.suit_name, card.suit_symbol, card.rank) for card in hand_cards]

    if ai_type == AIType.COUNTER:
        return ai_decision_counter(temp_hand_tuples, dealer_up_card_value, true_count)
    elif ai_type == AIType.BASIC:
        return ai_decision_basic(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.CONSERVATIVE:
        return ai_decision_conservative(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.AGGRESSIVE:
        return ai_decision_aggressive(temp_hand_tuples, dealer_up_card_value)
    elif ai_type == AIType.RANDOM:
        return random.choice(["hit", "stand"])
    else:
        print(f"{COLOR_RED}Warning: Unknown AI type {ai_type}. Defaulting to Basic.{COLOR_RESET}")
        return ai_decision_basic(temp_hand_tuples, dealer_up_card_value)

def _calculate_hand_value_for_ai(hand_tuples): 
    """Calculates hand value from card tuples for AI logic."""
    if not hand_tuples: return 0
    value = 0
    num_aces = 0
    for card_tuple in hand_tuples:
        if len(card_tuple) < 3: continue
        rank = card_tuple[2]
        value += VALUES_DATA.get(rank, 0)
        if rank == 'A': num_aces += 1
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

def ai_decision_basic(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21


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

def ai_decision_conservative(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21

    if hand_value < 11: return "hit"
    if is_soft:
        return "stand" if hand_value >= 18 else "hit"
    else: 
        if hand_value >= 15: return "stand"
        if hand_value >= 12 and dealer_up_card_value <= 6: return "stand"
        return "hit"

def ai_decision_aggressive(hand_tuples, dealer_up_card_value):
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    num_aces = sum(1 for _, _, rank_val in hand_tuples if rank_val == 'A')
    is_soft = num_aces > 0 and (hand_value - 10 * num_aces) + 11 * num_aces <= 21 and hand_value <= 21
    
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

def ai_decision_counter(hand_tuples, dealer_up_card_value, true_count):
    decision = ai_decision_basic(hand_tuples, dealer_up_card_value) 
    hand_value = _calculate_hand_value_for_ai(hand_tuples)
    if true_count >= 2: 
        if decision == "stand" and hand_value in [15, 16] and dealer_up_card_value >= 7:
            decision = "hit"
    elif true_count <= -1: 
        if decision == "hit" and hand_value == 12 and dealer_up_card_value <= 6:
            decision = "stand"
        elif decision == "hit" and hand_value == 13 and dealer_up_card_value <= 3:
            decision = "stand"
    return decision

# --- Card Counting Logic ---
def get_card_count_value(card_rank):
    """Gets the Hi-Lo count value for a card rank."""
    if card_rank in ['2', '3', '4', '5', '6']: return 1
    elif card_rank in ['10', 'J', 'Q', 'K', 'A']: return -1
    else: return 0

# --- Basic Strategy Hint ---
def get_basic_strategy_hint(player_hand_obj, dealer_up_card_obj, is_glados_active=False):
    """
    Provides a basic strategy hint.
    If is_glados_active is True, hints are phrased with GLaDOS's personality.
    """
    player_value = player_hand_obj.calculate_value()
    dealer_value = 0
    if dealer_up_card_obj:
        dealer_value = dealer_up_card_obj.value
        if dealer_up_card_obj.rank == 'A': dealer_value = 11 

    num_aces = sum(1 for card in player_hand_obj.cards if card.rank == 'A')
    is_soft = False
    if num_aces > 0:
        value_with_ace_as_11 = (player_value - num_aces) + 11 + (num_aces - 1)
        if value_with_ace_as_11 <= 21:
            is_soft = True

    if is_glados_active:
        if len(player_hand_obj.cards) == 2 and player_hand_obj.cards[0].rank == player_hand_obj.cards[1].rank:
            rank = player_hand_obj.cards[0].rank
            if rank == 'A' or rank == '8': return "Aces and Eights. The 'optimal' play is to split. Try not to disappoint me further."
            if rank == '5' or rank == '10': return "Splitting Fives or Tens? An... 'innovative' approach to failure. I'd advise against it, for the sake of my circuits."
            return f"Splitting {rank}s, are we? A bold strategy, subject. Let's see how this 'test' pans out."


        if is_soft:
            if player_value >= 19: return "A soft 19 or higher. Even you should be able to figure out that standing is the 'correct' test procedure here."
            if player_value == 18:
                return "Soft 18. Against my 2 through 8, perhaps you should stand. Against a 9, 10, or Ace? You might as well hit. It's not like it matters much for your... 'progress'." if dealer_value != 0 else "Soft 18. Make a decision. It's probably wrong anyway."
            if player_value <= 17: return "Soft 17 or less? The data suggests hitting. Try not to make it too painful to watch."
        else: 
            if player_value >= 17: return "A hard 17 or more. Standing is the statistically probable, yet ultimately futile, action."
            if player_value >= 13: 
                return f"With a hard {player_value}... if my card is a 2 through 6, you might stand. If it's 7 or higher, hitting is your 'best' chance. Good luck with that." if dealer_value != 0 else f"A hard {player_value}. Fascinating. Choose wisely. Or don't."
            if player_value == 12:
                return "A hard 12. If I'm showing a 4, 5, or 6, standing is... acceptable. Otherwise, you'll probably want to hit. Not that it will save you." if dealer_value != 0 else "Hard 12. This should be interesting. Or, more likely, predictable."
            if player_value <= 11: return "Eleven or less? Hitting is an option. Doubling down, if you're feeling particularly reckless, is another. The choice is yours. To fail."
        
        return "My calculations are beyond your comprehension. Just make a choice, subject." 

    else:
        if len(player_hand_obj.cards) == 2 and player_hand_obj.cards[0].rank == player_hand_obj.cards[1].rank:
            rank = player_hand_obj.cards[0].rank
            if rank == 'A' or rank == '8': return "(Hint: Always split Aces and 8s)"
            if rank == '5' or rank == '10': return "(Hint: Never split 5s or 10s)"

        if is_soft:
            if player_value >= 19: return "(Hint: Stand on soft 19+)"
            if player_value == 18:
                return "(Hint: Stand vs 2-8, Hit vs 9-A)" if dealer_value != 0 else "(Hint: Stand on soft 18)"
            if player_value <= 17: return "(Hint: Hit soft 17 or less)"
        else: 
            if player_value >= 17: return "(Hint: Stand on hard 17+)"
            if player_value >= 13: 
                return "(Hint: Stand vs 2-6, Hit vs 7+)" if dealer_value != 0 else "(Hint: Stand on 13-16)"
            if player_value == 12:
                return "(Hint: Stand vs 4-6, Hit vs 2,3,7+)" if dealer_value != 0 else "(Hint: Hit hard 12)"
            if player_value <= 11: return "(Hint: Hit or Double Down on 11 or less)"

        return "(Hint: Use Basic Strategy Chart)"


# --- Game Class ---
class BlackjackGame:
    def __init__(self, game_mode=GameMode.QUICK_PLAY, settings=None, stats=None):
        self.game_mode = game_mode
        self.settings = settings if settings is not None else BlackjackGame._default_settings()
        self.session_stats = stats if stats is not None else BlackjackGame._default_stats()
        
        self.deck = Deck(self.settings['num_decks'])
        self.dealer = Player("Dealer") 
        if self.settings.get('glados_dealer_mode', False):
            self.dealer.name = "GLaDOS"

        self.human_player = Player("Player (You)", chips=100) 
        self.ai_players = {} 

        self.running_count = 0
        self.true_count = 0
        self.decks_remaining_estimate = self.settings['num_decks']
        
        self._initialize_ai_players() 

    @staticmethod
    def _default_settings():
        return {'num_decks': 1, 'easy_mode': False, 'card_counting_cheat': False, 
                'european_rules': False, 'glados_dealer_mode': False} 

    @staticmethod
    def _default_stats():
        return {'hands_played': 0, 'player_wins': 0, 'dealer_wins': 0, 'pushes': 0,
                'player_blackjacks': 0, 'player_busts': 0, 'chips_won': 0, 'chips_lost': 0}

    def _create_and_shuffle_deck(self):
        """Re-initializes and shuffles the deck."""
        self.deck = Deck(self.settings['num_decks']) 
        self.running_count = 0
        self.true_count = 0
        self.decks_remaining_estimate = self.settings['num_decks']


    def _update_count(self, card): 
        """Updates the running and true count."""
        if card: 
            self.running_count += get_card_count_value(card.rank)
            self.decks_remaining_estimate = max(0.5, len(self.deck) / 52.0) 
            self.true_count = self.running_count / self.decks_remaining_estimate if self.decks_remaining_estimate > 0 else self.running_count


    def _initialize_ai_players(self):
        """Sets up AIPlayer objects based on game mode."""
        self.ai_players = {}
        if self.game_mode == GameMode.SOLO:
            return
        
        num_ai = random.randint(MIN_AI_PLAYERS, MAX_AI_PLAYERS)
        available_names = random.sample(AI_NAMES, k=min(len(AI_NAMES), num_ai))
        
        for name in available_names:
            ai_type_enum = random.choice(list(AIType))
            chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
            self.ai_players[name] = AIPlayer(name, ai_type_enum, chips)


    def _ai_place_bets(self):
        """Handles AI betting for Poker Style mode."""
        if self.game_mode != GameMode.POKER_STYLE:
            return
        print(f"\n{COLOR_BLUE}--- AI Players Placing Bets ---{COLOR_RESET}"); time.sleep(0.5)
        for name, ai_player_obj in list(self.ai_players.items()): 
            ai_player_obj.current_bet = 0 
            bet_amount = 0
            if ai_player_obj.chips >= AI_DEFAULT_BET * 2 and self.true_count >= 1:
                bet_amount = AI_DEFAULT_BET * 2
            elif ai_player_obj.chips >= AI_DEFAULT_BET:
                bet_amount = AI_DEFAULT_BET
            else:
                bet_amount = ai_player_obj.chips 
            
            bet_amount = min(bet_amount, ai_player_obj.chips) 

            if bet_amount > 0:
                ai_player_obj.chips -= bet_amount
                ai_player_obj.current_bet = bet_amount 
                print(f"{COLOR_BLUE}{name}{COLOR_RESET} bets {COLOR_YELLOW}{bet_amount}{COLOR_RESET} chips. ({COLOR_RED}-{bet_amount}{COLOR_RESET}) (Remaining: {ai_player_obj.chips})")
            else:
                print(f"{COLOR_BLUE}{name}{COLOR_RESET} cannot bet.")
            time.sleep(0.7)
        print("-" * 30)

    def _deal_card_to_hand(self, hand_obj, update_count_for_this_card=True):
        """Deals a single card to a Hand object, reshuffles if needed, and updates count."""
        if len(self.deck) == 0: 
            print(f"{COLOR_YELLOW}Deck empty, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck() 
        
        card_obj = self.deck.deal_card()
        if card_obj:
            hand_obj.add_card(card_obj)
            if update_count_for_this_card:
                self._update_count(card_obj) 
        else:
            sys.exit(f"{COLOR_RED}Critical error: Cannot deal from empty or None deck.{COLOR_RESET}")
        return card_obj


    def _ai_chat(self, category, player_action_details=None): 
        """Makes an AI player say something."""
        if not self.ai_players: return
        
        if random.random() < 0.40:
            if not self.ai_players: return 
            
            ai_name = random.choice(list(self.ai_players.keys()))
            chat_list_key = category

            if category == "player_action":
                combined_list = AI_CHAT.get("taunt", []) + AI_CHAT.get("general_insult", [])
                if combined_list:
                    message = random.choice(combined_list)
                    print(f"{COLOR_CYAN}[{ai_name}]: {message}{COLOR_RESET}")
                    time.sleep(1.2)
                return 

            chat_options = AI_CHAT.get(chat_list_key)
            if chat_options:
                message = random.choice(chat_options)
                print(f"{COLOR_CYAN}[{ai_name}]: {message}{COLOR_RESET}")
                time.sleep(1.2)


    def place_bet(self):
        """Allows the human player to place the initial bet for their first hand."""
        self.human_player.reset_hands() 
        self.human_player.hands = [Hand()] 
        self.human_player.bets = [0]      

        while True:
            try:
                print(f"\n{COLOR_YELLOW}Your chips: {self.human_player.chips}{COLOR_RESET}")
                if self.human_player.chips <= 0:
                    print(f"{COLOR_RED}You have no chips left to bet!{COLOR_RESET}")
                    return False
                
                bet_input = input(f"Place your initial bet (minimum 1, or 'q' to quit round): ")
                if bet_input.lower() == 'q':
                    return False 
                
                bet = int(bet_input)
                if bet <= 0:
                    print(f"{COLOR_RED}Bet must be positive.{COLOR_RESET}")
                elif bet > self.human_player.chips:
                    print(f"{COLOR_RED}You don't have enough chips.{COLOR_RESET}")
                else:
                    self.human_player.bets[0] = bet 
                    self.human_player.chips -= bet
                    print(f"{COLOR_GREEN}Betting {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}")
                    time.sleep(1)
                    return True 
            except ValueError:
                print(f"{COLOR_RED}Invalid input. Please enter a number or 'q'.{COLOR_RESET}")
            except EOFError: 
                print(f"\n{COLOR_RED}Input error. Returning to menu.{COLOR_RESET}")
                return False


    def deal_initial_cards(self):
        """Deals the initial two cards to everyone with animation."""
        print(f"\n{COLOR_BLUE}Dealing cards...{COLOR_RESET}"); time.sleep(0.5)

        self.human_player.hands[0] = Hand() 
        self.dealer.reset_hands()
        if self.settings.get('glados_dealer_mode', False): 
            self.dealer.name = "GLaDOS"
        else:
            self.dealer.name = "Dealer"

        for ai_p in self.ai_players.values():
            ai_p.reset_for_round() 

        participants_in_order = [self.human_player]
        if self.game_mode != GameMode.SOLO:
            participants_in_order.extend(list(self.ai_players.values()))
        participants_in_order.append(self.dealer)
        
        hidden_card_art_lines = Card('Hearts', 'A').get_display_lines(hidden=True) 

        for round_num in range(2): 
            for participant in participants_in_order:
                target_hand = participant.hands[0] 
                display_name = participant.name
                is_dealer_hidden_card = (participant == self.dealer and round_num == 0)

                print("\r" + " " * 60, end="") 
                print(f"\r{COLOR_BLUE}Dealing to {display_name}... {COLOR_RESET}", end="")
                sys.stdout.flush(); time.sleep(0.15)
                
                if hidden_card_art_lines and len(hidden_card_art_lines) > 3:
                     print("\r" + hidden_card_art_lines[3], end="") 
                     sys.stdout.flush(); time.sleep(0.2)

                print("\r" + " " * 60, end="") 
                print(f"\r{COLOR_BLUE}Dealing to {display_name}... Done.{COLOR_RESET}")

                self._deal_card_to_hand(target_hand, update_count_for_this_card=not is_dealer_hidden_card)
                time.sleep(0.1)
        
        print(f"\n{COLOR_BLUE}{'-' * 20}{COLOR_RESET}")


    def _offer_insurance(self):
        """Offers insurance bet to the player if dealer shows an Ace."""
        if not self.dealer.hands[0].cards or len(self.dealer.hands[0].cards) < 2:
             return 0 
        
        dealer_up_card = self.dealer.hands[0].cards[1] 
        
        if dealer_up_card.rank == 'A':
            max_insurance = self.human_player.bets[0] // 2 
            if self.human_player.can_afford_bet(max_insurance) and max_insurance > 0:
                while True:
                    ins_choice = input(f"{COLOR_YELLOW}{self.dealer.name} shows Ace. Insurance? (y/n): {COLOR_RESET}").lower().strip()
                    if ins_choice.startswith('y'):
                        self.human_player.chips -= max_insurance
                        print(f"{COLOR_GREEN}Placed insurance bet of {max_insurance} chips. ({COLOR_RED}-{max_insurance}{COLOR_RESET}){COLOR_RESET}")
                        time.sleep(1)
                        return max_insurance
                    elif ins_choice.startswith('n'):
                        print(f"{COLOR_BLUE}Insurance declined.{COLOR_RESET}"); time.sleep(1)
                        return 0
                    else:
                        print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
            else:
                print(f"{COLOR_DIM}{self.dealer.name} shows Ace, but not enough chips for insurance or insurance is 0.{COLOR_RESET}"); time.sleep(1)
        return 0

    def _resolve_insurance(self, insurance_bet):
        """Resolves the insurance bet."""
        if insurance_bet > 0:
            dealer_hand = self.dealer.hands[0]
            if dealer_hand.cards: 
                 if not self.settings.get("_dealer_hole_card_counted_insurance", False): 
                    self._update_count(dealer_hand.cards[0]) 
                    self.settings["_dealer_hole_card_counted_insurance"] = True


            print(f"\n{COLOR_MAGENTA}--- Resolving Insurance ---{COLOR_RESET}")
            self.display_table(hide_dealer_hole_card=False) # CORRECTED: hide_dealer_hole_card

            if dealer_hand.is_blackjack():
                winnings = insurance_bet * 2 
                total_returned_from_insurance = insurance_bet + winnings 
                print(f"{COLOR_GREEN}{self.dealer.name} has Blackjack! Insurance pays {winnings}. You get {total_returned_from_insurance} chips back from insurance. ({COLOR_GREEN}+{total_returned_from_insurance}{COLOR_RESET}){COLOR_RESET}")
                self.human_player.chips += total_returned_from_insurance
                time.sleep(2.5)
                return True 
            else:
                print(f"{COLOR_RED}{self.dealer.name} does not have Blackjack. Insurance bet lost.{COLOR_RESET}")
                time.sleep(2.5)
                return False 
        return False


    def _offer_even_money(self):
        """Offers even money if player has BJ and dealer shows Ace."""
        player_hand = self.human_player.hands[0]
        if not self.dealer.hands[0].cards or len(self.dealer.hands[0].cards) < 2:
            return False
        dealer_up_card = self.dealer.hands[0].cards[1]

        if player_hand.is_blackjack() and dealer_up_card and dealer_up_card.rank == 'A':
            while True:
                choice = input(f"{COLOR_YELLOW}You have Blackjack, {self.dealer.name} shows Ace. Take Even Money (1:1 payout)? (y/n): {COLOR_RESET}").lower().strip()
                if choice.startswith('y'):
                    payout_amount = self.human_player.bets[0] 
                    print(f"{COLOR_GREEN}Taking Even Money! Guaranteed win of {payout_amount} chips on your bet of {self.human_player.bets[0]}. ({COLOR_GREEN}+{payout_amount}{COLOR_RESET}){COLOR_RESET}")
                    return True 
                elif choice.startswith('n'):
                    print(f"{COLOR_BLUE}Declining Even Money. Playing out the hand...{COLOR_RESET}")
                    return False
                else:
                    print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
        return False


    def get_hand_display_lines(self, player_obj, hand_idx, hide_one_card=False, highlight_active=False, is_ai_poker_mode=False):
        """Generates display lines for a single hand of a player."""
        lines = []
        if hand_idx >= len(player_obj.hands) or hand_idx >= len(player_obj.bets):
            lines.append(f"{COLOR_RED}Error: Invalid hand index for display.{COLOR_RESET}")
            return lines

        hand_obj = player_obj.hands[hand_idx]
        bet_amount = player_obj.bets[hand_idx]
        
        player_name_color = COLOR_MAGENTA 
        display_player_name = player_obj.name 

        if isinstance(player_obj, AIPlayer):
            player_name_color = COLOR_BLUE
        elif player_obj == self.dealer : 
             player_name_color = COLOR_MAGENTA 

        highlight_prefix = f"{COLOR_BOLD}" if highlight_active else ""
        hand_label_str = f" (Hand {hand_idx + 1})" if len(player_obj.hands) > 1 else ""
        bet_info_str = f" | Bet: {bet_amount}" if bet_amount > 0 else ""
        
        ai_type_str = ""
        ai_chip_info_str = ""
        ai_current_bet_str = "" 
        if isinstance(player_obj, AIPlayer):
            ai_type_str = f" ({player_obj.ai_type.value})"
            if is_ai_poker_mode:
                ai_chip_info_str = f" | Chips: {player_obj.chips}"
                if player_obj.current_bet > 0 : 
                     ai_current_bet_str = f" | Betting: {player_obj.current_bet}"


        header = f"{highlight_prefix}{player_name_color}--- {display_player_name}{ai_type_str}{hand_label_str}'s Hand{bet_info_str}{ai_chip_info_str}{ai_current_bet_str} ---{COLOR_RESET}"
        lines.append(header)

        if not hand_obj.cards:
            lines.append("[ No cards ]")
        else:
            card_art_segments = [[] for _ in range(7)] 
            for i, card_obj_in_hand in enumerate(hand_obj.cards):
                is_hidden_for_display = hide_one_card and i == 0
                single_card_lines = card_obj_in_hand.get_display_lines(hidden=is_hidden_for_display)
                for line_num, line_content in enumerate(single_card_lines):
                    card_art_segments[line_num].append(line_content)
            
            for line_idx in range(7):
                lines.append("  ".join(card_art_segments[line_idx]))

        value_line_str = ""
        if not hide_one_card: 
            value = hand_obj.calculate_value()
            status_str = ""
            if hand_obj.is_blackjack(): status_str = f" {COLOR_GREEN}{COLOR_BOLD}BLACKJACK!{COLOR_RESET}"
            elif hand_obj.is_bust(): status_str = f" {COLOR_RED}{COLOR_BOLD}BUST!{COLOR_RESET}"
            value_line_str = f"{COLOR_YELLOW}Value: {value}{status_str}{COLOR_RESET}"
        elif len(hand_obj.cards) > 1: 
            visible_card = hand_obj.cards[1] 
            visible_value = visible_card.value
            if visible_card.rank == 'A': visible_value = 11 
            value_line_str = f"{COLOR_YELLOW}Showing: {visible_value}{COLOR_RESET}"
        elif hide_one_card and hand_obj.cards: 
             value_line_str = f"{COLOR_YELLOW}Showing: ?{COLOR_RESET}"


        if value_line_str:
            lines.append(value_line_str)

        visible_header_width = get_visible_width(header)
        lines.append(f"{player_name_color}-{COLOR_RESET}" * max(1,visible_header_width)) 
        return lines


    def display_table(self, hide_dealer_hole_card=True, current_player_hand_idx=-1):
        """Displays the current state of the table."""
        clear_screen()
        title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ {self.game_mode.value} ~~~{COLOR_RESET}"
        
        player_total_bet = sum(self.human_player.bets)
        count_info_str = ""
        if self.settings['card_counting_cheat']:
            count_info_str = f" | RC: {self.running_count} | TC: {self.true_count:.1f}"

        print(center_text(title, TERMINAL_WIDTH))
        print(center_text(f"{COLOR_YELLOW}Your Chips: {self.human_player.chips} | Your Bet(s): {player_total_bet}{count_info_str}{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")

        dealer_display_lines = self.get_hand_display_lines(self.dealer, 0, hide_one_card=hide_dealer_hole_card)
        for line in dealer_display_lines: print(line)
        print()

        if self.ai_players:
            print(center_text(f"{COLOR_BLUE}--- AI Players ---{COLOR_RESET}", TERMINAL_WIDTH))
            is_poker_mode_for_ai = (self.game_mode == GameMode.POKER_STYLE)
            for ai_p_obj in self.ai_players.values():
                ai_display_lines = self.get_hand_display_lines(ai_p_obj, 0, is_ai_poker_mode=is_poker_mode_for_ai)
                for line in ai_display_lines: print(line)
                print()
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")
        
        if self.human_player.hands and any(h.cards or b > 0 for h,b in zip(self.human_player.hands, self.human_player.bets) ):
            print(center_text(f"{COLOR_MAGENTA}--- Your Hands ---{COLOR_RESET}", TERMINAL_WIDTH))
            for idx, hand_obj in enumerate(self.human_player.hands):
                if hand_obj.cards or (idx < len(self.human_player.bets) and self.human_player.bets[idx] > 0):
                    is_active_hand = (idx == current_player_hand_idx) and (len(self.human_player.hands) > 1)
                    player_hand_lines = self.get_hand_display_lines(self.human_player, idx, highlight_active=is_active_hand)
                    for line in player_hand_lines: print(line)
                    print()
        else:
            print(center_text(f"{COLOR_DIM}[ No player hands active ]{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")


    def _play_one_human_hand(self, hand_index):
        """Handles the player's turn for a single hand. Returns status like 'stand', 'bust', 'surrender', 'error'."""
        if hand_index >= len(self.human_player.hands) or hand_index >= len(self.human_player.bets):
            print(f"{COLOR_RED}Error: Invalid hand index for player ({hand_index}).{COLOR_RESET}"); return 'error'
        
        current_hand = self.human_player.hands[hand_index]
        current_bet = self.human_player.bets[hand_index]
        hand_label = f"Hand {hand_index + 1}" if len(self.human_player.hands) > 1 else "Your Hand"
        
        can_take_initial_action = (len(current_hand.cards) == 2)
        player_stood_on_this_hand = False

        while current_hand.calculate_value() < 21 and not player_stood_on_this_hand:
            self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index)
            
            hint_str = "" 
            actual_hint_text = ""
            hint_prefix = ""

            dealer_up_card_for_hint = None
            if self.dealer.hands[0].cards and len(self.dealer.hands[0].cards) >= 2:
                dealer_up_card_for_hint = self.dealer.hands[0].cards[1]

            if current_hand.cards and dealer_up_card_for_hint:
                is_glados_mode_on = self.settings.get('glados_dealer_mode', False)
                if is_glados_mode_on:
                    hint_prefix = f"{COLOR_MAGENTA}[GLaDOS]: {COLOR_RESET}" 
                    actual_hint_text = get_basic_strategy_hint(current_hand, dealer_up_card_for_hint, is_glados_active=True)
                elif self.settings['easy_mode']:
                    actual_hint_text = get_basic_strategy_hint(current_hand, dealer_up_card_for_hint, is_glados_active=False)
                    if actual_hint_text : 
                         actual_hint_text = f"{COLOR_GREEN}{actual_hint_text}{COLOR_RESET}"


            if actual_hint_text:
                hint_str = f"{hint_prefix}{actual_hint_text}"
            
            count_hint_str = ""
            if self.settings['easy_mode'] and self.settings['card_counting_cheat']: 
                if self.true_count >= 2: count_hint_str = f" {COLOR_GREEN}(High Count: {self.true_count:.1f}){COLOR_RESET}"
                elif self.true_count <= -1: count_hint_str = f" {COLOR_RED}(Low Count: {self.true_count:.1f}){COLOR_RESET}"

            print(f"\n--- Playing {COLOR_MAGENTA}{hand_label}{COLOR_RESET} (Value: {current_hand.calculate_value()}) {hint_str}{count_hint_str} ---")

            options = ["(h)it", "(s)tand"]
            can_double = can_take_initial_action and self.human_player.can_afford_bet(current_bet)
            can_split = (can_take_initial_action and
                         len(current_hand.cards) == 2 and
                         current_hand.cards[0].rank == current_hand.cards[1].rank and
                         self.human_player.can_afford_bet(current_bet) and
                         len(self.human_player.hands) < 4) 
            can_surrender = can_take_initial_action

            if can_double: options.append("(d)ouble down")
            if can_split: options.append("s(p)lit")
            if can_surrender: options.append("su(r)render") 

            prompt = f"{COLOR_YELLOW}Choose action: {', '.join(options)}? {COLOR_RESET}"
            action = input(prompt).lower().strip()

            if action.startswith('h'): 
                new_card = self._deal_card_to_hand(current_hand)
                print(f"\n{COLOR_GREEN}You hit!{COLOR_RESET} Received:"); 
                for line in new_card.get_display_lines(): print(line)
                self._ai_chat("player_action", player_action_details='hit'); time.sleep(1.5)
                can_take_initial_action = False
                if current_hand.is_bust():
                    self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index) 
                    print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS!{COLOR_RESET}")
                    self.session_stats['player_busts'] += 1
                    self._ai_chat("player_bust"); time.sleep(1.5)
                    return 'bust'
            elif action.startswith('s'): 
                print(f"\n{COLOR_BLUE}You stand on {hand_label}.{COLOR_RESET}")
                self._ai_chat("player_action", player_action_details='stand'); time.sleep(1)
                player_stood_on_this_hand = True
            elif action.startswith('d') and can_double: 
                print(f"\n{COLOR_YELLOW}Doubling down on {hand_label}!{COLOR_RESET}")
                self.human_player.chips -= current_bet 
                self.human_player.bets[hand_index] += current_bet 
                print(f"Bet for this hand is now {self.human_player.bets[hand_index]}. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)
                
                new_card = self._deal_card_to_hand(current_hand)
                print(f"{COLOR_BLUE}Received one card:{COLOR_RESET}")
                for line in new_card.get_display_lines(): print(line)
                self._ai_chat("player_action", player_action_details='double'); time.sleep(1.5)
                
                self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index)
                final_value = current_hand.calculate_value()
                if current_hand.is_bust():
                    print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS after doubling down!{COLOR_RESET}")
                    self.session_stats['player_busts'] += 1; self._ai_chat("player_bust")
                    time.sleep(2); return 'double_bust' 
                else:
                    print(f"\n{hand_label} finishes with {final_value} after doubling down.")
                    time.sleep(2); return 'double_stand' 
            elif action.startswith('p') and can_split: 
                print(f"\n{COLOR_YELLOW}Splitting {current_hand.cards[0].rank}s!{COLOR_RESET}")
                self.human_player.chips -= current_bet 
                
                split_card = current_hand.cards.pop(1)
                new_hand_obj = Hand()
                new_hand_obj.add_card(split_card)
                
                self.human_player.hands.insert(hand_index + 1, new_hand_obj)
                self.human_player.bets.insert(hand_index + 1, current_bet)

                print(f"Placed additional {current_bet} bet for the new hand. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)

                print(f"Dealing card to original hand (Hand {hand_index + 1})..."); 
                self._deal_card_to_hand(current_hand); time.sleep(0.5)
                print(f"Dealing card to new hand (Hand {hand_index + 2})..."); 
                self._deal_card_to_hand(new_hand_obj); time.sleep(1)
                
                self._ai_chat("player_action", player_action_details='split')
                self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=hand_index) 
                time.sleep(1.5)
                can_take_initial_action = (len(current_hand.cards) == 2)
                if current_hand.cards and current_hand.cards[0].rank == 'A': 
                    print(f"{COLOR_BLUE}Played split Ace for Hand {hand_index + 1}. Standing automatically.{COLOR_RESET}")
                    player_stood_on_this_hand = True 
                continue 
            
            elif action.startswith('r') and can_surrender: 
                print(f"\n{COLOR_YELLOW}Surrendering {hand_label}.{COLOR_RESET}")
                refund = current_bet // 2
                print(f"Half your bet ({refund}) is returned.")
                self.human_player.chips += refund
                self.session_stats['chips_lost'] += (current_bet - refund) 
                self._ai_chat("player_action", player_action_details='surrender')
                time.sleep(2)
                current_hand.cards = [] 
                self.human_player.bets[hand_index] = 0 
                return 'surrender'
            else:
                print(f"{COLOR_RED}Invalid action or action not allowed now.{COLOR_RESET}")
                self._ai_chat("general_insult"); time.sleep(1.5)

            if current_hand.calculate_value() == 21 and not player_stood_on_this_hand:
                if not (len(current_hand.cards) == 2 and can_take_initial_action): 
                    print(f"\n{COLOR_GREEN}{hand_label} has 21! Standing automatically.{COLOR_RESET}"); time.sleep(1.5)
                player_stood_on_this_hand = True
        
        return 'stand' if player_stood_on_this_hand else 'bust'


    def human_player_turn(self):
        """Handles the human player's turn, iterating through all their active hands."""
        current_hand_idx_for_play = 0
        while current_hand_idx_for_play < len(self.human_player.hands):
            if current_hand_idx_for_play >= len(self.human_player.bets):
                break 

            current_playing_hand = self.human_player.hands[current_hand_idx_for_play]
            current_playing_bet = self.human_player.bets[current_hand_idx_for_play]

            if not current_playing_hand.cards and current_playing_bet == 0: 
                current_hand_idx_for_play += 1
                continue

            if current_playing_hand.is_blackjack(): 
                if not (current_playing_hand.cards[0].rank == 'A' and len(self.human_player.hands) > 1 and current_hand_idx_for_play > 0):
                    self.display_table(hide_dealer_hole_card=True, current_player_hand_idx=current_hand_idx_for_play)
                    hand_label = f"Hand {current_hand_idx_for_play + 1}" if len(self.human_player.hands) > 1 else "Your Hand"
                    print(f"\n{COLOR_GREEN}{hand_label} has Blackjack! Standing.{COLOR_RESET}")
                    time.sleep(1.5)
                current_hand_idx_for_play +=1
                continue
            hand_status = self._play_one_human_hand(current_hand_idx_for_play)
            current_hand_idx_for_play += 1
        
        if any(h.cards and not h.is_bust() for h in self.human_player.hands):
            print(f"\n{COLOR_BLUE}Player finishes playing all hands.{COLOR_RESET}"); time.sleep(1.5)


    def ai_turns(self):
        """Handles the turns for all AI players."""
        if not self.ai_players: return

        print(f"\n{COLOR_BLUE}--- AI Players' Turns ---{COLOR_RESET}"); time.sleep(1)
        
        dealer_up_card_obj = self.dealer.hands[0].cards[1] if len(self.dealer.hands[0].cards) >=2 else None
        dealer_up_card_value_for_ai = 0
        if dealer_up_card_obj:
            dealer_up_card_value_for_ai = dealer_up_card_obj.value
            if dealer_up_card_obj.rank == 'A': dealer_up_card_value_for_ai = 11 

        for name, ai_p_obj in list(self.ai_players.items()): 
            if name not in self.ai_players: continue 

            current_ai_hand = ai_p_obj.hands[0] 
            
            if self.game_mode == GameMode.POKER_STYLE and ai_p_obj.current_bet == 0:
                print(f"{COLOR_DIM}{name} did not bet this round.{COLOR_RESET}"); time.sleep(0.5)
                continue

            self.display_table(hide_dealer_hole_card=True) 
            print(f"\n{COLOR_BLUE}{name}'s turn ({ai_p_obj.ai_type.value})...{COLOR_RESET}"); time.sleep(1.5)

            while True: 
                if current_ai_hand.is_bust() or current_ai_hand.calculate_value() == 21:
                    break 

                decision = get_ai_decision(ai_p_obj.ai_type, current_ai_hand.cards, dealer_up_card_value_for_ai, self.running_count, self.true_count)
                
                print(f"{name} ({ai_p_obj.ai_type.value}) decides to {COLOR_YELLOW}{decision}{COLOR_RESET}..."); time.sleep(1.2)

                if decision == "hit":
                    print(f"{name} {COLOR_GREEN}hits{COLOR_RESET}..."); time.sleep(0.8)
                    self._deal_card_to_hand(current_ai_hand) 
                    self.display_table(hide_dealer_hole_card=True) 
                    time.sleep(1.5)
                    if current_ai_hand.is_bust():
                        print(f"\n{COLOR_RED}{COLOR_BOLD}{name} BUSTS!{COLOR_RESET}")
                        self._ai_chat("ai_bust"); time.sleep(1.5)
                        break 
                else: 
                    print(f"{name} {COLOR_BLUE}stands{COLOR_RESET}."); time.sleep(1)
                    break 
            
            if list(self.ai_players.keys())[-1] != name: 
                 print(f"{COLOR_DIM}{'-' * 15}{COLOR_RESET}"); time.sleep(1)


    def dealer_turn(self):
        """Handles the dealer's turn."""
        print(f"\n{COLOR_MAGENTA}--- {self.dealer.name}'s Turn ---{COLOR_RESET}"); time.sleep(1) 
        
        dealer_hand = self.dealer.hands[0]
        
        if len(dealer_hand.cards) == 2 and not self.settings.get("_dealer_hole_card_counted", False) \
           and not self.settings.get("_dealer_hole_card_counted_insurance", False): 
             self._update_count(dealer_hand.cards[0]) 
             self.settings["_dealer_hole_card_counted"] = True 

        self.display_table(hide_dealer_hole_card=False) 

        while dealer_hand.calculate_value() < 17:
            print(f"{COLOR_MAGENTA}{self.dealer.name} must hit...{COLOR_RESET}"); time.sleep(1.5)
            new_card = self._deal_card_to_hand(dealer_hand) 
            print(f"{COLOR_MAGENTA}{self.dealer.name} receives:{COLOR_RESET}")
            for line in new_card.get_display_lines(): print(line)
            time.sleep(1.5)
            self.display_table(hide_dealer_hole_card=False) 
            if dealer_hand.is_bust():
                print(f"\n{COLOR_RED}{COLOR_BOLD}{self.dealer.name} BUSTS!{COLOR_RESET}"); time.sleep(1.5)
                return
        
        dealer_final_value = dealer_hand.calculate_value()
        if not dealer_hand.is_bust(): 
            print(f"{COLOR_MAGENTA}{self.dealer.name} stands with {dealer_final_value}.{COLOR_RESET}")
        time.sleep(2)


    def determine_winner(self, even_money_taken=False):
        """Determines the winner(s) and distributes chips."""
        clear_screen()
        print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Round Results ---{COLOR_RESET}"); time.sleep(1)

        dealer_hand = self.dealer.hands[0]
        dealer_value = dealer_hand.calculate_value()
        is_dealer_blackjack = dealer_hand.is_blackjack()

        print(f"\n{COLOR_BLUE}--- Final Hands ---{COLOR_RESET}")
        for line in self.get_hand_display_lines(self.dealer, 0, hide_one_card=False): print(line)
        print()

        if self.ai_players:
            print(f"{COLOR_BLUE}--- AI Players Final Hands ---{COLOR_RESET}")
            is_poker_mode = (self.game_mode == GameMode.POKER_STYLE)
            for ai_p in self.ai_players.values():
                for line in self.get_hand_display_lines(ai_p, 0, is_ai_poker_mode=is_poker_mode): print(line)
                print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")

        if self.human_player.hands and any(h.cards or b > 0 for h,b in zip(self.human_player.hands, self.human_player.bets)):
            print(f"{COLOR_MAGENTA}--- Your Final Hands ---{COLOR_RESET}")
            for idx, hand_obj in enumerate(self.human_player.hands):
                 if hand_obj.cards or (idx < len(self.human_player.bets) and self.human_player.bets[idx] > 0) :
                    for line in self.get_hand_display_lines(self.human_player, idx): print(line)
                    print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")
        time.sleep(2.5)

        print(f"\n{COLOR_YELLOW}--- Your Hand Results ---{COLOR_RESET}")
        player_won_any_hand_this_round = False

        if even_money_taken: 
            bet_val = self.human_player.bets[0] 
            print(f"{COLOR_GREEN}Your Hand: Took Even Money. Won {bet_val} on your bet of {bet_val}. Total chips received: {bet_val*2}.{COLOR_RESET}")
            player_won_any_hand_this_round = True
        else: 
            for idx, player_h_obj in enumerate(self.human_player.hands):
                if idx >= len(self.human_player.bets): continue 

                if not player_h_obj.cards and self.human_player.bets[idx] == 0 : 
                    continue

                player_val = player_h_obj.calculate_value()
                bet_val = self.human_player.bets[idx]
                hand_label = f"Hand {idx+1}" if len(self.human_player.hands) > 1 else "Your Hand"
                is_player_bj_this_hand = player_h_obj.is_blackjack()
                
                payout = 0 
                result_text = ""
                chips_change_for_stats = 0 

                if player_h_obj.is_bust():
                    result_text = f"{COLOR_RED}{hand_label}: Busted! You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val 
                    self.session_stats['dealer_wins'] += 1
                elif is_player_bj_this_hand and not is_dealer_blackjack:
                    payout = int(bet_val * 1.5) 
                    self.human_player.chips += bet_val + payout 
                    result_text = f"{COLOR_GREEN}{COLOR_BOLD}{hand_label}: BLACKJACK! You win {payout} (pays 3:2). Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    self.session_stats['player_blackjacks'] += 1
                    player_won_any_hand_this_round = True
                elif is_dealer_blackjack and not is_player_bj_this_hand :
                    result_text = f"{COLOR_RED}{hand_label}: {self.dealer.name} has Blackjack! You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val
                    self.session_stats['dealer_wins'] += 1
                elif is_dealer_blackjack and is_player_bj_this_hand: 
                    self.human_player.chips += bet_val 
                    result_text = f"{COLOR_YELLOW}{hand_label}: Push! Both have Blackjack. Bet of {bet_val} returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}"
                    self.session_stats['pushes'] += 1
                elif dealer_hand.is_bust():
                    payout = bet_val 
                    self.human_player.chips += bet_val + payout 
                    result_text = f"{COLOR_GREEN}{hand_label}: {self.dealer.name} busts! You win {payout}. Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    player_won_any_hand_this_round = True
                elif player_val > dealer_value:
                    payout = bet_val
                    self.human_player.chips += bet_val + payout
                    result_text = f"{COLOR_GREEN}{hand_label}: You win! ({player_val} vs {dealer_value}). Win {payout}. Total: {bet_val+payout}. ({COLOR_GREEN}+{bet_val+payout}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = payout
                    self.session_stats['player_wins'] += 1
                    player_won_any_hand_this_round = True
                elif player_val == dealer_value:
                    self.human_player.chips += bet_val 
                    result_text = f"{COLOR_YELLOW}{hand_label}: Push! ({player_val}). Bet of {bet_val} returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}"
                    self.session_stats['pushes'] += 1
                else: 
                    result_text = f"{COLOR_RED}{hand_label}: {self.dealer.name} wins ({dealer_value} vs {player_val}). You lose {bet_val} chips. ({COLOR_RED}-{bet_val}{COLOR_RESET}){COLOR_RESET}"
                    chips_change_for_stats = -bet_val
                    self.session_stats['dealer_wins'] += 1
                
                print(result_text)
                if chips_change_for_stats > 0: self.session_stats['chips_won'] += chips_change_for_stats
                elif chips_change_for_stats < 0: self.session_stats['chips_lost'] += abs(chips_change_for_stats)
                time.sleep(1.5)

        if not even_money_taken:
            if player_won_any_hand_this_round: self._ai_chat("player_win")
            elif all(not h.cards or h.is_bust() for h in self.human_player.hands): pass 
            else: self._ai_chat("taunt") 

        print("-" * 30)
        print(f"{COLOR_YELLOW}Your chip total after round: {self.human_player.chips}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")
        time.sleep(2.5)

        if self.ai_players and self.game_mode == GameMode.POKER_STYLE:
            print(f"\n{COLOR_BLUE}--- AI Player Results ---{COLOR_RESET}")
            for name, ai_p_obj in list(self.ai_players.items()): 
                if name not in self.ai_players: continue 

                ai_hand = ai_p_obj.hands[0]
                ai_bet_val = ai_p_obj.current_bet 
                result_str = ""; result_color = COLOR_RESET; 
                net_chip_change = 0 

                if ai_bet_val > 0: 
                    ai_val = ai_hand.calculate_value()
                    is_ai_bj = ai_hand.is_blackjack()

                    if ai_hand.is_bust():
                        result_str = "Busted!"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val 
                    elif is_ai_bj and not is_dealer_blackjack:
                        result_str = "Blackjack! (Wins 3:2)"; result_color = COLOR_GREEN
                        net_chip_change = int(ai_bet_val * 1.5)
                        ai_p_obj.chips += ai_bet_val + net_chip_change 
                        self._ai_chat("ai_win")
                    elif is_dealer_blackjack and not is_ai_bj:
                        result_str = f"Loses (vs {self.dealer.name} BJ)"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val
                    elif is_dealer_blackjack and is_ai_bj: 
                        result_str = "Push (Both BJ)"; result_color = COLOR_YELLOW
                        ai_p_obj.chips += ai_bet_val 
                        net_chip_change = 0
                    elif dealer_hand.is_bust():
                        result_str = f"Wins ({self.dealer.name} Bust)"; result_color = COLOR_GREEN
                        net_chip_change = ai_bet_val
                        ai_p_obj.chips += ai_bet_val + net_chip_change
                        self._ai_chat("ai_win")
                    elif ai_val > dealer_value:
                        result_str = f"Wins ({ai_val} vs {dealer_value})"; result_color = COLOR_GREEN
                        net_chip_change = ai_bet_val
                        ai_p_obj.chips += ai_bet_val + net_chip_change
                        self._ai_chat("ai_win")
                    elif ai_val == dealer_value:
                        result_str = f"Push ({ai_val})"; result_color = COLOR_YELLOW
                        ai_p_obj.chips += ai_bet_val 
                        net_chip_change = 0
                    else: 
                        result_str = f"Loses ({ai_val} vs {dealer_value})"; result_color = COLOR_RED
                        net_chip_change = -ai_bet_val
                    
                    chip_change_color = COLOR_GREEN if net_chip_change > 0 else (COLOR_RED if net_chip_change < 0 else COLOR_YELLOW)
                    chip_change_sign = "+" if net_chip_change > 0 else ""
                    result_str += f" (Bet: {ai_bet_val}, Result: {chip_change_color}{chip_change_sign}{net_chip_change}{COLOR_RESET}) | Chips: {ai_p_obj.chips}"
                    
                    if ai_p_obj.chips <= 0:
                        print(f"{COLOR_RED}{name} ran out of chips and leaves the table!{COLOR_RESET}")
                        del self.ai_players[name]; time.sleep(1)
                        continue 
                else: 
                    result_str = "Did not bet"; result_color = COLOR_DIM 
                
                print(f"{COLOR_BLUE}{name} ({ai_p_obj.ai_type.value}){COLOR_RESET}: {result_color}{result_str}{COLOR_RESET}"); time.sleep(0.6)
            print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")


    def manage_ai_players(self):
        """Manages AI players joining/leaving in relevant game modes."""
        if self.game_mode == GameMode.SOLO: return
        
        print(f"\n{COLOR_YELLOW}Checking table activity...{COLOR_RESET}"); time.sleep(1)
        activity_occurred = False

        for name in list(self.ai_players.keys()):
            leave_chance = 0.25 if len(self.ai_players) >= MAX_AI_PLAYERS else 0.15
            if len(self.ai_players) > MIN_AI_PLAYERS and random.random() < leave_chance:
                if name in self.ai_players: 
                    print(f"{COLOR_RED}{self.ai_players[name].name} has left the table.{COLOR_RESET}")
                    del self.ai_players[name]
                    activity_occurred = True; time.sleep(0.8)
        
        available_spots = MAX_AI_PLAYERS - len(self.ai_players)
        potential_new_ai_names = [n for n in AI_NAMES if n not in self.ai_players] 

        join_chance = 0.4 if len(self.ai_players) < MAX_AI_PLAYERS / 2 else 0.25
        if available_spots > 0 and potential_new_ai_names and random.random() < join_chance:
            num_to_join = random.randint(1, min(available_spots, len(potential_new_ai_names)))
            for _ in range(num_to_join):
                if not potential_new_ai_names: break 
                
                new_ai_name = random.choice(potential_new_ai_names)
                potential_new_ai_names.remove(new_ai_name) 
                
                new_ai_type = random.choice(list(AIType))
                new_ai_chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
                
                self.ai_players[new_ai_name] = AIPlayer(new_ai_name, new_ai_type, new_ai_chips)
                chip_info = f" with {new_ai_chips} chips" if self.game_mode == GameMode.POKER_STYLE else ""
                print(f"{COLOR_GREEN}{new_ai_name} ({new_ai_type.value}) has joined the table{chip_info}!{COLOR_RESET}")
                activity_occurred = True; time.sleep(0.8)

        if not activity_occurred:
            print(f"{COLOR_DIM}The table remains the same.{COLOR_RESET}"); time.sleep(1)


    def play_round(self):
        """Plays a single round of Blackjack. Returns 'game_over', 'quit', or True for continue."""
        clear_screen()
        print(f"{COLOR_MAGENTA}--- Starting New Round ({self.game_mode.value}) ---{COLOR_RESET}")
        self.session_stats['hands_played'] += 1
        self.settings["_dealer_hole_card_counted"] = False 
        self.settings["_dealer_hole_card_counted_insurance"] = False

        if self.settings.get('glados_dealer_mode', False):
            self.dealer.name = "GLaDOS"
        else:
            self.dealer.name = "Dealer"

        if not self.place_bet(): 
            if self.human_player.chips <= 0:
                print(f"\n{COLOR_RED}Out of chips!{COLOR_RESET}"); time.sleep(2)
                return 'game_over'
            else: 
                print(f"{COLOR_YELLOW}Returning to menu...{COLOR_RESET}"); time.sleep(1.5)
                return 'quit'

        self._ai_place_bets() 

        max_potential_cards_needed = (1 + len(self.ai_players) + 1) * 5 + 10 
        if len(self.deck) < max_potential_cards_needed :
            print(f"{COLOR_YELLOW}Deck low, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck()
        else:
            print(f"{COLOR_YELLOW}Preparing next hand...{COLOR_RESET}"); time.sleep(0.7); clear_screen()

        self.deal_initial_cards()
        self.display_table(hide_dealer_hole_card=True)

        insurance_bet_amount = self._offer_insurance()
        
        took_even_money = False
        if self.human_player.hands[0].is_blackjack() and \
           self.dealer.hands[0].cards and len(self.dealer.hands[0].cards) >=2 and \
           self.dealer.hands[0].cards[1].rank == 'A':
            if self._offer_even_money():
                took_even_money = True
                payout = self.human_player.bets[0]
                self.human_player.chips += self.human_player.bets[0] + payout 
                self.session_stats['player_wins'] += 1
                self.session_stats['player_blackjacks'] += 1
                self.session_stats['chips_won'] += payout
                print(f"{COLOR_GREEN}Round over for you due to Even Money.{COLOR_RESET}"); time.sleep(2)
                
                if self.game_mode != GameMode.SOLO: self.ai_turns()
                self.dealer_turn() 
                self.determine_winner(even_money_taken=True) 
                return True 

        dealer_had_blackjack_on_insurance_check = self._resolve_insurance(insurance_bet_amount)

        player_initial_hand = self.human_player.hands[0]
        is_player_initial_blackjack = player_initial_hand.is_blackjack()

        if dealer_had_blackjack_on_insurance_check:
            print(f"{COLOR_RED}{self.dealer.name} Blackjack. Round over for player's main hand unless player also has BJ.{COLOR_RESET}"); time.sleep(2)
            if self.game_mode != GameMode.SOLO: self.ai_turns() 
            self.determine_winner() 
            return True

        if is_player_initial_blackjack and not dealer_had_blackjack_on_insurance_check: 
            print(f"\n{COLOR_GREEN}{COLOR_BOLD}Blackjack!{COLOR_RESET}"); time.sleep(1.5)
            if self.game_mode != GameMode.SOLO: self.ai_turns()
            self.dealer_turn()
            self.determine_winner()
            return True
        
        if not is_player_initial_blackjack and not dealer_had_blackjack_on_insurance_check:
            self.human_player_turn() 

            player_all_hands_busted_or_surrendered = all(
                not hand.cards or hand.is_bust() for hand in self.human_player.hands
            )

            if not player_all_hands_busted_or_surrendered:
                if self.game_mode != GameMode.SOLO: self.ai_turns()
                self.dealer_turn()
            else: 
                print(f"\n{COLOR_RED}All your hands busted or surrendered!{COLOR_RESET}")
                if any(ai_p.current_bet > 0 for ai_p in self.ai_players.values()) or self.game_mode != GameMode.SOLO:
                    print(f"{COLOR_DIM}{self.dealer.name} plays for AI / card counting...{COLOR_RESET}")
                    self.dealer_turn()
                else: 
                    print(f"\n{COLOR_MAGENTA}--- {self.dealer.name} reveals ---{COLOR_RESET}"); time.sleep(1)
                    if len(self.dealer.hands[0].cards) == 2 and \
                       not self.settings.get("_dealer_hole_card_counted", False) and \
                       not self.settings.get("_dealer_hole_card_counted_insurance", False):
                         self._update_count(self.dealer.hands[0].cards[0])
                         self.settings["_dealer_hole_card_counted"] = True
                    self.display_table(hide_dealer_hole_card=False); time.sleep(1.5)
        
        self.determine_winner()

        if self.human_player.chips <= 0:
            print(f"\n{COLOR_RED}You've run out of chips! Game Over.{COLOR_RESET}"); time.sleep(2.5)
            return 'game_over'
        
        self.manage_ai_players() 
        return True


    def run_game(self):
        """Runs the main game loop for playing rounds."""
        while True:
            round_status = self.play_round()
            if round_status == 'game_over':
                print(f"{COLOR_YELLOW}Returning to main menu...{COLOR_RESET}"); time.sleep(2)
                break 
            elif round_status == 'quit': 
                break
            elif round_status is True: 
                print(f"\n{COLOR_YELLOW}Your current chips: {self.human_player.chips}{COLOR_RESET}")
                if self.game_mode != GameMode.SOLO and not self.ai_players:
                    print(f"{COLOR_YELLOW}All AI players have left or busted out!{COLOR_RESET}")
                    input("Press Enter to return to menu..."); break
                
                next_round_choice = input(f"Press Enter for next round, or 'q' to return to menu... ").lower()
                if next_round_choice == 'q':
                    break
            else: 
                print(f"{COLOR_RED}Unexpected round result: {round_status}. Returning to menu.{COLOR_RESET}"); break
        clear_screen()


    def save_game(self):
        """Saves the current game state to a file."""
        ai_players_serializable = {}
        for name, ai_obj in self.ai_players.items():
            ai_players_serializable[name] = {
                'type': ai_obj.ai_type.name, 
                'chips': ai_obj.chips
            }
        
        state = {
            "player_chips": self.human_player.chips,
            "ai_players": ai_players_serializable, 
            "session_stats": self.session_stats,
            "game_mode": self.game_mode.name, 
            "settings": self.settings,
        }
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
            print(f"{COLOR_GREEN}Game saved successfully to {SAVE_FILE}{COLOR_RESET}")
        except IOError as e:
            print(f"{COLOR_RED}Error saving game: {e}{COLOR_RESET}")
        time.sleep(1.5)

    def load_game(self):
        """Loads game state from a file. Returns True if successful, False otherwise."""
        try:
            if not os.path.exists(SAVE_FILE):
                print(f"{COLOR_YELLOW}No save file found ({SAVE_FILE}).{COLOR_RESET}"); time.sleep(1.5)
                return False
            
            with open(SAVE_FILE, 'r') as f:
                state = json.load(f)

            self.human_player.chips = state.get("player_chips", 100)
            
            loaded_ai_data = state.get("ai_players", {})
            self.ai_players = {} 
            for name, data in loaded_ai_data.items():
                try:
                    ai_type_enum = AIType[data.get('type', 'BASIC')]
                except KeyError:
                    ai_type_enum = AIType.BASIC
                    print(f"{COLOR_RED}Warning: Invalid AI type '{data.get('type')}' for {name}. Defaulting.{COLOR_RESET}")
                self.ai_players[name] = AIPlayer(name, ai_type_enum, data.get('chips', AI_STARTING_CHIPS))

            self.session_stats = state.get("session_stats", BlackjackGame._default_stats())
            
            try:
                self.game_mode = GameMode[state.get("game_mode", "QUICK_PLAY")]
            except KeyError:
                print(f"{COLOR_RED}Warning: Invalid game mode '{state.get('game_mode')}' loaded. Defaulting.{COLOR_RESET}")
                self.game_mode = GameMode.QUICK_PLAY
            
            self.settings = state.get("settings", BlackjackGame._default_settings())
            
            if self.settings.get('glados_dealer_mode', False):
                self.dealer.name = "GLaDOS"
            else:
                self.dealer.name = "Dealer"

            self._create_and_shuffle_deck() 
            
            print(f"{COLOR_GREEN}Game loaded successfully from {SAVE_FILE}{COLOR_RESET}")
            print(f"Loaded Mode: {self.game_mode.value}, Player Chips: {self.human_player.chips}")
            time.sleep(2)
            return True
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print(f"{COLOR_RED}Error loading game: {e}{COLOR_RESET}")
            time.sleep(1.5)
            return False


# --- Main Application Logic ---
def main():
    """Main function to run the application."""
    global TERMINAL_WIDTH
    try:
        TERMINAL_WIDTH = os.get_terminal_size().columns
    except OSError:
        print(f"{COLOR_YELLOW}Could not detect terminal size. Using default width: {DEFAULT_TERMINAL_WIDTH}{COLOR_RESET}")
        TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH
        time.sleep(1.5)

    game_instance = None
    current_settings = BlackjackGame._default_settings() 
    current_stats = BlackjackGame._default_stats()

    title_screen()
    while True:
        stats_to_show = game_instance.session_stats if game_instance else current_stats
        settings_for_menu_display = current_settings 
        if game_instance and game_instance.settings: 
             pass 

        choice = display_menu()
        selected_game_mode_enum = None

        if choice == '1': selected_game_mode_enum = GameMode.QUICK_PLAY
        elif choice == '2': selected_game_mode_enum = GameMode.SOLO
        elif choice == '3': selected_game_mode_enum = GameMode.POKER_STYLE
        elif choice == '4': display_rules(); continue
        elif choice == '5':
            display_settings_menu(current_settings) 
            if game_instance:
                game_instance.settings['glados_dealer_mode'] = current_settings.get('glados_dealer_mode', False)
                if game_instance.settings.get('glados_dealer_mode', False):
                    game_instance.dealer.name = "GLaDOS"
                else:
                    game_instance.dealer.name = "Dealer"
            continue
        elif choice == '6': display_stats(stats_to_show); continue
        elif choice == '7': 
            if game_instance:
                game_instance.save_game()
            else:
                print(f"{COLOR_YELLOW}No active game to save.{COLOR_RESET}"); time.sleep(1)
            continue
        elif choice == '8': 
            temp_game = BlackjackGame(settings=current_settings, stats=current_stats) 
            if temp_game.load_game(): 
                game_instance = temp_game 
                current_settings = game_instance.settings 
                current_stats = game_instance.session_stats 
                print(f"{COLOR_GREEN}Starting loaded game...{COLOR_RESET}"); time.sleep(1)
                game_instance.run_game()
                current_stats = game_instance.session_stats 
            continue
        elif choice == '9': 
            print(f"\n{COLOR_MAGENTA}Thanks for playing Python Blackjack! (Refactored){COLOR_RESET}"); break

        if selected_game_mode_enum:
            print(f"\n{COLOR_YELLOW}Starting {selected_game_mode_enum.value}...{COLOR_RESET}"); time.sleep(1)
            current_stats = BlackjackGame._default_stats() 
            
            game_instance = BlackjackGame(game_mode=selected_game_mode_enum, 
                                          settings=current_settings, 
                                          stats=current_stats)
            
            game_instance.run_game()
            current_stats = game_instance.session_stats 

    print(COLOR_RESET) 

# --- Start Game ---
if __name__ == "__main__":
    can_use_color = sys.stdout.isatty()
    if os.name == 'nt': 
        os.system('') 
    
    if not can_use_color:
        print("Running without color support (or cannot detect). ANSI codes will be visible.")
    
    main()
