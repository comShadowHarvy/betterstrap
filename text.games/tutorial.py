"""
Tutorial Mode for Blackjack
Interactive walkthrough teaching new players the game
"""

import time
from card import COLOR_GREEN, COLOR_YELLOW, COLOR_RED, COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_BOLD, COLOR_DIM, COLOR_RESET
from game_utils import clear_screen

class Tutorial:
    """Interactive tutorial system for teaching blackjack"""
    
    def __init__(self):
        self.current_step = 0
        self.total_steps = 8
    
    def show_progress(self):
        """Show tutorial progress bar"""
        filled = int((self.current_step / self.total_steps) * 20)
        bar = "█" * filled + "░" * (20 - filled)
        print(f"{COLOR_CYAN}Tutorial Progress: [{bar}] {self.current_step}/{self.total_steps}{COLOR_RESET}\n")
    
    def wait_for_enter(self, prompt="Press Enter to continue..."):
        """Wait for user to press Enter"""
        input(f"{COLOR_YELLOW}{prompt}{COLOR_RESET}")
    
    def step_1_welcome(self):
        """Introduction to the tutorial"""
        clear_screen()
        self.current_step = 1
        self.show_progress()
        
        print(f"{COLOR_GREEN}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_GREEN}{COLOR_BOLD}     Welcome to the Blackjack Tutorial! 🎓{COLOR_RESET}")
        print(f"{COLOR_GREEN}{COLOR_BOLD}{'=' * 60}{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}This interactive tutorial will teach you:{COLOR_RESET}")
        print(f"  ✓ Basic rules and objective")
        print(f"  ✓ Card values")
        print(f"  ✓ How to play your hand")
        print(f"  ✓ Advanced actions (Double, Split, etc.)")
        print(f"  ✓ Betting strategy basics\n")
        
        print(f"{COLOR_DIM}The tutorial takes about 5 minutes to complete.{COLOR_RESET}\n")
        
        self.wait_for_enter()
    
    def step_2_objective(self):
        """Explain game objective"""
        clear_screen()
        self.current_step = 2
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 1: The Objective{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Goal:{COLOR_RESET} Beat the dealer by getting closer to {COLOR_BOLD}21{COLOR_RESET} without going over.\n")
        
        print(f"{COLOR_GREEN}You WIN if:{COLOR_RESET}")
        print(f"  • Your hand is closer to 21 than the dealer's")
        print(f"  • The dealer busts (goes over 21)")
        print(f"  • You get a Blackjack (Ace + 10-value card)\n")
        
        print(f"{COLOR_RED}You LOSE if:{COLOR_RESET}")
        print(f"  • Your hand goes over 21 (bust)")
        print(f"  • The dealer's hand is closer to 21 than yours\n")
        
        print(f"{COLOR_YELLOW}PUSH (tie):{COLOR_RESET}")
        print(f"  • You and the dealer have the same hand value")
        print(f"  • Your bet is returned\n")
        
        self.wait_for_enter()
    
    def step_3_card_values(self):
        """Explain card values"""
        clear_screen()
        self.current_step = 3
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 2: Card Values{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Number cards (2-10):{COLOR_RESET} Worth their face value")
        print(f"  Example: 5♠ = 5 points\n")
        
        print(f"{COLOR_CYAN}Face cards (J, Q, K):{COLOR_RESET} All worth 10 points")
        print(f"  Example: K♥ = 10 points, Q♦ = 10 points\n")
        
        print(f"{COLOR_CYAN}Aces (A):{COLOR_RESET} Worth 1 OR 11 points (your choice)")
        print(f"  Example: A♣ + 8♠ = 19 (Ace counts as 11)")
        print(f"  Example: A♣ + 8♠ + 5♦ = 14 (Ace counts as 1)\n")
        
        print(f"{COLOR_GREEN}{COLOR_BOLD}💎 BLACKJACK:{COLOR_RESET}")
        print(f"  Ace + 10-value card on first two cards")
        print(f"  Pays 3:2 (win 1.5x your bet!)\n")
        
        print(f"{COLOR_DIM}Tip: The game automatically counts Aces as 1 or 11 to give you the best hand.{COLOR_RESET}\n")
        
        self.wait_for_enter()
    
    def step_4_basic_actions(self):
        """Explain basic actions"""
        clear_screen()
        self.current_step = 4
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 3: Basic Actions{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}HIT (h):{COLOR_RESET} Take another card")
        print(f"  Use when: Your hand is low and you want to get closer to 21")
        print(f"  Example: You have 12, dealer shows 7 → HIT\n")
        
        print(f"{COLOR_CYAN}STAND (s):{COLOR_RESET} Keep your current hand")
        print(f"  Use when: You're happy with your total")
        print(f"  Example: You have 18, dealer shows 6 → STAND\n")
        
        print(f"{COLOR_GREEN}Quick Tips:{COLOR_RESET}")
        print(f"  • Always stand on 17 or higher")
        print(f"  • Hit on 11 or lower (you can't bust)")
        print(f"  • On 12-16, it depends on dealer's upcard\n")
        
        self.wait_for_enter()
    
    def step_5_advanced_actions(self):
        """Explain advanced actions"""
        clear_screen()
        self.current_step = 5
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 4: Advanced Actions{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}DOUBLE DOWN (d):{COLOR_RESET} Double your bet, get ONE more card, then stand")
        print(f"  Use when: You have a strong hand (9, 10, or 11)")
        print(f"  Example: You have 11, dealer shows 6 → DOUBLE DOWN\n")
        
        print(f"{COLOR_CYAN}SPLIT (p):{COLOR_RESET} Split matching cards into two separate hands")
        print(f"  Costs: Same as your original bet")
        print(f"  Use when: You have pairs like A-A or 8-8")
        print(f"  Example: You have 8♠ 8♥ → SPLIT into two hands\n")
        
        print(f"{COLOR_CYAN}SURRENDER (r):{COLOR_RESET} Give up and get half your bet back")
        print(f"  Use when: You have a terrible hand (e.g., 16 vs dealer Ace)")
        print(f"  Only available as your first action\n")
        
        print(f"{COLOR_YELLOW}INSURANCE:{COLOR_RESET} Side bet when dealer shows Ace")
        print(f"  Pays 2:1 if dealer has Blackjack")
        print(f"  Generally not recommended for beginners\n")
        
        self.wait_for_enter()
    
    def step_6_dealer_rules(self):
        """Explain dealer rules"""
        clear_screen()
        self.current_step = 6
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 5: How the Dealer Plays{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Dealer Rules:{COLOR_RESET}")
        print(f"  • Dealer MUST hit on 16 or lower")
        print(f"  • Dealer MUST stand on 17 or higher")
        print(f"  • Dealer has NO choices - follows fixed rules\n")
        
        print(f"{COLOR_GREEN}Why this matters:{COLOR_RESET}")
        print(f"  If dealer shows 6, they're likely to bust")
        print(f"  → You can play more conservatively\n")
        
        print(f"  If dealer shows 10 or Ace, they're strong")
        print(f"  → You need a better hand to win\n")
        
        print(f"{COLOR_DIM}Strategy Tip: When dealer shows 2-6 (weak cards), stand on lower totals.{COLOR_RESET}")
        print(f"{COLOR_DIM}When dealer shows 7-Ace (strong cards), hit more aggressively.{COLOR_RESET}\n")
        
        self.wait_for_enter()
    
    def step_7_betting(self):
        """Explain betting strategy"""
        clear_screen()
        self.current_step = 7
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 6: Betting Basics{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}Bankroll Management:{COLOR_RESET}")
        print(f"  • Start with small bets (5-10% of your chips)")
        print(f"  • Never bet more than you can afford to lose")
        print(f"  • Don't chase losses with bigger bets\n")
        
        print(f"{COLOR_GREEN}Good Betting Practices:{COLOR_RESET}")
        print(f"  ✓ Bet consistently - don't wildly vary amounts")
        print(f"  ✓ Set a limit and stick to it")
        print(f"  ✓ Walk away when you're ahead\n")
        
        print(f"{COLOR_RED}Avoid:{COLOR_RESET}")
        print(f"  ✗ Betting your entire bankroll on one hand")
        print(f"  ✗ Doubling bets after losses (Martingale)")
        print(f"  ✗ Playing when tilted or emotional\n")
        
        print(f"{COLOR_YELLOW}Payouts to Remember:{COLOR_RESET}")
        print(f"  • Regular win: 1:1 (bet $10, win $10)")
        print(f"  • Blackjack: 3:2 (bet $10, win $15)")
        print(f"  • Insurance: 2:1 (bet $5, win $10)\n")
        
        self.wait_for_enter()
    
    def step_8_practice(self):
        """Final step - practice time"""
        clear_screen()
        self.current_step = 8
        self.show_progress()
        
        print(f"{COLOR_MAGENTA}{COLOR_BOLD}Lesson 7: Time to Practice!{COLOR_RESET}\n")
        
        print(f"{COLOR_GREEN}🎉 Congratulations! You've completed the tutorial!{COLOR_RESET}\n")
        
        print(f"{COLOR_CYAN}You've learned:{COLOR_RESET}")
        print(f"  ✓ The objective of Blackjack")
        print(f"  ✓ Card values and Blackjacks")
        print(f"  ✓ Basic actions (Hit, Stand)")
        print(f"  ✓ Advanced actions (Double, Split, Surrender)")
        print(f"  ✓ How the dealer plays")
        print(f"  ✓ Betting strategy basics\n")
        
        print(f"{COLOR_YELLOW}Quick Reference Card:{COLOR_RESET}")
        print(f"{COLOR_DIM}{'─' * 50}{COLOR_RESET}")
        print(f"  h = Hit   |  s = Stand  |  d = Double Down")
        print(f"  p = Split |  r = Surrender")
        print(f"{COLOR_DIM}{'─' * 50}{COLOR_RESET}\n")
        
        print(f"{COLOR_GREEN}{COLOR_BOLD}Ready to play?{COLOR_RESET}")
        print(f"{COLOR_DIM}Start with Solo Play or Quick Play mode to practice!{COLOR_RESET}\n")
        
        self.wait_for_enter("Press Enter to return to the main menu...")


def run_tutorial():
    """Run the complete tutorial"""
    tutorial = Tutorial()
    
    tutorial.step_1_welcome()
    tutorial.step_2_objective()
    tutorial.step_3_card_values()
    tutorial.step_4_basic_actions()
    tutorial.step_5_advanced_actions()
    tutorial.step_6_dealer_rules()
    tutorial.step_7_betting()
    tutorial.step_8_practice()
    
    clear_screen()
