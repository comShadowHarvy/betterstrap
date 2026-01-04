"""
Blackjack Game Module
"""

import random
from card import Card, SUITS, RANKS, VALUES
from player import HumanPlayer, AIPlayer, AIType
from game_utils import clear_screen, typing_effect, display_card, display_hand

def create_deck(num_decks=1):
    """Create a deck of cards."""
    deck = []
    for _ in range(num_decks):
        for suit in SUITS:
            for rank in RANKS:
                deck.append(Card(suit, rank))
    return deck

def deal_card(deck):
    """Deal a card from the deck."""
    if not deck:
        return None
    return deck.pop()

def display_table(player, dealer, hide_dealer_one=True):
    """Display the current state of the table."""
    clear_screen()
    print("\n" + "="*40)
    print(f"{COLOR_MAGENTA}CASINO BLACKJACK{COLOR_RESET}")
    print("="*40)

    print(f"\n{player.name}'s Hand: {player.calculate_hand_value()}")
    display_hand(player.name, player.get_current_hand())

    print("\nDealer's Hand:")
    display_hand("Dealer", dealer.get_current_hand(), hide_one=hide_dealer_one)
    print("="*40 + "\n")

def get_player_action():
    """Get player's action input."""
    while True:
        action = input("What would you like to do? (H)it or (S)tand: ").lower()
        if action in ['h', 's']:
            return action
        print("Please enter 'H' to hit or 'S' to stand.")

def dealer_turn(dealer, deck):
    """Dealer's turn logic."""
    while dealer.calculate_hand_value() < 17:
        dealer.add_card(deal_card(deck))
    return dealer.calculate_hand_value()

def play_round():
    """Play a single round of blackjack."""
    deck = create_deck(6)
    random.shuffle(deck)

    player = HumanPlayer("Player")
    dealer = AIPlayer("Dealer", AIType.BASIC)

    # Deal initial cards
    player.add_hand()
    dealer.add_hand()

    player.add_card(deal_card(deck))
    dealer.add_card(deal_card(deck))
    player.add_card(deal_card(deck))
    dealer.add_card(deal_card(deck))

    # Check for blackjack
    if player.has_blackjack():
        typing_effect(f"{player.name} has Blackjack! {player.calculate_hand_value()}")
        return

    if dealer.has_blackjack():
        typing_effect(f"Dealer has Blackjack! {dealer.calculate_hand_value()}")
        return

    # Player's turn
    while True:
        display_table(player, dealer)
        action = get_player_action()

        if action == 's':
            break

        player.add_card(deal_card(deck))
        if player.is_bust():
            typing_effect(f"{player.name} busts with {player.calculate_hand_value()}")
            return

    # Dealer's turn
    dealer_value = dealer_turn(dealer, deck)
    display_table(player, dealer, hide_dealer_one=False)

    # Determine the winner
    player_value = player.calculate_hand_value()
    dealer_value = dealer.calculate_hand_value()

    if player_value > 21:
        typing_effect(f"Dealer wins! {dealer_value} > {player_value}")
    elif dealer_value > 21 or player_value > dealer_value:
        typing_effect(f"{player.name} wins! {player_value} > {dealer_value}")
    elif dealer_value > player_value:
        typing_effect(f"Dealer wins! {dealer_value} > {player_value}")
    else:
        typing_effect(f"It's a tie! {player_value} = {dealer_value}")

def main():
    """Main game loop."""
    typing_effect(f"{COLOR_MAGENTA}Welcome to Blackjack!{COLOR_RESET}")
    typing_effect("Let's get started!")

    while True:
        play_round()

        if input("\nPlay another round? (Y/N): ").lower() != 'y':
            typing_effect(f"{COLOR_GREEN}Thanks for playing!{COLOR_RESET}")
            break

if __name__ == "__main__":
    main()
