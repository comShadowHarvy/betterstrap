# First, update the AIStrategy enum with all the new strategies:

class AIStrategy(Enum):
    """Different strategies for AI snakes"""
    AGGRESSIVE = 1      # Focuses on getting food quickly
    CAUTIOUS = 2        # Prefers safe spaces over food
    OPPORTUNISTIC = 3   # Balanced approach
    DEFENSIVE = 4       # Avoids other snakes
    HUNTER = 5          # Targets other snake heads
    TERRITORIAL = 6     # Claims and defends a region
    SURVIVALIST = 7     # Focuses on staying alive
    TRAPPER = 8         # Tries to block other snakes
    SCAVENGER = 9       # Prioritizes dropped food
    POWER_HUNGRY = 10   # Prioritizes power-ups
    WALL_HUGGER = 11    # Prefers moving along walls
    AMBUSHER = 12       # Hides and waits to strike
    CHAOTIC = 13        # Makes unpredictable moves

# Next, add all the strategy implementations to the Snake.choose_direction method.
# Add these in the strategy-specific scoring section where
# the other strategies (AGGRESSIVE, CAUTIOUS, etc.) are already implemented.

# ----------------------------------------------------------------------------
# TERRITORIAL STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.TERRITORIAL:
    # Territorial: Claims and defends a specific region

    # Determine territory center if not already established
    if not hasattr(self, 'territory_center'):
        # Initialize territory in a quadrant based on snake ID
        # This ensures different snakes target different areas
        quadrant = (self.id % 4)
        if quadrant == 0:  # Top-left
            self.territory_center = (game_state.width // 4, game_state.height // 4)
        elif quadrant == 1:  # Top-right
            self.territory_center = (3 * game_state.width // 4, game_state.height // 4)
        elif quadrant == 2:  # Bottom-left
            self.territory_center = (game_state.width // 4, 3 * game_state.height // 4)
        else:  # Bottom-right
            self.territory_center = (3 * game_state.width // 4, 3 * game_state.height // 4)

        # Territory radius scales with board size
        self.territory_radius = min(game_state.width, game_state.height) // 5

    # Calculate distance from new position to territory center
    territory_distance = max(0, (abs(new_head[0] - self.territory_center[0]) +
                               abs(new_head[1] - self.territory_center[1]) -
                               self.territory_radius))

    # Strong incentive to stay within territory
    territory_score = 400 if territory_distance == 0 else 400 / (territory_distance + 1)

    # Check if food is in our territory
    food_in_territory_score = 0
    for food in foods:
        food_distance_to_center = abs(food.position[0] - self.territory_center[0]) + \
                                 abs(food.position[1] - self.territory_center[1])
        if food_distance_to_center <= self.territory_radius:
            # Food is in our territory - strongly prioritize
            food_in_territory_score += 600 / (abs(new_head[0] - food.position[0]) +
                                            abs(new_head[1] - food.position[1]) + 1)

    # Check for enemy snakes in our territory
    defense_score = 0
    for other_snake in game_state.snakes:
        if other_snake is not self and other_snake.alive:
            other_head = other_snake.body[0]
            other_distance_to_center = abs(other_head[0] - self.territory_center[0]) + \
                                     abs(other_head[1] - self.territory_center[1])

            # If enemy is in our territory
            if other_distance_to_center <= self.territory_radius:
                # Calculate approach vector to intercept
                approach_score = 500 / (abs(new_head[0] - other_head[0]) +
                                      abs(new_head[1] - other_head[1]) + 1)

                # Bigger bonus for intercepting if we're larger
                if len(self.body) > len(other_snake.body):
                    approach_score *= 1.5
                else:
                    # If smaller, only approach if we have advantage
                    approach_score *= 0.5

                defense_score += approach_score

    # Dynamic territory expansion - grow territory if dominating
    if hasattr(self, 'last_length') and len(self.body) > self.last_length + 5:
        self.territory_radius = min(self.territory_radius + 1, min(game_state.width, game_state.height) // 3)
    self.last_length = len(self.body)

    # Occasional ventures outside territory for food if we're hungry
    venture_score = 0
    if len(self.body) < 8 or random.random() < 0.2:
        closest_food_dist = float('inf')
        for food in foods:
            food_dist = abs(new_head[0] - food.position[0]) + abs(new_head[1] - food.position[1])
            if food_dist < closest_food_dist:
                closest_food_dist = food_dist

        # Strong incentive for nearby food when small
        if closest_food_dist < 8:
            venture_score = 300 / (closest_food_dist + 1)

    # Balance territorial control with survival
    strategy_score = (
        territory_score * 1.2 +
        food_in_territory_score * 1.5 +
        defense_score +
        venture_score +
        space_score * 1.0  # Still value space, but less than territory control
    )

    # Safety override - if in danger, prioritize survival
    if space < 15:
        strategy_score = space_score * 2 + territory_score * 0.5

# ----------------------------------------------------------------------------
# SURVIVALIST STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.SURVIVALIST:
    # Survivalist: Focuses purely on staying alive as long as possible

    # Extremely high value on open space
    survivalist_space_score = space_score * 3.0

    # Analyze the distribution of space in different directions
    space_distribution = []
    for test_dir in Direction.all_directions():
        if Direction.is_opposite(test_dir, direction):
            continue
        test_pos = (head[0] + test_dir.value[0], head[1] + test_dir.value[1])
        if not self.is_safe(test_pos, obstacles, game_state):
            continue
        test_space = self.free_space(test_pos, obstacles, foods, power_ups, game_state)
        space_distribution.append(test_space)

    # Space variance - prefer directions with more equal distribution of space
    space_variance = 0
    if len(space_distribution) >= 2:
        space_variance = sum((s - sum(space_distribution)/len(space_distribution))**2
                           for s in space_distribution) / len(space_distribution)

    # Penalize high variance - want to have multiple escape routes
    variance_penalty = min(300, space_variance * 3)

    # Distance from center - survivalists prefer middle areas for maximum options
    center_x, center_y = game_state.width // 2, game_state.height // 2
    center_distance = abs(new_head[0] - center_x) + abs(new_head[1] - center_y)
    center_score = 200 - (center_distance * 5)

    # Only go for food if it's very safe and we're not too large
    food_survival_score = 0
    if len(self.body) < 15 and space > 30:  # Only when we have plenty of space
        min_food_dist = float('inf')
        for food in foods:
            food_dist = abs(new_head[0] - food.position[0]) + abs(new_head[1] - food.position[1])

            # Check danger level around food
            food_safety = self.free_space(food.position, obstacles, foods, power_ups, game_state)
            if food_dist < min_food_dist and food_safety > 20:
                min_food_dist = food_dist

                # Only care about very close, safe food
                if food_dist < 3:
                    food_survival_score = 150

    # Avoid other snakes at all costs
    snake_avoidance = 0
    for other_snake in game_state.snakes:
        if other_snake is not self and other_snake.alive:
            other_head = other_snake.body[0]
            other_dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])

            # Strong penalty for being near other snakes
            if other_dist < 8:
                snake_avoidance -= (8 - other_dist) * 80

    strategy_score = (
        survivalist_space_score +
        center_score +
        food_survival_score +
        snake_avoidance -
        variance_penalty +
        direction_score * 0.5  # Some preference for continuing direction, but not strong
    )

# ----------------------------------------------------------------------------
# TRAPPER STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.TRAPPER:
    # Trapper: Look for opportunities to block other snakes

    # Identify potential choke points where we can trap other snakes
    trapping_score = 0

    # Calculate distance to other snake heads
    other_heads = []
    for other_snake in game_state.snakes:
        if other_snake is not self and other_snake.alive:
            other_heads.append(other_snake.body[0])

    # Find narrow passages and corridors
    narrow_passages = []
    for x in range(1, game_state.width - 1):
        for y in range(1, game_state.height - 1):
            pos = (x, y)
            if pos not in obstacles:
                # Count open neighbors (non-obstacles)
                open_neighbors = 0
                for test_dir in Direction.all_directions():
                    test_pos = (pos[0] + test_dir.value[0], pos[1] + test_dir.value[1])
                    if test_pos not in obstacles and 0 < test_pos[0] < game_state.width - 1 and 0 < test_pos[1] < game_state.height - 1:
                        open_neighbors += 1

                # If position has exactly 2 open neighbors, it's a potential corridor
                if open_neighbors == 2:
                    narrow_passages.append(pos)

    # Evaluate this move's trapping potential
    for passage in narrow_passages:
        # Calculate distance from new_head to this passage
        distance_to_passage = abs(new_head[0] - passage[0]) + abs(new_head[1] - passage[1])

        if distance_to_passage < 5:  # Only consider nearby passages
            # Check if any other snake is near this passage
            for other_head in other_heads:
                distance_from_snake = abs(other_head[0] - passage[0]) + abs(other_head[1] - passage[1])

                # Calculate trapping value - higher if:
                # 1. We're closer to the passage than the other snake
                # 2. The other snake is also close to the passage
                if distance_to_passage < distance_from_snake and distance_from_snake < 8:
                    # Perfect trapping scenario
                    trap_value = 300 - (distance_to_passage * 30)

                    # Extra points if the passage is between the other snake and food
                    for food in foods:
                        food_pos = food.position
                        snake_to_food = abs(other_head[0] - food_pos[0]) + abs(other_head[1] - food_pos[1])
                        passage_to_food = abs(passage[0] - food_pos[0]) + abs(passage[1] - food_pos[1])

                        if passage_to_food < snake_to_food:
                            trap_value += 200

                    trapping_score += trap_value

    # Add incentive to move toward the center early in the game
    early_game_centrality = 0
    if len(self.body) < 10:
        center_x, center_y = game_state.width // 2, game_state.height // 2
        distance_to_center = abs(new_head[0] - center_x) + abs(new_head[1] - center_y)
        early_game_centrality = 300 - (distance_to_center * 15)

    # Balance trapping with survival and food acquisition
    strategy_score = (
        trapping_score +
        target_score * 0.6 +  # Still care about food, but less
        space_score * 1.5 +   # Space remains important
        early_game_centrality
    )

    # If no good trapping opportunities, fall back to opportunistic behavior
    if trapping_score < 100:
        strategy_score += target_score * 0.8

# ----------------------------------------------------------------------------
# SCAVENGER STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.SCAVENGER:
    # Scavenger: Prioritizes eating dropped food from dead snakes

    # Strong preference for dropped food
    dropped_food_score = 0
    best_dropped_dist = float('inf')

    # Find the closest dropped food (temporary food from dead snakes)
    for food in game_state.temp_foods:  # Use the temp_foods list
        food_dist = abs(new_head[0] - food.position[0]) + abs(new_head[1] - food.position[1])

        if food_dist < best_dropped_dist:
            best_dropped_dist = food_dist

            # Higher value for closer dropped food
            dropped_food_score = 600 / (food_dist + 1)

    # Regular food is lower priority but still important
    regular_food_score = target_score * 0.6

    # Check for areas with high concentration of dropped food
    dropped_food_clusters = {}
    for food in game_state.temp_foods:
        # Get grid zone (divide board into 4x4 zones)
        zone_x = food.position[0] // (game_state.width // 4)
        zone_y = food.position[1] // (game_state.height // 4)
        zone = (zone_x, zone_y)

        if zone in dropped_food_clusters:
            dropped_food_clusters[zone] += 1
        else:
            dropped_food_clusters[zone] = 1

    # Add score for moving toward zones with lots of dropped food
    cluster_score = 0
    current_zone = (new_head[0] // (game_state.width // 4),
                   new_head[1] // (game_state.height // 4))

    for zone, count in dropped_food_clusters.items():
        if count >= 2:  # Only consider zones with multiple dropped food
            zone_dist = abs(current_zone[0] - zone[0]) + abs(current_zone[1] - zone[1])
            if zone_dist <= 1:  # We're in or adjacent to a good zone
                cluster_score += count * 100

    # Check for recent deaths (assume temp_foods were recently created)
    recent_death_bonus = 0
    if game_state.temp_foods and game_state.death_counter > len(game_state.snakes) / 2:
        recent_death_bonus = 200

    # Balance scavenging with survival
    strategy_score = (
        dropped_food_score * 1.5 +
        cluster_score +
        recent_death_bonus +
        regular_food_score +
        space_score * 1.2  # Survival still important
    )

    # If no dropped food nearby, fall back to normal food seeking
    if dropped_food_score == 0 and cluster_score == 0:
        strategy_score = target_score + space_score

# ----------------------------------------------------------------------------
# POWER_HUNGRY STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.POWER_HUNGRY:
    # Power Hungry: Prioritizes power-ups over regular food

    # Extremely high value for power-ups
    power_up_score = 0
    best_power_up_dist = float('inf')

    # Find the closest power-up
    for power_up in power_ups:
        pu_dist = abs(new_head[0] - power_up.position[0]) + abs(new_head[1] - power_up.position[1])

        # Skip if we already have this power-up
        if power_up.type in self.power_ups:
            continue

        # Different power-ups have different values
        pu_value = 600  # Base value

        # Adjust value based on power-up type and game situation
        if power_up.type == PowerUpType.INVINCIBILITY:
            if len(self.body) > 12:  # More valuable when larger
                pu_value += 200
        elif power_up.type == PowerUpType.GHOST:
            if len([s for s in game_state.snakes if s.alive]) > 3:  # More valuable with many snakes
                pu_value += 200
        elif power_up.type == PowerUpType.SPEED_BOOST:
            pu_value += 100
        elif power_up.type == PowerUpType.GROWTH:
            if len(self.body) < 10:  # More valuable when smaller
                pu_value += 200
        elif power_up.type == PowerUpType.SCORE_MULTIPLIER:
            if any(abs(f.position[0] - power_up.position[0]) +
                  abs(f.position[1] - power_up.position[1]) < 8 for f in foods):
                pu_value += 250  # More valuable when food is nearby

        if pu_dist < best_power_up_dist:
            best_power_up_dist = pu_dist
            # Scale by distance - closer is much better
            power_up_score = pu_value / (pu_dist + 1)

    # Value regular food less, but still important if no power-ups nearby
    food_value = target_score * 0.5

    # Special case: If close to food with a score multiplier active, prioritize food
    if PowerUpType.SCORE_MULTIPLIER in self.power_ups:
        food_value = target_score * 1.5

    # Keep track of current power-ups to maximize their use
    active_powerup_optimization = 0

    # If we have speed boost, prioritize getting to food quickly
    if PowerUpType.SPEED_BOOST in self.power_ups:
        food_value *= 1.3

    # If we have invincibility, we can be more aggressive
    if PowerUpType.INVINCIBILITY in self.power_ups:
        space_value = space_score * 0.6  # Care less about safety
        danger_value = danger_score * 0.3  # Care less about danger
    else:
        space_value = space_score * 1.2
        danger_value = danger_score

    # Always prioritize nearby power-ups, but balance with survival
    strategy_score = (
        power_up_score * 2.0 +
        food_value +
        space_value +
        danger_value +
        active_powerup_optimization
    )

    # If no power-ups nearby and we're small, focus more on food
    if power_up_score == 0 and len(self.body) < 8:
        strategy_score = target_score * 1.2 + space_score

# ----------------------------------------------------------------------------
# WALL_HUGGER STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.WALL_HUGGER:
    # Wall Hugger: Prefers moving along walls for safety

    # Calculate wall proximity - how close we are to any wall
    x, y = new_head
    wall_proximity = min(
        x,  # Distance to left wall
        game_state.width - 1 - x,  # Distance to right wall
        y,  # Distance to top wall
        game_state.height - 1 - y  # Distance to bottom wall
    )

    # Calculate how many walls we're adjacent to (0, 1, or 2)
    adjacent_walls = 0
    if x == 1 or x == game_state.width - 2:  # Adjacent to left or right wall
        adjacent_walls += 1
    if y == 1 or y == game_state.height - 2:  # Adjacent to top or bottom wall
        adjacent_walls += 1

    # Calculate how many walls the direction we're moving along
    wall_following_score = 0
    if adjacent_walls > 0:
        # Check if we're moving parallel to a wall
        if (x == 1 or x == game_state.width - 2) and (dy != 0 and dx == 0):
            wall_following_score += 200  # Moving along vertical wall
        elif (y == 1 or y == game_state.height - 2) and (dx != 0 and dy == 0):
            wall_following_score += 200  # Moving along horizontal wall

    # Wall preference score - highest when right next to wall but not in corner
    wall_preference = 0
    if wall_proximity == 1:
        wall_preference = 300
    elif wall_proximity == 2:
        wall_preference = 150
    elif wall_proximity == 3:
        wall_preference = 50

    # Avoid corners - they're dangerous
    corner_penalty = 0
    if adjacent_walls == 2:  # We're in a corner
        corner_penalty = 400

    # Calculate path to food that follows walls when possible
    wall_path_to_food = 0
    if target:
        # Check if target is near a wall
        tx, ty = target
        target_wall_proximity = min(tx, game_state.width - 1 - tx, ty, game_state.height - 1 - ty)

        if target_wall_proximity <= 2:
            # Target is near a wall - good!
            wall_path_to_food = 250
        elif manhattan_to_target < 10:
            # Target is not near wall but close - still worth getting
            wall_path_to_food = 150 / (manhattan_to_target + 1)

    # Consider breaking away from wall for high-value targets
    break_from_wall = 0
    for food in foods:
        if food.type == FoodType.BONUS and abs(new_head[0] - food.position[0]) + abs(new_head[1] - food.position[1]) < 5:
            break_from_wall = 300

    # Consider breaking from wall for power-ups
    for power_up in power_ups:
        if abs(new_head[0] - power_up.position[0]) + abs(new_head[1] - power_up.position[1]) < 4:
            # Power-ups might be worth leaving the wall
            break_from_wall = 250

    # Balance wall hugging with survival and occasional food ventures
    strategy_score = (
        wall_preference +
        wall_following_score +
        wall_path_to_food +
        break_from_wall +
        target_score * 0.5 -  # Reduced priority for random food
        corner_penalty +
        space_score * 0.8  # Still need to avoid getting trapped
    )

    # Safety override - if space is very constrained, prioritize survival
    if space < 10:
        strategy_score = space_score * 2.5

# ----------------------------------------------------------------------------
# AMBUSHER STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.AMBUSHER:
    # Ambusher: Hides and waits for opportunities to strike

    # Identify potential ambush spots (near walls or in corners)
    ambush_value = 0

    # Wall proximity - ambushers like to hide against walls
    x, y = new_head
    wall_proximity = min(
        x,  # Distance to left wall
        game_state.width - 1 - x,  # Distance to right wall
        y,  # Distance to top wall
        game_state.height - 1 - y  # Distance to bottom wall
    )

    # Points for being next to a wall but not in a corner
    if wall_proximity == 1:
        adjacent_walls = 0
        if x == 1 or x == game_state.width - 2:
            adjacent_walls += 1
        if y == 1 or y == game_state.height - 2:
            adjacent_walls += 1

        if adjacent_walls == 1:  # Next to exactly one wall - perfect!
            ambush_value += 300
        elif adjacent_walls == 2:  # In a corner - too risky!
            ambush_value -= 200

    # Check for other snakes to ambush
    ambush_targets = []
    for other_snake in game_state.snakes:
        if other_snake is not self and other_snake.alive and len(self.body) > len(other_snake.body):
            other_head = other_snake.body[0]

            # Calculate distance
            other_dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])

            # Check if the other snake is heading toward us (using its direction)
            other_next_pos = (other_head[0] + other_snake.direction.value[0],
                              other_head[1] + other_snake.direction.value[1])
            next_dist = abs(new_head[0] - other_next_pos[0]) + abs(new_head[1] - other_next_pos[1])

            # If they're getting closer to us, they might be a good ambush target
            if next_dist < other_dist and other_dist < 10:
                ambush_targets.append((other_snake, other_dist, next_dist))

    # Calculate ambush attack score - higher when we're in position to strike
    attack_score = 0
    for target, dist, next_dist in ambush_targets:
        # Perfect ambush distance is 2-3 spaces away
        if 2 <= dist <= 3:
            # Check if we can cut them off
            potential_score = 500 - (dist * 50)

            # Higher score if we're larger
            size_advantage = len(self.body) - len(target.body)
            potential_score += size_advantage * 20

            attack_score = max(attack_score, potential_score)

    # Ambushers still care about food, but less than hiding
    food_value = target_score * 0.6

    # If we haven't found a good ambush position or target,
    # move toward food that's in a potential ambush position
    strategic_food_value = 0
    for food in foods:
        food_pos = food.position
        food_dist = abs(new_head[0] - food_pos[0]) + abs(new_head[1] - food_pos[1])

        # Is food near a wall?
        food_wall_proximity = min(
            food_pos[0],
            game_state.width - 1 - food_pos[0],
            food_pos[1],
            game_state.height - 1 - food_pos[1]
        )

        if food_wall_proximity == 1 and food_dist < 8:
            strategic_food_value += 300 / (food_dist + 1)

    # Balance ambushing with survival
    strategy_score = (
        ambush_value +
        attack_score +
        strategic_food_value +
        food_value +
        space_score * 1.1  # Still need decent space
    )

    # If getting too small, focus more on food
    if len(self.body) < 6:
        strategy_score = food_value * 2 + space_score + ambush_value * 0.5

# ----------------------------------------------------------------------------
# CHAOTIC STRATEGY
# ----------------------------------------------------------------------------
elif temp_strategy == AIStrategy.CHAOTIC:
    # Chaotic: Makes somewhat unpredictable moves while staying safe

    # Add significant randomness to decision making
    random_factor = random.randint(0, 400)

    # But still care about not dying
    survival_score = space_score * 1.3

    # Sometimes prioritize food, sometimes ignore it
    food_priority = random.choice([0.2, 0.5, 1.0, 1.5])
    food_value = target_score * food_priority

    # Occasionally make dramatic direction changes
    direction_change_value = 0
    if random.random() < 0.3:  # 30% chance of direction change
        # Prefer directions different from current
        if direction != self.direction:
            direction_change_value += 200
    else:
        # Otherwise, prefer continuing in same direction
        if direction == self.direction:
            direction_change_value += 150

    # Sometimes prefer walls, sometimes avoid them
    wall_preference = 0
    x, y = new_head
    wall_proximity = min(
        x,  # Distance to left wall
        game_state.width - 1 - x,  # Distance to right wall
        y,  # Distance to top wall
        game_state.height - 1 - y  # Distance to bottom wall
    )

    if random.random() < 0.5:
        # Prefer being near walls
        if wall_proximity == 1:
            wall_preference += 150
    else:
        # Prefer being away from walls
        if wall_proximity > 3:
            wall_preference += 150

    # Sometimes target other snakes, sometimes avoid them
    snake_interaction = 0
    if random.random() < 0.3 and len(self.body) > 8:  # Only when we're big enough
        # Find close snakes
        for other_snake in game_state.snakes:
            if other_snake is not self and other_snake.alive:
                other_head = other_snake.body[0]
                other_dist = abs(new_head[0] - other_head[0]) + abs(new_head[1] - other_head[1])

                if other_dist < 5:
                    if len(self.body) > len(other_snake.body):
                        # We're bigger - get closer
                        snake_interaction += 300 / (other_dist + 1)
                    else:
                        # We're smaller - stay away
                        snake_interaction -= 400 / (other_dist + 1)

    # Balance randomness with basic survival
    strategy_score = (
        random_factor +
        survival_score +
        food_value +
        direction_change_value +
        wall_preference +
        snake_interaction
    )

    # Safety override - if genuinely in danger, be more predictable
    if space < 8:
        strategy_score = space_score * 3 + food_value * 0.5 + random_factor * 0.3
