import random
import time
import os
import sys  # Needed for flushing output in fast mode
import json  # For saving/loading settings
from typing import List, Optional, Tuple
from functools import total_ordering

# --- Game Configuration ---
DEFAULT_MAX_ROUNDS = 2000  # Default if no setting found
SETTINGS_FILE = "war_settings.json"  # File to store settings
WAR_FACE_DOWN_CARDS = 3  # Number of face-down cards in war
MIN_CARDS_FOR_WAR = 4  # Minimum cards needed to participate in war

# Define card suits, ranks, and their values
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
SUIT_SYMBOLS = {"Hearts": "♥", "Diamonds": "♦", "Clubs": "♣", "Spades": "♠"}
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
VALUES = {rank: i + 2 for i, rank in enumerate(RANKS)}
DISPLAY_RANKS = {"2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "J": "J", "Q": "Q", "K": "K", "A": "A"}

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
DEALING_CARD_PLACEHOLDER = "🂠" # Unicode playing card back

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

def get_game_mode() -> bool:
    """Gets the desired game mode (Normal or Fast).
    
    Returns:
        bool: True for fast mode, False for normal mode
    """
    while True:
        mode = input("Choose game speed (Normal / Fast): ").strip().lower()
        if mode in ['normal', 'n']:
            return False  # Not fast mode
        elif mode in ['fast', 'f']:
            return True  # Is fast mode
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
        sys.stdout.flush()  # Ensure the line is printed immediately
        time.sleep(0.1)  # Small delay between lines for animation effect

    time.sleep(2)  # Pause longer after the full title is displayed


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
        print(f"[{load_chars[i % len(load_chars)]}] ", end='\r')  # Use end='\r' to overwrite line
        time.sleep(0.1)
    print("[OK]      ")  # Print OK and spaces to clear loading chars
    time.sleep(1)
    clear_screen()


# --- Settings Class ---
class Settings:
    """Manages game settings, including saving/loading via JSON."""
    def __init__(self):
        # Default values
        self.player_name = "Player"
        self.use_ascii_art = True
        self.show_flavor_text = True
        self.clear_screen_enabled = True
        self.shuffle_won_cards = True
        self.max_rounds = DEFAULT_MAX_ROUNDS # Use default initially
        self.autoplay = False # Default to requiring Enter press

        self._load_settings() # Load settings from file, overwriting defaults if successful

    def _load_settings(self):
        """Loads settings from the JSON file."""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Update attributes safely, keeping defaults if keys are missing
                self.player_name = loaded_data.get('player_name', self.player_name)
                self.use_ascii_art = loaded_data.get('use_ascii_art', self.use_ascii_art)
                self.show_flavor_text = loaded_data.get('show_flavor_text', self.show_flavor_text)
                self.clear_screen_enabled = loaded_data.get('clear_screen_enabled', self.clear_screen_enabled)
                self.shuffle_won_cards = loaded_data.get('shuffle_won_cards', self.shuffle_won_cards)
                self.max_rounds = loaded_data.get('max_rounds', self.max_rounds)
                self.autoplay = loaded_data.get('autoplay', self.autoplay)
                # print(f"Settings loaded from {SETTINGS_FILE}") # Optional confirmation

        except FileNotFoundError:
            print(f"Settings file ({SETTINGS_FILE}) not found. Using defaults.")
            # No need to do anything, defaults are already set
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error reading settings file ({e}). Using defaults.")
            # Don't recursively call __init__, file is corrupt so defaults already set
        except Exception as e:
            print(f"An unexpected error occurred loading settings ({e}). Using defaults.")
            # Don't recursively call __init__, use existing defaults

    def _save_settings(self):
        """Saves the current settings to the JSON file."""
        settings_data = {
            'player_name': self.player_name,
            'use_ascii_art': self.use_ascii_art,
            'show_flavor_text': self.show_flavor_text,
            'clear_screen_enabled': self.clear_screen_enabled,
            'shuffle_won_cards': self.shuffle_won_cards,
            'max_rounds': self.max_rounds,
            'autoplay': self.autoplay,
        }
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4) # Use indent for readability
            # print("Settings saved.") # Optional: confirmation message
        except IOError as e:
            print(f"Warning: Could not save settings ({e}).")
        except Exception as e:
            print(f"An unexpected error occurred saving settings ({e}).")


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
        self.display_rank = DISPLAY_RANKS[rank]
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
        original_ranks_full = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        full_rank_name = original_ranks_full[self.value - 2]
        return f"{full_rank_name} of {self.suit}"

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

    def shuffle(self, settings: Settings, is_fast_mode: bool) -> None:
        """Shuffles the deck randomly."""
        if settings.clear_screen_enabled:
            clear_screen()
        print("Shuffling deck...")
        if not is_fast_mode:
            time.sleep(1)
        random.shuffle(self.cards)

    def deal(self, settings: Settings, player1_name: str, player2_name: str, is_fast_mode: bool) -> Tuple[List[Card], List[Card]]:
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
                if not is_fast_mode:
                    p1_display += DEALING_CARD_PLACEHOLDER + " "
                    if settings.clear_screen_enabled: clear_screen()
                    print("Dealing...")
                    print(f"{player1_name.ljust(15)}: {p1_display}")
                    print(f"{player2_name.ljust(15)}: {p2_display}")
                    time.sleep(deal_delay)  # Short pause for dealing effect
            else:
                hand2.append(card)
                if not is_fast_mode:
                    p2_display += DEALING_CARD_PLACEHOLDER + " "
                    if settings.clear_screen_enabled: clear_screen()
                    print("Dealing...")
                    print(f"{player1_name.ljust(15)}: {p1_display}")
                    print(f"{player2_name.ljust(15)}: {p2_display}")
                    time.sleep(deal_delay)  # Short pause for dealing effect

        if not is_fast_mode:
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

def display_cards_side_by_side(card1, card2, player1_name, player2_name, settings):
    """Prints two ASCII cards (or simple text) next to each other based on settings."""
    # Primarily used for War face-offs now, but kept for potential future use
    if settings.use_ascii_art:
        lines1 = str(card1).split('\n')
        lines2 = str(card2).split('\n')
        width1 = len(lines1[0])
        width2 = len(lines2[0])

        header1 = player1_name.center(width1)
        header2 = player2_name.center(width2)

        print(f"{header1}   {header2}")
        for i in range(len(lines1)):
            line1_content = lines1[i] if i < len(lines1) else ' ' * width1
            line2_content = lines2[i] if i < len(lines2) else ' ' * width2
            print(f"{line1_content}   {line2_content}")
    else:
        # Simple text display if ASCII is off
        print(f"{player1_name}: {card1.simple_str()}")
        print(f"{player2_name}: {card2.simple_str()}")


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
                   stats: GameStats, settings: Settings, is_fast_mode: bool) -> bool:
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
    if not is_fast_mode:
        time.sleep(2.0)  # Longer pause at start of war

    min_cards_for_war = MIN_CARDS_FOR_WAR
    p1_cards_left = player1.cards_left()
    p2_cards_left = player2.cards_left()

    # Check if players have enough cards for war
    if p1_cards_left < min_cards_for_war or p2_cards_left < min_cards_for_war:
        print(f"\nNot enough cards for a full War!")
        if not is_fast_mode: time.sleep(1.5)
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
        if winner == player1: stats.record_player_win()
        else: stats.record_computer_win()
        if not is_fast_mode: time.sleep(3.5)
        return False # Game ends

    # --- Show Face-Down Cards ---
    print(f"\n{player1.name} places {WAR_FACE_DOWN_CARDS} cards face down...")
    if not is_fast_mode:
        time.sleep(1)
    display_face_down_row(WAR_FACE_DOWN_CARDS, player1.name, settings)  # Pass settings
    war_cards_player1 = [player1.play_card() for _ in range(WAR_FACE_DOWN_CARDS)]
    if not is_fast_mode:
        time.sleep(1.5)

    print(f"\n{player2.name} places {WAR_FACE_DOWN_CARDS} cards face down...")
    if not is_fast_mode:
        time.sleep(1)
    display_face_down_row(WAR_FACE_DOWN_CARDS, player2.name, settings)  # Pass settings
    war_cards_player2 = [player2.play_card() for _ in range(WAR_FACE_DOWN_CARDS)]
    if not is_fast_mode:
        time.sleep(1.5)
    # --- End Show Face-Down Cards ---

    # Add actual cards to pot (filter None in case player ran out exactly)
    cards_on_table.extend([c for c in war_cards_player1 if c])
    cards_on_table.extend([c for c in war_cards_player2 if c])
    print(f"\nPot size is now {len(cards_on_table)} cards...") # Show growing pot
    if not is_fast_mode: time.sleep(1.5)


    print("\nPlaying face-up War cards...")
    if not is_fast_mode: time.sleep(1.0) # Pause before first card

    # Players play the face-up war card
    card1 = player1.play_card()
    if card1:
        display_single_card(card1, player1.name, settings, is_war_card=True) # Mark as war card
        if not is_fast_mode: time.sleep(1.0) # Pause between cards
    else:
        # Handle player 1 running out exactly here
        if settings.clear_screen_enabled: clear_screen()
        print("--- WAR OUTCOME ---")
        print(f"{player1.name} ran out of cards playing the face-up War card!")
        if not is_fast_mode: time.sleep(1.5)
        pot_to_add = cards_on_table # Computer gets the table cards
        player2.add_cards(pot_to_add, settings)
        player1.hand = []
        print(f"{player2.name} collects all {len(pot_to_add)} remaining cards.")
        stats.check_pot(len(pot_to_add), player2.name)
        stats.record_computer_win()
        if not is_fast_mode: time.sleep(3.5)
        return False # Game ends

    card2 = player2.play_card()
    if card2:
        display_single_card(card2, player2.name, settings, is_war_card=True) # Mark as war card
        if not is_fast_mode: time.sleep(1.5) # Pause after second card
    else:
        # Handle player 2 running out exactly here
        if settings.clear_screen_enabled: clear_screen()
        print("--- WAR OUTCOME ---")
        print(f"{player2.name} ran out of cards playing the face-up War card!")
        if not is_fast_mode: time.sleep(1.5)
        pot_to_add = cards_on_table + [card1] # Player 1 gets table cards + their own card
        player1.add_cards(pot_to_add, settings)
        player2.hand = []
        print(f"{player1.name} collects all {len(pot_to_add)} remaining cards.")
        stats.check_pot(len(pot_to_add), player1.name)
        stats.record_player_win()
        if not is_fast_mode: time.sleep(3.5)
        return False # Game ends

    cards_on_table.extend([card1, card2]) # Add face-up cards to pot
    print(f"\nComparing War cards: {card1.simple_str()} vs {card2.simple_str()}")
    if not is_fast_mode: time.sleep(1.5)

    # Compare the face-up war cards
    winner = None
    if card1 > card2:
        winner = player1
        stats.record_player_win() # Record streak
        win_comment = f" {random.choice(PLAYER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
        print(f"\n{player1.name} wins the war round!{win_comment}")
    elif card2 > card1:
        winner = player2
        stats.record_computer_win() # Record streak
        win_comment = f" {random.choice(COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
        print(f"\n{player2.name} wins the war round!{win_comment}")
    else:
        # Another war! Reset streaks as it's a tie for this comparison
        stats.player_win_streak = 0
        stats.computer_win_streak = 0
        print("\nWar cards are equal! Another War begins...")
        if not is_fast_mode: time.sleep(2)
        # Recursively call war, passing current pot, stats, settings
        return play_war_round(player1, player2, cards_on_table, stats, settings, is_fast_mode)

    # If there was a winner this war round
    if winner:
        winner.add_cards(cards_on_table, settings) # Add cards respecting settings
        print(f"{winner.name} collects {len(cards_on_table)} cards.")
        stats.check_pot(len(cards_on_table), winner.name)

    if not is_fast_mode: time.sleep(3.5)
    return True # Indicate war resolved without game ending

def sudden_death_war(player1: Player, player2: Player, stats: GameStats, 
                     settings: Settings, is_fast_mode: bool) -> Optional[Player]:
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
    if not is_fast_mode: time.sleep(2.5)

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
        if not is_fast_mode: time.sleep(3)
        # No need to add cards, just declare winner based on who had cards left
        return winner # Return the winning player object

    # Display cards sequentially
    print("\nPlaying final cards...")
    if not is_fast_mode: time.sleep(1.0)
    display_single_card(card1, player1.name, settings)
    if not is_fast_mode: time.sleep(1.0)
    display_single_card(card2, player2.name, settings)
    if not is_fast_mode: time.sleep(1.5)

    print(f"\nComparing Sudden Death cards: {card1.simple_str()} vs {card2.simple_str()}")
    if not is_fast_mode: time.sleep(2.0)

    # Determine winner - winner takes ALL cards from loser
    if card1 > card2:
        print(f"\n{player1.name} wins Sudden Death!")
        # Give all of player 2's cards (including the one just played) to player 1
        all_loser_cards = player2.hand + [card2]
        player1.add_cards(all_loser_cards, settings)
        player2.hand = [] # Empty loser's hand
        print(f"{player1.name} takes all remaining {len(all_loser_cards)} cards from {player2.name}!")
        winner = player1
    elif card2 > card1:
        print(f"\n{player2.name} wins Sudden Death!")
        # Give all of player 1's cards (including the one just played) to player 2
        all_loser_cards = player1.hand + [card1]
        player2.add_cards(all_loser_cards, settings)
        player1.hand = [] # Empty loser's hand
        print(f"{player2.name} takes all remaining {len(all_loser_cards)} cards from {player1.name}!")
        winner = player2
    else:
        # Tie in sudden death! Extremely rare. Could recurse or declare draw.
        # For simplicity, let's declare a draw in this unlikely event.
        print("\nSudden Death is a TIE! Unbelievable!")
        winner = None # Indicate a draw

    if not is_fast_mode: time.sleep(4.0)
    return winner # Return the winning player object or None for a draw


def game_loop() -> None:
    """Main function to run the War game."""
    # --- Title and Loading ---
    display_title_screen() # Animated title
    display_loading_screen() # Existing loading screen

    # --- Initial Setup ---
    settings = Settings() # Settings object now loads automatically
    is_fast_mode = get_game_mode() # Ask for speed first
    settings.configure() # Let user adjust settings, including name, max rounds etc.

    # --- Game Setup ---
    deck = Deck()
    stats = GameStats()
    deck.shuffle(settings, is_fast_mode) # Pass settings
    # Pass player names to deal for animated display
    hand1, hand2 = deck.deal(settings, settings.player_name, "Computer", is_fast_mode)
    # Use the name from settings
    player1 = Player(settings.player_name, hand1)
    player2 = Player("Computer", hand2)

    game_over_reason = None # To store how the game ended

    # --- Main Game Loop ---
    # Loop condition respects settings.max_rounds (0 means no limit)
    while player1.has_cards() and player2.has_cards() and \
          (settings.max_rounds <= 0 or stats.rounds_played < settings.max_rounds):

        stats.increment_round()
        round_num = stats.rounds_played

        # --- Display Round Info ---
        if settings.clear_screen_enabled and not is_fast_mode: clear_screen()
        print(f"\n====== Round {round_num}{'/' + str(settings.max_rounds) if settings.max_rounds > 0 else ''} ======") # Show max rounds if set
        # Use player1.name which reflects the chosen name
        print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
        print(f"Current Streak: {player1.name} ({stats.player_win_streak}), Computer ({stats.computer_win_streak})") # Show current streaks
        print("-" * 25)

        # Handle input/autoplay based on settings
        if not is_fast_mode and not settings.autoplay:
            try:
                input("Press Enter to play card...")
            except KeyboardInterrupt:
                if settings.clear_screen_enabled: clear_screen()
                print("\nExiting game."); return
        elif not is_fast_mode and settings.autoplay:
            print("Autoplaying...")
            time.sleep(0.5) # Short delay in autoplay normal mode
        else: # Fast mode
            time.sleep(0.01) # Very minimal delay in fast mode
            sys.stdout.flush()

        # --- Play and Display Cards ---
        cards_on_table = []
        card1 = player1.play_card()
        card2 = player2.play_card()

        if not card1 or not card2:
            game_over_reason = "Error: A player ran out of cards unexpectedly at round start."
            break

        # Display cards sequentially
        if settings.clear_screen_enabled and not is_fast_mode: clear_screen()
        print(f"\n====== Round {round_num}{'/' + str(settings.max_rounds) if settings.max_rounds > 0 else ''} Result ======")
        print(f"{player1.name}: {player1.cards_left()} cards | {player2.name}: {player2.cards_left()} cards")
        print("-" * 25)

        display_single_card(card1, player1.name, settings)
        if not is_fast_mode: time.sleep(1.0) # Pause between cards

        display_single_card(card2, player2.name, settings)
        if not is_fast_mode: time.sleep(1.5) # Pause after second card

        print(f"\nComparing: {card1.simple_str()} vs {card2.simple_str()}")
        if not is_fast_mode: time.sleep(1.5)

        cards_on_table.extend([card1, card2])

        # --- Compare and Resolve Round ---
        winner = None
        if card1 > card2:
            winner = player1
            stats.record_player_win() # Record streak
            win_comment = f" {random.choice(PLAYER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
            print(f"\n{player1.name} wins the round!{win_comment}")
        elif card2 > card1:
            winner = player2
            stats.record_computer_win() # Record streak
            win_comment = f" {random.choice(COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
            print(f"\n{player2.name} wins the round!{win_comment}")
        else:
            # War! Reset streaks as it's a tie for this comparison
            stats.player_win_streak = 0
            stats.computer_win_streak = 0
            print("\nCards are equal!")
            if not is_fast_mode: time.sleep(1)
            # War function handles its own logic based on settings
            war_ongoing = play_war_round(player1, player2, cards_on_table, stats, settings, is_fast_mode)
            if not war_ongoing:
                game_over_reason = "Game ended during War."
                break # Game ended during war
            continue # Skip normal win processing if war happened

        # If there was a winner (not war)
        if winner:
            winner.add_cards(cards_on_table, settings) # Pass settings
            print(f"{winner.name} collects {len(cards_on_table)} cards.")
            stats.check_pot(len(cards_on_table), winner.name)

        if not is_fast_mode: time.sleep(3.5) # Pause after normal round resolution

        # Check if game ended normally by running out of cards
        if not player1.has_cards():
            game_over_reason = f"{player1.name} ran out of cards."
            break
        if not player2.has_cards():
            game_over_reason = f"{player2.name} ran out of cards."
            break

    # --- Determine Winner & Show Stats ---
    if settings.clear_screen_enabled: clear_screen()
    print("\n" + "="*15 + " Game Over " + "="*15)
    if not is_fast_mode: time.sleep(1)

    # Check if game ended due to MAX_ROUNDS and needs Sudden Death
    # Ensure max_rounds is set (> 0) before triggering sudden death
    if settings.max_rounds > 0 and stats.rounds_played >= settings.max_rounds and player1.has_cards() and player2.has_cards():
        sudden_death_winner = sudden_death_war(player1, player2, stats, settings, is_fast_mode)
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
    stats.display(player1.name) # Pass player name for display


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


