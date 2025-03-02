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
    BASE_SPEED = 0.12  # Slightly slower initial speed for better playability
    SPEED_INCREASE_INTERVAL = 30  # Seconds
    MAX_SPEED_MULTIPLIER = 2.0
    
    # Food settings
    FOOD_BONUS_DURATION = 45  # Seconds until bonus food appears
    FOOD_POINTS = 1
    BONUS_FOOD_POINTS = 3
    TEMP_FOOD_POINTS = 1
    MIN_FOOD_COUNT = 6  # Increased minimum food count for more action
    
    # Snake settings
    INITIAL_SIZE = 3
    
    # Board settings
    MIN_WIDTH = 40
    MIN_HEIGHT = 15
    
    # Power-up settings
    POWER_UP_CHANCE = 0.008  # Slightly increased chance of power-ups
    POWER_UP_DURATION = 20  # Seconds
    
    # Other settings
    MAX_IDLE_TIME = 30  # Seconds before game speeds up if no food eaten
    
    # AI settings
    AI_UPDATE_INTERVAL = 0.05  # How often AI updates its direction
    EMERGENCY_WALL_CHECK = True  # Always check for walls even between update intervals
    LOOK_AHEAD_STEPS = 6  # How many steps ahead the AI should look 


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
    AGGRESSIVE = 1  # Focuses on getting food quickly
    CAUTIOUS = 2    # Prefers safe spaces over food
    OPPORTUNISTIC = 3  # Balanced approach
    DEFENSIVE = 4   # Avoids other snakes
    HUNTER = 5      # Targets other snake heads


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
            if Config.EMERGENCY_WALL_CHECK and (
                x <= 0 or x >= game_state.width - 1 or y <= 0 or y >= game_state.height - 1 or
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
        
        # Use a faster, less comprehensive calculation for large games
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
                return -200  # Increased penalty for hitting a wall
                
            # Check if next position would hit an obstacle
            if next_pos in future_obstacles:
                return -150  # Increased penalty for hitting an obstacle
                
            # Check if next position would hit our own future body
            if next_pos in positions:
                return -175  # Increased penalty for self-collision
                
            # Move to next position
            current_pos = next_pos
            positions.append(current_pos)
            
            # Add our current position to obstacles for next simulation step
            future_obstacles.add(current_pos)
            
            # Count available directions for this position
            available = 0
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
            
            available_directions_count.append(available)
            
            # If no directions available, this is a trap!
            if available == 0 and i < steps - 1:
                return -250  # Severely penalize getting trapped
                
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
        if len(available_directions_count) >= 3:
            if all(available_directions_count[i] > available_directions_count[i+1] 
                   for i in range(len(available_directions_count)-1)):
                return -50  # Penalty for consistently decreasing options
        
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
        step_completion_bonus = min(30, steps * 3)
            
        # Return score based on simulated moves with increased weight for space
        return 20 + free_neighbors * 10 + step_completion_bonus
    
    def choose_direction(self, foods, other_snakes_positions, power_ups, game_state):
        """Advanced AI logic to choose the next direction with improved decision making"""
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
                    type_bonus = 50
            
            # Check if food is in a danger zone
            danger_penalty = 200 if food_pos in danger_zones else 0
            
            # Calculate final score for this food
            # Closer food is better, clear path is better, 
            # special food is better, but avoid dangerous areas
            food_score = (1000 / (dist + 1)) + path_score + type_bonus - danger_penalty
            
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
            
            # Calculate score
            power_up_score = (800 / (dist + 1)) + type_value - danger_penalty
            
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
        if len(game_state.snakes) >= 6:
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
                
            # 2. Free space evaluation
            space = self.free_space(new_head, obstacles, foods, power_ups, game_state)
            space_score = 0.5 * space  # Increased weight for space
            
            # Extra penalty for very confined spaces
            if space < 8:
                space_score -= 300
            
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
                # Aggressive: Go straight for target, ignore some danger
                strategy_score = target_score * 2.0 - danger_score * 0.7
                # If very close to target, be even more aggressive
                if manhattan_to_target < 3:
                    strategy_score += 400
            
            elif temp_strategy == AIStrategy.CAUTIOUS:
                # Cautious: Value space and safety more than target
                strategy_score = space_score * 2.5 + look_ahead_score * 2.0 - danger_score * 1.5
                # But still go for target if it's very close
                if manhattan_to_target < 2:
                    strategy_score += target_score * 1.5
            
            elif temp_strategy == AIStrategy.OPPORTUNISTIC:
                # Opportunistic: Balance target and space, change direction based on situation
                strategy_score = target_score + space_score * 1.5 - danger_score + random.randint(0, 50)
                # More aggressive when target is close
                if manhattan_to_target < 5:
                    strategy_score += 250
                # More cautious when space is limited
                if space < 15:
                    strategy_score += space_score * 1.5
            
            elif temp_strategy == AIStrategy.DEFENSIVE:
                # Defensive: Stay away from other snakes
                snake_proximity = 0
                for pos in other_snakes_positions:
                    dist = abs(new_head[0] - pos[0]) + abs(new_head[1] - pos[1])
                    if dist < 5:
                        snake_proximity += (5 - dist) * 30
                
                strategy_score = target_score * 0.8 + space_score * 1.8 - snake_proximity * 1.5 + look_ahead_score * 1.5
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
                    if other_snake is not self and other_snake.alive and len(self.body) > len(other_snake.body):
                        other_head = other_snake.body[0]
                        dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])
                        # Only consider hunting when we're bigger and close
                        if dist < 6:
                            # More points for being exactly 1 space away - perfect for cutting off
                            if dist == 2:  # One move away
                                hunter_score += 400
                            elif dist < 4:  # Within hunting range
                                hunter_score += (6 - dist) * 80
                
                strategy_score = hunter_score + target_score * 0.6 + space_score
                # Don't forget food when it's very close
                if manhattan_to_target < 3:
                    strategy_score += target_score
            
            # Calculate total score
            total_score = (
                target_score + 
                space_score + 
                danger_score + 
                direction_score + 
                wall_score + 
                strategy_score + 
                look_ahead_score
            )
            
            # Add a bit of randomness to break ties and make behavior less predictable
            total_score += random.uniform(-10, 10)
            
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
            
            # Avoid loops by occasionally changing direction if many consecutive moves
            if self.consecutive_moves > 12 and random.random() < 0.4:
                alternative_dirs = [d for d, _ in candidates if d != self.direction]
                if alternative_dirs:
                    self.direction = random.choice(alternative_dirs)
                    self.consecutive_moves = 0


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
        self.create_initial_food()
    
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
        
        # Create AI snakes with different strategies
        ai_strategies = list(AIStrategy)
        
        # Ensure a good distribution of strategies for AI snakes
        if ai_snakes <= len(ai_strategies):
            # Use each strategy once if possible
            strategies = random.sample(ai_strategies, ai_snakes)
        else:
            # Use all strategies at least once, then repeat randomly
            strategies = ai_strategies.copy()
            while len(strategies) < ai_snakes:
                strategies.append(random.choice(ai_strategies))
            random.shuffle(strategies)
        
        # Create AI snakes in two columns with better distribution
        num_per_column = (ai_snakes + 1) // 2
        left_x = 5
        right_x = self.width - 6
        
        # Calculate spacing to distribute snakes more evenly
        spacing = (self.height - 10) // max(1, num_per_column - 1) if num_per_column > 1 else 0
        
        for i in range(ai_snakes):
            column_idx = i % 2
            row_idx = i // 2
            
            y = 5 + row_idx * spacing
            
            if column_idx == 0:  # Left column, moving right
                snake_body = [(left_x, y), (left_x-1, y), (left_x-2, y)]
                direction = Direction.RIGHT
            else:  # Right column, moving left
                snake_body = [(right_x, y), (right_x+1, y), (right_x+2, y)]
                direction = Direction.LEFT
            
            # Create snake with the assigned strategy
            snake = Snake(
                body=snake_body,
                direction=direction,
                id=i+1+strat_offset,
                strategy=strategies[i]
            )
            self.snakes.append(snake)
    
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
        for snake in self.snakes:
            all_positions.update(snake.body_set)
        all_positions.update(f.position for f in self.foods)
        all_positions.update(p.position for p in self.power_ups)
        all_positions.update(f.position for f in self.temp_foods)
        
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
            
            # Check for invincibility power-up
            has_invincibility = snake.has_power_up(PowerUpType.INVINCIBILITY)
            has_ghost = snake.has_power_up(PowerUpType.GHOST)
            
            # Check wall collision (unless invincible)
            hit_wall = (new_head[0] <= 0 or new_head[0] >= self.width - 1 or 
                      new_head[1] <= 0 or new_head[1] >= self.height - 1)
            
            if hit_wall and not has_invincibility:
                self.kill_snake(snake)
                continue
            
            # Check snake collision (unless ghost or invincible)
            hit_self = new_head in snake.body[1:]
            hit_other = new_head in other_positions
            
            if (hit_self and not has_invincibility) or (hit_other and not (has_ghost or has_invincibility)):
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
            
            snake_color = (snake.id % 8) + 1
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
            
            snake_color = (snake.id % 8) + 1
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
            self.safe_addstr(y_pos, 1, score_text, color_pair)
            y_pos += 1
    
    def draw_title_screen(self, width, height):
        """Draw the title screen"""
        self.stdscr.clear()
        
        title = "ULTIMATE SNAKE SHOWDOWN"
        subtitle = "A Battle of Serpentine Supremacy"
        author = "By ShadowHarvy, Enhanced with Smarter AI"
        options = [
            "2 Snakes", "4 Snakes", "6 Snakes", "8 Snakes", "10 Snakes", 
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
        
        # Display snake information
        for idx, snake in enumerate(ranking):
            rank = idx + 1
            snake_type = "Human" if snake.is_human else f"AI ({snake.strategy.name})"
            status = "ALIVE" if snake.alive else f"Died #{snake.death_order}"
            line = f"Rank {rank}: Snake {snake.id} ({snake_type}) - Score: {snake.score} - {status}"
            
            snake_color = (snake.id % 8) + 1
            color = curses.color_pair(snake_color)
            if snake.alive:
                color |= curses.A_BOLD
                
            self.safe_addstr(6 + idx, (width - len(line))//2, line, color)
        
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
            color = curses.color_pair((winner.id % 8) + 1)
        elif len(alive_snakes) > 1:
            # Multiple survivors, highest score wins
            winner = max(alive_snakes, key=lambda s: s.score)
            result = f"Snake {winner.id} wins with highest score!"
            color = curses.color_pair((winner.id % 8) + 1)
        else:
            # No survivors, highest score from all snakes
            winner = max(snakes, key=lambda s: s.score)
            result = f"All snakes died! Snake {winner.id} had the highest score."
            color = curses.color_pair((winner.id % 8) + 1)
        
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
        # Sort snakes by score
        ranking = sorted(self.game_state.snakes, 
                        key=lambda s: (s.score, 0 if s.alive else 1, s.death_order if s.death_order else float('inf')),
                        reverse=True)
        
        options = self.renderer.draw_ranking_screen(ranking, self.game_state.start_time, 
                                                 self.screen_width, self.screen_height)
        selected = 0
        
        while True:
            # Calculate position based on number of snakes
            menu_y = 8 + len(self.game_state.snakes)
            
            self.renderer.draw_menu_options(options, selected, menu_y, self.screen_width)
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
                                          self.screen_height//2 + 5, self.screen_width)
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if options[selected] == "Exit":
                    return False  # Exit
                elif options[selected] == "Restart":
                    return True  # Restart
                elif options[selected] == "See Rankings":
                    return self.show_ranking_screen()  # Show rankings, then get restart choice
            
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