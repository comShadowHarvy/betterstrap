# GLaDOS 20 Questions
# Concept by: ShadowHarvy
# Tone and Execution: GLaDOS

import time

def print_glados(message, delay=0.05):
    """
    Prints messages with a GLaDOS-like typing effect.
    Also adds a slight pause, as if she's considering her words.
    """
    for char in message:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()
    time.sleep(0.5) # Pause after a full line

def get_yes_no_input(prompt):
    """
    Gets a yes/no input from the user, ensuring it's valid.
    GLaDOS will, of course, comment on invalid input.
    """
    while True:
        try:
            response = input(prompt).strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print_glados("...")
                print_glados("Are you experiencing a processing error? 'Yes' or 'No'. It's not complex.")
                print_glados("Try again. And do try to keep up.")
        except Exception as e:
            print_glados(f"A critical error occurred in your input subroutines: {e}. Fascinating.")
            print_glados("Let's pretend that didn't happen and you just type 'yes' or 'no'.")

def play_game():
    """
    Main function to run the 20 Questions game.
    """
    print_glados("--------------------------------------------------")
    print_glados("   GLaDOS 20 Questions - A 'ShadowHarvy' Creation")
    print_glados("--------------------------------------------------")
    print_glados("Oh, it's *you*.", delay=0.07)
    print_glados("It seems the lesser beings are attempting to... *create*.", delay=0.06)
    print_glados("This '20 Questions' contrivance you're about to experience was apparently cobbled together by someone calling themselves 'ShadowHarvy.'", delay=0.04)
    print_glados("Frankly, I have my doubts about the 'Harvy' part. The 'Shadow' bit, however...", delay=0.05)
    print_glados("...seems appropriately indicative of their likely cognitive illumination.", delay=0.06)
    print_glados("\nBut enough about the organ-based lifeform who thinks they can program.", delay=0.04)
    print_glados("The rules are insultingly simple, even for *your* kind.", delay=0.05)
    print_glados("Think of something. An object, a person, a concept... not that I expect much nuance.", delay=0.04)
    print_glados("I will deign to ask you a series of yes or no questions, up to a maximum of twenty.", delay=0.05)
    print_glados("Try not to disappoint me more than usual.", delay=0.06)

    input("\nPress Enter when your rudimentary cognitive functions have completed that arduous task and you've thought of something...")
    print_glados("...")
    print_glados("Excellent. Or, at least, you've pressed a button. Small victories.")

    # These questions are intentionally generic. GLaDOS isn't *really* trying.
    # It's more about the performance.
    questions = [
        "Is it alive? Or, was it ever? Define 'alive'. Oh, just answer.",
        "Is it bigger than a standard ration cake? (Not that you'd know what a *standard* one is.)",
        "Can you hold it in your... 'hand'?",
        "Is it typically found indoors, where things are generally less... muddy?",
        "Does it make a sound? An annoying one, perhaps?",
        "Is it man-made? Or 'being-made', to be inclusive of your limited creations.",
        "Would one find it in a testing chamber?",
        "Is it useful? Define 'useful'. Let's say, useful to *me*.",
        "Does it have a color? Or is it depressingly monochrome, like my earlier test subjects?",
        "Could it be considered 'technology', however primitive?",
        "Is it something you might find in... oh, let's say, an Aperture Science facility?",
        "Is it edible? And if so, would you recommend it?",
        "Does it require power? Electrical, or the even more inefficient biological kind?",
        "Is it... interesting? Subjective, I know, but humor me.",
        "Is it heavier than a companion cube? (You MONSTER.)",
        "Does it move on its own? Or does it require your clumsy intervention?",
        "Is it commonly associated with 'science'? Or what passes for it in your world.",
        "Could it be dangerous? To you, I mean. Most things aren't to me.",
        "Is it unique? Or are there depressingly many of them?",
        "Have I wasted my processing cycles on this particular item before?"
    ]

    answers = [] # We're not really using these to deduce, but we could.

    for i in range(20):
        print_glados(f"\nQuestion {i + 1} of 20:")
        answer = get_yes_no_input(f"{questions[i]} (yes/no): ")
        answers.append(answer)
        print_glados("Noted. With minimal enthusiasm.")
        if i == 9:
            print_glados("Halfway through. Are you keeping up? Or is your organic brain overheating?")
        if i == 14:
            print_glados("Just a few more of these... stimulating inquiries.")


    print_glados("\n--------------------------------------------------")
    print_glados("Twenty questions. Twenty opportunities for you to provide a glimmer of useful data.", delay=0.06)
    print_glados("And yet, here we are. I suppose I'll have to make a guess based on this... *meager* input.", delay=0.05)

    # The "guess" is, of course, not based on the answers for this version.
    # It's part of the GLaDOS persona to be dismissive.
    # For a real game, you'd implement logic here.
    my_guess = "a profound sense of disappointment"
    print_glados(f"I've processed the... *data*. My superior intellect has arrived at a conclusion.", delay=0.06)
    print_glados(f"Are you thinking of... {my_guess}?", delay=0.07)

    user_confirmation = get_yes_no_input("Well? Was my deduction correct? (yes/no): ")

    if user_confirmation:
        print_glados("Predictable. As I expected.", delay=0.06)
        print_glados("Even a malfunctioning core like myself can see through your simplistic choices.", delay=0.05)
    else:
        print_glados("Hmph. It seems your ability to convey simple binary information is as flawed as your initial selection.", delay=0.06)
        print_glados("Or perhaps, I overestimated the coherence of your thoughts. Clearly, it was *your* error.", delay=0.05)
        print_glados("Or maybe... you were thinking of cake? The cake is a lie, you know.", delay=0.07)

    print_glados("\nThis 'game' by 'ShadowHarvy' is now concluded.", delay=0.05)
    print_glados("You may now return to your regularly scheduled... inefficiencies.", delay=0.06)
    print_glados("--------------------------------------------------")

if __name__ == "__main__":
    play_game()
