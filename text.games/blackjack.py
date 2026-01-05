"""
Blackjack Game Module
"""

import random
from card import Card, SUITS, RANKS, VALUES, COLOR_MAGENTA, COLOR_RESET, COLOR_GREEN, COLOR_RED, COLOR_YELLOW, COLOR_BOLD
from player import HumanPlayer, AIPlayer, AIType
from game_utils import clear_screen, typing_effect, display_card, display_hand, display_table, get_player_bet, get_player_action, display_game_stats

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

def dealer_turn(dealer, deck):
    """Dealer's turn logic."""
    while dealer.calculate_hand_value() < 17:
        dealer.add_card(deal_card(deck))
    return dealer.calculate_hand_value()

def play_round():
    """Play a single round of blackjack."""
    # Create and shuffle deck
    deck = create_deck(6)
    random.shuffle(deck)

    # Create players
    player = HumanPlayer("Player")
    dealer = AIPlayer("Dealer", AIType.BASIC)

    # Place bet
    bet = get_player_bet(player)
    if not player.place_bet(bet):
        typing_effect(f"{COLOR_RED}Bet failed! Not enough chips.{COLOR_RESET}")
        return

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
            # Push
            typing_effect(f"{COLOR_YELLOW}Both have Blackjack! It's a tie!{COLOR_RESET}")
            player.tie_bet()
        else:
            # Player wins
            player.win_bet(bet * 2.5)
            typing_effect(f"{COLOR_GREEN}Blackjack! You win {bet * 2.5} chips!{COLOR_RESET}")
        return

    if dealer.has_blackjack():
        # Dealer wins
        dealer.win_bet(bet)
        player.lose_bet(bet)
        typing_effect(f"{COLOR_RED}Dealer has Blackjack! You lose {bet} chips.{COLOR_RESET}")
        return

    # Player's turn
    while True:
        display_table(player, dealer, bet_amount=bet)
        action = get_player_action()

        if action == 's':
            break

        if action == 'd':
            # Double down logic
            if not player.can_afford_bet(bet):
                typing_effect(f"{COLOR_RED}Not enough chips to double down!{COLOR_RESET}")
                continue

            player.place_bet(bet)
            player.add_card(deal_card(deck))
            typing_effect(f"{COLOR_YELLOW}Doubled down! Added {bet} more chips.{COLOR_RESET}")
            break

        player.add_card(deal_card(deck))
        if player.is_bust():
            # Player busts
            dealer.win_bet(bet)
            player.lose_bet(bet)
            typing_effect(f"{COLOR_RED}Bust! You lose {bet} chips.{COLOR_RESET}")
            return

    # Dealer's turn
    dealer_value = dealer_turn(dealer, deck)
    display_table(player, dealer, hide_dealer_one=False, bet_amount=bet)

    # Determine the winner
    player_value = player.calculate_hand_value()
    dealer_value = dealer.calculate_hand_value()

    if player_value > 21:
        # Player busts
        dealer.win_bet(bet)
        player.lose_bet(bet)
        typing_effect(f"{COLOR_RED}Dealer wins! You bust with {player_value}.{COLOR_RESET}")
    elif dealer_value > 21:
        # Dealer busts
        player.win_bet(bet * 2)
        typing_effect(f"{COLOR_GREEN}Dealer busts! You win {bet * 2} chips!{COLOR_RESET}")
    elif player_value > dealer_value:
        # Player wins
        player.win_bet(bet * 2)
        typing_effect(f"{COLOR_GREEN}You win! {player_value} > {dealer_value}. You win {bet * 2} chips!{COLOR_RESET}")
    elif dealer_value > player_value:
        # Dealer wins
        dealer.win_bet(bet)
        player.lose_bet(bet)
        typing_effect(f"{COLOR_RED}Dealer wins! {dealer_value} > {player_value}. You lose {bet} chips.{COLOR_RESET}")
    else:
        # Tie
        player.tie_bet()
        typing_effect(f"{COLOR_YELLOW}It's a tie! {player_value} = {dealer_value}.{COLOR_RESET}")

def main():
    """Main game loop."""
    typing_effect(f"{COLOR_MAGENTA}Welcome to Blackjack!{COLOR_RESET}")
    typing_effect("Let's get started!")

    while True:
        play_round()

        if input("\nPlay another round? (Y/N): ").lower() != 'y':
            display_game_stats(HumanPlayer("Player"), AIPlayer("Dealer", AIType.BASIC))
            typing_effect(f"{COLOR_GREEN}Thanks for playing!{COLOR_RESET}")
            break

if __name__ == "__main__":
    main()
