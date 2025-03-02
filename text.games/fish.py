#!/usr/bin/env python3

import os
import sys
import time
import random
import curses
import curses.textpad
import signal
import threading
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Set
from collections import deque
from enum import Enum

# ====================================================================
# CONFIGURATION AND CONSTANTS
# ====================================================================

class Config:
    """Central configuration class for the aquarium simulation"""
    # Marine life population limits
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
    MAX_SCHOOLS = 3
    
    # Animation settings
    DEFAULT_ANIMATION_SPEED = 0.02
    MIN_ANIMATION_SPEED = 0.005
    MAX_ANIMATION_SPEED = 0.1
    ANIMATION_SPEED_STEP = 0.005
    
    # Game settings
    DEFAULT_SCORE_INCREMENT = 10
    FOOD_LIFESPAN = 100
    
    # Spatial hashing cell size for collision detection
    COLLISION_CELL_SIZE = 50
    
    # Night/day cycle duration in seconds
    DAY_DURATION = 1350  # 22.5 minutes for day
    NIGHT_DURATION = 1350  # 22.5 minutes for night
    
    # Color settings
    @staticmethod
    def init_colors():
        """Initialize color pairs for the terminal"""
        # Base colors
        curses.start_color()
        for idx, color in enumerate(COLOR_LIST, start=1):
            curses.init_pair(idx, color, curses.COLOR_BLACK)
        
        # Special colors
        curses.init_pair(len(COLOR_LIST) + 1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Food
        curses.init_pair(len(COLOR_LIST) + 2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Rocks
        curses.init_pair(len(COLOR_LIST) + 3, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Shipwrecks
        
        # Night mode colors
        curses.init_pair(100, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Night text
        for idx, color in enumerate(COLOR_LIST, start=101):
            curses.init_pair(idx, color, curses.COLOR_BLUE)  # Night versions of colors
    
    @staticmethod
    def get_color_pair(color_id, is_night=False):
        """Get the appropriate color pair based on day/night state"""
        if is_night and color_id <= len(COLOR_LIST):
            return curses.color_pair(color_id + 100)
        return curses.color_pair(color_id)


# Color constants
COLOR_LIST = [
    curses.COLOR_RED,
    curses.COLOR_GREEN,
    curses.COLOR_YELLOW,
    curses.COLOR_BLUE,
    curses.COLOR_MAGENTA,
    curses.COLOR_CYAN,
    curses.COLOR_WHITE
]

# Define Bubble Characters
BUBBLE_CHARS = ['o', 'O', '°', '*', '•']

# ====================================================================
# ASCII ART DEFINITIONS 
# ====================================================================

class AsciiArt:
    """Container for all ASCII art used in the simulation"""
    
    SEAWEED = [
        "  |",
        " /|\\",
        "/ | \\",
        "  |"
    ]

    CORAL = [
        " /\\",
        "/__\\",
        " || ",
        " || "
    ]

    JELLYFISH = [
        "  \\/",
        " \\||/",
        "  ||",
        " /||\\",
        "  /\\"
    ]

    SEA_TURTLE = [
        "    _____     ",
        "  /       \\  ",
        " |  O   O  | ",
        " |    ^    | ",
        "  \\  ---  /  ",
        "    -----    "
    ]

    CRAB = [
        "  / \\_/ \\  ",
        " ( o   o ) ",
        "  >  ^  <  ",
        " /       \\ "
    ]

    SEAHORSE = [
        "    _~_    ",
        "  /    \\  ",
        " |      | ",
        "  \\____/  ",
        "    ||     "
    ]

    SEA_URCHIN = [
        "   /\\_/\\   ",
        "  /     \\  ",
        " /       \\ ",
        " \\       / ",
        "  \\_____/  "
    ]

    DOLPHIN_FRAMES = [
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

    SHARK = [
        "      /\\",
        "     /  \\",
        "    /____\\",
        "    \\    /",
        "     \\  /",
        "      \\/"
    ]

    SMALL_FISH = {
        "right": "><>",
        "left": "<><"
    }

    MEDIUM_FISH = {
        "right": "><>><",
        "left": "<><><"
    }

    LARGE_FISH = {
        "right": "><>><>><",
        "left": "<><><><><"
    }

    OCTOPUS = [
        "  _-_-_",
        " (' o o ')",
        " /   O   ",
        " \\_/|_|\\_/"
    ]

    FOOD = "*"

    ROCK = [
        "   ___   ",
        " /     \\ ",
        "|       |",
        " \\___ / "
    ]

    SHIPWRECK = [
        "     /\\     ",
        "    /  \\    ",
        "   /____\\   ",
        "   |    |   ",
        "   |____|   ",
        "    |  |    ",
        "    |  |    "
    ]
    
    STARFISH = [
        "  *   ",
        " *|*  ",
        "**|** ",
        " *|*  ",
        "  *   "
    ]
    
    TREASURE_CHEST = [
        " ______ ",
        "|      |",
        "|######|",
        "|______|"
    ]
    
    MENU_BORDER = [
        "╔══════════════════════════════════════╗",
        "║                                      ║",
        "║                                      ║",
        "║                                      ║",
        "║                                      ║",
        "║                                      ║",
        "║                                      ║",
        "║                                      ║",
        "╚══════════════════════════════════════╝"
    ]

# Define different fish types with their ASCII art and speed
FISH_TYPES = [
    {
        "name": "small_fish",
        "right": AsciiArt.SMALL_FISH["right"],
        "left": AsciiArt.SMALL_FISH["left"],
        "speed": 0.1,
        "points": 5
    },
    {
        "name": "medium_fish",
        "right": AsciiArt.MEDIUM_FISH["right"],
        "left": AsciiArt.MEDIUM_FISH["left"],
        "speed": 0.15,
        "points": 10
    },
    {
        "name": "large_fish",
        "right": AsciiArt.LARGE_FISH["right"],
        "left": AsciiArt.LARGE_FISH["left"],
        "speed": 0.2,
        "points": 15
    }
]

# ====================================================================
# GAME STATE AND SCORE TRACKING
# ====================================================================

class GameState:
    """Manages global game state including score and day/night cycle"""
    def __init__(self):
        self.score = 0
        self.score_lock = threading.Lock()
        self.is_night = False
        self.day_night_counter = 0
        self.cycle_duration = Config.DAY_DURATION  # Start with day
        self.paused = False
        self.show_help = False
        self.show_menu = False
        self.selected_menu_item = 0
        self.menu_items = ["Continue", "Save Aquarium", "Load Aquarium", "Toggle Day/Night", "Help", "Quit"]
        self.creatures_eaten = 0
        self.food_consumed = 0

    def increment_score(self, points=Config.DEFAULT_SCORE_INCREMENT):
        """Thread-safe score increment"""
        with self.score_lock:
            self.score += points
            self.creatures_eaten += 1
    
    def increment_food_consumed(self):
        """Track food consumed"""
        with self.score_lock:
            self.food_consumed += 1
    
    def update_day_night_cycle(self):
        """Update day/night cycle"""
        if not self.paused:
            self.day_night_counter += 1
            if self.day_night_counter >= self.cycle_duration:
                self.toggle_day_night()
    
    def toggle_day_night(self):
        """Toggle between day and night"""
        self.is_night = not self.is_night
        self.day_night_counter = 0
        self.cycle_duration = Config.NIGHT_DURATION if self.is_night else Config.DAY_DURATION
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
    
    def toggle_help(self):
        """Toggle help screen"""
        self.show_help = not self.show_help
        
    def toggle_menu(self):
        """Toggle menu screen"""
        self.show_menu = not self.show_menu
        if self.show_menu:
            self.paused = True
        else:
            self.paused = False

# ====================================================================
# BASE CLASSES AND UTILITIES
# ====================================================================

@dataclass
class MarineConfig:
    """Configuration for marine life objects"""
    art: List[str]
    speed: float
    max_count: int
    color: int
    points: int = Config.DEFAULT_SCORE_INCREMENT

class CreatureType(Enum):
    """Enum for creature types"""
    FISH = 1
    SHARK = 2
    JELLYFISH = 3
    TURTLE = 4
    CRAB = 5
    SEAHORSE = 6
    DOLPHIN = 7
    OCTOPUS = 8
    URCHIN = 9
    FOOD = 10
    BUBBLE = 11
    STARFISH = 12

class MarineLife:
    """Base class for all marine life"""
    def __init__(self, x: int, y: int, config: MarineConfig, creature_type: CreatureType):
        self.x = x
        self.y = y
        self.art = config.art
        self.color = config.color
        self.speed = config.speed
        self.points = config.points
        self.move_counter = 0
        self.direction = random.choice([-1, 1])
        self.alive = True
        self._width = max(len(line) for line in self.art) if self.art else 1
        self._height = len(self.art) if self.art else 1
        self.creature_type = creature_type
        self.age = 0  # Age in frames
        self.hungry = False
        
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """Returns the bounding box of the creature for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def move(self, width: int, height: int, game_state: GameState) -> None:
        """Update creature position based on speed and state"""
        if not self.alive or game_state.paused:
            return
            
        self.age += 1
        
        # Adjust speed for night time
        effective_speed = self.speed * 0.7 if game_state.is_night else self.speed
            
        self.move_counter += effective_speed
        if self.move_counter >= 1:
            self.move_counter = 0
            self._update_position(width, height)
            
        # Random chance to get hungry
        if random.random() < 0.0005:
            self.hungry = True

    def _update_position(self, width: int, height: int) -> None:
        """Default movement behavior - override in subclasses"""
        self.x = (self.x + self.direction) % width

    def draw(self, stdscr, game_state: GameState) -> None:
        """Draw the creature onto the terminal"""
        if not self.alive:
            return
            
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass  # Ignore drawing errors when outside the terminal
                
    def reverse_direction(self):
        """Reverse the creature's direction and art"""
        self.direction *= -1
        self.art = [line[::-1] for line in self.art]
        
    def is_hungry(self):
        """Check if creature is hungry"""
        return self.hungry
        
    def eat(self, food):
        """Consume food"""
        self.hungry = False
        return True

class ObjectPool:
    """Object pool for recycling marine life objects"""
    def __init__(self, factory, max_size: int):
        self.available = deque(maxlen=max_size)
        self.in_use = set()
        self.factory = factory
        self.max_size = max_size

    def acquire(self, *args, **kwargs):
        """Get an object from the pool or create a new one"""
        if self.available:
            obj = self.available.pop()
            # Reset the object state
            obj.alive = True
            obj.x = kwargs.get('x', obj.x)
            obj.y = kwargs.get('y', obj.y)
            obj.direction = kwargs.get('direction', random.choice([-1, 1]))
            obj.move_counter = 0
            obj.age = 0
            obj.hungry = False
        else:
            obj = self.factory(*args, **kwargs)
            
        self.in_use.add(obj)
        return obj

    def release(self, obj):
        """Return an object to the pool"""
        if obj in self.in_use:
            self.in_use.remove(obj)
            if len(self.available) < self.max_size:
                self.available.append(obj)
                
    def release_all(self):
        """Return all objects to the pool"""
        for obj in list(self.in_use):
            self.release(obj)

class CollisionManager:
    """Efficient collision detection using spatial hashing"""
    def __init__(self, width: int, height: int, cell_size: int = Config.COLLISION_CELL_SIZE):
        self.cell_size = cell_size
        self.grid_width = width // cell_size + 1
        self.grid_height = height // cell_size + 1
        self.grid = {}

    def clear(self):
        """Clear the spatial hash grid"""
        self.grid.clear()

    def add_object(self, obj):
        """Add an object to the spatial hash grid"""
        x1, y1, x2, y2 = obj.get_bounding_box()
        cell_x1, cell_y1 = max(0, x1 // self.cell_size), max(0, y1 // self.cell_size)
        cell_x2, cell_y2 = max(0, x2 // self.cell_size), max(0, y2 // self.cell_size)

        for i in range(cell_x1, cell_x2 + 1):
            for j in range(cell_y1, cell_y2 + 1):
                key = (i, j)
                if key not in self.grid:
                    self.grid[key] = set()
                self.grid[key].add(obj)

    def get_nearby_objects(self, obj) -> Set[Any]:
        """Get all objects that might be colliding with the given object"""
        x1, y1, x2, y2 = obj.get_bounding_box()
        cell_x1, cell_y1 = max(0, x1 // self.cell_size), max(0, y1 // self.cell_size)
        cell_x2, cell_y2 = max(0, x2 // self.cell_size), max(0, y2 // self.cell_size)

        nearby = set()
        for i in range(cell_x1, cell_x2 + 1):
            for j in range(cell_y1, cell_y2 + 1):
                if (i, j) in self.grid:
                    nearby.update(self.grid[(i, j)])
        nearby.discard(obj)
        return nearby
        
    def check_collision(self, obj1, obj2) -> bool:
        """Checks if two objects have overlapping bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = obj1.get_bounding_box()
        x2_min, y2_min, x2_max, y2_max = obj2.get_bounding_box()
        return not (x1_max < x2_min or x1_min > x2_max or y1_max < y2_min or y1_min > y2_max)

# ====================================================================
# MARINE LIFE IMPLEMENTATIONS
# ====================================================================

class Seaweed:
    """Represents seaweed in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.SEAWEED
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def draw(self, stdscr, game_state):
        """Draw the seaweed on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass  # Ignore drawing errors when out of bounds

class Coral:
    """Represents coral in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.CORAL
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def draw(self, stdscr, game_state):
        """Draw the coral on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass  # Ignore drawing errors when out of bounds

class Starfish:
    """Represents a starfish in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.STARFISH
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def draw(self, stdscr, game_state):
        """Draw the starfish on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass

class TreasureChest:
    """Represents a treasure chest in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.TREASURE_CHEST
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        self.opened = False
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)
        
    def open(self):
        """Open the treasure chest"""
        if not self.opened:
            self.opened = True
            self.art[2] = "|      |"  # Change the closed lid to open
            return True
        return False

    def draw(self, stdscr, game_state):
        """Draw the treasure chest on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass

class Bubble(MarineLife):
    """Represents a bubble that moves upwards on the screen with varied speeds."""
    def __init__(self, x, y, char, color, speed):
        config = MarineConfig(
            art=[char],
            speed=speed,
            max_count=Config.MAX_BUBBLES,
            color=color
        )
        super().__init__(x, y, config, CreatureType.BUBBLE)
        self.char = char
        self._width = 1
        self._height = 1

    def _update_position(self, width, height):
        """Move the bubble upward"""
        self.y -= 1
        # Add slight horizontal drift
        if random.random() < 0.2:
            self.x += random.choice([-1, 0, 1])
            # Keep within screen bounds
            self.x = max(0, min(width - 1, self.x))

    def draw(self, stdscr, game_state):
        """Draw the bubble on the screen"""
        if self.y < 2:
            return
        try:
            color_pair = Config.get_color_pair(self.color, game_state.is_night)
            stdscr.addstr(int(self.y), int(self.x), self.char, color_pair)
        except curses.error:
            pass

class Fish(MarineLife):
    """Represents a fish in the aquarium."""
    def __init__(self, fish_type, x, y, direction, color, speed, school=None):
        art_choice = fish_type["right"] if direction == 1 else fish_type["left"]
        config = MarineConfig(
            art=[art_choice],
            speed=speed,
            max_count=Config.MAX_FISH,
            color=color,
            points=fish_type["points"]
        )
        super().__init__(x, y, config, CreatureType.FISH)
        self.fish_type = fish_type
        self.school = school
        self.direction = direction
        self.full_art = art_choice

    def _update_position(self, width: int, height: int) -> None:
        """Update the fish position and handle screen boundaries"""
        # Follow school direction if part of a school
        if self.school:
            self.direction = self.school.direction
            
        # Move in current direction
        self.x += self.direction
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.direction = -1
            self.art = [self.fish_type["left"]]
        elif self.direction == -1 and self.x <= 1:
            self.direction = 1
            self.art = [self.fish_type["right"]]
            
        # Small random vertical movement
        if random.random() < 0.2:
            self.y += random.choice([-1, 0, 1])
            # Keep within screen bounds
            self.y = max(2, min(height - 3, self.y))
            
    def eat(self, food):
        """Eat food and gain points"""
        self.hungry = False
        return True

class School:
    """Represents a school of fish."""
    def __init__(self, direction=1):
        self.fish = []
        self.direction = direction  # 1 for right, -1 for left
        self.target_x = None
        self.target_y = None

    def add_fish(self, fish):
        """Add a fish to the school"""
        self.fish.append(fish)
        fish.school = self

    def move(self, width, height, game_state):
        """Move all fish in the school"""
        if game_state.paused:
            return
            
        # Update school target if necessary
        if self.target_x is None or random.random() < 0.02:
            self.target_x = random.randint(10, width - 10)
            self.target_y = random.randint(5, height - 10)
            
        # Update direction based on target
        if self.target_x is not None:
            # Calculate center of school
            if self.fish:
                center_x = sum(fish.x for fish in self.fish) / len(self.fish)
                if center_x < self.target_x:
                    self.direction = 1
                else:
                    self.direction = -1
        
        # Move each fish
        for fish in self.fish:
            fish.direction = self.direction
            fish.move(width, height, game_state)
            
        # Remove dead fish
        self.fish = [fish for fish in self.fish if fish.alive]

    def draw(self, stdscr, game_state):
        """Draw all fish in the school"""
        for fish in self.fish:
            fish.draw(stdscr, game_state)

class Shark(MarineLife):
    """Represents a shark predator."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.SHARK,
            speed=speed,
            max_count=Config.MAX_SHARKS,
            color=color,
            points=30
        )
        super().__init__(x, y, config, CreatureType.SHARK)
        
    def _update_position(self, width, height):
        """Move the shark and handle screen boundaries"""
        # Move in current direction
        self.x += self.direction * 2  # Sharks move faster
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.reverse_direction()
        elif self.direction == -1 and self.x <= 1:
            self.reverse_direction()
            
        # Small random vertical movement
        if random.random() < 0.1:
            self.y += random.choice([-1, 0, 1])
            # Keep within screen bounds
            self.y = max(2, min(height - self._height - 1, self.y))
    
    def hunt(self, prey_list, collision_manager):
        """Hunting behavior: move towards nearest prey"""
        if not prey_list:
            return
            
        # Find the closest prey
        closest_prey = None
        min_distance = float('inf')
        
        for prey in prey_list:
            if prey.alive:
                distance = abs(prey.x - self.x) + abs(prey.y - self.y)  # Manhattan distance
                if distance < min_distance:
                    min_distance = distance
                    closest_prey = prey
                    
        # Change direction based on closest prey position
        if closest_prey:
            if self.x < closest_prey.x and self.direction == -1:
                self.reverse_direction()
            elif self.x > closest_prey.x and self.direction == 1:
                self.reverse_direction()
                
            # Check for collisions with prey
            for prey in prey_list:
                if prey.alive and collision_manager.check_collision(self, prey):
                    prey.alive = False
                    return prey.points
        
        return 0

class Food(MarineLife):
    """Represents food that attracts fish."""
    def __init__(self, x, y, color):
        config = MarineConfig(
            art=[AsciiArt.FOOD],
            speed=0.05,
            max_count=Config.MAX_FOOD,
            color=color
        )
        super().__init__(x, y, config, CreatureType.FOOD)
        self.lifespan = Config.FOOD_LIFESPAN
        self._width = 1
        self._height = 1

    def _update_position(self, width, height):
        """Food drifts downwards slowly"""
        self.y += 0.5
        self.lifespan -= 1
        
        # Add slight horizontal drift
        if random.random() < 0.2:
            self.x += random.choice([-1, 0, 1])
            # Keep within screen bounds
            self.x = max(0, min(width - 1, self.x))
    
    def is_expired(self):
        """Check if food has expired"""
        return self.lifespan <= 0
        
    def draw(self, stdscr, game_state):
        """Draw the food on the screen"""
        if self.lifespan <= 0:
            return
            
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        try:
            stdscr.addstr(int(self.y), int(self.x), AsciiArt.FOOD, color_pair)
        except curses.error:
            pass

class Dolphin(MarineLife):
    """Represents a dolphin that can perform jumps."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.DOLPHIN_FRAMES[0],
            speed=speed,
            max_count=Config.MAX_DOLPHINS,
            color=color,
            points=25
        )
        super().__init__(x, y, config, CreatureType.DOLPHIN)
        self.art_frames = AsciiArt.DOLPHIN_FRAMES
        self.current_frame = 0
        self.jump_counter = 0
        self.jump_height = 0
        self.original_y = y

    def _update_position(self, width, height):
        """Move the dolphin and handle jumping behavior"""
        # Move horizontally
        self.x += self.direction * 2
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.reverse_direction()
        elif self.direction == -1 and self.x <= 1:
            self.reverse_direction()
            
        # Jumping behavior
        if self.jump_counter > 0:
            # Continuing a jump
            self.jump_counter -= 1
            # Parabolic jumping motion
            if self.jump_counter > 5:
                self.y -= 1  # Going up
            elif self.jump_counter < 3:
                self.y += 1  # Going down
                
            if self.jump_counter == 0:
                # Land at original position
                self.y = self.original_y
        elif random.random() < 0.01:
            # Start a new jump
            self.jump_counter = 10
            self.original_y = self.y
            
        # Animate frames
        self.current_frame = (self.current_frame + 1) % len(self.art_frames)
        self.art = self.art_frames[self.current_frame]
        
        # Flip frames if moving left
        if self.direction == -1:
            self.art = [line[::-1] for line in self.art]

class Seahorse(MarineLife):
    """Represents a seahorse that swims gracefully."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.SEAHORSE,
            speed=speed,
            max_count=Config.MAX_SEAHORSES,
            color=color,
            points=15
        )
        super().__init__(x, y, config, CreatureType.SEAHORSE)

    def _update_position(self, width, height):
        """Move the seahorse with gentle up/down motion"""
        # Move horizontally slowly
        self.x += self.direction
        
        # Vertical bobbing motion
        self.y += random.choice([-1, 0, 1])
        self.y = max(2, min(height - self._height - 1, self.y))
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.reverse_direction()
        elif self.direction == -1 and self.x <= 1:
            self.reverse_direction()

class SeaUrchin(MarineLife):
    """Represents a stationary sea urchin."""
    def __init__(self, x, y, color):
        config = MarineConfig(
            art=AsciiArt.SEA_URCHIN,
            speed=0,  # Stationary
            max_count=Config.MAX_SEA_URCHINS,
            color=color,
            points=5
        )
        super().__init__(x, y, config, CreatureType.URCHIN)
        
    def _update_position(self, width, height):
        """Sea urchins are stationary"""
        pass  # No movement

class Octopus(MarineLife):
    """Represents an octopus that moves around the screen."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.OCTOPUS,
            speed=speed,
            max_count=Config.MAX_OCTOPUSES,
            color=color,
            points=20
        )
        super().__init__(x, y, config, CreatureType.OCTOPUS)
        
    def _update_position(self, width, height):
        """Move the octopus with random motion"""
        # Random movement in all directions
        if random.random() < 0.3:
            self.x += random.choice([-1, 0, 1])
        if random.random() < 0.3:
            self.y += random.choice([-1, 0, 1])
            
        # Keep within screen bounds
        self.x = max(1, min(width - self._width - 1, self.x))
        self.y = max(2, min(height - self._height - 1, self.y))

class Rock:
    """Represents a rock in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.ROCK
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def draw(self, stdscr, game_state):
        """Draw the rock on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass

class Shipwreck:
    """Represents a shipwreck in the aquarium."""
    def __init__(self, x, y, color):
        self.art = AsciiArt.SHIPWRECK
        self.x = x
        self.y = y
        self.color = color
        self._width = max(len(line) for line in self.art)
        self._height = len(self.art)
        
    def get_bounding_box(self):
        """Returns the bounding box for collision detection"""
        return (self.x, self.y, self.x + self._width, self.y + self._height)

    def draw(self, stdscr, game_state):
        """Draw the shipwreck on the screen"""
        color_pair = Config.get_color_pair(self.color, game_state.is_night)
        for i, line in enumerate(self.art):
            try:
                stdscr.addstr(int(self.y) + i, int(self.x), line, color_pair)
            except curses.error:
                pass

class Jellyfish(MarineLife):
    """Represents a jellyfish that drifts gracefully."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.JELLYFISH,
            speed=speed,
            max_count=Config.MAX_JELLYFISH,
            color=color,
            points=15
        )
        super().__init__(x, y, config, CreatureType.JELLYFISH)

    def _update_position(self, width, height):
        """Move the jellyfish with drifting motion"""
        # Drift horizontally
        self.x += self.direction
        
        # Pulsating up/down movement
        if random.random() < 0.5:
            self.y += random.choice([-1, 0, 1])
        self.y = max(2, min(height - self._height - 1, self.y))
        
        # Check horizontal boundary
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.direction = -1
        elif self.direction == -1 and self.x <= 1:
            self.direction = 1

class SeaTurtle(MarineLife):
    """Represents a sea turtle that swims slowly."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.SEA_TURTLE,
            speed=speed,
            max_count=Config.MAX_SEA_TURTLES,
            color=color,
            points=20
        )
        super().__init__(x, y, config, CreatureType.TURTLE)

    def _update_position(self, width, height):
        """Move the sea turtle with slow, deliberate motion"""
        # Move horizontally slowly
        self.x += self.direction
        
        # Occasional vertical movement
        if random.random() < 0.2:
            self.y += random.choice([-1, 0, 1])
        self.y = max(2, min(height - self._height - 1, self.y))
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.reverse_direction()
        elif self.direction == -1 and self.x <= 1:
            self.reverse_direction()

class Crab(MarineLife):
    """Represents a crab that scuttles sideways."""
    def __init__(self, x, y, color, speed):
        config = MarineConfig(
            art=AsciiArt.CRAB,
            speed=speed,
            max_count=Config.MAX_CRABS,
            color=color,
            points=10
        )
        super().__init__(x, y, config, CreatureType.CRAB)
        
    def _update_position(self, width, height):
        """Move the crab with sideways scuttling motion"""
        # Sideways movement
        self.x += self.direction
        
        # Occasional vertical movement
        if random.random() < 0.1:
            self.y += random.choice([-1, 0, 0, 1])  # More likely to stay at same level
        self.y = max(2, min(height - self._height - 1, self.y))
        
        # Check boundaries and reverse direction if needed
        if self.direction == 1 and self.x >= width - self._width - 1:
            self.reverse_direction()
        elif self.direction == -1 and self.x <= 1:
            self.reverse_direction()

# ====================================================================
# SAVE/LOAD FUNCTIONALITY
# ====================================================================

class AquariumSaver:
    """Handles saving and loading the aquarium state"""
    
    @staticmethod
    def save_aquarium(filename, marine_life, game_state):
        """Save the current state of the aquarium to a file"""
        save_data = {
            "score": game_state.score,
            "creatures_eaten": game_state.creatures_eaten,
            "food_consumed": game_state.food_consumed,
            "is_night": game_state.is_night,
            "marine_life": []
        }
        
        # Save data for each marine life type
        for life in marine_life:
            if hasattr(life, 'creature_type') and life.alive:
                life_data = {
                    "type": life.creature_type.name,
                    "x": life.x,
                    "y": life.y,
                    "direction": life.direction,
                    "color": life.color
                }
                
                # Add type-specific data
                if life.creature_type == CreatureType.FISH:
                    life_data["fish_type"] = life.fish_type["name"]
                
                save_data["marine_life"].append(life_data)
        
        # Save to file
        try:
            with open(filename, 'w') as f:
                json.dump(save_data, f)
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def load_aquarium(filename, marine_life_factory):
        """Load an aquarium state from a file"""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
                
            # Create marine life from saved data
            new_marine_life = []
            game_state = GameState()
            game_state.score = save_data.get("score", 0)
            game_state.creatures_eaten = save_data.get("creatures_eaten", 0)
            game_state.food_consumed = save_data.get("food_consumed", 0)
            game_state.is_night = save_data.get("is_night", False)
            
            for life_data in save_data.get("marine_life", []):
                creature_type = life_data.get("type")
                
                if creature_type:
                    # Create the appropriate marine life object
                    creature = marine_life_factory.create_creature(
                        CreatureType[creature_type],
                        life_data.get("x", 0),
                        life_data.get("y", 0),
                        life_data.get("direction", 1),
                        life_data.get("color", 1),
                        life_data.get("fish_type", "small_fish")
                    )
                    
                    if creature:
                        new_marine_life.append(creature)
            
            return new_marine_life, game_state
        except Exception as e:
            return None, None

class MarineLifeFactory:
    """Factory for creating different types of marine life"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def create_creature(self, creature_type, x=None, y=None, direction=None, color=None, fish_type_name=None):
        """Create a marine life creature of the specified type"""
        if x is None:
            x = random.randint(1, max(1, self.width - 10))
        if y is None:
            y = random.randint(2, max(2, self.height - 10))
        if direction is None:
            direction = random.choice([-1, 1])
        if color is None:
            color = random.randint(1, len(COLOR_LIST))
            
        if creature_type == CreatureType.FISH:
            # Find the fish type by name
            fish_type = next((ft for ft in FISH_TYPES if ft["name"] == fish_type_name), FISH_TYPES[0])
            return Fish(fish_type, x, y, direction, color, fish_type["speed"])
            
        elif creature_type == CreatureType.SHARK:
            return Shark(x, y, color, 0.2)
            
        elif creature_type == CreatureType.JELLYFISH:
            return Jellyfish(x, y, color, random.uniform(0.05, 0.1))
            
        elif creature_type == CreatureType.TURTLE:
            return SeaTurtle(x, y, color, 0.05)
            
        elif creature_type == CreatureType.CRAB:
            return Crab(x, y, color, 0.1)
            
        elif creature_type == CreatureType.SEAHORSE:
            return Seahorse(x, y, color, 0.05)
            
        elif creature_type == CreatureType.DOLPHIN:
            return Dolphin(x, y, color, 0.1)
            
        elif creature_type == CreatureType.OCTOPUS:
            return Octopus(x, y, color, 0.1)
            
        elif creature_type == CreatureType.URCHIN:
            return SeaUrchin(x, y, color)
            
        elif creature_type == CreatureType.FOOD:
            return Food(x, y, len(COLOR_LIST) + 1)
            
        elif creature_type == CreatureType.BUBBLE:
            char = random.choice(BUBBLE_CHARS)
            return Bubble(x, y, char, color, random.uniform(0.1, 0.3))
            
        return None

# ====================================================================
# UI COMPONENTS
# ====================================================================

class UI:
    """Handles all UI components and rendering"""
    
    @staticmethod
    def draw_border(stdscr, height, width, game_state):
        """Draw a border around the screen"""
        color_pair = Config.get_color_pair(len(COLOR_LIST) + 1, game_state.is_night)
        for i in range(width):
            try:
                stdscr.addstr(0, i, "═", color_pair)
                stdscr.addstr(height-1, i, "═", color_pair)
            except curses.error:
                pass
                
        for i in range(height):
            try:
                stdscr.addstr(i, 0, "║", color_pair)
                stdscr.addstr(i, width-1, "║", color_pair)
            except curses.error:
                pass
                
        # Corners
        try:
            stdscr.addstr(0, 0, "╔", color_pair)
            stdscr.addstr(0, width-1, "╗", color_pair)
            stdscr.addstr(height-1, 0, "╚", color_pair)
            stdscr.addstr(height-1, width-1, "╝", color_pair)
        except curses.error:
            pass
    
    @staticmethod
    def draw_status_bar(stdscr, width, game_state):
        """Draw the status bar with score and state information"""
        status_color = Config.get_color_pair(len(COLOR_LIST) + 1, game_state.is_night)
        
        # Format the status text
        status_text = f" Score: {game_state.score} | Creatures Eaten: {game_state.creatures_eaten} "
        status_text += f"| Food Consumed: {game_state.food_consumed} "
        
        # Add day/night indicator
        if game_state.is_night:
            status_text += "| 🌙 Night "
        else:
            status_text += "| ☀️ Day "
            
        # Add pause indicator
        if game_state.paused:
            status_text += "| ⏸️ PAUSED "
            
        # Make sure it fits in the width
        status_text = status_text[:width-1]
        
        try:
            stdscr.addstr(0, 0, status_text, status_color)
        except curses.error:
            pass
    
    @staticmethod
    def draw_help_screen(stdscr, height, width, game_state):
        """Draw the help screen with keyboard commands"""
        if not game_state.show_help:
            return
            
        # Calculate the help window dimensions
        help_height = 16
        help_width = 50
        start_y = (height - help_height) // 2
        start_x = (width - help_width) // 2
        
        # Draw help window
        for y in range(help_height):
            for x in range(help_width):
                if (y == 0 or y == help_height - 1) or (x == 0 or x == help_width - 1):
                    try:
                        stdscr.addstr(start_y + y, start_x + x, "█", curses.color_pair(7))
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(start_y + y, start_x + x, " ", curses.color_pair(0))
                    except curses.error:
                        pass
        
        # Draw help title
        title = "╔═══ AQUARIUM HELP ═══╗"
        try:
            stdscr.addstr(start_y + 1, start_x + (help_width - len(title)) // 2, title, curses.color_pair(7))
        except curses.error:
            pass
            
        # Draw help content
        help_items = [
            "q - Quit the aquarium",
            "p - Pause/resume simulation",
            "h - Toggle this help screen",
            "m - Open menu",
            "n - Toggle day/night cycle",
            "SPACE - Add food at random position",
            "+/- - Adjust animation speed",
            "f - Add a new fish",
            "o - Add an octopus",
            "j - Add a jellyfish",
            "d - Add a dolphin",
            "t - Add a sea turtle",
            "s - Add a school of fish"
        ]
        
        for i, item in enumerate(help_items):
            try:
                stdscr.addstr(start_y + 3 + i, start_x + 3, item, curses.color_pair(7))
            except curses.error:
                pass
                
        # Draw footer
        footer = "Press 'h' to close help"
        try:
            stdscr.addstr(start_y + help_height - 2, start_x + (help_width - len(footer)) // 2, 
                          footer, curses.color_pair(7))
        except curses.error:
            pass
    
    @staticmethod
    def draw_menu(stdscr, height, width, game_state):
        """Draw the menu screen"""
        if not game_state.show_menu:
            return
            
        # Calculate menu dimensions
        menu_height = 10
        menu_width = 30
        start_y = (height - menu_height) // 2
        start_x = (width - menu_width) // 2
        
        # Draw menu window
        for y in range(menu_height):
            for x in range(menu_width):
                if (y == 0 or y == menu_height - 1) or (x == 0 or x == menu_width - 1):
                    try:
                        stdscr.addstr(start_y + y, start_x + x, "█", curses.color_pair(7))
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(start_y + y, start_x + x, " ", curses.color_pair(0))
                    except curses.error:
                        pass
        
        # Draw menu title
        title = "╔═══ MENU ═══╗"
        try:
            stdscr.addstr(start_y + 1, start_x + (menu_width - len(title)) // 2, title, curses.color_pair(7))
        except curses.error:
            pass
            
        # Draw menu items
        for i, item in enumerate(game_state.menu_items):
            try:
                if i == game_state.selected_menu_item:
                    # Highlight selected item
                    stdscr.addstr(start_y + 3 + i, start_x + 3, f"> {item}", curses.color_pair(2))
                else:
                    stdscr.addstr(start_y + 3 + i, start_x + 3, f"  {item}", curses.color_pair(7))
            except curses.error:
                pass
                
        # Draw navigation help
        footer = "Use ↑↓ to navigate, ENTER to select"
        try:
            stdscr.addstr(start_y + menu_height - 2, start_x + (menu_width - len(footer)) // 2, 
                          footer, curses.color_pair(7))
        except curses.error:
            pass
    
    @staticmethod
    def draw_instructions(stdscr, height, width, game_state):
        """Draw the controls/instructions bar at the bottom of the screen"""
        instructions_color = Config.get_color_pair(len(COLOR_LIST), game_state.is_night)
        
        instructions = (
            "q:Quit | SPACE:Feed | +/-:Speed | h:Help | p:Pause | m:Menu | n:Day/Night"
        )
        
        try:
            stdscr.addstr(height-1, 1, instructions[:width-2], instructions_color)
        except curses.error:
            pass

# ====================================================================
# COLLISION HANDLING
# ====================================================================

def handle_collisions(collision_manager, predators, prey_list, game_state):
    """Check for collisions between predators and prey, and update score"""
    points_gained = 0
    
    # Update spatial hash grid
    collision_manager.clear()
    
    # Add all creatures to the spatial hash grid
    for predator in predators:
        if predator.alive:
            collision_manager.add_object(predator)
            
    for prey in prey_list:
        if prey.alive:
            collision_manager.add_object(prey)
    
    # Check for shark hunting success and award points
    for predator in predators:
        if predator.alive and hasattr(predator, 'hunt'):
            points = predator.hunt(prey_list, collision_manager)
            if points > 0:
                game_state.increment_score(points)
                points_gained += points
    
    return points_gained

def handle_feeding(collision_manager, marine_creatures, food_list, game_state):
    """Handle creatures eating food"""
    # Clear and rebuild spatial hash grid
    collision_manager.clear()
    
    # Add all food and hungry creatures
    for food in food_list:
        if food.alive and not food.is_expired():
            collision_manager.add_object(food)
            
    for creature in marine_creatures:
        if creature.alive and creature.is_hungry():
            collision_manager.add_object(creature)
    
    # Check for creatures eating food
    for food in list(food_list):
        if not food.alive or food.is_expired():
            continue
            
        nearby_creatures = collision_manager.get_nearby_objects(food)
        for creature in nearby_creatures:
            if creature.alive and creature.is_hungry() and collision_manager.check_collision(food, creature):
                if creature.eat(food):
                    food.alive = False
                    game_state.increment_food_consumed()
                    break

# ====================================================================
# MAIN FUNCTION
# ====================================================================

def main(stdscr):
    """Main function for the aquarium simulation"""
    # Initialize curses
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Non-blocking input
    stdscr.timeout(0)  # No blocking on getch()
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    
    # Initialize colors
    Config.init_colors()
    
    # Initialize game state
    game_state = GameState()
    
    # Get initial terminal size
    height, width = stdscr.getmaxyx()
    
    # Initialize marine life factory
    factory = MarineLifeFactory(width, height)
    
    # Initialize object pools and collections
    seaweeds = []
    corals = []
    starfish = []
    treasure_chests = []
    rocks = []
    shipwrecks = []
    schools = []
    bubbles = []
    fishes = []
    sharks = []
    jellyfishes = []
    sea_turtles = []
    crabs = []
    seahorses = []
    sea_urchins = []
    dolphins = []
    octopuses = []
    food_list = []
    
    # Initialize collision manager
    collision_manager = CollisionManager(width, height)
    
    # Initialize stationary decorations
    for _ in range(random.randint(3, 5)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(AsciiArt.SEAWEED) - 2
        color = random.randint(1, len(COLOR_LIST))
        seaweeds.append(Seaweed(x, y, color))

    for _ in range(random.randint(2, 4)):
        x = random.randint(1, max(1, width - 5))
        y = height - len(AsciiArt.CORAL) - 2
        color = random.randint(1, len(COLOR_LIST))
        corals.append(Coral(x, y, color))
        
    for _ in range(random.randint(2, 5)):
        x = random.randint(1, max(1, width - len(AsciiArt.STARFISH[0]) - 1))
        y = height - len(AsciiArt.STARFISH) - 2
        color = random.randint(1, len(COLOR_LIST))
        starfish.append(Starfish(x, y, color))
        
    # Add a treasure chest
    x = random.randint(1, max(1, width - len(AsciiArt.TREASURE_CHEST[0]) - 1))
    y = height - len(AsciiArt.TREASURE_CHEST) - 2
    color = random.randint(1, len(COLOR_LIST))
    treasure_chests.append(TreasureChest(x, y, color))

    # Initialize rocks
    for _ in range(random.randint(3, Config.MAX_ROCKS)):
        x = random.randint(1, max(1, width - len(AsciiArt.ROCK[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.ROCK) - 1))
        color = len(COLOR_LIST) + 2  # Special color for rocks
        rocks.append(Rock(x, y, color))

    # Initialize shipwrecks
    for _ in range(random.randint(0, Config.MAX_SHIPWRECKS)):
        x = random.randint(1, max(1, width - len(AsciiArt.SHIPWRECK[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.SHIPWRECK) - 1))
        color = len(COLOR_LIST) + 3  # Special color for shipwrecks
        shipwrecks.append(Shipwreck(x, y, color))

    # Initialize schools of fish
    for _ in range(random.randint(1, Config.MAX_SCHOOLS)):
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

    # Initialize individual fishes
    for _ in range(random.randint(5, Config.MAX_FISH)):
        fish_type = random.choice(FISH_TYPES)
        x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
        y = random.randint(2, max(2, height - 5))
        direction = random.choice([-1, 1])
        color = random.randint(1, len(COLOR_LIST))
        speed = fish_type["speed"]
        fishes.append(Fish(fish_type, x, y, direction, color, speed))

    # Initialize sea creatures
    for _ in range(random.randint(0, Config.MAX_OCTOPUSES)):
        x = random.randint(1, max(1, width - len(AsciiArt.OCTOPUS[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.OCTOPUS) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        octopuses.append(Octopus(x, y, color, speed))

    for _ in range(random.randint(1, Config.MAX_JELLYFISH)):
        x = random.randint(1, max(1, width - len(AsciiArt.JELLYFISH[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.JELLYFISH) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = random.uniform(0.05, 0.1)
        jellyfishes.append(Jellyfish(x, y, color, speed))

    for _ in range(random.randint(0, Config.MAX_SEA_TURTLES)):
        x = random.randint(1, max(1, width - len(AsciiArt.SEA_TURTLE[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.SEA_TURTLE) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        sea_turtles.append(SeaTurtle(x, y, color, speed))

    for _ in range(random.randint(0, Config.MAX_CRABS)):
        x = random.randint(1, max(1, width - len(AsciiArt.CRAB[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.CRAB) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        crabs.append(Crab(x, y, color, speed))

    for _ in range(random.randint(0, Config.MAX_SEAHORSES)):
        x = random.randint(1, max(1, width - len(AsciiArt.SEAHORSE[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.SEAHORSE) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.05
        seahorses.append(Seahorse(x, y, color, speed))

    for _ in range(random.randint(5, Config.MAX_SEA_URCHINS)):
        x = random.randint(1, max(1, width - len(AsciiArt.SEA_URCHIN[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.SEA_URCHIN) - 1))
        color = random.randint(1, len(COLOR_LIST))
        sea_urchins.append(SeaUrchin(x, y, color))

    for _ in range(random.randint(0, Config.MAX_DOLPHINS)):
        x = random.randint(1, max(1, width - len(AsciiArt.DOLPHIN_FRAMES[0][0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.DOLPHIN_FRAMES[0]) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.1
        dolphins.append(Dolphin(x, y, color, speed))

    for _ in range(random.randint(0, Config.MAX_SHARKS)):
        x = random.randint(1, max(1, width - len(AsciiArt.SHARK[0]) - 1))
        y = random.randint(2, max(2, height - len(AsciiArt.SHARK) - 1))
        color = random.randint(1, len(COLOR_LIST))
        speed = 0.2
        sharks.append(Shark(x, y, color, speed))

    animation_speed = Config.DEFAULT_ANIMATION_SPEED
    last_time = time.time()
    frame_duration = animation_speed  # Desired time per frame

    # Main game loop
    while True:
        current_time = time.time()
        elapsed = current_time - last_time

        # Maintain consistent frame rate
        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)
            current_time = time.time()
            elapsed = current_time - last_time

        last_time = current_time
        
        # Update day/night cycle
        game_state.update_day_night_cycle()

        # Handle user input
        try:
            key = stdscr.getch()
            if key != -1:
                if game_state.show_menu:
                    # Menu navigation
                    if key == curses.KEY_UP:
                        game_state.selected_menu_item = (game_state.selected_menu_item - 1) % len(game_state.menu_items)
                    elif key == curses.KEY_DOWN:
                        game_state.selected_menu_item = (game_state.selected_menu_item + 1) % len(game_state.menu_items)
                    elif key == 10:  # Enter key
                        # Handle menu selection
                        selected = game_state.menu_items[game_state.selected_menu_item]
                        if selected == "Continue":
                            game_state.toggle_menu()
                        elif selected == "Save Aquarium":
                            # Implement save functionality
                            AquariumSaver.save_aquarium("aquarium_save.json", 
                                                       fishes + sharks + jellyfishes + sea_turtles + 
                                                       crabs + seahorses + dolphins + octopuses, 
                                                       game_state)
                            game_state.toggle_menu()
                        elif selected == "Load Aquarium":
                            # Implement load functionality
                            new_marine_life, new_game_state = AquariumSaver.load_aquarium(
                                "aquarium_save.json", factory)
                            if new_marine_life and new_game_state:
                                # Clear existing creatures
                                fishes.clear()
                                sharks.clear()
                                jellyfishes.clear()
                                sea_turtles.clear()
                                crabs.clear()
                                seahorses.clear()
                                dolphins.clear()
                                octopuses.clear()
                                
                                # Add loaded creatures
                                for creature in new_marine_life:
                                    if creature.creature_type == CreatureType.FISH:
                                        fishes.append(creature)
                                    elif creature.creature_type == CreatureType.SHARK:
                                        sharks.append(creature)
                                    elif creature.creature_type == CreatureType.JELLYFISH:
                                        jellyfishes.append(creature)
                                    elif creature.creature_type == CreatureType.TURTLE:
                                        sea_turtles.append(creature)
                                    elif creature.creature_type == CreatureType.CRAB:
                                        crabs.append(creature)
                                    elif creature.creature_type == CreatureType.SEAHORSE:
                                        seahorses.append(creature)
                                    elif creature.creature_type == CreatureType.DOLPHIN:
                                        dolphins.append(creature)
                                    elif creature.creature_type == CreatureType.OCTOPUS:
                                        octopuses.append(creature)
                                
                                # Update game state
                                game_state.score = new_game_state.score
                                game_state.creatures_eaten = new_game_state.creatures_eaten
                                game_state.food_consumed = new_game_state.food_consumed
                                game_state.is_night = new_game_state.is_night
                            
                            game_state.toggle_menu()
                        elif selected == "Toggle Day/Night":
                            game_state.toggle_day_night()
                            game_state.toggle_menu()
                        elif selected == "Help":
                            game_state.toggle_menu()
                            game_state.toggle_help()
                        elif selected == "Quit":
                            break
                    elif key == ord('m') or key == 27:  # m or ESC
                        game_state.toggle_menu()
                elif game_state.show_help:
                    # Any key closes help
                    if key == ord('h') or key == 27:  # h or ESC
                        game_state.toggle_help()
                else:
                    # Normal gameplay controls
                    if key == ord('q'):
                        break  # Quit the program
                    elif key == ord('p'):
                        game_state.toggle_pause()
                    elif key == ord('h'):
                        game_state.toggle_help()
                    elif key == ord('m'):
                        game_state.toggle_menu()
                    elif key == ord('n'):
                        game_state.toggle_day_night()
                    elif key == ord('f'):
                        # Add a new fish
                        if len(fishes) < Config.MAX_FISH:
                            fish_type = random.choice(FISH_TYPES)
                            x = random.randint(1, max(1, width - len(fish_type["right"]) - 1))
                            y = random.randint(2, max(2, height - 5))
                            direction = random.choice([-1, 1])
                            color = random.randint(1, len(COLOR_LIST))
                            speed = fish_type["speed"]
                            fishes.append(Fish(fish_type, x, y, direction, color, speed))
                    elif key == ord('o'):
                        # Add a new octopus
                        if len(octopuses) < Config.MAX_OCTOPUSES:
                            x = random.randint(1, max(1, width - 10))
                            y = random.randint(2, max(2, height - 6))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.1
                            octopuses.append(Octopus(x, y, color, speed))
                    elif key == ord('j'):
                        # Add a new jellyfish
                        if len(jellyfishes) < Config.MAX_JELLYFISH:
                            x = random.randint(1, max(1, width - len(AsciiArt.JELLYFISH[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.JELLYFISH) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = random.uniform(0.05, 0.1)
                            jellyfishes.append(Jellyfish(x, y, color, speed))
                    elif key == ord('t'):
                        # Add a new sea turtle
                        if len(sea_turtles) < Config.MAX_SEA_TURTLES:
                            x = random.randint(1, max(1, width - len(AsciiArt.SEA_TURTLE[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.SEA_TURTLE) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.05
                            sea_turtles.append(SeaTurtle(x, y, color, speed))
                    elif key == ord('c'):
                        # Add a new crab
                        if len(crabs) < Config.MAX_CRABS:
                            x = random.randint(1, max(1, width - len(AsciiArt.CRAB[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.CRAB) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.1
                            crabs.append(Crab(x, y, color, speed))
                    elif key == ord('s'):
                        # Add a new school of fish
                        if len(schools) < Config.MAX_SCHOOLS:
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
                        if len(dolphins) < Config.MAX_DOLPHINS:
                            x = random.randint(1, max(1, width - len(AsciiArt.DOLPHIN_FRAMES[0][0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.DOLPHIN_FRAMES[0]) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.1
                            dolphins.append(Dolphin(x, y, color, speed))
                    elif key == ord('h'):
                        # Add a new seahorse
                        if len(seahorses) < Config.MAX_SEAHORSES:
                            x = random.randint(1, max(1, width - len(AsciiArt.SEAHORSE[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.SEAHORSE) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.05
                            seahorses.append(Seahorse(x, y, color, speed))
                    elif key == ord('u'):
                        # Add a new sea urchin
                        if len(sea_urchins) < Config.MAX_SEA_URCHINS:
                            x = random.randint(1, max(1, width - len(AsciiArt.SEA_URCHIN[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.SEA_URCHIN) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            sea_urchins.append(SeaUrchin(x, y, color))
                    elif key == ord('w'):
                        # Add a new shark
                        if len(sharks) < Config.MAX_SHARKS:
                            x = random.randint(1, max(1, width - len(AsciiArt.SHARK[0]) - 1))
                            y = random.randint(2, max(2, height - len(AsciiArt.SHARK) - 1))
                            color = random.randint(1, len(COLOR_LIST))
                            speed = 0.2
                            sharks.append(Shark(x, y, color, speed))
                    elif key == ord(' '):
                        # Feed the aquarium
                        if len(food_list) < Config.MAX_FOOD:
                            # Attempt to place food at the mouse click location if available
                            try:
                                _, mx, my, _, mouse_state = curses.getmouse()
                                if mouse_state & curses.BUTTON1_CLICKED:
                                    if 0 <= mx < width and 0 <= my < height:
                                        x = mx
                                        y = my
                                    else:
                                        x = random.randint(1, max(1, width - 1))
                                        y = random.randint(2, height - 5)
                            except curses.error:
                                # If no mouse support or invalid, spawn at random
                                x = random.randint(1, max(1, width - 1))
                                y = random.randint(2, height - 5)
                            color = len(COLOR_LIST) + 1  # White color for food
                            food_list.append(Food(x, y, color))
                    elif key == ord('+'):
                        # Increase animation speed
                        animation_speed = max(Config.MIN_ANIMATION_SPEED, 
                                              animation_speed - Config.ANIMATION_SPEED_STEP)
                        frame_duration = animation_speed
                    elif key == ord('-'):
                        # Decrease animation speed
                        animation_speed = min(Config.MAX_ANIMATION_SPEED, 
                                              animation_speed + Config.ANIMATION_SPEED_STEP)
                        frame_duration = animation_speed
                    elif key == curses.KEY_MOUSE:
                        # Place food with left-click
                        try:
                            _, mx, my, _, mouse_state = curses.getmouse()
                            if mouse_state & curses.BUTTON1_CLICKED:
                                if len(food_list) < Config.MAX_FOOD:
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
            
            # Update collision manager
            collision_manager = CollisionManager(width, height)

            # Adjust positions of all creatures to stay within the new bounds
            for sea_creature in (fishes + sharks + jellyfishes + sea_turtles + 
                              crabs + seahorses + sea_urchins + dolphins + octopuses):
                sea_creature.x = min(sea_creature.x, max(1, width - sea_creature._width - 1))
                sea_creature.y = min(sea_creature.y, max(2, height - sea_creature._height - 1))

        # Update positions for all marine life
        all_creatures = (fishes + sharks + jellyfishes + sea_turtles + 
                       crabs + seahorses + dolphins + octopuses)
        
        for school in schools:
            school.move(width, height, game_state)

        for creature in all_creatures:
            creature.move(width, height, game_state)

        for bubble in bubbles:
            bubble.move(width, height, game_state)

        for food in food_list:
            food.move(width, height, game_state)
            
        # Handle collisions
        if not game_state.paused:
            handle_collisions(collision_manager, sharks, fishes, game_state)
            handle_feeding(collision_manager, all_creatures, food_list, game_state)

        # Randomly generate new bubbles
        if not game_state.paused and len(bubbles) < Config.MAX_BUBBLES and random.random() < 0.3:
            x = random.randint(1, max(1, width - 1))
            y = height - 2  # Start slightly above the bottom
            char = random.choice(BUBBLE_CHARS)
            color = random.randint(1, len(COLOR_LIST))
            speed = random.uniform(0.1, 0.3)
            bubbles.append(Bubble(x, y, char, color, speed))

        # Remove bubbles that have moved off the screen
        bubbles = [b for b in bubbles if b.alive and b.y > 1]

        # Remove expired food
        food_list = [f for f in food_list if f.alive and not f.is_expired()]

        # Clear screen
        stdscr.erase()
        
        # Apply background color for night mode
        if game_state.is_night:
            for y in range(height):
                for x in range(width):
                    try:
                        stdscr.addstr(y, x, " ", curses.color_pair(100))
                    except curses.error:
                        pass

        # Draw stationary elements
        for seaweed in seaweeds:
            seaweed.draw(stdscr, game_state)
        for coral in corals:
            coral.draw(stdscr, game_state)
        for star in starfish:
            star.draw(stdscr, game_state)
        for chest in treasure_chests:
            chest.draw(stdscr, game_state)
        for rock in rocks:
            rock.draw(stdscr, game_state)
        for shipwreck in shipwrecks:
            shipwreck.draw(stdscr, game_state)
        for sea_urchin in sea_urchins:
            sea_urchin.draw(stdscr, game_state)

        # Draw food
        for food in food_list:
            food.draw(stdscr, game_state)

        # Draw marine life
        for jellyfish in jellyfishes:
            jellyfish.draw(stdscr, game_state)
        for sea_turtle in sea_turtles:
            sea_turtle.draw(stdscr, game_state)
        for crab in crabs:
            crab.draw(stdscr, game_state)
        for seahorse in seahorses:
            seahorse.draw(stdscr, game_state)
        for school in schools:
            school.draw(stdscr, game_state)
        for fish in fishes:
            fish.draw(stdscr, game_state)
        for dolphin in dolphins:
            dolphin.draw(stdscr, game_state)
        for shark in sharks:
            shark.draw(stdscr, game_state)
        for octopus in octopuses:
            octopus.draw(stdscr, game_state)
        for bubble in bubbles:
            bubble.draw(stdscr, game_state)

        # Draw UI elements
        UI.draw_border(stdscr, height, width, game_state)
        UI.draw_status_bar(stdscr, width, game_state)
        UI.draw_instructions(stdscr, height, width, game_state)
        UI.draw_help_screen(stdscr, height, width, game_state)
        UI.draw_menu(stdscr, height, width, game_state)

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
        curses.endwin()
        print(f"An error occurred: {e}")
        sys.exit(1)