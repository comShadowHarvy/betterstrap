"""
Tournament Mode for Blackjack
Features: Timed rounds, leaderboard system, elimination mechanics
"""

import time
from card import COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_BOLD, COLOR_DIM, COLOR_RESET
from game_utils import clear_screen

# Tournament constants
TOURNAMENT_STARTING_CHIPS = 500
TOURNAMENT_MIN_BET = 10
TOURNAMENT_ROUNDS = 10
TOURNAMENT_ELIMINATION_THRESHOLD = 0  # Eliminated if chips <= this

class Tournament:
    """Manages tournament state, leaderboard, and elimination"""
    
    def __init__(self, num_rounds=TOURNAMENT_ROUNDS):
        self.num_rounds = num_rounds
        self.current_round = 0
        self.start_time = None
        self.leaderboard = {}  # player_name: chips
        self.eliminated_players = []
        
    def display_tournament_intro(self):
        """Display tournament welcome screen"""
        clear_screen()
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}           🏆 BLACKJACK TOURNAMENT 🏆{COLOR_RESET}")
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Tournament Rules:{COLOR_RESET}")
        print(f"  • Starting chips: {COLOR_GREEN}{TOURNAMENT_STARTING_CHIPS}{COLOR_RESET}")
        print(f"  • Total rounds: {COLOR_YELLOW}{self.num_rounds}{COLOR_RESET}")
        print(f"  • Minimum bet per round: {COLOR_YELLOW}{TOURNAMENT_MIN_BET}{COLOR_RESET}")
        print(f"  • Players with {COLOR_RED}0 chips{COLOR_RESET} are eliminated")
        print(f"  • Player with most chips after {self.num_rounds} rounds wins!\n")
        
        print(f"{COLOR_DIM}Compete against AI opponents to climb the leaderboard!{COLOR_RESET}")
        print(f"{COLOR_DIM}{'=' * 60}{COLOR_RESET}\n")
        
        input(f"{COLOR_YELLOW}Press Enter to begin tournament...{COLOR_RESET}")
        self.start_time = time.time()
    
    def start_round(self, round_num):
        """Display round start info"""
        self.current_round = round_num
        print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}=== ROUND {round_num}/{self.num_rounds} ==={COLOR_RESET}")
        time.sleep(0.8)
    
    def update_leaderboard(self, player_name, chips):
        """Update player's chip count in leaderboard"""
        self.leaderboard[player_name] = chips
    
    def check_elimination(self, player_name, chips):
        """Check if a player should be eliminated"""
        if chips <= TOURNAMENT_ELIMINATION_THRESHOLD and player_name not in self.eliminated_players:
            self.eliminated_players.append(player_name)
            print(f"\n{COLOR_RED}{COLOR_BOLD}💀 {player_name} has been ELIMINATED from the tournament!{COLOR_RESET}")
            time.sleep(2)
            return True
        return False
    
    def display_leaderboard(self, show_full=False):
        """Display current tournament standings"""
        print(f"\n{COLOR_CYAN}{COLOR_BOLD}📊 LEADERBOARD - Round {self.current_round}/{self.num_rounds}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 50}{COLOR_RESET}")
        
        # Sort by chips (descending)
        sorted_players = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (player, chips) in enumerate(sorted_players, 1):
            eliminated_marker = f" {COLOR_RED}[ELIMINATED]{COLOR_RESET}" if player in self.eliminated_players else ""
            
            # Medal for top 3
            medal = ""
            if rank == 1:
                medal = "🥇 "
            elif rank == 2:
                medal = "🥈 "
            elif rank == 3:
                medal = "🥉 "
            else:
                medal = f"{rank}. "
            
            chip_color = COLOR_GREEN if chips > TOURNAMENT_STARTING_CHIPS else (COLOR_YELLOW if chips > 100 else COLOR_RED)
            
            # Show all if full leaderboard requested, otherwise top 5
            if show_full or rank <= 5:
                print(f"{medal}{player}: {chip_color}{chips}{COLOR_RESET} chips{eliminated_marker}")
        
        if not show_full and len(sorted_players) > 5:
            print(f"{COLOR_DIM}... and {len(sorted_players) - 5} more{COLOR_RESET}")
        
        print(f"{COLOR_DIM}{'-' * 50}{COLOR_RESET}")
    
    def display_final_results(self):
        """Display tournament final results and winner"""
        clear_screen()
        elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        
        print(f"\n{COLOR_MAGENTA}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}           🏆 TOURNAMENT COMPLETE 🏆{COLOR_RESET}")
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Tournament duration: {minutes}m {seconds}s{COLOR_RESET}")
        print(f"{COLOR_CYAN}Rounds played: {self.current_round}{COLOR_RESET}\n")
        
        # Sort and display final standings
        sorted_players = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_players:
            winner_name, winner_chips = sorted_players[0]
            print(f"{COLOR_GREEN}{COLOR_BOLD}🎉 WINNER: {winner_name} with {winner_chips} chips! 🎉{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}{COLOR_BOLD}Final Standings:{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 50}{COLOR_RESET}")
        
        for rank, (player, chips) in enumerate(sorted_players, 1):
            medal = ""
            if rank == 1:
                medal = "🥇 "
                color = COLOR_GREEN
            elif rank == 2:
                medal = "🥈 "
                color = COLOR_CYAN
            elif rank == 3:
                medal = "🥉 "
                color = COLOR_YELLOW
            else:
                medal = f"{rank}. "
                color = COLOR_RESET
            
            eliminated = f" {COLOR_RED}[ELIMINATED]{COLOR_RESET}" if player in self.eliminated_players else ""
            print(f"{medal}{color}{player}: {chips} chips{COLOR_RESET}{eliminated}")
        
        print(f"{COLOR_DIM}{'-' * 50}{COLOR_RESET}\n")
        
        input(f"{COLOR_YELLOW}Press Enter to return to main menu...{COLOR_RESET}")


def run_tournament(game_class, settings):
    """
    Runs a complete tournament using the BlackjackGame class.
    
    Args:
        game_class: The BlackjackGame class to instantiate
        settings: Game settings dict
    """
    from player import AIPlayer, AIType
    import random
    import sys
    import os
    
    # Add parent directory to path to import GameMode
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from jack import GameMode
    
    # Initialize tournament
    tournament = Tournament(num_rounds=TOURNAMENT_ROUNDS)
    tournament.display_tournament_intro()
    
    # Create game instance
    game = game_class(game_mode=GameMode.TOURNAMENT, settings=settings)
    
    # Reset player chips for tournament
    game.human_player.chips = TOURNAMENT_STARTING_CHIPS
    game.human_player.name = "You"
    
    # Initialize AI players for tournament
    game.ai_players = []
    ai_names = ["Alice", "Bob", "Charlie", "Diana", "Ethan"]
    for name in ai_names[:5]:  # 5 AI opponents
        ai_type = random.choice(list(AIType))
        ai_player = AIPlayer(name, ai_type, TOURNAMENT_STARTING_CHIPS)
        game.ai_players.append(ai_player)
        tournament.update_leaderboard(name, TOURNAMENT_STARTING_CHIPS)
    
    tournament.update_leaderboard(game.human_player.name, game.human_player.chips)
    
    # Play rounds
    for round_num in range(1, TOURNAMENT_ROUNDS + 1):
        tournament.start_round(round_num)
        
        # Show leaderboard before round
        tournament.display_leaderboard()
        time.sleep(2)
        
        # Play one round (simplified betting for tournament)
        result = game.play_round()
        
        # Update leaderboard
        tournament.update_leaderboard(game.human_player.name, game.human_player.chips)
        for ai in game.ai_players:
            tournament.update_leaderboard(ai.name, ai.chips)
        
        # Check eliminations
        if tournament.check_elimination(game.human_player.name, game.human_player.chips):
            print(f"{COLOR_RED}You've been eliminated from the tournament!{COLOR_RESET}")
            break
        
        # Check if player wants to continue
        if result == 'quit':
            break
        
        time.sleep(1)
    
    # Show final results
    tournament.display_final_results()
