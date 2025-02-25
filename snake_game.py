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
    BASE_SPEED = 0.1
    SPEED_INCREASE_INTERVAL = 30  # Seconds
    MAX_SPEED_MULTIPLIER = 2.0
    
    # Food settings
    FOOD_BONUS_DURATION = 60  # Seconds until bonus food appears
    FOOD_POINTS = 1
    BONUS_FOOD_POINTS = 3
    TEMP_FOOD_POINTS = 1
    MIN_FOOD_COUNT = 5  # Minimum number of food items on screen
    
    # Snake settings
    INITIAL_SIZE = 3
    
    # Board settings
    MIN_WIDTH = 40
    MIN_HEIGHT = 15
    
    # Power-up settings
    POWER_UP_CHANCE = 0.005  # Chance of power-up appearing each cycle
    POWER_UP_DURATION = 20  # Seconds
    
    # Other settings
    MAX_IDLE_TIME = 30  # Seconds before game speeds up if no food eaten
    
    # AI settings
    AI_UPDATE_INTERVAL = 0.05  # How often AI updates its direction
    EMERGENCY_WALL_CHECK = True  # Always check for walls even between update intervals


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
    SPEED_BOOST = 1
    INVINCIBILITY = 2
    GHOST = 3
    GROWTH = 4
    SCORE_MULTIPLIER = 5


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
    
    def __init__(self, position, type=None):
        self.position = position
        self.type = type or random.choice(list(PowerUpType))
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
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.position == other
        return self.position == other.position


class AIStrategy(Enum):
    """Different strategies for AI snakes"""
    AGGRESSIVE = 1
    CAUTIOUS = 2
    OPPORTUNISTIC = 3
    DEFENSIVE = 4
    HUNTER = 5


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
    
    def next_head(self, new_dir=None):
        """Calculate the position of the next head"""
        if new_dir is None:
            new_dir = self.direction
        head = self.body[0]
        dx, dy = new_dir.value
        return (head[0] + dx, head[1] + dy)
    
    def move(self, foods, other_snakes_positions, power_ups, game_state):
        """Move the snake by updating its direction and position"""
        # Update direction for AI snakes
        if not self.is_human:
            current_time = time.time()
            
            # Check if we're about to hit a wall
            next_head = self.next_head()
            x, y = next_head
            
            # Emergency wall avoidance - always check this regardless of AI update interval
            if (x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1 or
                next_head in other_snakes_positions or next_head in self.body[1:]):
                # About to hit something, find a safe direction immediately
                safe_directions = []
                for direction in Direction.all_directions():
                    if Direction.is_opposite(direction, self.direction):
                        continue
                    test_pos = (self.body[0][0] + direction.value[0], self.body[0][1] + direction.value[1])
                    if self.is_safe(test_pos, other_snakes_positions | set(self.body[1:]), game_state):
                        safe_directions.append(direction)
                
                # If we found a safe direction, change immediately
                if safe_directions:
                    self.direction = random.choice(safe_directions)
                    
            # Regular AI update on the normal interval
            if current_time - self.last_ai_update > Config.AI_UPDATE_INTERVAL:
                self.choose_direction(foods, other_snakes_positions, power_ups, game_state)
                self.last_ai_update = current_time
        
        # Get the new head position
        new_head = self.next_head()
        
        # Add the new head
        self.body.insert(0, new_head)
        self.body_set.add(new_head)
        
        return new_head
    
    def remove_tail(self):
        """Remove the snake's tail (last segment) safely"""
        if not self.body:
            return
            
        tail = self.body.pop()
        # Safely remove from set if it exists
        if tail in self.body_set:
            self.body_set.remove(tail)
        else:
            # Resync body_set with body if they're out of sync
            self.body_set = set(self.body)
    
    def gets_longer(self, food_type):
        """Snake gets longer based on the food type"""
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
    
    def update_power_ups(self):
        """Update active power-ups and remove expired ones"""
        current_time = time.time()
        expired = [p for p, t in self.power_ups.items() if current_time > t]
        for p in expired:
            del self.power_ups[p]
    
    def has_power_up(self, power_up_type):
        """Check if snake has a specific power-up active"""
        return power_up_type in self.power_ups
    
    def free_space(self, pos, obstacles, foods, power_ups, game_state):
        """Calculate free space around a position (floodfill algorithm with optimized performance)"""
        # Quick boundary check first
        x, y = pos
        if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
            return 0  # No free space if it's on a boundary
        
        # Use a faster, less comprehensive calculation for 10 snakes mode
        if len(game_state.snakes) >= 8:
            # Check immediate neighbors only for large games
            free_neighbors = 0
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = x + dx, y + dy
                if (nx <= 0 or nx >= game_state.width - 1 or 
                    ny <= 0 or ny >= game_state.height - 1):
                    continue
                if (nx, ny) not in obstacles:
                    free_neighbors += 1
            
            # Quick estimate based on free neighbors
            return free_neighbors * 20
        
        # Full floodfill algorithm for smaller games
        visited = set()
        to_visit = {pos}
        count = 0
        found_food = False
        found_power_up = False
        
        while to_visit and count < 100:  # Limit size of search for performance
            p = to_visit.pop()
            if p in visited or p in obstacles:
                continue
            
            visited.add(p)
            x, y = p
            
            # Check board boundaries
            if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
                continue
            
            # Check if food is found
            if any(p == food.position for food in foods):
                found_food = True
                if count > 15:  # Early exit if we found food and decent space
                    return count + 100
            
            # Check if power-up is found
            if any(p == powerup.position for powerup in power_ups):
                found_power_up = True
                if count > 10:  # Early exit if we found power-up and decent space
                    return count + 150
            
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
    
    def choose_direction(self, foods, other_snakes_positions, power_ups, game_state):
        """AI logic to choose the next direction with look-ahead capability"""
        head = self.body[0]
        obstacles = set(other_snakes_positions) | set(self.body[1:])
        
        # Find closest food and power-up
        closest_food = None
        min_food_dist = float('inf')
        closest_power_up = None
        min_power_up_dist = float('inf')
        
        # Find closest food
        for food in foods:
            food_pos = food.position
            dist = abs(head[0] - food_pos[0]) + abs(head[1] - food_pos[1])
            if dist < min_food_dist:
                min_food_dist = dist
                closest_food = food_pos
        
        # Find closest power-up
        for power_up in power_ups:
            power_up_pos = power_up.position
            dist = abs(head[0] - power_up_pos[0]) + abs(head[1] - power_up_pos[1])
            if dist < min_power_up_dist:
                min_power_up_dist = dist
                closest_power_up = power_up_pos
        
        # Prioritize food over power-ups, but consider power-ups if they're much closer
        target = closest_food
        if closest_power_up and min_power_up_dist < min_food_dist // 2:
            target = closest_power_up
            
        # Default to food if no target found
        if not target and closest_food:
            target = closest_food
        
        if not target:
            # Try to continue in same direction if safe
            next_pos = self.next_head()
            if self.is_safe(next_pos, obstacles, game_state):
                return
            
            # Find any safe direction
            for direction in Direction.all_directions():
                if Direction.is_opposite(direction, self.direction):
                    continue
                next_pos = (head[0] + direction.value[0], head[1] + direction.value[1])
                if self.is_safe(next_pos, obstacles, game_state):
                    self.direction = direction
                    return
            return
        
        # Simple algorithm for many snakes to improve performance
        if len(game_state.snakes) >= 8:
            # First priority: avoid immediate collisions
            next_pos = self.next_head()
            if not self.is_safe(next_pos, obstacles, game_state):
                # Current direction is unsafe, find a safe one
                safe_directions = []
                for direction in Direction.all_directions():
                    if Direction.is_opposite(direction, self.direction):
                        continue
                    new_head = (head[0] + direction.value[0], head[1] + direction.value[1])
                    if self.is_safe(new_head, obstacles, game_state):
                        # Calculate distance to target for this direction
                        dist = abs(new_head[0] - target[0]) + abs(new_head[1] - target[1])
                        safe_directions.append((direction, dist))
                
                if safe_directions:
                    # Sort by distance to target (ascending)
                    safe_directions.sort(key=lambda x: x[1])
                    # Choose the direction that gets us closest to target
                    self.direction = safe_directions[0][0]
                return
                
            # Move towards target if possible
            target_dx = target[0] - head[0]
            target_dy = target[1] - head[1]
            
            # Always try to move directly toward target
            # Determine if we should move horizontally or vertically based on which gets us closer
            if abs(target_dx) > abs(target_dy):
                # Try horizontal movement first
                new_dir = Direction.RIGHT if target_dx > 0 else Direction.LEFT
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state):
                        self.direction = new_dir
                        return
                
                # Try vertical if horizontal doesn't work
                new_dir = Direction.DOWN if target_dy > 0 else Direction.UP
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state):
                        self.direction = new_dir
                        return
            else:
                # Try vertical movement first
                new_dir = Direction.DOWN if target_dy > 0 else Direction.UP
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state):
                        self.direction = new_dir
                        return
                
                # Try horizontal if vertical doesn't work
                new_dir = Direction.RIGHT if target_dx > 0 else Direction.LEFT
                if not Direction.is_opposite(new_dir, self.direction):
                    new_head = (head[0] + new_dir.value[0], head[1] + new_dir.value[1])
                    if self.is_safe(new_head, obstacles, game_state):
                        self.direction = new_dir
                        return
            
            # Continue in same direction if it's safe (already checked above)
            return
        
        # -----------------------------------------------------------------
        # Full AI logic for smaller games with 4-step look-ahead
        # -----------------------------------------------------------------
        
        # Calculate direction to target
        target_dx = target[0] - head[0]
        target_dy = target[1] - head[1]
        
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
            
            # Look ahead 4 steps to check if this direction leads to self-collision
            future_score = self.look_ahead(new_head, direction, obstacles, game_state, 4)
            if future_score < 0:
                # This direction leads to certain death, skip it
                continue
            
            # Calculate score based on various factors
            
            # 1. Distance to food - higher score for closer food
            manhattan_to_target = abs(new_head[0] - target[0]) + abs(new_head[1] - target[1])
            target_score = 400 - 20 * manhattan_to_target
            
            # Direct path to target gets bonus
            if (target_dx > 0 and dx > 0) or (target_dx < 0 and dx < 0):  # Moving in correct x direction
                target_score += 100
            if (target_dy > 0 and dy > 0) or (target_dy < 0 and dy < 0):  # Moving in correct y direction
                target_score += 100
            
            # Immediate adjacent to target gets huge bonus
            if manhattan_to_target == 1:
                target_score += 1000
                
            # 2. If target is power-up, add bonus but not as much as food
            if target == closest_power_up:
                target_score = target_score * 0.8  # Power-ups are 80% as valuable as food
            
            # 3. Free space in that direction
            space = self.free_space(new_head, obstacles, foods, power_ups, game_state)
            space_score = 0.3 * space  # Increased weight for space
            
            # 4. Look-ahead bonus (from simulating future moves)
            look_ahead_score = future_score * 0.5  # Value future safety
            
            # 5. Preference for continuing in same direction
            direction_score = 50 if direction == self.direction else 0
            
            # 6. Score based on strategy
            strategy_score = 0
            if self.strategy == AIStrategy.AGGRESSIVE:
                # Aggressive: Go straight for target, ignore space
                strategy_score = target_score * 2.0
                # If very close to target, be even more aggressive
                if manhattan_to_target < 3:
                    strategy_score += 300
            elif self.strategy == AIStrategy.CAUTIOUS:
                # Cautious: Value space more than target
                strategy_score = space_score * 2.0 + look_ahead_score * 1.5
                # But still go for target if it's very close
                if manhattan_to_target < 2:
                    strategy_score += target_score
            elif self.strategy == AIStrategy.OPPORTUNISTIC:
                # Opportunistic: Balance target and space, opportunistically change direction
                strategy_score = target_score + space_score + random.randint(0, 50)
                # Be more aggressive when target is close
                if manhattan_to_target < 5:
                    strategy_score += 200
            elif self.strategy == AIStrategy.DEFENSIVE:
                # Defensive: Stay away from other snakes
                snake_proximity = 0
                for pos in other_snakes_positions:
                    dist = abs(new_head[0] - pos[0]) + abs(new_head[1] - pos[1])
                    if dist < 5:
                        snake_proximity += (5 - dist) * 20
                strategy_score = target_score + space_score - snake_proximity + look_ahead_score
                # Still go for target if it's very close
                if manhattan_to_target < 3:
                    strategy_score += 200
            elif self.strategy == AIStrategy.HUNTER:
                # Hunter: Aim for the head of other snakes to try to kill them
                for other_snake in game_state.snakes:
                    if other_snake is not self and other_snake.alive:
                        other_head = other_snake.body[0]
                        dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                        if dist < 5:
                            strategy_score += (5 - dist) * 30
                # Don't forget about target
                if manhattan_to_target < 3:
                    strategy_score += target_score
            
            # Calculate total score
            total_score = target_score + space_score + direction_score + strategy_score + look_ahead_score
            
            # Penalize moves that lead to dead ends
            if space < 5:
                total_score -= 500
            
            candidates.append((direction, total_score))
        
        # Choose direction with highest score
        if candidates:
            self.prev_direction = self.direction
            self.direction = max(candidates, key=lambda x: x[1])[0]
            
            # Increment consecutive moves counter if same direction
            if self.direction == self.prev_direction:
                self.consecutive_moves += 1
            else:
                self.consecutive_moves = 0
            
            # Avoid loops by occasionally changing direction
            if self.consecutive_moves > 15 and random.random() < 0.3:
                alternative_dirs = [d for d, _ in candidates if d != self.direction]
                if alternative_dirs:
                    self.direction = random.choice(alternative_dirs)
                    self.consecutive_moves = 0
                    
    def look_ahead(self, start_pos, direction, obstacles, game_state, steps):
        """Simulate future moves to detect potential collisions"""
        if steps <= 0:
            return 10  # Base score for reaching the look-ahead depth safely
            
        # Clone the obstacles set to avoid modifying the original
        future_obstacles = set(obstacles)
        
        # Start simulating moves
        current_pos = start_pos
        current_direction = direction
        positions = [current_pos]  # Track positions we would occupy
        
        for i in range(steps):
            # Calculate next position
            dx, dy = current_direction.value
            next_pos = (current_pos[0] + dx, current_pos[1] + dy)
            
            # Check if next position would hit a wall
            x, y = next_pos
            if x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1:
                return -100  # Severe penalty for hitting a wall
                
            # Check if next position would hit an obstacle
            if next_pos in future_obstacles:
                return -50  # Penalty for hitting an obstacle
                
            # Check if next position would hit our own future body
            if next_pos in positions:
                return -75  # Penalty for self-collision
                
            # Move to next position
            current_pos = next_pos
            positions.append(current_pos)
            
            # Add our current position to obstacles for next simulation step
            future_obstacles.add(current_pos)
            
            # For subsequent steps, just continue in same direction (simple simulation)
            # This could be enhanced to simulate more complex behavior
            
        # Calculate free space at final position
        free_neighbors = 0
        x, y = positions[-1]
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if (nx <= 0 or nx >= game_state.width - 1 or 
                ny <= 0 or ny >= game_state.height - 1 or
                (nx, ny) in future_obstacles):
                continue
            free_neighbors += 1
            
        # Return score based on simulated moves
        return 10 + free_neighbors * 5


# =============================================================================
# GAME STATE CLASS
# =============================================================================

class GameState:
    """Manages the state of the game"""
    
    def __init__(self, width, height, num_snakes, human_player=False):
        self.width = width
        self.height = height
        self.num_snakes = num_snakes
        self.human_player = human_player
        self.snakes = []
        self.foods = []
        self.power_ups = []
        self.temp_foods = []
        self.death_counter = 1
        self.start_time = time.time()
        self.last_food_time = time.time()
        self.game_over = False
        self.paused = False
        self.game_speed = Config.BASE_SPEED
        self.speed_multiplier = 1.0
        self.last_speed_increase = time.time()
        self.last_food_eaten = time.time()
    
    def initialize_game(self):
        """Initialize game elements"""
        self.create_snakes()
        self.create_food()
    
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
        
        # Create AI snakes in two columns
        num_per_column = ai_snakes // 2
        left_x = 5
        right_x = self.width - 6
        spacing = (self.height - 10) // max(1, num_per_column - 1) if num_per_column > 1 else 0
        
        for i in range(num_per_column):
            y = 5 + i * spacing
            # Left column snake, moving right
            s_left = Snake(
                body=[(left_x, y), (left_x-1, y), (left_x-2, y)],
                direction=Direction.RIGHT,
                id=i+1+strat_offset,
                strategy=random.choice(list(AIStrategy))
            )
            self.snakes.append(s_left)
            
            # Right column snake, moving left
            s_right = Snake(
                body=[(right_x, y), (right_x+1, y), (right_x+2, y)],
                direction=Direction.LEFT,
                id=i+num_per_column+1+strat_offset,
                strategy=random.choice(list(AIStrategy))
            )
            self.snakes.append(s_right)
        
        # Remove extra snakes if num_snakes is odd
        while len(self.snakes) > self.num_snakes:
            self.snakes.pop()
    
    def create_food(self, food_type=FoodType.NORMAL):
        """Create a new food item"""
        all_positions = set()
        for snake in self.snakes:
            all_positions.update(snake.body_set)
        all_positions.update(f.position for f in self.foods)
        all_positions.update(p.position for p in self.power_ups)
        
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
        for snake in self.snakes:
            all_positions.update(snake.body_set)
        all_positions.update(f.position for f in self.foods)
        all_positions.update(p.position for p in self.power_ups)
        
        while True:
            pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
            if pos not in all_positions:
                break
        
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
        
        # Update game speed
        self.update_game_speed()
        
        # Make sure we have enough food
        while len(self.foods) < Config.MIN_FOOD_COUNT:
            self.create_food()
        
        # Check and update power-ups for each snake
        for snake in self.snakes:
            if snake.alive:
                snake.update_power_ups()
        
        # Create bonus food if enough time has passed
        if (len([f for f in self.foods if f.type == FoodType.BONUS]) == 0 and 
                time.time() - self.last_food_time > Config.FOOD_BONUS_DURATION):
            self.create_food(FoodType.BONUS)
        
        # Randomly create power-ups
        if random.random() < Config.POWER_UP_CHANCE:
            self.create_power_up()
        
        # Move each snake and check collisions
        for snake in self.snakes:
            if not snake.alive:
                continue
            
            # Gather positions of other snakes
            other_positions = set()
            for other in self.snakes:
                if other is not snake and other.alive:
                    other_positions.update(other.body_set)
            
            # Move the snake
            new_head = snake.move(self.foods + self.temp_foods, other_positions, self.power_ups, self)
            
            # Check wall collision
            hit_wall = (new_head[0] <= 0 or new_head[0] >= self.width - 1 or 
                      new_head[1] <= 0 or new_head[1] >= self.height - 1)
            
            if hit_wall:
                self.kill_snake(snake)
                continue
            
            # Check snake collision
            hit_snake = (new_head in snake.body[1:] or new_head in other_positions)
            
            if hit_snake:
                self.kill_snake(snake)
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
        
        # Check if game is over
        self.check_game_over()
    
    def kill_snake(self, snake):
        """Handle snake death"""
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
    
    def handle_power_up_collected(self, snake, power_up):
        """Handle when a snake collects a power-up"""
        snake.add_power_up(power_up.type)
        self.power_ups.remove(power_up)
    
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
        
        # Initialize all color pairs
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake1
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Snake2
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)      # Food
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Snake3
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Snake4
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Temp food
        curses.init_pair(7, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Snake5
        curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLACK)      # Snake6
        curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake7
        curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Snake8
        curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Snake9
        curses.init_pair(12, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Snake10
    
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
        
        # Draw border
        border_color = curses.color_pair(0)
        for x in range(game_state.width):
            self.safe_addch(1, x, '#', border_color)
            self.safe_addch(game_state.height, x, '#', border_color)
        for y in range(1, game_state.height + 1):
            self.safe_addch(y, 0, '#', border_color)
            self.safe_addch(y, game_state.width-1, '#', border_color)
        
        # Draw food
        for food in game_state.foods:
            food_color = curses.color_pair(food.color)
            attributes = curses.A_BLINK if food.type == FoodType.BONUS else 0
            self.safe_addch(food.position[1] + 1, food.position[0], food.char, food_color | attributes)
        
        # Draw temporary foods
        for food in game_state.temp_foods:
            temp_color = curses.color_pair(food.color)
            self.safe_addch(food.position[1] + 1, food.position[0], food.char, temp_color)
        
        # Draw power-ups
        for power_up in game_state.power_ups:
            power_up_color = curses.color_pair(power_up.color)
            self.safe_addch(power_up.position[1] + 1, power_up.position[0], power_up.char, 
                           power_up_color | curses.A_BLINK)
        
        # Draw snakes
        for snake in game_state.snakes:
            if not snake.alive:
                continue
            
            snake_color = min(snake.id + 2, 12)
            color_pair = curses.color_pair(snake_color)
            
            # Add special attributes for power-ups
            attrs = 0
            if snake.power_ups:
                attrs |= curses.A_BOLD
                if PowerUpType.INVINCIBILITY in snake.power_ups:
                    attrs |= curses.A_BLINK
            
            # Draw each segment
            for i, cell in enumerate(snake.body):
                char = 'H' if i == 0 else 'o'
                self.safe_addch(cell[1] + 1, cell[0], char, color_pair | attrs)
        
        # Draw status bar
        self.draw_status_bar(game_state)
        
        # Draw help text
        help_text = "P: Pause | Q: Quit | Arrow Keys: Move"
        help_color = curses.color_pair(6)
        self.safe_addstr(game_state.height + 1, 1, help_text, help_color)
        
        # Draw paused indicator
        if game_state.paused:
            pause_text = "PAUSED - Press P to continue"
            self.safe_addstr(game_state.height // 2, 
                            (game_state.width - len(pause_text)) // 2,
                            pause_text, curses.A_BOLD | curses.A_REVERSE)
        
        self.stdscr.refresh()
    
    def draw_status_bar(self, game_state):
        """Draw status bar with game information"""
        # Calculate game duration
        game_duration = time.time() - game_state.start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        
        # Prepare status text
        speed = f"Speed: {game_state.speed_multiplier:.1f}x"
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        
        # Draw status bar background
        status_color = curses.color_pair(0)
        for x in range(game_state.width):
            self.safe_addch(0, x, ' ', status_color)
        
        # Draw status text components
        self.safe_addstr(0, 1, time_str, status_color)
        self.safe_addstr(0, 2 * game_state.width // 3, speed, status_color)
        
        # Draw each snake's score if alive
        y_pos = 2
        for snake in sorted(game_state.snakes, key=lambda s: s.score, reverse=True):
            if not snake.alive:
                continue
            
            snake_color = min(snake.id + 2, 12)
            color_pair = curses.color_pair(snake_color)
            
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
            self.safe_addstr(y_pos, game_state.width - len(score_text) - 1, score_text, color_pair)
            y_pos += 1
    
    def draw_title_screen(self, width, height):
        """Draw the title screen"""
        self.stdscr.clear()
        
        title = "ULTIMATE SNAKE SHOWDOWN"
        subtitle = "A Battle of Serpentine Supremacy"
        author = "By ShadowHarvy, Enhanced by Claude"
        options = [
            "2 Snakes", "4 Snakes", "6 Snakes", "8 Snakes", "10 Snakes", 
            "Human + AI", "Exit"
        ]
        
        # Draw title and subtitle
        self.safe_addstr(height//4, (width - len(title))//2, title, curses.A_BOLD)
        self.safe_addstr(height//4 + 1, (width - len(subtitle))//2, subtitle)
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
            self.safe_addstr(height//4 + 4 + i, (width - len(line))//2, line, curses.color_pair(1))
        
        return options
    
    def draw_menu_options(self, options, selected, start_y, width):
        """Draw menu options with selected item highlighted"""
        for idx, option in enumerate(options):
            attr = curses.A_REVERSE if idx == selected else 0
            self.safe_addstr(start_y + idx, (width - len(option))//2, option, attr)
    
    def draw_ranking_screen(self, ranking, start_time, width, height):
        """Draw the ranking screen"""
        self.stdscr.clear()
        
        # Draw header
        self.safe_addstr(2, width//2 - 4, "RANKING", curses.A_BOLD)
        
        # Calculate game duration
        end_time = time.time()
        game_duration = end_time - start_time
        minutes = int(game_duration // 60)
        seconds = int(game_duration % 60)
        
        # Display game duration
        time_str = f"Game Duration: {minutes:02d}:{seconds:02d}"
        self.safe_addstr(3, (width - len(time_str))//2, time_str)
        
        # Display snake information
        for idx, snake in enumerate(ranking):
            rank = idx + 1
            snake_type = "Human" if snake.is_human else f"AI ({snake.strategy.name})"
            line = f"Rank {rank}: Snake {snake.id} ({snake_type}) - Score: {snake.score}"
            
            snake_color = min(snake.id + 2, 12)
            self.safe_addstr(5 + idx, (width - len(line))//2, line, curses.color_pair(snake_color))
        
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
            color = curses.color_pair(min(winner.id + 2, 12))
        elif len(alive_snakes) > 1:
            # Multiple survivors, highest score wins
            winner = max(alive_snakes, key=lambda s: s.score)
            result = f"Snake {winner.id} wins with highest score!"
            color = curses.color_pair(min(winner.id + 2, 12))
        else:
            # No survivors, highest score from all snakes
            winner = max(snakes, key=lambda s: s.score)
            result = f"All snakes died! Snake {winner.id} had the highest score."
            color = curses.color_pair(min(winner.id + 2, 12))
        
        # Draw result
        self.safe_addstr(height//3, (width - len("GAME OVER"))//2, "GAME OVER", curses.A_BOLD)
        self.safe_addstr(height//3 + 2, (width - len(result))//2, result, color | curses.A_BOLD)
        
        # Draw options
        options = ["Restart", "Exit"]
        return options


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
    
    def setup_terminal(self):
        """Set up terminal for the game"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(1)  # Non-blocking input
        self.stdscr.timeout(0)  # No delay for getch()
        self.stdscr.keypad(True)  # Enable special keys
    
    def show_title_screen(self):
        """Show title screen and get game mode selection"""
        options = self.renderer.draw_title_screen(self.screen_width, self.screen_height)
        selected = 0
        
        while True:
            self.renderer.draw_menu_options(options, selected, self.screen_height//2, self.screen_width)
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Exit":
                    return (0, False)  # Exit code
                elif options[selected] == "Human + AI":
                    # Show submenu for number of AI snakes
                    ai_count = self.show_ai_count_menu()
                    if ai_count == 0:
                        return (0, False)  # Exit if user cancels
                    return (ai_count + 1, True)  # Number of snakes, human player flag
                else:
                    return (int(options[selected].split()[0]), False)
            
            time.sleep(0.1)
    
    def show_ai_count_menu(self):
        """Show menu to select number of AI snakes"""
        options = [str(i) for i in range(1, 10)] + ["Cancel"]
        selected = 0
        
        while True:
            self.stdscr.clear()
            self.renderer.safe_addstr(self.screen_height//4, 
                                    self.screen_width//2 - 15, 
                                    "Choose number of AI snakes (1-9):")
            
            self.renderer.draw_menu_options(options, selected, self.screen_height//2, self.screen_width)
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Cancel":
                    return 0
                else:
                    return int(options[selected])
            
            time.sleep(0.1)
    
    def show_ranking_screen(self):
        """Show ranking screen and handle restart/exit choice"""
        # Sort snakes by death order (alive snakes first, then by death order)
        ranking = sorted(self.game_state.snakes, 
                        key=lambda s: (0 if s.alive else 1, s.death_order if s.death_order else float('inf')))
        
        options = self.renderer.draw_ranking_screen(ranking, self.game_state.start_time, 
                                                 self.screen_width, self.screen_height)
        selected = 0
        
        while True:
            self.renderer.draw_menu_options(options, selected, 
                                          self.screen_height//2 + 6, self.screen_width)
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Restart":
                    return True  # Restart
                else:
                    return False  # Exit
            
            time.sleep(0.1)
    
    def show_game_over_screen(self):
        """Show game over screen and handle restart/exit choice"""
        options = self.renderer.draw_game_over_screen(self.game_state.snakes, 
                                                    self.screen_width, self.screen_height)
        selected = 0
        
        while True:
            self.renderer.draw_menu_options(options, selected, 
                                          self.screen_height//2 + 4, self.screen_width)
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Restart":
                    return True  # Restart
                else:
                    return False  # Exit
            
            time.sleep(0.1)
    
    def handle_input(self):
        """Handle user input during gameplay"""
        key = self.stdscr.getch()
        if key == -1:
            return True  # No input
        
        if key == ord('q'):
            return False  # Quit game
        
        if key == ord('p'):
            self.game_state.paused = not self.game_state.paused
        
        # Handle direction for human snake (if any)
        for snake in self.game_state.snakes:
            if snake.is_human and snake.alive:
                new_dir = Direction.from_key(key)
                if new_dir and not Direction.is_opposite(new_dir, snake.direction):
                    snake.direction = new_dir
        
        return True
    
    def run_game(self):
        """Main game loop"""
        # Show title screen and get game mode
        num_snakes, human_player = self.show_title_screen()
        if num_snakes == 0:
            return  # Exit if user chose to exit
        
        # Main game loop
        restart = True
        while restart:
            # Initialize game state
            self.game_state = GameState(self.screen_width, self.screen_height, num_snakes, human_player)
            self.game_state.initialize_game()
            
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
            restart = self.show_game_over_screen()


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