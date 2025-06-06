import os
import random
import math

# --- Game Settings ---
MAP_WIDTH = 50
MAP_HEIGHT = 25
FLOOR_CHAR = "."
WALL_CHAR = "#"
GOAL_CHAR = "G"
DEAD_ENEMY_CHAR = "%"
UNSEEN_CHAR = ' '

# Combat Effects
EFFECT_NONE = 0
EFFECT_ATTACK = 1
EFFECT_CRIT = 2
EFFECT_HEAL = 3
combat_effects = []

# Effect Characters
EFFECT_CHARS = {
    EFFECT_ATTACK: "*",
    EFFECT_CRIT: "⚔",
    EFFECT_HEAL: "+"
}

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 20
MAX_ENEMIES_PER_ROOM = 2

BASE_FOV_RADIUS = 8

# --- Player Class Definitions (Fixed passive names) ---
PLAYER_CLASSES = [
    {"name": "Warrior", "char": "W", "hp": 30, "base_attack": 7, "color_code": "\033[94m",
     "passives": {"name": "Improved Fortitude", "desc": "Takes 1 less damage from melee attacks and regenerates 1 HP every 30 turns"}},
    {"name": "Rogue", "char": "R", "hp": 22, "base_attack": 5, "color_code": "\033[92m",
     "passives": {"name": "Evasion Master", "desc": "15% dodge chance and deals +2 damage to enemies below 50% HP"}},
    {"name": "Mage", "char": "M", "hp": 18, "base_attack": 4, "color_code": "\033[95m",
     "passives": {"name": "Arcane Mastery", "desc": "Deals +2 damage and has 20% chance to deal 2 bonus damage"}, "range": 4},
    {"name": "Cleric", "char": "C", "hp": 26, "base_attack": 5, "color_code": "\033[96m",
     "passives": {"name": "Divine Blessing", "desc": "Heals 1 HP every 20 turns and deals +1 damage to undead"}},
    {"name": "Ranger", "char": "N", "hp": 24, "base_attack": 6, "color_code": "\033[32m",
     "passives": {"name": "Hunter's Precision", "desc": "Increased FOV (+2) and deals +1 damage at range 3+"}, "range": 5},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": "\033[91m",
     "passives": {"name": "Berserker", "desc": "+3 Attack when below 30% HP and 10% lifesteal on hits"}},
    {"name": "Druid", "char": "D", "hp": 25, "base_attack": 5, "color_code": "\033[33m",
     "passives": {"name": "Nature's Wrath", "desc": "Enemies take 1-2 damage on hit and heal 1 HP every 40 turns"}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": "\033[93m",
     "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has 15% chance to strike twice"}},
    {"name": "Archer", "char": "A", "hp": 20, "base_attack": 5, "color_code": "\033[92m",
     "passives": {"name": "Deadly Aim", "desc": "Can attack at range 5 and deals +2 damage to unaware enemies"}, "range": 5},
    {"name": "Sorcerer", "char": "S", "hp": 16, "base_attack": 6, "color_code": "\033[35m",
     "passives": {"name": "Spell Mastery", "desc": "Range 6 attacks and 25% chance to hit all adjacent enemies"}, "range": 6},
]
ANSI_RESET = "\033[0m"

# --- Enemy Definitions ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "color_code": "\033[31m", "ai": "melee", "type": "living"},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "color_code": "\033[33m", "ai": "melee", "type": "living"},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "color_code": "\033[97m", "ai": "melee", "type": "undead"},
    {"name": "Archer", "char": "a", "hp": 8, "attack": 3, "defense": 0, "color_code": "\033[92m", "ai": "ranged", "range": 5, "type": "living"},
    {"name": "Mage", "char": "m", "hp": 12, "attack": 6, "defense": 0, "color_code": "\033[95m", "ai": "ranged", "range": 6, "type": "living"},
    {"name": "Zombie", "char": "z", "hp": 12, "attack": 4, "defense": 2, "color_code": "\033[90m", "ai": "melee", "type": "undead"}
]

# --- Player Stats ---
player_x, player_y = 0, 0
player_class_info = {}
player_char = "@"
player_max_hp, player_current_hp = 0, 0
player_fov_radius = BASE_FOV_RADIUS
turns_since_regen = 0
warrior_regen_timer = 0
druid_regen_timer = 0
seen_enemy_ids = set()
enemy_id_counter = 0

# --- Game State ---
goal_x, goal_y = 0, 0
enemies = []
turns = 0
game_message = ["Welcome! Explore and survive."]
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

# --- Rect Class ---
class Rect:
    def __init__(self, x, y, w, h): 
        self.x1, self.y1, self.x2, self.y2 = x, y, x+w, y+h
    def center(self): 
        return ((self.x1+self.x2)//2, (self.y1+self.y2)//2)
    def intersects(self, other): 
        return (self.x1<=other.x2 and self.x2>=other.x1 and self.y1<=other.y2 and self.y2>=other.y1)

# --- Player Initialization ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius
    global turns_since_regen, warrior_regen_timer, druid_regen_timer
    
    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]
    player_current_hp = player_max_hp
    player_char = player_class_info["char"]
    player_fov_radius = BASE_FOV_RADIUS
    turns_since_regen = 0
    warrior_regen_timer = 0
    druid_regen_timer = 0

    # Apply Ranger's FOV bonus
    if player_class_info["passives"]["name"] == "Hunter's Precision":
        player_fov_radius += 2
    
    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{ANSI_RESET}!")
    add_message(f"Passive: {player_class_info['passives']['name']} - {player_class_info['passives']['desc']}")

def get_player_attack_power():
    base_atk = player_class_info["base_attack"]
    
    # Mage: Arcane Mastery
    if player_class_info["passives"]["name"] == "Arcane Mastery":
        base_atk += 2
    
    # Barbarian: Berserker rage
    if player_class_info["passives"]["name"] == "Berserker":
        if player_current_hp <= math.floor(player_max_hp * 0.3):
            base_atk += 3
    
    return base_atk

# --- Map Generation ---
def create_room(room):
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: 
                game_map[y][x] = FLOOR_CHAR

def create_h_tunnel(x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: 
            game_map[y][x] = FLOOR_CHAR

def create_v_tunnel(y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: 
            game_map[y][x] = FLOOR_CHAR

def is_blocked(x, y, check_player=True):
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT): 
        return True
    if game_map[y][x] == WALL_CHAR: 
        return True
    if check_player and x == player_x and y == player_y: 
        return True
    if x == goal_x and y == goal_y: 
        return True
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: 
            return True
    return False

def spawn_enemies(room):
    global enemies, enemy_id_counter
    num_spawn = random.randint(0, MAX_ENEMIES_PER_ROOM)
    for _ in range(num_spawn):
        for _attempt in range(5):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and \
               game_map[y][x] == FLOOR_CHAR and not is_blocked(x, y, check_player=False):
                enemy_type = random.choice(ENEMY_TYPES)
                new_enemy = enemy_type.copy()
                new_enemy['x'], new_enemy['y'] = x, y
                new_enemy['current_hp'] = enemy_type['hp']
                new_enemy['id'] = enemy_id_counter
                enemy_id_counter += 1
                enemies.append(new_enemy)
                break

def generate_map():
    global game_map, player_x, player_y, goal_x, goal_y, fov_map, enemies, seen_enemy_ids, enemy_id_counter
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    enemies = []
    rooms = []
    seen_enemy_ids = set()
    enemy_id_counter = 0

    for r_idx in range(MAX_ROOMS):
        w, h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x, y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(other_room) for other_room in rooms): 
            continue
        
        create_room(new_room)
        (new_cx, new_cy) = new_room.center()
        if not rooms:  # First room
            player_x, player_y = new_cx, new_cy
        else:
            (prev_cx, prev_cy) = rooms[-1].center()
            if random.randint(0, 1) == 1:
                create_h_tunnel(prev_cx, new_cx, prev_cy)
                create_v_tunnel(prev_cy, new_cy, new_cx)
            else:
                create_v_tunnel(prev_cy, new_cy, prev_cx)
                create_h_tunnel(prev_cx, new_cx, new_cy)
            spawn_enemies(new_room)
        rooms.append(new_room)

    if not rooms:  # Fallback
        player_x, player_y = MAP_WIDTH//2, MAP_HEIGHT//2
        game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    
    # Place goal
    if len(rooms) > 1:
        last_room = rooms[-1]
        for _ in range(10):
            gx, gy = random.randint(last_room.x1 + 1, last_room.x2 - 1), random.randint(last_room.y1 + 1, last_room.y2 - 1)
            if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT and game_map[gy][gx] == FLOOR_CHAR and not (gx == player_x and gy == player_y):
                goal_x, goal_y = gx, gy
                game_map[goal_y][goal_x] = GOAL_CHAR
                break

    update_fov()

# --- FOV Calculation ---
def get_line(x1, y1, x2, y2):
    """Bresenham's Line Algorithm"""
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    if dx > dy:
        err = dx // 2
        while x != x2:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy // 2
        while y != y2:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x2, y2))
    return points

def update_fov():
    global fov_map
    for y_ in range(MAP_HEIGHT):
        for x_ in range(MAP_WIDTH):
            if fov_map[y_][x_] == 2: 
                fov_map[y_][x_] = 1
    
    for x_offset in range(-player_fov_radius, player_fov_radius + 1):
        for y_offset in range(-player_fov_radius, player_fov_radius + 1):
            if x_offset*x_offset + y_offset*y_offset > player_fov_radius*player_fov_radius: 
                continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): 
                continue
            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                if not (0 <= lx < MAP_WIDTH and 0 <= ly < MAP_HEIGHT): 
                    break
                fov_map[ly][lx] = 2
                if game_map[ly][lx] == WALL_CHAR: 
                    break

# --- Messaging ---
def add_message(msg):
    global game_message
    game_message.append(msg)
    if len(game_message) > 5: 
        game_message = game_message[-5:]

# --- Combat Effects ---
def add_combat_effect(x, y, effect_type, duration=2):
    global combat_effects
    combat_effects.append((x, y, effect_type, duration))

def update_combat_effects():
    global combat_effects
    combat_effects = [(x, y, effect, dur-1) for x, y, effect, dur in combat_effects if dur > 1]

# --- Combat System ---
def player_attack_enemy(enemy_obj):
    global enemies, player_current_hp
    current_player_atk = get_player_attack_power()
    enemy_def = enemy_obj.get('defense', 0)

    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)

    # Get distance for range bonuses
    dist = max(abs(enemy_obj['x'] - player_x), abs(enemy_obj['y'] - player_y))
    
    # Ki Master: Ignore 1 defense
    if player_class_info["passives"]["name"] == "Ki Master":
        enemy_def = max(0, enemy_def - 1)
    
    # Deadly Aim: +2 damage to unaware enemies
    if player_class_info["passives"]["name"] == "Deadly Aim" and enemy_obj['id'] not in seen_enemy_ids:
        current_player_atk += 2
        add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
    
    # Hunter's Precision: +1 damage at range 3+
    if player_class_info["passives"]["name"] == "Hunter's Precision" and dist >= 3:
        current_player_atk += 1
        add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)

    # Evasion Master: +2 damage to enemies below 50% HP
    if player_class_info["passives"]["name"] == "Evasion Master" and \
       enemy_obj['current_hp'] < enemy_obj['hp'] / 2:
        current_player_atk += 2

    # Divine Blessing: +1 damage to undead
    if player_class_info["passives"]["name"] == "Divine Blessing" and \
       enemy_obj.get('type') == 'undead':
        current_player_atk += 1

    damage = max(0, current_player_atk - enemy_def)
    
    # Arcane Mastery: 20% chance for +2 bonus damage
    if player_class_info["passives"]["name"] == "Arcane Mastery" and random.random() < 0.20:
        damage += 2
        add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
        add_message("Your spell crackles with extra power!")

    # Apply damage
    enemy_obj['current_hp'] -= damage
    
    # Berserker: 10% lifesteal
    if player_class_info["passives"]["name"] == "Berserker":
        heal = max(1, math.floor(damage * 0.1))
        if heal > 0 and player_current_hp < player_max_hp:
            player_current_hp = min(player_max_hp, player_current_hp + heal)
            add_combat_effect(player_x, player_y, EFFECT_HEAL)
            add_message(f"You drain {heal} life!")

    # Ki Master: 15% chance to strike twice
    if player_class_info["passives"]["name"] == "Ki Master" and random.random() < 0.15:
        enemy_obj['current_hp'] -= damage
        add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
        add_message("Your ki flows into a second strike!")

    # Nature's Wrath: Enemies take 1-2 additional damage
    if player_class_info["passives"]["name"] == "Nature's Wrath":
        nature_damage = random.randint(1, 2)
        enemy_obj['current_hp'] -= nature_damage
        add_message(f"Nature strikes for {nature_damage} additional damage!")

    # Spell Mastery: 25% chance to hit adjacent enemies
    if player_class_info["passives"]["name"] == "Spell Mastery" and random.random() < 0.25:
        add_message("Your spell erupts in a magical explosion!")
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: 
                    continue
                for other_enemy in list(enemies):
                    if other_enemy['x'] == enemy_obj['x'] + dx and \
                       other_enemy['y'] == enemy_obj['y'] + dy:
                        splash_damage = damage // 2
                        other_enemy['current_hp'] -= splash_damage
                        add_combat_effect(other_enemy['x'], other_enemy['y'], EFFECT_ATTACK)
                        if other_enemy['current_hp'] <= 0:
                            add_message(f"The explosion kills a {other_enemy['name']}!")
                            game_map[other_enemy['y']][other_enemy['x']] = DEAD_ENEMY_CHAR
                            enemies.remove(other_enemy)

    # Handle enemy death
    if enemy_obj['current_hp'] <= 0:
        add_message(f"You defeated the {enemy_obj['color_code']}{enemy_obj['name']}{ANSI_RESET}!")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        enemies.remove(enemy_obj)
    else:
        add_message(f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{ANSI_RESET} for {damage} damage. ({enemy_obj['current_hp']}/{enemy_obj['hp']} HP)")

def player_take_damage(damage_amount, enemy_attacker=None):
    global player_current_hp
    
    add_combat_effect(player_x, player_y, EFFECT_ATTACK)
    
    # Improved Fortitude: Take 1 less damage
    if player_class_info["passives"]["name"] == "Improved Fortitude":
        damage_amount = max(1, damage_amount - 1)

    # Evasion Master: 15% dodge chance
    if player_class_info["passives"]["name"] == "Evasion Master":
        if random.random() < 0.15:
            add_message(f"You deftly evade the attack!")
            return

    player_current_hp -= damage_amount
    add_message(f"You take {damage_amount} damage!")

    # Nature's Wrath: Thorns damage
    if player_class_info["passives"]["name"] == "Nature's Wrath" and enemy_attacker:
        if enemy_attacker in enemies:
            thorns_damage = random.randint(1, 2)
            enemy_attacker['current_hp'] -= thorns_damage
            add_combat_effect(enemy_attacker['x'], enemy_attacker['y'], EFFECT_ATTACK)
            add_message(f"Nature's thorns deal {thorns_damage} damage to the {enemy_attacker['name']}!")
            if enemy_attacker['current_hp'] <= 0:
                add_message(f"The {enemy_attacker['name']} succumbs to the thorns!")
                game_map[enemy_attacker['y']][enemy_attacker['x']] = DEAD_ENEMY_CHAR
                enemies.remove(enemy_attacker)

    if player_current_hp < 0: 
        player_current_hp = 0

# --- Drawing ---
def clear_screen():
    if os.name == 'nt': 
        _ = os.system('cls')
    else: 
        _ = os.system('clear')

def get_char_at(x, y):
    # Check for combat effects first
    for effect_x, effect_y, effect_type, _ in combat_effects:
        if effect_x == x and effect_y == y and effect_type in EFFECT_CHARS:
            return f"\033[1;33m{EFFECT_CHARS[effect_type]}\033[0m"
    
    if x == player_x and y == player_y:
        return f"{player_class_info['color_code']}{player_char}{ANSI_RESET}"
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y:
            return f"{enemy['color_code']}{enemy['char']}{ANSI_RESET}"
    return game_map[y][x]

def draw_game():
    clear_screen()
    update_combat_effects()
    
    for y_disp in range(MAP_HEIGHT):
        row_str = "".join(
            get_char_at(x_disp, y_disp) if fov_map[y_disp][x_disp] == 2 else
            (game_map[y_disp][x_disp] if fov_map[y_disp][x_disp] == 1 and game_map[y_disp][x_disp] != WALL_CHAR else
             (WALL_CHAR if fov_map[y_disp][x_disp] == 1 and game_map[y_disp][x_disp] == WALL_CHAR else UNSEEN_CHAR))
            for x_disp in range(MAP_WIDTH)
        )
        print(row_str)
    
    print("-" * MAP_WIDTH)
    
    # UI Panel
    class_display = f"Class: {player_class_info['color_code']}{player_class_info['name']}{ANSI_RESET}"
    hp_display = f"HP: {player_class_info['color_code']}{player_current_hp}/{player_max_hp}{ANSI_RESET}"
    current_attack = get_player_attack_power()
    attack_display = f"Atk: {current_attack}"
    
    if player_can_ranged_attack():
        attack_display += f" (Range: {player_ranged_range()})"
    
    if player_class_info["passives"]["name"] == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3):
        attack_display += " (Raging!)"
    
    turns_display = f"Turns: {turns}"
    print(f"{class_display:<25} {hp_display:<20} {attack_display:<20} {turns_display:<10}")
    
    passive_display = f"Passive: {player_class_info['passives']['name']}"
    print(f"{passive_display:<50} FOV: {player_fov_radius}")
    print("-" * MAP_WIDTH)
    
    for msg in game_message: 
        print(msg)
    print("Move:W,A,S,D | F:Ranged Attack | Q:Quit")

# --- Ranged Attack ---
def player_can_ranged_attack():
    return "range" in player_class_info

def player_ranged_range():
    return player_class_info.get("range", 1)

def player_ranged_attack():
    px, py = player_x, player_y
    rng = player_ranged_range()
    
    for enemy in enemies:
        ex, ey = enemy['x'], enemy['y']
        dist = max(abs(ex - px), abs(ey - py))
        if dist <= rng:
            # Check line of sight
            los = True
            for lx, ly in get_line(px, py, ex, ey)[1:-1]:
                if game_map[ly][lx] == WALL_CHAR:
                    los = False
                    break
            if los:
                player_attack_enemy(enemy)
                return True
    return False

# --- Game Logic ---
def handle_regeneration():
    global player_current_hp, turns_since_regen, warrior_regen_timer, druid_regen_timer
    
    # Divine Blessing: Heal 1 HP every 20 turns
    if player_class_info["passives"]["name"] == "Divine Blessing":
        if turns_since_regen >= 20:
            if player_current_hp < player_max_hp:
                player_current_hp += 1
                add_combat_effect(player_x, player_y, EFFECT_HEAL)
                add_message("Divine blessing restores 1 HP.")
            turns_since_regen = 0
    
    # Improved Fortitude: Heal 1 HP every 30 turns
    if player_class_info["passives"]["name"] == "Improved Fortitude":
        warrior_regen_timer += 1
        if warrior_regen_timer >= 30:
            if player_current_hp < player_max_hp:
                player_current_hp += 1
                add_combat_effect(player_x, player_y, EFFECT_HEAL)
                add_message("Your fortitude restores 1 HP.")
            warrior_regen_timer = 0
    
    # Nature's Wrath: Heal 1 HP every 40 turns
    if player_class_info["passives"]["name"] == "Nature's Wrath":
        druid_regen_timer += 1
        if druid_regen_timer >= 40:
            if player_current_hp < player_max_hp:
                player_current_hp += 1
                add_combat_effect(player_x, player_y, EFFECT_HEAL)
                add_message("Nature's energy restores 1 HP.")
            druid_regen_timer = 0

def handle_input():
    global player_x, player_y, turns, game_message, player_current_hp, turns_since_regen
    
    action = input("> ").lower()
    old_px, old_py = player_x, player_y
    moved = False

    if len(game_message) > 0 and not any(kw in game_message[-1] for kw in ["Ouch!", "Invalid", "You are", "Passive:"]):
        game_message = []

    if action == 'w': 
        player_y -= 1
        moved = True
    elif action == 's': 
        player_y += 1
        moved = True
    elif action == 'a': 
        player_x -= 1
        moved = True
    elif action == 'd': 
        player_x += 1
        moved = True
    elif action == 'f':
        if player_can_ranged_attack():
            if not player_ranged_attack():
                add_message("No enemy in range/line of sight.")
        else:
            add_message("Your class cannot perform ranged attacks.")
        turns += 1
        turns_since_regen += 1
        handle_regeneration()
        enemy_turn()
        if player_current_hp <= 0: 
            return "lost"
        return "playing"
    elif action == 'q': 
        return "quit"
    else: 
        add_message("Invalid command.")
        return "playing"

    turns += 1
    turns_since_regen += 1
    handle_regeneration()

    # Check collision
    if not (0 <= player_x < MAP_WIDTH and 0 <= player_y < MAP_HEIGHT) or \
       game_map[player_y][player_x] == WALL_CHAR:
        add_message("Ouch! A wall.")
        player_x, player_y = old_px, old_py
        moved = False
    
    if moved:
        update_fov()
        if player_x == goal_x and player_y == goal_y: 
            return "won"

        # Auto-attack adjacent enemies
        attacked_this_turn = False
        for dx_check in range(-1, 2):
            for dy_check in range(-1, 2):
                if dx_check == 0 and dy_check == 0: 
                    continue
                target_x, target_y = player_x + dx_check, player_y + dy_check
                if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): 
                    continue
                if fov_map[target_y][target_x] == 2:
                    for enemy in list(enemies):
                        if enemy['x'] == target_x and enemy['y'] == target_y:
                            player_attack_enemy(enemy)
                            attacked_this_turn = True
                            break
                if attacked_this_turn: 
                    break
            if attacked_this_turn: 
                break

        # Auto-ranged attack if available and no melee attack occurred
        if not attacked_this_turn and player_can_ranged_attack():
            player_ranged_attack()
        
        # Update seen enemies using IDs
        for enemy in enemies:
            if fov_map[enemy['y']][enemy['x']] == 2:
                seen_enemy_ids.add(enemy['id'])

        enemy_turn()
    
    if player_current_hp <= 0: 
        return "lost"
    return "playing"

# --- Enemy AI ---
def enemy_turn():
    global player_current_hp
    px, py = player_x, player_y
    
    for enemy in list(enemies):
        ex, ey = enemy['x'], enemy['y']
        
        # If adjacent, attack
        if abs(ex - px) <= 1 and abs(ey - py) <= 1:
            player_take_damage(enemy['attack'], enemy_attacker=enemy)
            add_message(f"The {enemy['color_code']}{enemy['name']}{ANSI_RESET} attacks you for {enemy['attack']} damage!")
            continue
        
        # Ranged enemy: attack if in range and line of sight
        if enemy.get('ai') == 'ranged':
            rng = enemy.get('range', 5)
            dist = max(abs(ex - px), abs(ey - py))
            if dist <= rng:
                # Check line of sight
                los = True
                for lx, ly in get_line(ex, ey, px, py):
                    if (lx, ly) == (ex, ey) or (lx, ly) == (px, py): 
                        continue
                    if game_map[ly][lx] == WALL_CHAR:
                        los = False
                        break
                if los:
                    player_take_damage(enemy['attack'], enemy_attacker=enemy)
                    add_message(f"The {enemy['color_code']}{enemy['name']}{ANSI_RESET} fires a ranged attack at you!")
                    continue
        
        # Move towards player if in FOV
        if fov_map[ey][ex] == 2:
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            nx, ny = ex + dx, ey + dy
            if not is_blocked(nx, ny, check_player=False) and (nx, ny) != (goal_x, goal_y):
                enemy['x'], enemy['y'] = nx, ny

# --- Main Game Loop ---
def game_loop():
    global game_message, turns, player_current_hp, player_class_info
    initialize_player()
    generate_map()
    game_state = "playing"
    
    while game_state == "playing":
        draw_game()
        game_state = handle_input()

    draw_game() 
    end_color = player_class_info.get('color_code', ANSI_RESET)
    end_name = player_class_info.get('name', 'Adventurer')
    
    if game_state == "won": 
        add_message(f"VICTORY! Goal reached in {turns} turns as a {end_color}{end_name}{ANSI_RESET}!")
    elif game_state == "lost": 
        add_message(f"DEFEAT! Died after {turns} turns as a {end_color}{end_name}{ANSI_RESET}. Game Over.")
    elif game_state == "quit": 
        add_message(f"You quit after {turns} turns. Farewell, {end_color}{end_name}{ANSI_RESET}!")
    
    print("-" * MAP_WIDTH)
    for msg in game_message: 
        print(msg)
    print(ANSI_RESET)

if __name__ == "__main__":
    try: 
        game_loop()
    finally: 
        print(ANSI_RESET)  # Ensure color reset