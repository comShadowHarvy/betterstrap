import random
import time
import os
import sys # Needed for flushing output in fast mode
import json # For saving/loading settings
from collections import defaultdict # For stats

# --- Game Configuration ---
DEFAULT_MAX_ROUNDS = 2000 # Default if no setting found
SETTINGS_FILE = "war_settings_multi_decks.json" # Updated settings filename
MIN_PLAYERS = 2
MAX_PLAYERS = 6 # Max total players (human + computer)
MIN_COMPUTER_PLAYERS = 1
MAX_COMPUTER_PLAYERS = 4
DEFAULT_NUM_DECKS = 1

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
def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_game_mode():
    """Gets the desired game mode (Normal or Fast)."""
    while True:
        mode = input("Choose game speed (Normal / Fast): ").strip().lower()
        if mode in ['normal', 'n']:
            return False # Not fast mode
        elif mode in ['fast', 'f']:
            return True # Is fast mode
        else:
            print("Invalid choice. Please enter 'Normal' or 'Fast'.")

def get_num_human_players():
    """Gets the number of human players."""
    max_humans = MAX_PLAYERS - MIN_COMPUTER_PLAYERS # Need at least 1 computer
    while True:
        try:
            num = int(input(f"Enter number of human players (0-{max_humans}): ").strip())
            if 0 <= num <= max_humans:
                return num
            else:
                print(f"Please enter a number between 0 and {max_humans}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_num_computer_players(num_human_players):
    """Gets the number of computer players."""
    min_computers = MIN_COMPUTER_PLAYERS
    # Adjust max computers based on humans already chosen
    max_computers = min(MAX_COMPUTER_PLAYERS, MAX_PLAYERS - num_human_players)

    # Ensure there's at least MIN_PLAYERS total
    if num_human_players == 0:
        min_computers = max(MIN_COMPUTER_PLAYERS, MIN_PLAYERS) # Need at least 2 computers if no humans

    if min_computers > max_computers:
         print(f"Error: Cannot have {num_human_players} human players and satisfy player limits.")
         print(f"Requires between {MIN_PLAYERS} and {MAX_PLAYERS} total players.")
         # This case should ideally be prevented by checks in get_num_human_players,
         # but added as a safeguard. We might exit or re-prompt here.
         # For now, let's force the minimum valid number of computers.
         print(f"Setting computer players to the minimum required: {min_computers}")
         return min_computers


    while True:
        try:
            # Adjust prompt based on whether it's a fixed choice
            if min_computers == max_computers:
                 print(f"Number of computer players automatically set to {min_computers} to meet player limits.")
                 return min_computers

            prompt = f"Enter number of computer players ({min_computers}-{max_computers}): "
            num = int(input(prompt).strip())

            if min_computers <= num <= max_computers:
                 # Final check for total players
                 if MIN_PLAYERS <= (num_human_players + num) <= MAX_PLAYERS:
                     return num
                 else:
                      # This condition should technically be covered by the min/max calculation,
                      # but double-checking helps.
                      print(f"Invalid total players ({num_human_players + num}). Must be between {MIN_PLAYERS} and {MAX_PLAYERS}.")

            else:
                print(f"Please enter a number between {min_computers} and {max_computers}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_player_names(num_human_players, num_computer_players):
    """Gets names for human players and generates names for computers."""
    names = []
    # Get human names
    for i in range(num_human_players):
        while True:
            name = input(f"Enter name for Human Player {i+1}: ").strip()
            # Basic validation
            if name and name not in names and not name.lower().startswith("computer"):
                names.append(name)
                break
            elif name.lower().startswith("computer"):
                 print("Name cannot start with 'Computer'.")
            elif name in names:
                 print(f"Name '{name}' is already taken.")
            else:
                print("Name cannot be empty.")

    # Generate computer names
    for i in range(num_computer_players):
        comp_name = f"Computer {i+1}"
        # Ensure generated name doesn't clash with a human name (highly unlikely)
        original_comp_name = comp_name
        count = 2
        while comp_name in names:
            comp_name = f"{original_comp_name} ({count})"
            count += 1
        names.append(comp_name)

    return names


def display_title_screen():
    """Displays the improved ASCII art title screen with animation."""
    clear_screen()
    title_lines = [
        r"╔═════════════════════════════════════════════════════════════╗",
        r"║                                                             ║",
        r"║   WW      WW   AAAAAA   RRRRRRR                             ║",
        r"║   WW      WW  AA    AA  RR    RR                            ║",
        r"║   WW   W  WW  AAAAAAAA  RRRRRRR      (Multiplayer/Multi-Deck)║",
        r"║   WW  W W WW  AA    AA  RR   RR                             ║",
        r"║   WWW   WWW  AA    AA  RR    RR                             ║",
        r"║                                                             ║",
        r"╠═════════════════════════════════════════════════════════════╣",
        r"║                      By: ShadowHarvy & AI                   ║",
        r"╚═════════════════════════════════════════════════════════════╝"
    ]
    for line in title_lines:
        print(line)
        sys.stdout.flush() # Ensure the line is printed immediately
        time.sleep(0.07) # Slightly faster animation
    time.sleep(1.5)


def display_loading_screen():
    """Displays a fake loading sequence."""
    clear_screen()
    print("Initializing Hyper-Dimensional Card Shuffler...")
    time.sleep(0.6)
    print("Calibrating Multi-Deck Randomness Matrix...")
    time.sleep(0.7)
    print("Loading Advanced Settings & Polygons...")
    load_chars = ['|', '/', '-', '\\']
    for i in range(15):
        print(f"[{load_chars[i % len(load_chars)]}] ", end='\r')
        time.sleep(0.1)
    print("[OK]      ")
    time.sleep(1)
    clear_screen()


# --- Settings Class ---
class Settings:
    """Manages game settings, including saving/loading via JSON."""
    def __init__(self):
        # Default values
        self.use_ascii_art = True
        self.show_flavor_text = True
        self.clear_screen_enabled = True
        self.shuffle_won_cards = True
        self.max_rounds = DEFAULT_MAX_ROUNDS
        self.autoplay = False
        self.war_face_down_count = 3
        self.num_decks = DEFAULT_NUM_DECKS # New setting for number of decks

        self._load_settings() # Load settings from file

    def _load_settings(self):
        """Loads settings from the JSON file."""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Update attributes safely
                self.use_ascii_art = loaded_data.get('use_ascii_art', self.use_ascii_art)
                self.show_flavor_text = loaded_data.get('show_flavor_text', self.show_flavor_text)
                self.clear_screen_enabled = loaded_data.get('clear_screen_enabled', self.clear_screen_enabled)
                self.shuffle_won_cards = loaded_data.get('shuffle_won_cards', self.shuffle_won_cards)
                self.max_rounds = loaded_data.get('max_rounds', self.max_rounds)
                self.autoplay = loaded_data.get('autoplay', self.autoplay)
                self.war_face_down_count = loaded_data.get('war_face_down_count', self.war_face_down_count)
                self.num_decks = loaded_data.get('num_decks', self.num_decks) # Load num_decks

                # Validate loaded values
                if self.war_face_down_count < 1: self.war_face_down_count = 1
                if self.num_decks < 1: self.num_decks = 1

        except FileNotFoundError:
            print(f"Settings file ({SETTINGS_FILE}) not found. Using defaults.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error reading settings file ({e}). Using defaults.")
            self.__init__()
        except Exception as e:
            print(f"An unexpected error occurred loading settings ({e}). Using defaults.")
            self.__init__()

    def _save_settings(self):
        """Saves the current settings to the JSON file."""
        settings_data = {
            'use_ascii_art': self.use_ascii_art,
            'show_flavor_text': self.show_flavor_text,
            'clear_screen_enabled': self.clear_screen_enabled,
            'shuffle_won_cards': self.shuffle_won_cards,
            'max_rounds': self.max_rounds,
            'autoplay': self.autoplay,
            'war_face_down_count': self.war_face_down_count,
            'num_decks': self.num_decks, # Save num_decks
        }
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
        except IOError as e:
            print(f"Warning: Could not save settings ({e}).")
        except Exception as e:
            print(f"An unexpected error occurred saving settings ({e}).")

    def _get_status(self, setting_value):
        """Returns 'ON' or 'OFF' string for display."""
        return "ON" if setting_value else "OFF"

    def display_menu(self):
        """Displays the settings configuration menu."""
        clear_screen()
        print("╔══════════════════════════════════════════╗")
        print("║      War Settings (Multiplayer/Deck)     ║")
        print("╠══════════════════════════════════════════╣")
        max_round_str = str(self.max_rounds) if self.max_rounds > 0 else "Unlimited"
        print(f"║ M. Max Rounds          : {max_round_str:<16} ║")
        print(f"║ W. War Face-Down Cards : {self.war_face_down_count:<16} ║")
        print(f"║ D. Number of Decks     : {self.num_decks:<16} ║") # Display num_decks
        print("║------------------------------------------║")
        print(f"║ 1. Use ASCII Card Art  : {self._get_status(self.use_ascii_art):<16} ║")
        print(f"║ 2. Show Flavor Text    : {self._get_status(self.show_flavor_text):<16} ║")
        print(f"║ 3. Clear Screen        : {self._get_status(self.clear_screen_enabled):<16} ║")
        print(f"║ 4. Shuffle Won Cards   : {self._get_status(self.shuffle_won_cards):<16} ║")
        print(f"║ 5. Autoplay (Normal)   : {self._get_status(self.autoplay):<16} ║")
        print("╠══════════════════════════════════════════╣")
        print("║ S. Start Game                            ║")
        print("╚══════════════════════════════════════════╝")

    def configure(self):
        """Allows the user to toggle settings before starting."""
        needs_save = False
        while True:
            self.display_menu()
            choice = input("Enter option to change, or 'S' to start: ").strip().lower()

            if choice == 'm': # Max Rounds
                while True:
                    try:
                        new_max = input(f"Enter max rounds (current: {self.max_rounds if self.max_rounds > 0 else 'Unlimited'}, 0 for Unlimited): ").strip()
                        val = int(new_max)
                        if val >= 0:
                            if self.max_rounds != val: self.max_rounds = val; needs_save = True
                            break
                        else: print("Please enter a non-negative number.")
                    except ValueError: print("Invalid input. Please enter a number (or 0).")
            elif choice == 'w': # War Face-Down
                 while True:
                    try:
                        new_count = input(f"Enter number of face-down cards in War (current: {self.war_face_down_count}, min 1): ").strip()
                        val = int(new_count)
                        if val >= 1:
                            if self.war_face_down_count != val: self.war_face_down_count = val; needs_save = True
                            break
                        else: print("Please enter a number >= 1.")
                    except ValueError: print("Invalid input. Please enter a number.")
            elif choice == 'd': # Number of Decks
                 while True:
                    try:
                        new_decks = input(f"Enter number of decks to use (current: {self.num_decks}, min 1): ").strip()
                        val = int(new_decks)
                        if val >= 1:
                             # Optional: Add a reasonable upper limit? e.g., 8 decks
                             # if val > 8: print("Maximum 8 decks allowed."); continue
                            if self.num_decks != val: self.num_decks = val; needs_save = True
                            break
                        else: print("Please enter a number >= 1.")
                    except ValueError: print("Invalid input. Please enter a number.")

            elif choice == '1': self.use_ascii_art = not self.use_ascii_art; needs_save = True
            elif choice == '2': self.show_flavor_text = not self.show_flavor_text; needs_save = True
            elif choice == '3': self.clear_screen_enabled = not self.clear_screen_enabled; needs_save = True
            elif choice == '4': self.shuffle_won_cards = not self.shuffle_won_cards; needs_save = True
            elif choice == '5': self.autoplay = not self.autoplay; needs_save = True
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
class Card:
    """Represents a single playing card."""
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.display_rank = DISPLAY_RANKS[rank]
        self.value = VALUES[rank]
        self.suit_symbol = SUIT_SYMBOLS[suit]

    def __str__(self):
        """Returns a multi-line ASCII string representation of the card."""
        top_rank = self.display_rank.ljust(2)
        bottom_rank = self.display_rank.rjust(2)
        suit_line = f"│    {self.suit_symbol}    │"
        # Basic centering, might need adjustment for '10'
        if self.rank == '10':
             top_rank = self.display_rank # '10' takes 2 chars
             bottom_rank = self.display_rank
             return (
                 f"┌─────────┐\n"
                 f"│ {top_rank}      │\n"
                 f"│         │\n"
                 f"{suit_line}\n"
                 f"│         │\n"
                 f"│      {bottom_rank} │\n"
                 f"└─────────┘"
            )
        else:
             return (
                f"┌─────────┐\n"
                f"│ {top_rank}      │\n"
                f"│         │\n"
                f"{suit_line}\n"
                f"│         │\n"
                f"│      {bottom_rank} │\n"
                f"└─────────┘"
            )


    def simple_str(self):
        """Returns a simple one-line string representation."""
        original_ranks_full = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
        full_rank_name = original_ranks_full[self.value - 2]
        return f"{full_rank_name} of {self.suit}"

    def __lt__(self, other): return self.value < other.value
    def __gt__(self, other): return self.value > other.value
    def __eq__(self, other): return self.value == other.value
    def __repr__(self):
        return f"Card({self.suit}, {self.rank})"


class Deck:
    """Represents one or more decks of 52 playing cards combined."""
    def __init__(self, num_decks=1):
        self.cards = []
        # Create the specified number of decks
        for _ in range(num_decks):
            self.cards.extend([Card(suit, rank) for suit in SUITS for rank in RANKS])
        print(f"Created a combined deck with {len(self.cards)} cards ({num_decks} deck{'s' if num_decks > 1 else ''}).")


    def shuffle(self, settings, is_fast_mode):
        """Shuffles the combined deck randomly."""
        if settings.clear_screen_enabled: clear_screen()
        print(f"Shuffling {len(self.cards)} cards...")
        if not is_fast_mode: time.sleep(1 + 0.2 * settings.num_decks) # Longer shuffle for more cards
        random.shuffle(self.cards)

    def deal(self, players, settings, is_fast_mode):
        """Deals the combined deck as evenly as possible among players."""
        num_players = len(players)
        num_cards_total = len(self.cards)
        if settings.clear_screen_enabled: clear_screen()
        print(f"Dealing {num_cards_total} cards to {num_players} players...")
        time.sleep(0.5)

        player_hands = {player.name: [] for player in players}
        player_displays = {player.name: "" for player in players}
        # Adjust deal delay based on total cards and mode
        deal_delay = 0.005 if is_fast_mode else (0.02 if num_cards_total > 100 else 0.03)

        for i, card in enumerate(self.cards):
            current_player = players[i % num_players]
            player_hands[current_player.name].append(card)

            if not is_fast_mode:
                # Only update display periodically to speed up dealing animation
                if i % (num_players * 2) == 0 or i == num_cards_total - 1: # Update every few cards per player
                    player_displays[current_player.name] += DEALING_CARD_PLACEHOLDER + " "
                    if settings.clear_screen_enabled: clear_screen()
                    print("Dealing...")
                    for player in players:
                        # Show approx count during deal
                        approx_count = len(player_displays[player.name].split())
                        print(f"{player.name.ljust(15)}: {approx_count} cards {player_displays[player.name][-20:]}") # Show last part of dealing string
                    time.sleep(deal_delay)

        # Assign hands to player objects
        for player in players:
            player.hand = player_hands[player.name]

        if not is_fast_mode:
             if settings.clear_screen_enabled: clear_screen()
             print("Dealing complete!")
             for player in players:
                 print(f"{player.name} received {player.cards_left()} cards.")
             time.sleep(1.5 + 0.5 * num_players)

        self.cards = [] # Deck is now empty


class Player:
    """Represents a player in the game."""
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.is_active = True
        self.is_human = not name.lower().startswith("computer") # Track if human

    def play_card(self):
        """Removes and returns the top card from the player's hand."""
        return self.hand.pop(0) if self.hand else None

    def add_cards(self, cards, settings):
        """Adds a list of cards to the bottom of the player's hand."""
        if not cards: return
        valid_cards = [c for c in cards if c is not None]
        if not valid_cards: return

        if settings.shuffle_won_cards:
            random.shuffle(valid_cards)
        self.hand.extend(valid_cards)

    def has_cards(self):
        """Checks if the player still has cards."""
        return len(self.hand) > 0

    def cards_left(self):
        """Returns the number of cards the player has."""
        return len(self.hand)

    def set_active(self, status):
        """Sets the player's active status."""
        self.is_active = status


class GameStats:
    """Tracks game statistics for multiple players."""
    def __init__(self, player_names):
        self.rounds_played = 0
        self.wars_occurred = 0
        self.max_pot_won = 0
        self.max_pot_winner = "No one"
        self.win_streaks = defaultdict(int)
        self.max_streaks = defaultdict(int)
        self.round_wins = defaultdict(int)
        self.war_wins = defaultdict(int)
        self.player_names = list(player_names) # Ensure it's a list

    def increment_round(self):
        self.rounds_played += 1

    def increment_war(self):
        self.wars_occurred += 1

    def record_round_win(self, winner_name):
        """Records a regular round win and updates streaks."""
        if winner_name not in self.player_names: return # Safety check
        self.round_wins[winner_name] += 1
        self.win_streaks[winner_name] += 1
        if self.win_streaks[winner_name] > self.max_streaks[winner_name]:
            self.max_streaks[winner_name] = self.win_streaks[winner_name]
        # Reset streaks for all other players
        for name in self.player_names:
            if name != winner_name:
                self.win_streaks[name] = 0

    def record_war_win(self, winner_name):
        """Records a war win."""
        if winner_name not in self.player_names: return # Safety check
        self.war_wins[winner_name] += 1
        # Note: record_round_win should also be called by the war logic
        # to handle streaks correctly for the overall war outcome.

    def reset_streaks_after_tie(self, active_player_names):
        """Resets streaks for all currently active players on a tie."""
        for name in active_player_names:
             if name in self.player_names: # Check if name is valid
                self.win_streaks[name] = 0

    def check_pot(self, pot_size, winner_name):
        """Checks if the current pot is the largest won so far."""
        if winner_name not in self.player_names and winner_name != "No one": return # Safety
        if pot_size > self.max_pot_won:
            self.max_pot_won = pot_size
            self.max_pot_winner = winner_name

    def display(self):
        """Prints the final game statistics."""
        print("\n--- Game Statistics ---")
        print(f"Total Rounds Played: {self.rounds_played}")
        print(f"Wars Occurred: {self.wars_occurred}")
        if self.max_pot_won > 0:
            print(f"Largest Pot Won: {self.max_pot_won} cards (by {self.max_pot_winner})")
        else:
            print("Largest Pot Won: N/A")
        print("\nPlayer Stats:")
        # Sort names for consistent display order
        sorted_names = sorted(self.player_names)
        for name in sorted_names:
            # Check if player actually participated (might have been removed if names changed)
            if name in self.round_wins or name in self.war_wins or name in self.max_streaks:
                 print(f"  {name}:")
                 print(f"    Round Wins: {self.round_wins.get(name, 0)}")
                 print(f"    War Wins: {self.war_wins.get(name, 0)}")
                 print(f"    Longest Win Streak: {self.max_streaks.get(name, 0)}")
            # else:
            #      print(f"  {name}: (No stats recorded)") # Optional: show players with 0 stats
        print("-----------------------")


# --- Display Functions ---
def display_played_cards(played_cards_dict, settings):
    """Displays the cards played by each player in the current round."""
    print("\nCards Played:")
    if not played_cards_dict:
        print("  (No cards played this round)")
        return

    # Use simple text if ASCII is off, or too many players
    if not settings.use_ascii_art or len(played_cards_dict) > 3:
        for name, card in played_cards_dict.items():
            if card: print(f"  {name}: {card.simple_str()}")
            else: print(f"  {name}: (Error: Missing Card)") # Should not happen
        return

    # Attempt side-by-side ASCII for 1-3 players
    player_names = list(played_cards_dict.keys())
    cards = list(played_cards_dict.values())
    lines_list = [str(card).split('\n') for card in cards if card] # Ensure card exists

    if not lines_list: # Handle case where cards might be None unexpectedly
         print("  (Error displaying cards)")
         return

    max_lines = max(len(lines) for lines in lines_list)
    # Get width from the first line of the first card
    card_width = len(lines_list[0][0]) if lines_list and lines_list[0] else 10

    # Print headers (player names)
    header_line = ""
    for name in player_names:
        header_line += name.center(card_width) + "   "
    print(header_line.rstrip())

    # Print card lines
    for i in range(max_lines):
        row_line = ""
        for idx, lines in enumerate(lines_list):
            # Check if the original card for this index existed
            if idx < len(cards) and cards[idx]:
                 row_line += (lines[i] if i < len(lines) else ' ' * card_width) + "   "
            else: # Placeholder if card was missing
                 row_line += ' ' * card_width + "   "
        print(row_line.rstrip())


def display_face_down_row(count, player_name, settings):
    """Prints a row of face-down cards if ASCII art is enabled."""
    if not settings.use_ascii_art:
        print(f"{player_name} places {count} card(s) face down.")
        return

    if count <= 0: return

    lines = FACE_DOWN_CARD.split('\n')
    card_width = len(lines[0])
    # Simple horizontal layout
    print(f"{player_name}'s face-down cards:")
    for i in range(len(lines)):
        row_line = (lines[i] + "   ") * count
        print(row_line.rstrip())


# --- Core Game Logic ---
# Global variable for fast mode, accessed by functions if needed
# Declared here for clarity, set in game_loop
is_fast_mode = False

def play_war_round(warring_players, cards_on_table, stats, settings):
    """Handles a 'War' round among the specified players."""
    # Access global is_fast_mode
    global is_fast_mode

    stats.increment_war()
    if settings.clear_screen_enabled and not is_fast_mode: clear_screen()

    war_comment = f" ({random.choice(WAR_COMMENTS)})" if settings.show_flavor_text else ""
    player_names_str = ", ".join([p.name for p in warring_players])
    print("\n" + "="*10 + f" W A R between {player_names_str}!{war_comment} " + "="*10)

    initial_pot = len(cards_on_table)
    print(f"\nCards initially contested: {initial_pot}")
    print("Current card counts:")
    for p in warring_players:
        print(f"  {p.name}: {p.cards_left()} cards")
    if not is_fast_mode: time.sleep(2.0)

    # --- Face-Down Cards ---
    face_down_cards_per_player = settings.war_face_down_count
    print(f"\nEach warring player needs {face_down_cards_per_player} face-down card(s) + 1 face-up card.")
    if not is_fast_mode: time.sleep(1.5)

    war_face_down_pot = []
    players_in_this_war_round = [] # Track who actually plays face-up

    # Create a copy to iterate over, as we might modify the original list implicitly
    current_warring_players = list(warring_players)

    for player in current_warring_players:
        # Ensure player is still active (might have been eliminated in a previous step/round)
        if not player.is_active:
             continue

        cards_needed = face_down_cards_per_player + 1
        player_cards_left = player.cards_left() # Get current count

        if player_cards_left < cards_needed:
            print(f"\n{player.name} only has {player_cards_left} card(s) left!")
            num_face_down = max(0, player_cards_left - 1)
            print(f"{player.name} places {num_face_down} card(s) face down.")
            if not is_fast_mode: time.sleep(1)

            down_cards = []
            if num_face_down > 0:
                display_face_down_row(num_face_down, player.name, settings)
                down_cards = [player.play_card() for _ in range(num_face_down)]
                war_face_down_pot.extend(filter(None, down_cards))

            # Check if they have the face-up card left
            if player.has_cards():
                 players_in_this_war_round.append(player)
            else:
                 print(f"{player.name} ran out completely placing face-down cards!")
                 # Player is eliminated from the war, cards remain in pot
                 player.set_active(False) # Mark as inactive for the main game loop check
            if not is_fast_mode: time.sleep(1.5)

        else:
            # Player has enough cards
            print(f"\n{player.name} places {face_down_cards_per_player} card(s) face down...")
            if not is_fast_mode: time.sleep(1)
            display_face_down_row(face_down_cards_per_player, player.name, settings)
            down_cards = [player.play_card() for _ in range(face_down_cards_per_player)]
            war_face_down_pot.extend(filter(None, down_cards))
            players_in_this_war_round.append(player) # Will play face-up card
            if not is_fast_mode: time.sleep(1.5)

    # Add the face-down cards to the main pot
    cards_on_table.extend(war_face_down_pot)
    print(f"\nPot size is now {len(cards_on_table)} cards...")
    if not is_fast_mode: time.sleep(1.5)

    # Filter out any players who became inactive during face-down placement
    players_in_this_war_round = [p for p in players_in_this_war_round if p.is_active]

    # Check if enough players remain for the face-up part
    if len(players_in_this_war_round) < 2:
        print("\nNot enough active players remaining in the war to compare face-up cards!")
        if not is_fast_mode: time.sleep(1.5)
        if len(players_in_this_war_round) == 1:
            winner = players_in_this_war_round[0]
            print(f"{winner.name} is the last one standing in this war!")
            winner.add_cards(cards_on_table, settings)
            print(f"{winner.name} collects all {len(cards_on_table)} cards.")
            stats.check_pot(len(cards_on_table), winner.name)
            stats.record_war_win(winner.name)
            stats.record_round_win(winner.name) # Also counts as round win
            if not is_fast_mode: time.sleep(3)
            return True # War resolved
        else:
            print(f"No players left capable of playing face-up. The pot of {len(cards_on_table)} cards is discarded.")
            if not is_fast_mode: time.sleep(3)
            return True # War technically resolved (ended badly)

    # --- Face-Up Cards ---
    print("\nPlaying face-up War cards...")
    if not is_fast_mode: time.sleep(1.0)

    war_face_up_cards = {} # {player_name: Card}
    highest_card_value = -1
    winners = [] # List of players who tied for highest card

    # Iterate over a copy in case a player runs out playing the card
    active_players_for_faceup = list(players_in_this_war_round)
    for player in active_players_for_faceup:
        card = player.play_card()
        if card:
            war_face_up_cards[player.name] = card
            print(f"  {player.name} plays: {card.simple_str()}")
            if not is_fast_mode: time.sleep(0.8)

            if card.value > highest_card_value:
                highest_card_value = card.value
                winners = [player]
            elif card.value == highest_card_value:
                winners.append(player)
        else:
            # Player ran out exactly on the face-up card
            print(f"{player.name} ran out playing the face-up War card!")
            player.set_active(False)
            # Remove from contention for this war round
            if player in players_in_this_war_round:
                 players_in_this_war_round.remove(player)
            if player in winners: # Should also be removed if they were a potential winner
                 winners.remove(player)


    # Add face-up cards to the main pot
    cards_on_table.extend(war_face_up_cards.values())
    print(f"\nComparing War cards...")
    if not is_fast_mode: time.sleep(1.5)

    # --- Determine War Winner ---
    # Filter winners list again for any players who ran out playing the face-up card
    winners = [p for p in winners if p.is_active]

    if len(winners) == 1:
        winner = winners[0]
        stats.record_war_win(winner.name)
        stats.record_round_win(winner.name) # War win implies round win
        win_comment = f" {random.choice(PLAYER_WINS_COMMENTS if winner.is_human else COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
        print(f"\n{winner.name} wins the war!{win_comment}")
        winner.add_cards(cards_on_table, settings)
        print(f"{winner.name} collects {len(cards_on_table)} cards.")
        stats.check_pot(len(cards_on_table), winner.name)
        if not is_fast_mode: time.sleep(3.5)
        return True # War resolved

    elif len(winners) > 1:
        # Another tie! Recursive war.
        tied_names = ", ".join([p.name for p in winners])
        print(f"\nWar cards tied again between {tied_names}! Another War begins...")
        if not is_fast_mode: time.sleep(2)
        # Recursively call war with only the currently tied & active players
        return play_war_round(winners, cards_on_table, stats, settings)
    else:
        # No active winners left (e.g., all ran out simultaneously)
        print("\nNo active winner remaining after comparing face-up cards.")
        print(f"The pot of {len(cards_on_table)} cards is discarded.")
        if not is_fast_mode: time.sleep(3)
        return True # War ended (unresolved winner)


def check_max_rounds_winner(active_players, settings):
    """Determines the winner if max rounds is reached based on card count."""
    global is_fast_mode # Access global
    if settings.clear_screen_enabled and not is_fast_mode: clear_screen()
    print("\n" + "="*10 + f" Maximum Rounds Reached ({settings.max_rounds}) " + "="*10)
    print("Determining winner based on card count...")
    if not is_fast_mode: time.sleep(2)

    max_cards = -1
    winners = []
    print("Final Card Counts:")
    for player in active_players:
        count = player.cards_left()
        print(f"  {player.name}: {count} cards")
        if count > max_cards:
            max_cards = count
            winners = [player]
        elif count == max_cards:
            winners.append(player)

    if len(winners) == 1:
        print(f"\n{winners[0].name} wins with the most cards ({max_cards})!")
        return winners[0]
    else:
        tied_names = ", ".join([p.name for p in winners])
        print(f"\nIt's a TIE between {tied_names} with {max_cards} cards each!")
        return None # Indicates a draw


def game_loop():
    """Main function to run the Multiplayer War game."""
    global is_fast_mode # Allow modification of the global variable

    # --- Title and Loading ---
    display_title_screen()
    display_loading_screen()

    # --- Initial Setup ---
    settings = Settings() # Loads settings
    is_fast_mode = get_game_mode() # Set global based on user choice
    num_human_players = get_num_human_players()
    num_computer_players = get_num_computer_players(num_human_players)
    player_names = get_player_names(num_human_players, num_computer_players)
    settings.configure() # Allow settings adjustment (incl. num_decks)

    # --- Game Setup ---
    deck = Deck(settings.num_decks) # Create deck with specified number
    stats = GameStats(player_names)
    players = [Player(name) for name in player_names]

    deck.shuffle(settings, is_fast_mode)
    deck.deal(players, settings, is_fast_mode)

    active_players = list(players)
    game_over_reason = None

    # --- Main Game Loop ---
    while len(active_players) > 1 and \
          (settings.max_rounds <= 0 or stats.rounds_played < settings.max_rounds):

        stats.increment_round()
        round_num = stats.rounds_played

        # --- Display Round Info ---
        if settings.clear_screen_enabled and not is_fast_mode: clear_screen()
        print(f"\n====== Round {round_num}{'/' + str(settings.max_rounds) if settings.max_rounds > 0 else ''} ======")
        print("Active Players & Card Counts:")
        # Sort active players for consistent display order
        active_players.sort(key=lambda p: p.name)
        for p in active_players:
             streak_info = f"(Streak: {stats.win_streaks.get(p.name, 0)})" if stats.win_streaks.get(p.name, 0) > 0 else ""
             print(f"  {p.name}: {p.cards_left()} cards {streak_info}")
        print("-" * 35)

        # Handle input/autoplay
        human_player_active = any(p.is_human for p in active_players)
        if not is_fast_mode and not settings.autoplay and human_player_active:
            try:
                input("Press Enter to play round...")
            except KeyboardInterrupt:
                if settings.clear_screen_enabled: clear_screen()
                print("\nExiting game."); return
        elif not is_fast_mode and settings.autoplay:
            print("Autoplaying...")
            time.sleep(0.4) # Slightly faster autoplay delay
        elif is_fast_mode:
            # Minimal delay in fast mode, flush output
            time.sleep(0.005)
            sys.stdout.flush()

        # --- Play Cards ---
        cards_on_table = []
        played_cards = {} # {player_name: Card}
        highest_card_value = -1
        round_winners = [] # Players who tied for highest card this round

        if settings.clear_screen_enabled and not is_fast_mode: clear_screen()
        print(f"\n====== Round {round_num}{'/' + str(settings.max_rounds) if settings.max_rounds > 0 else ''} Plays ======")

        # Iterate over a copy of active players for safety during card playing/elimination
        current_round_players = list(active_players)
        for player in current_round_players:
             # Double check if player is still active before playing
             if not player.is_active:
                  continue

             card = player.play_card()
             if card:
                 played_cards[player.name] = card
                 cards_on_table.append(card)

                 if card.value > highest_card_value:
                     highest_card_value = card.value
                     round_winners = [player]
                 elif card.value == highest_card_value:
                     round_winners.append(player)
             else:
                 # Player ran out *before* playing this round
                 print(f"{player.name} ran out of cards before playing!")
                 player.set_active(False)
                 if player in active_players: # Remove from main active list
                      active_players.remove(player)
                 # No card played, not added to played_cards or round_winners

        # Display the cards that were played
        display_played_cards(played_cards, settings)
        if not is_fast_mode: time.sleep(1.5 + 0.2 * len(played_cards))

        # Filter round_winners to only include players still active after playing cards
        round_winners = [p for p in round_winners if p.is_active]

        # --- Compare and Resolve Round ---
        if not round_winners:
             print("\nNo active players had the highest card (or no cards played).")
             if not is_fast_mode: time.sleep(2)
             # Elimination check below will handle players running out

        elif len(round_winners) == 1:
            winner = round_winners[0]
            stats.record_round_win(winner.name)
            win_comment = f" {random.choice(PLAYER_WINS_COMMENTS if winner.is_human else COMPUTER_WINS_COMMENTS)}" if settings.show_flavor_text else ""
            print(f"\n{winner.name} wins the round!{win_comment}")
            winner.add_cards(cards_on_table, settings)
            print(f"{winner.name} collects {len(cards_on_table)} cards.")
            stats.check_pot(len(cards_on_table), winner.name)
            if not is_fast_mode: time.sleep(3.0)

        else:
            # Tie! War time.
            tied_names = ", ".join([p.name for p in round_winners])
            print(f"\nCards tied between {tied_names}!")
            active_names = [p.name for p in active_players] # Get current active names for streak reset
            stats.reset_streaks_after_tie(active_names)
            if not is_fast_mode: time.sleep(1)
            # Pass only the tied players to the war function
            war_resolved = play_war_round(round_winners, cards_on_table, stats, settings)
            # Elimination check below will handle players running out during war

        # --- Check for Player Elimination (Post-Round/War) ---
        # Iterate over a copy, as we modify active_players list
        players_to_check = list(active_players)
        for player in players_to_check:
            if not player.has_cards() and player.is_active:
                print(f"\n{player.name} has run out of cards and is eliminated!")
                player.set_active(False)
                active_players.remove(player) # Remove from the list for next round
                if not is_fast_mode: time.sleep(1.5)

        # Check if only one player remains
        if len(active_players) <= 1:
            game_over_reason = "Only one player remaining."
            break

    # --- Determine Winner & Show Stats ---
    if settings.clear_screen_enabled: clear_screen()
    print("\n" + "="*15 + " Game Over " + "="*15)
    if not is_fast_mode: time.sleep(1)

    final_winner = None
    # Check if max rounds was the reason for stopping
    if settings.max_rounds > 0 and stats.rounds_played >= settings.max_rounds and len(active_players) > 1:
        final_winner = check_max_rounds_winner(active_players, settings) # Returns winner or None for draw
        if final_winner:
             game_over_reason = f"Max rounds ({settings.max_rounds}) reached. {final_winner.name} had the most cards."
        else:
             game_over_reason = f"Max rounds ({settings.max_rounds}) reached. Draw between players with the most cards."

    # Otherwise, game ended because only one player was left
    elif len(active_players) == 1:
        final_winner = active_players[0]
        print(f"\n{final_winner.name} is the last player standing and wins the game!")
        print(f"Reason: {game_over_reason if game_over_reason else 'All other players eliminated.'}")
    elif len(active_players) == 0:
        print("\nAll players were eliminated simultaneously! It's a draw!")
        game_over_reason = "Simultaneous elimination."
    else:
         # Should only happen if loop exited unexpectedly
         print("\nGame concluded unexpectedly.")
         print(f"Reason: {game_over_reason if game_over_reason else 'Unknown.'}")
         print(f"Remaining players: {[p.name for p in active_players]}")

    # Display statistics
    stats.display()


# --- Start the Game ---
if __name__ == "__main__":
    try:
        game_loop()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nThanks for playing Multiplayer Multi-Deck War!")


