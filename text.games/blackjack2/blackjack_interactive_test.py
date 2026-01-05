"""
Interactive test script for Blackjack game with betting and more features.
"""

import random
from card import Card, SUITS, RANKS, VALUES, COLOR_MAGENTA, COLOR_RESET, COLOR_GREEN, COLOR_RED, COLOR_YELLOW
from player import HumanPlayer, AIPlayer, AIType
from blackjack import create_deck, deal_card, display_table, get_player_bet, get_player_action, dealer_turn

def test_interactive():
    """Interactive test of the blackjack game with betting."""
    print("=== Enhanced Interactive Blackjack Test ===")

    # Create a deck and shuffle it
    deck = create_deck(2)
    random.shuffle(deck)

    # Create players with different chip amounts
    player = HumanPlayer("Test Player", 500)
    dealer = AIPlayer("Test Dealer", AIType.BASIC)

    # Main game loop
    while player.chips > 0:
        print(f"\nCurrent chips: {player.chips}")

        # Place bet
        bet = get_player_bet(player)
        if not player.place_bet(bet):
            print(f"Not enough chips! Game over.")
            break

        # Deal initial cards
        player.add_hand()
        dealer.add_hand()

        player.add_card(deal_card(deck))
        dealer.add_card(deal_card(deck))
        player.add_card(deal_card(deck))
        dealer.add_card(deal_card(deck))

        # Check for blackjack
        if player.has_blackjack():
            dealer_value = dealer.calculate_hand_value()
            if dealer_value == 21:
                print(f"\nBoth have Blackjack! It's a tie!")
                player.tie_bet()
            else:
                print(f"\nBlackjack! You win {bet * 2.5} chips!")
                player.win_bet(bet * 2.5)
            continue

        if dealer.has_blackjack():
            print(f"\nDealer has Blackjack! You lose {bet} chips.")
            dealer.win_bet(bet)
            player.lose_bet(bet)
            continue

        # Player's turn
        print("\n=== Player's Turn ===")
        while True:
            display_table(player, dealer, bet_amount=bet)
            action = get_player_action()

            if action == 's':
                break

            if action == 'd':
                # Double down logic
                if not player.can_afford_bet(bet):
                    print("Not enough chips to double down!")
                    continue

                player.place_bet(bet)
                player.add_card(deal_card(deck))
                print(f"Doubled down! Added {bet} more chips.")
                break

            player.add_card(deal_card(deck))
            if player.is_bust():
                print(f"\nBust! You lose {bet} chips.")
                dealer.win_bet(bet)
                player.lose_bet(bet)
                break

        # Dealer's turn
        print("\n=== Dealer's Turn ===")
        dealer_value = dealer_turn(dealer, deck)
        display_table(player, dealer, hide_dealer_one=False, bet_amount=bet)

        # Determine the winner
        player_value = player.calculate_hand_value()
        dealer_value = dealer.calculate_hand_value()

        if player_value > 21:
            print(f"\nDealer wins! You bust with {player_value}.")
            dealer.win_bet(bet)
            player.lose_bet(bet)
        elif dealer_value > 21:
            print(f"\nDealer busts! You win {bet * 2} chips!")
            player.win_bet(bet * 2)
        elif player_value > dealer_value:
            print(f"\nYou win! {player_value} > {dealer_value}. You win {bet * 2} chips!")
            player.win_bet(bet * 2)
        elif dealer_value > player_value:
            print(f"\nDealer wins! {dealer_value} > {player_value}. You lose {bet} chips.")
            dealer.win_bet(bet)
            player.lose_bet(bet)
        else:
            print(f"\nIt's a tie! {player_value} = {dealer_value}.")
            player.tie_bet()

        # Check if player has lost all chips
        if player.chips <= 0:
            print(f"\nGame over! You've lost all your chips.")
            break

        # Ask to play again
        if input("\nPlay another round? (Y/N): ").lower() != 'y':
            break

    # Display final stats
    print("\n=== Final Stats ===")
    player.display_stats()
    print(f"\n{dealer.name} Stats:")
    print(f"  Wins: {dealer.wins}")
    print(f"  Losses: {dealer.losses}")
    print(f"  Ties: {dealer.ties}")

if __name__ == "__main__":
    test_interactive()
