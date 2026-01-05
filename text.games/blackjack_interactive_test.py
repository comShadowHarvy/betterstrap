"""
Interactive test script for Blackjack game.
"""

import random
from card import Card, SUITS, RANKS, VALUES
from player import HumanPlayer, AIPlayer, AIType
from blackjack import create_deck, deal_card, display_table, get_player_action, dealer_turn

def test_interactive():
    """Interactive test of the blackjack game."""
    print("=== Interactive Blackjack Test ===")

    # Create a deck and shuffle it
    deck = create_deck(2)
    random.shuffle(deck)

    # Create players
    player = HumanPlayer("Test Player")
    dealer = AIPlayer("Test Dealer", AIType.BASIC)

    # Deal initial cards
    player.add_hand()
    dealer.add_hand()

    print("\nDealing initial cards...")
    player.add_card(deal_card(deck))
    dealer.add_card(deal_card(deck))
    player.add_card(deal_card(deck))
    dealer.add_card(deal_card(deck))

    # Check for blackjack
    if player.has_blackjack():
        print(f"\n{player.name} has Blackjack! Value: {player.calculate_hand_value()}")
        return

    if dealer.has_blackjack():
        print(f"\nDealer has Blackjack! Value: {dealer.calculate_hand_value()}")
        return

    # Player's turn
    print("\n=== Player's Turn ===")
    while True:
        display_table(player, dealer)
        action = get_player_action()

        if action == 's':
            break

        player.add_card(deal_card(deck))
        if player.is_bust():
            print(f"\n{player.name} busts with {player.calculate_hand_value()}")
            return

    # Dealer's turn
    print("\n=== Dealer's Turn ===")
    dealer_value = dealer_turn(dealer, deck)
    display_table(player, dealer, hide_dealer_one=False)

    # Determine the winner
    player_value = player.calculate_hand_value()
    dealer_value = dealer.calculate_hand_value()

    print("\n=== Results ===")
    print(f"{player.name}'s final hand value: {player_value}")
    print(f"Dealer's final hand value: {dealer_value}")

    if player_value > 21:
        print("Dealer wins!")
    elif dealer_value > 21 or player_value > dealer_value:
        print(f"{player.name} wins!")
    elif dealer_value > player_value:
        print("Dealer wins!")
    else:
        print("It's a tie!")

if __name__ == "__main__":
    test_interactive()
