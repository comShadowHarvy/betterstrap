import random
import time
import os
import sys
import enum # Import enum for AI types and Game Modes
import json # For Save/Load
import re # Import regex for stripping ANSI codes

from card import Card, SUITS, RANKS, VALUES, CARD_BACK, get_card_color, COLOR_RESET, COLOR_RED, COLOR_BLACK, COLOR_WHITE_BG, COLOR_GREEN, COLOR_YELLOW, COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_BOLD, COLOR_DIM
from game_utils import clear_screen, typing_effect, strip_ansi_codes, get_visible_width, center_text, shuffle_animation
from player import Player, HumanPlayer, AIPlayer, AIType
from ai_chat import AI_CHAT

# --- Constants ---
AI_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ivan", "Judy", "Kevin", "Laura"] # More names
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 5 # Increased max slightly
AI_STARTING_CHIPS = 100 # Increased AI starting chips
AI_DEFAULT_BET = 5
SAVE_FILE = "blackjack_save.json" # Filename for save/load
HAND_WIDTH_APPROX = 25 # Approx width for one hand display (adjust if needed)
DEFAULT_TERMINAL_WIDTH = 80 # Fallback width
WIDE_LAYOUT_THRESHOLD = 100 # Min width for side-by-side AI layout

# --- Global Variable for Terminal Width ---
TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH

# --- Enums ---
class GameMode(enum.Enum):
    QUICK_PLAY = "Quick Play (vs AI)"
    SOLO = "Solo Play (vs Dealer)"
    POKER_STYLE = "Poker Style (vs AI with Chips)"








def create_deck(num_decks=1):
    """Creates a deck with a specified number of standard 52-card decks."""
    deck = []
    for _ in range(num_decks):
        for suit_name in SUITS:
            for rank in RANKS:
                deck.append(Card(suit_name, rank))
    print(f"{COLOR_DIM}(Using {num_decks} deck{'s' if num_decks > 1 else ''}){COLOR_RESET}")
    time.sleep(0.5)
    return deck

def calculate_hand_value(hand):
    """Calculates the value of a hand in Blackjack."""
    if not hand: return 0
    value = 0; num_aces = 0
    for card in hand:
        value += card.value
        if card.rank == 'A': num_aces += 1
    while value > 21 and num_aces: value -= 10; num_aces -= 1
    return value

def display_card(card, hidden=False):
    """Returns the string representation of a card with color."""
    if hidden:
        # Keep hidden card simple
        back = CARD_BACK * 9
        lines = ["┌─────────┐", f"│{back}│", f"│{back}│", f"│{COLOR_DIM} HIDDEN {COLOR_RESET}{COLOR_WHITE_BG}{COLOR_BLACK}│", f"│{back}│", f"│{back}│", "└─────────┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]
    if not isinstance(card, Card):
        print(f"{COLOR_RED}Error: Invalid card data format: {card}{COLOR_RESET}")
        lines = ["┌─────────┐", "│  ERROR  │", "│ INVALID │", "│  CARD   │", "│  DATA   │", "│         │", "└─────────┘"]
        return [f"{COLOR_WHITE_BG}{COLOR_RED}{line}{COLOR_RESET}" for line in lines]

    card_color = card.color
    rank_str = card.rank.ljust(2) # Ensure rank takes 2 spaces (e.g., '10', 'K ', 'A ')
    suit_str = card.suit_symbol

    # Enhanced card layout
    lines = [
        "┌─────────┐",
        f"│{card_color}{rank_str}{COLOR_BLACK}       │", # Rank top-left
        f"│ {card_color}{suit_str}{COLOR_BLACK}       │", # Suit top-left (optional, can be blank)
        f"│    {card_color}{suit_str}{COLOR_BLACK}    │", # Suit middle
        f"│       {card_color}{suit_str}{COLOR_BLACK} │", # Suit bottom-right (optional, can be blank)
        f"│       {card_color}{rank_str}{COLOR_BLACK}│", # Rank bottom-right
        "└─────────┘"
    ]
    return [f"{COLOR_WHITE_BG}{COLOR_BLACK}{line}{COLOR_RESET}" for line in lines]



def title_screen():
    """Displays a simplified, animated title screen."""
    clear_screen(); title = "B L A C K J A C K"; author = "Created by ShadowHarvy"
    card_width = 11; screen_width = TERMINAL_WIDTH # Use dynamic width
    print("\n" * 5); typing_effect(center_text(title, screen_width), delay=0.08, color=COLOR_GREEN + COLOR_BOLD); print("\n")
    print(center_text(f"{COLOR_BLUE}Dealing...{COLOR_RESET}", screen_width)); time.sleep(0.5)
    temp_deck = create_deck(); random.shuffle(temp_deck)
    dealt_card1 = temp_deck.pop() if temp_deck else Card('Spades', 'A')
    dealt_card2 = temp_deck.pop() if temp_deck else Card('Hearts', 'K')

    card1_lines = display_card(dealt_card1); card2_lines = display_card(dealt_card2)
    total_card_width = card_width * 2 + 2; left_padding = (screen_width - total_card_width) // 2; padding_str = " " * left_padding
    current_lines = [""] * (5 + 1 + 1 + 7 + 1); line_offset = 6
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
    """Displays the main menu with game modes and gets user choice."""
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
        if choice in [str(i) for i in range(1, 10)]: return choice
        else: print(f"{COLOR_RED}Invalid choice. Please enter 1-9.{COLOR_RESET}")

def display_rules():
    """Displays the basic rules of the game."""
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Blackjack Rules ---{COLOR_RESET}")
    rules = [ "- Goal: Get closer to 21 than the dealer without going over.",
        "- Card Values: 2-10 face value, J/Q/K = 10, Ace = 1 or 11.",
        "- Blackjack: Ace + 10-value card on first two cards (pays 3:2).",
        "- Hit: Take another card.", "- Stand: Keep current hand.",
        "- Double Down: Double bet, take one more card, then stand (first 2 cards only).",
        "- Split: If first two cards match rank, double bet to play two separate hands.",
        "- Insurance: If dealer shows Ace, bet up to half original bet that dealer has BJ (pays 2:1).",
        "- Surrender: Forfeit half your bet and end hand immediately (first action only).",
        "- Even Money: If you have BJ and dealer shows Ace, take guaranteed 1:1 payout.",
        "- Bust: Hand value over 21 (lose).", "- Push: Tie with dealer (bet returned).",
        "- Dealer Rules: Hits until 17 or more." ]
    for rule in rules: print(f"{COLOR_BLUE} {rule}{COLOR_RESET}"); time.sleep(0.1)
    print("-" * 25); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()

def display_settings_menu(settings):
    """Displays settings and allows changes."""
    while True:
        clear_screen()
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Settings ---{COLOR_RESET}")
        print(f"[1] Number of Decks: {COLOR_CYAN}{settings['num_decks']}{COLOR_RESET} (1-8)")
        print(f"[2] Easy Mode (Hints): {COLOR_GREEN if settings['easy_mode'] else COLOR_RED}{settings['easy_mode']}{COLOR_RESET}")
        print(f"[3] Card Counting Cheat: {COLOR_GREEN if settings['card_counting_cheat'] else COLOR_RED}{settings['card_counting_cheat']}{COLOR_RESET}")
        print(f"[4] European Rules: {COLOR_GREEN if settings.get('european_rules', False) else COLOR_RED}{settings.get('european_rules', False)}{COLOR_RESET}")
        print("[5] Back to Main Menu")
        print("-" * 30)
        choice = input(f"{COLOR_YELLOW}Choose setting to change (1-5): {COLOR_RESET}")

        if choice == '1':
            while True:
                try:
                    num = int(input(f"{COLOR_YELLOW}Enter number of decks (1-8): {COLOR_RESET}"))
                    if 1 <= num <= 8:
                        settings['num_decks'] = num
                        break # Exit inner loop on valid input
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
            break # Exit settings menu loop
        else:
            print(f"{COLOR_RED}Invalid choice.{COLOR_RESET}"); time.sleep(1)

def display_stats(stats):
    """Displays session statistics."""
    clear_screen(); print(f"{COLOR_MAGENTA}{COLOR_BOLD}--- Session Statistics ---{COLOR_RESET}")
    print(f"Hands Played: {COLOR_CYAN}{stats['hands_played']}{COLOR_RESET}")
    print(f"Player Wins: {COLOR_GREEN}{stats['player_wins']}{COLOR_RESET}")
    print(f"Dealer Wins: {COLOR_RED}{stats['dealer_wins']}{COLOR_RESET}")
    print(f"Pushes: {COLOR_YELLOW}{stats['pushes']}{COLOR_RESET}")
    print(f"Player Blackjacks: {COLOR_GREEN}{stats['player_blackjacks']}{COLOR_RESET}")
    print(f"Player Busts: {COLOR_RED}{stats['player_busts']}{COLOR_RESET}")
    net_chips = stats['chips_won'] - stats['chips_lost']
    chip_color = COLOR_GREEN if net_chips >= 0 else COLOR_RED
    print(f"Net Chips: {chip_color}{net_chips:+}{COLOR_RESET}")
    print("-" * 30); input(f"{COLOR_YELLOW}Press Enter to return to the menu...{COLOR_RESET}"); clear_screen()



# --- Card Counting Logic ---
def get_card_count_value(rank):
    """Gets the Hi-Lo count value for a card rank."""
    if rank in ['2', '3', '4', '5', '6']: return 1
    elif rank in ['10', 'J', 'Q', 'K', 'A']: return -1
    else: return 0

# --- Basic Strategy Hint ---
def get_basic_strategy_hint(player_hand, dealer_up_card):
    """Provides a basic strategy hint (Simplified)."""
    player_value = calculate_hand_value(player_hand)
    # Ensure dealer_up_card is valid before accessing its rank
    dealer_value = 0
    if dealer_up_card:
        dealer_rank = dealer_up_card.rank
        dealer_value = VALUES.get(dealer_rank, 0)
        if dealer_rank == 'A': dealer_value = 11 # Treat Ace as 11 for hints initially

    num_aces = sum(1 for card in player_hand if card.rank == 'A')
    is_soft = num_aces > 0 and calculate_hand_value(player_hand) - 10 < 11

    # Check for split possibility
    if len(player_hand) == 2 and player_hand[0].rank == player_hand[1].rank:
        rank = player_hand[0].rank
        if rank == 'A' or rank == '8': return "(Hint: Always split Aces and 8s)"
        if rank == '5' or rank == '10': return "(Hint: Never split 5s or 10s)"
        # Add more specific split hints if desired

    # Soft hand hints
    if is_soft:
        if player_value >= 19: return "(Hint: Stand on soft 19+)"
        if player_value == 18:
            return "(Hint: Stand vs 2-8, Hit vs 9-A)" if dealer_value != 0 else "(Hint: Stand on soft 18)" # Handle case where dealer upcard unknown
        if player_value <= 17: return "(Hint: Hit soft 17 or less)"
    # Hard hand hints
    else:
        if player_value >= 17: return "(Hint: Stand on hard 17+)"
        if player_value >= 13: # 13-16
            return "(Hint: Stand vs 2-6, Hit vs 7+)" if dealer_value != 0 else "(Hint: Stand on 13-16)"
        if player_value == 12:
            return "(Hint: Stand vs 4-6, Hit vs 2,3,7+)" if dealer_value != 0 else "(Hint: Hit hard 12)"
        if player_value <= 11: return "(Hint: Hit or Double Down on 11 or less)"

    return "(Hint: Use Basic Strategy Chart)" # Default fallback

# --- Game Class ---
class BlackjackGame:
    def __init__(self, game_mode=GameMode.QUICK_PLAY, settings=None, stats=None):
        self.deck = []
        self.dealer = Player("Dealer")
        self.human_player = HumanPlayer("Player (You)")
        self.ai_players = []
        self.current_hand_index = 0
        self.game_mode = game_mode
        self.settings = settings if settings is not None else self._default_settings()
        self.session_stats = stats if stats is not None else self._default_stats()
        self.running_count = 0
        self.true_count = 0
        self.decks_remaining = self.settings['num_decks']
        self._initialize_ai_players()
        self._create_and_shuffle_deck()

    def _default_settings(self):
        return {'num_decks': 1, 'easy_mode': False, 'card_counting_cheat': False}

    def _default_stats(self):
        return {'hands_played': 0, 'player_wins': 0, 'dealer_wins': 0, 'pushes': 0,
                'player_blackjacks': 0, 'player_busts': 0, 'chips_won': 0, 'chips_lost': 0}

    def _create_and_shuffle_deck(self):
        """Creates and shuffles the deck based on settings."""
        self.deck = create_deck(self.settings['num_decks'])
        random.shuffle(self.deck)
        self.running_count = 0; self.true_count = 0; self.decks_remaining = self.settings['num_decks']
        print(f"{COLOR_DIM}Deck created with {self.settings['num_decks']} deck(s) and shuffled.{COLOR_RESET}"); time.sleep(0.5)

    def _update_count(self, card):
        """Updates the running and true count."""
        self.running_count += get_card_count_value(card.rank)
        self.decks_remaining = max(0.5, len(self.deck) / 52.0)
        self.true_count = self.running_count / self.decks_remaining if self.decks_remaining > 0 else self.running_count

    def _initialize_ai_players(self):
        """Sets up AI players based on game mode."""
        self.ai_players = []
        if self.game_mode == GameMode.SOLO: return
        num_ai = random.randint(MIN_AI_PLAYERS, MAX_AI_PLAYERS)
        available_names = random.sample(AI_NAMES, k=min(len(AI_NAMES), MAX_AI_PLAYERS + 2))
        chosen_names = random.sample(available_names, k=num_ai)
        for name in chosen_names:
            ai_type = random.choice(list(AIType))
            chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
            self.ai_players.append(AIPlayer(name, ai_type, chips))

    def _ai_place_bets(self):
        """Handles AI betting for Poker Style mode."""
        if self.game_mode != GameMode.POKER_STYLE: return
        print(f"\n{COLOR_BLUE}--- AI Players Placing Bets ---{COLOR_RESET}"); time.sleep(0.5)
        for ai_player in self.ai_players:
            bet_amount = 0
            # Dynamic Betting (Simple Example)
            if ai_player.chips >= AI_DEFAULT_BET * 2 and self.true_count >= 1: bet_amount = AI_DEFAULT_BET * 2
            elif ai_player.chips >= AI_DEFAULT_BET: bet_amount = AI_DEFAULT_BET
            else: bet_amount = ai_player.chips # Bet all if less than default

            if bet_amount > 0:
                ai_player.chips -= bet_amount
                ai_player.current_bet = bet_amount
                print(f"{COLOR_BLUE}{ai_player.name}{COLOR_RESET} bets {COLOR_YELLOW}{bet_amount}{COLOR_RESET} chips. ({COLOR_RED}-{bet_amount}{COLOR_RESET}) (Remaining: {ai_player.chips})") # Added visual chip change
            else:
                ai_player.current_bet = 0
                print(f"{COLOR_BLUE}{ai_player.name}{COLOR_RESET} cannot bet.")
            time.sleep(0.7)
        print("-" * 30)

    def _deal_card(self, hand, update_count=True):
        """Deals a single card, reshuffles, and updates count."""
        if not self.deck:
            print(f"{COLOR_YELLOW}Deck empty, reshuffling...{COLOR_RESET}")
            shuffle_animation()
            self._create_and_shuffle_deck() # Use internal method to reset counts too
        if not self.deck: sys.exit(f"{COLOR_RED}Critical error: Cannot deal from empty deck.{COLOR_RESET}")
        card = self.deck.pop()
        hand.append(card)
        if update_count: # Only update count for visible cards
            self._update_count(card)
        return card

    def _ai_chat(self, category, player_action=None):
        """Makes an AI player say something based on category and context."""
        if not self.ai_players: return
        if random.random() < 0.40: # Increased chat chance significantly (e.g., 40%)
            if not self.ai_players: return # Check again in case AI left
            ai_player = random.choice(self.ai_players)

            # Select appropriate chat list
            chat_list = AI_CHAT.get(category)

            # More specific chat based on player action
            if category == "player_action":
               
                     chat_list = AI_CHAT.get("taunt", []) + AI_CHAT.get("general_insult", [])


            if chat_list: # Ensure the list exists and is not empty
                 message = random.choice(chat_list)
                 print(f"{COLOR_CYAN}[{ai_player.name}]: {message}{COLOR_RESET}")
                 time.sleep(1.2)

    def place_bet(self):
        """Allows the player to place the initial bet."""
        while True:
            try:
                print(f"\n{COLOR_YELLOW}Your chips: {self.human_player.chips}{COLOR_RESET}")
                if self.human_player.chips <= 0: print(f"{COLOR_RED}You have no chips left to bet!{COLOR_RESET}"); return False
                bet_input = input(f"Place your initial bet (minimum 1, or 'q' to quit round): ")
                if bet_input.lower() == 'q': return False
                bet = int(bet_input)
                if bet <= 0: print(f"{COLOR_RED}Bet must be positive.{COLOR_RESET}")
                elif bet > self.human_player.chips: print(f"{COLOR_RED}You don't have enough chips.{COLOR_RESET}")
                else:
                    self.human_player.hands = [[]]; self.human_player.bets = [bet]
                    self.human_player.chips -= bet; self.current_hand_index = 0
                    print(f"{COLOR_GREEN}Betting {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}"); time.sleep(1); return True # Added visual chip change
            except ValueError: print(f"{COLOR_RED}Invalid input. Please enter a number or 'q'.{COLOR_RESET}")
            except EOFError: print(f"\n{COLOR_RED}Input error. Returning to menu.{COLOR_RESET}"); return False

    def deal_initial_cards(self):
        """Deals the initial two cards to everyone with animation."""
        print(f"\n{COLOR_BLUE}Dealing cards...{COLOR_RESET}"); time.sleep(0.5)
        self.human_player.hands = [[] for _ in self.human_player.bets]
        self.dealer.hand = []
        for ai_player in self.ai_players:
            ai_player.hand = []
        participants_order = [self.human_player]
        if self.game_mode != GameMode.SOLO:
            participants_order.extend(self.ai_players)
        participants_order.append(self.dealer)
        hidden_card_lines = display_card(None, hidden=True)

        for round_num in range(2):
            for participant in participants_order:
                target_hand = None
                display_name = participant.name
                is_dealer_hidden_card = (participant == self.dealer and round_num == 0)

                if isinstance(participant, HumanPlayer):
                    if not self.human_player.hands: continue
                    if len(self.human_player.hands[0]) < 2:
                        target_hand = self.human_player.hands[0]
                    else:
                        continue
                elif isinstance(participant, AIPlayer):
                    target_hand = participant.hand
                elif isinstance(participant, Player):
                    target_hand = participant.hand

                if target_hand is not None:
                    # --- Dealing Animation ---
                    print("\r" + " " * 40, end=""); print(f"\r{COLOR_BLUE}Dealing to {display_name}... {COLOR_RESET}", end=""); sys.stdout.flush(); time.sleep(0.15)
                    print("\r" + hidden_card_lines[3], end=""); sys.stdout.flush(); time.sleep(0.2)
                    print("\r" + " " * 40, end=""); print(f"\r{COLOR_BLUE}Dealing to {display_name}... Done.{COLOR_RESET}")
                    # --- End Animation ---
                    # Deal the card, only update count if it's NOT the dealer's hidden card
                    self._deal_card(target_hand, update_count=not is_dealer_hidden_card); time.sleep(0.1)

        print(f"\n{COLOR_BLUE}{'-' * 20}{COLOR_RESET}")

    # *** Methods to be restored: _offer_insurance, _resolve_insurance, _offer_even_money ***
    def _offer_insurance(self):
        """Offers insurance bet to the player."""
        if not self.human_player.hands or not self.human_player.bets: return 0
        if not self.dealer.hand or len(self.dealer.hand) != 2: return 0
        if self.dealer.hand[1].rank == 'A': # Check if dealer shows Ace
            max_insurance = self.human_player.bets[0] // 2
            if self.human_player.chips >= max_insurance and max_insurance > 0:
                while True:
                    ins_choice = input(f"{COLOR_YELLOW}Dealer shows Ace. Insurance? (y/n): {COLOR_RESET}").lower().strip()
                    if ins_choice.startswith('y'):
                        insurance_bet = max_insurance
                        self.human_player.chips -= insurance_bet
                        print(f"{COLOR_GREEN}Placed insurance bet of {insurance_bet} chips. ({COLOR_RED}-{insurance_bet}{COLOR_RESET}){COLOR_RESET}"); time.sleep(1) # Added visual chip change
                        return insurance_bet
                    elif ins_choice.startswith('n'): print(f"{COLOR_BLUE}Insurance declined.{COLOR_RESET}"); time.sleep(1); return 0
                    else: print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
            else: print(f"{COLOR_DIM}Dealer shows Ace, but not enough chips for insurance.{COLOR_RESET}"); time.sleep(1)
        return 0

    def _resolve_insurance(self, insurance_bet):
        """Resolves the insurance bet if one was placed."""
        if insurance_bet > 0:
            if not self.dealer.hand or len(self.dealer.hand) != 2: return False
            dealer_value = calculate_hand_value(self.dealer.hand)
            is_dealer_blackjack = dealer_value == 21
            print(f"\n{COLOR_MAGENTA}--- Resolving Insurance ---{COLOR_RESET}")
            self._update_count(self.dealer.hand[0]) # Count hidden card now
            self.display_table(hide_dealer=False)
            if is_dealer_blackjack:
                winnings = insurance_bet * 3 # Total returned (original insurance + 2:1 payout)
                payout = insurance_bet * 2 # The actual winnings
                print(f"{COLOR_GREEN}Dealer has Blackjack! Insurance pays {payout}. You win {winnings} chips back. ({COLOR_GREEN}+{winnings}{COLOR_RESET}){COLOR_RESET}") # Added visual chip change
                self.human_player.chips += winnings
            else: print(f"{COLOR_RED}Dealer does not have Blackjack. Insurance bet lost.{COLOR_RESET}")
            time.sleep(2.5); return is_dealer_blackjack
        return False

    def _offer_even_money(self):
        """Offers even money if player has BJ and dealer shows Ace."""
        if not self.human_player.hands or not self.dealer.hand or len(self.dealer.hand) != 2: return False
        player_has_bj = len(self.human_player.hands) == 1 and calculate_hand_value(self.human_player.hands[0]) == 21 and len(self.human_player.hands[0]) == 2
        dealer_shows_ace = self.dealer.hand[1].rank == 'A'
        if player_has_bj and dealer_shows_ace:
            while True:
                choice = input(f"{COLOR_YELLOW}You have Blackjack, Dealer shows Ace. Take Even Money (1:1 payout)? (y/n): {COLOR_RESET}").lower().strip()
                if choice.startswith('y'):
                    payout = self.human_player.bets[0] # Even money pays 1:1 on the original bet
                    print(f"{COLOR_GREEN}Taking Even Money! Guaranteed win of {payout} chips. ({COLOR_GREEN}+{payout}{COLOR_RESET}){COLOR_RESET}"); # Added visual chip change
                    return True
                elif choice.startswith('n'): print(f"{COLOR_BLUE}Declining Even Money. Playing out the hand...{COLOR_RESET}"); return False
                else: print(f"{COLOR_RED}Invalid input. Please enter 'y' or 'n'.{COLOR_RESET}")
        return False

    # --- End of Restored Methods ---

    # *** Method moved inside the class ***
    def get_hand_lines(self, player_name, hand, hide_one=False, highlight=False, bet_amount=0, hand_label="", ai_type=None, chips=None, current_bet=None, show_ai_details=False):
        """Returns a list of lines representing the hand display (for layout composition)."""
        lines = []
        player_color = COLOR_BLUE if player_name not in ["Dealer", "Player (You)"] else COLOR_MAGENTA
        highlight_prefix = f"{COLOR_BOLD}" if highlight else ""
        label_suffix = f" ({hand_label})" if hand_label else ""
        bet_info = f" | Bet: {bet_amount}" if bet_amount > 0 else ""
        ai_type_info = f" ({ai_type.value})" if ai_type else ""
        ai_chip_info = f" | Chips: {chips}" if show_ai_details and chips is not None else ""
        ai_bet_info = f" | Betting: {current_bet}" if show_ai_details and current_bet is not None and current_bet > 0 else ""
        header = f"{highlight_prefix}{player_color}--- {player_name}{ai_type_info}{label_suffix}'s Hand{bet_info}{ai_chip_info}{ai_bet_info} ---{COLOR_RESET}"
        lines.append(header)
        if not hand:
            lines.append("[ No cards ]")
            card_lines = [[] for _ in range(7)]
        else:
            card_lines = [[] for _ in range(7)]
            for i, card_data in enumerate(hand):
                is_hidden = hide_one and i == 0
                card_str_lines = display_card(card_data, hidden=is_hidden)
                for line_num, line in enumerate(card_str_lines):
                    card_lines[line_num].append(line)
            for line_idx in range(7):
                lines.append("  ".join(card_lines[line_idx]))

        # Value/Status Line
        value_line = ""
        if not hide_one:
            value = calculate_hand_value(hand)
            status = ""
            if value == 21 and len(hand) == 2:
                status = f" {COLOR_GREEN}{COLOR_BOLD}BLACKJACK!{COLOR_RESET}"
            elif value > 21:
                status = f" {COLOR_RED}{COLOR_BOLD}BUST!{COLOR_RESET}"
            value_line = f"{COLOR_YELLOW}Value: {value}{status}{COLOR_RESET}"
        elif len(hand) > 1:
            visible_value = hand[1].value
            if hand[1].rank == 'A':
                visible_value = 11
            value_line = f"{COLOR_YELLOW}Showing: {visible_value}{COLOR_RESET}"
        elif hide_one:
            value_line = f"{COLOR_YELLOW}Showing: ?{COLOR_RESET}"
        if value_line:
            lines.append(value_line)

        # Footer Line
        visible_header_width = get_visible_width(header)
        lines.append(f"{player_color}-{COLOR_RESET}" * visible_header_width)
        return lines

    def display_table(self, hide_dealer=True):
        """Displays the current state of the table with simplified layout."""
        clear_screen()
        title = f"{COLOR_MAGENTA}{COLOR_BOLD}~~~ {self.game_mode.value} ~~~{COLOR_RESET}"
        total_bet = sum(self.human_player.bets) if self.human_player.bets else 0
        count_info = ""
        if self.settings['card_counting_cheat']:
             count_info = f" | RC: {self.running_count} | TC: {self.true_count:.1f}"
        # Print Header centered
        print(center_text(title, TERMINAL_WIDTH)); print(center_text(f"{COLOR_YELLOW}Your Chips: {self.human_player.chips} | Your Bet(s): {total_bet}{count_info}{COLOR_RESET}", TERMINAL_WIDTH)); print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")

        # --- Dealer (Top) ---
        dealer_lines = self.get_hand_lines("Dealer", self.dealer.hand, hide_one=hide_dealer)
        for line in dealer_lines:
            print(line)
        print()

        # --- AI Players (Vertical List) ---
        if self.ai_players:
            print(center_text(f"{COLOR_BLUE}--- AI Players ---{COLOR_RESET}", TERMINAL_WIDTH)) # Center Header
            show_ai_details = (self.game_mode == GameMode.POKER_STYLE)
            for ai_player in self.ai_players:
                 ai_lines = self.get_hand_lines(
                     ai_player.name, ai_player.hand,
                     ai_type=ai_player.ai_type,
                     chips=ai_player.chips,
                     current_bet=ai_player.current_bet,
                     show_ai_details=show_ai_details
                 )
                 for line in ai_lines:
                     print(line)
                 print()
            print(f"{COLOR_DIM}{'-' * TERMINAL_WIDTH}{COLOR_RESET}")

        # --- Player Hands (Bottom) ---
        if self.human_player.hands:
            print(center_text(f"{COLOR_MAGENTA}--- Your Hands ---{COLOR_RESET}", TERMINAL_WIDTH)) # Center Header
            for i, hand in enumerate(self.human_player.hands):
                 is_current_hand = (self.current_hand_index >= 0 and i == self.current_hand_index) and (len(self.human_player.hands) > 1)
                 hand_label = f"Hand {i+1}" if len(self.human_player.hands) > 1 else ""
                 bet = self.human_player.bets[i] if i < len(self.human_player.bets) else 0
                 player_lines = self.get_hand_lines(
                     self.human_player.name, hand,
                     highlight=is_current_hand,
                     bet_amount=bet,
                     hand_label=hand_label
                 )
                 for line in player_lines:
                     print(line)
                 print()
        else: print(center_text(f"{COLOR_DIM}[ No player hands active ]{COLOR_RESET}", TERMINAL_WIDTH))
        print(f"{COLOR_DIM}{'=' * TERMINAL_WIDTH}{COLOR_RESET}")


    def _play_one_hand(self, hand_index):
        """Handles the player's turn for a single hand."""
        if hand_index >= len(self.human_player.hands): print(f"{COLOR_RED}Error: Invalid hand index.{COLOR_RESET}"); return 'error'
        hand = self.human_player.hands[hand_index]
        if hand_index >= len(self.human_player.bets): print(f"{COLOR_RED}Error: Bet index out of sync.{COLOR_RESET}"); bet = 0
        else: bet = self.human_player.bets[hand_index]
        hand_label = f"Hand {hand_index + 1}" if len(self.human_player.hands) > 1 else "Your Hand"
        can_take_initial_action = len(hand) == 2
        player_stood = False

        while calculate_hand_value(hand) < 21 and not player_stood:
            self.display_table(hide_dealer=True)
            hint = ""
            # Ensure dealer hand exists and has upcard before getting hint
            if self.settings['easy_mode'] and len(hand) >= 1 and self.dealer.hand and len(self.dealer.hand) > 1:
                hint = get_basic_strategy_hint(hand, self.dealer.hand[1])
            count_hint = ""
            if self.settings['easy_mode'] and self.settings['card_counting_cheat']:
                if self.true_count >= 2: count_hint = f" {COLOR_GREEN}(High Count: {self.true_count:.1f}){COLOR_RESET}"
                elif self.true_count <= -1: count_hint = f" {COLOR_RED}(Low Count: {self.true_count:.1f}){COLOR_RESET}"
            print(f"\n--- Playing {COLOR_MAGENTA}{hand_label}{COLOR_RESET} (Value: {calculate_hand_value(hand)}) {hint}{count_hint} ---")

            options = ["(h)it", "(s)tand"]
            can_double = can_take_initial_action and self.human_player.chips >= bet
            can_split = (can_take_initial_action and len(hand) == 2 and
                         hand[0].rank == hand[1].rank and self.human_player.chips >= bet and len(self.human_player.hands) < 4)
            can_surrender = can_take_initial_action

            if can_double: options.append("(d)ouble down")
            if can_split: options.append("s(p)lit")
            if can_surrender: options.append("su(r)render")

            prompt = f"{COLOR_YELLOW}Choose action: {', '.join(options)}? {COLOR_RESET}"
            action = input(prompt).lower().strip()

            if action.startswith('h'):
                new_card = self._deal_card(hand); print(f"\n{COLOR_GREEN}You hit!{COLOR_RESET}"); print(f"{COLOR_BLUE}Received:{COLOR_RESET}")
                for line in display_card(new_card): print(line)
                self._ai_chat("player_action", player_action='hit'); time.sleep(1.5); can_take_initial_action = False # Pass action to chat
                if calculate_hand_value(hand) > 21:
                    self.display_table(hide_dealer=True); print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS!{COLOR_RESET}")
                    self.session_stats['player_busts'] += 1; self._ai_chat("player_bust"); time.sleep(1.5); return 'bust'
            elif action.startswith('s'):
                print(f"\n{COLOR_BLUE}You stand on {hand_label}.{COLOR_RESET}"); self._ai_chat("player_action", player_action='stand') # Pass action to chat
                player_stood = True; time.sleep(1);
            elif action.startswith('d') and can_double:
                print(f"\n{COLOR_YELLOW}Doubling down on {hand_label}!{COLOR_RESET}"); self.human_player.chips -= bet; self.human_player.bets[hand_index] += bet
                print(f"Bet for this hand is now {self.human_player.bets[hand_index]}. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)
                new_card = self._deal_card(hand); print(f"{COLOR_BLUE}Received one card:{COLOR_RESET}")
                for line in display_card(new_card): print(line)
                self._ai_chat("player_action", player_action='double') # Pass action to chat
                time.sleep(1.5); self.display_table(hide_dealer=True); final_value = calculate_hand_value(hand)
                if final_value > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}{hand_label} BUSTS after doubling down!{COLOR_RESET}"); self.session_stats['player_busts'] += 1; self._ai_chat("player_bust")
                else: print(f"\n{hand_label} finishes with {final_value} after doubling down.")
                time.sleep(2); return 'double_bust' if final_value > 21 else 'double_stand'
            elif action.startswith('p') and can_split:
                 print(f"\n{COLOR_YELLOW}Splitting {hand[0].rank}s!{COLOR_RESET}"); self.human_player.chips -= bet; split_card = hand.pop(1)
                 new_hand = [split_card]; self.human_player.hands.insert(hand_index + 1, new_hand); self.human_player.bets.insert(hand_index + 1, bet)
                 print(f"Placed additional {bet} bet. Chips remaining: {self.human_player.chips}"); time.sleep(1.5)
                 print(f"Dealing card to original hand (Hand {hand_index + 1})..."); self._deal_card(hand); time.sleep(0.5)
                 print(f"Dealing card to new hand (Hand {hand_index + 2})..."); self._deal_card(new_hand); time.sleep(1)
                 self._ai_chat("player_action", player_action='split') # Pass action to chat
                 self.display_table(hide_dealer=True); time.sleep(1.5); can_take_initial_action = True; continue
            elif action.startswith('r') and can_surrender:
                 print(f"\n{COLOR_YELLOW}Surrendering {hand_label}.{COLOR_RESET}")
                 refund = bet // 2; print(f"Half your bet ({refund}) is returned.")
                 self.human_player.chips += refund; self.session_stats['chips_lost'] += (bet - refund);
                 self._ai_chat("player_action", player_action='surrender') # Pass action to chat
                 time.sleep(2); return 'surrender'
            else:
                 print(f"{COLOR_RED}Invalid action or action not allowed now.{COLOR_RESET}"); self._ai_chat("general_insult"); time.sleep(1.5)

            if calculate_hand_value(hand) == 21 and not player_stood:
                 if not (len(hand) == 2 and can_take_initial_action): print(f"\n{COLOR_GREEN}{hand_label} has 21!{COLOR_RESET}"); time.sleep(1.5)
                 player_stood = True

        return 'stand' if player_stood else 'bust'


    def player_turn(self):
        """Handles the player's turn, iterating through all active hands."""
        self.current_hand_index = 0
        while self.current_hand_index < len(self.human_player.hands):
            if self.current_hand_index >= len(self.human_player.hands): break
            hand_status = self._play_one_hand(self.current_hand_index)
            if hand_status == 'surrender': self.human_player.hands[self.current_hand_index] = [] # Mark as done
            self.current_hand_index += 1
        self.current_hand_index = -1
        if any(h and calculate_hand_value(h) <= 21 for h in self.human_player.hands): print(f"\n{COLOR_BLUE}Player finishes playing all hands.{COLOR_RESET}"); time.sleep(1.5)

    def ai_turns(self):
        """Handles the turns for all AI players."""
        if not self.ai_players: return
        print(f"\n{COLOR_BLUE}--- AI Players' Turns ---{COLOR_RESET}"); time.sleep(1)
        dealer_up_card_value = 0
        if len(self.dealer.hand) > 1: dealer_up_rank = self.dealer.hand[1].rank; dealer_up_card_value = 11 if dealer_up_rank == 'A' else VALUES.get(dealer_up_rank, 0)
        for ai_player in self.ai_players:
            hand = ai_player.hand
            if self.game_mode == GameMode.POKER_STYLE and ai_player.current_bet == 0:
                print(f"{COLOR_DIM}{ai_player.name} did not bet this round.{COLOR_RESET}")
                time.sleep(0.5)
                continue
            self.display_table(hide_dealer=True)
            print(f"\n{COLOR_BLUE}{ai_player.name}'s turn ({ai_player.ai_type.value})...{COLOR_RESET}")
            time.sleep(1.5)
            while True:
                current_value = calculate_hand_value(hand)
                if current_value > 21: time.sleep(1); break
                decision = ai_player.get_decision(hand, dealer_up_card_value, self.true_count)
                print(f"{ai_player.name} ({ai_player.ai_type.value}) decides to {COLOR_YELLOW}{decision}{COLOR_RESET}..."); time.sleep(1.2)
                if decision == "hit":
                    print(f"{ai_player.name} {COLOR_GREEN}hits{COLOR_RESET}..."); time.sleep(0.8)
                    self._deal_card(hand); self.display_table(hide_dealer=True); time.sleep(1.5)
                    if calculate_hand_value(hand) > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}{ai_player.name} BUSTS!{COLOR_RESET}"); self._ai_chat("ai_bust"); time.sleep(1.5); break # AI chat on AI bust
                else: print(f"{ai_player.name} {COLOR_BLUE}stands{COLOR_RESET}."); time.sleep(1); break # No chat for AI stand? Or add one?
            if self.ai_players[-1] != ai_player or True: print(f"{COLOR_DIM}{'-' * 15}{COLOR_RESET}"); time.sleep(1)

    def dealer_turn(self):
        """Handles the dealer's turn."""
        print(f"\n{COLOR_MAGENTA}--- Dealer's Turn ---{COLOR_RESET}"); time.sleep(1)
        if len(self.dealer.hand) == 2: self._update_count(self.dealer.hand[0])
        self.display_table(hide_dealer=False)
        while calculate_hand_value(self.dealer.hand) < 17:
            print(f"{COLOR_MAGENTA}Dealer must hit...{COLOR_RESET}"); time.sleep(1.5)
            new_card = self._deal_card(self.dealer.hand); print(f"{COLOR_MAGENTA}Dealer receives:{COLOR_RESET}")
            for line in display_card(new_card): print(line)
            time.sleep(1.5); self.display_table(hide_dealer=False)
            if calculate_hand_value(self.dealer.hand) > 21: print(f"\n{COLOR_RED}{COLOR_BOLD}Dealer BUSTS!{COLOR_RESET}"); time.sleep(1.5); return
        dealer_value = calculate_hand_value(self.dealer.hand)
        if dealer_value <= 21: print(f"{COLOR_MAGENTA}Dealer stands with {dealer_value}.{COLOR_RESET}")
        time.sleep(2)

    def determine_winner(self):
        """Determines the winner(s) and distributes chips."""
        clear_screen(); print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}--- Round Results ---{COLOR_RESET}"); time.sleep(1)
        dealer_value = calculate_hand_value(self.dealer.hand) if self.dealer.hand else 0
        dealer_blackjack = dealer_value == 21 and len(self.dealer.hand) == 2

        # --- Display Final Hands (using simplified layout) ---
        print(f"\n{COLOR_BLUE}--- Final Hands ---{COLOR_RESET}")
        for line in self.get_hand_lines("Dealer", self.dealer.hand, hide_one=False):
            print(line)
        print()

        if self.ai_players:
            print(f"\n{COLOR_BLUE}--- AI Players Final Hands ---{COLOR_RESET}")
            show_ai_details = (self.game_mode == GameMode.POKER_STYLE)
            for ai_player in self.ai_players:
                for line in self.get_hand_lines(
                    ai_player.name, ai_player.hand,
                    ai_type=ai_player.ai_type,
                    chips=ai_player.chips,
                    current_bet=ai_player.current_bet,
                    show_ai_details=show_ai_details
                ):
                    print(line)
                print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")

        if self.human_player.hands:
            print(f"\n{COLOR_MAGENTA}--- Your Final Hands ---{COLOR_RESET}")
            self.current_hand_index = -1
            for i, hand in enumerate(self.human_player.hands):
                if not hand: continue # Skip surrendered
                hand_label = f"Hand {i+1}" if len(self.human_player.hands) > 1 else ""
                bet = self.human_player.bets[i] if i < len(self.human_player.bets) else 0
                for line in self.get_hand_lines(self.human_player.name, hand, bet_amount=bet, hand_label=hand_label):
                    print(line)
                print()
            print(f"{COLOR_DIM}{'-' * 60}{COLOR_RESET}")
        time.sleep(2.5)

        # --- Player Hand Outcomes ---
        print(f"\n{COLOR_YELLOW}--- Your Hand Results ---{COLOR_RESET}")
        player_won_any = False
        if not self.human_player.hands:
            print(f"{COLOR_DIM}[ No hands played this round ]{COLOR_RESET}")
        else:
            for i, hand in enumerate(self.human_player.hands):
                if not hand:
                    print(f"\n{COLOR_YELLOW}Hand {i+1}: {COLOR_DIM}Surrendered (Half bet returned){COLOR_RESET}")
                    continue
                if i >= len(self.human_player.bets): continue
                player_value = calculate_hand_value(hand)
                bet = self.human_player.bets[i]
                hand_label = f"Hand {i+1}" if len(self.human_player.hands) > 1 else "Your Hand"
                is_initial_hand_blackjack = (i == 0 and len(self.human_player.hands) == 1 and player_value == 21 and len(hand) == 2)
                player_21 = player_value == 21
                payout = 0
                result_text = ""
                chips_change = 0
                player_wins_this_hand = False

                if player_value > 21:
                    result_text = f"{COLOR_RED}{hand_label}: Busted! You lose your bet of {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = 0
                    chips_change = -bet
                    self.session_stats['dealer_wins'] += 1
                elif is_initial_hand_blackjack and not dealer_blackjack:
                    blackjack_payout = int(bet * 1.5)
                    total_win = bet + blackjack_payout
                    result_text = f"{COLOR_GREEN}{COLOR_BOLD}{hand_label}: BLACKJACK! You win {total_win} chips (payout 3:2). ({COLOR_GREEN}+{total_win}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = total_win
                    chips_change = blackjack_payout
                    self.session_stats['player_wins'] += 1
                    self.session_stats['player_blackjacks'] += 1
                    player_wins_this_hand = True
                elif player_21 and dealer_blackjack:
                    result_text = f"{COLOR_RED}{hand_label}: Dealer has Blackjack and beats your 21. You lose your bet of {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = 0
                    chips_change = -bet
                    self.session_stats['dealer_wins'] += 1
                elif dealer_blackjack and not player_21:
                    result_text = f"{COLOR_RED}{hand_label}: Dealer has Blackjack! You lose your bet of {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = 0
                    chips_change = -bet
                    self.session_stats['dealer_wins'] += 1
                elif dealer_value > 21:
                    total_win = bet * 2
                    result_text = f"{COLOR_GREEN}{hand_label}: Dealer busts! You win {total_win} chips. ({COLOR_GREEN}+{total_win}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = total_win
                    chips_change = bet
                    self.session_stats['player_wins'] += 1
                    player_wins_this_hand = True
                elif player_value > dealer_value:
                    total_win = bet * 2
                    result_text = f"{COLOR_GREEN}{hand_label}: You beat the dealer! You win {total_win} chips. ({COLOR_GREEN}+{total_win}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = total_win
                    chips_change = bet
                    self.session_stats['player_wins'] += 1
                    player_wins_this_hand = True
                elif player_value == dealer_value:
                    if is_initial_hand_blackjack and dealer_blackjack:
                        result_text = f"{COLOR_YELLOW}{hand_label}: Push! Both you and the dealer have Blackjack. Your bet is returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}" # Added visual
                    else:
                        result_text = f"{COLOR_YELLOW}{hand_label}: Push! You tie with the dealer. Your bet is returned. ({COLOR_YELLOW}±0{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = bet
                    chips_change = 0
                    self.session_stats['pushes'] += 1
                else:
                    result_text = f"{COLOR_RED}{hand_label}: Dealer wins. You lose your bet of {bet} chips. ({COLOR_RED}-{bet}{COLOR_RESET}){COLOR_RESET}" # Added visual
                    payout = 0
                    chips_change = -bet
                    self.session_stats['dealer_wins'] += 1

                print(result_text)
                self.human_player.chips += payout
                if chips_change > 0:
                    self.session_stats['chips_won'] += chips_change
                elif chips_change < 0:
                    self.session_stats['chips_lost'] += abs(chips_change)
                if player_wins_this_hand:
                    player_won_any = True
                time.sleep(1.5)

            # AI chat based on overall player outcome for the round
            if player_won_any:
                self._ai_chat("player_win")
            elif all(not h or calculate_hand_value(h) > 21 for h in self.human_player.hands):
                pass # Already chatted on bust
            else:
                self._ai_chat("taunt") # Player didn't win, maybe taunt?

        print("-" * 30)
        print(f"{COLOR_YELLOW}Your chip total after round: {self.human_player.chips}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")
        time.sleep(2.5)

        # --- AI Outcomes & Chip Handling (Poker Style) ---
        if self.ai_players:
            print(f"\n{COLOR_BLUE}--- AI Player Results ---{COLOR_RESET}")
            for ai_player in self.ai_players:
                hand = ai_player.hand
                ai_bet = ai_player.current_bet; result = ""; result_color = COLOR_RESET; ai_payout = 0
                if ai_bet > 0:
                    ai_value = calculate_hand_value(hand)
                    ai_blackjack = ai_value == 21 and len(hand) == 2
                    net_change = 0 # Calculate net change for visual
                    if ai_value > 21:
                        result = "Busted!"; result_color = COLOR_RED; ai_payout = 0; net_change = -ai_bet
                    elif ai_blackjack and not dealer_blackjack:
                        result = "Blackjack! (Wins)"; result_color = COLOR_GREEN; ai_payout = ai_bet + int(ai_bet * 1.5); net_change = int(ai_bet * 1.5); self._ai_chat("ai_win")
                    elif dealer_blackjack and not ai_blackjack:
                        result = "Loses (vs Dealer BJ)"; result_color = COLOR_RED; ai_payout = 0; net_change = -ai_bet
                    elif dealer_value > 21:
                        result = "Wins (Dealer Bust)"; result_color = COLOR_GREEN; ai_payout = ai_bet * 2; net_change = ai_bet; self._ai_chat("ai_win")
                    elif ai_value > dealer_value:
                        result = f"Wins ({ai_value} vs {dealer_value})"; result_color = COLOR_GREEN; ai_payout = ai_bet * 2; net_change = ai_bet; self._ai_chat("ai_win")
                    elif ai_value == dealer_value:
                         if ai_blackjack and dealer_blackjack: result = "Push (Both BJ)"
                         elif ai_blackjack: result = "Blackjack! (Wins vs 21)" ; result_color = COLOR_GREEN; ai_payout = ai_bet + int(ai_bet * 1.5); net_change = int(ai_bet*1.5); self._ai_chat("ai_win")
                         else: result = f"Push ({ai_value})"
                         if "Push" in result: result_color = COLOR_YELLOW; ai_payout = ai_bet; net_change = 0
                    else:
                        result = f"Loses ({ai_value} vs {dealer_value})" ; result_color = COLOR_RED; ai_payout = 0; net_change = -ai_bet

                    if self.game_mode == GameMode.POKER_STYLE:
                        ai_player.chips += ai_payout
                        chip_change_color = COLOR_GREEN if net_change > 0 else (COLOR_RED if net_change < 0 else COLOR_YELLOW)
                        chip_change_sign = "+" if net_change > 0 else ""
                        result += f" ({chip_change_color}{chip_change_sign}{net_change}{COLOR_RESET}) | Chips: {ai_player.chips}" # Added visual chip change
                        if ai_player.chips <= 0:
                             print(f"{COLOR_RED}{ai_player.name} ran out of chips and leaves the table!{COLOR_RESET}")
                             self.ai_players.remove(ai_player); time.sleep(1); continue
                else: result = "Did not bet"; result_color = COLOR_DIM
                print(f"{COLOR_BLUE}{ai_player.name} ({ai_player.ai_type.value}){COLOR_RESET}: {result_color}{result}{COLOR_RESET}"); time.sleep(0.6)
            print(f"{COLOR_DIM}{'-' * 20}{COLOR_RESET}")


    def manage_ai_players(self):
        """Manages AI players joining/leaving."""
        if self.game_mode == GameMode.SOLO: return
        print(f"\n{COLOR_YELLOW}Checking table activity...{COLOR_RESET}"); time.sleep(1); activity = False
        # AI leaving
        ai_players_to_remove = []
        for ai_player in self.ai_players:
            leave_chance = 0.25 if len(self.ai_players) >= MAX_AI_PLAYERS else 0.15
            if len(self.ai_players) > MIN_AI_PLAYERS and random.random() < leave_chance:
                ai_players_to_remove.append(ai_player)
                print(f"{COLOR_RED}{ai_player.name} has left the table.{COLOR_RESET}"); activity = True; time.sleep(0.8)
        for ai_player in ai_players_to_remove:
            self.ai_players.remove(ai_player)

        # AI joining
        available_spots = MAX_AI_PLAYERS - len(self.ai_players)
        potential_new_names = [n for n in AI_NAMES if n not in [p.name for p in self.ai_players]]
        join_chance = 0.4 if len(self.ai_players) < MAX_AI_PLAYERS / 2 else 0.25
        if available_spots > 0 and potential_new_names and random.random() < join_chance:
            num_joining = random.randint(1, min(available_spots, len(potential_new_names)))
            for _ in range(num_joining):
                if not potential_new_names: break
                new_player_name = random.choice(potential_new_names)
                potential_new_names.remove(new_player_name)
                new_ai_type = random.choice(list(AIType))
                new_chips = AI_STARTING_CHIPS if self.game_mode == GameMode.POKER_STYLE else 0
                self.ai_players.append(AIPlayer(new_player_name, new_ai_type, new_chips))
                chip_info = f" with {new_chips} chips" if self.game_mode == GameMode.POKER_STYLE else ""
                print(f"{COLOR_GREEN}{new_player_name} ({new_ai_type.value}) has joined the table{chip_info}!{COLOR_RESET}"); activity = True; time.sleep(0.8)
        if not activity: print(f"{COLOR_DIM}The table remains the same.{COLOR_RESET}"); time.sleep(1)

    def play_round(self):
        """Plays a single round of Blackjack."""
        clear_screen(); print(f"{COLOR_MAGENTA}--- Starting New Round ({self.game_mode.value}) ---{COLOR_RESET}")
        self.human_player.hands = []; self.human_player.bets = []; self.current_hand_index = 0
        self.session_stats['hands_played'] += 1

        if not self.place_bet():
             if self.human_player.chips <= 0: print(f"\n{COLOR_RED}Out of chips!{COLOR_RESET}"); time.sleep(2); return 'game_over'
             else: print(f"{COLOR_YELLOW}Returning to menu...{COLOR_RESET}"); time.sleep(1.5); return 'quit'

        self._ai_place_bets()

        max_potential_cards = (1 + len(self.ai_players)) * 5 + 5
        if len(self.deck) < max_potential_cards:
             print(f"{COLOR_YELLOW}Deck low, reshuffling...{COLOR_RESET}"); shuffle_animation(); self._create_and_shuffle_deck()
        else: print(f"{COLOR_YELLOW}Preparing next hand...{COLOR_RESET}"); time.sleep(0.7); clear_screen()

        self.deal_initial_cards()
        self.display_table(hide_dealer=True)

        insurance_bet = self._offer_insurance()

        if self._offer_even_money():
             payout = self.human_player.bets[0] # This is the *winnings*, not the total returned
             total_returned = payout * 2
             self.human_player.chips += total_returned # Add originalbet back + winnings
             self.session_stats['player_wins'] += 1; self.session_stats['player_blackjacks'] += 1; self.session_stats['chips_won'] += payout
             # Message already printed in _offer_even_money
             print(f"{COLOR_GREEN}Round over.{COLOR_RESET}"); time.sleep(2)
             # Need to resolve AI/Dealer turns if they exist for chip counts, even though player hand is done
             self.ai_turns()
             self.dealer_turn()
             self.determine_winner() # Call determine winner to show final hands and process AI results
             return True

        dealer_had_blackjack = self._resolve_insurance(insurance_bet)

        is_player_blackjack = False
        if self.human_player.hands and len(self.human_player.hands[0]) == 2: initial_player_hand = self.human_player.hands[0]; is_player_blackjack = calculate_hand_value(initial_player_hand) == 21

        if dealer_had_blackjack and not is_player_blackjack:
             print(f"{COLOR_RED}Dealer Blackjack. Round over.{COLOR_RESET}"); time.sleep(2)
             self.determine_winner(); return True

        if is_player_blackjack and not dealer_had_blackjack:
             print(f"\n{COLOR_GREEN}{COLOR_BOLD}Blackjack!{COLOR_RESET}"); time.sleep(1.5)
             self.ai_turns(); self.dealer_turn(); self.determine_winner(); return True

        if not is_player_blackjack and not dealer_had_blackjack:
            self.player_turn()
            player_busted_all = all(not h or calculate_hand_value(h) > 21 for h in self.human_player.hands)
            if not player_busted_all: self.ai_turns(); self.dealer_turn()
            else:
                print(f"\n{COLOR_RED}All your hands busted or surrendered!{COLOR_RESET}")
                if any(ai.current_bet > 0 for ai in self.ai_players):
                     print(f"{COLOR_DIM}Dealer plays for AI...{COLOR_RESET}"); self.dealer_turn()
                else:
                     print(f"\n{COLOR_MAGENTA}--- Dealer reveals ---{COLOR_RESET}"); time.sleep(1)
                     # Ensure dealer hand has hidden card before updating count
                     if len(self.dealer.hand) > 0:
                         self._update_count(self.dealer.hand[0])
                     self.display_table(hide_dealer=False); time.sleep(1.5)


        self.determine_winner()
        if self.human_player.chips <= 0: print(f"\n{COLOR_RED}You've run out of chips! Game Over.{COLOR_RESET}"); time.sleep(2.5); return 'game_over'
        self.manage_ai_players()
        return True

    def run_game(self):
        """Runs the main game loop for playing rounds."""
        if not self.deck: self._create_and_shuffle_deck()

        while True:
            round_result = self.play_round()
            if round_result == 'game_over':
                print(f"{COLOR_YELLOW}Returning to main menu...{COLOR_RESET}"); time.sleep(2); break
            elif round_result == 'quit':
                break
            elif round_result is True:
                print(f"\n{COLOR_YELLOW}Your current chips: {self.human_player.chips}{COLOR_RESET}")
                if self.game_mode != GameMode.SOLO and not self.ai_players:
                    print(f"{COLOR_YELLOW}All AI players have left or busted out!{COLOR_RESET}"); input("Press Enter to return to menu..."); break
                next_round = input(f"Press Enter for next round, or 'q' to return to menu... ").lower()
                if next_round == 'q':
                                       break
            else:
                print(f"{COLOR_RED}Unexpected round result. Returning to menu.{COLOR_RESET}"); break
        clear_screen()

    def save_game(self):
        """Saves the current game state to a file."""
        ai_players_serializable = []
        for ai_player in self.ai_players:
            ai_players_serializable.append({
                "name": ai_player.name,
                "type": ai_player.ai_type.name,
                "chips": ai_player.chips
            })
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
        """Loads game state from a file."""
        try:
            if not os.path.exists(SAVE_FILE): print(f"{COLOR_YELLOW}No save file found ({SAVE_FILE}).{COLOR_RESET}"); time.sleep(1.5); return False
            with open(SAVE_FILE, 'r') as f: state =json.load(f)
            self.human_player.chips = state.get("player_chips", 100)
            loaded_ai = state.get("ai_players", [])
            self.ai_players = []
            for data in loaded_ai:
                 try: ai_type_enum = AIType[data.get('type', 'BASIC')]
                 except KeyError: ai_type_enum = AIType.BASIC; print(f"{COLOR_RED}Warning: Invalid AI type '{data.get('type')}' loaded for {data.get('name')}. Defaulting.{COLOR_RESET}")
                 self.ai_players.append(AIPlayer(data.get('name'), ai_type_enum, data.get('chips', AI_STARTING_CHIPS)))
            self.session_stats = state.get("session_stats", self._default_stats())
            try: self.game_mode = GameMode[state.get("game_mode", "QUICK_PLAY")]
            except KeyError: print(f"{COLOR_RED}Warning: Invalid game mode '{state.get('game_mode')}' loaded. Defaulting.{COLOR_RESET}"); self.game_mode = GameMode.QUICK_PLAY
            self.settings = state.get("settings", self._default_settings()) # Load settings
            self._create_and_shuffle_deck() # Create new deck based on loaded settings
            print(f"{COLOR_GREEN}Game loaded successfully from {SAVE_FILE}{COLOR_RESET}")
            print(f"Loaded Mode: {self.game_mode.value}, Player Chips: {self.human_player.chips}")
            time.sleep(2); return True
        except (IOError, json.JSONDecodeError, KeyError) as e: print(f"{COLOR_RED}Error loading game: {e}{COLOR_RESET}"); time.sleep(1.5); return False


# --- Main Application Logic ---
def main():
    """Main function to run the application."""
    global TERMINAL_WIDTH # Allow modification of global width
    try:
        # Get terminal size once at the start
        try:
            TERMINAL_WIDTH = os.get_terminal_size().columns
        except OSError:
            print(f"{COLOR_YELLOW}Could not detect terminal size. Using default width: {DEFAULT_TERMINAL_WIDTH}{COLOR_RESET}")
            TERMINAL_WIDTH = DEFAULT_TERMINAL_WIDTH
            time.sleep(1.5) # Give user time to see message

        game_instance = None
        current_settings = BlackjackGame._default_settings(None)
        current_stats = BlackjackGame._default_stats(None)

        title_screen()
        while True:
            choice = display_menu()
            game_mode = None

            if choice == '1': game_mode = GameMode.QUICK_PLAY
            elif choice == '2': game_mode = GameMode.SOLO
            elif choice == '3': game_mode = GameMode.POKER_STYLE
            elif choice == '4': display_rules(); continue
            elif choice == '5': display_settings_menu(current_settings); continue
            elif choice == '6': display_stats(current_stats); continue
            elif choice == '7':
                if game_instance: game_instance.save_game()
                else: print(f"{COLOR_YELLOW}No active game to save.{COLOR_RESET}"); time.sleep(1)
                continue
            elif choice == '8':
                 temp_game = BlackjackGame(settings=current_settings, stats=current_stats)
                 if temp_game.load_game():
                      game_instance = temp_game
                      current_settings = game_instance.settings
                      current_stats = game_instance.session_stats # Load stats from save
                      print(f"{COLOR_GREEN}Starting loaded game...{COLOR_RESET}"); time.sleep(1)
                      game_instance.run_game()
                      current_stats = game_instance.session_stats # Update stats after game run
                 continue
            elif choice == '9':
                print(f"\n{COLOR_MAGENTA}Thanks for playing Python Blackjack by ShadowHarvy!{COLOR_RESET}"); break

            if game_mode:
                 print(f"\n{COLOR_YELLOW}Starting {game_mode.value}...{COLOR_RESET}"); time.sleep(1)
                 # Start new game: Use current settings, reset stats, reset player chips
                 current_stats = BlackjackGame._default_stats(None)
                 game_instance = BlackjackGame(game_mode=game_mode, settings=current_settings, stats=current_stats)
                 game_instance.run_game()
                 current_stats = game_instance.session_stats # Update overall stats after game run

    except KeyboardInterrupt: print(f"\n{COLOR_RED}Game interrupted. Exiting.{COLOR_RESET}")
    except Exception as e:
         print(f"\n{COLOR_RED}An unexpected error occurred: {e}{COLOR_RESET}")
         import traceback; traceback.print_exc()
    finally: print(COLOR_RESET)


# --- Start Game ---
if __name__ == "__main__":
    # Color Support Check
    can_use_color = sys.stdout.isatty() and os.name == 'posix'
    if os.name == 'nt': os.system(''); can_use_color = sys.stdout.isatty()
    if not can_use_color:
        print("Running without color support (or cannot detect).")
        COLOR_RESET=COLOR_RED=COLOR_BLACK=COLOR_WHITE_BG=COLOR_GREEN=COLOR_YELLOW=COLOR_BLUE=COLOR_MAGENTA=COLOR_BOLD=COLOR_DIM=COLOR_CYAN=""

    main() # Call the main function


