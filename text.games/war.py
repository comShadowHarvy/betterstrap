import random
import time
import os
import sys
import json
from typing import List, Optional, Tuple
from functools import total_ordering
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# --- Game Configuration ---
DEFAULT_MAX_ROUNDS = 2000
SETTINGS_FILE = Path("war_settings.json")
WAR_FACE_DOWN_CARDS = 3
MIN_CARDS_FOR_WAR = 4

# Timing constants (in seconds)
TITLE_LINE_DELAY = 0.1
TITLE_PAUSE = 2.0
LOADING_DELAY = 0.1
NORMAL_CARD_DELAY = 1.0
WAR_START_DELAY = 2.0
ROUND_END_DELAY = 3.5

# Define card suits, ranks, and their values
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
SUIT_SYMBOLS = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_NAMES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
VALUES = {rank: i + 2 for i, rank in enumerate(RANKS)}

# ASCII representation for a face-down card
FACE_DOWN_CARD = (
    "┌─────────┐\n"
    "│░░░░░░░░░│\n"
    "│░░░░░░░░░│\n"
    "│░░░░░░░░░│\n"
    "│░░░░░░░░░│\n"
    "│░░░░░░░░░│\n"
    "└─────────┘"
)
DEALING_CARD_PLACEHOLDER = "🂠"


class GameMode(Enum):
    """Enum for game speed modes."""
    NORMAL = "normal"
    FAST = "fast"

# --- Flavor Text ---
PLAYER_WINS_COMMENTS = [
    "Nice one!", "Excellent play!", "You're on fire!", "Too easy!",
    "Fortune favors you!", "A well-deserved win!", "Impressive!",
]
COMPUTER_WINS_COMMENTS = [
    "Better luck next time.", "The machines are rising!", "Just warming up.",
    "Did that sting?", "Resistance is futile.", "Calculating... Victory!", "Ouch.",
]
WAR_COMMENTS = [
    "This means WAR!", "To battle!", "Prepare for glory!", "No surrender!",
    "Let the cards decide!", "Things are heating up!", "Escalation!",
]
SUDDEN_DEATH_COMMENTS = [
    "It all comes down to this!", "One card to rule them all!", "High stakes!",
    "Winner takes all!", "The final showdown!",
]


# --- Utility Functions ---
def clear_screen() -> None:
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_game_mode() -> GameMode:
    """Gets the desired game mode (Normal or Fast).
    
    Returns:
        GameMode: The selected game mode
    """
    while True:
        mode = input("Choose game speed (Normal / Fast): ").strip().lower()
        if mode in ['normal', 'n']:
            return GameMode.NORMAL
        elif mode in ['fast', 'f']:
            return GameMode.FAST
        else:
            print("Invalid choice. Please enter 'Normal' or 'Fast'.")

def display_title_screen() -> None:
    """Displays the improved ASCII art title screen with animation."""
    clear_screen()
    title_lines = [
        r"╔═════════════════════════════════════════════════════════════╗",
        r"║                                                             ║",
        r"║   WW      WW   AAAAAA   RRRRRRR                             ║",
        r"║   WW      WW  AA    AA  RR    RR                            ║",
        r"║   WW   W  WW  AAAAAAAA  RRRRRRR                             ║",
        r"║   WW  W W WW  AA    AA  RR   RR                             ║",
        r"║   WWW   WWW  AA    AA  RR    RR       The Card Game        ║",
        r"║                                                             ║",
        r"╠═════════════════════════════════════════════════════════════╣",
        r"║                      By: ShadowHarvy                        ║",
        r"╚═════════════════════════════════════════════════════════════╝"
    ]
    for line in title_lines:
        print(line)
        sys.stdout.flush()
        time.sleep(TITLE_LINE_DELAY)

    time.sleep(TITLE_PAUSE)


def display_loading_screen() -> None:
    """Displays a fake loading sequence."""
    clear_screen()
    print("Initializing Card Shuffler...")
    time.sleep(0.7)
    print("Calibrating Randomness Engine...")
    time.sleep(0.8)
    print("Loading Settings & Graphics...")
    load_chars = ['|', '/', '-', '\\']
    for i in range(15):
        print(f"[{load_chars[i % len(load_chars)]}] ", end='\r')
        time.sleep(LOADING_DELAY)
    print("[OK]      ")  # Print OK and spaces to clear loading chars
    time.sleep(1)
    clear_screen()


# --- Settings Class ---
@dataclass
class Settings:
    """Manages game settings, including saving/loading via JSON."""
    player_name: str = "Player"
    use_ascii_art: bool = True
    show_flavor_text: bool = True
    clear_screen_enabled: bool = True
    shuffle_won_cards: bool = True
    max_rounds: int = DEFAULT_MAX_ROUNDS
    autoplay: bool = False

    def __post_init__(self) -> None:
        """Load settings from file after initialization."""
        self._load_settings()

    def _load_settings(self) -> None:
        """Loads settings from the JSON file."""
        if not SETTINGS_FILE.exists():
            return
        
        try:
            with SETTINGS_FILE.open('r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Update attributes safely, keeping defaults if keys are missing
                for key, value in loaded_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error reading settings file: {e}. Using defaults.")
        except Exception as e:
            print(f"Unexpected error loading settings: {e}. Using defaults.")

    def _save_settings(self) -> None:
        """Saves the current settings to the JSON file."""
        try:
            with SETTINGS_FILE.open('w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=4)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
        except Exception as e:
            print(f"Unexpected error saving settings: {e}")


    def _get_status(self, setting_value: bool) -> str:
        """Returns 'ON' or 'OFF' string for display."""
        return "ON" if setting_value else "OFF"

    def display_menu(self) -> None:
        """Displays the settings configuration menu."""
        clear_screen()
        print("╔══════════════════════════════════════════╗")
        print("║                Game Settings             ║")
        print("╠══════════════════════════════════════════╣")
        print(f"║ N. Player Name         : {self.player_name:<16} ║")
        max_round_str = str(self.max_rounds) if self.max_rounds > 0 else "Unlimited"
        print(f"║ M. Max Rounds          : {max_round_str:<16} ║")
        print("║------------------------------------------║")
        print(f"║ 1. Use ASCII Card Art  : {self._get_status(self.use_ascii_art):<16} ║")
        print(f"║ 2. Show Flavor Text    : {self._get_status(self.show_flavor_text):<16} ║")
        print(f"║ 3. Clear Screen        : {self._get_status(self.clear_screen_enabled):<16} ║")
        print(f"║ 4. Shuffle Won Cards   : {self._get_status(self.shuffle_won_cards):<16} ║")
        print(f"║ 5. Autoplay (Normal)   : {self._get_status(self.autoplay):<16} ║")
        print("╠══════════════════════════════════════════╣")
        print("║ S. Start Game                            ║")
        print("╚══════════════════════════════════════════╝")


    def configure(self) -> None:
        """Allows the user to toggle settings before starting."""
        needs_save = False
        while True:
            self.display_menu()
            choice = input("Enter option to change, or 'S' to start: ").strip().lower()

            if choice == 'n':
                new_name = input(f"Enter new player name (current: {self.player_name}): ").strip()
                if new_name:
                    if self.player_name != new_name:
                        self.player_name = new_name
                        needs_save = True
                else:
                    print("Name cannot be empty. Keeping current name.")
                    time.sleep(1)
            elif choice == 'm':
                while True:
                    try:
                        new_max = input(f"Enter max rounds (current: {self.max_rounds if self.max_rounds > 0 else 'Unlimited'}, 0 for Unlimited): ").strip()
                        val = int(new_max)
                        if val >= 0:
                            if self.max_rounds != val:
                                self.max_rounds = val
                                needs_save = True
                            break
                        else:
                            print("Please enter a non-negative number.")
                    except ValueError:
                        print("Invalid input. Please enter a number (or 0).")
            elif choice == '1':
                self.use_ascii_art = not self.use_ascii_art
                needs_save = True
            elif choice == '2':
                self.show_flavor_text = not self.show_flavor_text
                needs_save = True
            elif choice == '3':
                self.clear_screen_enabled = not self.clear_screen_enabled
                needs_save = True
            elif choice == '4':
                self.shuffle_won_cards = not self.shuffle_won_cards
                needs_save = True
            elif choice == '5':
                self.autoplay = not self.autoplay
                needs_save = True
            elif choice == 's':
                if needs_save:
                    print("Saving settings...")
                    self._save_settings()
                    time.sleep(0.5)
                print("Starting game...")
                time.sleep(1)
                break # Exit configuration loop
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)

# --- Game Classes ---
@total_ordering
class Card:
    """Represents a single playing card."""
    def __init__(self, suit: str, rank: str) -> None:
        self.suit = suit
        self.rank = rank
        self.display_rank = rank  # Display rank is just the rank itself
        self.value = VALUES[rank]
        self.suit_symbol = SUIT_SYMBOLS[suit]

    def __str__(self):
        """Returns a multi-line ASCII string representation of the card."""
        top_rank = self.display_rank.ljust(2)
        bottom_rank = self.display_rank.rjust(2)
        return (
            f"┌─────────┐\n"
            f"│ {top_rank}      │\n"
            f"│         │\n"
            f"│    {self.suit_symbol}    │\n"
            f"│         │\n"
            f"│      {bottom_rank} │\n"
            f"└─────────┘"
        )

    def simple_str(self) -> str:
        """Returns a simple one-line string representation."""
        full_rank_name = RANK_NAMES[self.value - 2]
        return f"{full_rank_name} of {self.suit}"
    
    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"Card({self.suit}, {self.rank}, value={self.value})"

    def __lt__(self, other: 'Card') -> bool:
        return self.value < other.value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value == other.value

class Deck:
    """Represents a deck of 52 playing cards."""
    def __init__(self) -> None:
        self.cards: List[Card] = [Card(suit, rank) for suit in SUITS for rank in RANKS]

    def shuffle(self, settings: Settings, mode: GameMode) -> None:
        """Shuffles the deck randomly."""
        if settings.clear_screen_enabled:
            clear_screen()
        print("Shuffling deck...")
        if mode == GameMode.NORMAL:
            time.sleep(1)
        random.shuffle(self.cards)

    def deal(self, settings: Settings, player1_name: str, player2_name: str, mode: GameMode) -> Tuple[List[Card], List[Card]]:
        """Deals the entire deck evenly between two players with animation."""
        if settings.clear_screen_enabled:
            clear_screen()
        print("Dealing cards...")
        time.sleep(0.5)

        hand1: List[Card] = []
        hand2: List[Card] = []
        p1_display = ""
        p2_display = ""
        deal_delay = 0.05 if settings.use_ascii_art else 0.01  # Faster if no art

        for i, card in enumerate(self.cards):
            if i % 2 == 0:
                hand1.append(card)
                if mode == GameMode.NORMAL:
                    p1_display += DEALING_CARD_PLACEHOLDER + " "
                    if settings.clear_screen_enabled:
                        clear_screen()
                    print("Dealing...")
                    print(f"{player1_name.ljust(15)}: {p1_display}")
                    print(f"{player2_name.ljust(15)}: {p2_display}")
                    time.sleep(deal_delay)
            else:
                hand2.append(card)
                if mode == GameMode.NORMAL:
                    p2_display += DEALING_CARD_PLACEHOLDER + " "
                    if settings.clear_screen_enabled:
                        clear_screen()
                    print("Dealing...")
                    print(f"{player1_name.ljust(15)}: {p1_display}")
                    print(f"{player2_name.ljust(15)}: {p2_display}")
                    time.sleep(deal_delay)

        if mode == GameMode.NORMAL:
            if settings.clear_screen_enabled:
                clear_screen()
            print("Dealing complete!")
            print(f"{player1_name} received {len(hand1)} cards.")
            print(f"{player2_name} received {len(hand2)} cards.")
            time.sleep(1.5)

        return hand1, hand2


class Player:
    """Represents a player in the game."""
    def __init__(self, name: str, hand: List[Card]) -> None:
        self.name = name
        self.hand: List[Card] = list(hand)
    
    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"Player(name={self.name}, cards={len(self.hand)})"

    def play_card(self) -> Optional[Card]:
        """Removes and returns the top card from the player's hand."""
        return self.hand.pop(0) if self.hand else None

    def add_cards(self, cards: List[Card], settings: Settings) -> None:
        """Adds a list of cards to the bottom of the player's hand."""
        if not cards:
            return  # Avoid error if passed empty list
        if settings.shuffle_won_cards:
            random.shuffle(cards)  # Shuffle won cards if setting is ON
        self.hand.extend(cards)

    def has_cards(self) -> bool:
        """Checks if the player still has cards."""
        return len(self.hand) > 0

    def cards_left(self) -> int:
        """Returns the number of cards the player has."""
        return len(self.hand)

class GameStats:
    """Tracks game statistics."""
    def __init__(self) -> None:
        self.rounds_played: int = 0
        self.wars_occurred: int = 0
        self.max_pot_won: int = 0
        self.max_pot_winner: str = "No one"
        self.player_win_streak: int = 0
        self.computer_win_streak: int = 0
        self.max_player_streak: int = 0
        self.max_computer_streak: int = 0

    def increment_round(self) -> None:
        self.rounds_played += 1

    def increment_war(self) -> None:
        self.wars_occurred += 1

    def record_player_win(self) -> None:
        """Records a player win and updates streaks."""
        self.player_win_streak += 1
        self.computer_win_streak = 0  # Reset opponent's streak
        if self.player_win_streak > self.max_player_streak:
            self.max_player_streak = self.player_win_streak

    def record_computer_win(self) -> None:
        """Records a computer win and updates streaks."""
        self.computer_win_streak += 1
        self.player_win_streak = 0  # Reset opponent's streak
        if self.computer_win_streak > self.max_computer_streak:
            self.max_computer_streak = self.computer_win_streak

    def check_pot(self, pot_size: int, winner_name: str) -> None:
        """Checks if the current pot is the largest won so far."""
        if pot_size > self.max_pot_won:
            self.max_pot_won = pot_size
            self.max_pot_winner = winner_name

    def display(self, player_name: str) -> None:
        """Prints the final game statistics."""
        print("\n--- Game Statistics ---")
        print(f"Total Rounds Played: {self.rounds_played}")
        print(f"Wars Occurred: {self.wars_occurred}")
        if self.max_pot_won > 0:
            print(f"Largest Pot Won: {self.max_pot_won} cards (by {self.max_pot_winner})")
        else:
            print("Largest Pot Won: N/A")
        print(f"Longest Win Streak ({player_name}): {self.max_player_streak}")
        print(f"Longest Win Streak (Computer): {self.max_computer_streak}")
        print("-----------------------")


# --- Display Functions ---
def display_single_card(card: Card, player_name: str, settings: Settings, is_war_card: bool = False) -> None:
    """Displays a single player's card, optionally marking it as a War card."""
    marker = " (WAR!)" if is_war_card else ""
    print(f"\n{player_name} plays{marker}:")
    if settings.use_ascii_art:
        print(card)
    else:
        print(card.simple_str())

def display_face_down_row(count: int, player_name: str, settings: Settings) -> None:
    """Prints a row of face-down cards if ASCII art is enabled."""
    if not settings.use_ascii_art:
        # If ASCII is off, just print a simple message
        print(f"{player_name} places {count} card(s) face down.")
        return

    if count <= 0:
        return

    lines = FACE_DOWN_CARD.split('\n')
    card_width = len(lines[0])
    total_width = (card_width + 3) * count - 3
    # Center the label above the cards
    print(f"{player_name}'s face-down cards:".center(total_width))

    for i in range(len(lines)):
        row_line = ""
        for _ in range(count):
            row_line += lines[i] + "   "
        print(row_line.rstrip())

# --- Core Game Logic ---
def play_war_round(player1: Player, player2: Player, cards_on_table: List[Card], 
                   stats: GameStats, settings: Settings, mode: GameMode) -> bool:
    """Handles a 'War' round, respecting settings.
    
    Returns:
        bool: True if war resolved and game continues, False if game ended
    """
    stats.increment_war()
    if settings.clear_screen_enabled:
        clear_screen()

    war_comment = f" ({random.choice(WAR_COMMENTS)})" if settings.show_flavor_text else ""
    print("\n" + "="*15 + f" W A R !{war_comment} " + "="*15)  # More prominent header

    initial_pot = len(cards_on_table)
    print(f"\nCards initially contested: {initial_pot}")
    print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
    if mode == GameMode.NORMAL:
        time.sleep(WAR_START_DELAY)

    min_cards_for_war = MIN_CARDS_FOR_WAR
    p1_cards_left = player1.cards_left()
    p2_cards_left = player2.cards_left()

    # Check if players have enough cards for war
    if p1_cards_left < min_cards_for_war or p2_cards_left < min_cards_for_war:
        print(f"\nNot enough cards for a full War!")
        if mode == GameMode.NORMAL:
            time.sleep(1.5)
        # Determine winner/loser based on who has fewer cards
        winner, loser = (player2, player1) if p1_cards_left < p2_cards_left else (player1, player2)
        print(f"{loser.name} doesn't have enough cards ({loser.cards_left()} left)!")
        loser_remaining = loser.hand[:] # Get remaining cards *before* emptying hand
        loser.hand = []
        all_cards = cards_on_table + loser_remaining
        winner.add_cards(all_cards, settings) # Add cards respecting settings
        print(f"{winner.name} collects all {len(all_cards)} cards.")
        stats.check_pot(len(all_cards), winner.name)
        # Record win based on who collected cards
        if winner == player1:
            stats.record_player_win()
        else:
            stats.record_computer_win()
        if mode == GameMode.NORMAL:
            time.sleep(ROUND_END_DELAY)
        return False

    # --- Show Face-Down Cards ---
    print(f"\n{player1.name} places {WAR_FACE_DOWN_CARDS} cards face down...")
    if mode == GameMode.NORMAL:
        time.sleep(1)
    display_face_down_row(WAR_FACE_DOWN_CARDS, player1.name, settings)
    war_cards_player1 = [player1.play_card() for _ in range(WAR_FACE_DOWN_CARDS)]
    if mode == GameMode.NORMAL:
        time.sleep(1.5)

    print(f"\n{player2.name} places {WAR_FACE_DOWN_CARDS} cards face down...")
    if mode == GameMode.NORMAL:
        time.sleep(1)
    display_face_down_row(WAR_FACE_DOWN_CARDS, player2.name, settings)
    war_cards_player2 = [player2.play_card() for _ in range(WAR_FACE_DOWN_CARDS)]
    if mode == GameMode.NORMAL:
        time.sleep(1.5)
    # --- End Show Face-Down Cards ---

    # Add actual cards to pot (filter None in case player ran out exactly)
    cards_on_table.extend([c for c in war_cards_player1 if c])
    cards_on_table.extend([c for c in war_cards_player2 if c])
    print(f"\nPot size is now {len(cards_on_table)} cards...")
    if mode == GameMode.NORMAL:
        time.sleep(1.5)

    print("\nPlaying face-up War cards...")
    if mode == GameMode.NORMAL:
        time.sleep(NORMAL_CARD_DELAY)

    # Players play the face-up war card
    card1 = player1.play_card()
    if card1:
        display_single_card(card1, player1.name, settings, is_war_card=True)
        if mode == GameMode.NORMAL:
            time.sleep(NORMAL_CARD_DELAY)
    else:
        # Handle player 1 running out exactly here
        if settings.clear_screen_enabled:
            clear_screen()
        print("--- WAR OUTCOME ---")
        print(f"{player1.name} ran out of cards playing the face-up War card!")
        if mode == GameMode.NORMAL:
            time.sleep(1.5)
        pot_to_add = cards_on_table # Computer gets the table cards
        player2.add_cards(pot_to_add, settings)
        player1.hand = []
        print(f"{player2.name} collects all {len(pot_to_add)} remaining cards.")
        stats.check_pot(len(pot_to_add), player2.name)
        stats.record_computer_win()
        if mode == GameMode.NORMAL:
            time.sleep(ROUND_END_DELAY)
        return False

    card2 = player2.play_card()
    if card2:
        display_single_card(card2, player2.name, settings, is_war_card=True)
        if mode == GameMode.NORMAL:
            time.sleep(1.5)
    else:
        # Handle player 2 running out exactly here
        if settings.clear_screen_enabled:
            clear_screen()
        print("--- WAR OUTCOME ---")
        print(f"{player2.name} ran out of cards playing the face-up War card!")
        if mode == GameMode.NORMAL:
            time.sleep(1.5)
        pot_to_add = cards_on_table + [card1] # Player 1 gets table cards + their own card
        player1.add_cards(pot_to_add, settings)
        player2.hand = []
        print(f"{player1.name} collects all {len(pot_to_add)} remaining cards.")
        stats.check_pot(len(pot_to_add), player1.name)
        stats.record_player_win()
        if mode == GameMode.NORMAL:
            time.sleep(ROUND_END_DELAY)
        return False

    cards_on_table.extend([card1, card2])
    print(f"\nComparing War cards: {card1.simple_str()} vs {card2.simple_str()}")
    if mode == GameMode.NORMAL:
        time.sleep(1.5)

    # Compare the face-up war cards
    winner = None
    if card1 > card2:
        winner = player1
        stats.record_player_win()
        win_comment = f" {random.choice(PLAYER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
        print(f"\n{player1.name} wins the war round!{win_comment}")
    elif card2 > card1:
        winner = player2
        stats.record_computer_win()
        win_comment = f" {random.choice(COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
        print(f"\n{player2.name} wins the war round!{win_comment}")
    else:
        # Another war! Reset streaks as it's a tie for this comparison
        stats.player_win_streak = 0
        stats.computer_win_streak = 0
        print("\nWar cards are equal! Another War begins...")
        if mode == GameMode.NORMAL:
            time.sleep(2)
        return play_war_round(player1, player2, cards_on_table, stats, settings, mode)

    # If there was a winner this war round
    if winner:
        winner.add_cards(cards_on_table, settings)
        print(f"{winner.name} collects {len(cards_on_table)} cards.")
        stats.check_pot(len(cards_on_table), winner.name)

    if mode == GameMode.NORMAL:
        time.sleep(ROUND_END_DELAY)
    return True

def sudden_death_war(player1: Player, player2: Player, stats: GameStats, 
                     settings: Settings, mode: GameMode) -> Optional[Player]:
    """Handles the Sudden Death face-off at MAX_ROUNDS.
    
    Returns:
        Optional[Player]: The winning player, or None if it's a draw
    """
    if settings.clear_screen_enabled:
        clear_screen()
    sd_comment = random.choice(SUDDEN_DEATH_COMMENTS)
    print("\n" + "="*10 + f" SUDDEN DEATH! ({sd_comment}) " + "="*10)
    print("Maximum rounds reached! One final card determines the winner!")
    print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
    if mode == GameMode.NORMAL:
        time.sleep(2.5)

    # Play one card each
    card1 = player1.play_card()
    card2 = player2.play_card()

    # Handle edge case where one player runs out exactly on the last round (unlikely)
    if not card1 or not card2:
        print("\nA player ran out of cards just before Sudden Death!")
        # The player with cards remaining wins by default
        winner = player2 if not card1 else player1
        loser = player1 if not card1 else player2
        print(f"{loser.name} ran out! {winner.name} wins by default!")
        if mode == GameMode.NORMAL:
            time.sleep(3)
        return winner

    # Display cards sequentially
    print("\nPlaying final cards...")
    if mode == GameMode.NORMAL:
        time.sleep(NORMAL_CARD_DELAY)
    display_single_card(card1, player1.name, settings)
    if mode == GameMode.NORMAL:
        time.sleep(NORMAL_CARD_DELAY)
    display_single_card(card2, player2.name, settings)
    if mode == GameMode.NORMAL:
        time.sleep(1.5)

    print(f"\nComparing Sudden Death cards: {card1.simple_str()} vs {card2.simple_str()}")
    if mode == GameMode.NORMAL:
        time.sleep(2.0)

    # Determine winner - winner takes ALL cards from loser
    if card1 > card2:
        print(f"\n{player1.name} wins Sudden Death!")
        # Give all of player 2's cards (including the one just played) to player 1
        all_loser_cards = player2.hand + [card2]
        player1.add_cards(all_loser_cards, settings)
        player2.hand = []
        print(f"{player1.name} takes all remaining {len(all_loser_cards)} cards from {player2.name}!")
        winner = player1
    elif card2 > card1:
        print(f"\n{player2.name} wins Sudden Death!")
        all_loser_cards = player1.hand + [card1]
        player2.add_cards(all_loser_cards, settings)
        player1.hand = []
        print(f"{player2.name} takes all remaining {len(all_loser_cards)} cards from {player1.name}!")
        winner = player2
    else:
        print("\nSudden Death is a TIE! Unbelievable!")
        winner = None

    if mode == GameMode.NORMAL:
        time.sleep(4.0)
    return winner


def game_loop() -> None:
    """Main function to run the War game."""
    # --- Title and Loading ---
    display_title_screen()
    display_loading_screen()

    # --- Initial Setup ---
    settings = Settings()
    mode = get_game_mode()
    settings.configure()

    # --- Game Setup ---
    deck = Deck()
    stats = GameStats()
    deck.shuffle(settings, mode)
    hand1, hand2 = deck.deal(settings, settings.player_name, "Computer", mode)
    player1 = Player(settings.player_name, hand1)
    player2 = Player("Computer", hand2)

    game_over_reason: Optional[str] = None

    # --- Main Game Loop ---
    # Loop condition respects settings.max_rounds (0 means no limit)
    while player1.has_cards() and player2.has_cards() and \
          (settings.max_rounds <= 0 or stats.rounds_played < settings.max_rounds):

        stats.increment_round()
        round_num = stats.rounds_played

        # --- Display Round Info ---
        if settings.clear_screen_enabled and mode == GameMode.NORMAL:
            clear_screen()
        round_display = f"/{settings.max_rounds}" if settings.max_rounds > 0 else ""
        print(f"\n====== Round {round_num}{round_display} ======")
        print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
        print(f"Current Streak: {player1.name} ({stats.player_win_streak}), Computer ({stats.computer_win_streak})")
        print("-" * 25)

        # Handle input/autoplay based on settings
        if mode == GameMode.NORMAL and not settings.autoplay:
            try:
                input("Press Enter to play card...")
            except KeyboardInterrupt:
                if settings.clear_screen_enabled:
                    clear_screen()
                print("\nExiting game.")
                return
        elif mode == GameMode.NORMAL and settings.autoplay:
            print("Autoplaying...")
            time.sleep(0.5)
        else:
            time.sleep(0.01)
            sys.stdout.flush()

        # --- Play and Display Cards ---
        cards_on_table = []
        card1 = player1.play_card()
        card2 = player2.play_card()

        if not card1 or not card2:
            game_over_reason = "Error: A player ran out of cards unexpectedly at round start."
            break

        # Display cards sequentially
        if settings.clear_screen_enabled and mode == GameMode.NORMAL:
            clear_screen()
        print(f"\n====== Round {round_num}{round_display} Result ======")
        print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
        print("-" * 25)

        display_single_card(card1, player1.name, settings)
        if mode == GameMode.NORMAL:
            time.sleep(NORMAL_CARD_DELAY)

        display_single_card(card2, player2.name, settings)
        if mode == GameMode.NORMAL:
            time.sleep(1.5)

        print(f"\nComparing: {card1.simple_str()} vs {card2.simple_str()}")
        if mode == GameMode.NORMAL:
            time.sleep(1.5)

        cards_on_table.extend([card1, card2])

        # --- Compare and Resolve Round ---
        winner = None
        if card1 > card2:
            winner = player1
            stats.record_player_win()
            win_comment = f" {random.choice(PLAYER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
            print(f"\n{player1.name} wins the round!{win_comment}")
        elif card2 > card1:
            winner = player2
            stats.record_computer_win()
            win_comment = f" {random.choice(COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
            print(f"\n{player2.name} wins the round!{win_comment}")
        else:
            # War! Reset streaks as it's a tie for this comparison
            stats.player_win_streak = 0
            stats.computer_win_streak = 0
            print("\nCards are equal!")
            if mode == GameMode.NORMAL:
                time.sleep(1)
            war_ongoing = play_war_round(player1, player2, cards_on_table, stats, settings, mode)
            if not war_ongoing:
                game_over_reason = "Game ended during War."
                break
            continue

        # If there was a winner (not war)
        if winner:
            winner.add_cards(cards_on_table, settings)
            print(f"{winner.name} collects {len(cards_on_table)} cards.")
            stats.check_pot(len(cards_on_table), winner.name)

        if mode == GameMode.NORMAL:
            time.sleep(ROUND_END_DELAY)

        # Check if game ended normally by running out of cards
        if not player1.has_cards():
            game_over_reason = f"{player1.name} ran out of cards."
            break
        if not player2.has_cards():
            game_over_reason = f"{player2.name} ran out of cards."
            break

    # --- Determine Winner & Show Stats ---
    if settings.clear_screen_enabled:
        clear_screen()
    print("\n" + "="*15 + " Game Over " + "="*15)
    if mode == GameMode.NORMAL:
        time.sleep(1)

    # Check if game ended due to MAX_ROUNDS and needs Sudden Death
    if settings.max_rounds > 0 and stats.rounds_played >= settings.max_rounds and player1.has_cards() and player2.has_cards():
        sudden_death_winner = sudden_death_war(player1, player2, stats, settings, mode)
        if sudden_death_winner == player1:
            print(f"\n{player1.name} is the ULTIMATE WINNER after Sudden Death!")
        elif sudden_death_winner == player2:
            print(f"\n{player2.name} is the ULTIMATE WINNER after Sudden Death!")
        else:
            print("\nThe game ends in a DRAW after a tied Sudden Death!")
        game_over_reason = f"Sudden Death round concluded after {settings.max_rounds} rounds."

    # Regular Game Over conditions
    elif not player1.has_cards() and player2.has_cards():
        print(f"{player2.name} wins the game with all {player2.cards_left()} cards!")
        print(f"Reason: {game_over_reason if game_over_reason else f'{player1.name} ran out of cards.'}")
    elif not player2.has_cards() and player1.has_cards():
        print(f"{player1.name} wins the game with all {player1.cards_left()} cards!")
        print(f"Reason: {game_over_reason if game_over_reason else f'{player2.name} ran out of cards.'}")
    elif not player1.has_cards() and not player2.has_cards():
         print("Both players ran out of cards simultaneously! It's a draw!")
         print(f"Reason: {game_over_reason if game_over_reason else 'Simultaneous card depletion.'}")
    elif game_over_reason: # Catch cases where game ended during war or error
         print("Game concluded.")
         print(f"Reason: {game_over_reason}")
    else:
        # Should only be reached if max_rounds was unlimited (0) and someone ran out
        # or if sudden death resulted in a draw (handled above)
        # Re-check card counts for clarity if reason wasn't set
        if not player1.has_cards():
             print(f"{player2.name} wins the game with all {player2.cards_left()} cards!")
             print(f"Reason: {player1.name} ran out of cards (unlimited rounds).")
        elif not player2.has_cards():
             print(f"{player1.name} wins the game with all {player1.cards_left()} cards!")
             print(f"Reason: {player2.name} ran out of cards (unlimited rounds).")
        else:
             print("Game concluded.") # Fallback


    # Display statistics
    stats.display(player1.name)


# --- Start the Game ---
if __name__ == "__main__":
    try:
        game_loop()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nThanks for playing!")


