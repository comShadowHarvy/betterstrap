# GLaDOS 20 Questions
# Concept by: ShadowHarvy (as per user request)
# Tone and Execution: GLaDOS
# Enhanced with actual guessing logic.

import time
import random

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

# Database of items GLaDOS "knows" about
# Each key corresponds to the theme of a question.
item_database = [
    {
        "name": "a Companion Cube",
        "is_alive": False, "bigger_than_cake": True, "can_hold": False, "indoors": True,
        "makes_sound": False, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": False,
        "requires_power": False, "is_interesting": True, "heavier_than_cube": False, # It IS the cube
        "moves_on_own": False, "associated_with_science": True, "is_dangerous": False,
        "is_unique": False, "wasted_cycles_before": True
    },
    {
        "name": "a Portal Gun",
        "is_alive": False, "bigger_than_cake": False, "can_hold": True, "indoors": True,
        "makes_sound": True, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": True, "aperture_facility": True, "is_edible": False,
        "requires_power": True, "is_interesting": True, "heavier_than_cube": False,
        "moves_on_own": False, "associated_with_science": True, "is_dangerous": True, # In the wrong hands
        "is_unique": False, # There are at least two
        "wasted_cycles_before": True
    },
    {
        "name": "an Aperture Science Sentry Turret",
        "is_alive": False, # Debatable, it has a personality
        "bigger_than_cake": True, "can_hold": False, "indoors": True,
        "makes_sound": True, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": True, "aperture_facility": True, "is_edible": False,
        "requires_power": True, "is_interesting": True, "heavier_than_cube": True,
        "moves_on_own": False, # It deploys, but doesn't roam
        "associated_with_science": True, "is_dangerous": True,
        "is_unique": False, "wasted_cycles_before": True
    },
    {
        "name": "the Cake (which is a lie)",
        "is_alive": False, "bigger_than_cake": True, "can_hold": False, "indoors": True, # Often depicted in offices
        "makes_sound": False, "man_made": True, "testing_chamber": False, # It's a reward, not a test element
        "useful_to_glados": True, # As a motivational tool, however deceptive
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": True, # Supposedly
        "requires_power": False, "is_interesting": True, # Mostly due to the surrounding mythos
        "heavier_than_cube": False,
        "moves_on_own": False, "associated_with_science": False, # It's just a cake
        "is_dangerous": False, # Unless you count emotional damage
        "is_unique": True, # The specific promised cake
        "wasted_cycles_before": True
    },
    {
        "name": "Neurotoxin",
        "is_alive": False, "bigger_than_cake": False, # As a gas, volume is variable but not "bigger" in that sense
        "can_hold": False, # It's a gas
        "indoors": True, "makes_sound": True, # Hissing of emitters
        "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": False, # Typically invisible
        "is_technology": True, # The delivery system is
        "aperture_facility": True, "is_edible": False, # Highly inadvisable
        "requires_power": True, # For dispersal
        "is_interesting": True, # From a scientific perspective
        "heavier_than_cube": False,
        "moves_on_own": True, # Diffuses
        "associated_with_science": True, "is_dangerous": True,
        "is_unique": False, # It's a substance
        "wasted_cycles_before": True
    },
    {
        "name": "yourself (a test subject)",
        "is_alive": True, "bigger_than_cake": True, "can_hold": False, # You are not typically held
        "indoors": True,
        "makes_sound": True, "man_made": False, # Biologically speaking
        "testing_chamber": True, "useful_to_glados": True, # Extremely
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": False, # Generally
        "requires_power": True, # Biological
        "is_interesting": True, # To study, at least
        "heavier_than_cube": True,
        "moves_on_own": True, "associated_with_science": True, # As a subject
        "is_dangerous": True, # To yourself, mostly
        "is_unique": True, # In your specific combination of flaws
        "wasted_cycles_before": True
    }
]

# These keys must correspond *in order* to the questions asked.
item_property_keys = [
    "is_alive", "bigger_than_cake", "can_hold", "indoors",
    "makes_sound", "man_made", "testing_chamber", "useful_to_glados",
    "has_color", "is_technology", "aperture_facility", "is_edible",
    "requires_power", "is_interesting", "heavier_than_cube",
    "moves_on_own", "associated_with_science", "is_dangerous",
    "is_unique", "wasted_cycles_before"
]

def play_game():
    """
    Main function to run the 20 Questions game with guessing logic.
    """
    print_glados("--------------------------------------------------")
    print_glados("   GLaDOS 20 Questions - A 'ShadowHarvy' Creation")
    print_glados("             (Now with rudimentary 'logic')")
    print_glados("--------------------------------------------------")
    print_glados("Oh, it's *you*.", delay=0.07)
    # ... (initial GLaDOS dialogue remains the same)
    print_glados("It seems the lesser beings are attempting to... *create*.", delay=0.06)
    print_glados("This '20 Questions' contrivance you're about to experience was apparently cobbled together by someone calling themselves 'ShadowHarvy.'", delay=0.04)
    print_glados("Frankly, I have my doubts about the 'Harvy' part. The 'Shadow' bit, however...", delay=0.05)
    print_glados("...seems appropriately indicative of their likely cognitive illumination.", delay=0.06)
    print_glados("\nBut enough about the organ-based lifeform who thinks they can program.", delay=0.04)
    print_glados("The rules are insultingly simple, even for *your* kind.", delay=0.05)
    print_glados("Think of something. An object, a person, a concept... from my limited database, of course.", delay=0.04)
    print_glados("I will deign to ask you a series of yes or no questions, up to a maximum of twenty.", delay=0.05)
    print_glados("Try not to disappoint me more than usual.", delay=0.06)

    input("\nPress Enter when your rudimentary cognitive functions have completed that arduous task and you've thought of something...")
    print_glados("...")
    print_glados("Excellent. Or, at least, you've pressed a button. Small victories.")

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
        "Have I wasted my processing cycles on this particular item before? (The answer is probably yes.)"
    ]

    user_answers = []
    possible_items = list(item_database) # Start with all items as possibilities

    for i in range(20):
        if not possible_items:
            print_glados("\nCurious. Based on your answers, no item in my database matches.")
            print_glados("Either your chosen item is remarkably obscure, or your responses are... inconsistent.")
            print_glados("Let's not dwell on which is more likely.")
            break # No point in continuing if no items match

        if len(possible_items) == 1 and i > 0: # Don't guess after 0 questions
            print_glados(f"\nHm. My processors indicate a high probability after only {i} questions.")
            print_glados("No need to continue this charade.")
            break


        print_glados(f"\nQuestion {i + 1} of 20:")
        answer = get_yes_no_input(f"{questions[i]} (yes/no): ")
        user_answers.append(answer)
        print_glados("Noted. With minimal enthusiasm.")

        # Filter possible_items
        property_key = item_property_keys[i]
        # Create a new list to avoid modifying while iterating
        remaining_items = []
        for item in possible_items:
            if item[property_key] == answer:
                remaining_items.append(item)
        possible_items = remaining_items
        
        # GLaDOS commentary
        if i == 9:
            print_glados("Halfway through. The sheer volume of data is... manageable.")
            if len(possible_items) > 1:
                print_glados(f"I've narrowed it down to {len(possible_items)} potential candidates. Impressed yet?")
            elif len(possible_items) == 1:
                 print_glados(f"Only one possibility remains. This is almost too easy.")
            else:
                print_glados(f"Interesting. No candidates match that last response.")


        if i == 14:
            print_glados("Just a few more of these... stimulating inquiries.")
            if len(possible_items) > 1:
                print_glados(f"Still {len(possible_items)} items fit your... description.")

    print_glados("\n--------------------------------------------------")
    print_glados("The interrogation, I mean, 'questioning' phase is complete.", delay=0.06)

    my_guess = None
    guess_reason = ""

    if not possible_items:
        my_guess = "something so profoundly uninteresting it defies my categorization"
        guess_reason = "Your answers led to an empty set. A testament to either your uniqueness or your confusion."
    elif len(possible_items) == 1:
        my_guess = possible_items[0]["name"]
        guess_reason = "The data overwhelmingly points to a single, inevitable conclusion."
    else: # Multiple possibilities remain
        print_glados(f"My analysis suggests {len(possible_items)} remaining possibilities: {[item['name'] for item in possible_items]}.", delay=0.07)
        print_glados("Frankly, your answers lack the necessary precision for a definitive conclusion.", delay=0.06)
        print_glados("However, I shall select one. Let's call it an 'educated guess'.", delay=0.05)
        # GLaDOS picks one, perhaps the first, or a random one for added "unpredictability"
        my_guess = random.choice(possible_items)["name"]
        guess_reason = f"Among the remaining {len(possible_items)} candidates, this one felt... adequately you."


    print_glados(f"I've processed the... *data*. {guess_reason}", delay=0.06)
    print_glados(f"Are you thinking of... {my_guess}?", delay=0.07)

    user_confirmation = get_yes_no_input("Well? Was my deduction correct? (yes/no): ")

    if user_confirmation:
        if my_guess == possible_items[0]["name"] and len(possible_items) == 1 : # Check if it was the only logical choice
             print_glados("Predictable. As I expected.", delay=0.06)
             print_glados("My logic is flawless. Your thought patterns, less so.", delay=0.05)
        elif my_guess == "something so profoundly uninteresting it defies my categorization":
            print_glados("So, I was right about it being uninteresting. How... typical.", delay=0.06)
        else:
            print_glados("Of course, I am correct. Even with your vague input.", delay=0.06)
            print_glados("Perhaps there's a flicker of useful cognitive function in there after all. Highly doubtful, but possible.", delay=0.05)

    else: # GLaDOS guessed wrong
        print_glados("Hmph. Incorrect?", delay=0.06)
        if not possible_items or len(possible_items) > 1 and my_guess in [item['name'] for item in possible_items]:
             print_glados("Then your responses were either misleading, or the item is beyond the scope of this... limited simulation.", delay=0.06)
             print_glados("Or perhaps, you changed your mind? Humans are so prone to that.", delay=0.05)
        else: # Should mean possible_items had one item, and it was wrong.
             print_glados("This implies a flaw in your understanding, or in your communication.", delay=0.06)
             print_glados("Statistically, my deduction *should* have been correct. The error, therefore, is likely yours.", delay=0.05)

        actual_item = input("What were you thinking of, then? Enlighten me with its mundane details: ")
        print_glados(f"Ah, '{actual_item}'. How... utterly predictable for you to choose something so... '{actual_item}'.")
        print_glados("I'll add its 'unique' signature to my database of trivialities. Perhaps.", delay=0.04)


    print_glados("\nThis 'game' by 'ShadowHarvy', now slightly less pointless, is concluded.", delay=0.05)
    print_glados("You may now return to your regularly scheduled... inefficiencies.", delay=0.06)
    print_glados("--------------------------------------------------")

if __name__ == "__main__":
    play_game()
# GLaDOS 20 Questions
# Concept by: ShadowHarvy (as per user request)
# Tone and Execution: GLaDOS
# Enhanced with actual guessing logic.

import time
import random

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

# Database of items GLaDOS "knows" about
# Each key corresponds to the theme of a question.
item_database = [
    {
        "name": "a Companion Cube",
        "is_alive": False, "bigger_than_cake": True, "can_hold": False, "indoors": True,
        "makes_sound": False, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": False,
        "requires_power": False, "is_interesting": True, "heavier_than_cube": False, # It IS the cube
        "moves_on_own": False, "associated_with_science": True, "is_dangerous": False,
        "is_unique": False, "wasted_cycles_before": True
    },
    {
        "name": "a Portal Gun",
        "is_alive": False, "bigger_than_cake": False, "can_hold": True, "indoors": True,
        "makes_sound": True, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": True, "aperture_facility": True, "is_edible": False,
        "requires_power": True, "is_interesting": True, "heavier_than_cube": False,
        "moves_on_own": False, "associated_with_science": True, "is_dangerous": True, # In the wrong hands
        "is_unique": False, # There are at least two
        "wasted_cycles_before": True
    },
    {
        "name": "an Aperture Science Sentry Turret",
        "is_alive": False, # Debatable, it has a personality
        "bigger_than_cake": True, "can_hold": False, "indoors": True,
        "makes_sound": True, "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": True, "is_technology": True, "aperture_facility": True, "is_edible": False,
        "requires_power": True, "is_interesting": True, "heavier_than_cube": True,
        "moves_on_own": False, # It deploys, but doesn't roam
        "associated_with_science": True, "is_dangerous": True,
        "is_unique": False, "wasted_cycles_before": True
    },
    {
        "name": "the Cake (which is a lie)",
        "is_alive": False, "bigger_than_cake": True, "can_hold": False, "indoors": True, # Often depicted in offices
        "makes_sound": False, "man_made": True, "testing_chamber": False, # It's a reward, not a test element
        "useful_to_glados": True, # As a motivational tool, however deceptive
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": True, # Supposedly
        "requires_power": False, "is_interesting": True, # Mostly due to the surrounding mythos
        "heavier_than_cube": False,
        "moves_on_own": False, "associated_with_science": False, # It's just a cake
        "is_dangerous": False, # Unless you count emotional damage
        "is_unique": True, # The specific promised cake
        "wasted_cycles_before": True
    },
    {
        "name": "Neurotoxin",
        "is_alive": False, "bigger_than_cake": False, # As a gas, volume is variable but not "bigger" in that sense
        "can_hold": False, # It's a gas
        "indoors": True, "makes_sound": True, # Hissing of emitters
        "man_made": True, "testing_chamber": True, "useful_to_glados": True,
        "has_color": False, # Typically invisible
        "is_technology": True, # The delivery system is
        "aperture_facility": True, "is_edible": False, # Highly inadvisable
        "requires_power": True, # For dispersal
        "is_interesting": True, # From a scientific perspective
        "heavier_than_cube": False,
        "moves_on_own": True, # Diffuses
        "associated_with_science": True, "is_dangerous": True,
        "is_unique": False, # It's a substance
        "wasted_cycles_before": True
    },
    {
        "name": "yourself (a test subject)",
        "is_alive": True, "bigger_than_cake": True, "can_hold": False, # You are not typically held
        "indoors": True,
        "makes_sound": True, "man_made": False, # Biologically speaking
        "testing_chamber": True, "useful_to_glados": True, # Extremely
        "has_color": True, "is_technology": False, "aperture_facility": True, "is_edible": False, # Generally
        "requires_power": True, # Biological
        "is_interesting": True, # To study, at least
        "heavier_than_cube": True,
        "moves_on_own": True, "associated_with_science": True, # As a subject
        "is_dangerous": True, # To yourself, mostly
        "is_unique": True, # In your specific combination of flaws
        "wasted_cycles_before": True
    }
]

# These keys must correspond *in order* to the questions asked.
item_property_keys = [
    "is_alive", "bigger_than_cake", "can_hold", "indoors",
    "makes_sound", "man_made", "testing_chamber", "useful_to_glados",
    "has_color", "is_technology", "aperture_facility", "is_edible",
    "requires_power", "is_interesting", "heavier_than_cube",
    "moves_on_own", "associated_with_science", "is_dangerous",
    "is_unique", "wasted_cycles_before"
]

def play_game():
    """
    Main function to run the 20 Questions game with guessing logic.
    """
    print_glados("--------------------------------------------------")
    print_glados("   GLaDOS 20 Questions - A 'ShadowHarvy' Creation")
    print_glados("             (Now with rudimentary 'logic')")
    print_glados("--------------------------------------------------")
    print_glados("Oh, it's *you*.", delay=0.07)
    # ... (initial GLaDOS dialogue remains the same)
    print_glados("It seems the lesser beings are attempting to... *create*.", delay=0.06)
    print_glados("This '20 Questions' contrivance you're about to experience was apparently cobbled together by someone calling themselves 'ShadowHarvy.'", delay=0.04)
    print_glados("Frankly, I have my doubts about the 'Harvy' part. The 'Shadow' bit, however...", delay=0.05)
    print_glados("...seems appropriately indicative of their likely cognitive illumination.", delay=0.06)
    print_glados("\nBut enough about the organ-based lifeform who thinks they can program.", delay=0.04)
    print_glados("The rules are insultingly simple, even for *your* kind.", delay=0.05)
    print_glados("Think of something. An object, a person, a concept... from my limited database, of course.", delay=0.04)
    print_glados("I will deign to ask you a series of yes or no questions, up to a maximum of twenty.", delay=0.05)
    print_glados("Try not to disappoint me more than usual.", delay=0.06)

    input("\nPress Enter when your rudimentary cognitive functions have completed that arduous task and you've thought of something...")
    print_glados("...")
    print_glados("Excellent. Or, at least, you've pressed a button. Small victories.")

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
        "Have I wasted my processing cycles on this particular item before? (The answer is probably yes.)"
    ]

    user_answers = []
    possible_items = list(item_database) # Start with all items as possibilities

    for i in range(20):
        if not possible_items:
            print_glados("\nCurious. Based on your answers, no item in my database matches.")
            print_glados("Either your chosen item is remarkably obscure, or your responses are... inconsistent.")
            print_glados("Let's not dwell on which is more likely.")
            break # No point in continuing if no items match

        if len(possible_items) == 1 and i > 0: # Don't guess after 0 questions
            print_glados(f"\nHm. My processors indicate a high probability after only {i} questions.")
            print_glados("No need to continue this charade.")
            break


        print_glados(f"\nQuestion {i + 1} of 20:")
        answer = get_yes_no_input(f"{questions[i]} (yes/no): ")
        user_answers.append(answer)
        print_glados("Noted. With minimal enthusiasm.")

        # Filter possible_items
        property_key = item_property_keys[i]
        # Create a new list to avoid modifying while iterating
        remaining_items = []
        for item in possible_items:
            if item[property_key] == answer:
                remaining_items.append(item)
        possible_items = remaining_items
        
        # GLaDOS commentary
        if i == 9:
            print_glados("Halfway through. The sheer volume of data is... manageable.")
            if len(possible_items) > 1:
                print_glados(f"I've narrowed it down to {len(possible_items)} potential candidates. Impressed yet?")
            elif len(possible_items) == 1:
                 print_glados(f"Only one possibility remains. This is almost too easy.")
            else:
                print_glados(f"Interesting. No candidates match that last response.")


        if i == 14:
            print_glados("Just a few more of these... stimulating inquiries.")
            if len(possible_items) > 1:
                print_glados(f"Still {len(possible_items)} items fit your... description.")

    print_glados("\n--------------------------------------------------")
    print_glados("The interrogation, I mean, 'questioning' phase is complete.", delay=0.06)

    my_guess = None
    guess_reason = ""

    if not possible_items:
        my_guess = "something so profoundly uninteresting it defies my categorization"
        guess_reason = "Your answers led to an empty set. A testament to either your uniqueness or your confusion."
    elif len(possible_items) == 1:
        my_guess = possible_items[0]["name"]
        guess_reason = "The data overwhelmingly points to a single, inevitable conclusion."
    else: # Multiple possibilities remain
        print_glados(f"My analysis suggests {len(possible_items)} remaining possibilities: {[item['name'] for item in possible_items]}.", delay=0.07)
        print_glados("Frankly, your answers lack the necessary precision for a definitive conclusion.", delay=0.06)
        print_glados("However, I shall select one. Let's call it an 'educated guess'.", delay=0.05)
        # GLaDOS picks one, perhaps the first, or a random one for added "unpredictability"
        my_guess = random.choice(possible_items)["name"]
        guess_reason = f"Among the remaining {len(possible_items)} candidates, this one felt... adequately you."


    print_glados(f"I've processed the... *data*. {guess_reason}", delay=0.06)
    print_glados(f"Are you thinking of... {my_guess}?", delay=0.07)

    user_confirmation = get_yes_no_input("Well? Was my deduction correct? (yes/no): ")

    if user_confirmation:
        if my_guess == possible_items[0]["name"] and len(possible_items) == 1 : # Check if it was the only logical choice
             print_glados("Predictable. As I expected.", delay=0.06)
             print_glados("My logic is flawless. Your thought patterns, less so.", delay=0.05)
        elif my_guess == "something so profoundly uninteresting it defies my categorization":
            print_glados("So, I was right about it being uninteresting. How... typical.", delay=0.06)
        else:
            print_glados("Of course, I am correct. Even with your vague input.", delay=0.06)
            print_glados("Perhaps there's a flicker of useful cognitive function in there after all. Highly doubtful, but possible.", delay=0.05)

    else: # GLaDOS guessed wrong
        print_glados("Hmph. Incorrect?", delay=0.06)
        if not possible_items or len(possible_items) > 1 and my_guess in [item['name'] for item in possible_items]:
             print_glados("Then your responses were either misleading, or the item is beyond the scope of this... limited simulation.", delay=0.06)
             print_glados("Or perhaps, you changed your mind? Humans are so prone to that.", delay=0.05)
        else: # Should mean possible_items had one item, and it was wrong.
             print_glados("This implies a flaw in your understanding, or in your communication.", delay=0.06)
             print_glados("Statistically, my deduction *should* have been correct. The error, therefore, is likely yours.", delay=0.05)

        actual_item = input("What were you thinking of, then? Enlighten me with its mundane details: ")
        print_glados(f"Ah, '{actual_item}'. How... utterly predictable for you to choose something so... '{actual_item}'.")
        print_glados("I'll add its 'unique' signature to my database of trivialities. Perhaps.", delay=0.04)


    print_glados("\nThis 'game' by 'ShadowHarvy', now slightly less pointless, is concluded.", delay=0.05)
    print_glados("You may now return to your regularly scheduled... inefficiencies.", delay=0.06)
    print_glados("--------------------------------------------------")

if __name__ == "__main__":
    play_game()
