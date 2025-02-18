#!/usr/bin/env python3

import os
import sys
import time
import random
import curses
import curses.textpad
import signal
import threading
from dataclasses import dataclass
from typing import List, Tuple, Optional
from collections import deque

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
MAX_ROCKS = 10
MAX_SHIPWRECKS = 2

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

MEDIUM_FISH_ART = [
    "><>><",
    "><>><",
    "><>><"
]

LARGE_FISH_ART = [
    "><>><>><",
    "><>><>><",
    "><>><>><"
]

FOOD_ART = "*"

# Define Rock and Shipwreck ASCII arts
ROCK_ART = [
    "   ___   ",
    " /     \\ ",
    "|       |",
    " \\___ / "
]

SHIPWRECK_ART = [
    "     /\\     ",
    "    /  \\    ",
    "   /____\\   ",
    "   |    |   ",
    "   |____|   ",
    "    |  |    ",
    "    |  |    "
]

# Define Bubble Characters
BUBBLE_CHARS = ['o', 'O', '°', '*', '•']

# Define different fish types with their ASCII art and speed
FISH_TYPES = [
    {
        "name": "small_fish",
        "right": SMALL_FISH_ART[0],
        "left": SMALL_FISH_ART[0][::-1],
        "speed": 0.1
    },
    {
        "name": "medium_fish",
        "right": MEDIUM_FISH_ART[0],
        "left": MEDIUM_FISH_ART[0][::-1],
        "speed": 0.15
    },
    {
        "name": "large_fish",
        "right": LARGE_FISH_ART[0],
        "left": LARGE_FISH_ART[0][::-1],
        "speed": 0.2
    }
]

# Scoring System
score = 0
score_lock = threading.Lock()

@dataclass
class MarineConfig:
    """Configuration for marine life objects"""
    art: List[str]
    speed: float
    max_count: int
    color: int

class MarineLife:
    """Base class for all marine life"""
    def __init__(self, x: int, y: int, config: MarineConfig):
        self.x = x
        self.y = y
        self.art = config.art
        self.color = config.color
        self.speed = config.speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])
        self.alive = True
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)

    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def move(self, width: int, height: int) -> None:
        if not self.alive:
            return
        self.move_counter += self.speed
        if self.move_counter >= 1:
            self.move_counter = 0
            self._update_position(width, height)

    def _update_position(self, width: int, height: int) -> None:
        # Default movement behavior - override in subclasses
        self.x = (self.x + self.direction) % width

    def draw(self, stdscr) -> None:
        if not self.alive:
            return
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class ObjectPool:
    """Object pool for recycling marine life objects"""
    def __init__(self, factory, max_size: int):
        self.available = deque(maxlen=max_size)
        self.in_use = set()
        self.factory = factory
        self.max_size = max_size

    def acquire(self, *args, **kwargs):
        obj = self.available.pop() if self.available else self.factory(*args, **kwargs)
        self.in_use.add(obj)
        return obj

    def release(self, obj):
        if obj in self.in_use:
            self.in_use.remove(obj)
            if len(self.available) < self.max_size:
                self.available.append(obj)

class CollisionManager:
    """Efficient collision detection using spatial hashing"""
    def __init__(self, width: int, height: int, cell_size: int = 50):
        self.cell_size = cell_size
        self.grid_width = width // cell_size + 1
        self.grid_height = height // cell_size + 1
        self.grid = {}

    def clear(self):
        self.grid.clear()

    def add_object(self, obj):
        x1, y1, x2, y2 = obj.get_bounding_box()
        cell_x1, cell_y1 = x1 // self.cell_size, y1 // self.cell_size
        cell_x2, cell_y2 = x2 // self.cell_size, y2 // self.cell_size

        for i in range(cell_x1, cell_x2 + 1):
            for j in range(cell_y1, cell_y2 + 1):
                key = (i, j)
                if key not in self.grid:
                    self.grid[key] = set()
                self.grid[key].add(obj)

    def get_nearby_objects(self, obj):
        x1, y1, x2, y2 = obj.get_bounding_box()
        cell_x1, cell_y1 = x1 // self.cell_size, y1 // self.cell_size
        cell_x2, cell_y2 = x2 // self.cell_size, y2 // self.cell_size

        nearby = set()
        for i in range(cell_x1, cell_x2 + 1):
            for j in range(cell_y1, cell_y2 + 1):
                if (i, j) in self.grid:
                    nearby.update(self.grid[(i, j)])
        nearby.discard(obj)
        return nearby

# -------------- CLASSES --------------

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
        if self.y < 2:
            return
        try:
            stdscr.addstr(int(self.y), int(self.x), self.char, curses.color_pair(self.color))
        except curses.error:
            pass  # Ignore drawing errors when bubble is out of bounds

class Fish(MarineLife):
    def __init__(self, fish_type, x, y, direction, color, speed, school=None):
        config = MarineConfig(
            art=[fish_type["right"] if direction == 1 else fish_type["left"]],
            speed=speed,
            max_count=MAX_FISH,
            color=color
        )
        super().__init__(x, y, config)
        self.school = school
        self.direction = direction

    def _update_position(self, width: int, height: int) -> None:
        if self.school:
            self.direction = self.school.direction
        self.x += self.direction

        if self.direction == 1 and self.x >= width - self._width - 1:
            self.direction = -1
            self.art = [line[::-1] for line in self.art]
        elif self.direction == -1 and self.x <= 1:
            self.direction = 1
            self.art = [line[::-1] for line in self.art]

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
            # Chasing behavior: move towards the nearest prey
            if prey_list:
                prey = min(prey_list, key=lambda p: abs(p.x - self.x))
                if self.x < prey.x:
                    self.direction = 1
                else:
                    self.direction = -1
                self.x += self.direction * 2  # Sharks move faster

                # Change direction at screen edges
                shark_width = max(len(line) for line in self.art)
                if self.direction == 1 and self.x >= width - shark_width - 1:
                    self.direction = -1
                    self.art = [line[::-1] for line in self.art]  # Reverse art for direction
                elif self.direction == -1 and self.x <= 1:
                    self.direction = 1
                    self.art = [line[::-1] for line in self.art]
            else:
                # Wander randomly if no prey
                self.x += self.direction * 2
                shark_width = max(len(line) for line in self.art)
                if self.direction == 1 and self.x >= width - shark_width - 1:
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
        # Food drifts upwards each frame
        self.y -= 1
        self.lifespan -= 1

    def draw(self, stdscr):
        if self.lifespan > 0 and 1 <= self.y < height:
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

            # Check boundary horizontally
            dolphin_width = max(len(line) for line in self.art)
            if self.direction == 1 and self.x >= width - dolphin_width - 1:
                self.direction = -1
                self.art = [line[::-1] for line in self.art]  # Reverse art
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
            self.y = max(2, min(height - len(self.art) - 1, self.y))

            # Check horizontal boundary with correct width
            seahorse_width = max(len(line) for line in self.art)
            if self.direction == 1 and self.x >= width - seahorse_width - 1:
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
                # Clamp x
                octo_width = max(len(line) for line in self.art)
                self.x = max(1, min(width - octo_width - 1, self.x))
            # Random vertical movement
            if random.random() < 0.3:
                self.y += random.choice([-1, 1])
                # Clamp y
                self.y = max(2, min(height - len(self.art) - 1, self.y))

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Rock:
    """
    Represents a rock in the aquarium.
    """
    def __init__(self, x, y, color):
        self.art = ROCK_ART
        self.x = x
        self.y = y
        self.color = color

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Shipwreck:
    """
    Represents a shipwreck in the aquarium.
    """
    def __init__(self, x, y, color):
        self.art = SHIPWRECK_ART
        self.x = x
        self.y = y
        self.color = color

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class Jellyfish:
    """
    Represents a jellyfish that drifts gracefully.
    """
    def __init__(self, x, y, color, speed):
        self.art = JELLYFISH_ART
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.move_counter = 0
        self.direction = random.choice([-1, 1])  # 1 for right, -1 for left
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
            # Drift horizontally
            self.x += self.direction
            # Slight vertical movement
            self.y += random.choice([-1, 1])
            self.y = max(2, min(height - len(self.art) - 1, self.y))

            # Check horizontal boundary properly
            jelly_width = max(len(line) for line in self.art)
            if self.direction == 1 and self.x >= width - jelly_width - 1:
                self.direction = -1
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass

class SeaTurtle:
    """
    Represents a sea turtle that swims slowly.
    """
    def __init__(self, x, y, color, speed):
        self.art = SEA_TURTLE_ART
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
            # Move horizontally slowly
            self.x += self.direction
            # Slight vertical movement
            self.y += random.choice([-1, 1])
            self.y = max(2, min(height - len(self.art) - 1, self.y))

            turtle_width = max(len(line) for line in self.art)
            # Change direction at screen edges
            if self.direction == 1 and self.x >= width - turtle_width - 1:
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

# --------------------------------------------------------------------
# NEW CRAB CLASS DEFINITION
# --------------------------------------------------------------------
class Crab:
    """
    Represents a crab that scuttles sideways.
    """
    def __init__(self, x, y, color, speed):
        self.art = CRAB_ART
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
            # Basic sideways movement
            self.x += self.direction
            # Optionally random vertical movement:
            # self.y += random.choice([-1, 0, 1])

            # Clamp horizontal position
            crab_width = max(len(line) for line in self.art)
            if self.direction == 1 and self.x >= width - crab_width - 1:
                self.direction = -1
                self.art = [line[::-1] for line in self.art]
            elif self.direction == -1 and self.x <= 1:
                self.direction = 1
                self.art = [line[::-1] for line in self.art]

            # Optional vertical clamp if you add vertical movement
            # self.y = max(2, min(height - len(self.art) - 1, self.y))

    def draw(self, stdscr):
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, curses.color_pair(self.color))
            except curses.error:
                pass
# --------------------------------------------------------------------

def detect_collision(obj1, obj2):
    """Detects if two objects have overlapping bounding boxes."""
    x1_min, y1_min, x1_max, y1_max = obj1.get_bounding_box()
    x2_min, y2_min, x2_max, y2_max = obj2.get_bounding_box()
    return not (x1_max < x2_min or x1_min > x2_max or y1_max < y2_min or y1_min > y2_max)

def handle_collisions(predators, prey_list):
    """Check for collisions between predators and prey."""
    global score
    for predator in predators:
        for prey in prey_list:
            if prey.alive and detect_collision(predator, prey):
                prey.alive = False
                with score_lock:
                    score += 1  # Increment score when a fish is eaten

def main(stdscr):
    global score
    # Initialize curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(0)  # No blocking on getch()
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    # Initialize color pairs
    curses.start_color()
    for idx, color in enumerate(COLOR_LIST, start=1):
        curses.init_pair(idx, color, curses.COLOR_BLACK)
    # Additional color pairs for food, rocks, and shipwrecks
    curses.init_pair(len(COLOR_LIST) + 1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Food
    curses.init_pair(len(COLOR_LIST) + 2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Rocks
    curses.init_pair(len(COLOR_LIST) + 3, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Shipwrecks

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
    rocks = []
    shipwrecks = []

    # Initialize object pools
    fish_pool = ObjectPool(Fish, MAX_FISH)
    shark_pool = ObjectPool(Shark, MAX_SHARKS)
    # ... other pools ...

    # Get initial terminal size
    height, width = stdscr.getmaxyx()

    # Initialize collision manager
    collision_manager = CollisionManager(width, height)

    # Initialize seaweeds and corals
    for _ in range(random.randint(3, 5)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(SEAWEED_ART) - 2
        color = random.randint(1, len(COLOR_LIST))
        seaweeds.append(Seaweed(x, y, color))

    for _ in range(random.randint(2, 4)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(CORAL_ART) - 2
        color = random.randint(1, len(COLOR_LIST))
        corals.append(Coral(x, y, color))

    # Initialize rocks
    for _ in range(random.randint(3, MAX_ROCKS)):
        x = random.randint(1, max(1, width - len(ROCK_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(ROCK_ART) - 1))
        color = len(COLOR_LIST) + 2  # Assign specific color for rocks
        rocks.append(Rock(x, y, color))

    # Initialize shipwrecks
    for _ in range(random.randint(0, MAX_SHIPWRECKS)):
        x = random.randint(1, max(1, width - len(SHIPWRECK_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(SHIPWRECK_ART) - 1))
        color = len(COLOR_LIST) + 3  # Assign specific color for shipwrecks
        shipwrecks.append(Shipwreck(x, y, color))

    # Initialize schools of fish
    for _ in range(random.randint(1, 3)):
        school_direction = random.choice([-1, 1])
        school = School(direction=school_direction)
        for _ in range(random.randint(5, 10)):
            fish_type = random.choice(FISH_TYPES)
            x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
            y = random.randint(2, max(2, height - 5))
            color = random.randint(1, len(COLOR_LIST))
            speed = fish_type["speed"]
            fish = Fish(fish_type, x, y, school_direction, color, speed, school=school)
            school.add_fish(fish)
        schools.append(school)

    # Initialize individual fishes (not part of schools)
    for _ in range(random.randint(5, MAX_FISH)):
        fish_type = random.choice(FISH_TYPES)
        x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
        y = random.randint(2, max(2, height - 5))
        direction = random.choice([-1, 1])
        color = random.randint(1, len(COLOR_LIST))
        speed = fish_type["speed"]
        fishes.append(Fish(fish_type, x, y, direction, color, speed))

    # Initialize octopuses
    for _ in range(random.randint(0, MAX_OCTOPUSES)):
        x = random.randint(1, max(1, width - 10))
        y = random.randint(2, max(2, height - 6))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        octopuses.append(Octopus(x, y, color, speed))

    # Initialize jellyfishes
    for _ in range(random.randint(1, MAX_JELLYFISH)):
        x = random.randint(1, max(1, width - len(JELLYFISH_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(JELLYFISH_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = random.uniform(0.05, 0.1)
        jellyfishes.append(Jellyfish(x, y, color, speed))

    # Initialize sea turtles
    for _ in range(random.randint(0, MAX_SEA_TURTLES)):
        x = random.randint(1, max(1, width - len(SEA_TURTLE_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(SEA_TURTLE_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        sea_turtles.append(SeaTurtle(x, y, color, speed))

    # Initialize crabs
    for _ in range(random.randint(0, MAX_CRABS)):
        x = random.randint(1, max(1, width - len(CRAB_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(CRAB_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        crabs.append(Crab(x, y, color, speed))

    # Initialize seahorses
    for _ in range(random.randint(0, MAX_SEAHORSES)):
        x = random.randint(1, max(1, width - len(SEAHORSE_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(SEAHORSE_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        seahorses.append(Seahorse(x, y, color, speed))

    # Initialize sea urchins
    for _ in range(random.randint(5, MAX_SEA_URCHINS)):
        x = random.randint(1, max(1, width - len(SEA_URCHIN_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(SEA_URCHIN_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        sea_urchins.append(SeaUrchin(x, y, color))

    # Initialize dolphins
    for _ in range(random.randint(0, MAX_DOLPHINS)):
        x = random.randint(1, max(1, width - len(DOLPHIN_ART_FRAMES[0][0]) - 1))
        y = random.randint(2, max(2, height - len(DOLPHIN_ART_FRAMES[0]) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        dolphins.append(Dolphin(x, y, color, speed))

    # Initialize sharks
    for _ in range(random.randint(0, MAX_SHARKS)):
        x = random.randint(1, max(1, width - len(SHARK_ART[0]) - 1))
        y = random.randint(2, max(2, height - len(SHARK_ART) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.2
        sharks.append(Shark(x, y, color, speed))

    animation_speed = 0.02  # Initial delay between frames in seconds
    last_time = time.time()
    frame_duration = animation_speed  # Desired time per frame

    # Food target location (unused, but you can expand on it)
    food_target = None  # Tuple (x, y) if you want targeted feeding

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
                        y = random.randint(2, max(2, height - 5))
                        direction = random.choice([-1, 1])
                        color = random.randint(1, len(COLOR_LIST))
                        speed = fish_type["speed"]
                        fish = Fish(fish_type, x, y, direction, color, speed)
                        fishes.append(fish)
                elif key == ord('o'):
                    # Add a new octopus
                    if len(octopuses) < MAX_OCTOPUSES:
                        x = random.randint(1, max(1, width - 10))
                        y = random.randint(2, max(2, height - 6))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.1
                        octopuses.append(Octopus(x, y, color, speed))
                elif key == ord('j'):
                    # Add a new jellyfish
                    if len(jellyfishes) < MAX_JELLYFISH:
                        x = random.randint(1, max(1, width - len(JELLYFISH_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(JELLYFISH_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = random.uniform(0.05, 0.1)
                        jellyfishes.append(Jellyfish(x, y, color, speed))
                elif key == ord('t'):
                    # Add a new sea turtle
                    if len(sea_turtles) < MAX_SEA_TURTLES:
                        x = random.randint(1, max(1, width - len(SEA_TURTLE_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(SEA_TURTLE_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.05
                        sea_turtles.append(SeaTurtle(x, y, color, speed))
                elif key == ord('c'):
                    # Add a new crab
                    if len(crabs) < MAX_CRABS:
                        x = random.randint(1, max(1, width - len(CRAB_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(CRAB_ART) - 1))
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
                            y = random.randint(2, max(2, height - 5))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = fish_type["speed"]
                            fish = Fish(fish_type, x, y, school_direction, color, speed, school=school)
                            school.add_fish(fish)
                        schools.append(school)
                elif key == ord('d'):
                    # Add a new dolphin
                    if len(dolphins) < MAX_DOLPHINS:
                        x = random.randint(1, max(1, width - len(DOLPHIN_ART_FRAMES[0][0]) - 1))
                        y = random.randint(2, max(2, height - len(DOLPHIN_ART_FRAMES[0]) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.1
                        dolphins.append(Dolphin(x, y, color, speed))
                elif key == ord('h'):
                    # Add a new seahorse
                    if len(seahorses) < MAX_SEAHORSES:
                        x = random.randint(1, max(1, width - len(SEAHORSE_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(SEAHORSE_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.05
                        seahorses.append(Seahorse(x, y, color, speed))
                elif key == ord('u'):
                    # Add a new sea urchin
                    if len(sea_urchins) < MAX_SEA_URCHINS:
                        x = random.randint(1, max(1, width - len(SEA_URCHIN_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(SEA_URCHIN_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        sea_urchins.append(SeaUrchin(x, y, color))
                elif key == ord('w'):
                    # Add a new shark
                    if len(sharks) < MAX_SHARKS:
                        x = random.randint(1, max(1, width - len(SHARK_ART[0]) - 1))
                        y = random.randint(2, max(2, height - len(SHARK_ART) - 1))
                        color = random.randint(1, len(COLOR_LIST))
                        speed = 0.2
                        sharks.append(Shark(x, y, color, speed))
                elif key == ord(' '):
                    # Feed the aquarium
                    if len(food_list) < MAX_FOOD:
                        # Attempt to place food at the mouse click location if available
                        try:
                            _, mx, my, _, mouse_state = curses.getmouse()
                            if mouse_state & curses.BUTTON1_CLICKED:
                                if 0 <= mx < width and 0 <= my < height:
                                    x = mx
                                    y = my
                                else:
                                    x = random.randint(1, max(1, width - 1))
                                    y = height - 2
                        except curses.error:
                            # If no mouse support or invalid, spawn at random
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
                elif key == curses.KEY_MOUSE:
                    # Another way to place food with left-click
                    try:
                        _, mx, my, _, mouse_state = curses.getmouse()
                        if mouse_state & curses.BUTTON1_CLICKED:
                            if len(food_list) < MAX_FOOD:
                                x = mx
                                y = my
                                color = len(COLOR_LIST) + 1  # White color for food
                                food_list.append(Food(x, y, color))
                    except curses.error:
                        pass
        except KeyboardInterrupt:
            break

        # Check for terminal resize
        new_height, new_width = stdscr.getmaxyx()
        if new_height != height or new_width != width:
            height, width = new_height, new_width
            stdscr.clear()

            # Adjust seaweeds and corals positions
            seaweeds = [Seaweed(random.randint(1, max(1, width - 5)),
                                height - len(SEAWEED_ART) - 2,
                                random.randint(1, len(COLOR_LIST))) 
                        for seaweed in seaweeds]
            corals = [Coral(random.randint(1, max(1, width - 5)),
                            height - len(CORAL_ART) - 2,
                            random.randint(1, len(COLOR_LIST)))
                      for coral in corals]

            # Adjust rocks and shipwrecks
            rocks = [Rock(random.randint(1, max(1, width - len(ROCK_ART[0]) - 1)),
                          random.randint(2, max(2, height - len(ROCK_ART) - 1)),
                          len(COLOR_LIST) + 2)
                     for _ in rocks]
            shipwrecks = [Shipwreck(random.randint(1, max(1, width - len(SHIPWRECK_ART[0]) - 1)),
                                    random.randint(2, max(2, height - len(SHIPWRECK_ART) - 1)),
                                    len(COLOR_LIST) + 3)
                          for _ in shipwrecks]

            # Adjust moving marine life positions
            for school in schools:
                for fish in school.fish:
                    fish.y = min(fish.y, max(2, height - 2))
                    fish.x = min(fish.x, max(1, width - len(fish.art) - 1))

            for fish in fishes:
                fish.y = min(fish.y, max(2, height - 2))
                fish.x = min(fish.x, max(1, width - len(fish.art) - 1))

            for predator in sharks:
                predator.y = min(predator.y, max(2, height - len(predator.art) - 1))
                predator.x = min(predator.x, max(1, width - max(len(line) for line in predator.art) - 1))

            for dolphin in dolphins:
                dolphin.y = min(dolphin.y, max(2, height - len(dolphin.art) - 1))
                dolphin.x = min(dolphin.x, max(1, width - max(len(line) for line in dolphin.art) - 1))

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
        bubbles = [b for b in bubbles if b.y > 1]

        # Move food
        for food in food_list:
            food.move(height)
        # Remove food that has disappeared
        food_list = [f for f in food_list if f.lifespan > 0 and f.y > 1]

        # Detect and handle collisions between predators and prey
        handle_collisions(sharks, fishes)

        # Attract fish towards food
        for food in food_list:
            for school in schools:
                for fish in school.fish:
                    fish.direction = 1 if fish.x < food.x else -1
            for fish in fishes:
                fish.direction = 1 if fish.x < food.x else -1

        # Clear screen
        stdscr.erase()

        # Draw seaweeds and corals
        for seaweed in seaweeds:
            seaweed.draw(stdscr)
        for coral in corals:
            coral.draw(stdscr)

        # Draw rocks and shipwrecks
        for rock in rocks:
            rock.draw(stdscr)
        for shipwreck in shipwrecks:
            shipwreck.draw(stdscr)

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

        # Display score and instructions
        try:
            with score_lock:
                score_text = f"Score: {score}"
            instructions = (
                "Press 'q' to quit | 'f' Add Fish | 'o' Add Octopus | "
                "'j' Add Jellyfish | 't' Add Sea Turtle | 'c' Add Crab | 's' Add School | "
                "'d' Add Dolphin | 'h' Add Seahorse | 'u' Add Sea Urchin | 'w' Add Shark | "
                "Space: Feed | '+'/'-' Adjust Speed | Left Click: Feed"
            )
            stdscr.addstr(0, 0, instructions[:width-1], curses.color_pair(len(COLOR_LIST)))
            stdscr.addstr(1, 0, score_text[:width-1], curses.color_pair(len(COLOR_LIST) + 1))
        except curses.error:
            pass  # Ignore if the terminal is too small

        # Refresh the screen
        stdscr.refresh()

    # Restore cursor
    curses.curs_set(1)

if __name__ == "__main__":
    try:
        # Enable mouse events and run the main loop
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Ensure the terminal state is restored on error
        print(f"An error occurred: {e}")
        sys.exit(1)

