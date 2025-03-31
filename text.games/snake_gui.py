#!/usr/bin/env python3
import pygame
import time
import random
import sys
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional, Any

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Game configuration settings"""
    
    # Game speed settings
    BASE_SPEED = 0.11  # Even faster gameplay for more excitement
    SPEED_INCREASE_INTERVAL = 25  # Faster speed increases
    MAX_SPEED_MULTIPLIER = 2.5  # Higher maximum speed for more challenge
    
    # Food settings
    FOOD_BONUS_DURATION = 30  # Seconds until bonus food appears - more frequent bonus food
    FOOD_POINTS = 1
    BONUS_FOOD_POINTS = 5  # Higher value bonus food
    TEMP_FOOD_POINTS = 3  # Higher value for dropped food to encourage scavenging
    MIN_FOOD_COUNT = 15  # Even more food for more action
    
    # Snake settings
    INITIAL_SIZE = 3
    MAX_SNAKES = 25  # Support for up to 25 snakes
    
    # Board settings
    MIN_WIDTH = 70  # Grid width
    MIN_HEIGHT = 30  # Grid height
    CELL_SIZE = 20   # Size of each cell in pixels
    
    # Window settings
    WINDOW_WIDTH = MIN_WIDTH * CELL_SIZE
    WINDOW_HEIGHT = MIN_HEIGHT * CELL_SIZE
    
    # Power-up settings
    POWER_UP_CHANCE = 0.04  # Higher power-up chance for more excitement
    POWER_UP_DURATION = 12  # Shorter duration for better balance
    SPECIAL_POWER_UP_CHANCE = 0.01  # Chance for rare power-ups to appear
    
    # Other settings
    MAX_IDLE_TIME = 25  # Less time before game speeds up - faster pacing
    OBSTACLE_ENABLED = True  # Enable obstacles in the game
    OBSTACLE_COUNT = 5  # Number of obstacles to place on the board
    
    # AI settings
    AI_UPDATE_INTERVAL = 0.02  # More frequent AI updates for more responsive behavior
    EMERGENCY_WALL_CHECK = True  # Always check for walls even between update intervals
    LOOK_AHEAD_STEPS = 8  # Increased look ahead for smarter AI behavior
    OPEN_SPACE_WEIGHT = 2.2  # Reduced space weight to make AIs more willing to enter confined areas
    SURVIVAL_THRESHOLD = 6  # Lower space threshold for survival mode - more aggressive
    TUNNEL_CHECK_ENABLED = True  # Check tunnels for safety
    AGGRESSION_FACTOR = 1.2  # Global aggression factor for AI (higher = more aggressive)
    
    # Performance optimization settings
    OPTIMIZE_FOR_LARGE_GAMES = True  # Enable performance optimizations for large games
    LARGE_GAME_THRESHOLD = 10  # Number of snakes that trigger large game optimizations
    ADAPTIVE_AI = True  # AI adapts to game conditions
    
    # Visual settings
    ENHANCED_VISUALS = True  # Use enhanced visual elements
    SHOW_POWER_UP_EFFECTS = True  # Show visual effects for power-ups
    COLOR_CYCLING = True  # Enable color cycling for visual effects
    
    # PyGame specific settings
    FPS = 60
    BACKGROUND_COLOR = (15, 15, 15)
    GRID_COLOR = (40, 40, 40)
    WALL_COLOR = (80, 80, 80)
    TEXT_COLOR = (255, 255, 255)
    SCORE_FONT_SIZE = 24
    INFO_FONT_SIZE = 18
    HEADER_HEIGHT = 40

# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class Direction(Enum):
    """Snake movement directions"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    
    @staticmethod
    def is_opposite(dir1, dir2):
        """Check if two directions are opposite"""
        return dir1.value[0] == -dir2.value[0] and dir1.value[1] == -dir2.value[1]
    
    @staticmethod
    def from_key(key):
        """Convert pygame key to Direction enum"""
        return {
            pygame.K_UP: Direction.UP,
            pygame.K_DOWN: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT,
            pygame.K_w: Direction.UP,
            pygame.K_s: Direction.DOWN,
            pygame.K_a: Direction.LEFT,
            pygame.K_d: Direction.RIGHT
        }.get(key)
    
    @staticmethod
    def all_directions():
        """Return all four directions"""
        return [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]


class FoodType(Enum):
    """Types of food in the game"""
    NORMAL = 1
    BONUS = 2
    DROPPED = 3
    

class PowerUpType(Enum):
    """Types of power-ups in the game"""
    SPEED_BOOST = 1       # Increases snake speed
    INVINCIBILITY = 2     # Makes snake invincible to collisions
    GHOST = 3             # Allows passing through other snakes
    GROWTH = 4            # Increases length gain from food
    SCORE_MULTIPLIER = 5  # Doubles points from food
    SHRINK = 6            # Reduces snake size
    MAGNETIC = 7          # Attracts nearby food
    FREEZE = 8            # Temporarily freezes other snakes
    TELEPORT = 9          # Allows teleporting through walls
    VISION = 10           # Shows food through walls
    CONFUSION = 11        # Causes other snakes to move randomly
    REVERSE = 12          # Temporarily reverses controls for other snakes
    WARP_DRIVE = 13       # Super speed for a short duration
    PORTAL = 14           # Creates two portals on the map for instant transport
    BLACK_HOLE = 15       # Creates a black hole that consumes other snakes
    TIME_SLOW = 16        # Slows down time for other snakes
    DUPLICATE = 17        # Creates a temporary clone that follows the same path
    INVISIBILITY = 18     # Makes the snake temporarily invisible to other AI snakes
    LASER_BEAM = 19       # Allows shooting in the current direction to clear obstacles
    SHIELD = 20           # Bounces other snakes away on collision
    MAGNET_REPEL = 21     # Pushes other snakes away
    SIZE_SHIFTER = 22     # Randomly grows and shrinks the snake
    FOOD_RAIN = 23        # Causes food to spawn around the snake
    ACID_TRAIL = 24       # Leaves a deadly trail behind
    TIME_WARP = 25        # Temporarily rewinds snake's position if it dies


@dataclass
class Food:
    """Food object representing something snakes can eat"""
    position: Tuple[int, int]
    type: FoodType = FoodType.NORMAL
    points: int = Config.FOOD_POINTS
    color: Tuple[int, int, int] = (255, 255, 0)  # Yellow for normal food
    
    def __init__(self, position, type=FoodType.NORMAL):
        self.position = position
        self.type = type
        
        # Set points based on type
        if type == FoodType.NORMAL:
            self.points = Config.FOOD_POINTS
            self.color = (255, 255, 0)  # Yellow
        elif type == FoodType.BONUS:
            self.points = Config.BONUS_FOOD_POINTS
            self.color = (255, 0, 255)  # Magenta
        elif type == FoodType.DROPPED:
            self.points = Config.TEMP_FOOD_POINTS
            self.color = (0, 255, 255)  # Cyan
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position

    def draw(self, screen):
        x, y = self.position
        # Draw food with slight pulsing effect
        pulse = (math.sin(time.time() * 5) * 0.3 + 0.7)
        size = int(Config.CELL_SIZE * 0.65 * pulse)
        pygame.draw.circle(
            screen,
            self.color,
            (x * Config.CELL_SIZE + Config.CELL_SIZE // 2, 
             y * Config.CELL_SIZE + Config.CELL_SIZE // 2 + Config.HEADER_HEIGHT),
            size
        )


@dataclass
class PowerUp:
    """Power-up object with special effects"""
    position: Tuple[int, int]
    type: PowerUpType
    duration: int
    color: Tuple[int, int, int]
    rarity: str = "common"  # common, uncommon, rare, epic
    
    def __init__(self, position, type=None):
        self.position = position
        
        # Determine if this should be a special/rare power-up
        if type is None:
            if random.random() < Config.SPECIAL_POWER_UP_CHANCE:
                # Select from rare power-ups (indexes 6-13)
                power_up_options = list(PowerUpType)[5:]
                self.type = random.choice(power_up_options)
                self.rarity = "rare"
            else:
                # Select from common power-ups (indexes 0-5)
                power_up_options = list(PowerUpType)[:5]
                self.type = random.choice(power_up_options)
                self.rarity = "common"
        else:
            self.type = type
            # Set rarity based on type
            if self.type.value <= 5:
                self.rarity = "common"
            else:
                self.rarity = "rare"
        
        # Adjust duration based on rarity
        if self.rarity == "rare":
            self.duration = int(Config.POWER_UP_DURATION * 0.7)  # Shorter duration for powerful effects
        else:
            self.duration = Config.POWER_UP_DURATION
        
        # Set appearance based on type
        if self.type == PowerUpType.SPEED_BOOST:
            self.color = (0, 255, 0)  # Green
        elif self.type == PowerUpType.INVINCIBILITY:
            self.color = (255, 215, 0)  # Gold
        elif self.type == PowerUpType.GHOST:
            self.color = (200, 200, 255)  # Light blue
        elif self.type == PowerUpType.GROWTH:
            self.color = (255, 50, 50)  # Red
        elif self.type == PowerUpType.SCORE_MULTIPLIER:
            self.color = (255, 165, 0)  # Orange
        elif self.type == PowerUpType.SHRINK:
            self.color = (100, 100, 255)  # Blue
        elif self.type == PowerUpType.MAGNETIC:
            self.color = (150, 75, 255)  # Purple
        elif self.type == PowerUpType.FREEZE:
            self.color = (0, 255, 255)  # Cyan
        elif self.type == PowerUpType.TELEPORT:
            self.color = (255, 20, 147)  # Pink
        else:
            # Default for other power-ups
            self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position
    
    def draw(self, screen):
        x, y = self.position
        # Draw power-up with pulsing/glowing effect
        pulse = (math.sin(time.time() * 4) * 0.4 + 0.6)
        size = int(Config.CELL_SIZE * 0.5)
        
        # Draw outer glow for rare power-ups
        if self.rarity == "rare":
            glow_size = int(size * 1.5 * pulse)
            glow_color = tuple(min(255, c + 40) for c in self.color)
            pygame.draw.rect(
                screen,
                glow_color,
                (x * Config.CELL_SIZE + Config.CELL_SIZE // 2 - glow_size // 2,
                 y * Config.CELL_SIZE + Config.CELL_SIZE // 2 - glow_size // 2 + Config.HEADER_HEIGHT,
                 glow_size, glow_size),
                border_radius=glow_size // 3
            )
            
        # Draw the power-up
        pygame.draw.rect(
            screen,
            self.color,
            (x * Config.CELL_SIZE + Config.CELL_SIZE // 2 - size // 2,
             y * Config.CELL_SIZE + Config.CELL_SIZE // 2 - size // 2 + Config.HEADER_HEIGHT,
             size, size),
            border_radius=size // 4
        )


class AIStrategy(Enum):
    """Different strategies for AI snakes"""
    AGGRESSIVE = 1       # Focuses on getting food quickly
    CAUTIOUS = 2         # Prefers safe spaces over food
    OPPORTUNISTIC = 3    # Balanced approach
    DEFENSIVE = 4        # Avoids other snakes
    HUNTER = 5           # Targets other snake heads
    SCAVENGER = 6        # Prefers dropped food from dead snakes
    TERRITORIAL = 7      # Controls and defends a specific area
    BERSERKER = 8        # Super aggressive, targets food and other snakes with minimal safety checks
    INTERCEPTOR = 9      # Tries to cut off other snakes' paths to food
    POWERUP_SEEKER = 10  # Prioritizes power-ups over food


# =============================================================================
# OBSTACLE CLASS
# =============================================================================

class ObstacleType(Enum):
    """Types of obstacles in the game"""
    WALL = 1        # Solid wall that cannot be passed
    SPIKES = 2      # Damaging obstacle that kills snakes
    WORMHOLE = 3    # Teleports snakes to another location
    SWAMP = 4       # Slows down snakes passing through
    ENERGY_FIELD = 5 # Speeds up snakes passing through

@dataclass
class Obstacle:
    """Obstacle object that affects snake movement"""
    position: Tuple[int, int]
    type: ObstacleType
    color: Tuple[int, int, int]
    linked_position: Optional[Tuple[int, int]] = None  # For wormholes
    
    def __init__(self, position, type=None):
        self.position = position
        self.type = type or random.choice([t for t in ObstacleType if t != ObstacleType.WORMHOLE])
        
        # Set appearance based on type
        if self.type == ObstacleType.WALL:
            self.color = (100, 100, 100)  # Gray
        elif self.type == ObstacleType.SPIKES:
            self.color = (255, 0, 0)  # Red
        elif self.type == ObstacleType.WORMHOLE:
            self.color = (128, 0, 128)  # Purple
        elif self.type == ObstacleType.SWAMP:
            self.color = (0, 100, 0)  # Dark green
        elif self.type == ObstacleType.ENERGY_FIELD:
            self.color = (0, 128, 255)  # Light blue
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position
    
    def get_effect(self):
        """Get the obstacle's effect on a snake"""
        if self.type == ObstacleType.WALL:
            return {"deadly": True}
        elif self.type == ObstacleType.SPIKES:
            return {"deadly": True}
        elif self.type == ObstacleType.WORMHOLE:
            return {"teleport": self.linked_position}
        elif self.type == ObstacleType.SWAMP:
            return {"speed_multiplier": 0.5}
        elif self.type == ObstacleType.ENERGY_FIELD:
            return {"speed_multiplier": 1.5}
        return {}
    
    def draw(self, screen):
        x, y = self.position
        rect = pygame.Rect(
            x * Config.CELL_SIZE, 
            y * Config.CELL_SIZE + Config.HEADER_HEIGHT,
            Config.CELL_SIZE, 
            Config.CELL_SIZE
        )
        
        if self.type == ObstacleType.WALL:
            pygame.draw.rect(screen, self.color, rect)
        elif self.type == ObstacleType.SPIKES:
            pygame.draw.rect(screen, self.color, rect)
            # Draw spikes
            for i in range(3):
                pygame.draw.line(
                    screen,
                    (255, 100, 100),
                    (rect.x + i * rect.width // 3 + rect.width // 6, rect.y + rect.height // 2),
                    (rect.x + i * rect.width // 3 + rect.width // 6, rect.y + rect.height // 4),
                    3
                )
        elif self.type == ObstacleType.WORMHOLE:
            # Draw a pulsing circular wormhole
            pulse = (math.sin(time.time() * 3) * 0.2 + 0.8)
            size = int(Config.CELL_SIZE * 0.7 * pulse)
            pygame.draw.circle(
                screen,
                self.color,
                (rect.centerx, rect.centery),
                size
            )
            # Draw inner circle
            pygame.draw.circle(
                screen,
                (200, 200, 255),
                (rect.centerx, rect.centery),
                size // 2
            )
        elif self.type == ObstacleType.SWAMP:
            pygame.draw.rect(screen, self.color, rect)
            # Draw swamp waves
            for i in range(3):
                y_offset = math.sin(time.time() * 2 + i) * 3
                pygame.draw.line(
                    screen,
                    (0, 200, 100),
                    (rect.x, rect.y + i * rect.height // 3 + rect.height // 6 + y_offset),
                    (rect.x + rect.width, rect.y + i * rect.height // 3 + rect.height // 6 + y_offset),
                    2
                )
        elif self.type == ObstacleType.ENERGY_FIELD:
            pygame.draw.rect(screen, self.color, rect, border_radius=5)
            # Draw energy lines
            for i in range(3):
                offset = (time.time() * 20 + i * 10) % rect.width
                pygame.draw.line(
                    screen,
                    (100, 200, 255),
                    (rect.x + offset, rect.y),
                    (rect.x + offset, rect.y + rect.height),
                    2
                )


# =============================================================================
# SNAKE CLASS
# =============================================================================

class Snake:
    """Snake class representing a player or AI-controlled snake"""
    
    def __init__(self, body, direction, id, strategy=None, is_human=False):
        self.body = list(body)  # List of (x, y) coordinates, head is first
        self.body_set = set(body)  # Set for faster collision checks
        self.direction = direction
        self.prev_direction = direction
        self.id = id
        self.is_human = is_human
        self.strategy = strategy or random.choice(list(AIStrategy))
        self.alive = True
        self.score = 0
        self.death_order = None
        self.current_target = None
        self.last_ai_update = 0
        self.power_ups = {}  # Dict of active power-ups with end times
        self.consecutive_moves = 0  # Count of moves in same direction
        self.territory_center = None  # For territorial strategy
        
        # Visual properties (color is based on ID)
        self.color = self.get_color_from_id(id)
        self.head_color = self.get_head_color()
    
    def get_color_from_id(self, id):
        """Generate a color based on the snake ID"""
        base_colors = [
            (0, 255, 0),     # Green (player)
            (255, 100, 0),   # Orange
            (0, 100, 255),   # Blue
            (255, 0, 100),   # Pink
            (100, 255, 0),   # Lime
            (0, 255, 255),   # Cyan
            (255, 255, 0),   # Yellow
            (255, 0, 255),   # Magenta
            (100, 100, 255), # Light blue
            (255, 100, 100)  # Light red
        ]
        
        if self.is_human:
            return base_colors[0]  # Player is always green
        
        # For AI snakes, use modulo to cycle through colors
        return base_colors[id % len(base_colors)]
    
    def get_head_color(self):
        """Get a slightly brighter color for the snake's head"""
        r, g, b = self.color
        return (min(255, r + 50), min(255, g + 50), min(255, b + 50))

    def next_head(self, new_dir=None):
        """Calculate the position of the next head"""
        if not self.body:  # Check if body is empty
            return None
        if new_dir is None:
            new_dir = self.direction
        head = self.body[0]
        dx, dy = new_dir.value
        return (head[0] + dx, head[1] + dy)
    
    def move(self, foods, other_snakes_positions, power_ups, game_state):
        """Move the snake by updating its direction and position"""
        # Check if snake has a body
        if not self.body:
            return None
            
        # Update direction for AI snakes
        if not self.is_human:
            current_time = time.time()
            
            # Check if we're about to hit a wall
            next_head = self.next_head()
            if next_head is None:
                return None
            x, y = next_head
            
            # Emergency wall avoidance
            if Config.EMERGENCY_WALL_CHECK and (
                x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1 or
                next_head in other_snakes_positions or next_head in self.body[1:]):
                # About to hit something, find a safe direction immediately
                safe_directions = []
                
                # Evaluate each direction
                direction_scores = []
                for direction in Direction.all_directions():
                    if Direction.is_opposite(direction, self.direction):
                        continue
                    
                    test_pos = (self.body[0][0] + direction.value[0], self.body[0][1] + direction.value[1])
                    if not self.is_safe(test_pos, other_snakes_positions | set(self.body[1:]), game_state):
                        continue
                    
                    space_score = self.free_space(test_pos, other_snakes_positions | set(self.body[1:]),
                                               foods, power_ups, game_state)
                    
                    direction_scores.append((direction, space_score))
                    safe_directions.append(direction)
                
                # Choose direction with most space
                if direction_scores:
                    best_direction = max(direction_scores, key=lambda x: x[1])[0]
                    self.direction = best_direction
                elif safe_directions:
                    self.direction = random.choice(safe_directions)
                    
            # Regular AI update on the normal interval
            if current_time - self.last_ai_update > Config.AI_UPDATE_INTERVAL:
                self.choose_direction(foods, other_snakes_positions, power_ups, game_state)
                self.last_ai_update = current_time
        
        # Get the new head position
        new_head = self.next_head()
        
        # Check for obstacles before inserting
        for obstacle in game_state.obstacles:
            if new_head == obstacle.position:
                effect = obstacle.get_effect()
                if "teleport" in effect and effect["teleport"]:
                    return self.body[0]
        
        # Add the new head
        self.body.insert(0, new_head)
        self.body_set.add(new_head)
        
        # Ensure body_set and body are in sync
        if len(self.body_set) != len(set(self.body)):
            self.body_set = set(self.body)
        
        return new_head
    
    def remove_tail(self):
        """Remove the snake's tail (last segment) safely"""
        if not self.body:
            return
            
        tail = self.body.pop()
        
        # Check if the tail position exists elsewhere in the body
        tail_also_in_body = tail in self.body
        
        # Only remove from body_set if this is the only occurrence of this position
        if not tail_also_in_body and tail in self.body_set:
            self.body_set.remove(tail)
        elif not tail_also_in_body:
            # Resync the body_set
            self.body_set = set(self.body)
    
    def gets_longer(self, food_type):
        """Snake gets longer based on the food type"""
        if not self.body:
            return
            
        length_gain = 0
        if food_type == FoodType.BONUS:
            length_gain = 3
        elif PowerUpType.GROWTH in self.power_ups:
            length_gain = 2
        else:
            length_gain = 1
        
        # Add extra segments at the tail
        tail = self.body[-1]
        for _ in range(length_gain - 1):
            self.body.append(tail)
            self.body_set.add(tail)
    
    def add_power_up(self, power_up_type):
        """Add a power-up to the snake"""
        end_time = time.time() + Config.POWER_UP_DURATION
        self.power_ups[power_up_type] = end_time
        
        # Apply immediate effects for certain power-ups
        if power_up_type == PowerUpType.SHRINK:
            if not self.body:
                return
                
            # Shrink the snake by removing up to 30% of its length (minimum 3 segments)
            shrink_amount = max(0, min(len(self.body) - 3, int(len(self.body) * 0.3)))
            for _ in range(shrink_amount):
                if len(self.body) > 3:  # Maintain minimum size
                    self.remove_tail()
        
        # Special power-up effects are handled in game_state functions
    
    def update_power_ups(self):
        """Update active power-ups and remove expired ones"""
        current_time = time.time()
        expired = [p for p, t in self.power_ups.items() if current_time > t]
        for p in expired:
            # Special effects when power-ups expire
            if p == PowerUpType.WARP_DRIVE:
                # Apply a brief slowdown after warp drive expires (cooldown)
                self.add_power_up(PowerUpType.SPEED_BOOST)  # Override with 1.0x speed
            
            # Remove the expired power-up
            del self.power_ups[p]
    
    def has_power_up(self, power_up_type):
        """Check if snake has a specific power-up active"""
        return power_up_type in self.power_ups
    
    def is_frozen(self):
        """Check if snake is currently frozen"""
        return self.has_power_up(PowerUpType.FREEZE)
        
    def is_confused(self):
        """Check if snake is currently confused"""
        return self.has_power_up(PowerUpType.CONFUSION)
        
    def is_reversed(self):
        """Check if snake's controls are currently reversed"""
        return self.has_power_up(PowerUpType.REVERSE)
        
    def has_shield(self):
        """Check if snake has an active shield"""
        return self.has_power_up(PowerUpType.SHIELD)
        
    def has_time_warp(self):
        """Check if snake has time warp ability"""
        return self.has_power_up(PowerUpType.TIME_WARP)
    
    def get_effective_speed(self, base_speed):
        """Calculate effective movement speed based on active power-ups"""
        speed_multiplier = 1.0
        
        if self.has_power_up(PowerUpType.SPEED_BOOST):
            speed_multiplier *= 1.5
        
        if self.has_power_up(PowerUpType.WARP_DRIVE):
            speed_multiplier *= 3.0
        
        return base_speed * speed_multiplier
    
    def is_safe(self, pos, obstacles, game_state):
        """Check if position is safe (not a wall or other snake)"""
        x, y = pos
        
        # Check for wall collisions
        if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
            return False
        
        # Check for snake body collisions
        if pos in obstacles:
            return False
        
        return True
    
    def free_space(self, pos, obstacles, foods, power_ups, game_state):
        """Calculate free space around a position (floodfill algorithm)"""
        # Simplified version for PyGame implementation
        x, y = pos
        if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
            return 0
        
        # Quick estimate for performance
        free_neighbors = 0
        exit_paths = 0
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
            nx, ny = x + dx, y + dy
            if (nx <= 0 or nx >= game_state.width - 1 or 
                ny <= 0 or ny >= game_state.height - 1):
                continue
            if (nx, ny) not in obstacles:
                free_neighbors += 1
                # Check for exit paths
                has_further_space = False
                for nx2, ny2 in [(nx+1, ny), (nx-1, ny), (nx, ny+1), (nx, ny-1)]:
                    if (nx2 <= 0 or nx2 >= game_state.width - 1 or 
                        ny2 <= 0 or ny2 >= game_state.height - 1):
                        continue
                    if (nx2, ny2) not in obstacles and (nx2, ny2) != pos:
                        has_further_space = True
                        break
                if has_further_space:
                    exit_paths += 1
        
        # Quick estimate based on free neighbors and exit paths
        return free_neighbors * 15 + exit_paths * 10
    
    def choose_direction(self, foods, other_snakes_positions, power_ups, game_state):
        """AI logic to choose the next direction"""
        if not self.body:
            return
        
        head = self.body[0]
        best_direction = self.direction
        best_score = float('-inf')
        
        # For each possible direction
        for direction in Direction.all_directions():
            # Skip opposite direction (can't go backwards)
            if Direction.is_opposite(direction, self.direction):
                continue
            
            # Calculate new position if we move in this direction
            x, y = head
            dx, dy = direction.value
            new_pos = (x + dx, y + dy)
            
            # Skip if not safe
            if not self.is_safe(new_pos, other_snakes_positions | set(self.body[1:]), game_state):
                continue
            
            # Basic score based on strategy
            score = 0
            
            # Calculate distance to closest food
            min_food_distance = float('inf')
            for food in foods:
                dist = abs(new_pos[0] - food.position[0]) + abs(new_pos[1] - food.position[1])
                if dist < min_food_distance:
                    min_food_distance = dist
            
            # Calculate distance to closest power-up
            min_powerup_distance = float('inf')
            for powerup in power_ups:
                dist = abs(new_pos[0] - powerup.position[0]) + abs(new_pos[1] - powerup.position[1])
                if dist < min_powerup_distance:
                    min_powerup_distance = dist
            
            # Calculate free space
            space_score = self.free_space(new_pos, other_snakes_positions | set(self.body[1:]), 
                                           foods, power_ups, game_state)
            
            # Different strategies prioritize different factors
            if self.strategy == AIStrategy.AGGRESSIVE:
                # Aggressively seek food
                if min_food_distance > 0:
                    score = 1000 / min_food_distance + space_score * 0.5
                else:
                    score = 2000  # Max priority if food is right next to us
                    
            elif self.strategy == AIStrategy.CAUTIOUS:
                # Prioritize open space over food
                score = space_score * 2 + (500 / min_food_distance if min_food_distance > 0 else 1000)
                
            elif self.strategy == AIStrategy.OPPORTUNISTIC:
                # Balance food and space
                score = space_score + (800 / min_food_distance if min_food_distance > 0 else 1600)
                
            elif self.strategy == AIStrategy.POWERUP_SEEKER:
                # Prioritize power-ups
                if min_powerup_distance < float('inf'):
                    score = 1500 / min_powerup_distance + space_score * 0.3
                else:
                    # Fall back to seeking food if no power-ups
                    score = 500 / min_food_distance if min_food_distance > 0 else 1000
            
            else:
                # Default balanced approach
                food_score = 700 / min_food_distance if min_food_distance > 0 else 1400
                score = food_score + space_score
            
            # Update best direction if better score
            if score > best_score:
                best_score = score
                best_direction = direction
        
        # If we found a valid direction, use it
        if best_score > float('-inf'):
            self.direction = best_direction
        else:
            # No good direction found, try any safe direction
            safe_directions = []
            for direction in Direction.all_directions():
                if Direction.is_opposite(direction, self.direction):
                    continue
                    
                new_pos = (head[0] + direction.value[0], head[1] + direction.value[1])
                if self.is_safe(new_pos, other_snakes_positions | set(self.body[1:]), game_state):
                    safe_directions.append(direction)
            
            if safe_directions:
                self.direction = random.choice(safe_directions)
    
    def draw(self, screen):
        """Draw the snake on the screen"""
        if not self.body or not self.alive:
            return
        
        # Draw snake body
        for i, segment in enumerate(self.body):
            x, y = segment
            
            # Calculate segment color with a gradient from head to tail
            if i == 0:  # Head
                color = self.head_color
            else:  # Body
                # Apply effects if snake has power-ups
                if self.has_power_up(PowerUpType.INVINCIBILITY):
                    # Pulsing golden effect for invincibility
                    pulse = (math.sin(time.time() * 10) * 0.5 + 0.5)
                    r, g, b = self.color
                    color = (int(r + (255 - r) * pulse * 0.7), 
                             int(g + (215 - g) * pulse * 0.7), 
                             int(b + (0 - b) * pulse * 0.7))
                elif self.has_power_up(PowerUpType.GHOST):
                    # Translucent effect for ghost
                    r, g, b = self.color
                    alpha = 128 + int(math.sin(time.time() * 5) * 64)
                    color = (r, g, b)
                    # Note: alpha is handled differently in drawing
                else:
                    # Normal color with slight gradient toward tail
                    r, g, b = self.color
                    fade = max(0.5, 1 - i / len(self.body) * 0.5)
                    color = (int(r * fade), int(g * fade), int(b * fade))
            
            # Draw segment with slight gap between segments
            size = int(Config.CELL_SIZE * 0.85)
            offset = (Config.CELL_SIZE - size) // 2
            
            pygame.draw.rect(
                screen,
                color,
                (x * Config.CELL_SIZE + offset, 
                 y * Config.CELL_SIZE + offset + Config.HEADER_HEIGHT,
                 size, size),
                border_radius=5 if i == 0 else 3  # Rounded corners, more for head
            )
            
            # Draw eyes on the head
            if i == 0:
                # Calculate eye positions based on direction
                eye_size = Config.CELL_SIZE // 8
                if self.direction == Direction.UP:
                    left_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE // 3, 
                                y * Config.CELL_SIZE + Config.CELL_SIZE // 3 + Config.HEADER_HEIGHT)
                    right_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3, 
                                 y * Config.CELL_SIZE + Config.CELL_SIZE // 3 + Config.HEADER_HEIGHT)
                elif self.direction == Direction.DOWN:
                    left_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE // 3, 
                                y * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3 + Config.HEADER_HEIGHT)
                    right_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3, 
                                 y * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3 + Config.HEADER_HEIGHT)
                elif self.direction == Direction.LEFT:
                    left_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE // 3, 
                                y * Config.CELL_SIZE + Config.CELL_SIZE // 3 + Config.HEADER_HEIGHT)
                    right_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE // 3, 
                                 y * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3 + Config.HEADER_HEIGHT)
                else:  # RIGHT
                    left_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3, 
                                y * Config.CELL_SIZE + Config.CELL_SIZE // 3 + Config.HEADER_HEIGHT)
                    right_eye = (x * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3, 
                                 y * Config.CELL_SIZE + Config.CELL_SIZE * 2 // 3 + Config.HEADER_HEIGHT)
                
                pygame.draw.circle(screen, (255, 255, 255), left_eye, eye_size)
                pygame.draw.circle(screen, (255, 255, 255), right_eye, eye_size)
                pygame.draw.circle(screen, (0, 0, 0), left_eye, eye_size // 2)
                pygame.draw.circle(screen, (0, 0, 0), right_eye, eye_size // 2)


# =============================================================================
# GAME STATE CLASS
# =============================================================================

class GameState:
    """Game state class managing the overall game state"""
    
    def __init__(self, width=None, height=None, ai_count=5):
        """Initialize the game state with snakes, food, etc."""
        self.width = width or Config.MIN_WIDTH
        self.height = height or Config.MIN_HEIGHT
        self.snakes = []
        self.foods = []
        self.power_ups = []
        self.obstacles = []
        self.game_over = False
        self.winner = None
        self.paused = False
        self.tick_count = 0
        self.last_food_spawn = 0
        self.last_bonus_food_spawn = 0
        self.last_powerup_spawn = 0
        self.current_speed = Config.BASE_SPEED
        self.speed_multiplier = 1.0
        self.human_snake_id = 0
        self.ai_count = ai_count
        # Initialize game with a setup method that can also be used to reset the game
        self.initialize_game()
    
    def initialize_game(self):
        """Initialize the game state with snakes, food, and obstacles"""
        self.snakes = []
        self.foods = []
        self.power_ups = []
        self.obstacles = []
        self.game_over = False
        self.winner = None
        self.paused = False
        self.tick_count = 0
        self.last_food_spawn = time.time()
        self.last_bonus_food_spawn = time.time()
        self.last_powerup_spawn = time.time()
        self.current_speed = Config.BASE_SPEED
        self.speed_multiplier = 1.0
        
        # Create player snake
        player_pos = (self.width // 4, self.height // 2)
        player_body = [(player_pos[0], player_pos[1]), 
                       (player_pos[0] - 1, player_pos[1]),
                       (player_pos[0] - 2, player_pos[1])]
        player_snake = Snake(player_body, Direction.RIGHT, self.human_snake_id, is_human=True)
        self.snakes.append(player_snake)
        
        # Create AI snakes
        for i in range(1, self.ai_count + 1):
            # Place AI snakes at different corners/areas of the board
            if i % 4 == 0:
                pos = (self.width // 4, self.height // 4)
                direction = Direction.DOWN
            elif i % 4 == 1:
                pos = (self.width * 3 // 4, self.height // 4)
                direction = Direction.DOWN
            elif i % 4 == 2:
                pos = (self.width // 4, self.height * 3 // 4)
                direction = Direction.UP
            else:
                pos = (self.width * 3 // 4, self.height * 3 // 4)
                direction = Direction.UP
            
            # Offset to avoid immediate collisions
            pos = (pos[0] + i % 3, pos[1] + i % 2)
            
            # Create snake body
            body = [(pos[0], pos[1]), (pos[0] - 1, pos[1]), (pos[0] - 2, pos[1])]
            snake = Snake(body, direction, i, is_human=False)
            self.snakes.append(snake)
        
        # Generate initial food
        for _ in range(Config.MIN_FOOD_COUNT):
            self.spawn_food()
        
        # Generate obstacles
        if Config.OBSTACLE_ENABLED:
            self.generate_obstacles()
    
    def generate_obstacles(self):
        """Generate obstacles on the board"""
        obstacle_count = Config.OBSTACLE_COUNT
        
        # Create wall obstacles around the board
        self.obstacles = []
        
        # Create internal obstacles
        for _ in range(obstacle_count):
            while True:
                x = random.randint(2, self.width - 3)
                y = random.randint(2, self.height - 3)
                pos = (x, y)
                
                # Check if position is free of snakes and other obstacles
                if (not any(pos in snake.body for snake in self.snakes) and
                    not any(pos == obstacle.position for obstacle in self.obstacles)):
                    obstacle_type = random.choice(list(ObstacleType))
                    new_obstacle = Obstacle(pos, obstacle_type)
                    
                    # If it's a wormhole, create a linked wormhole
                    if obstacle_type == ObstacleType.WORMHOLE:
                        # Find a position for the linked wormhole
                        linked_pos = None
                        for _ in range(20):  # Try 20 times to find a valid position
                            tx = random.randint(2, self.width - 3)
                            ty = random.randint(2, self.height - 3)
                            test_pos = (tx, ty)
                            
                            if (test_pos != pos and
                                not any(test_pos in snake.body for snake in self.snakes) and
                                not any(test_pos == obstacle.position for obstacle in self.obstacles)):
                                linked_pos = test_pos
                                break
                        
                        if linked_pos:
                            new_obstacle.linked_position = linked_pos
                            linked_obstacle = Obstacle(linked_pos, ObstacleType.WORMHOLE)
                            linked_obstacle.linked_position = pos
                            self.obstacles.append(new_obstacle)
                            self.obstacles.append(linked_obstacle)
                        else:
                            # Couldn't find a valid linked position, make it a regular wall
                            new_obstacle.type = ObstacleType.WALL
                            self.obstacles.append(new_obstacle)
                    else:
                        self.obstacles.append(new_obstacle)
                    break
    
    def spawn_food(self, food_type=FoodType.NORMAL):
        """Spawn food at a random empty position"""
        # Calculate all occupied positions
        occupied_positions = set()
        for snake in self.snakes:
            occupied_positions.update(snake.body)
        
        for food in self.foods:
            occupied_positions.add(food.position)
            
        for power_up in self.power_ups:
            occupied_positions.add(power_up.position)
            
        for obstacle in self.obstacles:
            occupied_positions.add(obstacle.position)
        
        # Find a random empty position
        for _ in range(100):  # Try 100 times to find a valid position
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            pos = (x, y)
            
            if pos not in occupied_positions:
                new_food = Food(pos, food_type)
                self.foods.append(new_food)
                return True
        
        return False  # Couldn't find a valid position
    
    def spawn_power_up(self):
        """Spawn a power-up at a random empty position"""
        # Calculate all occupied positions
        occupied_positions = set()
        for snake in self.snakes:
            occupied_positions.update(snake.body)
        
        for food in self.foods:
            occupied_positions.add(food.position)
            
        for power_up in self.power_ups:
            occupied_positions.add(power_up.position)
            
        for obstacle in self.obstacles:
            occupied_positions.add(obstacle.position)
        
        # Find a random empty position
        for _ in range(100):  # Try 100 times to find a valid position
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            pos = (x, y)
            
            if pos not in occupied_positions:
                new_power_up = PowerUp(pos)
                self.power_ups.append(new_power_up)
                return True
        
        return False  # Couldn't find a valid position
    
    def check_food_collision(self, snake, head_pos):
        """Check if a snake has collided with food"""
        for i, food in enumerate(self.foods):
            if head_pos == food.position:
                # Snake eats food
                snake.score += food.points
                
                # Apply score multiplier if active
                if snake.has_power_up(PowerUpType.SCORE_MULTIPLIER):
                    snake.score += food.points  # Double points
                
                # Snake gets longer
                snake.gets_longer(food.type)
                
                # Remove the food
                self.foods.pop(i)
                
                return True
        return False
    
    def check_power_up_collision(self, snake, head_pos):
        """Check if a snake has collided with a power-up"""
        for i, power_up in enumerate(self.power_ups):
            if head_pos == power_up.position:
                # Snake gets the power-up
                snake.add_power_up(power_up.type)
                
                # Remove the power-up
                self.power_ups.pop(i)
                
                return True
        return False
    
    def check_obstacle_collision(self, snake, head_pos):
        """Check if a snake has collided with an obstacle"""
        for obstacle in self.obstacles:
            if head_pos == obstacle.position:
                effect = obstacle.get_effect()
                
                # Handle teleportation
                if "teleport" in effect and effect["teleport"]:
                    # Teleport the snake's head to the linked position
                    snake.body[0] = effect["teleport"]
                    snake.body_set.remove(head_pos)
                    snake.body_set.add(effect["teleport"])
                    return False  # Not a deadly collision
                
                # Handle speed modifiers
                if "speed_multiplier" in effect:
                    # Apply temporary speed effect
                    pass
                
                # Check if obstacle is deadly
                if "deadly" in effect and effect["deadly"]:
                    # Only kill if snake doesn't have invincibility
                    if not snake.has_power_up(PowerUpType.INVINCIBILITY):
                        return True  # Deadly collision
                
                return False  # Non-deadly collision
                
        return False  # No collision
    
    def check_snake_collision(self, snake, head_pos):
        """Check if a snake has collided with another snake or itself"""
        # Check collision with own body (except if ghost power-up is active)
        if head_pos in snake.body[1:]:
            if snake.has_power_up(PowerUpType.GHOST) or snake.has_power_up(PowerUpType.INVINCIBILITY):
                return False
            return True
        
        # Check collision with other snakes
        for other_snake in self.snakes:
            if other_snake.id == snake.id or not other_snake.alive:
                continue
                
            # Check if head collided with other snake's body
            if head_pos in other_snake.body:
                # If snake has invincibility or ghost, it passes through
                if snake.has_power_up(PowerUpType.INVINCIBILITY) or snake.has_power_up(PowerUpType.GHOST):
                    return False
                    
                # If snake has shield, bounce instead of dying
                if snake.has_power_up(PowerUpType.SHIELD):
                    # Reverse direction
                    if snake.direction == Direction.UP:
                        snake.direction = Direction.DOWN
                    elif snake.direction == Direction.DOWN:
                        snake.direction = Direction.UP
                    elif snake.direction == Direction.LEFT:
                        snake.direction = Direction.RIGHT
                    elif snake.direction == Direction.RIGHT:
                        snake.direction = Direction.LEFT
                    return False
                
                return True
        
        return False
    
    def check_wall_collision(self, snake, head_pos):
        """Check if a snake has collided with a wall"""
        x, y = head_pos
        
        # Check if position is outside board boundaries
        if x <= 0 or x >= self.width - 1 or y <= 0 or y >= self.height - 1:
            # If snake has teleport power-up, wrap around
            if snake.has_power_up(PowerUpType.TELEPORT):
                new_x = x
                new_y = y
                
                if x <= 0:
                    new_x = self.width - 2
                elif x >= self.width - 1:
                    new_x = 1
                
                if y <= 0:
                    new_y = self.height - 2
                elif y >= self.height - 1:
                    new_y = 1
                
                # Update snake's head position
                snake.body[0] = (new_x, new_y)
                return False
            
            # If snake has invincibility, it doesn't die from wall collisions
            if snake.has_power_up(PowerUpType.INVINCIBILITY):
                return False
                
            return True
        
        return False
    
    def kill_snake(self, snake):
        """Handle a snake's death"""
        if not snake.alive:
            return
            
        snake.alive = False
        
        # Determine death order for scoring
        death_order = sum(1 for s in self.snakes if not s.alive)
        snake.death_order = death_order
        
        # Drop food from dead snake's body parts
        for segment in snake.body[::3]:  # Drop food from every third segment
            # 50% chance to drop food
            if random.random() < 0.5:
                # Only drop if position is free
                if not any(segment == food.position for food in self.foods):
                    dropped_food = Food(segment, FoodType.DROPPED)
                    self.foods.append(dropped_food)
    
    def update(self):
        """Update the game state for one tick"""
        if self.paused or self.game_over:
            return
            
        current_time = time.time()
        
        # Spawn food if needed
        if len(self.foods) < Config.MIN_FOOD_COUNT:
            self.spawn_food()
        
        # Spawn bonus food periodically
        if current_time - self.last_bonus_food_spawn > Config.FOOD_BONUS_DURATION:
            self.spawn_food(FoodType.BONUS)
            self.last_bonus_food_spawn = current_time
        
        # Spawn power-ups with a random chance
        if random.random() < Config.POWER_UP_CHANCE and current_time - self.last_powerup_spawn > 5:
            self.spawn_power_up()
            self.last_powerup_spawn = current_time
        
        # Collect all snake body positions for collision detection
        all_snake_positions = set()
        for snake in self.snakes:
            if snake.alive:
                all_snake_positions.update(snake.body)
        
        # Update each snake
        for snake in self.snakes:
            if not snake.alive:
                continue
                
            # Update active power-ups
            snake.update_power_ups()
            
            # Skip frozen snakes
            if snake.is_frozen():
                continue
            
            # Move the snake
            other_snake_positions = all_snake_positions - snake.body_set
            head_pos = snake.move(self.foods, other_snake_positions, self.power_ups, self)
            
            if head_pos is None:
                continue
            
            # Check for food collision
            self.check_food_collision(snake, head_pos)
            
            # Check for power-up collision
            self.check_power_up_collision(snake, head_pos)
            
            # Check for obstacle collision
            if self.check_obstacle_collision(snake, head_pos):
                self.kill_snake(snake)
                continue
            
            # Check for wall collision
            if self.check_wall_collision(snake, head_pos):
                self.kill_snake(snake)
                continue
            
            # Check for snake collision
            if self.check_snake_collision(snake, head_pos):
                self.kill_snake(snake)
                continue
            
            # If all checks passed, remove tail unless food was eaten (handled in check_food_collision)
            snake.remove_tail()
        
        # Check game over conditions
        alive_snakes = [snake for snake in self.snakes if snake.alive]
        
        if not alive_snakes:
            self.game_over = True
            self.winner = None  # No winner, everyone died
        elif len(alive_snakes) == 1:
            self.game_over = True
            self.winner = alive_snakes[0]
        
        # Update game speed based on time
        if self.tick_count % Config.SPEED_INCREASE_INTERVAL == 0:
            self.speed_multiplier = min(self.speed_multiplier * 1.05, Config.MAX_SPEED_MULTIPLIER)
        
        self.tick_count += 1
    
    def draw(self, screen, font, fps):
        """Draw the game state to the screen"""
        # Clear the screen
        screen.fill(Config.BACKGROUND_COLOR)
        
        # Draw header with scores
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, Config.WINDOW_WIDTH, Config.HEADER_HEIGHT))
        
        # Draw FPS
        fps_text = font.render(f"FPS: {int(fps)}", True, Config.TEXT_COLOR)
        screen.blit(fps_text, (10, 10))
        
        # Draw player score
        player_snake = next((s for s in self.snakes if s.is_human), None)
        if player_snake:
            score_text = font.render(f"Score: {player_snake.score}", True, Config.TEXT_COLOR)
            screen.blit(score_text, (Config.WINDOW_WIDTH // 2 - score_text.get_width() // 2, 10))
        
        # Draw active power-ups for the player
        if player_snake and player_snake.power_ups:
            power_up_text = "Power-ups: "
            for power_up in player_snake.power_ups:
                power_up_text += f"{power_up.name.replace('_', ' ')} "
            pu_text = font.render(power_up_text, True, Config.TEXT_COLOR)
            screen.blit(pu_text, (Config.WINDOW_WIDTH - pu_text.get_width() - 10, 10))
        
        # Draw grid
        for x in range(0, Config.WINDOW_WIDTH, Config.CELL_SIZE):
            pygame.draw.line(screen, Config.GRID_COLOR, (x, Config.HEADER_HEIGHT), 
                            (x, Config.WINDOW_HEIGHT + Config.HEADER_HEIGHT))
        for y in range(Config.HEADER_HEIGHT, Config.WINDOW_HEIGHT + Config.HEADER_HEIGHT, Config.CELL_SIZE):
            pygame.draw.line(screen, Config.GRID_COLOR, (0, y), 
                            (Config.WINDOW_WIDTH, y))
        
        # Draw walls around the border
        pygame.draw.rect(screen, Config.WALL_COLOR, 
                        (0, Config.HEADER_HEIGHT, Config.WINDOW_WIDTH, Config.CELL_SIZE), 1)
        pygame.draw.rect(screen, Config.WALL_COLOR, 
                        (0, Config.WINDOW_HEIGHT - Config.CELL_SIZE + Config.HEADER_HEIGHT, 
                         Config.WINDOW_WIDTH, Config.CELL_SIZE), 1)
        pygame.draw.rect(screen, Config.WALL_COLOR, 
                        (0, Config.HEADER_HEIGHT, Config.CELL_SIZE, Config.WINDOW_HEIGHT), 1)
        pygame.draw.rect(screen, Config.WALL_COLOR, 
                        (Config.WINDOW_WIDTH - Config.CELL_SIZE, Config.HEADER_HEIGHT, 
                         Config.CELL_SIZE, Config.WINDOW_HEIGHT), 1)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(screen)
        
        # Draw food
        for food in self.foods:
            food.draw(screen)
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(screen)
        
        # Draw snakes (with AI snakes first, then player on top)
        # Sort by is_human to draw player last (on top)
        for snake in sorted(self.snakes, key=lambda s: s.is_human):
            snake.draw(screen)
        
        # Draw game over screen
        if self.game_over:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT + Config.HEADER_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Game over text
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("GAME OVER", True, (255, 50, 50))
            screen.blit(game_over_text, 
                       (Config.WINDOW_WIDTH // 2 - game_over_text.get_width() // 2,
                        Config.WINDOW_HEIGHT // 3))
            
            # Winner text
            if self.winner:
                winner_text = font.render(
                    f"Winner: {'Player' if self.winner.is_human else f'AI Snake {self.winner.id}'} with score {self.winner.score}",
                    True, Config.TEXT_COLOR)
                screen.blit(winner_text, 
                           (Config.WINDOW_WIDTH // 2 - winner_text.get_width() // 2,
                            Config.WINDOW_HEIGHT // 2))
            else:
                no_winner_text = font.render("No winner! All snakes died.", True, Config.TEXT_COLOR)
                screen.blit(no_winner_text, 
                           (Config.WINDOW_WIDTH // 2 - no_winner_text.get_width() // 2,
                            Config.WINDOW_HEIGHT // 2))
            
            # Restart instructions
            restart_text = font.render("Press SPACE to restart or ESC to quit", True, Config.TEXT_COLOR)
            screen.blit(restart_text, 
                       (Config.WINDOW_WIDTH // 2 - restart_text.get_width() // 2,
                        Config.WINDOW_HEIGHT * 2 // 3))


# =============================================================================
# MAIN GAME LOOP
# =============================================================================

def main():
    """Main game function"""
    # Initialize pygame
    pygame.init()
    pygame.display.set_caption("Snake Game")
    
    # Create window
    screen = pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT + Config.HEADER_HEIGHT))
    
    # Create fonts
    font = pygame.font.Font(None, Config.SCORE_FONT_SIZE)
    
    # Initialize game state
    game_state = GameState(Config.MIN_WIDTH, Config.MIN_HEIGHT, ai_count=5)
    
    # Game clock
    clock = pygame.time.Clock()
    
    # Movement timer
    last_move_time = time.time()
    
    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Get player snake
                player_snake = next((s for s in game_state.snakes if s.is_human), None)
                
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    game_state.paused = not game_state.paused
                elif event.key == pygame.K_SPACE:
                    if game_state.game_over:
                        game_state.initialize_game()
                    else:
                        game_state.paused = not game_state.paused
                elif player_snake and player_snake.alive:
                    # Handle direction changes
                    new_dir = Direction.from_key(event.key)
                    if new_dir and not Direction.is_opposite(new_dir, player_snake.direction):
                        player_snake.direction = new_dir
        
        # Calculate time since last move
        current_time = time.time()
        move_delay = game_state.current_speed / game_state.speed_multiplier
        
        # Update the game state if enough time has passed
        if current_time - last_move_time > move_delay and not game_state.paused:
            game_state.update()
            last_move_time = current_time
        
        # Draw everything
        game_state.draw(screen, font, clock.get_fps())
        
        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(Config.FPS)
    
    # Quit pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()