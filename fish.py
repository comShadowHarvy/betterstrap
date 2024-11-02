import os
import sys
import time
import random
import curses
import signal
import threading

# Constants for maximum elements
MAX_BUBBLES = 50
MAX_OCTOPUSES = 3
MAX_FISH = 50
MAX_JELLYFISH = 5
MAX_SEA_TURTLES = 3
MAX_CRABS = 5
MAX_SEAHORSES = 5
MAX_SEA_URCHINS = 10
MAX_DOLPHINS = 3
MAX_SHARKS = 3
MAX_SMALL_FISH = 30
MAX_FOOD = 20

# Define colors using curses color pairs
COLOR_LIST = [
    curses.COLOR_RED,
    curses.COLOR_GREEN,
    curses.COLOR_YELLOW,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_CYAN,
    curses.COLOR_WHITE
]

# Define marine life ASCII arts
SEAWEED_ART = [
    "  |",
    " /|\\",
    "/ | \\",
    "  |"
]

CORAL_ART = [
    " /\\",
    "/__\\",
    " || ",
    " || "
]

JELLYFISH_ART = [
    "  \\/",
    " \\||/",
    "  ||",
    " /||\\",
    "  /\\"
]

SEA_TURTLE_ART = [
    "    _____     ",
    "  /       \\  ",
    " |  O   O  | ",
    " |    ^    | ",
    "  \\  ---  /  ",
    "    -----    "
]

CRAB_ART = [
    "  / \\_/ \\  ",
    " ( o   o ) ",
    "  >  ^  <  ",
    " /       \\ "
]

SEAHORSE_ART = [
    "    _~_    ",
    "  /    \\  ",
    " |      | ",
    "  \\____/  ",
    "    ||     "
]

SEA_URCHIN_ART = [
    "   /\\_/\\   ",
    "  /     \\  ",
    " /       \\ ",
    " \\       / ",
    "  \\_____/  "
]

DOLPHIN_ART_FRAMES = [
    [
        "     ___",
        " ___/o o\\___",
        "/          \\",
        "\\___      __/",
        "    \\____/"
    ],
    [
        "     ___",
        " ___/o o\\___",
        "/          \\",
        "\\___    __/",
        "    \\__/"
    ]
]

SHARK_ART = [
    "      /\\",
    "     /  \\",
    "    /____\\",
    "    \\    /",
    "     \\  /",
    "      \\/"
]

SMALL_FISH_ART = [
    "<><",
    "<><",
    "<><"
]

FOOD_ART = "*"

# Define Bubble Characters
BUBBLE_CHARS = ['o', 'O', '°', '*', '•']

# Define different fish types with their ASCII art and speed
FISH_TYPES = [
    {
        "name": "small_fish",
        "right": "<><",
        "left": "><>",
        "speed": 0.1
    },
    {
        "name": "medium_fish",
        "right": "><>><",
        "left": "<<><<",
        "speed": 0.15
    },
    {
        "name": "large_fish",
        "right": "><>><>><",
        "left": "<<><<><<",
        "speed": 0.2
    }
]

# Define all marine life classes

class Seaweed:
    """
    Represents seaweed in the aquarium.
    """
    def __init__(self, x, y, color):
        self.art = SEAWEED_ART
        self.x = x
        self.y = y
        self.color = color

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass  # Ignore drawing errors when seaweed is out of bounds

class Coral:
    """
    Represents coral in the aquarium.
    """
    def __init__(self, x, y, color):
        self.art = CORAL_ART
        self.x = x
        self.y = y
        self.color = color

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass  # Ignore drawing errors when coral is out of bounds

class Bubble:
    """
    Represents a bubble that moves upwards on the screen with varied speeds.
    """
    def __init__(self, x, y, char, color, speed):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.speed = speed
        self.move_counter = 0

    def move(self):
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            self.y -= 1

    def draw(self, stdscr):
        if self.y < 1:
            return
        try:
            stdscr.addstr(int(self.y), int(self.x), self.char, curses.color_pair(self.color))
        except curses.error:
            pass  # Ignore drawing errors when bubble is out of bounds

class Fish:
    """
    Represents a small fish that can be part of a school.
    """
    def __init__(self, fish_type, x, y, direction, color, speed, school=None):
        self.art = fish_type["right"] if direction == 1 else fish_type["left"]
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = direction  # 1 for right, -1 for left
        self.school = school  # Reference to the school it belongs to
        self.alive = True

    def get_bounding_box(self):
        """Returns the bounding box of the fish as (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + len(self.art), self.y)

    def move(self, width, height):
        if not self.alive:
            return

        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            if self.school:
                # Schooling behavior
                target_direction = self.school.direction
                self.direction = target_direction
                self.x += self.direction
            else:
                # Independent movement
                self.x += self.direction

            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - len(self.art) - 1:
                self.direction = -1
                self.art = self.art[::-1]  # Reverse art for direction
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1
                self.art = self.art[::-1]

            # Random vertical movement
            if random.random() < 0.3:
                self.y += random.choice([-1, 1])
                self.y = max(1, min(height - 2, self.y))

    def draw(self, stdscr):
        if not self.alive:
            return
        try:
            stdscr.addstr(int(self.y), int(self.x), self.art, curses.color_pair(self.color))
        except curses.error:
            pass  # Ignore drawing errors when fish is out of bounds

class Shark:
    """
    Represents a shark predator.
    """
    def __init__(self, x, y, color, speed):
        self.art = SHARK_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])
        self.alive = True

    def get_bounding_box(self):
        """Returns the bounding box of the shark."""
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height, prey_list):
        if not self.alive:
            return

        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            # Simple chasing behavior: move towards the first prey in the list
            if prey_list:
                prey = prey_list[0]
                if self.x < prey.x:
                    self.direction = 1
                else:
                    self.direction = -1
                self.x += self.direction * 2  # Sharks move faster

                # Change direction at screen edges
                if self.direction == 1 and self.x >= width - max(len(line) for line in self.art) - 1:
                    self.direction = -1
                    self.art = [line[::-1] for line in self.art]  # Reverse art for direction
                elif self.direction == -1 and self.x <= 1:
                    self.direction = 1
                    self.art = [line[::-1] for line in self.art]
            else:
                # Wander randomly if no prey
                self.x += self.direction * 2
                if self.direction == 1 and self.x >= width - max(len(line) for line in self.art) - 1:
                    self.direction = -1
                    self.art = [line[::-1] for line in self.art]
                elif self.direction == -1 and self.x <= 1:
                    self.direction = 1
                    self.art = [line[::-1] for line in self.art]

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class School:
    """
    Represents a school of fish.
    """
    def __init__(self, direction=1):
        self.fish = []
        self.direction = direction  # 1 for right, -1 for left

    def add_fish(self, fish):
        self.fish.append(fish)
        fish.school = self

    def move(self, width, height):
        for fish in self.fish:
            fish.direction = self.direction
            fish.move(width, height)

    def draw(self, stdscr):
        for fish in self.fish:
            fish.draw(stdscr)

class Food:
    """
    Represents food that attracts fish.
    """
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.char = FOOD_ART
        self.color = color
        self.lifespan = 100  # Frames before disappearing

    def move(self, height):
        self.y -= 1  # Food sinks upwards
        self.lifespan -= 1

    def draw(self, stdscr):
        if self.lifespan > 0:
            try:
                stdscr.addstr(int(self.y), int(self.x), self.char, curses.color_pair(self.color))
            except curses.error:
                pass

class Dolphin:
    """
    Represents a dolphin that can perform jumps.
    """
    def __init__(self, x, y, color, speed):
        self.art_frames = DOLPHIN_ART_FRAMES
        self.current_frame = 0
        self.art = self.art_frames[self.current_frame]
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])
        self.jump_counter = 0
        self.alive = True

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        if not self.alive:
            return

        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            # Move horizontally
            self.x += self.direction * 2

            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - max(len(line) for line in self.art) - 1:
                self.direction = -1
                self.art = [line[::-1] for line in self.art]  # Reverse art for direction
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1
                self.art = [line[::-1] for line in self.art]

            # Jump behavior
            if self.jump_counter > 0:
                self.y -= 1
                self.jump_counter -= 1
                if self.jump_counter == 0:
                    # Return to original position
                    self.y += 1

            elif random.random() < 0.01:
                self.jump_counter = 5  # Jump duration

            # Animate frames
            self.current_frame = (self.current_frame + 1) % len(self.art_frames)
            self.art = self.art_frames[self.current_frame]

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Seahorse:
    """
    Represents a seahorse that swims gracefully.
    """
    def __init__(self, x, y, color, speed):
        self.art = SEAHORSE_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])
        self.alive = True

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        if not self.alive:
            return

        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            # Move horizontally with gentle up/down
            self.x += self.direction
            self.y += random.choice([-1, 1])
            self.y = max(1, min(height - len(self.art) - 1, self.y))

            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - len(self.art) - 1:
                self.direction = -1
                self.art = self.art[::-1]
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1
                self.art = self.art[::-1]

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class SeaUrchin:
    """
    Represents a sea urchin, a stationary object.
    """
    def __init__(self, x, y, color):
        self.art = SEA_URCHIN_ART
        self.x = x
        self.y = y
        self.color = color
        self.alive = True

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        pass  # Sea urchins are stationary

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Octopus:
    """
    Represents an octopus that moves around the screen.
    """
    def __init__(self, x, y, color, speed):
        self.art = [
            "  _-_-_",
            " (' o o ')",
            " /   O   ",
            " \\_/|_|\\_/"
        ]
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0

    def get_bounding_box(self):
        """Returns the bounding box of the octopus."""
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            # Random horizontal movement
            if random.random() < 0.3:
                self.x += random.choice([-1, 1])
                self.x = max(1, min(width - max(len(line) for line in self.art) - 1, self.x))
            # Random vertical movement
            if random.random() < 0.3:
                self.y += random.choice([-1, 1])
                self.y = max(1, min(height - len(self.art) - 1, self.y))

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Jellyfish:
    """
    Represents a jellyfish that floats upwards with gentle movements.
    """
    def __init__(self, x, y, color, speed):
        self.art = JELLYFISH_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])  # Horizontal drift direction

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            # Float upwards
            self.y -= 1
            # Horizontal drift
            if random.random() < 0.5:
                self.x += self.direction
                # Change drift direction upon hitting boundaries
                if self.x <= 1 or self.x >= width - max(len(line) for line in self.art) - 1:
                    self.direction *= -1

    def draw(self, stdscr):
        if self.y < 1:
            return
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class SeaTurtle:
    """
    Represents a sea turtle that moves slowly across the screen.
    """
    def __init__(self, x, y, color, speed):
        self.art = SEA_TURTLE_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])  # 1 for right, -1 for left

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            self.x += self.direction * 0.5  # Slow movement
            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - len(self.art) - 1:
                self.direction = -1
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Crab:
    """
    Represents a crab that scuttles sideways across the screen.
    """
    def __init__(self, x, y, color, speed):
        self.art = CRAB_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])

    def get_bounding_box(self):
        width = max(len(line) for line in self.art)
        height = len(self.art)
        return (self.x, self.y, self.x + width, self.y + height - 1)

    def move(self, width, height):
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            self.x += self.direction * 2  # Faster movement
            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - len(self.art) - 2:
                self.direction = -1
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

def detect_collision(obj1, obj2):
    """Detects if two objects have overlapping bounding boxes."""
    x1_min, y1_min, x1_max, y1_max = obj1.get_bounding_box()
    x2_min, y2_min, x2_max, y2_max = obj2.get_bounding_box()
    return not (x1_max < x2_min or x1_min > x2_max or y1_max < y2_min or y1_min > y2_max)

def handle_collisions(predators, prey_list):
    """Check for collisions between predators and prey."""
    for predator in predators:
        for prey in prey_list:
            if detect_collision(predator, prey):
                # Remove prey if collided
                prey.alive = False
                # Predator gains speed or other enhancements (optional)
                # Could add score or other game mechanics here

def main(stdscr):
    # Initialize curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(0)  # No blocking on getch()

    # Initialize color pairs
    curses.start_color()
    for idx, color in enumerate(COLOR_LIST, start=1):
        curses.init_pair(idx, color, curses.COLOR_BLACK)
    # Additional color pairs for food
    curses.init_pair(len(COLOR_LIST) + 1, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Initialize lists
    fishes = []
    bubbles = []
    octopuses = []
    seaweeds = []
    corals = []
    jellyfishes = []
    sea_turtles = []
    crabs = []
    seahorses = []
    sea_urchins = []
    dolphins = []
    sharks = []
    schools = []
    food_list = []

    # Get initial terminal size
    height, width = stdscr.getmaxyx()

    # Initialize seaweeds and corals
    for _ in range(random.randint(3, 5)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(SEAWEED_ART) - 1
        color = random.randint(1, len(COLOR_LIST))
        seaweeds.append(Seaweed(x, y, color))

    for _ in range(random.randint(2, 4)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(CORAL_ART) - 1
        color = random.randint(1, len(COLOR_LIST))
        corals.append(Coral(x, y, color))

    # Initialize schools of fish
    for _ in range(random.randint(1, 3)):
        school_direction = random.choice([-1, 1])
        school = School(direction=school_direction)
        for _ in range(random.randint(5, 10)):
            fish_type = random.choice(FISH_TYPES)
            x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
            y = random.randint(1, max(1, height - 5))
            color = random.randint(1, len(COLOR_LIST))
            speed = fish_type["speed"]
            fish = Fish(fish_type, x, y, school_direction, color, speed, school=school)
            school.add_fish(fish)
        schools.append(school)

    # Initialize individual fishes (not part of schools)
    for _ in range(random.randint(5, MAX_FISH)):
        fish_type = random.choice(FISH_TYPES)
        x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
        y = random.randint(1, max(1, height - 5))
        direction = random.choice([-1, 1])
        color = random.randint(1, len(COLOR_LIST))
        speed = fish_type["speed"]
        fishes.append(Fish(fish_type, x, y, direction, color, speed))

    # Initialize octopuses
    for _ in range(random.randint(0, MAX_OCTOPUSES)):
        x = random.randint(1, max(1, width - 10))
        y = random.randint(1, max(1, height - 6))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        octopuses.append(Octopus(x, y, color, speed))

    # Initialize jellyfishes
    for _ in range(random.randint(1, MAX_JELLYFISH)):
        x = random.randint(1, max(1, width - len(JELLYFISH_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(JELLYFISH_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = random.uniform(0.05, 0.1)
        jellyfishes.append(Jellyfish(x, y, color, speed))

    # Initialize sea turtles
    for _ in range(random.randint(0, MAX_SEA_TURTLES)):
        x = random.randint(1, max(1, width - len(SEA_TURTLE_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(SEA_TURTLE_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        sea_turtles.append(SeaTurtle(x, y, color, speed))

    # Initialize crabs
    for _ in range(random.randint(0, MAX_CRABS)):
        x = random.randint(1, max(1, width - len(CRAB_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(CRAB_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        crabs.append(Crab(x, y, color, speed))

    # Initialize seahorses
    for _ in range(random.randint(0, MAX_SEAHORSES)):
        x = random.randint(1, max(1, width - len(SEAHORSE_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(SEAHORSE_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        seahorses.append(Seahorse(x, y, color, speed))

    # Initialize sea urchins
    for _ in range(random.randint(5, MAX_SEA_URCHINS)):
        x = random.randint(1, max(1, width - len(SEA_URCHIN_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(SEA_URCHIN_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        sea_urchins.append(SeaUrchin(x, y, color))

    # Initialize dolphins
    for _ in range(random.randint(0, MAX_DOLPHINS)):
        x = random.randint(1, max(1, width - len(DOLPHIN_ART_FRAMES[0][0]) - 1))
        y = random.randint(1, max(1, height - len(DOLPHIN_ART_FRAMES[0]) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        dolphins.append(Dolphin(x, y, color, speed))

    # Initialize sharks
    for _ in range(random.randint(0, MAX_SHARKS)):
        x = random.randint(1, max(1, width - len(SHARK_ART[0]) - 1))
        y = random.randint(1, max(1, height - len(SHARK_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.2
        sharks.append(Shark(x, y, color, speed))

    animation_speed = 0.02  # Initial delay between frames in seconds
    last_time = time.time()
    frame_duration = animation_speed  # Desired time per frame

    # Food target location
    food_target = None  # Tuple (x, y)

    while True:
        current_time = time.time()
        elapsed = current_time - last_time

        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)
            current_time = time.time()
            elapsed = current_time - last_time

        last_time = current_time

        # Handle user input
        try:
            key = stdscr.getch()
            if key != -1:
                if key == ord('q'):
                    break  # Quit the program
                elif key == ord('f'):
                    # Add a new fish
                    if len(fishes) + sum(len(s.fish) for s in schools) < MAX_FISH + MAX_SMALL_FISH:
                        fish_type = random.choice(FISH_TYPES)
                        x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
                        y = random.randint(1, max(1, height - 5))
                        direction = random.choice([-1, 1])
                        color = random.randint(1, len(COLOR_LIST))
                        speed = fish_type["speed"]
                        fish = Fish(fish_type, x, y, direction, color, speed)
                        fishes.append(fish)
                elif key == ord('o'):
                    # Add a new octopus
                    if len(octopuses) < MAX_OCTOPUSES:
                        x = random.randint(1, max(1, width - 10))
                        y = random.randint(1, max(1, height - 6))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.1
                        octopuses.append(Octopus(x, y, color, speed))
                elif key == ord('j'):
                    # Add a new jellyfish
                    if len(jellyfishes) < MAX_JELLYFISH:
                        x = random.randint(1, max(1, width - len(JELLYFISH_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(JELLYFISH_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = random.uniform(0.05, 0.1)
                        jellyfishes.append(Jellyfish(x, y, color, speed))
                elif key == ord('t'):
                    # Add a new sea turtle
                    if len(sea_turtles) < MAX_SEA_TURTLES:
                        x = random.randint(1, max(1, width - len(SEA_TURTLE_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(SEA_TURTLE_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.05
                        sea_turtles.append(SeaTurtle(x, y, color, speed))
                elif key == ord('c'):
                    # Add a new crab
                    if len(crabs) < MAX_CRABS:
                        x = random.randint(1, max(1, width - len(CRAB_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(CRAB_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.1
                        crabs.append(Crab(x, y, color, speed))
                elif key == ord('s'):
                    # Add a new school of fish
                    if len(schools) < 5:  # Limit number of schools
                        school_direction = random.choice([-1, 1])
                        school = School(direction=school_direction)
                        for _ in range(random.randint(5, 10)):
                            fish_type = random.choice(FISH_TYPES)
                            x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
                            y = random.randint(1, max(1, height - 5))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = fish_type["speed"]
                            fish = Fish(fish_type, x, y, school_direction, color, speed, school=school)
                            school.add_fish(fish)
                        schools.append(school)
                elif key == ord('d'):
                    # Add a new dolphin
                    if len(dolphins) < MAX_DOLPHINS:
                        x = random.randint(1, max(1, width - len(DOLPHIN_ART_FRAMES[0][0]) - 1))
                        y = random.randint(1, max(1, height - len(DOLPHIN_ART_FRAMES[0]) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.1
                        dolphins.append(Dolphin(x, y, color, speed))
                elif key == ord('h'):
                    # Add a new seahorse
                    if len(seahorses) < MAX_SEAHORSES:
                        x = random.randint(1, max(1, width - len(SEAHORSE_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(SEAHORSE_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.05
                        seahorses.append(Seahorse(x, y, color, speed))
                elif key == ord('u'):
                    # Add a new sea urchin
                    if len(sea_urchins) < MAX_SEA_URCHINS:
                        x = random.randint(1, max(1, width - len(SEA_URCHIN_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(SEA_URCHIN_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        sea_urchins.append(SeaUrchin(x, y, color))
                elif key == ord('w'):
                    # Add a new shark
                    if len(sharks) < MAX_SHARKS:
                        x = random.randint(1, max(1, width - len(SHARK_ART[0]) - 1))
                        y = random.randint(1, max(1, height - len(SHARK_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.2
                        sharks.append(Shark(x, y, color, speed))
                elif key == ord(' '):
                    # Feed the aquarium: spawn food at random location
                    if len(food_list) < MAX_FOOD:
                        x = random.randint(1, max(1, width - 1))
                        y = height - 2
                        color = len(COLOR_LIST) + 1  # White color for food
                        food_list.append(Food(x, y, color))
                elif key == ord('+'):
                    # Increase animation speed
                    animation_speed = max(0.005, animation_speed - 0.005)
                    frame_duration = animation_speed
                elif key == ord('-'):
                    # Decrease animation speed
                    animation_speed = min(0.1, animation_speed + 0.005)
                    frame_duration = animation_speed
        except KeyboardInterrupt:
            break

        # Check for terminal resize
        new_height, new_width = stdscr.getmaxyx()
        if new_height != height or new_width != width:
            height, width = new_height, new_width
            stdscr.clear()

            # Adjust seaweeds and corals positions
            seaweeds = [Seaweed(random.randint(1, max(1, width - 5)), height - len(SEAWEED_ART) - 1, random.randint(1, len(COLOR_LIST))) for seaweed in seaweeds]
            corals = [Coral(random.randint(1, max(1, width - 5)), height - len(CORAL_ART) - 1, random.randint(1, len(COLOR_LIST))) for coral in corals]
            jellyfishes = [Jellyfish(random.randint(1, max(1, width - len(JELLYFISH_ART[0]) - 1)), random.randint(1, max(1, height - len(JELLYFISH_ART) - 1)), random.randint(1, len(COLOR_LIST)), jf.speed) for jf in jellyfishes]
            sea_turtles = [SeaTurtle(random.randint(1, max(1, width - len(SEA_TURTLE_ART[0]) - 1)), random.randint(1, max(1, height - len(SEA_TURTLE_ART) - 1)), random.randint(1, len(COLOR_LIST)), st.speed) for st in sea_turtles]
            crabs = [Crab(random.randint(1, max(1, width - len(CRAB_ART[0]) - 1)), random.randint(1, max(1, height - len(CRAB_ART) - 1)), random.randint(1, len(COLOR_LIST)), c.speed) for c in crabs]
            seahorses = [Seahorse(random.randint(1, max(1, width - len(SEAHORSE_ART[0]) - 1)), random.randint(1, max(1, height - len(SEAHORSE_ART) - 1)), random.randint(1, len(COLOR_LIST)), sh.speed) for sh in seahorses]
            sea_urchins = [SeaUrchin(random.randint(1, max(1, width - len(SEA_URCHIN_ART[0]) - 1)), random.randint(1, max(1, height - len(SEA_URCHIN_ART) - 1)), random.randint(1, len(COLOR_LIST))) for _ in sea_urchins]
            dolphins = [Dolphin(random.randint(1, max(1, width - len(DOLPHIN_ART_FRAMES[0][0]) - 1)), random.randint(1, max(1, height - len(DOLPHIN_ART_FRAMES[0]) - 1)), random.randint(1, len(COLOR_LIST)), d.speed) for d in dolphins]
            sharks = [Shark(random.randint(1, max(1, width - len(SHARK_ART[0]) - 1)), random.randint(1, max(1, height - len(SHARK_ART) - 1)), random.randint(1, len(COLOR_LIST)), s.speed) for s in sharks]

            # Adjust fish positions
            for school in schools:
                for fish in school.fish:
                    fish.y = min(fish.y, max(1, height - 2))
                    fish.x = min(fish.x, max(1, width - len(fish.art) - 1))

            for fish in fishes:
                fish.y = min(fish.y, max(1, height - 2))
                fish.x = min(fish.x, max(1, width - len(fish.art) - 1))

            for predator in sharks:
                predator.y = min(predator.y, max(1, height - len(predator.art) - 1))
                predator.x = min(predator.x, max(1, width - max(len(line) for line in predator.art) - 1))

        # Update positions
        for school in schools:
            school.move(width, height)

        for fish in fishes:
            fish.move(width, height)

        for bubble in bubbles:
            bubble.move()

        for octopus in octopuses:
            octopus.move(width, height)

        for jellyfish in jellyfishes:
            jellyfish.move(width, height)

        for sea_turtle in sea_turtles:
            sea_turtle.move(width, height)

        for crab in crabs:
            crab.move(width, height)

        for seahorse in seahorses:
            seahorse.move(width, height)

        for dolphin in dolphins:
            dolphin.move(width, height)

        for shark in sharks:
            shark.move(width, height, prey_list=fishes)

        # Randomly generate new bubbles
        if len(bubbles) < MAX_BUBBLES and random.random() < 0.3:
            x = random.randint(1, max(1, width - 1))
            y = height - 2  # Start slightly above the bottom
            char = random.choice(BUBBLE_CHARS)
            color = random.randint(1, len(COLOR_LIST))
            speed = random.uniform(0.1, 0.3)
            bubbles.append(Bubble(x, y, char, color, speed))

        # Remove bubbles that have moved off the screen
        bubbles = [b for b in bubbles if b.y > 0]

        # Spawn food if any
        for food in food_list:
            food.move(height)
        # Remove food that has disappeared
        food_list = [f for f in food_list if f.lifespan > 0 and f.y > 0]

        # Detect and handle collisions between predators and prey
        handle_collisions(sharks, fishes)

        # Attract fish towards food
        for food in food_list:
            for school in schools:
                for fish in school.fish:
                    if fish.x < food.x:
                        fish.direction = 1
                    else:
                        fish.direction = -1
            for fish in fishes:
                if fish.x < food.x:
                    fish.direction = 1
                else:
                    fish.direction = -1

        # Clear screen
        stdscr.erase()

        # Draw seaweeds and corals
        for seaweed in seaweeds:
            seaweed.draw(stdscr)

        for coral in corals:
            coral.draw(stdscr)

        # Draw sea urchins
        for sea_urchin in sea_urchins:
            sea_urchin.draw(stdscr)

        # Draw food
        for food in food_list:
            food.draw(stdscr)

        # Draw jellyfishes
        for jellyfish in jellyfishes:
            jellyfish.draw(stdscr)

        # Draw sea turtles
        for sea_turtle in sea_turtles:
            sea_turtle.draw(stdscr)

        # Draw crabs
        for crab in crabs:
            crab.draw(stdscr)

        # Draw seahorses
        for seahorse in seahorses:
            seahorse.draw(stdscr)

        # Draw schools of fish
        for school in schools:
            school.draw(stdscr)

        # Draw individual fishes
        for fish in fishes:
            fish.draw(stdscr)

        # Draw dolphins
        for dolphin in dolphins:
            dolphin.draw(stdscr)

        # Draw sharks
        for shark in sharks:
            shark.draw(stdscr)

        # Draw bubbles
        for bubble in bubbles:
            bubble.draw(stdscr)

        # Display instructions
        try:
            instructions = "Press 'q' to quit | 'f' Add Fish | 'o' Add Octopus | 'j' Add Jellyfish | 't' Add Sea Turtle | 'c' Add Crab | 's' Add School | 'd' Add Dolphin | 'h' Add Seahorse | 'u' Add Sea Urchin | 'w' Add Shark | Space: Feed | '+'/'-' Adjust Speed"
            stdscr.addstr(0, 0, instructions[:width-1], curses.color_pair(len(COLOR_LIST)))
        except curses.error:
            pass  # Ignore if the terminal is too small

        # Refresh the screen
        stdscr.refresh()

    # Restore cursor
    curses.curs_set(1)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Ensure the terminal state is restored on error
        curses.endwin()
        print(f"An error occurred: {e}")
        sys.exit(1)
