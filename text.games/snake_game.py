#!/usr/bin/env python3
import curses
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
    MIN_WIDTH = 70  # Increased minimum width for more snakes
    MIN_HEIGHT = 30  # Increased minimum height for more snakes
    
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
    
    # Debug settings
    DEBUG_INTEGRITY = True  # Enable body integrity checks to prevent invisible collision bugs


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
        """Convert curses key to Direction enum"""
        return {
            curses.KEY_UP: Direction.UP,
            curses.KEY_DOWN: Direction.DOWN,
            curses.KEY_LEFT: Direction.LEFT,
            curses.KEY_RIGHT: Direction.RIGHT,
            ord('w'): Direction.UP,
            ord('s'): Direction.DOWN,
            ord('a'): Direction.LEFT,
            ord('d'): Direction.RIGHT
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
    PHASE_SHIFT = 26      # Allows passing through walls once
    GOLD_RUSH = 27        # Temporarily turns all food into bonus food
    RAINBOW = 28          # Snake changes colors and gets bonus points for food variety
    GRAVITY = 29          # Creates a gravitational pull affecting other snakes
    MIMIC = 30            # Copies the power-up effect of the nearest snake


@dataclass
class Food:
    """Food object representing something snakes can eat"""
    position: Tuple[int, int]
    type: FoodType = FoodType.NORMAL
    points: int = Config.FOOD_POINTS
    char: str = "*"
    color: int = 3
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position


@dataclass
class PowerUp:
    """Power-up object with special effects"""
    position: Tuple[int, int]
    type: PowerUpType
    duration: int
    char: str
    color: int
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
            self.char = "S"
            self.color = 4
        elif self.type == PowerUpType.INVINCIBILITY:
            self.char = "I" 
            self.color = 5
        elif self.type == PowerUpType.GHOST:
            self.char = "G"
            self.color = 6
        elif self.type == PowerUpType.GROWTH:
            self.char = "+"
            self.color = 7
        elif self.type == PowerUpType.SCORE_MULTIPLIER:
            self.char = "M"
            self.color = 3
        elif self.type == PowerUpType.SHRINK:
            self.char = "-"
            self.color = 1
        elif self.type == PowerUpType.MAGNETIC:
            self.char = "Ω"
            self.color = 2
        elif self.type == PowerUpType.FREEZE:
            self.char = "F"
            self.color = 6
        elif self.type == PowerUpType.TELEPORT:
            self.char = "T"
            self.color = 5
        elif self.type == PowerUpType.VISION:
            self.char = "V"
            self.color = 7
        elif self.type == PowerUpType.CONFUSION:
            self.char = "C"
            self.color = 1
        elif self.type == PowerUpType.REVERSE:
            self.char = "R"
            self.color = 2
        elif self.type == PowerUpType.WARP_DRIVE:
            self.char = "W"
            self.color = 4
        elif self.type == PowerUpType.PORTAL:
            self.char = "P"
            self.color = 5
        elif self.type == PowerUpType.BLACK_HOLE:
            self.char = "B"
            self.color = 8
        elif self.type == PowerUpType.TIME_SLOW:
            self.char = "Z"
            self.color = 6
        elif self.type == PowerUpType.DUPLICATE:
            self.char = "D"
            self.color = 3
        elif self.type == PowerUpType.INVISIBILITY:
            self.char = "X"
            self.color = 7
        elif self.type == PowerUpType.LASER_BEAM:
            self.char = "L"
            self.color = 1
        elif self.type == PowerUpType.SHIELD:
            self.char = "◇"
            self.color = 6
        elif self.type == PowerUpType.MAGNET_REPEL:
            self.char = "Ψ"
            self.color = 4
        elif self.type == PowerUpType.SIZE_SHIFTER:
            self.char = "≈"
            self.color = 2
        elif self.type == PowerUpType.FOOD_RAIN:
            self.char = "☂"
            self.color = 3
        elif self.type == PowerUpType.ACID_TRAIL:
            self.char = "A"
            self.color = 2
        elif self.type == PowerUpType.TIME_WARP:
            self.char = "↺"
            self.color = 5
        elif self.type == PowerUpType.PHASE_SHIFT:
            self.char = "Φ"
            self.color = 4
        elif self.type == PowerUpType.GOLD_RUSH:
            self.char = "G"
            self.color = 3
        elif self.type == PowerUpType.RAINBOW:
            self.char = "R"
            self.color = 7
        elif self.type == PowerUpType.GRAVITY:
            self.char = "∇"
            self.color = 6
        elif self.type == PowerUpType.MIMIC:
            self.char = "M"
            self.color = 5
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position
        
    def get_display_attributes(self, game_state):
        """Get display attributes with visual effects if enabled"""
        attrs = 0
        if Config.ENHANCED_VISUALS:
            if self.rarity == "rare":
                # Make rare power-ups blink and stand out
                attrs |= curses.A_BOLD | curses.A_BLINK
            else:
                attrs |= curses.A_BOLD
        return attrs


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
    STALKER = 11         # Follows the largest snake, waiting for an opportunity to attack
    TRAP_SETTER = 12     # Creates loops and traps for other snakes
    KAMIKAZE = 13        # Grows quickly and then charges at other snakes, accepting high risk
    ADAPTIVE = 14        # Changes strategy based on game conditions
    SWARM = 15           # Tries to move in coordination with other similar snakes
    NINJA = 16           # Stays hidden and avoids confrontation until necessary
    HOARDER = 17         # Focuses on collecting as many power-ups as possible
    SPEEDSTER = 18       # Prioritizes speed and quick movement
    SURVIVOR = 19        # Ultimate survival strategy, extremely cautious
    CHAMELEON = 20       # Mimics the strategy of the most successful snake
    JUGGERNAUT = 21      # Grows as big as possible and then uses size to dominate
    AMBUSHER = 22        # Hides near food and waits for other snakes
    PATHFINDER = 23      # Excellent at finding efficient paths through tight spaces
    ENFORCER = 24        # Attempts to eliminate the leading snake


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
    char: str
    color: int
    linked_position: Optional[Tuple[int, int]] = None  # For wormholes
    
    def __init__(self, position, type=None):
        self.position = position
        self.type = type or random.choice([t for t in ObstacleType if t != ObstacleType.WORMHOLE])
        
        # Set appearance based on type
        if self.type == ObstacleType.WALL:
            self.char = "█"
            self.color = 8  # Gray
        elif self.type == ObstacleType.SPIKES:
            self.char = "╳"
            self.color = 1  # Red
        elif self.type == ObstacleType.WORMHOLE:
            self.char = "O"
            self.color = 5  # Magenta
        elif self.type == ObstacleType.SWAMP:
            self.char = "≈"
            self.color = 2  # Green
        elif self.type == ObstacleType.ENERGY_FIELD:
            self.char = "≡"
            self.color = 6  # Cyan
    
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
    
    def _rebuild_body_set(self):
        """Rebuild body_set from body to ensure synchronization"""
        self.body_set = set(self.body)
    
    def _assert_no_duplicates(self):
        """Assert that body has no duplicate positions"""
        if len(self.body) != len(set(self.body)):
            if Config.DEBUG_INTEGRITY:
                # Find duplicates for debugging
                seen = set()
                duplicates = []
                for pos in self.body:
                    if pos in seen:
                        duplicates.append(pos)
                    seen.add(pos)
                raise ValueError(f"Snake {self.id} has duplicate positions in body: {duplicates}")
    
    def validate_body_integrity(self, strict=True):
        """Validate that body and body_set are properly synchronized.
        
        This ensures:
        - No duplicate positions in body
        - body_set equals set(body)
        - If strict, head is at body[0] and is in body_set
        
        Returns True if valid, raises ValueError if invalid when DEBUG_INTEGRITY is enabled.
        """
        if not Config.DEBUG_INTEGRITY:
            return True
            
        if not self.body:
            # Empty body is valid (dead snake)
            if len(self.body_set) != 0:
                raise ValueError(f"Snake {self.id}: body is empty but body_set has {len(self.body_set)} items")
            return True
        
        # Check for duplicates
        expected_set = set(self.body)
        if len(self.body) != len(expected_set):
            self._assert_no_duplicates()  # This will raise with details
        
        # Check body_set matches expected_set
        if self.body_set != expected_set:
            missing = expected_set - self.body_set
            extra = self.body_set - expected_set
            raise ValueError(
                f"Snake {self.id}: body_set mismatch. "
                f"Body len={len(self.body)}, Set len={len(self.body_set)}. "
                f"Missing from set: {missing}. Extra in set: {extra}"
            )
        
        if strict:
            # Check head is properly positioned
            head = self.body[0]
            if head not in self.body_set:
                raise ValueError(f"Snake {self.id}: head {head} not in body_set")
        
        return True
    
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
        """Move the snake by updating its direction and position.
        
        CRITICAL: The new head is added to body exactly ONCE, and only AFTER all
        collision and teleportation checks pass. This prevents phantom positions
        from being added to body_set.
        
        Returns: The final head position after the move, or None if the snake died.
        """
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
            
            # Emergency wall avoidance - always check this regardless of AI update interval
            if Config.EMERGENCY_WALL_CHECK and (
                x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1 or
                next_head in other_snakes_positions or next_head in self.body[1:]):
                # About to hit something, find a safe direction immediately
                safe_directions = []
                
                # First, evaluate each direction thoroughly
                direction_scores = []
                for direction in Direction.all_directions():
                    if Direction.is_opposite(direction, self.direction):
                        continue
                    
                    test_pos = (self.body[0][0] + direction.value[0], self.body[0][1] + direction.value[1])
                    if not self.is_safe(test_pos, other_snakes_positions | set(self.body[1:]), game_state):
                        continue
                    
                    # Calculate free space score to find the best escape route
                    space_score = self.free_space(test_pos, other_snakes_positions | set(self.body[1:]),
                                                foods, power_ups, game_state)
                    
                    # Check if this direction might lead to a tunnel/trap
                    if Config.TUNNEL_CHECK_ENABLED:
                        is_tunnel_safe = self.check_tunnel_safety(
                            self.body[0], direction, other_snakes_positions | set(self.body[1:]), 
                            set(), game_state)
                        
                        if not is_tunnel_safe:
                            space_score -= 300  # Penalize tunnels, but don't remove them completely
                    
                    direction_scores.append((direction, space_score))
                    safe_directions.append(direction)
                
                # If we found safe directions, choose the one with the most space
                if direction_scores:
                    best_direction = max(direction_scores, key=lambda x: x[1])[0]
                    self.direction = best_direction
                elif safe_directions:
                    # Fallback to any safe direction if scoring failed
                    self.direction = random.choice(safe_directions)
                    
            # Regular AI update on the normal interval
            if current_time - self.last_ai_update > Config.AI_UPDATE_INTERVAL:
                self.choose_direction(foods, other_snakes_positions, power_ups, game_state)
                self.last_ai_update = current_time
        
        # Calculate the intended next head position
        # IMPORTANT: Do NOT add this to body or body_set yet!
        intended_head = self.next_head()
        if intended_head is None:
            return None
        
        # Check if this position has an obstacle that might teleport us
        final_head = intended_head
        for obstacle in game_state.obstacles:
            if intended_head == obstacle.position:
                effect = obstacle.get_effect()
                if "teleport" in effect and effect["teleport"]:
                    teleport_dest = effect["teleport"]
                    
                    # Verify the teleport destination is safe
                    # Check bounds
                    if not (0 < teleport_dest[0] < game_state.width - 1 and 
                            0 < teleport_dest[1] < game_state.height - 1):
                        # Destination out of bounds, don't teleport - snake will die
                        break
                    
                    # Check if destination has another snake
                    destination_blocked = teleport_dest in other_snakes_positions
                    
                    # Check if destination has a deadly obstacle
                    if not destination_blocked:
                        for other_obstacle in game_state.obstacles:
                            if other_obstacle.position == teleport_dest:
                                other_effect = other_obstacle.get_effect()
                                if other_effect.get("deadly", False):
                                    destination_blocked = True
                                    break
                    
                    # Only use teleport destination if it's safe
                    if not destination_blocked:
                        final_head = teleport_dest
                    # Otherwise, snake enters wormhole and dies (final_head stays as wormhole position)
                    break
        
        # Now build the new body with the final head position
        # This is the ONLY place where the head is added
        new_body = [final_head] + self.body
        
        # Rebuild body_set from the new body to guarantee synchronization
        self.body = new_body
        self._rebuild_body_set()
        
        # Validate integrity in debug mode
        if Config.DEBUG_INTEGRITY:
            try:
                self.validate_body_integrity()
            except ValueError as e:
                # Log but don't crash - force a rebuild to recover
                print(f"WARNING: Snake {self.id} integrity check failed in move(): {e}")
                self._rebuild_body_set()
        
        return final_head
    
    def remove_tail(self):
        """Remove the snake's tail (last segment) safely.
        
        This method maintains the invariant that body_set == set(body).
        After removal, body_set is rebuilt to guarantee synchronization.
        """
        if not self.body:
            return
        
        # Remove the last segment
        self.body.pop()
        
        # Rebuild body_set from body to ensure perfect synchronization
        # This prevents any desynchronization bugs
        self._rebuild_body_set()
        
        # Validate integrity in debug mode
        if Config.DEBUG_INTEGRITY:
            try:
                self.validate_body_integrity(strict=False)
            except ValueError as e:
                print(f"WARNING: Snake {self.id} integrity check failed in remove_tail(): {e}")
                self._rebuild_body_set()
    
    def gets_longer(self, food_type):
        """Snake gets longer based on the food type.
        
        This method maintains body integrity by rebuilding body_set after growth.
        """
        if not self.body:  # Check if body is empty
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
        
        # Rebuild body_set to ensure synchronization
        self._rebuild_body_set()
        
        # Validate integrity in debug mode
        if Config.DEBUG_INTEGRITY:
            try:
                self.validate_body_integrity(strict=False)
            except ValueError as e:
                print(f"WARNING: Snake {self.id} integrity check failed in gets_longer(): {e}")
                self._rebuild_body_set()
    
    def add_power_up(self, power_up_type):
        """Add a power-up to the snake"""
        end_time = time.time() + Config.POWER_UP_DURATION
        self.power_ups[power_up_type] = end_time
        
        # Apply immediate effects for certain power-ups
        if power_up_type == PowerUpType.SHRINK:
            # Make sure snake has a body
            if not self.body:
                return
                
            # Shrink the snake by removing up to 30% of its length (minimum 3 segments)
            shrink_amount = max(0, min(len(self.body) - 3, int(len(self.body) * 0.3)))
            for _ in range(shrink_amount):
                if len(self.body) > 3:  # Maintain minimum size
                    self.remove_tail()
        
        # Special handling for FOOD_RAIN power-up
        elif power_up_type == PowerUpType.FOOD_RAIN:
            # This will be applied in the game_state update to spawn food around the snake
            pass
            
        # Special handling for LASER_BEAM power-up
        elif power_up_type == PowerUpType.LASER_BEAM:
            # This will be handled in key processing for player snakes
            # and in AI logic for computer snakes
            pass
            
        # Special handling for SIZE_SHIFTER power-up
        elif power_up_type == PowerUpType.SIZE_SHIFTER:
            if not self.body or len(self.body) <= 3:
                return
            
            # Random growth or shrink with 50% chance each way
            if random.random() < 0.5:
                # Grow
                for _ in range(2):
                    if self.body:
                        tail = self.body[-1]
                        self.body.append(tail)
                        self.body_set.add(tail)
            else:
                # Shrink
                for _ in range(2):
                    if len(self.body) > 3:
                        self.remove_tail()
        
        # Special handling for FREEZE power-up
        # Will be handled in the game_state update method
        
        # Special handling for TELEPORT power-up
        # Will be applied when checking collisions
        
        # Special handling for REVERSE power-up
        # Will be handled in the game_state update method for other snakes
    
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
        
    def get_effective_speed(self, base_speed):
        """Calculate effective movement speed based on active power-ups"""
        speed_multiplier = 1.0
        
        # Apply speed boost power-up
        if self.has_power_up(PowerUpType.SPEED_BOOST):
            speed_multiplier *= 1.5
        
        # Apply warp drive power-up
        if self.has_power_up(PowerUpType.WARP_DRIVE):
            speed_multiplier *= 3.0
        
        # Apply freeze power-up (affects other snakes)
        # This is handled in the game update loop
        
        return base_speed * speed_multiplier
        
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
        
    def apply_magnetic_pull(self, foods, max_distance=10):
        """Pull nearby food closer if the magnetic power-up is active"""
        if not self.has_power_up(PowerUpType.MAGNETIC):
            return
        
        if not self.body:  # Check if body is empty
            return
            
        head = self.body[0]
        for food in foods:
            # Calculate distance to food
            dist = abs(head[0] - food.position[0]) + abs(head[1] - food.position[1])
            if dist <= max_distance:
                # Move food slightly closer to snake
                dx = 1 if food.position[0] < head[0] else -1 if food.position[0] > head[0] else 0
                dy = 1 if food.position[1] < head[1] else -1 if food.position[1] > head[1] else 0
                
                # Ensure at least some movement
                if dx == 0 and dy == 0:
                    dx = random.choice([-1, 1])
                
                # Update food position
                food.position = (food.position[0] + dx, food.position[1] + dy)
    
    def free_space(self, pos, obstacles, foods, power_ups, game_state):
        """Calculate free space around a position (floodfill algorithm with optimized performance)"""
        # Quick boundary check first
        x, y = pos
        if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
            return 0  # No free space if it's on a boundary
        
        # Use a faster, less comprehensive calculation for large games
        if Config.OPTIMIZE_FOR_LARGE_GAMES and len(game_state.snakes) >= Config.LARGE_GAME_THRESHOLD:
            # Check immediate and diagonal neighbors for large games
            free_neighbors = 0
            exit_paths = 0
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                nx, ny = x + dx, y + dy
                if (nx <= 0 or nx >= game_state.width - 1 or 
                    ny <= 0 or ny >= game_state.height - 1):
                    continue
                if (nx, ny) not in obstacles:
                    free_neighbors += 1
                    # Check for exit paths - spaces that lead to even more space
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
        
        # Full floodfill algorithm for smaller games
        visited = set()
        to_visit = {pos}
        count = 0
        found_food = False
        found_power_up = False
        exit_routes = 0
        
        # Increase the search limit for better path finding
        search_limit = 150  # Higher search limit
        
        while to_visit and count < search_limit:
            p = to_visit.pop()
            if p in visited or p in obstacles:
                continue
            
            visited.add(p)
            x, y = p
            
            # Check board boundaries
            if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
                continue
            
            # Check if we found a potential exit route (near edge of search space)
            if count > 30:
                # Check if this point has neighbors outside our visited area
                # which would suggest it leads to more open space
                neighbors_outside = 0
                for direction in Direction.all_directions():
                    dx, dy = direction.value
                    neighbor = (x + dx, y + dy)
                    if neighbor not in visited and neighbor not in obstacles:
                        nx, ny = neighbor
                        if not (nx <= 0 or nx >= game_state.width - 1 or 
                                ny <= 0 or ny >= game_state.height - 1):
                            neighbors_outside += 1
                
                if neighbors_outside >= 2:
                    exit_routes += 1
            
            # Check if food is found
            if any(p == food.position for food in foods):
                found_food = True
                if count > 20 and exit_routes > 0:  # Exit if we found food and have exit routes
                    return count + 100 + exit_routes * 30
            
            # Check if power-up is found
            if any(p == powerup.position for powerup in power_ups):
                found_power_up = True
                if count > 15 and exit_routes > 0:  # Exit if we found power-up and have exit routes
                    return count + 150 + exit_routes * 30
            
            count += 1
            
            # Add neighbors
            for direction in Direction.all_directions():
                dx, dy = direction.value
                neighbor = (x + dx, y + dy)
                if neighbor not in visited and neighbor not in obstacles:
                    to_visit.add(neighbor)
        
        # Calculate score based on findings
        space_score = count
        if found_food:
            space_score += 100
        if found_power_up:
            space_score += 150
        
        # Big bonus for having multiple exit routes
        space_score += exit_routes * 40
        
        return space_score
    
    def is_safe(self, pos, obstacles, game_state):
        """Check if position is safe (not a wall or other snake)"""
        x, y = pos
        
        # First check for wall collisions
        if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
            return False
        
        # Then check for snake body collisions
        if pos in obstacles:
            return False
        
        return True
    
    def check_tunnel_safety(self, pos, direction, obstacles, occupied, game_state):
        """Check if a tunnel (single path) eventually leads to an open space"""
        # Maximum tunnel length to check
        max_tunnel_length = 15
        current_pos = pos
        
        # Track positions we check to avoid loops
        checked_positions = set(occupied)
        
        # Follow the tunnel
        for i in range(max_tunnel_length):
            # Move in the given direction
            dx, dy = direction.value
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Check if hit wall or obstacle
            x, y = next_pos
            if (x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1 or
                next_pos in obstacles or next_pos in checked_positions):
                return False  # Dead end
            
            # Add to checked positions
            checked_positions.add(next_pos)
            current_pos = next_pos
            
            # Count available directions from this position
            available = 0
            for test_dir in Direction.all_directions():
                test_pos = (current_pos[0] + test_dir.value[0], current_pos[1] + test_dir.value[1])
                test_x, test_y = test_pos
                if (test_x <= 0 or test_x >= game_state.width - 1 or 
                    test_y <= 0 or test_y >= game_state.height - 1 or 
                    test_pos in obstacles or
                    test_pos in checked_positions):
                    continue
                available += 1
            
            # If we found multiple options, it's not a pure tunnel anymore
            if available > 1:
                return True  # Tunnel leads to open space
            
            # If no directions available, it's a dead end
            if available == 0:
                return False
            
            # If exactly one direction, continue following the tunnel
            for test_dir in Direction.all_directions():
                test_pos = (current_pos[0] + test_dir.value[0], current_pos[1] + test_dir.value[1])
                test_x, test_y = test_pos
                if (test_x <= 0 or test_x >= game_state.width - 1 or 
                    test_y <= 0 or test_y >= game_state.height - 1 or 
                    test_pos in obstacles or
                    test_pos in checked_positions):
                    continue
                direction = test_dir
                break
        
        # If we checked the maximum length and didn't find a dead end or opening,
        # assume it's risky but not necessarily fatal
        return False
    
    def look_ahead(self, start_pos, direction, obstacles, game_state, steps):
        """Improved simulation of future moves to detect potential collisions and traps"""
        if steps <= 0:
            return 10  # Base score for reaching the look-ahead depth safely
            
        # Clone the obstacles set to avoid modifying the original
        future_obstacles = set(obstacles)
        
        # Start simulating moves
        current_pos = start_pos
        current_direction = direction
        positions = [current_pos]  # Track positions we would occupy
        
        # Track available directions at each step to detect traps
        available_directions_count = []
        
        for i in range(steps):
            # Calculate next position
            dx, dy = current_direction.value
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Check if next position would hit a wall
            x, y = next_pos
            if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
                return -400  # Severely increased penalty for hitting a wall
                
            # Check if next position would hit an obstacle
            if next_pos in future_obstacles:
                return -300  # Severely increased penalty for hitting an obstacle
                
            # Check if next position would hit our own future body
            if next_pos in positions:
                return -350  # Severely increased penalty for self-collision
                
            # Move to next position
            current_pos = next_pos
            positions.append(current_pos)
            
            # Add our current position to obstacles for next simulation step
            future_obstacles.add(current_pos)
            
            # Count available directions for this position
            available = 0
            available_directions = []
            
            for test_dir in Direction.all_directions():
                if Direction.is_opposite(test_dir, current_direction):
                    continue
                test_pos = (current_pos[0] + test_dir.value[0], current_pos[1] + test_dir.value[1])
                test_x, test_y = test_pos
                if (test_x <= 0 or test_x >= game_state.width - 1 or 
                    test_y <= 0 or test_y >= game_state.height - 1 or 
                    test_pos in future_obstacles or
                    test_pos in positions):
                    continue
                available += 1
                available_directions.append(test_dir)
            
            available_directions_count.append(available)
            
            # If only one direction available, do a deeper check to see if it's a tunnel
            if available == 1 and i < steps - 1:
                # Check if this single available direction leads to a dead end
                tunnel_dir = available_directions[0]
                is_tunnel_safe = self.check_tunnel_safety(current_pos, tunnel_dir, future_obstacles, positions, game_state)
                
                if not is_tunnel_safe:
                    return -500  # Severely penalize tunnels with no exit
            
            # If no directions available, this is a trap!
            elif available == 0 and i < steps - 1:
                return -600  # Extremely penalize getting trapped
                
            # For subsequent steps, choose the direction with most options 
            # (more sophisticated than just continuing in the same direction)
            if i < steps - 1:
                best_dir = None
                most_options = -1
                
                for test_dir in Direction.all_directions():
                    if Direction.is_opposite(test_dir, current_direction):
                        continue
                    test_pos = (current_pos[0] + test_dir.value[0], current_pos[1] + test_dir.value[1])
                    test_x, test_y = test_pos
                    if (test_x <= 0 or test_x >= game_state.width - 1 or 
                        test_y <= 0 or test_y >= game_state.height - 1 or 
                        test_pos in future_obstacles or
                        test_pos in positions):
                        continue
                    
                    # Count options from this new position
                    options = 0
                    for next_dir in Direction.all_directions():
                        if Direction.is_opposite(next_dir, test_dir):
                            continue
                        next_test_pos = (test_pos[0] + next_dir.value[0], test_pos[1] + next_dir.value[1])
                        next_x, next_y = next_test_pos
                        if (next_x <= 0 or next_x >= game_state.width - 1 or 
                            next_y <= 0 or next_y >= game_state.height - 1 or 
                            next_test_pos in future_obstacles or
                            next_test_pos in positions):
                            continue
                        options += 1
                    
                    if options > most_options:
                        most_options = options
                        best_dir = test_dir
                
                # If found a better direction, use it
                if best_dir:
                    current_direction = best_dir
        
        # Analyze the trend of available directions
        # If consistently decreasing, it's heading into a confined space
        if len(available_directions_count) >= 2:
            if all(available_directions_count[i] > available_directions_count[i+1] 
                   for i in range(len(available_directions_count)-1)):
                return -150  # Increased penalty for consistently decreasing options
            
            # Especially penalize directions that end with very few options
            if available_directions_count[-1] < 2:
                return -200  # Significant penalty for ending with limited options
        
        # Calculate free space at final position with more weight
        free_neighbors = 0
        x, y = positions[-1]
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if (nx <= 0 or nx >= game_state.width - 1 or 
                ny <= 0 or ny >= game_state.height - 1 or
                (nx, ny) in future_obstacles):
                continue
            free_neighbors += 1
        
        # Apply distance-based penalties (with diminishing effect)
        # The further we can go without issues, the better
        step_completion_bonus = min(50, steps * 5)
            
        # Add bonus for having multiple options at the end
        options_bonus = available_directions_count[-1] * 20 if available_directions_count else 0
            
        # Return score based on simulated moves with increased weight for space and options
        return 50 + free_neighbors * 25 + step_completion_bonus + options_bonus
    
    def choose_direction(self, foods, other_snakes_positions, power_ups, game_state):
        """Advanced AI logic to choose the next direction with improved decision making"""
        if not self.body:  # Check if body is empty
            return None
            
        head = self.body[0]
        obstacles = set(other_snakes_positions) | set(self.body[1:])
        
        # Calculate danger zones (spaces next to other snake heads)
        # This helps avoiding potential head-to-head collisions
        danger_zones = set()
        for other_snake in game_state.snakes:
            if other_snake is not self and other_snake.alive and len(other_snake.body) >= len(self.body):
                other_head = other_snake.body[0]
                for direction in Direction.all_directions():
                    danger_pos = (other_head[0] + direction.value[0], other_head[1] + direction.value[1])
                    # Don't mark as danger if it's a wall (already avoided)
                    x, y = danger_pos
                    if not (x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1):
                        danger_zones.add(danger_pos)
        
        # Find food and power-ups with improved evaluation
        food_targets = []
        power_up_targets = []
        
        # For Scavenger strategy, prioritize dropped food
        dropped_food_bonus = 0
        if self.strategy == AIStrategy.SCAVENGER:
            dropped_food_bonus = 300
            
        # For Territorial strategy, establish a territory if none exists
        if self.strategy == AIStrategy.TERRITORIAL and not self.territory_center:
            self.territory_center = (self.body[0][0], self.body[0][1])
        
        # Evaluate each food item
        for food in foods:
            food_pos = food.position
            dist = abs(head[0] - food_pos[0]) + abs(head[1] - food_pos[1])
            
            # Check if path to food is reasonably clear
            path_score = 0
            
            # Simplified path check for performance
            # Check if there's a relatively clear path to the food
            x_step = 1 if food_pos[0] > head[0] else -1 if food_pos[0] < head[0] else 0
            y_step = 1 if food_pos[1] > head[1] else -1 if food_pos[1] < head[1] else 0
            
            # Sample points along potential path
            path_clear = True
            check_points = []
            
            # X-path
            if x_step != 0:
                for x in range(head[0] + x_step, food_pos[0] + x_step, x_step):
                    check_points.append((x, head[1]))
            
            # Y-path
            if y_step != 0:
                for y in range(head[1] + y_step, food_pos[1] + y_step, y_step):
                    check_points.append((food_pos[0], y))
            
            # Check sample points
            obstacles_in_path = 0
            for point in check_points:
                if point in obstacles:
                    obstacles_in_path += 1
                    
            # Path score reduced based on obstacles
            if len(check_points) > 0:
                path_score = 100 * (1 - obstacles_in_path / len(check_points))
            
            # Bonus for food type
            type_bonus = 0
            if hasattr(food, 'type'):
                if food.type == FoodType.BONUS:
                    type_bonus = 200
                elif food.type == FoodType.DROPPED:
                    type_bonus = 50 + dropped_food_bonus  # Extra bonus for Scavenger strategy
            
            # Territorial strategy bonus/penalty based on distance from territory center
            territorial_factor = 0
            if self.strategy == AIStrategy.TERRITORIAL and self.territory_center:
                dist_to_territory = abs(food_pos[0] - self.territory_center[0]) + abs(food_pos[1] - self.territory_center[1])
                # Prefer food close to territory, penalty for food far away
                territorial_factor = 200 - dist_to_territory * 10
            
            # Check if food is in a danger zone
            danger_penalty = 200 if food_pos in danger_zones else 0
            
            # Calculate final score for this food
            # Closer food is better, clear path is better, 
            # special food is better, but avoid dangerous areas
            food_score = (1000 / (dist + 1)) + path_score + type_bonus - danger_penalty + territorial_factor
            
            food_targets.append((food_pos, food_score, dist))
        
        # Evaluate power-ups similarly to food
        for power_up in power_ups:
            power_up_pos = power_up.position
            dist = abs(head[0] - power_up_pos[0]) + abs(head[1] - power_up_pos[1])
            
            # Prioritize power-ups based on situation
            type_value = 0
            if power_up.type == PowerUpType.INVINCIBILITY:
                # More valuable when longer
                type_value = 300 if len(self.body) > 10 else 150
            elif power_up.type == PowerUpType.GHOST:
                # More valuable when many snakes
                type_value = 50 * len([s for s in game_state.snakes if s.alive])
            elif power_up.type == PowerUpType.SPEED_BOOST:
                # Generally useful
                type_value = 150
            elif power_up.type == PowerUpType.GROWTH:
                # More valuable early game
                type_value = 250 if game_state.death_counter <= 2 else 100
            elif power_up.type == PowerUpType.SCORE_MULTIPLIER:
                # More valuable when food is nearby
                nearby_food = sum(1 for f in foods if abs(f.position[0] - power_up_pos[0]) + abs(f.position[1] - power_up_pos[1]) < 10)
                type_value = 100 + 50 * nearby_food
            
            # Check if power-up is in a danger zone
            danger_penalty = 150 if power_up_pos in danger_zones else 0
            
            # Territorial strategy adjustment
            territorial_factor = 0
            if self.strategy == AIStrategy.TERRITORIAL and self.territory_center:
                dist_to_territory = abs(power_up_pos[0] - self.territory_center[0]) + abs(power_up_pos[1] - self.territory_center[1])
                territorial_factor = 150 - dist_to_territory * 8
            
            # Calculate score
            power_up_score = (800 / (dist + 1)) + type_value - danger_penalty + territorial_factor
            
            # If already have this power-up, less valuable
            if power_up.type in self.power_ups:
                power_up_score *= 0.3
                
            power_up_targets.append((power_up_pos, power_up_score, dist))
        
        # Sort targets by score (descending)
        food_targets.sort(key=lambda x: x[1], reverse=True)
        power_up_targets.sort(key=lambda x: x[1], reverse=True)
        
        # Select primary target - best food or power-up
        target = None
        target_score = 0
        
        if food_targets and (not power_up_targets or food_targets[0][1] >= power_up_targets[0][1]):
            target = food_targets[0][0]
            target_score = food_targets[0][1]
        elif power_up_targets:
            target = power_up_targets[0][0]
            target_score = power_up_targets[0][1]
        
        # If no target found, try to continue safely
        if not target:
            # Try to continue in same direction if safe
            next_pos = self.next_head()
            if self.is_safe(next_pos, obstacles, game_state) and next_pos not in danger_zones:
                return
            
            # Find any safe direction, preferring ones with most free space
            safe_directions = []
            for direction in Direction.all_directions():
                if Direction.is_opposite(direction, self.direction):
                    continue
                next_pos = (head[0] + direction.value[0], head[1] + direction.value[1])
                if self.is_safe(next_pos, obstacles, game_state):
                    # Calculate free space in this direction
                    space = self.free_space(next_pos, obstacles, foods, power_ups, game_state)
                    danger = 100 if next_pos in danger_zones else 0
                    safe_directions.append((direction, space - danger))
            
            if safe_directions:
                # Choose direction with most free space
                self.direction = max(safe_directions, key=lambda x: x[1])[0]
            return
        
        # Simple algorithm for many snakes to improve performance
        if Config.OPTIMIZE_FOR_LARGE_GAMES and len(game_state.snakes) >= Config.LARGE_GAME_THRESHOLD:
            # First priority: avoid immediate collisions
            next_pos = self.next_head()
            if not self.is_safe(next_pos, obstacles, game_state) or next_pos in danger_zones:
                # Current direction is unsafe, find a safe one
                safe_directions = []
                for direction in Direction.all_directions():
                    if Direction.is_opposite(direction, self.direction):
                        continue
                    new_head = (head[0] + direction.value[0], head[1] + direction.value[1])
                    if self.is_safe(new_head, obstacles, game_state) and new_head not in danger_zones:
                        # Calculate distance to target for this direction
                        dist = abs(new_head[0] - target[0]) + abs(new_head[1] - target[1])
                        safe_directions.append((direction, dist))
                
                if safe_directions:
                    # Sort by distance to target (ascending)
                    safe_directions.sort(key=lambda x: x[1])
                    # Choose the direction that gets us closest to target
                    self.direction = safe_directions[0][0]
                elif any(self.is_safe((head[0] + d.value[0], head[1] + d.value[1]), obstacles, game_state) 
                        for d in Direction.all_directions() if not Direction.is_opposite(d, self.direction)):
                    # If no safe direction without danger, just pick any safe direction
                    for direction in Direction.all_directions():
                        if Direction.is_opposite(direction, self.direction):
                            continue
                        new_head = (head[0] + direction.value[0], head[1] + direction.value[1])
                        if self.is_safe(new_head, obstacles, game_state):
                            self.direction = direction
                            break
                return
                
            # Move towards target if possible
            target_dx = target[0] - head[0]
            target_dy = target[1] - head[1]
            
            # Determine if we should move horizontally or vertically based on which gets us closer
            if abs(target_dx) > abs(target_dy):
                # Try horizontal movement first
                new_dir = Direction.RIGHT if target_dx > 0 else Direction.LEFT
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state) and new_head not in danger_zones:
                        self.direction = new_dir
                        return
                
                # Try vertical if horizontal doesn't work
                new_dir = Direction.DOWN if target_dy > 0 else Direction.UP
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state) and new_head not in danger_zones:
                        self.direction = new_dir
                        return
                    elif self.is_safe(new_head, obstacles, game_state):  # Accept danger if necessary
                        self.direction = new_dir
                        return
            else:
                # Try vertical movement first
                new_dir = Direction.DOWN if target_dy > 0 else Direction.UP
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state) and new_head not in danger_zones:
                        self.direction = new_dir
                        return
                
                # Try horizontal if vertical doesn't work
                new_dir = Direction.RIGHT if target_dx > 0 else Direction.LEFT
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state) and new_head not in danger_zones:
                        self.direction = new_dir
                        return
                    elif self.is_safe(new_head, obstacles, game_state):  # Accept danger if necessary
                        self.direction = new_dir
                        return
            
            # Continue in same direction if it's safe (already checked above)
            return
        
        # Calculate direction to target
        target_dx = target[0] - head[0]
        target_dy = target[1] - head[1]
        
        # Dynamically adjust strategy based on game situation
        # This makes AI adaptable to changing conditions
        if self.strategy == AIStrategy.AGGRESSIVE and len(self.body) < 5:
            # Be less aggressive when small
            temp_strategy = AIStrategy.OPPORTUNISTIC
        elif self.strategy == AIStrategy.HUNTER and len(game_state.snakes) <= 2:
            # No point being a hunter with few snakes
            temp_strategy = AIStrategy.AGGRESSIVE
        elif self.strategy == AIStrategy.CAUTIOUS and game_state.death_counter > len(game_state.snakes) / 2:
            # Be more aggressive in late game
            temp_strategy = AIStrategy.OPPORTUNISTIC
        else:
            temp_strategy = self.strategy
        
        # Evaluate each possible direction with look-ahead
        candidates = []
        for direction in Direction.all_directions():
            # Skip opposite direction
            if Direction.is_opposite(direction, self.direction):
                continue
            
            # Get next position in this direction
            dx, dy = direction.value
            new_head = (head[0] + dx, head[1] + dy)
            
            # Skip if not safe
            if not self.is_safe(new_head, obstacles, game_state):
                continue
            
            # Look ahead further (6 steps instead of 4)
            future_score = self.look_ahead(new_head, direction, obstacles, game_state, Config.LOOK_AHEAD_STEPS)
            if future_score < -100:  # Increased threshold
                # This direction leads to certain death, skip it
                continue
            
            # Distance to target
            manhattan_to_target = abs(new_head[0] - target[0]) + abs(new_head[1] - target[1])
            
            # Calculate more factors for decision making
            
            # 1. Target approach score - higher for moves toward target
            target_score = 500 - 20 * manhattan_to_target
            
            # Direct path to target gets bonus
            if (target_dx > 0 and dx > 0) or (target_dx < 0 and dx < 0):  # Moving in correct x direction
                target_score += 150
            if (target_dy > 0 and dy > 0) or (target_dy < 0 and dy < 0):  # Moving in correct y direction
                target_score += 150
            
            # Immediate adjacent to target gets huge bonus
            if manhattan_to_target == 1:
                target_score += 1500
                
            # 2. Space evaluation - now with much higher priority for survival
            space = self.free_space(new_head, obstacles, foods, power_ups, game_state)
            space_score = Config.OPEN_SPACE_WEIGHT * space  # Significantly increased weight for space
            
            # Much higher penalty for confined spaces to ensure exit paths
            if space < Config.SURVIVAL_THRESHOLD:
                space_score -= 600  # Severe penalty
            elif space < 15:
                space_score -= 300  # Significant penalty
            
            # 3. Danger zone avoidance
            danger_score = -250 if new_head in danger_zones else 0
            
            # Adjust danger score based on snake size - bigger snakes can be more aggressive
            if len(self.body) > 15:
                danger_score = danger_score * 0.5  # Half penalty for big snakes
            
            # 4. Look-ahead bonus
            look_ahead_score = future_score * 0.8  # Increased weight
            
            # 5. Preference for continuing in same direction (smoother movement)
            direction_score = 75 if direction == self.direction else 0
            
            # 6. Wall proximity penalty - avoid moving along walls when not necessary
            wall_score = 0
            if new_head[0] == 1 or new_head[0] == game_state.width - 2:  # Near vertical walls
                wall_score -= 30
            if new_head[1] == 1 or new_head[1] == game_state.height - 2:  # Near horizontal walls
                wall_score -= 30
            
            # 7. Strategy-specific scoring
            strategy_score = 0
            
            if temp_strategy == AIStrategy.AGGRESSIVE:
                # Aggressive: Go straight for target, ignore most danger
                strategy_score = target_score * 3.0 - danger_score * 0.3  # Much more aggressive
                # If close to target, be extremely aggressive
                if manhattan_to_target < 5:
                    strategy_score += 800
                # Significantly less concerned with space
                space_weight_reduction = min(0.6, 1.0 - len(self.body) * 0.02)  # Bigger snakes care less about space
                strategy_score -= space_score * space_weight_reduction
            
            elif temp_strategy == AIStrategy.CAUTIOUS:
                # Cautious: Value space and safety more than target
                strategy_score = space_score * 2.5 + look_ahead_score * 2.0 - danger_score * 1.5
                # But still go for target if it's very close
                if manhattan_to_target < 2:
                    strategy_score += target_score * 1.5
            
            elif temp_strategy == AIStrategy.OPPORTUNISTIC:
                # Opportunistic: Balance target and space, change direction based on situation
                strategy_score = target_score * 1.5 + space_score * 1.2 - danger_score * 0.8 + random.randint(0, 100)
                # More aggressive when target is close
                if manhattan_to_target < 5:
                    strategy_score += 300
                # More cautious when space is limited
                if space < 12:
                    strategy_score += space_score * 1.2
            
            elif temp_strategy == AIStrategy.DEFENSIVE:
                # Defensive: Stay away from other snakes
                snake_proximity = 0
                for pos in other_snakes_positions:
                    dist = abs(new_head[0] - pos[0]) + abs(new_head[1] - pos[1])
                    if dist < 5:
                        snake_proximity += (5 - dist) * 35
                
                strategy_score = target_score * 0.8 + space_score * 1.8 - snake_proximity * 1.8 + look_ahead_score * 1.5
                # Stronger space preference
                if space < 20:
                    strategy_score += space_score * 2
                # Still go for target if it's very close
                if manhattan_to_target < 3:
                    strategy_score += 300
            
            elif temp_strategy == AIStrategy.HUNTER:
                # Hunter: Target other snake heads to try to kill them
                hunter_score = 0
                for other_snake in game_state.snakes:
                    if other_snake is not self and other_snake.alive:
                        other_head = other_snake.body[0]
                        dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                        
                        # More aggressive hunting - consider attacking even smaller snakes
                        size_advantage = len(self.body) - len(other_snake.body)
                        
                        # Only hunt if we're bigger or same size
                        if size_advantage >= 0 and dist < 8:
                            # Perfect position for head-on collision when we're bigger
                            if dist == 2 and size_advantage > 0:  
                                hunter_score += 800
                            # Within hunting range
                            elif dist < 5:  
                                hunter_score += (8 - dist) * 120
                
                strategy_score = hunter_score + target_score * 0.4 + space_score * 0.7
                # Don't forget food when it's very close
                if manhattan_to_target < 3:
                    strategy_score += target_score * 0.8
                    
            elif temp_strategy == AIStrategy.SCAVENGER:
                # Scavenger: Prioritize dropped food and safety over aggression
                is_dropped_target = any(f.position == target and f.type == FoodType.DROPPED for f in foods)
                dropped_bonus = 800 if is_dropped_target else 0
                
                strategy_score = target_score * 1.2 + space_score * 1.2 + dropped_bonus - danger_score * 1.0
                # Less cautious overall, more focused on finding dropped food
                if not is_dropped_target:
                    strategy_score += look_ahead_score * 1.2
                    
            elif temp_strategy == AIStrategy.TERRITORIAL:
                # Territorial: Prefer staying in a specific area but more aggressive in defense
                if self.territory_center:
                    territory_dist = abs(new_head[0] - self.territory_center[0]) + abs(new_head[1] - self.territory_center[1])
                    # Higher score for staying close to territory center
                    territory_score = 400 - territory_dist * 12
                    
                    # Check if any other snakes are in our territory
                    invaders = 0
                    for other_snake in game_state.snakes:
                        if other_snake is not self and other_snake.alive:
                            other_head = other_snake.body[0]
                            dist_to_territory = abs(other_head[0] - self.territory_center[0]) + abs(other_head[1] - self.territory_center[1])
                            if dist_to_territory < 8:  # Close to our territory
                                invaders += 1
                                invader_dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                                if invader_dist < 5:  # We're close to invader
                                    # Become more aggressive to defend territory
                                    territory_score += (5 - invader_dist) * 150
                    
                    # Balance between territory defense and food/space
                    strategy_score = target_score * 0.7 + space_score * 1.0 + territory_score
                    
                    # If far from territory, prioritize getting back
                    if territory_dist > 10:
                        strategy_score += territory_score * 2
                else:
                    # No territory yet, behave opportunistically until established
                    strategy_score = target_score + space_score * 1.5
                    
            elif temp_strategy == AIStrategy.BERSERKER:
                # Berserker: Super aggressive, minimal safety checks
                # Target score is massively important
                strategy_score = target_score * 5.0 - danger_score * 0.2
                
                # Almost no concern for space unless critically low
                if space < 5:  # Only care about space if it's extremely confined
                    strategy_score += space_score * 0.5
                
                # Even more aggressive when target is close
                if manhattan_to_target < 6:
                    strategy_score += 1000
                
                # Also aggressive toward other snakes
                for other_snake in game_state.snakes:
                    if other_snake is not self and other_snake.alive:
                        other_head = other_snake.body[0]
                        dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                        
                        # If we're bigger and close, consider attacking
                        if len(self.body) > len(other_snake.body) and dist < 4:
                            strategy_score += (4 - dist) * 200
                
            elif temp_strategy == AIStrategy.INTERCEPTOR:
                # Interceptor: Tries to cut off other snakes' paths to food
                intercept_score = 0
                
                # Identify other snakes close to food
                for food_item in foods:
                    food_pos = food_item.position
                    food_value = food_item.points
                    
                    # Find snakes heading toward this food
                    for other_snake in game_state.snakes:
                        if other_snake is not self and other_snake.alive:
                            other_head = other_snake.body[0]
                            other_dist = abs(other_head[0] - food_pos[0]) + abs(other_head[1] - food_pos[1])
                            
                            # If another snake is close to food
                            if other_dist < 8:
                                # Calculate ideal intercept position
                                intercept_x = (food_pos[0] + other_head[0]) // 2
                                intercept_y = (food_pos[1] + other_head[1]) // 2
                                
                                # Calculate our distance to intercept
                                intercept_dist = abs(head[0] - intercept_x) + abs(head[1] - intercept_y)
                                
                                # Higher score for closer intercepts with more valuable food
                                if intercept_dist < 10:
                                    intercept_value = (food_value * 100) / (intercept_dist + 1)
                                    intercept_score += intercept_value
                
                # Balance between interception and normal targeting
                strategy_score = intercept_score + target_score * 0.6 + space_score * 0.8
                
            elif temp_strategy == AIStrategy.POWERUP_SEEKER:
                # PowerUp Seeker: Prioritizes power-ups above all else
                powerup_score = 0
                
                # Check if we're targeting a power-up
                is_powerup_target = any(p.position == target for p in power_ups)
                
                if is_powerup_target:
                    # Massively boost score for power-up targets
                    powerup_score = 1500
                    
                    # Check which type of power-up
                    for p in power_ups:
                        if p.position == target:
                            # Additional bonus based on power-up type
                            if p.type == PowerUpType.INVINCIBILITY:
                                powerup_score += 300
                            elif p.type == PowerUpType.GHOST:
                                powerup_score += 250
                            elif p.type == PowerUpType.SPEED_BOOST:
                                powerup_score += 200
                            break
                else:
                    # If not targeting a power-up, normal scoring but with slight preference for being in center
                    center_dist = abs(new_head[0] - game_state.width//2) + abs(new_head[1] - game_state.height//2)
                    center_bonus = 100 - (center_dist * 2)
                    strategy_score = target_score * 0.7 + space_score + center_bonus
                
                strategy_score = powerup_score + target_score * 0.5 + space_score * 0.8
                
            elif temp_strategy == AIStrategy.STALKER:
                # Stalker: Follows the largest snake, waiting for opportunity
                stalker_score = 0
                target_snake = None
                max_size = 0
                
                # Find the largest snake
                for other_snake in game_state.snakes:
                    if other_snake is not self and other_snake.alive and len(other_snake.body) > max_size:
                        max_size = len(other_snake.body)
                        target_snake = other_snake
                
                if target_snake:
                    target_head = target_snake.body[0]
                    target_tail = target_snake.body[-1]
                    
                    head_dist = abs(new_head[0] - target_head[0]) + abs(new_head[1] - target_head[1])
                    tail_dist = abs(new_head[0] - target_tail[0]) + abs(new_head[1] - target_tail[1])
                    
                    # Prefer to stay close but not too close to the target snake
                    if head_dist < 3:  # Too close to head - might be dangerous
                        stalker_score -= 200
                    elif head_dist < 6:  # Ideal distance to track
                        stalker_score += 600 - (head_dist * 50)
                    elif head_dist < 12:  # Still tracking but further
                        stalker_score += 300 - (head_dist * 20)
                    
                    # Bonus for being near the tail - good to pick up dropped food
                    if tail_dist < 5:
                        stalker_score += 250 - (tail_dist * 30)
                
                # Balance between stalking and normal targeting
                strategy_score = stalker_score + target_score * 0.6 + space_score
                
            elif temp_strategy == AIStrategy.TRAP_SETTER:
                # Trap Setter: Creates loops and traps for other snakes
                trap_score = 0
                
                # Check if we're near a wall - good for creating traps
                wall_dist = min(
                    new_head[0],  # Distance to left wall
                    game_state.width - 1 - new_head[0],  # Distance to right wall
                    new_head[1],  # Distance to top wall
                    game_state.height - 1 - new_head[1]  # Distance to bottom wall
                )
                
                # Prefer to stay near walls but not right against them
                if wall_dist == 1:
                    trap_score += 200
                elif wall_dist == 2:
                    trap_score += 300
                elif wall_dist == 3:
                    trap_score += 100
                
                # Check for other snakes nearby to trap
                for other_snake in game_state.snakes:
                    if other_snake is not self and other_snake.alive:
                        other_head = other_snake.body[0]
                        dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                        
                        if dist < 8:  # Snake is close enough to potentially trap
                            # Calculate position where we might cut off their path
                            # Prefer to be in their most likely path to food
                            for food_item in foods:
                                food_dist = abs(other_head[0] - food_item.position[0]) + abs(other_head[1] - food_item.position[1])
                                if food_dist < 10:  # Food is close to other snake
                                    # Position between snake and food is ideal for trapping
                                    mid_x = (other_head[0] + food_item.position[0]) // 2
                                    mid_y = (other_head[1] + food_item.position[1]) // 2
                                    
                                    # Distance to ideal trap position
                                    trap_pos_dist = abs(new_head[0] - mid_x) + abs(new_head[1] - mid_y)
                                    if trap_pos_dist < 5:
                                        trap_score += (5 - trap_pos_dist) * 150
                
                # Balance between trapping and normal strategy
                strategy_score = trap_score + target_score * 0.7 + space_score
                
            elif temp_strategy == AIStrategy.KAMIKAZE:
                # Kamikaze: Grows quickly then charges at other snakes
                kamikaze_score = 0
                
                # Early game strategy - focus on growth
                if len(self.body) < 15:
                    # Be food-focused to grow quickly
                    strategy_score = target_score * 2.5 + space_score * 0.5
                    
                    # More aggressive for nearby food
                    if manhattan_to_target < 4:
                        strategy_score += 500
                else:
                    # Late game - target other snakes aggressively
                    for other_snake in game_state.snakes:
                        if other_snake is not self and other_snake.alive:
                            other_head = other_snake.body[0]
                            dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                            
                            if dist < 10:  # Close enough to charge
                                # Charge regardless of size
                                charge_score = 1000 - (dist * 100)
                                kamikaze_score += charge_score
                                
                                # Even more aggressive when in striking distance
                                if dist < 3:
                                    kamikaze_score += 1000
                    
                    # Ignore safety concerns when charging
                    strategy_score = kamikaze_score + target_score * 0.3
                    
                    # Almost zero concern for space
                    if space < 3:  # Only care if critically confined
                        strategy_score += space_score * 0.3
            
            # Safety check - enter survival mode if space is dangerously low
            # Only certain strategies will enter survival mode, others will be more reckless
            survival_strategies = [AIStrategy.CAUTIOUS, AIStrategy.DEFENSIVE, AIStrategy.SCAVENGER, AIStrategy.TERRITORIAL]
            reckless_strategies = [AIStrategy.BERSERKER, AIStrategy.KAMIKAZE]
            
            survival_mode = space < Config.SURVIVAL_THRESHOLD and self.strategy in survival_strategies
            
            # Super aggressive strategies like BERSERKER and KAMIKAZE ignore danger completely unless extremely confined
            reckless_mode = self.strategy in reckless_strategies and space > 3
            
            if survival_mode:
                # In survival mode, prioritize space and exit routes above all else
                total_score = (
                    space_score * 3.0 +  # Triple importance of space
                    look_ahead_score * 2.0 +  # Double importance of future path safety
                    direction_score * 0.5 +  # Still prefer continuing same direction if safe
                    danger_score * 2.0 +  # Double danger avoidance
                    wall_score * 2.0 +  # Double wall avoidance
                    target_score * 0.2  # Target is much less important when in danger
                )
            elif reckless_mode:
                # In reckless mode, almost completely ignore safety concerns
                total_score = (
                    target_score * 2.5 +  # Massively boost target importance
                    strategy_score * 2.0 +  # Double strategy-specific behavior
                    space_score * 0.2 +   # Almost no concern for space
                    danger_score * 0.2 +  # Almost no concern for danger
                    direction_score +     # Normal preference for continuing in same direction
                    wall_score * 0.5 +    # Reduced wall avoidance
                    look_ahead_score * 0.3  # Minimal concern for future safety
                )
            else:
                # Normal mode - balanced but more aggressive scoring
                total_score = (
                    target_score * 1.3 +  # Increased target importance
                    space_score * 1.2 +   # Slightly reduced space importance
                    danger_score * 0.8 +  # Reduced danger avoidance
                    direction_score + 
                    wall_score + 
                    strategy_score * 1.5 + # Increased strategy weight
                    look_ahead_score * 0.8  # Reduced future safety importance
                )
            
            # Add a small bit of randomness to break ties
            total_score += random.uniform(-5, 5)
            
            candidates.append((direction, total_score))
        
        # Choose direction with highest score, with additional checks
        if candidates:
            # First, check if we need to perform a special safety check
            # If we have very few candidates, verify they don't lead to dead ends
            if len(candidates) <= 2 and Config.TUNNEL_CHECK_ENABLED:
                # For each candidate, do an extended safety check
                safe_candidates = []
                for dir_candidate, score in candidates:
                    next_pos = (head[0] + dir_candidate.value[0], head[1] + dir_candidate.value[1])
                    is_safe_path = self.check_tunnel_safety(head, dir_candidate, obstacles, set(self.body), game_state)
                    if is_safe_path:
                        safe_candidates.append((dir_candidate, score))
                    else:
                        # If not safe, significantly reduce the score
                        safe_candidates.append((dir_candidate, score - 500))
                        
                candidates = safe_candidates
            
            # Sort candidates by score for better decision making
            sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
            
            # Choose the highest scoring direction
            self.prev_direction = self.direction
            self.direction = sorted_candidates[0][0]
            
            # Additional safety measure: if highest-scoring direction has nearly the same score
            # as the second-best but the second-best has more free space, prefer that
            if len(sorted_candidates) > 1:
                best_score = sorted_candidates[0][1]
                second_score = sorted_candidates[1][1]
                
                # If scores are close (within 10%)
                if second_score > 0 and best_score > 0 and (best_score - second_score) / best_score < 0.1:
                    best_dir = sorted_candidates[0][0]
                    second_dir = sorted_candidates[1][0]
                    
                    # Check free space for both
                    best_pos = (head[0] + best_dir.value[0], head[1] + best_dir.value[1])
                    second_pos = (head[0] + second_dir.value[0], head[1] + second_dir.value[1])
                    
                    best_space = self.free_space(best_pos, obstacles, foods, power_ups, game_state)
                    second_space = self.free_space(second_pos, obstacles, foods, power_ups, game_state)
                    
                    # If second direction has significantly more space, choose it instead
                    if second_space > best_space * 1.5:
                        self.direction = second_dir
            
            # Increment consecutive moves counter if same direction
            if self.direction == self.prev_direction:
                self.consecutive_moves += 1
            else:
                self.consecutive_moves = 0
            
            # Avoid loops by occasionally changing direction if many consecutive moves
            if self.consecutive_moves > 10 and random.random() < 0.5:  # More aggressive loop avoidance
                alternative_dirs = [d for d, _ in sorted_candidates if d != self.direction]
                if alternative_dirs:
                    self.direction = alternative_dirs[0]  # Take the highest-scoring alternative
                    self.consecutive_moves = 0


# =============================================================================
# GAME STATE CLASS
# =============================================================================

class GameState:
    """Manages the state of the game"""
    
    def __init__(self, width, height, num_snakes, human_player=False):
        self.width = width
        self.height = height
        self.num_snakes = min(num_snakes, Config.MAX_SNAKES)  # Respect max snakes setting
        self.human_player = human_player
        self.snakes = []
        self.foods = []
        self.power_ups = []
        self.temp_foods = []
        self.obstacles = []  # New list for obstacles
        self.death_counter = 1
        self.start_time = time.time()
        self.last_food_time = time.time()
        self.game_over = False
        self.paused = False
        self.game_speed = Config.BASE_SPEED
        self.speed_multiplier = 1.0
        self.last_speed_increase = time.time()
        self.last_food_eaten = time.time()
        self.current_leader = None  # Track the current leading snake
        self.frame_count = 0  # Track frames for visual effects
        self.difficulty = "Normal"  # Default difficulty
        self.special_event_timer = 0  # Timer for special events
        self.special_event_active = False  # Flag for special events
    
    def initialize_game(self):
        """Initialize game elements"""
        self.create_snakes()
        self.create_initial_food()
        
        # Create obstacles if enabled
        if Config.OBSTACLE_ENABLED:
            self.create_obstacles()
    
    def create_obstacles(self, avoid_positions=None):
        """Create obstacles on the board"""
        if not Config.OBSTACLE_ENABLED:
            return False
            
        # If this is the initial setup, clear all obstacles
        if avoid_positions is None:
            # Clear existing obstacles
            self.obstacles = []
            avoid_positions = set()
        
        # Create pair of wormholes (teleport points)
        if len(self.obstacles) == 0 and random.random() < 0.7:  # 70% chance to have wormholes on initial setup
            wormhole_positions = []
            
            # Try to find good positions for wormholes
            for _ in range(2):
                attempts = 0
                while attempts < 50:
                    x = random.randint(2, self.width - 3)
                    y = random.randint(2, self.height - 3)
                    pos = (x, y)
                    
                    # Check if position is clear and not in avoid_positions
                    if self.is_position_clear(pos, min_distance=10) and pos not in avoid_positions:
                        wormhole_positions.append(pos)
                        break
                    attempts += 1
            
            # Create linked wormholes if we found 2 good positions
            if len(wormhole_positions) == 2:
                wormhole1 = Obstacle(wormhole_positions[0], ObstacleType.WORMHOLE)
                wormhole2 = Obstacle(wormhole_positions[1], ObstacleType.WORMHOLE)
                
                # Link the wormholes to each other
                wormhole1.linked_position = wormhole_positions[1]
                wormhole2.linked_position = wormhole_positions[0]
                
                self.obstacles.append(wormhole1)
                self.obstacles.append(wormhole2)
        
        # Create a single random obstacle (for special events) or all obstacles (initial setup)
        obstacle_count = Config.OBSTACLE_COUNT if avoid_positions is None else 1
        
        for _ in range(obstacle_count):
            obstacle_type = random.choice([
                ObstacleType.WALL,
                ObstacleType.SPIKES,
                ObstacleType.SWAMP,
                ObstacleType.ENERGY_FIELD
            ])
            
            # Try to find a good position
            attempts = 0
            while attempts < 50:
                x = random.randint(2, self.width - 3)
                y = random.randint(2, self.height - 3)
                pos = (x, y)
                
                # Check if position is clear and not in avoid_positions
                if self.is_position_clear(pos) and pos not in avoid_positions:
                    # For walls and swamps, create a small cluster
                    if obstacle_type in [ObstacleType.WALL, ObstacleType.SWAMP]:
                        # Create a small cluster of this obstacle (smaller for special events)
                        cluster_size = random.randint(2, 4) if avoid_positions else random.randint(3, 6)
                        positions_created = self.create_obstacle_cluster(pos, obstacle_type, cluster_size, avoid_positions)
                        return len(positions_created) > 0  # Created successfully
                    else:
                        # Create a single obstacle
                        self.obstacles.append(Obstacle(pos, obstacle_type))
                        return True  # Created successfully
                attempts += 1
                
        return False  # Failed to create obstacle
    
    def create_obstacle_cluster(self, start_pos, obstacle_type, size, avoid_positions=None):
        """Create a cluster of obstacles"""
        if avoid_positions is None:
            avoid_positions = set()
            
        positions = [start_pos]
        added = {start_pos}
        created_obstacles = []
        
        # Add obstacles in a cluster
        for _ in range(size - 1):
            if not positions:
                break
                
            # Get a random position from our cluster to expand from
            base_pos = random.choice(positions)
            x, y = base_pos
            
            # Try to add an adjacent obstacle
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_pos = (x + dx, y + dy)
                
                # Check if position is valid and not already in the cluster
                if (2 <= new_pos[0] < self.width - 2 and 
                    2 <= new_pos[1] < self.height - 2 and
                    new_pos not in added and
                    new_pos not in avoid_positions and
                    self.is_position_clear(new_pos)):
                    
                    # Add the new position to our cluster
                    positions.append(new_pos)
                    added.add(new_pos)
                    new_obstacle = Obstacle(new_pos, obstacle_type)
                    self.obstacles.append(new_obstacle)
                    created_obstacles.append(new_obstacle)
                    break
        
        # Create the first obstacle (start position)
        if start_pos not in avoid_positions:
            start_obstacle = Obstacle(start_pos, obstacle_type)
            self.obstacles.append(start_obstacle)
            created_obstacles.append(start_obstacle)
            
        return created_obstacles
    
    def is_position_clear(self, pos, min_distance=3):
        """Check if a position is clear of other objects"""
        x, y = pos
        
        # Check if too close to other obstacles
        for obstacle in self.obstacles:
            ox, oy = obstacle.position
            if abs(ox - x) + abs(oy - y) < min_distance:
                return False
        
        # Check if too close to food
        for food in self.foods:
            fx, fy = food.position
            if abs(fx - x) + abs(fy - y) < min_distance:
                return False
        
        # Check if too close to power-ups
        for power_up in self.power_ups:
            px, py = power_up.position
            if abs(px - x) + abs(py - y) < min_distance:
                return False
        
        # Check if too close to snakes
        for snake in self.snakes:
            if not snake.alive:
                continue
                
            # Check distance to snake head
            sx, sy = snake.body[0]
            if abs(sx - x) + abs(sy - y) < min_distance:
                return False
        
        return True
    
    def create_snakes(self):
        """Create snakes based on configuration"""
        self.snakes = []
        
        # Create human player if selected
        if self.human_player:
            human_snake = Snake(
                body=[(self.width//2, self.height//2), 
                      (self.width//2-1, self.height//2), 
                      (self.width//2-2, self.height//2)],
                direction=Direction.RIGHT,
                id=1,
                is_human=True
            )
            self.snakes.append(human_snake)
            ai_snakes = self.num_snakes - 1
            strat_offset = 1
        else:
            ai_snakes = self.num_snakes
            strat_offset = 0
        
        # Create AI snakes with different strategies - favoring aggressive ones
        ai_strategies = list(AIStrategy)
        
        # Define aggressive strategies with higher weights for selection
        aggressive_strategies = [
            AIStrategy.AGGRESSIVE,
            AIStrategy.HUNTER,
            AIStrategy.BERSERKER,
            AIStrategy.KAMIKAZE,
            AIStrategy.INTERCEPTOR
        ]
        
        # Define tactical strategies with medium weights
        tactical_strategies = [
            AIStrategy.OPPORTUNISTIC,
            AIStrategy.TERRITORIAL,
            AIStrategy.TRAP_SETTER,
            AIStrategy.STALKER
        ]
        
        # Define defensive strategies with lower weights
        defensive_strategies = [
            AIStrategy.CAUTIOUS,
            AIStrategy.DEFENSIVE,
            AIStrategy.SCAVENGER,
            AIStrategy.POWERUP_SEEKER
        ]
        
        # Create a weighted strategy pool to favor more aggressive behavior
        weighted_strategies = []
        weighted_strategies.extend(aggressive_strategies * 5)  # 5x weight for aggressive
        weighted_strategies.extend(tactical_strategies * 3)    # 3x weight for tactical
        weighted_strategies.extend(defensive_strategies * 1)   # 1x weight for defensive
        
        # Ensure a good distribution of strategies for AI snakes
        if ai_snakes <= len(ai_strategies):
            # Guarantee at least one berserker and one kamikaze for excitement
            strategies = []
            if ai_snakes >= 2:
                strategies.append(AIStrategy.BERSERKER)
                strategies.append(AIStrategy.KAMIKAZE)
                # Fill the rest with weighted random selection
                strategies.extend(random.sample(weighted_strategies, ai_snakes - 2))
            else:
                # Just one snake - make it aggressive
                strategies = [random.choice(aggressive_strategies)]
        else:
            # Use all strategies at least once, then add extras with weighting
            strategies = ai_strategies.copy()
            remaining = ai_snakes - len(strategies)
            
            # Add extras based on weighted selection
            for _ in range(remaining):
                strategies.append(random.choice(weighted_strategies))
                
            random.shuffle(strategies)
        
        # Calculate optimal positions for many snakes
        # Use a quadrant-based approach for up to 20 snakes
        
        # Determine how many snakes to place per quadrant
        snakes_per_quadrant = max(1, ai_snakes // 4)
        remainder = ai_snakes % 4
        
        quadrants = [
            {'x_range': (self.width // 4, self.width // 2 - 5), 'y_range': (self.height // 4, self.height // 2 - 5), 'count': snakes_per_quadrant + (1 if remainder > 0 else 0)},
            {'x_range': (self.width // 2 + 5, 3 * self.width // 4), 'y_range': (self.height // 4, self.height // 2 - 5), 'count': snakes_per_quadrant + (1 if remainder > 1 else 0)},
            {'x_range': (self.width // 4, self.width // 2 - 5), 'y_range': (self.height // 2 + 5, 3 * self.height // 4), 'count': snakes_per_quadrant + (1 if remainder > 2 else 0)},
            {'x_range': (self.width // 2 + 5, 3 * self.width // 4), 'y_range': (self.height // 2 + 5, 3 * self.height // 4), 'count': snakes_per_quadrant},
        ]
        
        snake_idx = 0
        
        # Place snakes in each quadrant
        for q, quadrant in enumerate(quadrants):
            for i in range(quadrant['count']):
                if snake_idx >= ai_snakes:
                    break
                    
                # Calculate position within quadrant
                x_min, x_max = quadrant['x_range']
                y_min, y_max = quadrant['y_range']
                
                # Distribute snakes evenly within quadrant
                x_pos = x_min + (i * (x_max - x_min)) // max(1, quadrant['count'])
                y_pos = y_min + (i * (y_max - y_min)) // max(1, quadrant['count'])
                
                # Add some randomness to prevent collisions
                x_pos += random.randint(-3, 3)
                y_pos += random.randint(-3, 3)
                
                # Ensure position is within board boundaries
                x_pos = max(5, min(self.width - 6, x_pos))
                y_pos = max(5, min(self.height - 6, y_pos))
                
                # Determine direction based on quadrant
                if q == 0:
                    direction = Direction.RIGHT
                    snake_body = [(x_pos, y_pos), (x_pos-1, y_pos), (x_pos-2, y_pos)]
                elif q == 1:
                    direction = Direction.LEFT
                    snake_body = [(x_pos, y_pos), (x_pos+1, y_pos), (x_pos+2, y_pos)]
                elif q == 2:
                    direction = Direction.UP
                    snake_body = [(x_pos, y_pos), (x_pos, y_pos+1), (x_pos, y_pos+2)]
                else:
                    direction = Direction.DOWN
                    snake_body = [(x_pos, y_pos), (x_pos, y_pos-1), (x_pos, y_pos-2)]
                
                # Create snake with the assigned strategy
                snake = Snake(
                    body=snake_body,
                    direction=direction,
                    id=snake_idx+1+strat_offset,
                    strategy=strategies[snake_idx]
                )
                
                # For territorial strategy, set territory center
                if snake.strategy == AIStrategy.TERRITORIAL:
                    snake.territory_center = (x_pos, y_pos)
                    
                self.snakes.append(snake)
                snake_idx += 1
    
    def create_initial_food(self):
        """Create initial food items for game start"""
        for _ in range(Config.MIN_FOOD_COUNT):
            self.create_food()
        
        # Create one bonus food at start for excitement
        self.create_food(FoodType.BONUS)
    
    def create_food(self, food_type=FoodType.NORMAL):
        """Create a new food item in a valid location"""
        all_positions = set()
        
        # Collect positions of all objects
        for snake in self.snakes:
            all_positions.update(snake.body_set)
        all_positions.update(f.position for f in self.foods)
        all_positions.update(p.position for p in self.power_ups)
        all_positions.update(o.position for o in self.obstacles)  # Avoid obstacles too
        
        # Prevent food from spawning on the border
        border_positions = set()
        for x in range(self.width):
            border_positions.add((x, 0))
            border_positions.add((x, self.height - 1))
        for y in range(self.height):
            border_positions.add((0, y))
            border_positions.add((self.width - 1, y))
            
        all_positions.update(border_positions)
        
        # Try to find a valid position
        attempts = 0
        while attempts < 100:  # Limit attempts to avoid infinite loop
            pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
            if pos not in all_positions:
                break
            attempts += 1
            
        if attempts >= 100:
            # Fallback: try to find any free position
            for x in range(1, self.width-1):
                for y in range(1, self.height-1):
                    pos = (x, y)
                    if pos not in all_positions:
                        break
                else:
                    continue
                break
            else:
                # No free positions found, don't create food
                return None
        
        # Set appearance and points based on food type
        points = Config.FOOD_POINTS
        char = "*"
        color = 3
        
        if food_type == FoodType.BONUS:
            points = Config.BONUS_FOOD_POINTS
            char = "F"
            color = 3
        elif food_type == FoodType.DROPPED:
            points = Config.TEMP_FOOD_POINTS
            char = ":"
            color = 6
        
        food = Food(position=pos, type=food_type, points=points, char=char, color=color)
        self.foods.append(food)
        self.last_food_time = time.time()
        return food
    
    def create_power_up(self):
        """Create a new power-up item"""
        all_positions = set()
        
        # Avoid placing power-ups on snakes, food, other power-ups, or obstacles
        for snake in self.snakes:
            all_positions.update(snake.body_set)
        all_positions.update(f.position for f in self.foods)
        all_positions.update(p.position for p in self.power_ups)
        all_positions.update(f.position for f in self.temp_foods)
        all_positions.update(o.position for o in self.obstacles)  # Avoid obstacles too
        
        # Avoid borders
        border_positions = set()
        for x in range(self.width):
            border_positions.add((x, 0))
            border_positions.add((x, self.height - 1))
        for y in range(self.height):
            border_positions.add((0, y))
            border_positions.add((self.width - 1, y))
            
        all_positions.update(border_positions)
        
        # Try multiple times to find a good position
        attempts = 0
        while attempts < 50:
            pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
            if pos not in all_positions:
                break
            attempts += 1
            
        if attempts >= 50:
            return None  # Could not find a suitable position
        
        power_up = PowerUp(position=pos)
        self.power_ups.append(power_up)
        return power_up
    
    def drop_snake_as_food(self, snake):
        """Turn a defeated snake's body into food"""
        for pos in snake.body:
            self.temp_foods.append(Food(
                position=pos,
                type=FoodType.DROPPED,
                points=Config.TEMP_FOOD_POINTS,
                char=":",
                color=6
            ))
        snake.body = []
        snake.body_set = set()
    
    def update(self):
        """Update game state (move snakes, check collisions, etc.)"""
        if self.paused:
            return
        
        # Increment frame counter for visual effects
        self.frame_count += 1
        
        # Update game speed
        self.update_game_speed()
        
        # Update special event state
        self.update_special_event()
        
        # Make sure we have enough food
        while len(self.foods) < Config.MIN_FOOD_COUNT:
            self.create_food()
        
        # Check and update power-ups for each snake
        for snake in self.snakes:
            if snake.alive:
                snake.update_power_ups()
                
                # Apply magnetic effect for snakes with that power-up
                if snake.has_power_up(PowerUpType.MAGNETIC):
                    snake.apply_magnetic_pull(self.foods + self.temp_foods)
                
                # Apply food rain effect
                if snake.has_power_up(PowerUpType.FOOD_RAIN) and snake.body:
                    # Create food around the snake's head
                    if random.random() < 0.3:  # 30% chance each frame
                        head = snake.body[0]
                        
                        # Try to spawn food in a random nearby position
                        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), 
                                      (1, 1), (-1, -1), (1, -1), (-1, 1)]
                        
                        # Randomly select a direction
                        dx, dy = random.choice(directions)
                        pos = (head[0] + dx, head[1] + dy)
                        
                        # Check if position is valid (not on wall, snake, etc.)
                        all_positions = set()
                        for s in self.snakes:
                            all_positions.update(s.body_set)
                        
                        if (1 < pos[0] < self.width-1 and 
                            1 < pos[1] < self.height-1 and 
                            pos not in all_positions):
                            
                            self.foods.append(Food(
                                position=pos,
                                type=FoodType.NORMAL,
                                points=Config.FOOD_POINTS,
                                char="*",
                                color=3
                            ))
                
                # Apply acid trail effect
                if snake.has_power_up(PowerUpType.ACID_TRAIL) and len(snake.body) > 1:
                    # 10% chance each frame to leave an acid spot
                    if random.random() < 0.1 and len(snake.body) > 2:
                        # Create an acid spot at the snake's second segment
                        acid_pos = snake.body[1]
                        
                        # Store acid trails in a new attribute if needed
                        if not hasattr(self, 'acid_trails'):
                            self.acid_trails = []
                            
                        # Add acid trail with limited lifetime
                        self.acid_trails.append({
                            'position': acid_pos,
                            'created_by': snake.id,
                            'end_time': time.time() + 3  # 3 seconds lifetime
                        })
        
        # Check and process acid trails
        if hasattr(self, 'acid_trails'):
            current_time = time.time()
            active_trails = []
            
            for trail in self.acid_trails:
                # Keep only active trails
                if current_time < trail['end_time']:
                    active_trails.append(trail)
                    
                    # Check if any snake hit an acid trail (except creator)
                    for snake in self.snakes:
                        if snake.alive and snake.id != trail['created_by']:
                            if snake.body and snake.body[0] == trail['position']:
                                if not snake.has_power_up(PowerUpType.INVINCIBILITY) and not snake.has_power_up(PowerUpType.GHOST):
                                    # Snake hit acid, eliminate it
                                    snake.alive = False
                                    
                                    # Record death order for scoring
                                    snake.death_order = self.death_counter
                                    self.death_counter += 1
                                    
                                    # Drop snake as food after recording death
                                    self.drop_snake_as_food(snake)
            
            # Update the acid trails list
            self.acid_trails = active_trails
            
        # Create bonus food if enough time has passed
        if (len([f for f in self.foods if f.type == FoodType.BONUS]) == 0 and 
                time.time() - self.last_food_time > Config.FOOD_BONUS_DURATION):
            self.create_food(FoodType.BONUS)
        
        # Randomly create power-ups
        if random.random() < Config.POWER_UP_CHANCE:
            self.create_power_up()
        
        # Update current leader for ENFORCER strategy
        self.update_current_leader()
        
        # Move each snake and check collisions
        for snake in self.snakes:
            if not snake.alive:
                continue
                
            # Skip frozen snakes
            if snake.is_frozen():
                continue
            
            # Gather positions of other snakes
            other_positions = set()
            for other in self.snakes:
                if other is not snake and other.alive:
                    other_positions.update(other.body_set)
            
            # Move the snake
            new_head = snake.move(self.foods + self.temp_foods, other_positions, self.power_ups, self)
            
            # Skip if snake has no body or move returned None
            if new_head is None:
                continue
            
            # Check for power-ups
            has_invincibility = snake.has_power_up(PowerUpType.INVINCIBILITY)
            has_ghost = snake.has_power_up(PowerUpType.GHOST)
            has_teleport = snake.has_power_up(PowerUpType.TELEPORT)
            
            # Check wall collision (handling teleport and invincibility)
            hit_wall = (new_head[0] <= 0 or new_head[0] >= self.width - 1 or 
                      new_head[1] <= 0 or new_head[1] >= self.height - 1)
            
            if hit_wall:
                if has_teleport:
                    # Teleport to the opposite side
                    if new_head[0] <= 0:
                        new_head = (self.width - 2, new_head[1])
                    elif new_head[0] >= self.width - 1:
                        new_head = (1, new_head[1])
                    elif new_head[1] <= 0:
                        new_head = (new_head[0], self.height - 2)
                    elif new_head[1] >= self.height - 1:
                        new_head = (new_head[0], 1)
                    
                    # Update the snake's head position
                    snake.body[0] = new_head
                    
                    # Update the snake's body set
                    if new_head not in snake.body_set:
                        snake.body_set.add(new_head)
                elif not has_invincibility:
                    if self.kill_snake(snake):
                        continue
            
            # Check for obstacle collisions
            hit_obstacle = self.check_obstacle_collision(snake, new_head)
            if hit_obstacle:
                continue  # Snake has been handled (killed or teleported)
            
            # Check snake collision (unless ghost or invincible)
            hit_self = new_head in snake.body[1:]
            hit_other = new_head in other_positions
            
            if (hit_self and not has_invincibility) or (hit_other and not (has_ghost or has_invincibility)):
                if self.kill_snake(snake):
                    continue
            
            # Check for eating food
            ate_food = False
            for food in self.foods + self.temp_foods:
                if new_head == food.position:
                    ate_food = True
                    self.handle_food_eaten(snake, food)
                    break
            
            # Check for power-up collection
            for power_up in list(self.power_ups):
                if new_head == power_up.position:
                    self.handle_power_up_collected(snake, power_up)
                    break
            
            # Remove tail if didn't eat
            if not ate_food:
                snake.remove_tail()
            
            # Validate snake integrity after all modifications
            if Config.DEBUG_INTEGRITY and snake.alive:
                try:
                    snake.validate_body_integrity()
                except ValueError as e:
                    # Log the error but don't crash the game
                    # In a real scenario, you'd use proper logging
                    print(f"Integrity check failed for Snake {snake.id}: {e}")
                    # Force a resync to recover
                    snake._rebuild_body_set()
        
        # Final validation pass for all alive snakes
        if Config.DEBUG_INTEGRITY:
            for snake in self.snakes:
                if snake.alive and snake.body:
                    try:
                        snake.validate_body_integrity()
                    except ValueError as e:
                        print(f"Final check failed for Snake {snake.id}: {e}")
                        # Force a resync to recover
                        snake._rebuild_body_set()
        
        # Check if game is over
        self.check_game_over()
        
    def check_obstacle_collision(self, snake, head_pos):
        """Check if snake has collided with an obstacle and handle effects.
        
        IMPORTANT: This method does NOT mutate snake.body or snake.body_set.
        Teleportation is handled in Snake.move() before the head is added.
        This method only applies power-up effects and returns collision status.
        
        Returns: True if the snake hit a deadly obstacle, False otherwise.
        """
        for obstacle in self.obstacles:
            if head_pos == obstacle.position:
                effect = obstacle.get_effect()
                
                # Handle deadly obstacles
                if effect.get("deadly", False) and not snake.has_power_up(PowerUpType.INVINCIBILITY):
                    self.kill_snake(snake)
                    return True
                
                # Note: Teleport is now handled in Snake.move() BEFORE head insertion
                # This prevents phantom positions from being added
                
                # Handle speed effects (swamp, energy field)
                if "speed_multiplier" in effect:
                    multiplier = effect["speed_multiplier"]
                    if multiplier < 1.0:  # Slowing effect (swamp)
                        # Apply temporary slowing effect but don't override existing speed boost
                        if not snake.has_power_up(PowerUpType.SPEED_BOOST) and not snake.has_power_up(PowerUpType.WARP_DRIVE):
                            snake.add_power_up(PowerUpType.SPEED_BOOST)  # Override with slowing
                    elif multiplier > 1.0:  # Speeding effect (energy field)
                        # Apply temporary speed boost but don't override warp drive
                        if not snake.has_power_up(PowerUpType.SPEED_BOOST) and not snake.has_power_up(PowerUpType.WARP_DRIVE):
                            snake.add_power_up(PowerUpType.SPEED_BOOST)
                
        return False
        
    def update_current_leader(self):
        """Update the current leading snake based on score"""
        if not self.snakes:
            self.current_leader = None
            return
            
        # Find the snake with the highest score
        alive_snakes = [s for s in self.snakes if s.alive]
        if not alive_snakes:
            self.current_leader = None
            return
            
        leader = max(alive_snakes, key=lambda s: s.score)
        self.current_leader = leader
    
    def kill_snake(self, snake):
        """Handle snake death"""
        # Check if snake has shield
        if snake.has_shield():
            # Shield absorbs one fatal hit, then is removed
            if PowerUpType.SHIELD in snake.power_ups:
                del snake.power_ups[PowerUpType.SHIELD]
            return False  # Snake survived
            
        # Check if snake has time warp
        if snake.has_time_warp() and len(snake.body) > 3:
            # Instead of dying, teleport back to third segment
            safe_pos = snake.body[2] 
            snake.body = [safe_pos] + snake.body[3:]
            snake.body_set = set(snake.body)
            
            # Remove the time warp power-up
            if PowerUpType.TIME_WARP in snake.power_ups:
                del snake.power_ups[PowerUpType.TIME_WARP]
            
            return False  # Snake survived
        
        # No protective power-ups, snake dies
        snake.alive = False
        snake.death_order = self.death_counter
        self.death_counter += 1
        
        # Save the body before clearing it
        body_copy = list(snake.body)
        
        # Clear the snake's body data structures to avoid any issues
        snake.body = []
        snake.body_set.clear()
        
        # Now convert the saved body to food
        for pos in body_copy:
            self.temp_foods.append(Food(
                position=pos,
                type=FoodType.DROPPED,
                points=Config.TEMP_FOOD_POINTS,
                char=":",
                color=6
            ))
            
        return True  # Snake died
    
    def handle_food_eaten(self, snake, food):
        """Handle when a snake eats food"""
        # Update score based on food type and power-ups
        base_points = food.points
        if snake.has_power_up(PowerUpType.SCORE_MULTIPLIER):
            base_points *= 2
        
        snake.score += base_points
        
        # Make the snake longer
        snake.gets_longer(food.type)
        
        # Remove the food
        if food in self.foods:
            self.foods.remove(food)
            # Create a new food if normal/bonus food was eaten
            self.create_food()
        elif food in self.temp_foods:
            self.temp_foods.remove(food)
        
        # Reset food eaten time
        self.last_food_eaten = time.time()
        
        # Small chance to trigger special event when eating bonus food
        if food.type == FoodType.BONUS and random.random() < 0.2:
            self.trigger_special_event()
            
    def trigger_special_event(self):
        """Trigger a special game event for more dynamic gameplay"""
        if self.special_event_active:
            return  # Don't trigger another event if one is active
            
        self.special_event_active = True
        self.special_event_timer = 50  # Event duration in frames
        
        # Choose a random event
        event_type = random.randint(1, 5)
        
        if event_type == 1:
            # Power-up rain - spawn multiple power-ups
            for _ in range(random.randint(3, 6)):
                # Create power-ups in safe locations
                attempts = 0
                while attempts < 20:
                    valid_position = self.create_power_up()
                    if valid_position:
                        break
                    attempts += 1
                
        elif event_type == 2:
            # Food frenzy - spawn lots of bonus food
            for _ in range(random.randint(5, 10)):
                # Create food in safe locations
                attempts = 0
                while attempts < 20:
                    valid_position = self.create_food(FoodType.BONUS)
                    if valid_position:
                        break
                    attempts += 1
                
        elif event_type == 3:
            # Speed burst - temporarily increase game speed
            self.speed_multiplier *= 1.5
            
        elif event_type == 4:
            # Snake swap - randomize AI strategies
            for snake in self.snakes:
                if not snake.is_human and snake.alive:
                    # Change to a random strategy
                    snake.strategy = random.choice(list(AIStrategy))
                    
        elif event_type == 5:
            # Obstacle shift - remove and recreate obstacles
            if Config.OBSTACLE_ENABLED:
                # Save snake positions to avoid placing obstacles on them
                snake_positions = set()
                for snake in self.snakes:
                    if snake.alive:
                        snake_positions.update(snake.body)
                
                # Clear obstacles
                self.obstacles = []
                
                # Recreate obstacles, avoiding snake positions
                attempts = 0
                obstacles_created = 0
                max_attempts = 50
                
                while obstacles_created < Config.OBSTACLE_COUNT and attempts < max_attempts:
                    # Create obstacles in safe locations
                    if self.create_obstacles(snake_positions):
                        obstacles_created += 1
                    attempts += 1
                
    def update_special_event(self):
        """Update special event state"""
        if not self.special_event_active:
            return
            
        self.special_event_timer -= 1
        
        if self.special_event_timer <= 0:
            # End the special event
            self.special_event_active = False
            
            # Reset any temporary effects
            if self.speed_multiplier > 2.0:  # Likely from a speed burst event
                self.speed_multiplier = max(1.0, self.speed_multiplier / 1.5)
    
    def handle_power_up_collected(self, snake, power_up):
        """Handle when a snake collects a power-up"""
        # Store the power-up type before removing it from the list
        power_up_type = power_up.type
        
        # Remove the power-up first to avoid collision detection issues
        self.power_ups.remove(power_up)
        
        # Apply the power-up effect after removing it
        snake.add_power_up(power_up_type)
    
    def check_game_over(self):
        """Check if game is over (all snakes dead)"""
        if not any(snake.alive for snake in self.snakes):
            self.game_over = True
    
    def update_game_speed(self):
        """Update game speed based on time and events"""
        current_time = time.time()
        
        # Increase speed over time
        if current_time - self.last_speed_increase > Config.SPEED_INCREASE_INTERVAL:
            self.speed_multiplier = min(Config.MAX_SPEED_MULTIPLIER, 
                                        self.speed_multiplier + 0.1)
            self.last_speed_increase = current_time
        
        # Speed up if no food has been eaten for a while
        if current_time - self.last_food_eaten > Config.MAX_IDLE_TIME:
            idle_factor = min(2.0, 1.0 + ((current_time - self.last_food_eaten) / Config.MAX_IDLE_TIME))
            self.speed_multiplier = min(Config.MAX_SPEED_MULTIPLIER, self.speed_multiplier * idle_factor)
            # Reset the timer to avoid compounding speed
            self.last_food_eaten = current_time - Config.MAX_IDLE_TIME
        
        # Calculate effective speed (lower number = faster game)
        self.game_speed = Config.BASE_SPEED / self.speed_multiplier


# =============================================================================
# UI RENDERER CLASS
# =============================================================================

class Renderer:
    """Handles all rendering operations"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()
    
    def setup_colors(self):
        """Initialize color pairs"""
        curses.start_color()
        curses.use_default_colors()
        
        # Initialize all color pairs - expanded to 20 for more snakes
        # Base colors
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake1
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Snake2
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)      # Food
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Snake3
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Snake4
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Temp food
        curses.init_pair(7, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Snake5
        
        # Additional color pairs for more snakes - using combinations of colors and attributes
        curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLACK)      # Snake6
        curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake7
        curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Snake8
        curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Snake9
        curses.init_pair(12, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Snake10
        curses.init_pair(13, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Snake11
        curses.init_pair(14, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Snake12
        curses.init_pair(15, curses.COLOR_RED, curses.COLOR_BLACK)     # Snake13
        curses.init_pair(16, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Snake14
        curses.init_pair(17, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Snake15
        curses.init_pair(18, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Snake16
        curses.init_pair(19, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Snake17
        curses.init_pair(20, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Snake18
    
    def get_snake_color(self, snake_id):
        """Get color for a snake with attributes for variety"""
        # Use modulo to cycle through color pairs
        color_pair = (snake_id % 7) + 1
        
        # Add attributes based on id to create more visual variety
        attrs = 0
        if snake_id > 7 and snake_id <= 14:
            attrs |= curses.A_BOLD
        elif snake_id > 14:
            attrs |= curses.A_REVERSE
            
        return curses.color_pair(color_pair) | attrs
    
    def safe_addch(self, y, x, ch, attr=0):
        """Safely add a character to the screen"""
        try:
            self.stdscr.addch(y, x, ch, attr)
        except curses.error:
            pass
    
    def safe_addstr(self, y, x, string, attr=0):
        """Safely add a string to the screen"""
        try:
            self.stdscr.addstr(y, x, string, attr)
        except curses.error:
            pass
    
    def draw_board(self, game_state):
        """Draw the game board with all elements"""
        self.stdscr.clear()
        
        # Draw border with enhanced visuals
        if Config.ENHANCED_VISUALS:
            border_style = self.get_border_style(game_state)
            for x in range(game_state.width):
                self.safe_addch(1, x, border_style['horizontal'], border_style['color'] | border_style['attr'])
                self.safe_addch(game_state.height, x, border_style['horizontal'], border_style['color'] | border_style['attr'])
            for y in range(1, game_state.height + 1):
                self.safe_addch(y, 0, border_style['vertical'], border_style['color'] | border_style['attr'])
                self.safe_addch(y, game_state.width-1, border_style['vertical'], border_style['color'] | border_style['attr'])
            
            # Draw corners
            self.safe_addch(1, 0, border_style['top_left'], border_style['color'] | border_style['attr'])
            self.safe_addch(1, game_state.width-1, border_style['top_right'], border_style['color'] | border_style['attr'])
            self.safe_addch(game_state.height, 0, border_style['bottom_left'], border_style['color'] | border_style['attr'])
            self.safe_addch(game_state.height, game_state.width-1, border_style['bottom_right'], border_style['color'] | border_style['attr'])
        else:
            # Traditional border
            border_color = curses.color_pair(0)
            for x in range(game_state.width):
                self.safe_addch(1, x, '#', border_color)
                self.safe_addch(game_state.height, x, '#', border_color)
            for y in range(1, game_state.height + 1):
                self.safe_addch(y, 0, '#', border_color)
                self.safe_addch(y, game_state.width-1, '#', border_color)
        
        # Draw obstacles
        for obstacle in game_state.obstacles:
            obstacle_color = curses.color_pair(obstacle.color)
            attrs = 0
            
            # Add visual effects for certain obstacle types
            if obstacle.type == ObstacleType.WORMHOLE:
                attrs |= curses.A_BOLD
                if game_state.frame_count % 10 < 5:  # Animation effect
                    attrs |= curses.A_BLINK
            elif obstacle.type == ObstacleType.ENERGY_FIELD:
                if game_state.frame_count % 6 < 3:  # Alternate characters for animation
                    self.safe_addch(obstacle.position[1] + 1, obstacle.position[0], "≡", obstacle_color | attrs)
                else:
                    self.safe_addch(obstacle.position[1] + 1, obstacle.position[0], "≣", obstacle_color | attrs)
                continue
                
            self.safe_addch(obstacle.position[1] + 1, obstacle.position[0], obstacle.char, obstacle_color | attrs)
        
        # Draw food
        for food in game_state.foods:
            food_color = curses.color_pair(food.color)
            attributes = curses.A_BLINK if food.type == FoodType.BONUS else 0
            
            # Enhance visuals for bonus food
            if Config.ENHANCED_VISUALS and food.type == FoodType.BONUS:
                if game_state.frame_count % 10 < 5:
                    self.safe_addch(food.position[1] + 1, food.position[0], "★", food_color | curses.A_BOLD)
                else:
                    self.safe_addch(food.position[1] + 1, food.position[0], "☆", food_color | curses.A_BOLD)
            else:
                self.safe_addch(food.position[1] + 1, food.position[0], food.char, food_color | attributes)
        
        # Draw temporary foods
        for food in game_state.temp_foods:
            temp_color = curses.color_pair(food.color)
            # Special animation for temporary food if enhanced visuals are enabled
            if Config.ENHANCED_VISUALS and game_state.frame_count % 6 < 3:
                self.safe_addch(food.position[1] + 1, food.position[0], "·", temp_color | curses.A_DIM)
            else:
                self.safe_addch(food.position[1] + 1, food.position[0], food.char, temp_color)
        
        # Draw power-ups with enhanced visuals
        for power_up in game_state.power_ups:
            power_up_color = curses.color_pair(power_up.color)
            
            # Get additional attributes for this power-up
            if Config.ENHANCED_VISUALS:
                attrs = power_up.get_display_attributes(game_state)
                
                # Special animation for rare power-ups
                if power_up.rarity == "rare" and game_state.frame_count % 10 < 5:
                    char = "✧" if power_up.char == "✦" else "✦"
                    self.safe_addch(power_up.position[1] + 1, power_up.position[0], char, 
                                 power_up_color | attrs)
                    continue
            else:
                attrs = curses.A_BLINK
                
            self.safe_addch(power_up.position[1] + 1, power_up.position[0], power_up.char, 
                           power_up_color | attrs)
        
        # Draw snakes
        for snake in game_state.snakes:
            if not snake.alive:
                continue
            
            snake_color = self.get_snake_color(snake.id)
            
            # Add special attributes for power-ups
            attrs = 0
            head_char = 'H'
            body_char = 'o'
            
            # Apply power-up visual effects
            if snake.power_ups:
                attrs |= curses.A_BOLD
                
                # Invincibility effect
                if snake.has_power_up(PowerUpType.INVINCIBILITY):
                    attrs |= curses.A_BLINK
                    head_char = '@'
                
                # Ghost effect    
                if snake.has_power_up(PowerUpType.GHOST):
                    body_char = '░'
                    
                # Speed boost effect
                if snake.has_power_up(PowerUpType.SPEED_BOOST):
                    head_char = '>'
                
                # Warp drive effect
                if snake.has_power_up(PowerUpType.WARP_DRIVE):
                    head_char = '⚡'
                    body_char = '~'
                
                # Magnetic effect
                if snake.has_power_up(PowerUpType.MAGNETIC):
                    head_char = 'Ω'
                
                # Shrink effect
                if snake.has_power_up(PowerUpType.SHRINK):
                    body_char = '.'
                
                # Vision effect
                if snake.has_power_up(PowerUpType.VISION):
                    head_char = 'V'
                
                # Teleport effect
                if snake.has_power_up(PowerUpType.TELEPORT):
                    head_char = 'T'
                
                # Freeze effect - unlikely but possible if snake collected it and then got frozen
                if snake.is_frozen():
                    attrs |= curses.A_DIM
                    head_char = 'F'
                
                # Confusion effect
                if snake.has_power_up(PowerUpType.CONFUSION):
                    head_char = '?'
                
                # Reverse effect
                if snake.has_power_up(PowerUpType.REVERSE):
                    head_char = 'R'
            
            # Special effect for the leader snake
            if snake == game_state.current_leader and Config.ENHANCED_VISUALS:
                attrs |= curses.A_BOLD
                # Cycle colors for the leader's head
                if Config.COLOR_CYCLING:
                    cycle_color = (game_state.frame_count // 5) % 7 + 1
                    leader_color = curses.color_pair(cycle_color) | attrs
                    self.safe_addch(snake.body[0][1] + 1, snake.body[0][0], '★', leader_color)
                    
                    # Draw rest of body
                    for i, cell in enumerate(snake.body[1:], 1):
                        self.safe_addch(cell[1] + 1, cell[0], body_char, snake_color | attrs)
                    
                    continue  # Skip normal snake drawing
            
            # Draw each segment
            for i, cell in enumerate(snake.body):
                char = head_char if i == 0 else body_char
                self.safe_addch(cell[1] + 1, cell[0], char, snake_color | attrs)
        
        # Draw status bar
        self.draw_status_bar(game_state)
        
        # Draw help text with enhanced visuals
        if Config.ENHANCED_VISUALS:
            help_text = "P: Pause | Q: Quit | Arrow Keys: Move | Space: Special Event"
            help_color = curses.color_pair(6) | curses.A_BOLD
        else:
            help_text = "P: Pause | Q: Quit | Arrow Keys: Move"
            help_color = curses.color_pair(6)
            
        self.safe_addstr(game_state.height + 1, 1, help_text, help_color)
        
        # Draw paused indicator
        if game_state.paused:
            if Config.ENHANCED_VISUALS:
                # Enhanced pause screen
                pause_box_width = 30
                pause_box_height = 5
                start_x = (game_state.width - pause_box_width) // 2
                start_y = (game_state.height - pause_box_height) // 2
                
                # Draw box
                for y in range(pause_box_height):
                    for x in range(pause_box_width):
                        if (y == 0 or y == pause_box_height - 1) or (x == 0 or x == pause_box_width - 1):
                            self.safe_addch(start_y + y, start_x + x, '█', curses.color_pair(7))
                        else:
                            self.safe_addch(start_y + y, start_x + x, ' ', curses.A_REVERSE)
                
                # Draw text
                pause_text = "GAME PAUSED"
                self.safe_addstr(start_y + 1, start_x + (pause_box_width - len(pause_text)) // 2, 
                                pause_text, curses.A_BOLD | curses.A_REVERSE)
                
                help_text = "Press P to continue"
                self.safe_addstr(start_y + 3, start_x + (pause_box_width - len(help_text)) // 2, 
                                help_text, curses.A_REVERSE)
            else:
                # Simple pause text
                pause_text = "PAUSED - Press P to continue"
                self.safe_addstr(game_state.height // 2, 
                                (game_state.width - len(pause_text)) // 2,
                                pause_text, curses.A_BOLD | curses.A_REVERSE)
        
        self.stdscr.refresh()
        
    def get_border_style(self, game_state):
        """Get border style based on game state and frame count"""
        style = {
            'horizontal': '═',
            'vertical': '║',
            'top_left': '╔',
            'top_right': '╗',
            'bottom_left': '╚',
            'bottom_right': '╝',
            'color': curses.color_pair(7),
            'attr': curses.A_NORMAL
        }
        
        # Change color based on frame count if color cycling is enabled
        if Config.COLOR_CYCLING:
            cycle_color = (game_state.frame_count // 20) % 7 + 1
            style['color'] = curses.color_pair(cycle_color)
        
        # Add special effects based on game state
        if game_state.special_event_active:
            style['attr'] |= curses.A_BOLD
            if game_state.frame_count % 10 < 5:
                style['attr'] |= curses.A_BLINK
                
        return style
    
    def draw_status_bar(self, game_state):
        """Draw status bar with game information"""
        # Calculate game duration
        game_duration = time.time() - game_state.start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        
        # Prepare status text
        speed = f"Speed: {game_state.speed_multiplier:.1f}x"
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        alive_count = sum(1 for s in game_state.snakes if s.alive)
        count_str = f"Snakes: {alive_count}/{len(game_state.snakes)}"
        difficulty = f"Difficulty: {game_state.difficulty}"
        
        # Draw status bar background with enhanced visuals
        if Config.ENHANCED_VISUALS:
            # Use a gradient or special color for status bar
            status_color = curses.color_pair(7) | curses.A_BOLD
            
            # Draw status bar border
            for x in range(game_state.width):
                self.safe_addch(0, x, '▁', status_color)
        else:
            # Traditional status bar
            status_color = curses.color_pair(0)
            for x in range(game_state.width):
                self.safe_addch(0, x, ' ', status_color)
        
        # Draw status text components
        self.safe_addstr(0, 1, time_str, status_color)
        self.safe_addstr(0, game_state.width // 4, count_str, status_color)
        self.safe_addstr(0, 2 * game_state.width // 4, speed, status_color)
        self.safe_addstr(0, 3 * game_state.width // 4, difficulty, status_color)
        
        # Draw active powerups indicator for human player if enhanced visuals enabled
        if Config.ENHANCED_VISUALS and game_state.human_player:
            human_snake = next((s for s in game_state.snakes if s.is_human and s.alive), None)
            if human_snake and human_snake.power_ups:
                powerup_text = "Active Power-ups: "
                powerup_indicators = []
                
                for power_up_type in human_snake.power_ups:
                    if power_up_type == PowerUpType.SPEED_BOOST:
                        powerup_indicators.append("S")
                    elif power_up_type == PowerUpType.INVINCIBILITY:
                        powerup_indicators.append("I")
                    elif power_up_type == PowerUpType.GHOST:
                        powerup_indicators.append("G")
                    elif power_up_type == PowerUpType.GROWTH:
                        powerup_indicators.append("+")
                    elif power_up_type == PowerUpType.SCORE_MULTIPLIER:
                        powerup_indicators.append("M")
                    elif power_up_type == PowerUpType.SHRINK:
                        powerup_indicators.append("-")
                    elif power_up_type == PowerUpType.MAGNETIC:
                        powerup_indicators.append("Ω")
                    elif power_up_type == PowerUpType.FREEZE:
                        powerup_indicators.append("F")
                    elif power_up_type == PowerUpType.TELEPORT:
                        powerup_indicators.append("T")
                    elif power_up_type == PowerUpType.VISION:
                        powerup_indicators.append("V")
                    elif power_up_type == PowerUpType.CONFUSION:
                        powerup_indicators.append("C")
                    elif power_up_type == PowerUpType.REVERSE:
                        powerup_indicators.append("R")
                    elif power_up_type == PowerUpType.WARP_DRIVE:
                        powerup_indicators.append("W")
                
                # Draw power-up indicators
                if powerup_indicators:
                    powerup_text += ", ".join(powerup_indicators)
                    powerup_color = curses.color_pair(5) | curses.A_BOLD
                    
                    # Calculate where to place the text (centered below the status bar)
                    y_pos = game_state.height + 2  # Below the help text
                    x_pos = max(1, (game_state.width - len(powerup_text)) // 2)
                    
                    self.safe_addstr(y_pos, x_pos, powerup_text, powerup_color)
        
        # Draw each snake's score if alive
        # For large games, draw scores in compact format
        if len(game_state.snakes) <= 6:
            # Standard display for few snakes
            y_pos = 2
            for snake in sorted(game_state.snakes, key=lambda s: s.score, reverse=True):
                if not snake.alive:
                    continue
                
                snake_color = self.get_snake_color(snake.id)
                
                # Show snake ID and score
                snake_type = "Human" if snake.is_human else f"AI-{snake.strategy.name}"
                power_ups = ""
                if snake.power_ups:
                    power_up_chars = {
                        PowerUpType.SPEED_BOOST: "⚡",
                        PowerUpType.INVINCIBILITY: "★",
                        PowerUpType.GHOST: "👻",
                        PowerUpType.GROWTH: "↑",
                        PowerUpType.SCORE_MULTIPLIER: "×2"
                    }
                    power_ups = " " + "".join(power_up_chars.get(p, "") for p in snake.power_ups)
                
                score_text = f"Snake {snake.id} ({snake_type}): {snake.score}{power_ups}"
                self.safe_addstr(y_pos, 1, score_text, snake_color)
                y_pos += 1
        else:
            # Compact display for many snakes - show as grid
            max_per_line = min(8, (game_state.width - 4) // 10)
            alive_snakes = [s for s in game_state.snakes if s.alive]
            
            for i, snake in enumerate(sorted(alive_snakes, key=lambda s: s.score, reverse=True)):
                row = i // max_per_line
                col = i % max_per_line
                
                x_pos = 1 + col * 10
                y_pos = 2 + row
                
                snake_color = self.get_snake_color(snake.id)
                score_text = f"S{snake.id}:{snake.score}"
                
                # Add power-up indicators
                if snake.power_ups:
                    for p in snake.power_ups:
                        if p == PowerUpType.INVINCIBILITY:
                            score_text += "*"
                        elif p == PowerUpType.GHOST:
                            score_text += "g"
                
                self.safe_addstr(y_pos, x_pos, score_text, snake_color)
    
    def draw_title_screen(self, width, height):
        """Draw the title screen"""
        self.stdscr.clear()
        
        title = "ULTIMATE SNAKE SHOWDOWN"
        subtitle = "A Battle of Serpentine Supremacy"
        author = "By ShadowHarvy, Enhanced with Smarter AI"
        options = [
            "2 Snakes", "4 Snakes", "6 Snakes", "8 Snakes", "10 Snakes", 
            "12 Snakes", "14 Snakes", "16 Snakes", "18 Snakes", "20 Snakes",
            "Human + AI", "Exit"
        ]
        
        # Draw title and subtitle
        title_color = curses.color_pair(4) | curses.A_BOLD
        subtitle_color = curses.color_pair(6)
        
        self.safe_addstr(height//4, (width - len(title))//2, title, title_color)
        self.safe_addstr(height//4 + 1, (width - len(subtitle))//2, subtitle, subtitle_color)
        self.safe_addstr(height//4 + 2, (width - len(author))//2, author)
        
        # Draw snake decoration
        snake_art = [
            "    _________         _________",
            "   /         \\       /         \\",
            "  /  /~~~~~~~\\\\     /  /~~~~~~~\\\\",
            " /  /        _\\\\   /  /        _\\\\",
            "|  |        /  || |  |        /  ||",
            "|  |       |   || |  |       |   ||",
            "|  |       |   || |  |       |   ||",
            " \\  \\      |  //   \\  \\      |  //",
            "  \\  ~~~~~  //     \\  ~~~~~  //",
            "   \\_______//       \\_______//",
        ]
        
        for i, line in enumerate(snake_art):
            color = curses.color_pair(i % 5 + 1)
            self.safe_addstr(height//4 + 4 + i, (width - len(line))//2, line, color)
        
        return options
    
    def draw_menu_options(self, options, selected, start_y, width):
        """Draw menu options with selected item highlighted"""
        # For many options, draw in multiple columns
        if len(options) > 10:
            items_per_col = (len(options) + 1) // 2
            for idx, option in enumerate(options):
                col = idx // items_per_col
                row = idx % items_per_col
                
                x_pos = width//3 + col * (width//3)
                y_pos = start_y + row
                
                attr = curses.A_REVERSE if idx == selected else 0
                self.safe_addstr(y_pos, x_pos - len(option)//2, option, attr)
        else:
            # Original single column display
            for idx, option in enumerate(options):
                attr = curses.A_REVERSE if idx == selected else 0
                self.safe_addstr(start_y + idx, (width - len(option))//2, option, attr)
    
    def draw_ranking_screen(self, ranking, start_time, width, height):
        """Draw the ranking screen"""
        self.stdscr.clear()
        
        # Draw header
        self.safe_addstr(2, width//2 - 4, "GAME OVER", curses.A_BOLD | curses.color_pair(3))
        self.safe_addstr(3, width//2 - 3, "RANKING", curses.A_BOLD)
        
        # Calculate game duration
        end_time = time.time()
        game_duration = end_time - start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        
        # Display game duration
        time_str = f"Game Duration: {minutes:02d}:{seconds:02d}"
        self.safe_addstr(4, (width - len(time_str))//2, time_str)
        
        # For large games, show top performers and compact display
        if len(ranking) > 10:
            # Top performers
            self.safe_addstr(6, width//4, "TOP PERFORMERS", curses.A_BOLD)
            
            # Display top 5 snakes
            for idx, snake in enumerate(ranking[:5]):
                rank = idx + 1
                snake_type = "Human" if snake.is_human else f"AI ({snake.strategy.name})"
                status = "ALIVE" if snake.alive else f"Died #{snake.death_order}"
                line = f"Rank {rank}: Snake {snake.id} ({snake_type}) - Score: {snake.score} - {status}"
                
                snake_color = self.get_snake_color(snake.id)
                if snake.alive:
                    snake_color |= curses.A_BOLD
                    
                self.safe_addstr(7 + idx, width//4, line, snake_color)
            
            # Display additional rankings in a compact table
            self.safe_addstr(6, 3*width//4, "OTHER SNAKES", curses.A_BOLD)
            
            # Create a compact table for remaining snakes
            for idx, snake in enumerate(ranking[5:15]):
                rank = idx + 6
                snake_type = "H" if snake.is_human else "AI"
                status = "A" if snake.alive else f"D{snake.death_order}"
                line = f"R{rank}: S{snake.id} ({snake_type}) - {snake.score} - {status}"
                
                snake_color = self.get_snake_color(snake.id)
                if snake.alive:
                    snake_color |= curses.A_BOLD
                    
                row = idx // 2
                col = idx % 2
                
                x_pos = 3*width//4 + col * (width//6)
                y_pos = 7 + row
                
                self.safe_addstr(y_pos, x_pos, line, snake_color)
                
            # Indicate if there are more snakes not shown
            if len(ranking) > 15:
                self.safe_addstr(12, 3*width//4, f"+ {len(ranking) - 15} more snakes", curses.A_DIM)
        else:
            # Display snake information in the standard way for smaller games
            for idx, snake in enumerate(ranking):
                rank = idx + 1
                snake_type = "Human" if snake.is_human else f"AI ({snake.strategy.name})"
                status = "ALIVE" if snake.alive else f"Died #{snake.death_order}"
                line = f"Rank {rank}: Snake {snake.id} ({snake_type}) - Score: {snake.score} - {status}"
                
                snake_color = self.get_snake_color(snake.id)
                if snake.alive:
                    snake_color |= curses.A_BOLD
                    
                self.safe_addstr(6 + idx, (width - len(line))//2, line, snake_color)
        
        # Draw restart/exit options
        options = ["Restart", "Exit"]
        return options
    
    def draw_game_over_screen(self, snakes, width, height):
        """Draw the game over screen"""
        self.stdscr.clear()
        
        # Determine winner
        alive_snakes = [s for s in snakes if s.alive]
        if len(alive_snakes) == 1:
            winner = alive_snakes[0]
            result = f"Snake {winner.id} wins!"
            color = self.get_snake_color(winner.id)
        elif len(alive_snakes) > 1:
            # Multiple survivors, highest score wins
            winner = max(alive_snakes, key=lambda s: s.score)
            result = f"Snake {winner.id} wins with highest score!"
            color = self.get_snake_color(winner.id)
        else:
            # No survivors, highest score from all snakes
            winner = max(snakes, key=lambda s: s.score)
            result = f"All snakes died! Snake {winner.id} had the highest score."
            color = self.get_snake_color(winner.id)
        
        # Draw result
        self.safe_addstr(height//3, (width - len("GAME OVER"))//2, "GAME OVER", curses.A_BOLD | curses.color_pair(3))
        self.safe_addstr(height//3 + 2, (width - len(result))//2, result, color | curses.A_BOLD)
        
        # Show winner's strategy if AI
        if not winner.is_human:
            strategy_text = f"Winning strategy: {winner.strategy.name}"
            self.safe_addstr(height//3 + 3, (width - len(strategy_text))//2, strategy_text, color)
        
        # Draw options
        options = ["See Rankings", "Restart", "Exit"]
        return options


# =============================================================================
# MENU SYSTEM CLASS
# =============================================================================

class MenuSystem:
    """Advanced menu system for the game"""
    
    def __init__(self, stdscr, renderer, screen_width, screen_height):
        self.stdscr = stdscr
        self.renderer = renderer
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_menu = "main"
        self.settings = {
            "difficulty": "Normal",
            "sound": "On",
            "theme": "Classic",
            "game_speed": 1.0
        }
        
    def draw_menu_border(self, title):
        """Draw a decorative border around the menu"""
        # Draw box border
        box_width = min(60, self.screen_width - 4)
        box_height = min(20, self.screen_height - 4)
        
        start_x = (self.screen_width - box_width) // 2
        start_y = (self.screen_height - box_height) // 2
        
        # Draw horizontal borders
        for x in range(start_x, start_x + box_width):
            self.renderer.safe_addch(start_y, x, '═', curses.color_pair(4))
            self.renderer.safe_addch(start_y + box_height, x, '═', curses.color_pair(4))
            
        # Draw vertical borders
        for y in range(start_y + 1, start_y + box_height):
            self.renderer.safe_addch(y, start_x, '║', curses.color_pair(4))
            self.renderer.safe_addch(y, start_x + box_width - 1, '║', curses.color_pair(4))
            
        # Draw corners
        self.renderer.safe_addch(start_y, start_x, '╔', curses.color_pair(4))
        self.renderer.safe_addch(start_y, start_x + box_width - 1, '╗', curses.color_pair(4))
        self.renderer.safe_addch(start_y + box_height, start_x, '╚', curses.color_pair(4))
        self.renderer.safe_addch(start_y + box_height, start_x + box_width - 1, '╝', curses.color_pair(4))
        
        # Draw title
        title_x = start_x + (box_width - len(title) - 2) // 2
        self.renderer.safe_addstr(start_y, title_x, f" {title} ", curses.color_pair(4) | curses.A_BOLD)
        
        return (start_x, start_y, box_width, box_height)
        
    def display_menu(self, options, selected, title):
        """Display a menu with options"""
        self.stdscr.clear()
        
        # Draw decorative border
        border_info = self.draw_menu_border(title)
        start_x, start_y, box_width, box_height = border_info
        
        # Calculate starting position for the menu items
        menu_start_y = start_y + 3
        
        # Draw help text at the bottom
        help_text = "↑↓: Navigate   Enter: Select   Esc: Back"
        help_x = (self.screen_width - len(help_text)) // 2
        self.renderer.safe_addstr(start_y + box_height - 1, help_x, help_text, curses.color_pair(6))
        
        # Draw options
        for idx, option in enumerate(options):
            # Check if this is a menu category header
            if option.startswith("--"):
                # It's a header, draw it differently
                header_text = option[2:]  # Remove the -- prefix
                self.renderer.safe_addstr(menu_start_y + idx, start_x + (box_width - len(header_text)) // 2, header_text, 
                                         curses.A_BOLD | curses.color_pair(5))
            else:
                # Regular menu option
                option_x = start_x + 4
                
                # For settings options, show current value
                if ":" in option:
                    option_parts = option.split(":", 1)
                    option_text = option_parts[0].strip()
                    option_value = option_parts[1].strip()
                    
                    # Draw the option text
                    attr = curses.A_REVERSE if idx == selected else 0
                    self.renderer.safe_addstr(menu_start_y + idx, option_x, option_text, attr)
                    
                    # Draw the value with a different style
                    value_x = option_x + len(option_text) + 2
                    value_attr = curses.color_pair(3) | (curses.A_REVERSE if idx == selected else 0)
                    self.renderer.safe_addstr(menu_start_y + idx, value_x, option_value, value_attr)
                else:
                    # Standard option
                    attr = curses.A_REVERSE if idx == selected else 0
                    self.renderer.safe_addstr(menu_start_y + idx, option_x, option, attr)
                    
                    # If this is a selected option, add a cursor indicator
                    if idx == selected:
                        self.renderer.safe_addstr(menu_start_y + idx, option_x - 2, ">", curses.color_pair(2))
        
        self.stdscr.refresh()
        
    def handle_menu_input(self, options):
        """Handle user input for menu navigation"""
        # Calculate which options are selectable (not headers)
        selectable_indices = [i for i, opt in enumerate(options) if not opt.startswith("--")]
        if not selectable_indices:
            return -1  # No selectable options
            
        selected_idx = selectable_indices[0]  # Start with first selectable option
        
        while True:
            # Get current position in selectable options list
            current_position = selectable_indices.index(selected_idx)
            
            # Display the menu
            self.display_menu(options, selected_idx, self.get_menu_title())
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                # Move to previous selectable option
                if current_position > 0:
                    selected_idx = selectable_indices[current_position - 1]
                else:
                    selected_idx = selectable_indices[-1]  # Wrap around to the last option
                    
            elif key == curses.KEY_DOWN:
                # Move to next selectable option
                if current_position < len(selectable_indices) - 1:
                    selected_idx = selectable_indices[current_position + 1]
                else:
                    selected_idx = selectable_indices[0]  # Wrap around to the first option
                    
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                # Return the selected option text
                return options[selected_idx]
                
            elif key == 27:  # ESC key
                return "BACK"
                
            time.sleep(0.1)
    
    def get_menu_title(self):
        """Get the title for the current menu"""
        menu_titles = {
            "main": "ULTIMATE SNAKE SHOWDOWN",
            "settings": "GAME SETTINGS",
            "help": "GAME HELP",
            "difficulty": "DIFFICULTY SETTINGS",
            "themes": "VISUAL THEMES",
            "ai_count": "AI SNAKE COUNT",
            "game_over": "GAME OVER"
        }
        return menu_titles.get(self.current_menu, "SNAKE GAME")
    
    def show_main_menu(self):
        """Show the main menu and handle selection"""
        self.current_menu = "main"
        
        # Create a more organized main menu
        options = [
            "--GAME MODES--",
            "Quick Game (4 AI Snakes)",
            "Human vs AI",
            "AI Battle Royale",
            "",
            "--OPTIONS--",
            "Settings",
            "Help",
            "Exit Game"
        ]
        
        selection = self.handle_menu_input(options)
        
        if selection == "Quick Game (4 AI Snakes)":
            return (4, False)  # 4 AI snakes
        elif selection == "Human vs AI":
            ai_count = self.show_ai_count_menu()
            if ai_count == 0:
                return self.show_main_menu()  # Go back to main menu
            return (ai_count + 1, True)  # Human + AI count
        elif selection == "AI Battle Royale":
            return self.show_snake_count_menu()
        elif selection == "Settings":
            self.show_settings_menu()
            return self.show_main_menu()  # Return to main menu after settings
        elif selection == "Help":
            self.show_help_screen()
            return self.show_main_menu()  # Return to main menu after help
        elif selection == "Exit Game":
            return (0, False)  # Exit code
        else:
            # If we get here, user likely pressed ESC
            return self.show_main_menu()
    
    def show_settings_menu(self):
        """Show and handle the settings menu"""
        self.current_menu = "settings"
        
        # Create settings menu with current values
        options = [
            "--GAME SETTINGS--",
            f"Difficulty: {self.settings['difficulty']}",
            f"Game Speed: {self.settings['game_speed']}x",
            f"Sound Effects: {self.settings['sound']}",
            f"Visual Theme: {self.settings['theme']}",
            "",
            "Save and Return"
        ]
        
        while True:
            selection = self.handle_menu_input(options)
            
            if selection == "Save and Return" or selection == "BACK":
                return  # Return to previous menu
            elif "Difficulty:" in selection:
                # Cycle through difficulty options
                difficulties = ["Easy", "Normal", "Hard", "Extreme"]
                current_idx = difficulties.index(self.settings['difficulty'])
                next_idx = (current_idx + 1) % len(difficulties)
                self.settings['difficulty'] = difficulties[next_idx]
                
                # Update the menu option
                diff_idx = next(i for i, opt in enumerate(options) if "Difficulty:" in opt)
                options[diff_idx] = f"Difficulty: {self.settings['difficulty']}"
                
            elif "Game Speed:" in selection:
                # Cycle through speed options
                speeds = [0.5, 0.75, 1.0, 1.25, 1.5]
                current_speed = self.settings['game_speed']
                current_idx = speeds.index(current_speed) if current_speed in speeds else 2
                next_idx = (current_idx + 1) % len(speeds)
                self.settings['game_speed'] = speeds[next_idx]
                
                # Update the menu option
                speed_idx = next(i for i, opt in enumerate(options) if "Game Speed:" in opt)
                options[speed_idx] = f"Game Speed: {self.settings['game_speed']}x"
                
            elif "Sound Effects:" in selection:
                # Toggle sound on/off
                self.settings['sound'] = "Off" if self.settings['sound'] == "On" else "On"
                
                # Update the menu option
                sound_idx = next(i for i, opt in enumerate(options) if "Sound Effects:" in opt)
                options[sound_idx] = f"Sound Effects: {self.settings['sound']}"
                
            elif "Visual Theme:" in selection:
                # Cycle through theme options
                themes = ["Classic", "Neon", "Retro", "Dark"]
                current_idx = themes.index(self.settings['theme'])
                next_idx = (current_idx + 1) % len(themes)
                self.settings['theme'] = themes[next_idx]
                
                # Update the menu option
                theme_idx = next(i for i, opt in enumerate(options) if "Visual Theme:" in opt)
                options[theme_idx] = f"Visual Theme: {self.settings['theme']}"
    
    def show_help_screen(self):
        """Show help information"""
        self.current_menu = "help"
        self.stdscr.clear()
        
        # Draw decorative border
        border_info = self.draw_menu_border("GAME HELP")
        start_x, start_y, box_width, box_height = border_info
        
        # Help content
        help_text = [
            "CONTROLS:",
            "- Arrow Keys: Change snake direction",
            "- WASD: Alternative movement controls",
            "- P: Pause game",
            "- Q: Quit to menu",
            "",
            "GAMEPLAY:",
            "- Eat food (*) to grow and earn points",
            "- Bonus food appears regularly (blinking)",
            "- Power-ups give special abilities:",
            "  S: Speed boost",
            "  I: Invincibility",
            "  G: Ghost mode (pass through other snakes)",
            "  +: Growth boost",
            "  M: Score multiplier",
            "",
            "Press any key to return..."
        ]
        
        # Display help text
        for i, line in enumerate(help_text):
            y_pos = start_y + 2 + i
            x_pos = start_x + 2
            
            if ":" in line and not line.startswith("-"):
                # It's a section header
                self.renderer.safe_addstr(y_pos, x_pos, line, curses.A_BOLD | curses.color_pair(5))
            else:
                self.renderer.safe_addstr(y_pos, x_pos, line)
        
        self.stdscr.refresh()
        
        # Wait for any key
        self.stdscr.nodelay(0)  # Switch to blocking input
        self.stdscr.getch()
        self.stdscr.nodelay(1)  # Switch back to non-blocking
    
    def show_snake_count_menu(self):
        """Show menu to select number of AI snakes for AI battle"""
        self.current_menu = "ai_count"
        
        options = [
            "--SELECT NUMBER OF AI SNAKES--",
            "2 Snakes", 
            "4 Snakes", 
            "6 Snakes", 
            "8 Snakes", 
            "10 Snakes", 
            "12 Snakes", 
            "14 Snakes", 
            "16 Snakes", 
            "18 Snakes", 
            "20 Snakes",
            "",
            "Back to Main Menu"
        ]
        
        selection = self.handle_menu_input(options)
        
        if selection == "Back to Main Menu" or selection == "BACK":
            return self.show_main_menu()
        else:
            # Parse snake count from option text
            try:
                snake_count = int(selection.split()[0])
                return (snake_count, False)
            except (ValueError, IndexError):
                return self.show_main_menu()
    
    def show_ai_count_menu(self):
        """Show menu to select number of AI snakes for human vs AI"""
        self.current_menu = "ai_count"
        
        options = ["--SELECT AI OPPONENTS--"]
        
        # Add options for 1-10 AI snakes
        for i in range(1, min(11, Config.MAX_SNAKES)):
            snake_text = "Snake" if i == 1 else "Snakes"
            options.append(f"{i} AI {snake_text}")
            
        options.append("")
        options.append("Back to Main Menu")
        
        selection = self.handle_menu_input(options)
        
        if selection == "Back to Main Menu" or selection == "BACK":
            return 0
        else:
            # Parse AI count from option text
            try:
                ai_count = int(selection.split()[0])
                return ai_count
            except (ValueError, IndexError):
                return 0
    
    def show_game_over_menu(self, game_state):
        """Show enhanced game over screen with options"""
        self.current_menu = "game_over"
        
        # Determine winner
        alive_snakes = [s for s in game_state.snakes if s.alive]
        if len(alive_snakes) == 1:
            winner = alive_snakes[0]
            result = f"Snake {winner.id} wins!"
            color = self.renderer.get_snake_color(winner.id)
        elif len(alive_snakes) > 1:
            # Multiple survivors, highest score wins
            winner = max(alive_snakes, key=lambda s: s.score)
            result = f"Snake {winner.id} wins with highest score!"
            color = self.renderer.get_snake_color(winner.id)
        else:
            # No survivors, highest score from all snakes
            winner = max(game_state.snakes, key=lambda s: s.score)
            result = f"All snakes died! Snake {winner.id} had the highest score."
            color = self.renderer.get_snake_color(winner.id)
        
        self.stdscr.clear()
        
        # Draw a fancy game over header
        game_over_text = "GAME OVER"
        self.renderer.safe_addstr(self.screen_height//3, 
                                 (self.screen_width - len(game_over_text))//2, 
                                 game_over_text, 
                                 curses.A_BOLD | curses.color_pair(3))
        
        # Draw winner information
        self.renderer.safe_addstr(self.screen_height//3 + 2, 
                                 (self.screen_width - len(result))//2, 
                                 result, 
                                 color | curses.A_BOLD)
        
        # Show winner's strategy if AI
        if not winner.is_human:
            strategy_text = f"Winning strategy: {winner.strategy.name}"
            self.renderer.safe_addstr(self.screen_height//3 + 3, 
                                     (self.screen_width - len(strategy_text))//2, 
                                     strategy_text, 
                                     color)
        
        # Show game statistics
        game_duration = time.time() - game_state.start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        time_str = f"Game Duration: {minutes:02d}:{seconds:02d}"
        
        self.renderer.safe_addstr(self.screen_height//3 + 5, 
                                 (self.screen_width - len(time_str))//2, 
                                 time_str)
                                 
        # Game over options
        options = [
            "--GAME FINISHED--",
            "View Rankings",
            "Play Again",
            "Change Settings",
            "Return to Main Menu",
            "Exit Game"
        ]
        
        selection = self.handle_menu_input(options)
        
        if selection == "View Rankings":
            return self.show_ranking_screen(game_state)
        elif selection == "Play Again":
            return True  # Restart the game with the same settings
        elif selection == "Change Settings":
            self.show_settings_menu()
            return self.show_game_over_menu(game_state)
        elif selection == "Return to Main Menu":
            # Return to main menu and get a new game configuration
            result = self.show_main_menu()
            if result == (0, False):
                return False  # Exit
            return result
        elif selection == "Exit Game":
            return False  # Exit the game
        else:
            return False
            
    def show_ranking_screen(self, game_state):
        """Show enhanced ranking screen"""
        self.current_menu = "ranking"
        
        # Sort snakes by score
        ranking = sorted(game_state.snakes, 
                        key=lambda s: (s.score, 0 if s.alive else 1, s.death_order if s.death_order else float('inf')),
                        reverse=True)
        
        self.stdscr.clear()
        
        # Draw decorative border
        border_info = self.draw_menu_border("FINAL RANKINGS")
        start_x, start_y, box_width, box_height = border_info
        
        # Calculate game duration
        game_duration = time.time() - game_state.start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        
        # Display game duration
        time_str = f"Game Duration: {minutes:02d}:{seconds:02d}"
        self.renderer.safe_addstr(start_y + 2, start_x + (box_width - len(time_str))//2, time_str)
        
        # Display ranking table header
        header_y = start_y + 4
        self.renderer.safe_addstr(header_y, start_x + 3, "Rank", curses.A_BOLD)
        self.renderer.safe_addstr(header_y, start_x + 10, "Snake", curses.A_BOLD)
        self.renderer.safe_addstr(header_y, start_x + 25, "Type", curses.A_BOLD)
        self.renderer.safe_addstr(header_y, start_x + 40, "Score", curses.A_BOLD)
        self.renderer.safe_addstr(header_y, start_x + 50, "Status", curses.A_BOLD)
        
        # Draw separator line
        for x in range(start_x + 2, start_x + box_width - 2):
            self.renderer.safe_addch(header_y + 1, x, '─')
        
        # Display snake rankings
        max_display = min(10, len(ranking))  # Display up to 10 snakes
        for idx, snake in enumerate(ranking[:max_display]):
            row_y = header_y + 2 + idx
            
            # Get snake color and set attributes
            snake_color = self.renderer.get_snake_color(snake.id)
            if snake.alive:
                snake_color |= curses.A_BOLD
            
            # Rank
            rank_text = f"#{idx+1}"
            self.renderer.safe_addstr(row_y, start_x + 3, rank_text, snake_color)
            
            # Snake ID
            snake_text = f"Snake {snake.id}"
            self.renderer.safe_addstr(row_y, start_x + 10, snake_text, snake_color)
            
            # Snake type
            type_text = "Human" if snake.is_human else f"AI ({snake.strategy.name[:4]})"
            self.renderer.safe_addstr(row_y, start_x + 25, type_text, snake_color)
            
            # Score
            score_text = str(snake.score)
            self.renderer.safe_addstr(row_y, start_x + 40, score_text, snake_color)
            
            # Status
            status = "ALIVE" if snake.alive else f"#{snake.death_order}" if snake.death_order else "DEAD"
            self.renderer.safe_addstr(row_y, start_x + 50, status, snake_color)
        
        # Options at the bottom
        options = ["Play Again", "Return to Main Menu", "Exit Game"]
        
        # Calculate options position
        options_y = start_y + box_height - 4
        options_x = start_x + (box_width - sum(len(opt) for opt in options) - 4) // 2
        
        # Draw options
        selected = 0
        while True:
            for idx, option in enumerate(options):
                attr = curses.A_REVERSE if idx == selected else 0
                self.renderer.safe_addstr(options_y, options_x, option, attr)
                options_x += len(option) + 2
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_LEFT:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_RIGHT:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Exit Game":
                    return False  # Exit
                elif options[selected] == "Play Again":
                    return True  # Restart
                elif options[selected] == "Return to Main Menu":
                    # Return to main menu and get a new game configuration
                    result = self.show_main_menu()
                    if result == (0, False):
                        return False  # Exit
                    return result
            
            # Reset options position for redrawing
            options_x = start_x + (box_width - sum(len(opt) for opt in options) - 4) // 2
            time.sleep(0.1)

# =============================================================================
# GAME CONTROLLER CLASS
# =============================================================================

class GameController:
    """Controls the game loop and handles input"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.renderer = Renderer(stdscr)
        self.setup_terminal()
        
        # Get terminal size
        term_height, term_width = stdscr.getmaxyx()
        self.screen_height = term_height - 2  # Leave room for status bar and help
        self.screen_width = term_width - 1    # Leave room for right border
        
        # Ensure minimum size
        if self.screen_height < Config.MIN_HEIGHT or self.screen_width < Config.MIN_WIDTH:
            raise ValueError(f"Terminal too small! Need at least {Config.MIN_WIDTH}x{Config.MIN_HEIGHT}")
        
        self.game_state = None
        self.menu_system = MenuSystem(stdscr, self.renderer, self.screen_width, self.screen_height)
    
    def setup_terminal(self):
        """Set up terminal for the game"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(1)  # Non-blocking input
        self.stdscr.timeout(0)  # No delay for getch()
        self.stdscr.keypad(True)  # Enable special keys
    
    def show_title_screen(self):
        """Show title screen and get game mode selection"""
        # Use the new menu system
        return self.menu_system.show_main_menu()
    
    def show_ai_count_menu(self):
        """Show menu to select number of AI snakes"""
        return self.menu_system.show_ai_count_menu()
    
    def show_ranking_screen(self):
        """Show ranking screen and handle restart/exit choice"""
        return self.menu_system.show_ranking_screen(self.game_state)
    
    def show_game_over_screen(self):
        """Show game over screen and handle restart/exit choice"""
        return self.menu_system.show_game_over_menu(self.game_state)
    
    def handle_input(self):
        """Handle user input during gameplay"""
        key = self.stdscr.getch()
        if key == -1:
            return True  # No input
        
        if key == ord('q'):
            return False  # Quit game
        
        if key == ord('p'):
            self.game_state.paused = not self.game_state.paused
        
        # Special event trigger with space bar
        if key == ord(' ') and Config.ENHANCED_VISUALS:
            # Allow manual triggering of special events if enhanced visuals are enabled
            if not self.game_state.special_event_active:
                self.game_state.trigger_special_event()
        
        # Handle difficulty cycling with 'd' key
        if key == ord('d'):
            difficulties = ["Easy", "Normal", "Hard", "Extreme"]
            current_idx = difficulties.index(self.game_state.difficulty)
            next_idx = (current_idx + 1) % len(difficulties)
            self.game_state.difficulty = difficulties[next_idx]
            
            # Adjust game parameters based on new difficulty
            if self.game_state.difficulty == "Easy":
                self.game_state.game_speed = Config.BASE_SPEED * 1.3  # Slower
            elif self.game_state.difficulty == "Normal":
                self.game_state.game_speed = Config.BASE_SPEED
            elif self.game_state.difficulty == "Hard":
                self.game_state.game_speed = Config.BASE_SPEED * 0.8  # Faster
            elif self.game_state.difficulty == "Extreme":
                self.game_state.game_speed = Config.BASE_SPEED * 0.6  # Much faster
        
        # Handle direction for human snake (if any)
        for snake in self.game_state.snakes:
            if snake.is_human and snake.alive:
                # Check if controls are reversed due to power-up
                if snake.is_reversed():
                    # Reverse the direction keys
                    reversed_key = key
                    if key == curses.KEY_UP:
                        reversed_key = curses.KEY_DOWN
                    elif key == curses.KEY_DOWN:
                        reversed_key = curses.KEY_UP
                    elif key == curses.KEY_LEFT:
                        reversed_key = curses.KEY_RIGHT
                    elif key == curses.KEY_RIGHT:
                        reversed_key = curses.KEY_LEFT
                    elif key == ord('w'):
                        reversed_key = ord('s')
                    elif key == ord('s'):
                        reversed_key = ord('w')
                    elif key == ord('a'):
                        reversed_key = ord('d')
                    elif key == ord('d'):
                        reversed_key = ord('a')
                    
                    new_dir = Direction.from_key(reversed_key)
                else:
                    new_dir = Direction.from_key(key)
                    
                # Check if snake is confused (random direction)
                if snake.is_confused() and new_dir:
                    # 50% chance to go random direction
                    if random.random() < 0.5:
                        new_dir = random.choice([d for d in Direction.all_directions() 
                                              if not Direction.is_opposite(d, snake.direction)])
                
                if new_dir and not Direction.is_opposite(new_dir, snake.direction):
                    snake.direction = new_dir
        
        return True
    
    def run_game(self):
        """Main game loop"""
        # Show title screen and get game mode
        result = self.show_title_screen()
        if isinstance(result, tuple):
            num_snakes, human_player = result
            if num_snakes == 0:
                return  # Exit if user chose to exit
        else:
            # In case we get a non-tuple result
            return
        
        # Main game loop
        restart = True
        while restart:
            # Initialize game state
            self.game_state = GameState(self.screen_width, self.screen_height, num_snakes, human_player)
            self.game_state.initialize_game()
            
            # Apply game settings from the menu system
            if 'difficulty' in self.menu_system.settings:
                # Adjust game parameters based on difficulty
                if self.menu_system.settings['difficulty'] == 'Easy':
                    self.game_state.game_speed = Config.BASE_SPEED * 1.3  # Slower
                    self.game_state.idle_time_threshold = Config.MAX_IDLE_TIME * 1.5  # More time before speed up
                elif self.menu_system.settings['difficulty'] == 'Hard':
                    self.game_state.game_speed = Config.BASE_SPEED * 0.8  # Faster
                    self.game_state.idle_time_threshold = Config.MAX_IDLE_TIME * 0.8  # Less time before speed up
                elif self.menu_system.settings['difficulty'] == 'Extreme':
                    self.game_state.game_speed = Config.BASE_SPEED * 0.6  # Much faster
                    self.game_state.idle_time_threshold = Config.MAX_IDLE_TIME * 0.5  # Much less time before speed up
            
            # Apply game speed from settings
            if 'game_speed' in self.menu_system.settings:
                speed_multiplier = self.menu_system.settings['game_speed']
                self.game_state.game_speed /= speed_multiplier  # Adjust base speed (lower = faster)
            
            # Game loop
            while not self.game_state.game_over:
                # Handle input
                if not self.handle_input():
                    break  # User quit
                
                # Update game state
                self.game_state.update()
                
                # Draw game
                self.renderer.draw_board(self.game_state)
                
                # Control game speed
                time.sleep(self.game_state.game_speed)
            
            # Game over - show ranking and ask for restart
            restart_result = self.show_game_over_screen()
            
            # Check if we need to restart with the same settings or start a new game
            if isinstance(restart_result, tuple):
                # We got a new game configuration from the menu
                num_snakes, human_player = restart_result
                if num_snakes == 0:
                    return  # Exit if user chose to exit
                restart = True
            else:
                # Simple boolean restart
                restart = restart_result


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main(stdscr):
    """Main function - entry point"""
    try:
        game = GameController(stdscr)
        game.run_game()
    except ValueError as e:
        stdscr.clear()
        stdscr.addstr(0, 0, str(e))
        stdscr.refresh()
        stdscr.getch()

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)