import random
import time
import os
import sys
import enum
import json
import re
# import shutil # Alternative for terminal size

# --- ANSI Color Codes ---
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_BLACK = "\033[30m"
COLOR_WHITE_BG = "\033[107m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"

# --- Constants ---
SUITS = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
STD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
EUCHRE_RANKS = ['9', '10', 'J', 'Q', 'K', 'A']
BJ_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
WAR_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
EUCHRE_VALUES_PLACEHOLDER = {'9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
AI_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ivan", "Judy", "Kevin", "Laura"]
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 5
CARD_BACK = "░"
AI_STARTING_CHIPS = 100
AI_DEFAULT_BET = 5
SAVE_FILE = "card_games_save.json"
HAND_WIDTH_APPROX = 25
DEFAULT_TERMINAL_WIDTH = 80
WIDE_LAYOUT_THRESHOLD = 100
TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH

# --- Enums ---
class GameType(enum.Enum):
    BLACKJACK = "Blackjack"
    WAR = "War"
    EUCHRE = "Euchre"

class BlackjackGameMode(enum.Enum):
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
    "compliment": ["Nice play!", "Good one.", "Well done.", "Lucky!", "Impressive."],
    "insult": ["Bold move...", "Are you sure?", "Hmm...", "Ouch.", "Risky!"],
    "taunt": ["My luck is turning!", "Feeling confident?", "Easy game!", "You can't beat me!", "Is that all?"],
    "bust": ["Too many!", "Busted!", "Ah, unlucky!", "Greedy!", "Overdid it!"],
    "win": ["Winner!", "Gotcha!", "Too easy.", "My turn!", "I win this time!"],
    "lose": ["Darn!", "You got lucky!", "Next time!", "Argh!"],
    "hit_good": ["Nice hit!", "Good card!", "Looking sharp.", "Calculated risk."],
    "hit_bad": ["Oof, tough luck.", "That didn't help much.", "Getting close...", "Risky!"],
    "stand_good": ["Smart stand.", "Good call.", "Solid play.", "Playing it safe."],
    "stand_bad": ["Standing on that? Bold.", "Feeling brave?", "Hope that holds up!", "Interesting strategy..."],
    "player_bust": ["Busted! Too greedy?", "Ouch, over 21!", "Better luck next time!", "Happens to the best of us."],
    "player_win": ["Congrats!", "You got lucky!", "Nice hand!", "Well played!"],
    "player_blackjack": ["Blackjack! Wow!", "Can't beat that!", "Beginner's luck?"],
    "ai_win": ["Winner!", "Gotcha!", "Too easy.", "Read 'em and weep!", "My turn!", "Dealer's loss is my gain."],
    "ai_bust": ["Darn!", "Too many!", "Argh, busted!", "Miscalculated!", "Pushed my luck."],
    "general_insult": ["Are you even trying?", "My grandma plays better than that.", "Was that intentional?", "Seriously?", "..."]
}

# --- Helper Functions (Global Scope) ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.03, color=COLOR_RESET, newline=True):
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char); sys.stdout.flush(); time.sleep(delay)
    sys.stdout.write(COLOR_RESET)
    if newline: print()

def get_card_color(suit_name):
    return COLOR_RED if suit_name in ['Hearts', 'Diamonds'] else COLOR_BLACK

def create_deck(num_decks=1, ranks=STD_RANKS):
    deck = []
    print(f"{COLOR_DIM}(Creating deck with {len(ranks)} ranks per suit){COLOR_RESET}")
    time.sleep(0.2)
    for _ in range(num_decks):
        for suit_name in SUITS:
            for rank in ranks:
                deck.append((suit_name, SUITS[suit_name], rank))
    print(f"{COLOR_DIM}(Using {num_decks} deck{'s' if num_decks > 1 else ''}){COLOR_RESET}")
    time.sleep(0.5)
    return deck

def calculate_blackjack_value(hand):
    if not hand: return 0
    value = 0; num_aces = 0
    for card in hand:
        if len(card) < 3: continue
        rank = card[2]
        value += BJ_VALUES.get(rank, 0)
        if rank == 'A': num_aces += 1
    while value > 21 and num_aces: value -= 10; num_aces -= 1
    return value

def display_card(card, hidden=False):
    if hidden:
        back = CARD_BACK * 9
        lines = ["┌─────────┐", f"│{back}│", f"│{back}│", f"│{COLOR_DIM} HIDDEN {COLOR_RESET}{COLOR_WHITE_BG}{COLOR_BLACK}│", f"│{back}│", f"│{back}│", "└─────────┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]
    if not isinstance(card, (list, tuple)) or len(card) < 3:
        print(f"{COLOR_RED}Error: Invalid card data format: {card}{COLOR_RESET}")
        lines = ["┌─────────┐", "│  ERROR  │", "│ INVALID │", "│  CARD   │", "│  DATA   │", "│         │", "└─────────┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_RED}{line}{COLOR_RESET}" for line in lines]
    suit_name, suit_symbol, rank = card
    card_color = get_card_color(suit_name); rank_str = rank.ljust(2)
    lines = ["┌─────────┐", f"│ {card_color}{rank_str}{COLOR_BLACK}      │", "│         │", f"│    {card_color}{suit_symbol}{COLOR_BLACK}    │", "│         │", f"│      {card_color}{rank_str}{COLOR_BLACK} │", "└─────────┘"]
    return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_visible_width(text):
    return len(strip_ansi_codes(text))

def center_text(text, width):
    visible_width = get_visible_width(text)
    padding = (width - visible_width) // 2
    if padding < 0: padding = 0
    return " " * padding + text

def shuffle_animation(duration=1.5):
    clear_screen(); print(f"{COLOR_YELLOW}Shuffling Deck...{COLOR_RESET}")
    symbols = ['♠', '♥', '♦', '♣', CARD_BACK, '?']; colors = [COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN]
    width = 40; lines = 5; end_time = time.time() + duration
    while time.time() < end_time:
        output_lines = []
        for _ in range(lines):
            line = "".join(f"{random.choice(colors)}{random.choice(symbols)}{COLOR_RESET}" if random.random() < 0.3 else " " for _ in range(width))
            output_lines.append(line)
        sys.stdout.write(f"\033[{lines}A")
        for line in output_lines: sys.stdout.write(f"\r{line.ljust(width)}\n")
        sys.stdout.flush(); time.sleep(0.05)
    clear_screen(); print(f"{COLOR_GREEN}Deck Shuffled!{COLOR_RESET}"); time.sleep(0.5)

def title_screen_main():
    clear_screen(); title = "Card Game System"; author = "by ShadowHarvy"; screen_width = TERMINAL_WIDTH
    print("\n" * 3); print(f"{COLOR_MAGENTA}{'*' * (screen_width // 2)}{COLOR_RESET}".center(screen_width)); print(center_text(f"{COLOR_GREEN}{COLOR_BOLD}{title}{COLOR_RESET}", screen_width)); print(center_text(f"{COLOR_CYAN}{author}{COLOR_RESET}", screen_width)); print(f"{COLOR_MAGENTA}{'*' * (screen_width // 2)}{COLOR_RESET}".center(screen_width)); print("\n" * 2)
    print(center_text(f"{COLOR_WHITE_BG}{COLOR_RED} A♥ {COLOR_RESET}  {COLOR_WHITE_BG}{COLOR_BLACK} K♠ {COLOR_RESET}  {COLOR_WHITE_BG}{COLOR_RED} Q♦ {COLOR_RESET}  {COLOR_WHITE_BG}{COLOR_BLACK} J♣ {COLOR_RESET}", screen_width)); print("\n" * 2); time.sleep(2.5)

def title_screen_blackjack():
    clear_screen(); title = "B L A C K J A C K"; card_width = 11; screen_width = TERMINAL_WIDTH
    print("\n" * 5); typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_GREEN + COLOR_BOLD); print("\n")
    temp_deck = create_deck(); random.shuffle(temp_deck); card1 = temp_deck.pop() if temp_deck else ('Spades', '♠', 'A'); card2 = temp_deck.pop() if temp_deck else ('Hearts', '♥', 'K')
    card1_lines = display_card(card1); card2_lines = display_card(card2); total_card_width = card_width * 2 + 2; left_padding = (screen_width - total_card_width) // 2; padding_str = " " * left_padding
    for j in range(len(card1_lines)): print(f"{padding_str}{card1_lines[j]}  {card2_lines[j]}")
    print("\n"); time.sleep(1.5)

def title_screen_war():
    clear_screen(); title = "W A R"; card_width = 11; screen_width = TERMINAL_WIDTH
    print("\n" * 5); typing_effect(center_text(title, screen_width), delay=0.1, color=COLOR_RED + COLOR_BOLD); print("\n")
    temp_deck = create_deck(); random.shuffle(temp_deck); card1 = temp_deck.pop() if temp_deck else ('Diamonds', '♦', '7'); card2 = temp_deck.pop() if temp_deck else ('Clubs', '♣', '7')
    card1_lines = display_card(card1); card2_lines = display_card(card2); total_card_width = card_width * 2 + 2; left_padding = (screen_width - total_card_width) // 2; padding_str = " " * left_padding
    for j in range(len(card1_lines)): print(f"{padding_str}{card1_lines[j]}  {card2_lines[j]}")
    print("\n"); time.sleep(1.5)

def title_screen_euchre():
    clear_screen(); title = "E U C H R E"; card_width = 11; screen_width = TERMINAL_WIDTH
    print("\n" * 5); typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_BLUE + COLOR_BOLD); print("\n")
    temp_deck = create_deck(ranks=EUCHRE_RANKS); random.shuffle(temp_deck); card1 = temp_deck.pop() if temp_deck else ('Clubs', '♣', 'J'); card2 = temp_deck.pop() if temp_deck else ('Spades', '♠', 'J')
    card1_lines = display_card(card1); card2_lines = display_card(card2); total_card_width = card_width * 2 + 2; left_padding = (screen_width - total_card_width) // 2; padding_str = " " * left_padding
    for j in range(len(card1_lines)): print(f"{padding_str}{card1_lines[j]}  {card2_lines[j]}")
    print("\n"); time.sleep(1.5)

def display_main_menu():
    print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Game Selection ---{COLOR_RESET}")
    print(f"[{COLOR_CYAN}1{COLOR_RESET}] {GameType.BLACKJACK.value}"); print(f"[{COLOR_CYAN}2{COLOR_RESET}] {GameType.WAR.value}"); print(f"[{COLOR_CYAN}3{COLOR_RESET}] {GameType.EUCHRE.value}")
    print("-" * 25); print(f"[{COLOR_CYAN}R{COLOR_RESET}] Rules (Overall)"); print(f"[{COLOR_CYAN}S{COLOR_RESET}] Settings"); print(f"[{COLOR_CYAN}T{COLOR_RESET}] View Stats"); print(f"[{COLOR_CYAN}V{COLOR_RESET}] Save Current Game"); print(f"[{COLOR_CYAN}L{COLOR_RESET}] Load Game"); print(f"[{COLOR_CYAN}Q{COLOR_RESET}] Quit System"); print("-" * 25)
    while True:
        choice = input(f"{COLOR_YELLOW}Choose a game or option: {COLOR_RESET}").upper()
        if choice in ['1', '2', '3', 'R', 'S', 'T', 'V', 'L', 'Q']: return choice
        else: print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}")

def display_rules_overall():
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- General Info ---{COLOR_RESET}")
    print(f"{COLOR_BLUE}- Select a game from the main menu.{COLOR_RESET}"); print(f"{COLOR_BLUE}- Game-specific rules can be viewed if implemented within the game.{COLOR_RESET}"); print(f"{COLOR_BLUE}- Settings affect new games started after changes.{COLOR_RESET}"); print(f"{COLOR_BLUE}- Stats track progress across sessions if saved/loaded.{COLOR_RESET}")
    print("-" * 25); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

def display_settings_menu(settings):
    while True:
        clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Global Settings ---{COLOR_RESET}")
        print(f"[1] Number of Decks (Blackjack): {COLOR_CYAN}{settings['num_decks']}{COLOR_RESET} (1-8)")
        print(f"[2] Easy Mode (Hints - Blackjack): {COLOR_GREEN if settings['easy_mode'] else COLOR_RED}{settings['easy_mode']}{COLOR_RESET}")
        print(f"[3] Card Counting Cheat (Blackjack): {COLOR_GREEN if settings['card_counting_cheat'] else COLOR_RED}{settings['card_counting_cheat']}{COLOR_RESET}")
        print("[4] Back to Main Menu"); print("-" * 30)
        choice = input(f"{COLOR_YELLOW}Choose setting to change (1-4): {COLOR_RESET}")
        if choice == '1':
            while True:
                try: # *** Corrected Indentation Here ***
                    num = int(input(f"{COLOR_YELLOW}Enter number of decks (1-8): {COLOR_RESET}"))
                    if 1 <= num <= 8: settings['num_decks'] = num; break
                    else: print(f"{COLOR_RED}Invalid number. Please enter 1-8.{COLOR_RESET}")
                except ValueError: print(f"{COLOR_RED}Invalid input. Please enter a number.{COLOR_RESET}") # Correct indentation
        elif choice == '2': settings['easy_mode'] = not settings['easy_mode']; print(f"{COLOR_BLUE}Easy Mode set to: {settings['easy_mode']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '3': settings['card_counting_cheat'] = not settings['card_counting_cheat']; print(f"{COLOR_BLUE}Card Counting Cheat set to: {settings['card_counting_cheat']}{COLOR_RESET}"); time.sleep(1)
        elif choice == '4': break
        else: print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}"); time.sleep(1)

def display_stats(stats):
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Overall Session Statistics ---{COLOR_RESET}")
    bj_stats = stats.get(GameType.BLACKJACK.name, {}); print(f"\n{COLOR_GREEN}Blackjack:{COLOR_RESET}")
    print(f"  Hands Played: {COLOR_CYAN}{bj_stats.get('hands_played', 0)}{COLOR_RESET}"); print(f"  Player Wins: {COLOR_GREEN}{bj_stats.get('player_wins', 0)}{COLOR_RESET}"); print(f"  Dealer Wins: {COLOR_RED}{bj_stats.get('dealer_wins', 0)}{COLOR_RESET}"); print(f"  Pushes: {COLOR_YELLOW}{bj_stats.get('pushes', 0)}{COLOR_RESET}"); print(f"  Player Blackjacks: {COLOR_GREEN}{bj_stats.get('player_blackjacks', 0)}{COLOR_RESET}"); print(f"  Player Busts: {COLOR_RED}{bj_stats.get('player_busts', 0)}{COLOR_RESET}")
    net_chips = bj_stats.get('chips_won', 0) - bj_stats.get('chips_lost', 0); chip_color = COLOR_GREEN if net_chips >= 0 else COLOR_RED; print(f"  Net Chips: {chip_color}{net_chips:+}{COLOR_RESET}")
    war_stats = stats.get(GameType.WAR.name, {}); print(f"\n{COLOR_RED}War:{COLOR_RESET}")
    print(f"  Rounds Played: {COLOR_CYAN}{war_stats.get('rounds_played', 0)}{COLOR_RESET}"); print(f"  Player Wins: {COLOR_GREEN}{war_stats.get('player_wins', 0)}{COLOR_RESET}"); print(f"  AI Wins: {COLOR_RED}{war_stats.get('ai_wins', 0)}{COLOR_RESET}"); print(f"  Wars Fought: {COLOR_YELLOW}{war_stats.get('wars_fought', 0)}{COLOR_RESET}")
    euchre_stats = stats.get(GameType.EUCHRE.name, {}); print(f"\n{COLOR_BLUE}Euchre:{COLOR_RESET}")
    print(f"  Games Played: {COLOR_CYAN}{euchre_stats.get('games_played', 0)}{COLOR_RESET}"); print(f"  Points Scored: {COLOR_GREEN}{euchre_stats.get('points_scored', 0)}{COLOR_RESET}")
    print("-" * 30); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

# --- AI Player Logic ---
def get_ai_decision(ai_type, hand, dealer_up_card_value, running_count=0, true_count=0):
    if ai_type == AIType.COUNTER: return ai_decision_counter(hand, dealer_up_card_value, true_count)
    elif ai_type == AIType.BASIC: return ai_decision_basic(hand, dealer_up_card_value)
    elif ai_type == AIType.CONSERVATIVE: return ai_decision_conservative(hand, dealer_up_card_value)
    elif ai_type == AIType.AGGRESSIVE: return ai_decision_aggressive(hand, dealer_up_card_value)
    elif ai_type == AIType.RANDOM: return random.choice(["hit", "stand"])
    else: print(f"{COLOR_RED}Warning: Unknown AI type {ai_type}. Defaulting to Basic.{COLOR_RESET}"); return ai_decision_basic(hand, dealer_up_card_value)
def ai_decision_basic(hand, dealer_up_card_value):
    hand_value = calculate_blackjack_value(hand); num_aces = sum(1 for _, _, rank in hand if rank == 'A'); is_soft = num_aces > 0 and hand_value - 10 < 11
    if hand_value < 12: return "hit"
    if is_soft:
        if hand_value == 18 and dealer_up_card_value >= 9: return "hit"
        if hand_value >= 19: return "stand"
        if hand_value <= 17: return "hit"
        return "stand"
    else:
        if hand_value >= 17: return "stand"
        if hand_value >= 13 and hand_value <= 16: return "stand" if dealer_up_card_value >= 2 and dealer_up_card_value <= 6 else "hit"
        if hand_value == 12: return "stand" if dealer_up_card_value >= 4 and dealer_up_card_value <= 6 else "hit"
        return "hit"
def ai_decision_conservative(hand, dealer_up_card_value):
    hand_value = calculate_blackjack_value(hand); num_aces = sum(1 for _, _, rank in hand if rank == 'A'); is_soft = num_aces > 0 and hand_value - 10 < 11
    if hand_value < 11: return "hit"
    if is_soft: return "stand" if hand_value >= 18 else "hit"
    else:
        if hand_value >= 15: return "stand"
        if hand_value >= 12 and dealer_up_card_value <= 6: return "stand"
        return "hit"
def ai_decision_aggressive(hand, dealer_up_card_value):
    hand_value = calculate_blackjack_value(hand); num_aces = sum(1 for _, _, rank in hand if rank == 'A'); is_soft = num_aces > 0 and hand_value - 10 < 11
    if hand_value < 13: return "hit"
    if is_soft:
        if hand_value == 18 and dealer_up_card_value not in [2, 7, 8]: return "hit"
        if hand_value >= 19: return "stand"
        return "hit"
    else:
        if hand_value >= 17: return "stand"
        if hand_value == 16 and dealer_up_card_value <= 6 and random.random() < 0.4: return "hit"
        if hand_value >= 12 and dealer_up_card_value >= 7: return "hit"
        if hand_value >= 13 and hand_value <= 16: return "stand"
        if hand_value == 12: return "stand" if dealer_up_card_value >= 4 else "hit"
        return "hit"
def ai_decision_counter(hand, dealer_up_card_value, true_count):
    decision = ai_decision_basic(hand, dealer_up_card_value); hand_value = calculate_blackjack_value(hand)
    if true_count >= 2:
        if decision == "stand" and hand_value in [15, 16] and dealer_up_card_value >= 7: decision = "hit"
    elif true_count <= -1:
        if decision == "hit" and hand_value == 12 and dealer_up_card_value <= 6: decision = "stand"
        elif decision == "hit" and hand_value == 13 and dealer_up_card_value <= 3: decision = "stand"
    return decision
def get_card_count_value(rank):
    if rank in ['2', '3', '4', '5', '6']: return 1
    elif rank in ['10', 'J', 'Q', 'K', 'A']: return -1
    else: return 0
def get_basic_strategy_hint(player_hand, dealer_up_card):
    player_value = calculate_blackjack_value(player_hand); dealer_value = 0
    if dealer_up_card and len(dealer_up_card) > 2: dealer_rank = dealer_up_card[2]; dealer_value = BJ_VALUES.get(dealer_rank, 0);
        if dealer_rank == 'A': dealer_value = 11
    num_aces = sum(1 for _, _, rank in player_hand if rank == 'A'); is_soft = num_aces > 0 and calculate_blackjack_value(player_hand) - 10 < 11
    if len(player_hand) == 2 and len(player_hand[0]) > 2 and len(player_hand[1]) > 2 and player_hand[0][2] == player_hand[1][2]:
        rank = player_hand[0][2]
        if rank == 'A' or rank == '8': return "(Hint: Always split Aces and 8s)"
        if rank == '5' or rank == '10': return "(Hint: Never split 5s or 10s)"
    if is_soft:
        if player_value >= 19: return "(Hint: Stand on soft 19+)"
        if player_value == 18: return "(Hint: Stand vs 2-8, Hit vs 9-A)" if dealer_value != 0 else "(Hint: Stand on soft 18)"
        if player_value <= 17: return "(Hint: Hit soft 17 or less)"
    else:
        if player_value >= 17: return "(Hint: Stand on hard 17+)"
        if player_value >= 13: return "(Hint: Stand vs 2-6, Hit vs 7+)" if dealer_value != 0 else "(Hint: Stand on 13-16)"
        if player_value == 12: return "(Hint: Stand vs 4-6, Hit vs 2,3,7+)" if dealer_value != 0 else "(Hint: Hit hard 12)"
        if player_value <= 11: return "(Hint: Hit or Double Down on 11 or less)"
    return "(Hint: Use Basic Strategy Chart)"

# --- Game Classes ---

class BlackjackGame:
    # (Full BlackjackGame Class from previous version goes here)
    # --- [ Start of BlackjackGame Methods ] ---
    def __init__(self, game_mode=BlackjackGameMode.QUICK_PLAY, settings=None, stats=None): # Use BlackjackGameMode
        self.game_type = GameType.BLACKJACK # Identify game type
        self.deck = []
        self.dealer_hand = []
        self.ai_players = {}
        self.player_chips = 100
        self.player_hands = []
        self.player_bets = []
        self.current_hand_index = 0
        self.blackjack_game_mode = game_mode # Store the specific BJ game mode
        self.settings = settings if settings is not None else self._default_settings()
        self.session_stats = stats if stats is not None else { GameType.BLACKJACK.name: self._default_stats() }
        if GameType.BLACKJACK.name not in self.session_stats: self.session_stats[GameType.BLACKJACK.name] = self._default_stats()
        self.running_count = 0; self.true_count = 0; self.decks_remaining = self.settings['num_decks']
        self._initialize_ai_players()
        self._create_and_shuffle_deck()
    def _default_settings(self): return {'num_decks': 1, 'easy_mode': False, 'card_counting_cheat': False}
    def _default_stats(self): return {'hands_played': 0, 'player_wins': 0, 'dealer_wins': 0, 'pushes': 0, 'player_blackjacks': 0, 'player_busts': 0, 'chips_won': 0, 'chips_lost': 0}
    def _create_and_shuffle_deck(self): self.deck = create_deck(self.settings['num_decks']); random.shuffle(self.deck); self.running_count = 0; self.true_count = 0; self.decks_remaining = self.settings['num_decks']; print(f"{COLOR_DIM}Deck created with {self.settings['num_decks']} deck(s) and shuffled.{COLOR_RESET}"); time.sleep(0.5)
    def _update_count(self, card_rank): self.running_count += get_card_count_value(card_rank); self.decks_remaining = max(0.5, len(self.deck) / 52.0); self.true_count = self.running_count / self.decks_remaining if self.decks_remaining > 0 else self.running_count
    def _initialize_ai_players(self):
        self.ai_players = {}
        if self.blackjack_game_mode == BlackjackGameMode.SOLO: return
        num_ai = random.randint(MIN_AI_PLAYERS, MAX_AI_PLAYERS); available_names = random.sample(AI_NAMES, k=min(len(AI_NAMES), MAX_AI_PLAYERS + 2)); chosen_names = random.sample(available_names, k=num_ai)
        for name in chosen_names: ai_type = random.choice(list(AIType)); chips = AI_STARTING_CHIPS if self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE else 0; self.ai_players[name] = {'hand': [], 'type': ai_type, 'chips': chips, 'current_bet': 0}
    def _ai_place_bets(self):
        if self.blackjack_game_mode != BlackjackGameMode.POKER_STYLE: return
        print(f"\n{COLOR_BLUE}--- AI Players Placing Bets ---{COLOR_RESET}"); time.sleep(0.5)
        for name, ai_data in list(self.ai_players.items()):
            bet_amount = 0
            if ai_data['chips'] >= AI_DEFAULT_BET * 2 and self.true_count >= 1: bet_amount = AI_DEFAULT_BET * 2
            elif ai_data['chips'] >= AI_DEFAULT_BET: bet_amount = AI_DEFAULT_BET
            else: bet_amount = ai_data['chips']
            if bet_amount > 0: ai_data['chips'] -= bet_amount; ai_data['current_bet'] = bet_amount; print(f"{COLOR_BLUE}{name}{COLOR_RESET} bets {COLOR_YELLOW}{bet_amount}{COLOR_RESET} chips. (Remaining: {ai_data['chips']})")
            else: ai_data['current_bet'] = 0; print(f"{COLOR_BLUE}{name}{COLOR_RESET} cannot bet.")
            time.sleep(0.7)
        print("-" * 30)
    def _deal_card(self, hand, update_count=True):
        if not self.deck: print(f"{COLOR_YELLOW}Deck empty, reshuffling...{COLOR_RESET}"); shuffle_animation(); self._create_and_shuffle_deck()
        if not self.deck: sys.exit(f"{COLOR_RED}Critical error: Cannot deal from empty deck.{COLOR_RESET}")
        card = self.deck.pop(); hand.append(card)
        if update_count: self._update_count(card[2])
        return card
    def _ai_chat(self, category, player_action=None):
        if not self.ai_players: return
        if random.random() < 0.25:
            if not self.ai_players: return
            ai_name = random.choice(list(self.ai_players.keys())); chat_list = AI_CHAT.get(category)
            if category == "player_action":
                if player_action == 'hit': chat_list = AI_CHAT.get("hit_good", []) + AI_CHAT.get("hit_bad", [])
                elif player_action == 'stand': chat_list = AI_CHAT.get("stand_good", []) + AI_CHAT.get("stand_bad", [])
                elif player_action == 'double': chat_list = AI_CHAT.get("compliment", []) + AI_CHAT.get("taunt", [])
                elif player_action == 'split': chat_list = AI_CHAT.get("compliment", []) + AI_CHAT.get("insult", [])
                elif player_action == 'surrender': chat_list = AI_CHAT.get("insult", []) + ["Playing it safe, huh?", "Scared money don't make money!"]
                else: chat_list = AI_CHAT.get("compliment", []) + AI_CHAT.get("insult", [])
            if chat_list: message = random.choice(chat_list); print(f"{COLOR_CYAN}[{ai_name}]: {message}{COLOR_RESET}"); time.sleep(1.2)
    def place_bet(self):
        while True:
            try:
                print(f"\n{COLOR_YELLOW}Your chips: {self.player_chips}{COLOR_RESET}")
                if self.player_chips <= 0: print(f"{COLOR_RED}You have no chips left to bet!{COLOR_RESET}"); return False
                bet_input = input(f"Place your initial bet (minimum 1, or 'q' to quit round): ")
                if bet_input.lower() == 'q': return False
                bet = int(bet_input)
                if bet <= 0: print(f"{COLOR_RED}Bet must be positive.{COLOR_RESET}")
                elif bet > self.player_chips: print(f"{COLOR_RED}You don't have enough chips.{COLOR_RESET}")
                else: self.player_hands = [[]]; self.player_bets = [bet]; self.player_chips -= bet; self.current_hand_index = 0; print(f"{COLOR_GREEN}Betting {bet} chips.{COLOR_RESET}"); time.sleep(1); return True
            except ValueError: print(f"{COLOR_RED}Invalid input. Please enter a number or 'q'.{COLOR_RESET}")
            except EOFError: print(f"\n{COLOR_RED}Input error. Returning to menu.{COLOR_RESET}"); return False
    def deal_initial_cards(self):
        print(f"\n{COLOR_BLUE}Dealing cards...{COLOR_RESET}"); time.sleep(0.5)
        self.player_hands = [[] for _ in self.player_bets]; self.dealer_hand = []
        for name in self.ai_players: self.ai_players[name]['hand'] = []
        participants_order = ["Player"]
        if self.blackjack_game_mode != BlackjackGameMode.SOLO: participants_order.extend(list(self.ai_players.keys())) # Use BJ mode
        participants_order.append("Dealer"); hidden_card_lines = display_card(None, hidden=True)
        for round_num in range(2):
            for name in participants_order:
                target_hand = None; display_name = name; is_dealer_hidden_card = (name == "Dealer" and round_num == 0)
                if name == "Player":
                    if not self.player_hands: continue
                    if len(self.player_hands[0]) < 2: target_hand = self.player_hands[0]; display_name = "Player (You)"
                    else: continue
                elif name == "Dealer": target_hand = self.dealer_hand
                else:
                    if name in self.ai_players: target_hand = self.ai_players[name]['hand']
                    else: continue
                if target_hand is not None:
                    print("\r" + " " * 40, end=""); print(f"\r{COLOR_BLUE}Dealing to {display_name}... {COLOR_RESET}", end=""); sys.stdout.flush(); time.sleep(0.15)
                    print("\r" + hidden_card_lines[3], end=""); sys.stdout.flush(); time.sleep(0.2)
                    print("\r" + " " * 40, end=""); print(f"\r{COLOR_BLUE}Dealing to {display_name}... Done.{COLOR_RESET}")
                    self._deal_card(target_hand, update_count=not is_dealer_hidden_card); time.sleep(0.1)
        print(f"\n{COLOR_BLUE}{'-' * 20}{COLOR_RESET}")
    def _offer_insurance(self):
        if not self.player_hands or not self.player_bets: return 0
        if not self.dealer_hand or len(self.dealer_hand) != 2 or len(self.dealer_hand[1]) < 3: return 0
        if self.dealer_hand[1][2] == 'A':
            max_insurance = self.player_bets[0] // 2
            if self.player_chips >= max_insurance and max_insurance > 0:
                while True:
                    ins_choice = input(f"{COLOR_YELLOW}Dealer shows Ace. Insurance? (y/n): {COLOR_RESET}").lower().strip()
                    if ins_choice.startswith('y'): insurance_bet = max_insurance; self.player_chips -= insurance_bet; print(f"{COLOR_GREEN}Placed insurance bet of {insurance_bet} chips.{COLOR_RESET}"); time.sleep(1); return insurance_bet
                    elif ins_choice.startswith('n'): print(f"{COLOR_BLUE}Insurance declined.{COLOR_RESET}"); time.sleep(1); return 0
                    else: print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
            else: print(f"{COLOR_DIM}Dealer shows Ace, but not enough chips for insurance.{COLOR_RESET}"); time.sleep(1)
        return 0
    def _resolve_insurance(self, insurance_bet):
        if insurance_bet > 0:
            if not self.dealer_hand or len(self.dealer_hand) != 2: return False
            dealer_value = calculate_blackjack_value(self.dealer_hand); is_dealer_blackjack = dealer_value == 21
            print(f"\n{COLOR_MAGENTA}--- Resolving Insurance ---{COLOR_RESET}")
            self._update_count(self.dealer_hand[0][2]); self.display_table(hide_dealer=False)
            if is_dealer_blackjack: winnings = insurance_bet * 3; print(f"{COLOR_GREEN}Dealer has Blackjack! Insurance pays {insurance_bet * 2}. You win {winnings} chips back.{COLOR_RESET}"); self.player_chips += winnings
            else: print(f"{COLOR_RED}Dealer does not have Blackjack. Insurance bet lost.{COLOR_RESET}")
            time.sleep(2.5); return is_dealer_blackjack
        return False
    def _offer_even_money(self):
        if not self.player_hands or not self.dealer_hand or len(self.dealer_hand) != 2 or len(self.dealer_hand[1]) < 3: return False
        player_has_bj = len(self.player_hands) == 1 and calculate_blackjack_value(self.player_hands[0]) == 21 and len(self.player_hands[0]) == 2
        dealer_shows_ace = self.dealer_hand[1][2] == 'A'
        if player_has_bj and dealer_shows_ace:
            while True:
                choice = input(f"{COLOR_YELLOW}You have Blackjack, Dealer shows Ace. Take Even Money (1:1 payout)? (y/n): {COLOR_RESET}").lower().strip()
                if choice.startswith('y'): print(f"{COLOR_GREEN}Taking Even Money!{COLOR_RESET}"); return True
                elif choice.startswith('n'): print(f"{COLOR_BLUE}Declining Even Money. Playing out the hand...{COLOR_RESET}"); return False
                else: print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
        return False
    def display_hand(self, player_name, hand, hide_one=False, highlight=False, bet_amount=0, hand_label="", ai_type=None, chips=None, current_bet=None, show_ai_details=False):
        player_color = COLOR_BLUE if player_name not in ["Dealer", "Player (You)"] else COLOR_MAGENTA
        highlight_prefix = f"{COLOR_BOLD}" if highlight else ""; label_suffix = f" ({hand_label})" if hand_label else ""; bet_info = f" | Bet: {bet_amount}" if bet_amount > 0 else ""
        ai_type_info = f" ({ai_type.value})" if ai_type else ""; ai_chip_info = f" | Chips: {chips}" if show_ai_details and chips is not None else ""; ai_bet_info = f" | Betting: {current_bet}" if show_ai_details and current_bet is not None and current_bet > 0 else ""
        header = f"{highlight_prefix}{player_color}--- {player_name}{ai_type_info}{label_suffix}'s Hand{bet_info}{ai_chip_info}{ai_bet_info} ---{COLOR_RESET}"; print(header)
        if not hand: print("[ No cards ]")
        else:
            card_lines = [[] for _ in range(7)]
            for i, card_data in enumerate(hand): is_hidden = hide_one and i == 0; card_str_lines = display_card(card_data, hidden=is_hidden);
                for line_num, line in enumerate(card_str_lines): card_lines[line_num].append(line)
            for line_idx in range(7): print("  ".join(card_lines[line_idx]))
        value_line = ""
        if not hide_one: value = calculate_blackjack_value(hand); status = "";
            if value == 21 and len(hand) == 2: status = f" {COLOR_GREEN}{COLOR_BOLD}BLACKJACK!{COLOR_RESET}"
            elif value > 21: status = f" {COLOR_RED}{COLOR_BOLD}BUST!{COLOR_RESET}"; value_line = f"{COLOR_YELLOW}Value: {value}{status}{COLOR_RESET}"
        elif len(hand) > 1:
            if len(hand[1]) > 2: rank = hand[1][2]; visible_value = VALUES.get(rank, 0); # Use BJ_VALUES
                if rank == 'A': visible_value = 11; value_line = f"{COLOR_YELLOW}Showing: {visible_value}{COLOR_RESET}"
            else: value_line = f"{COLOR_YELLOW}Showing: ? (Invalid card data){COLOR_RESET}"
        elif hide_one: value_line = f"{COLOR_YELLOW}Showing: ?{COLOR_RESET}"
        if value_line: print(value_line)
        visible_header_width = get_visible_width(header); print(f"{player_color}-{COLOR_RESET}" * visible_header_width)
    def display_table(self, hide_dealer=True):
        clear_screen(); title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ {self.blackjack_game_mode.value} ~~~{COLOR_RESET}"; total_bet = sum(self.player_bets) if self.player_bets else 0; count_info = ""
        if self.settings['card_counting_cheat']: count_info = f" | RC: {self.running_count} | TC: {self.true_count:.1f}"
        print(center_text(title, TERMINAL_WIDTH)); print(center_text(f"{COLOR_YELLOW}Your Chips: {self.player_chips} | Your Bet(s): {total_bet}{count_info}{COLOR_RESET}", TERMINAL_WIDTH)); print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")
        self.display_hand("Dealer", self.dealer_hand, hide_one=hide_dealer); print()
        if self.ai_players:
            print(center_text(f"{COLOR_BLUE}--- AI Players ---{COLOR_RESET}", TERMINAL_WIDTH)); show_ai_details = (self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE)
            for name, ai_data in list(self.ai_players.items()):
                 if name not in self.ai_players: continue
                 self.display_hand(name, ai_data['hand'], ai_type=ai_data['type'], chips=ai_data.get('chips'), current_bet=ai_data.get('current_bet'), show_ai_details=show_ai_details); print()
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")
        if self.player_hands:
            print(center_text(f"{COLOR_MAGENTA}--- Your Hands ---{COLOR_RESET}", TERMINAL_WIDTH))
            for i, hand in enumerate(self.player_hands):
                 is_current_hand = (self.current_hand_index >= 0 and i == self.current_hand_index) and (len(self.player_hands) > 1)
                 hand_label = f"Hand {i+1}" if len(self.player_hands) > 1 else ""; bet = self.player_bets[i] if i < len(self.player_bets) else 0
                 self.display_hand("Player (You)", hand, highlight=is_current_hand, bet_amount=bet, hand_label=hand_label); print()
        else: print(center_text(f"{COLOR_DIM}[ No player hands active ]{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")
    def _play_one_hand(self, hand_index):
        if hand_index >= len(self.player_hands): print(f"{COLOR_RED}Error: Invalid hand index.{COLOR_RESET}"); return 'error'
        hand = self.player_hands[hand_index]
        if hand_index >= len(self.player_bets): print(f"{COLOR_RED}Error: Bet index out of sync.{COLOR_RESET}"); bet = 0
        else: bet = self.player_bets[hand_index]
        hand_label = f"Hand {hand_index + 1}" if len(self.player_hands) > 1 else "Your Hand"; can_take_initial_action = len(hand) == 2; player_stood = False
        while calculate_blackjack_value(hand) < 21 and not player_stood:
            self.display_table(hide_dealer=True); hint = ""
            if self.settings['easy_mode'] and len(hand) >= 1 and self.dealer_hand and len(self.dealer_hand) > 1 and len(self.dealer_hand[1]) > 2: hint = get_basic_strategy_hint(hand, self.dealer_hand[1])
            count_hint = ""
            if self.settings['easy_mode'] and self.settings['card_counting_cheat']:
                 if self.true_count >= 2: count_hint = f" {COLOR_GREEN}(High Count: {self.true_count:.1f}){COLOR_RESET}"
                 elif self.true_count <= -1: count_hint = f" {COLOR_RED}(Low Count: {self.true_count:.1f}){COLOR_RESET}"
            print(f"\n--- Playing {COLOR_MAGENTA}{hand_label}{COLOR_RESET} (Value: {calculate_blackjack_value(hand)}) {hint}{count_hint} ---")
            options = ["(h)it", "(s)tand"]; can_double = can_take_initial_action and self.player_chips >= bet
            can_split = (can_take_initial_action and len(hand) == 2 and len(hand[0]) > 2 and len(hand[1]) > 2 and hand[0][2] == hand[1][2] and self.player_chips >= bet and len(self.player_hands) < 4)
            can_surrender = can_take_initial_action
            if can_double: options.append("(d)ouble down"); if can_split: options.append("s(p)lit"); if can_surrender: options.append("su(r)render")
            prompt = f"{COLOR_YELLOW}Choose action: {', '.join(options)}? {COLOR_RESET}"; action = input(prompt).lower().strip()
            if action.startswith('h'):
                new_card = self._deal_card(hand); print(f"\n{COLOR_GREEN}You hit!{COLOR_RESET}"); print(f"{COLOR_BLUE}Received:{COLOR_RESET}");
                for line in display_card(new_card): print(line)
                self._ai_chat("player_action", player_action='hit'); time.sleep(1.5); can_take_initial_action = False
                if calculate_blackjack_value(hand) > 21: self.display_table(hide_dealer=True); print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS!{COLOR_RESET}"); self.session_stats[self.game_type.name]['player_busts'] += 1; self._ai_chat("player_bust"); time.sleep(1.5); return 'bust'
            elif action.startswith('s'): print(f"\n{COLOR_BLUE}You stand on {hand_label}.{COLOR_RESET}"); self._ai_chat("player_action", player_action='stand'); player_stood = True; time.sleep(1);
            elif action.startswith('d') and can_double:
                print(f"\n{COLOR_YELLOW}Doubling down on {hand_label}!{COLOR_RESET}"); self.player_chips -= bet; self.player_bets[hand_index] += bet; print(f"Bet for this hand is now {self.player_bets[hand_index]}. Chips remaining: {self.player_chips}"); time.sleep(1.5)
                new_card = self._deal_card(hand); print(f"{COLOR_BLUE}Received one card:{COLOR_RESET}");
                for line in display_card(new_card): print(line)
                self._ai_chat("player_action", player_action='double'); time.sleep(1.5); self.display_table(hide_dealer=True); final_value = calculate_blackjack_value(hand)
                if final_value > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS after doubling down!{COLOR_RESET}"); self.session_stats[self.game_type.name]['player_busts'] += 1; self._ai_chat("player_bust")
                else: print(f"\n{hand_label} finishes with {final_value} after doubling down.")
                time.sleep(2); return 'double_bust' if final_value > 21 else 'double_stand'
            elif action.startswith('p') and can_split:
                 print(f"\n{COLOR_YELLOW}Splitting {hand[0][2]}s!{COLOR_RESET}"); self.player_chips -= bet; split_card = hand.pop(1); new_hand = [split_card]; self.player_hands.insert(hand_index + 1, new_hand); self.player_bets.insert(hand_index + 1, bet)
                 print(f"Placed additional {bet} bet. Chips remaining: {self.player_chips}"); time.sleep(1.5); print(f"Dealing card to original hand (Hand {hand_index + 1})..."); self._deal_card(hand); time.sleep(0.5); print(f"Dealing card to new hand (Hand {hand_index + 2})..."); self._deal_card(new_hand); time.sleep(1)
                 self._ai_chat("player_action", player_action='split'); self.display_table(hide_dealer=True); time.sleep(1.5); can_take_initial_action = True; continue
            elif action.startswith('r') and can_surrender:
                 print(f"\n{COLOR_YELLOW}Surrendering {hand_label}.{COLOR_RESET}"); refund = bet // 2; print(f"Half your bet ({refund}) is returned."); self.player_chips += refund; self.session_stats[self.game_type.name]['chips_lost'] += (bet - refund); self._ai_chat("player_action", player_action='surrender'); time.sleep(2); return 'surrender'
            else: print(f"{COLOR_RED}Invalid action or action not allowed now.{COLOR_RESET}"); self._ai_chat("general_insult"); time.sleep(1.5)
            if calculate_blackjack_value(hand) == 21 and not player_stood:
                 if not (len(hand) == 2 and can_take_initial_action): print(f"\n{COLOR_GREEN}{hand_label} has 21!{COLOR_RESET}"); time.sleep(1.5)
                 player_stood = True
        return 'stand' if player_stood else 'bust'
    def player_turn(self):
        self.current_hand_index = 0
        while self.current_hand_index < len(self.player_hands):
            if self.current_hand_index >= len(self.player_hands): break
            hand_status = self._play_one_hand(self.current_hand_index)
            if hand_status == 'surrender': self.player_hands[self.current_hand_index] = []
            self.current_hand_index += 1
        self.current_hand_index = -1
        if any(h and calculate_blackjack_value(h) <= 21 for h in self.player_hands): print(f"\n{COLOR_BLUE}Player finishes playing all hands.{COLOR_RESET}"); time.sleep(1.5)
    def ai_turns(self):
        if not self.ai_players: return
        print(f"\n{COLOR_BLUE}--- AI Players' Turns ---{COLOR_RESET}"); time.sleep(1)
        dealer_up_card_value = 0
        if len(self.dealer_hand) > 1 and len(self.dealer_hand[1]) > 2: dealer_up_rank = self.dealer_hand[1][2]; dealer_up_card_value = 11 if dealer_up_rank == 'A' else VALUES.get(dealer_up_rank, 0)
        for name, ai_data in list(self.ai_players.items()):
            if name not in self.ai_players: continue
            hand = ai_data['hand']; ai_type = ai_data['type']
            if self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE and ai_data.get('current_bet', 0) == 0: print(f"{COLOR_DIM}{name} did not bet this round.{COLOR_RESET}"); time.sleep(0.5); continue
            self.display_table(hide_dealer=True); print(f"\n{COLOR_BLUE}{name}'s turn ({ai_type.value})...{COLOR_RESET}"); time.sleep(1.5)
            while True:
                current_value = calculate_blackjack_value(hand)
                if current_value > 21: time.sleep(1); break
                decision = get_ai_decision(ai_type, hand, dealer_up_card_value, self.running_count, self.true_count)
                print(f"{name} ({ai_type.value}) decides to {COLOR_YELLOW}{decision}{COLOR_RESET}..."); time.sleep(1.2)
                if decision == "hit":
                    print(f"{name} {COLOR_GREEN}hits{COLOR_RESET}..."); time.sleep(0.8)
                    self._deal_card(hand); self.display_table(hide_dealer=True); time.sleep(1.5)
                    if calculate_blackjack_value(hand) > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}{name} BUSTS!{COLOR_RESET}"); self._ai_chat("ai_bust"); time.sleep(1.5); break
                else: print(f"{name} {COLOR_BLUE}stands{COLOR_RESET}."); time.sleep(1); break
            if list(self.ai_players.keys())[-1] != name or True: print(f"{COLOR_DIM}{'-' * 15}{COLOR_RESET}"); time.sleep(1)
    def dealer_turn(self):
        print(f"\n{COLOR_MAGENTA}--- Dealer's Turn ---{COLOR_RESET}"); time.sleep(1)
        if len(self.dealer_hand) == 2: self._update_count(self.dealer_hand[0][2])
        self.display_table(hide_dealer=False)
        while calculate_blackjack_value(self.dealer_hand) < 17:
            print(f"{COLOR_MAGENTA}Dealer must hit...{COLOR_RESET}"); time.sleep(1.5)
            new_card = self._deal_card(self.dealer_hand); print(f"{COLOR_MAGENTA}Dealer receives:{COLOR_RESET}");
            for line in display_card(new_card): print(line)
            time.sleep(1.5); self.display_table(hide_dealer=False)
            if calculate_blackjack_value(self.dealer_hand) > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}Dealer BUSTS!{COLOR_RESET}"); time.sleep(1.5); return
        dealer_value = calculate_blackjack_value(self.dealer_hand)
        if dealer_value <= 21: print(f"{COLOR_MAGENTA}Dealer stands with {dealer_value}.{COLOR_RESET}")
        time.sleep(2)
    def determine_winner(self):
        clear_screen(); print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Round Results ---{COLOR_RESET}"); time.sleep(1)
        dealer_value = calculate_blackjack_value(self.dealer_hand) if self.dealer_hand else 0
        dealer_blackjack = dealer_value == 21 and len(self.dealer_hand) == 2
        print(f"\n{COLOR_BLUE}--- Final Hands ---{COLOR_RESET}"); self.display_hand("Dealer", self.dealer_hand, hide_one=False); print()
        if self.ai_players:
            print(f"{COLOR_BLUE}--- AI Players Final Hands ---{COLOR_RESET}"); show_ai_details = (self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE)
            for name, ai_data in list(self.ai_players.items()):
                 if name not in self.ai_players: continue
                 self.display_hand(name, ai_data['hand'], ai_type=ai_data['type'], chips=ai_data.get('chips'), current_bet=ai_data.get('current_bet'), show_ai_details=show_ai_details); print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")
        if self.player_hands:
            print(f"{COLOR_MAGENTA}--- Your Final Hands ---{COLOR_RESET}"); self.current_hand_index = -1
            for i, hand in enumerate(self.player_hands):
                 if not hand: continue
                 hand_label = f"Hand {i+1}" if len(self.player_hands) > 1 else ""; bet = self.player_bets[i] if i < len(self.player_bets) else 0
                 self.display_hand("Player (You)", hand, bet_amount=bet, hand_label=hand_label); print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")
        time.sleep(2.5)
        print(f"\n{COLOR_YELLOW}--- Your Hand Results ---{COLOR_RESET}"); player_won_any = False
        if not self.player_hands: print(f"{COLOR_DIM}[ No hands played this round ]{COLOR_RESET}")
        else:
            for i, hand in enumerate(self.player_hands):
                if not hand: print(f"\n{COLOR_YELLOW}Hand {i+1}: Surrendered{COLOR_RESET}"); continue
                if i >= len(self.player_bets): continue
                player_value = calculate_blackjack_value(hand); bet = self.player_bets[i]; hand_label = f"Hand {i+1}" if len(self.player_hands) > 1 else "Your Hand"
                is_initial_hand_blackjack = (i == 0 and len(self.player_hands) == 1 and player_value == 21 and len(hand) == 2)
                player_21 = player_value == 21; print(f"\n{COLOR_YELLOW}Result for {hand_label} (Bet: {bet}):{COLOR_RESET}"); payout = 0; result_text = ""; chips_change = 0; player_wins_this_hand = False
                stats_key = self.game_type.name # Key for stats dictionary
                if player_value > 21: result_text = f"{COLOR_RED}{hand_label} busted! Lose {bet} chips.{COLOR_RESET}"; payout = 0; chips_change = -bet; self.session_stats[stats_key]['dealer_wins'] += 1
                elif is_initial_hand_blackjack and not dealer_blackjack: blackjack_payout = int(bet * 1.5); total_win = bet + blackjack_payout; result_text = f"{COLOR_GREEN}{COLOR_BOLD}Blackjack! Win {total_win} chips!{COLOR_RESET}"; payout = total_win; chips_change = blackjack_payout; self.session_stats[stats_key]['player_wins'] += 1; self.session_stats[stats_key]['player_blackjacks'] += 1; player_wins_this_hand = True
                elif player_21 and dealer_blackjack: result_text = f"{COLOR_RED}Dealer BJ beats 21! Lose {bet} chips.{COLOR_RESET}"; payout = 0; chips_change = -bet; self.session_stats[stats_key]['dealer_wins'] += 1
                elif dealer_blackjack and not player_21: result_text = f"{COLOR_RED}Dealer Blackjack! Lose {bet} chips.{COLOR_RESET}"; payout = 0; chips_change = -bet; self.session_stats[stats_key]['dealer_wins'] += 1
                elif dealer_value > 21: result_text = f"{COLOR_GREEN}Dealer busts! Win {bet * 2} chips!{COLOR_RESET}"; payout = bet * 2; chips_change = bet; self.session_stats[stats_key]['player_wins'] += 1; player_wins_this_hand = True
                elif player_value > dealer_value: result_text = f"{COLOR_GREEN}{hand_label} wins! Win {bet * 2} chips!{COLOR_RESET}"; payout = bet * 2; chips_change = bet; self.session_stats[stats_key]['player_wins'] += 1; player_wins_this_hand = True
                elif player_value == dealer_value:
                     if is_initial_hand_blackjack and dealer_blackjack: result_text = f"{COLOR_YELLOW}Push! Both BJ. Bet returned.{COLOR_RESET}"
                     else: result_text = f"{COLOR_YELLOW}Push! Bet returned.{COLOR_RESET}"
                     payout = bet; chips_change = 0; self.session_stats[stats_key]['pushes'] += 1
                else: result_text = f"{COLOR_RED}Dealer wins. Lose {bet} chips.{COLOR_RESET}"; payout = 0; chips_change = -bet; self.session_stats[stats_key]['dealer_wins'] += 1
                print(result_text); self.player_chips += payout
                if chips_change > 0: self.session_stats[stats_key]['chips_won'] += chips_change
                elif chips_change < 0: self.session_stats[stats_key]['chips_lost'] += abs(chips_change)
                if player_wins_this_hand: player_won_any = True
                time.sleep(1.5)
            if player_won_any: self._ai_chat("player_win")
            elif all(not h or calculate_blackjack_value(h) > 21 for h in self.player_hands): pass
            else: self._ai_chat("taunt")
        print("-" * 30); print(f"{COLOR_YELLOW}Your chip total after round: {self.player_chips}{COLOR_RESET}"); print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}"); time.sleep(2.5)
        if self.ai_players:
            print(f"\n{COLOR_BLUE}--- AI Player Results ---{COLOR_RESET}")
            for name, ai_data in list(self.ai_players.items()):
                if name not in self.ai_players: continue
                hand = ai_data['hand']; ai_value = calculate_blackjack_value(hand); ai_blackjack = ai_value == 21 and len(hand) == 2
                ai_bet = ai_data.get('current_bet', 0); result = ""; result_color = COLOR_RESET; ai_payout = 0
                if ai_bet > 0:
                    if ai_value > 21: result = "Busted!"; result_color = COLOR_RED; ai_payout = 0 # Chat handled in ai_turns
                    elif ai_blackjack and not dealer_blackjack: result = "Blackjack! (Wins)"; result_color = COLOR_GREEN; ai_payout = ai_bet + int(ai_bet * 1.5); self._ai_chat("ai_win")
                    elif dealer_blackjack and not ai_blackjack: result = "Loses (vs Dealer BJ)"; result_color = COLOR_RED; ai_payout = 0
                    elif dealer_value > 21: result = "Wins (Dealer Bust)"; result_color = COLOR_GREEN; ai_payout = ai_bet * 2; self._ai_chat("ai_win")
                    elif ai_value > dealer_value: result = f"Wins ({ai_value} vs {dealer_value})"; result_color = COLOR_GREEN; ai_payout = ai_bet * 2; self._ai_chat("ai_win")
                    elif ai_value == dealer_value:
                         if ai_blackjack and dealer_blackjack: result = "Push (Both BJ)"
                         elif ai_blackjack: result = "Blackjack! (Wins vs 21)" ; result_color = COLOR_GREEN; ai_payout = ai_bet + int(ai_bet * 1.5); self._ai_chat("ai_win")
                         else: result = f"Push ({ai_value})"
                         if "Push" in result: result_color = COLOR_YELLOW; ai_payout = ai_bet
                    else: result = f"Loses ({ai_value} vs {dealer_value})" ; result_color = COLOR_RED; ai_payout = 0
                    if self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE: # Use BJ mode
                        ai_data['chips'] += ai_payout; result += f" | Chips: {ai_data['chips']}"
                        if ai_data['chips'] <= 0: print(f"{COLOR_RED}{name} ran out of chips and leaves the table!{COLOR_RESET}"); del self.ai_players[name]; time.sleep(1); continue
                else: result = "Did not bet"; result_color = COLOR_DIM
                print(f"{COLOR_BLUE}{name} ({ai_data['type'].value}){COLOR_RESET}: {result_color}{result}{COLOR_RESET}"); time.sleep(0.6)
            print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")
    def manage_ai_players(self):
        if self.blackjack_game_mode == BlackjackGameMode.SOLO: return # Use BJ mode
        print(f"\n{COLOR_YELLOW}Checking table activity...{COLOR_RESET}"); time.sleep(1); activity = False
        for name in list(self.ai_players.keys()):
             leave_chance = 0.25 if len(self.ai_players) >= MAX_AI_PLAYERS else 0.15
             if len(self.ai_players) > MIN_AI_PLAYERS and random.random() < leave_chance:
                 if name in self.ai_players: del self.ai_players[name]
                 print(f"{COLOR_RED}{name} has left the table.{COLOR_RESET}"); activity = True; time.sleep(0.8)
        available_spots = MAX_AI_PLAYERS - len(self.ai_players)
        potential_new_players = [n for n in AI_NAMES if n not in self.ai_players]
        join_chance = 0.4 if len(self.ai_players) < MAX_AI_PLAYERS / 2 else 0.25
        if available_spots > 0 and potential_new_players and random.random() < join_chance:
             num_joining = random.randint(1, min(available_spots, len(potential_new_players)))
             for _ in range(num_joining):
                 if not potential_new_players: break
                 new_player_name = random.choice(potential_new_players); potential_new_players.remove(new_player_name)
                 new_ai_type = random.choice(list(AIType))
                 new_chips = AI_STARTING_CHIPS if self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE else 0 # Use BJ mode
                 self.ai_players[new_player_name] = {'hand': [], 'type': new_ai_type, 'chips': new_chips, 'current_bet': 0}
                 chip_info = f" with {new_chips} chips" if self.blackjack_game_mode == BlackjackGameMode.POKER_STYLE else "" # Use BJ mode
                 print(f"{COLOR_GREEN}{new_player_name} ({new_ai_type.value}) has joined the table{chip_info}!{COLOR_RESET}"); activity = True; time.sleep(0.8)
        if not activity: print(f"{COLOR_DIM}The table remains the same.{COLOR_RESET}"); time.sleep(1)
    def play_round(self):
        clear_screen(); print(f"{COLOR_MAGENTA}--- Starting New Round ({self.blackjack_game_mode.value}) ---{COLOR_RESET}") # Use BJ mode
        self.player_hands = []; self.player_bets = []; self.current_hand_index = 0
        self.session_stats[self.game_type.name]['hands_played'] += 1 # Use game_type
        if not self.place_bet():
             if self.player_chips <= 0: print(f"\n{COLOR_RED}Out of chips!{COLOR_RESET}"); time.sleep(2); return 'game_over'
             else: print(f"{COLOR_YELLOW}Returning to menu...{COLOR_RESET}"); time.sleep(1.5); return 'quit'
        self._ai_place_bets()
        max_potential_cards = (1 + len(self.ai_players)) * 5 + 5
        if len(self.deck) < max_potential_cards: print(f"{COLOR_YELLOW}Deck low, reshuffling...{COLOR_RESET}"); shuffle_animation(); self._create_and_shuffle_deck()
        else: print(f"{COLOR_YELLOW}Preparing next hand...{COLOR_RESET}"); time.sleep(0.7); clear_screen()
        self.deal_initial_cards(); self.display_table(hide_dealer=True)
        insurance_bet = self._offer_insurance()
        if self._offer_even_money():
             payout = self.player_bets[0]; self.player_chips += payout * 2
             self.session_stats[self.game_type.name]['player_wins'] += 1; self.session_stats[self.game_type.name]['player_blackjacks'] += 1; self.session_stats[self.game_type.name]['chips_won'] += payout
             print(f"{COLOR_GREEN}Paid {payout} chips. Round over.{COLOR_RESET}"); time.sleep(2); self.dealer_turn(); self.determine_winner(); return True
        dealer_had_blackjack = self._resolve_insurance(insurance_bet)
        is_player_blackjack = False
        if self.player_hands and len(self.player_hands[0]) == 2: initial_player_hand = self.player_hands[0]; is_player_blackjack = calculate_blackjack_value(initial_player_hand) == 21
        if dealer_had_blackjack and not is_player_blackjack: print(f"{COLOR_RED}Dealer Blackjack. Round over.{COLOR_RESET}"); time.sleep(2); self.determine_winner(); return True
        if is_player_blackjack and not dealer_had_blackjack: print(f"\n{COLOR_GREEN}{COLOR_BOLD}Blackjack!{COLOR_RESET}"); time.sleep(1.5); self.ai_turns(); self.dealer_turn(); self.determine_winner(); return True
        if not is_player_blackjack and not dealer_had_blackjack:
            self.player_turn(); player_busted_all = all(not h or calculate_blackjack_value(h) > 21 for h in self.player_hands)
            if not player_busted_all: self.ai_turns(); self.dealer_turn()
            else:
                print(f"\n{COLOR_RED}All your hands busted or surrendered!{COLOR_RESET}")
                if any(ai.get('current_bet', 0) > 0 for ai in self.ai_players.values()): print(f"{COLOR_DIM}Dealer plays for AI...{COLOR_RESET}"); self.dealer_turn()
                else: print(f"\n{COLOR_MAGENTA}--- Dealer reveals ---{COLOR_RESET}"); time.sleep(1);
                      if len(self.dealer_hand) > 0 and self.dealer_hand[0]: self._update_count(self.dealer_hand[0][2]); self.display_table(hide_dealer=False); time.sleep(1.5)
        self.determine_winner()
        if self.player_chips <= 0: print(f"\n{COLOR_RED}You've run out of chips! Game Over.{COLOR_RESET}"); time.sleep(2.5); return 'game_over'
        self.manage_ai_players()
        return True
    def run_game(self):
        if not self.deck: self._create_and_shuffle_deck()
        while True:
            round_result = self.play_round()
            if round_result == 'game_over': print(f"{COLOR_YELLOW}Returning to main menu...{COLOR_RESET}"); time.sleep(2); break
            elif round_result == 'quit': break
            elif round_result is True:
                 print(f"\n{COLOR_YELLOW}Your current chips: {self.player_chips}{COLOR_RESET}")
                 if self.blackjack_game_mode != BlackjackGameMode.SOLO and not self.ai_players: print(f"{COLOR_YELLOW}All AI players have left or busted out!{COLOR_RESET}"); input("Press Enter to return to menu..."); break
                 next_round = input(f"Press Enter for next round, or 'q' to return to menu... ").lower()
                 if next_round == 'q': break
            else: print(f"{COLOR_RED}Unexpected round result. Returning to menu.{COLOR_RESET}"); break
        clear_screen()
    # Remove save/load from within BlackjackGame if handled globally
    # def save_game(self): ...
    # def load_game(self): ...

# <<< WarGame Class >>>
class WarGame:
    def __init__(self, settings=None, stats=None):
        self.game_type = GameType.WAR
        self.settings = settings if settings is not None else {'num_decks': 1} # War usually uses 1 deck
        # Initialize War stats within the main stats dictionary
        self.session_stats = stats if stats is not None else { GameType.WAR.name: self._default_stats() }
        if GameType.WAR.name not in self.session_stats:
            self.session_stats[GameType.WAR.name] = self._default_stats()

        self.player_deck = []
        self.ai_deck = []
        self.player_card = None
        self.ai_card = None
        self.spoils = [] # Cards in the middle during war

    def _default_stats(self):
        return {'rounds_played': 0, 'player_wins': 0, 'ai_wins': 0, 'wars_fought': 0}

    def _deal_decks(self):
        """Deals the deck(s) evenly between player and AI."""
        print(f"{COLOR_YELLOW}Dealing cards for War...{COLOR_RESET}")
        full_deck = create_deck(self.settings.get('num_decks', 1), ranks=STD_RANKS) # Use standard ranks
        random.shuffle(full_deck)
        self.player_deck = full_deck[::2] # Deal alternating cards
        self.ai_deck = full_deck[1::2]
        print(f"Dealt {len(self.player_deck)} cards to Player and {len(self.ai_deck)} cards to AI.")
        time.sleep(1)

    def _compare_cards(self, card1, card2):
        """Compares two cards based on War values."""
        val1 = WAR_VALUES.get(card1[2], 0) if card1 else 0
        val2 = WAR_VALUES.get(card2[2], 0) if card2 else 0
        if val1 > val2: return 1 # Player wins
        elif val2 > val1: return -1 # AI wins
        else: return 0 # War

    def _display_war_table(self):
        """Displays the current state of the War table."""
        clear_screen()
        title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ {self.game_type.value} ~~~{COLOR_RESET}"
        print(center_text(title, TERMINAL_WIDTH))
        print(center_text(f"{COLOR_YELLOW}Player Cards: {len(self.player_deck)} | AI Cards: {len(self.ai_deck)}{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}\n")

        # Display cards being played
        lines1 = display_card(self.player_card) if self.player_card else [" " * 11] * 7
        lines2 = display_card(self.ai_card) if self.ai_card else [" " * 11] * 7

        # Calculate padding to center the two cards
        total_width = 11 * 2 + 10 # 2 cards + 10 spaces for "VS"
        padding = (TERMINAL_WIDTH - total_width) // 2
        if padding < 0: padding = 0
        padding_str = " " * padding
        vs_str = f"{COLOR_RED}{COLOR_BOLD} V S {COLOR_RESET}"

        print(center_text(f"{COLOR_MAGENTA}Player{COLOR_RESET}", TERMINAL_WIDTH // 2 - 5) + " " * 10 + center_text(f"{COLOR_BLUE}AI{COLOR_RESET}", TERMINAL_WIDTH // 2 - 5))
        for i in range(7):
            print(f"{padding_str}{lines1[i]}    {vs_str if i == 3 else '    '}    {lines2[i]}")
        print()

        if self.spoils:
            print(center_text(f"{COLOR_YELLOW}Spoils: {len(self.spoils)} cards{COLOR_RESET}", TERMINAL_WIDTH))

        print(f"\n{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")


    def play_round(self):
        """Plays one round (battle or war) of War."""
        if not self.player_deck or not self.ai_deck:
            return False # Game over if someone is out of cards

        self.session_stats[self.game_type.name]['rounds_played'] += 1
        self.spoils = [] # Clear spoils from previous round

        self.player_card = self.player_deck.pop(0)
        self.ai_card = self.ai_deck.pop(0)
        self.spoils.extend([self.player_card, self.ai_card])

        self._display_war_table()
        time.sleep(1) # Pause to see cards

        result = self._compare_cards(self.player_card, self.ai_card)

        while result == 0: # It's War!
            print(f"\n{COLOR_RED}{COLOR_BOLD}****** W A R ! ******{COLOR_RESET}")
            self.session_stats[self.game_type.name]['wars_fought'] += 1
            time.sleep(1)

            # Each player puts down 3 cards (or fewer if they don't have enough)
            player_war_cards = []
            ai_war_cards = []
            for _ in range(3):
                if self.player_deck: player_war_cards.append(self.player_deck.pop(0))
                if self.ai_deck: ai_war_cards.append(self.ai_deck.pop(0))

            self.spoils.extend(player_war_cards)
            self.spoils.extend(ai_war_cards)

            print(f"Player puts down {len(player_war_cards)} card(s) face down.")
            print(f"AI puts down {len(ai_war_cards)} card(s) face down.")
            time.sleep(1.5)

            # Check if anyone ran out during the face-down part
            if not self.player_deck or not self.ai_deck:
                # Assign remaining spoils randomly or based on last comparison?
                # Simplest: Last player with cards gets spoils? Or split? Let's give to player who didn't run out.
                if not self.player_deck: self.ai_deck.extend(self.spoils)
                else: self.player_deck.extend(self.spoils)
                self.spoils = []
                print(f"{COLOR_YELLOW}A player ran out of cards during War!{COLOR_RESET}")
                time.sleep(1)
                return False # Game likely over

            # Flip the next card
            self.player_card = self.player_deck.pop(0)
            self.ai_card = self.ai_deck.pop(0)
            self.spoils.extend([self.player_card, self.ai_card])
            self._display_war_table() # Show the war cards
            time.sleep(1)
            result = self._compare_cards(self.player_card, self.ai_card)
            # Loop continues if result is 0 again

        # Determine winner of the battle/war
        random.shuffle(self.spoils) # Shuffle spoils before adding
        if result == 1: # Player wins
            print(f"\n{COLOR_GREEN}Player wins {len(self.spoils)} cards!{COLOR_RESET}")
            self.player_deck.extend(self.spoils)
            self.session_stats[self.game_type.name]['player_wins'] += 1
        elif result == -1: # AI wins
            print(f"\n{COLOR_RED}AI wins {len(self.spoils)} cards!{COLOR_RESET}")
            self.ai_deck.extend(self.spoils)
            self.session_stats[self.game_type.name]['ai_wins'] += 1

        self.spoils = []
        self.player_card = None
        self.ai_card = None
        time.sleep(1.5)
        return True # Round completed

    def run_game(self):
        """Runs the main game loop for War."""
        title_screen_war()
        self._deal_decks()

        while self.player_deck and self.ai_deck:
            input(f"{COLOR_YELLOW}Press Enter to play next round...{COLOR_RESET}")
            if not self.play_round():
                break # Game ended mid-round (e.g., ran out during war)

        # Determine final winner
        clear_screen()
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- GAME OVER ---{COLOR_RESET}")
        if len(self.player_deck) > len(self.ai_deck):
            print(f"{COLOR_GREEN}Player wins the War with {len(self.player_deck)} cards!{COLOR_RESET}")
        elif len(self.ai_deck) > len(self.player_deck):
            print(f"{COLOR_RED}AI wins the War with {len(self.ai_deck)} cards!{COLOR_RESET}")
        else:
            print(f"{COLOR_YELLOW}The War ends in a draw?! (Shouldn't happen with odd spoils){COLOR_RESET}")

        print("\nFinal Stats for this Game:")
        print(f"  Rounds Played: {self.session_stats[self.game_type.name]['rounds_played']}")
        print(f"  Player Wins: {self.session_stats[self.game_type.name]['player_wins']}")
        print(f"  AI Wins: {self.session_stats[self.game_type.name]['ai_wins']}")
        print(f"  Wars Fought: {self.session_stats[self.game_type.name]['wars_fought']}")
        input(f"\n{COLOR_YELLOW}Press Enter to return to main menu...{COLOR_RESET}")
        clear_screen()

# <<< EuchreGame Class (Placeholder) >>>
class EuchreGame:
    def __init__(self, settings=None, stats=None):
        self.game_type = GameType.EUCHRE
        self.settings = settings if settings is not None else {} # Add Euchre specific settings?
        # Initialize Euchre stats
        self.session_stats = stats if stats is not None else { GameType.EUCHRE.name: self._default_stats() }
        if GameType.EUCHRE.name not in self.session_stats:
            self.session_stats[GameType.EUCHRE.name] = self._default_stats()
        # Add Euchre specific game state variables here (players, hands, trump, score, etc.)
        print(f"{COLOR_YELLOW}DEBUG: EuchreGame initialized (placeholder).{COLOR_RESET}")

    def _default_stats(self):
        # Define stats relevant to Euchre
        return {'games_played': 0, 'points_scored': 0, 'tricks_taken': 0, 'euchres': 0}

    def run_game(self):
        """Placeholder for running a game of Euchre."""
        title_screen_euchre()
        print(f"\n{COLOR_YELLOW}Euchre game logic not yet implemented!{COLOR_RESET}")
        input(f"\n{COLOR_YELLOW}Press Enter to return to main menu...{COLOR_RESET}")
        clear_screen()
        # Update placeholder stats
        self.session_stats[self.game_type.name]['games_played'] += 1


# --- Main Application Logic ---
def main():
    """Main function to run the application."""
    global TERMINAL_WIDTH
    try:
        TERMINAL_WIDTH = os.get_terminal_size().columns
    except OSError:
        print(f"{COLOR_YELLOW}Could not detect terminal size. Using default width: {DEFAULT_TERMINAL_WIDTH}{COLOR_RESET}")
        TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH; time.sleep(1.5)

    game_instance = None
    # Load settings/stats once at start if they exist
    current_settings, current_stats = load_global_state()

    try:
        title_screen_main()
        while True:
            choice = display_main_menu()
            game_type_to_start = None

            if choice == '1': game_type_to_start = GameType.BLACKJACK
            elif choice == '2': game_type_to_start = GameType.WAR
            elif choice == '3': game_type_to_start = GameType.EUCHRE # Handle Euchre choice
            # Add elif for other game numbers
            elif choice == 'R': display_rules_overall(); continue
            elif choice == 'S': display_settings_menu(current_settings); continue # Settings apply globally
            elif choice == 'T': display_stats(current_stats); continue
            elif choice == 'V': save_game_state(game_instance, current_stats, current_settings); continue # Save current game if active
            elif choice == 'L': # Load Game
                 loaded_game, loaded_stats, loaded_settings = load_game_state()
                 if loaded_game:
                      game_instance = loaded_game
                      current_stats = loaded_stats
                      current_settings = loaded_settings
                      print(f"{COLOR_GREEN}Starting loaded {game_instance.game_type.value} game...{COLOR_RESET}"); time.sleep(1)
                      game_instance.run_game()
                      # Update global stats after loaded game finishes
                      current_stats = game_instance.session_stats
                      game_instance = None # Clear instance after game finishes
                 continue # Go back to menu after load attempt
            elif choice == 'Q':
                print(f"\n{COLOR_MAGENTA}Thanks for playing! Goodbye!{COLOR_RESET}"); break

            if game_type_to_start:
                 print(f"\n{COLOR_YELLOW}Starting {game_type_to_start.value}...{COLOR_RESET}"); time.sleep(1)
                 # Ensure stats dictionary has an entry for the game
                 if game_type_to_start.name not in current_stats:
                      # Initialize stats for the specific game if missing
                      if game_type_to_start == GameType.BLACKJACK: current_stats[game_type_to_start.name] = BlackjackGame._default_stats(None)
                      elif game_type_to_start == GameType.WAR: current_stats[game_type_to_start.name] = WarGame._default_stats(None)
                      elif game_type_to_start == GameType.EUCHRE: current_stats[game_type_to_start.name] = EuchreGame._default_stats(None)

                 if game_type_to_start == GameType.BLACKJACK:
                     bj_mode = display_blackjack_menu()
                     if bj_mode:
                         bj_stats = current_stats.setdefault(GameType.BLACKJACK.name, BlackjackGame._default_stats(None))
                         game_instance = BlackjackGame(game_mode=bj_mode, settings=current_settings, stats=bj_stats)
                         game_instance.player_chips = 100
                         game_instance.run_game()
                         current_stats[GameType.BLACKJACK.name] = game_instance.session_stats
                         game_instance = None
                 elif game_type_to_start == GameType.WAR:
                      war_stats = current_stats.setdefault(GameType.WAR.name, WarGame._default_stats(None))
                      game_instance = WarGame(settings=current_settings, stats=war_stats)
                      game_instance.run_game()
                      current_stats[GameType.WAR.name] = game_instance.session_stats
                      game_instance = None
                 elif game_type_to_start == GameType.EUCHRE:
                      euchre_stats = current_stats.setdefault(GameType.EUCHRE.name, EuchreGame._default_stats(None))
                      game_instance = EuchreGame(settings=current_settings, stats=euchre_stats)
                      game_instance.run_game() # Run the placeholder game
                      current_stats[GameType.EUCHRE.name] = game_instance.session_stats
                      game_instance = None
                 # Add elif for other games

    except KeyboardInterrupt: print(f"\n{COLOR_RED}Game interrupted. Exiting.{COLOR_RESET}")
    except Exception as e:
         print(f"\n{COLOR_RED}An unexpected error occurred: {e}{COLOR_RESET}")
         import traceback; traceback.print_exc()
    finally: print(COLOR_RESET)

def display_blackjack_menu():
     """Displays sub-menu for Blackjack modes."""
     print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Blackjack Modes ---{COLOR_RESET}")
     print(f"[{COLOR_CYAN}1{COLOR_RESET}] {BlackjackGameMode.QUICK_PLAY.value}")
     print(f"[{COLOR_CYAN}2{COLOR_RESET}] {BlackjackGameMode.SOLO.value}")
     print(f"[{COLOR_CYAN}3{COLOR_RESET}] {BlackjackGameMode.POKER_STYLE.value}")
     print(f"[{COLOR_CYAN}4{COLOR_RESET}] Back to Main Menu")
     print("-" * 30)
     while True:
         choice = input(f"{COLOR_YELLOW}Choose Blackjack mode (1-4): {COLOR_RESET}")
         if choice == '1': return BlackjackGameMode.QUICK_PLAY
         elif choice == '2': return BlackjackGameMode.SOLO
         elif choice == '3': return BlackjackGameMode.POKER_STYLE
         elif choice == '4': return None # Signal to go back
         else: print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}")

def save_global_state(stats, settings):
     """Saves overall stats and settings (not active game)."""
     state = {"session_stats": stats, "settings": settings}
     try:
         with open(SAVE_FILE, 'w') as f: json.dump(state, f, indent=4)
         print(f"{COLOR_GREEN}Overall stats/settings saved to {SAVE_FILE}{COLOR_RESET}")
     except IOError as e: print(f"{COLOR_RED}Error saving state: {e}{COLOR_RESET}")
     time.sleep(1.5)

def load_global_state():
     """Loads overall stats and settings."""
     default_settings = BlackjackGame._default_settings(None) # Base default settings on BJ
     # Initialize default stats structure for all known games
     default_stats = {}
     for game_t in GameType:
         if game_t == GameType.BLACKJACK: default_stats[game_t.name] = BlackjackGame._default_stats(None)
         elif game_t == GameType.WAR: default_stats[game_t.name] = WarGame._default_stats(None)
         elif game_t == GameType.EUCHRE: default_stats[game_t.name] = EuchreGame._default_stats(None)
         # Add defaults for other games here

     try:
         if not os.path.exists(SAVE_FILE): return default_settings, default_stats
         with open(SAVE_FILE, 'r') as f: state = json.load(f)
         loaded_settings = state.get("settings", default_settings)
         loaded_stats = state.get("session_stats", default_stats)
         # Ensure stats dict has entries for all known games after loading
         for game_t in GameType:
             if game_t.name not in loaded_stats:
                 if game_t == GameType.BLACKJACK: loaded_stats[game_t.name] = BlackjackGame._default_stats(None)
                 elif game_t == GameType.WAR: loaded_stats[game_t.name] = WarGame._default_stats(None)
                 elif game_t == GameType.EUCHRE: loaded_stats[game_t.name] = EuchreGame._default_stats(None)
                 # Add defaults for other games here
         print(f"{COLOR_GREEN}Loaded previous settings and stats.{COLOR_RESET}"); time.sleep(1)
         return loaded_settings, loaded_stats
     except (IOError, json.JSONDecodeError) as e:
         print(f"{COLOR_RED}Error loading state: {e}. Using defaults.{COLOR_RESET}"); time.sleep(1.5)
         return default_settings, default_stats


# --- Start Game ---
if __name__ == "__main__":
    # Color Support Check
    can_use_color = sys.stdout.isatty() and os.name == 'posix'
    if os.name == 'nt': os.system(''); can_use_color = sys.stdout.isatty()
    if not can_use_color:
        print("Running without color support (or cannot detect).")
        COLOR_RESET=COLOR_RED=COLOR_BLACK=COLOR_WHITE_BG=COLOR_GREEN=COLOR_YELLOW=COLOR_BLUE=COLOR_MAGENTA=COLOR_BOLD=COLOR_DIM=COLOR_CYAN=""

    main() # Call the main function

