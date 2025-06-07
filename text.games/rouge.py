import os
import random
import math

# --- Game Settings ---
MAP_WIDTH = 60
MAP_HEIGHT = 28
FLOOR_CHAR = "."
WALL_CHAR = "#"
GOAL_CHAR = "G"
DEAD_ENEMY_CHAR = "%"
UNSEEN_CHAR = ' '

# --- Color Definitions ---
class Colors:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    STRIKETHROUGH = "\033[9m"
    RESET = "\033[0m"

# --- Environment Color Settings ---
FLOOR_COLOR = Colors.BRIGHT_BLACK
WALL_COLOR = Colors.WHITE
GOAL_COLOR = Colors.BOLD + Colors.BRIGHT_YELLOW + Colors.BG_BLUE
DEAD_ENEMY_COLOR = Colors.DIM + Colors.RED
UNSEEN_COLOR = Colors.BLACK

# --- Combat Effects ---
EFFECT_ATTACK = 1
EFFECT_CRIT = 2
EFFECT_HEAL = 3
combat_effects = []
EFFECT_CHARS = {
    EFFECT_ATTACK: f"{Colors.BOLD}{Colors.BRIGHT_RED}*{Colors.RESET}",
    EFFECT_CRIT: f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}⚔{Colors.RESET}",
    EFFECT_HEAL: f"{Colors.BOLD}{Colors.BRIGHT_GREEN}+{Colors.RESET}"
}

ROOM_MAX_SIZE = 12
ROOM_MIN_SIZE = 6
MAX_ROOMS = 25
MAX_ENEMIES_PER_ROOM = 3
BASE_FOV_RADIUS = 8

# --- Player Class Definitions ---
PLAYER_CLASSES = [
    {"name": "Warrior", "char": "W", "hp": 30, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_BLUE,
     "passives": {"name": "Improved Fortitude", "desc": "Takes 1 less damage from melee attacks and regenerates 1 HP every 30 turns"}},
    {"name": "Rogue", "char": "R", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.GREEN,
     "passives": {"name": "Evasion Master", "desc": "15% dodge chance and deals +2 damage to enemies below 50% HP"}},
    {"name": "Mage", "char": "M", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_MAGENTA,
     "passives": {"name": "Arcane Mastery", "desc": "Deals +2 damage and has 20% chance to deal 2 bonus damage"}, "range": 4},
    {"name": "Cleric", "char": "C", "hp": 26, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_CYAN,
     "passives": {"name": "Divine Blessing", "desc": "Heals 1 HP every 20 turns and deals +1 damage to undead"}},
    {"name": "Ranger", "char": "N", "hp": 24, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_GREEN,
     "passives": {"name": "Keen Eyes", "desc": "Increased Field of View (+2 radius)"}},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_RED,
     "passives": {"name": "Berserker", "desc": "+3 Attack when below 30% HP and 10% lifesteal on hits"}},
    {"name": "Druid", "char": "D", "hp": 25, "base_attack": 5, "color_code": Colors.BOLD + Colors.YELLOW,
     "passives": {"name": "Nature's Wrath", "desc": "Enemies take 1-2 damage on hit and heal 1 HP every 40 turns"}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW,
     "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has 15% chance to strike twice"}},
]

# --- Enemy Definitions with XP Value ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "xp_value": 10, "color_code": Colors.BOLD + Colors.RED, "ai": "melee", "type": "living"},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "xp_value": 25, "color_code": Colors.BOLD + Colors.YELLOW, "ai": "melee", "type": "living"},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "xp_value": 15, "color_code": Colors.BOLD + Colors.WHITE, "ai": "melee", "type": "undead"},
]

# --- Global Player and Game State Variables ---
player_x, player_y = 0, 0
player_class_info = {}
player_char = "@"
player_max_hp, player_current_hp = 0, 0
player_fov_radius = BASE_FOV_RADIUS
turns_since_regen = 0
warrior_regen_timer = 0
druid_regen_timer = 0
goal_x, goal_y = 0, 0
enemies = []
turns = 0
game_message = ["Welcome! Explore and survive."]
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
# XP and Leveling System
player_level = 1
player_xp = 0
xp_to_next_level = 100

# --- Rect Class for Map Generation ---
class Rect:
    def __init__(self, x, y, w, h):
        self.x1, self.y1, self.x2, self.y2 = x, y, x + w, y + h
    def center(self):
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1)

# --- General Functions ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Initialization ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius
    global turns_since_regen, warrior_regen_timer, druid_regen_timer
    global player_level, player_xp, xp_to_next_level

    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]
    player_current_hp = player_max_hp
    player_char = player_class_info["char"]
    player_fov_radius = BASE_FOV_RADIUS
    turns_since_regen, warrior_regen_timer, druid_regen_timer = 0, 0, 0
    player_level, player_xp, xp_to_next_level = 1, 0, 100

    if player_class_info["passives"]["name"] == "Keen Eyes":
        player_fov_radius += 2

    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET}!")
    add_message(f"{Colors.BRIGHT_CYAN}Passive:{Colors.RESET} {Colors.BRIGHT_YELLOW}{player_class_info['passives']['name']}{Colors.RESET} - {player_class_info['passives']['desc']}")

def get_player_attack_power():
    base_atk = player_class_info["base_attack"]
    passive = player_class_info["passives"]["name"]
    if passive == "Arcane Mastery": base_atk += 2
    elif passive == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3): base_atk += 3
    return base_atk

# --- Map Generation ---
def create_room(room):
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: game_map[y][x] = FLOOR_CHAR

def create_h_tunnel(x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: game_map[y][x] = FLOOR_CHAR

def create_v_tunnel(y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: game_map[y][x] = FLOOR_CHAR

def is_blocked(x, y):
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT) or game_map[y][x] == WALL_CHAR: return True
    if x == player_x and y == player_y: return True
    return any(enemy['x'] == x and enemy['y'] == y for enemy in enemies)

def spawn_enemies(room):
    global enemies
    num_spawn = random.randint(0, MAX_ENEMIES_PER_ROOM)
    for _ in range(num_spawn):
        for _attempt in range(10):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and not is_blocked(x, y):
                enemy_type = random.choice(ENEMY_TYPES)
                new_enemy = enemy_type.copy()
                new_enemy.update({'x': x, 'y': y, 'current_hp': enemy_type['hp']})
                enemies.append(new_enemy)
                break

def generate_map():
    global game_map, player_x, player_y, goal_x, goal_y, fov_map, enemies
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    enemies, rooms = [], []

    for _ in range(MAX_ROOMS):
        w, h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x, y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(other_room) for other_room in rooms): continue

        create_room(new_room)
        (new_cx, new_cy) = new_room.center()
        if not rooms:
            player_x, player_y = new_cx, new_cy
        else:
            (prev_cx, prev_cy) = rooms[-1].center()
            if random.randint(0, 1): create_h_tunnel(prev_cx, new_cx, prev_cy); create_v_tunnel(prev_cy, new_cy, new_cx)
            else: create_v_tunnel(prev_cy, new_cy, prev_cx); create_h_tunnel(prev_cx, new_cx, new_cy)
            spawn_enemies(new_room)
        rooms.append(new_room)

    if not rooms:
        player_x, player_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    
    if rooms:
        goal_x, goal_y = rooms[-1].center()
        game_map[goal_y][goal_x] = GOAL_CHAR
    update_fov()

# --- FOV Calculation ---
def get_line(x1, y1, x2, y2):
    points, dx, dy = [], abs(x2 - x1), abs(y2 - y1)
    x, y, sx, sy = x1, y1, 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
    if dx > dy:
        err = dx / 2.0
        while True:
            points.append((x, y));
            if x == x2: break
            err -= dy;
            if err < 0: y += sy; err += dx
            x += sx
    else:
        err = dy / 2.0
        while True:
            points.append((x, y));
            if y == y2: break
            err -= dx;
            if err < 0: x += sx; err += dy
            y += sy
    return points

def update_fov():
    global fov_map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if fov_map[y][x] == 2: fov_map[y][x] = 1

    for x_offset in range(-player_fov_radius, player_fov_radius + 1):
        for y_offset in range(-player_fov_radius, player_fov_radius + 1):
            if x_offset*x_offset + y_offset*y_offset > player_fov_radius**2: continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
            
            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                fov_map[ly][lx] = 2
                if game_map[ly][lx] == WALL_CHAR: break

# --- Messaging & Combat Effects ---
def add_message(msg):
    global game_message; game_message.append(msg)
    if len(game_message) > 5: game_message = game_message[-5:]

def add_combat_effect(x, y, effect_type, duration=2):
    combat_effects.append((x, y, effect_type, duration))

def update_combat_effects():
    global combat_effects; combat_effects[:] = [(x,y,e,d-1) for x,y,e,d in combat_effects if d > 1]

# --- Drawing ---
def get_char_at(x, y):
    for ex, ey, eft, _ in combat_effects:
        if ex == x and ey == y: return EFFECT_CHARS[eft]
    if x == player_x and y == player_y: return f"{player_class_info.get('color_code', Colors.RESET)}{player_char}{Colors.RESET}"
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: return f"{enemy['color_code']}{enemy['char']}{Colors.RESET}"
    char = game_map[y][x]
    if char == FLOOR_CHAR: return f"{FLOOR_COLOR}{FLOOR_CHAR}{Colors.RESET}"
    elif char == WALL_CHAR: return f"{WALL_COLOR}{WALL_CHAR}{Colors.RESET}"
    elif char == GOAL_CHAR: return f"{GOAL_COLOR}{GOAL_CHAR}{Colors.RESET}"
    elif char == DEAD_ENEMY_CHAR: return f"{DEAD_ENEMY_COLOR}{DEAD_ENEMY_CHAR}{Colors.RESET}"
    return char

# --- Combat System ---
def player_attack_enemy(enemy_obj):
    global enemies, player_current_hp; current_player_atk = get_player_attack_power()
    enemy_def = enemy_obj.get('defense', 0); damage = max(0, current_player_atk - enemy_def)
    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)
    enemy_obj['current_hp'] -= damage
    if enemy_obj['current_hp'] <= 0:
        add_message(f"{Colors.BRIGHT_GREEN}You defeated the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET}!{Colors.RESET}")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        gain_xp(enemy_obj.get('xp_value', 0)) # Gain XP on kill
        enemies[:] = [e for e in enemies if e != enemy_obj]
    else:
        add_message(f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET} for {Colors.BRIGHT_RED}{damage}{Colors.RESET} damage.")

def player_take_damage(damage_amount):
    global player_current_hp; add_combat_effect(player_x, player_y, EFFECT_ATTACK)
    passive = player_class_info["passives"]["name"]
    if passive == "Improved Fortitude": damage_amount = max(1, damage_amount - 1)
    if random.random() < 0.15 and passive == "Evasion Master": add_message(f"{Colors.BRIGHT_CYAN}You deftly evade the attack!{Colors.RESET}"); return
    player_current_hp -= damage_amount; add_message(f"{Colors.BRIGHT_RED}You take {damage_amount} damage!{Colors.RESET}")
    if player_current_hp < 0: player_current_hp = 0

# --- XP and Leveling Up ---
def level_up_bonus():
    global player_max_hp, player_current_hp
    add_message("Choose a bonus: (1) +20 Max HP, (2) +2 Attack")
    while True:
        draw_game()
        choice = input("> Your choice: ").lower()
        if choice == '1':
            player_max_hp += 20
            player_current_hp = player_max_hp # Full heal
            add_message("Your maximum health increases!"); break
        elif choice == '2':
            player_class_info['base_attack'] += 2
            add_message("Your base attack increases!"); break
        else:
            add_message("Invalid choice.")

def gain_xp(amount):
    global player_xp, xp_to_next_level, player_level, player_current_hp
    player_xp += amount
    add_message(f"You gain {amount} XP.")
    if player_xp >= xp_to_next_level:
        player_xp -= xp_to_next_level
        player_level += 1
        xp_to_next_level = int(xp_to_next_level * 1.5)
        player_current_hp = player_max_hp # Fully heal on level up
        add_message(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}LEVEL UP! You are now level {player_level}!{Colors.RESET}")
        level_up_bonus()

# --- AI and Turns ---
def enemy_turn():
    global player_current_hp
    for enemy in list(enemies):
        if enemy['current_hp'] <= 0: continue
        ex, ey = enemy['x'], enemy['y']
        if fov_map[ey][ex] != 2: continue
        player_dist = max(abs(ex - player_x), abs(ey - player_y))
        if player_dist <= 1: player_take_damage(enemy['attack'])
        else:
            dx = 1 if player_x > ex else -1 if player_x < ex else 0
            dy = 1 if player_y > ey else -1 if player_y < ey else 0
            nx, ny = ex + dx, ey + dy
            if not is_blocked(nx, ny): enemy['x'], enemy['y'] = nx, ny

# --- Drawing ---
def draw_game():
    clear_screen(); update_combat_effects();
    border = "═" * (MAP_WIDTH + 2); print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    for y in range(MAP_HEIGHT):
        row_str = f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
        for x in range(MAP_WIDTH):
            if fov_map[y][x] == 2: row_str += get_char_at(x,y)
            elif fov_map[y][x] == 1:
                char = game_map[y][x];
                if char == WALL_CHAR: row_str += f"{Colors.DIM}{WALL_COLOR}{char}{Colors.RESET}"
                else: row_str += f"{Colors.DIM}{FLOOR_COLOR}{char}{Colors.RESET}"
            else: row_str += f"{UNSEEN_COLOR}{UNSEEN_CHAR}{Colors.RESET}"
        row_str += f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"; print(row_str)
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    
    # UI Panel
    hp_perc = player_current_hp / player_max_hp if player_max_hp > 0 else 0
    hp_color = Colors.BRIGHT_GREEN if hp_perc > 0.7 else Colors.BRIGHT_YELLOW if hp_perc > 0.3 else Colors.BRIGHT_RED
    hp_display = f"{Colors.BOLD}HP:{Colors.RESET} {hp_color}{player_current_hp}/{player_max_hp}{Colors.RESET}"
    attack_display = f"{Colors.BOLD}Atk:{Colors.RESET} {Colors.BRIGHT_RED}{get_player_attack_power()}{Colors.RESET}"
    level_display = f"{Colors.BOLD}Lvl:{Colors.RESET} {Colors.BRIGHT_YELLOW}{player_level}{Colors.RESET} ({player_xp}/{xp_to_next_level} XP)"
    
    print(f"{Colors.BOLD}Class:{Colors.RESET} {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET} | {hp_display} | {attack_display} | {Colors.BOLD}Turns:{Colors.RESET} {Colors.BRIGHT_CYAN}{turns}{Colors.RESET}")
    print(level_display)
    
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}")
    for msg in game_message: print(msg)
    print(f"{Colors.BOLD}Move:{Colors.YELLOW}W,A,S,D{Colors.RESET} | {Colors.BOLD}Quit:{Colors.RED}Q{Colors.RESET}")

# --- Main Game Logic ---
def handle_input():
    global player_x, player_y, turns
    action = input("> ").lower()
    
    target_x, target_y = player_x, player_y
    moved = False

    if action == 'w': target_y -= 1; moved = True
    elif action == 's': target_y += 1; moved = True
    elif action == 'a': target_x -= 1; moved = True
    elif action == 'd': target_x += 1; moved = True
    elif action == 'q': return "quit"
    else: add_message(f"{Colors.BRIGHT_RED}Invalid command.{Colors.RESET}"); return "playing"

    turns += 1
    
    if moved:
        if not is_blocked(target_x, target_y):
            player_x, player_y = target_x, target_y
            update_fov()
        else:
            bumped_enemy = next((e for e in enemies if e['x'] == target_x and e['y'] == target_y), None)
            if bumped_enemy: player_attack_enemy(bumped_enemy)
            else: add_message(f"{Colors.BRIGHT_RED}Ouch! A wall.{Colors.RESET}")

    enemy_turn()

    if player_x == goal_x and player_y == goal_y: return "won"
    if player_current_hp <= 0: return "lost"
    return "playing"

# --- Main Game Loop ---
def game_loop():
    initialize_player(); generate_map()
    game_state = "playing"
    while game_state == "playing":
        draw_game(); game_state = handle_input()

    draw_game()
    end_color = player_class_info.get('color_code', Colors.RESET)
    end_name = player_class_info.get('name', 'Adventurer')
    final_message = ""
    if game_state == "won": final_message = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 VICTORY! Goal reached in {turns} turns as a {end_color}{end_name}{Colors.RESET}!"
    elif game_state == "lost": final_message = f"{Colors.BOLD}{Colors.BRIGHT_RED}💀 DEFEAT! Died after {turns} turns as a {end_color}{end_name}{Colors.RESET}."
    elif game_state == "quit": final_message = f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}You quit after {turns} turns. Farewell, {end_color}{end_name}{Colors.RESET}!"
    
    print(final_message)


if __name__ == "__main__":
    try: game_loop()
    except Exception as e:
        print(f"\n--- PYTHON ROGUE: UNEXPECTED ERROR ---"); print(f"Error: {e}"); import traceback; traceback.print_exc(); print(f"------------------------------------------\n")
    finally: print(Colors.RESET)
