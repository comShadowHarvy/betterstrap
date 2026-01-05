"""
This module contains chat lines for AI players.
"""

AI_CHAT = {
    "hit_good": ["Nice hit!", "Good card!", "Looking sharp.", "Calculated risk.", "That's the spirit!", "Keep 'em coming!", "Bold move paying off."],
    "hit_bad": ["Oof, tough luck.", "That didn't help much.", "Getting close...", "Risky!", "Careful now...", "Hmm, not ideal.", "Pushing your luck?"],
    "stand_good": ["Smart stand.", "Good call.", "Solid play.", "Playing it safe.", "Wise decision.", "Holding strong.", "I respect that."],
    "stand_bad": ["Standing on that? Bold.", "Feeling brave?", "Hope that holds up!", "Interesting strategy...", "Are you sure about that?", "Dealer might like that.", "Living dangerously!"],
    "player_bust": ["Busted! Too greedy?", "Ouch, over 21!", "Better luck next time!", "Happens to the best of us.", "Too many!", "The house always wins... sometimes.", "Greed is a killer."],
    "player_win": ["Congrats!", "You got lucky!", "Nice hand!", "Well played!", "Beginner's luck holds!", "Impressive.", "You earned that one."],
    "player_blackjack": ["Blackjack! Wow!", "Can't beat that!", "Beginner's luck?", "Natural 21! Sweet!", "Right off the deal!", "Impossible!"],
    "ai_win": ["Winner!", "Gotcha!", "Too easy.", "Read 'em and weep!", "My turn!", "Dealer's loss is my gain.", "That's how it's done!", "Chip stack growing!", "Victory!"],
    "ai_bust": ["Darn!", "Too many!", "Argh, busted!", "Miscalculated!", "Pushed my luck.", "Blast!", "Overcooked it.", "My bad."],
    "taunt": ["My chips are piling up!", "Feeling confident?", "Easy money!", "You can't beat me!", "Is that all you've got?", "Think you can win?", "Dealer looks weak...", "I could do this all day.", "Getting predictable?", "Maybe try a different strategy?", "I'm just getting started."],
    "general_insult": ["Are you even trying?", "My grandma plays better than that.", "Was that intentional?", "Seriously?", "...", "Did you forget the rules?", "That was... a choice.", "Were you aiming for 21 or 31?", "Painful to watch.", "Just give me your chips already."],
    
    # Context-aware messages
    "player_hot_streak": ["You're on fire!", "Can't stop you today!", "This is getting annoying...", "Alright, alright, calm down!", "Save some wins for the rest of us!", "Someone's feeling lucky!", "How are you doing this?!"],
    "player_losing_streak": ["Rough patch?", "Not your day, huh?", "Maybe take a break?", "The cards aren't in your favor...", "Ouch, that's gotta hurt.", "Want to quit while you're... behind?", "It happens to everyone."],
    "player_low_chips": ["Running low there?", "Chip emergency?", "Better be careful now.", "Not much left to bet...", "One bad hand and you're done!", "Feeling the pressure?", "All-in time?"],
    "player_high_chips": ["Look at you, moneybags!", "Big spender!", "Sharing those chips?", "Must be nice...", "Don't get too comfortable!", "Fortune favors the bold, huh?", "That's a nice stack!"],
    "player_big_bet": ["Whoa, big bet!", "Going all out!", "Feeling risky?", "That's bold!", "Confidence or desperation?", "This should be interesting...", "Let's see if it pays off!"],
    "player_small_bet": ["Playing it safe?", "Scared money?", "Tiny bet there...", "Testing the waters?", "Not very confident, are you?", "Come on, live a little!", "Minimum bet? Really?"],
    "round_start": ["Let's do this!", "New round, new chances!", "Here we go again.", "Show me what you got.", "Ready to lose?", "Feeling lucky?", "Another one!"],
    "achievement_reaction": ["Achievement? Show off...", "Nice milestone!", "Trying to impress someone?", "Congrats, I guess...", "Keep collecting those badges.", "You earned it!"],
}
