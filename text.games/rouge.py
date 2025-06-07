import os
import random
import math

# --- Game Settings ---
MAP_WIDTH = 60
MAP_HEIGHT = 28
FLOOR_CHAR = "."
WALL_CHAR = "#"
STAIRS_DOWN_CHAR = ">"
DEAD_ENEMY_CHAR = "%"
UNSEEN_CHAR = ' '
CHEST_CHAR = "C"
BOSS_FLOOR = 5

# --- Color Definitions ---
class Colors:
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = (f"\033[3{i}m" for i in range(8))
    BRIGHT_BLACK, BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE, BRIGHT_MAGENTA, BRIGHT_CYAN, BRIGHT_WHITE = (f"\033[9{i}m" for i in range(8))
    BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"

# --- Environment Color Settings ---
FLOOR_COLOR = Colors.BRIGHT_BLACK
WALL_COLOR = Colors.WHITE
STAIRS_COLOR = Colors.BOLD + Colors.BRIGHT_MAGENTA
DEAD_ENEMY_COLOR = Colors.DIM + Colors.RED
UNSEEN_COLOR = Colors.BLACK
CHEST_COLOR = Colors.BOLD + Colors.YELLOW

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
MAX_ENEMIES_PER_ROOM = 2
MAX_CHESTS_PER_ROOM = 1
BASE_FOV_RADIUS = 8

# --- Item & Weapon System ---
class Item:
    def __init__(self, name, char='!'): self.name, self.char = name, char
class Weapon(Item):
    def __init__(self, name, damage_bonus, char='/'): super().__init__(name, char); self.damage_bonus = damage_bonus
class Potion(Item):
    def __init__(self, name, heal_amount, char='!'): super().__init__(name, char); self.heal_amount = heal_amount
class Scroll(Item):
     def __init__(self, name, effect, char='?'): super().__init__(name, char); self.effect = effect

# --- Item/Weapon Definitions ---
POTION_TYPES = [Potion("Healing Potion", 15), Potion("Greater Healing Potion", 30)]
WEAPON_TYPES = [Weapon("Dagger", 2), Weapon("Shortsword", 4), Weapon("Longsword", 6), Weapon("Greatsword", 8)]
SCROLL_TYPES = [Scroll("Scroll of Fireball", "fireball")]
CHEST_LOOT_TABLE = POTION_TYPES + WEAPON_TYPES + SCROLL_TYPES

# --- Player Class Definitions ---
PLAYER_CLASSES = [
    {"name": "Warrior", "char": "W", "hp": 30, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_BLUE, "passives": {"name": "Improved Fortitude", "desc": "Takes 1 less damage from melee attacks and regenerates 1 HP every 30 turns"}},
    {"name": "Rogue", "char": "R", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.GREEN, "passives": {"name": "Evasion Master", "desc": "15% dodge chance and deals +2 damage to enemies below 50% HP"}},
    {"name": "Mage", "char": "M", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_MAGENTA, "passives": {"name": "Arcane Mastery", "desc": "Deals +2 damage and has 20% chance to deal 2 bonus damage"}, "range": 4},
    {"name": "Cleric", "char": "C", "hp": 26, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_CYAN, "passives": {"name": "Divine Blessing", "desc": "Heals 1 HP every 20 turns and deals +1 damage to undead"}},
    {"name": "Ranger", "char": "N", "hp": 24, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_GREEN, "passives": {"name": "Keen Eyes", "desc": "Increased Field of View (+2 radius)"}},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "passives": {"name": "Berserker", "desc": "+3 Attack when below 30% HP and 10% lifesteal on hits"}},
    {"name": "Druid", "char": "D", "hp": 25, "base_attack": 5, "color_code": Colors.BOLD + Colors.YELLOW, "passives": {"name": "Nature's Wrath", "desc": "Enemies take 1-2 damage on hit and heal 1 HP every 40 turns"}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW, "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has 15% chance to strike twice"}},
]

# --- Enemy Definitions with XP Value ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "xp_value": 10, "color_code": Colors.BOLD + Colors.RED, "spawn_level": 1},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "xp_value": 25, "color_code": Colors.BOLD + Colors.YELLOW, "spawn_level": 2},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "xp_value": 15, "color_code": Colors.BOLD + Colors.WHITE, "spawn_level": 1},
    {"name": "The Balrog", "char": "B", "hp": 150, "attack": 12, "defense": 5, "xp_value": 500, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "spawn_level": BOSS_FLOOR},
]

# --- Global Player and Game State Variables ---
player_x, player_y = 0, 0
player_class_info = {}
player_char = "@"
player_max_hp, player_current_hp = 0, 0
player_fov_radius = BASE_FOV_RADIUS
turns = 0
dungeon_level = 1
enemies = []
chests = []
inventory = []
equipped_weapon = None
game_message = ["Welcome! Explore and survive."]
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
player_level = 1
player_xp = 0
xp_to_next_level = 50

# --- Rect Class for Map Generation ---
class Rect:
    def __init__(self, x, y, w, h): self.x1, self.y1, self.x2, self.y2 = x,y,x+w,y+h
    def center(self): return ((self.x1+self.x2)//2, (self.y1+self.y2)//2)
    def intersects(self, other): return (self.x1<=other.x2 and self.x2>=other.x1 and self.y1<=other.y2 and self.y2>=other.y1)

# --- General Functions ---
def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')

# --- Initialization ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius
    global player_level, player_xp, xp_to_next_level, equipped_weapon, inventory

    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]
    player_current_hp = player_max_hp
    player_char = player_class_info["char"]
    player_fov_radius = BASE_FOV_RADIUS
    player_level, player_xp, xp_to_next_level = 1, 0, 50
    equipped_weapon = Weapon("Fists", 1)
    inventory = []

    if player_class_info["passives"]["name"] == "Keen Eyes": player_fov_radius += 2

    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET}!")
    add_message(f"{Colors.BRIGHT_CYAN}Passive:{Colors.RESET} {player_class_info['passives']['name']}{Colors.RESET} - {player_class_info['passives']['desc']}")

def get_player_attack_power():
    base_atk = player_class_info["base_attack"]
    weapon_bonus = equipped_weapon.damage_bonus if equipped_weapon else 0
    passive = player_class_info["passives"]["name"]
    if passive == "Arcane Mastery": base_atk += 2
    elif passive == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3): base_atk += 3
    return base_atk + weapon_bonus

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

def spawn_entities(room):
    global enemies, chests
    eligible_enemies = [e for e in ENEMY_TYPES if e['spawn_level'] <= dungeon_level and e['name'] != 'The Balrog']
    if not eligible_enemies: return

    num_enemies = random.randint(0, MAX_ENEMIES_PER_ROOM + dungeon_level // 2)
    for _ in range(num_enemies):
        for _attempt in range(10):
            x = random.randint(room.x1 + 1, room.x2 - 1); y = random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and not is_blocked(x, y):
                enemy_type = random.choice(eligible_enemies); new_enemy = enemy_type.copy()
                new_enemy.update({'x': x, 'y': y, 'current_hp': enemy_type['hp']}); enemies.append(new_enemy); break
    
    num_chests = random.randint(0, MAX_CHESTS_PER_ROOM)
    for _ in range(num_chests):
        for _attempt in range(10):
            x, y = random.randint(room.x1 + 1, room.x2 - 1), random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and not is_blocked(x, y):
                chests.append((x,y)); break

def generate_map():
    global game_map, player_x, player_y, fov_map, enemies, chests
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    enemies, rooms, chests = [], [], []

    for _ in range(MAX_ROOMS):
        w,h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x,y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(other) for other in rooms): continue
        create_room(new_room)
        (new_cx, new_cy) = new_room.center()
        if not rooms: player_x, player_y = new_cx, new_cy
        else:
            (prev_cx, prev_cy) = rooms[-1].center()
            if random.randint(0,1): create_h_tunnel(prev_cx, new_cx, prev_cy); create_v_tunnel(prev_cy, new_cy, new_cx)
            else: create_v_tunnel(prev_cy, new_cy, prev_cx); create_h_tunnel(prev_cx, new_cx, new_cy)
        if dungeon_level != BOSS_FLOOR: spawn_entities(new_room)
        rooms.append(new_room)

    if not rooms:
        player_x, player_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    
    if rooms:
        final_room_center = rooms[-1].center()
        if dungeon_level == BOSS_FLOOR:
            boss_type = next(e for e in ENEMY_TYPES if e['name'] == 'The Balrog'); boss = boss_type.copy()
            boss.update({'x': final_room_center[0], 'y': final_room_center[1], 'current_hp': boss_type['hp']})
            enemies.append(boss); add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}You have entered the Balrog's Lair!{Colors.RESET}")
        else:
            game_map[final_room_center[1]][final_room_center[0]] = STAIRS_DOWN_CHAR
    update_fov()

# --- FOV Calculation, Messaging, Effects, Drawing ---
def get_line(x1, y1, x2, y2):
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    if dx > dy:
        err = dx / 2.0
        while True:
            points.append((x, y))
            if x == x2: break
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while True:
            points.append((x, y))
            if y == y2: break
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    return points

def update_fov():
    global fov_map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if fov_map[y][x] == 2: fov_map[y][x] = 1
    for x_offset in range(-player_fov_radius, player_fov_radius + 1):
        for y_offset in range(-player_fov_radius, player_fov_radius + 1):
            if x_offset**2 + y_offset**2 > player_fov_radius**2: continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                fov_map[ly][lx] = 2
                if game_map[ly][lx] == WALL_CHAR: break

def add_message(msg):
    global game_message; game_message.append(msg)
    if len(game_message) > 5: game_message = game_message[-5:]

def add_combat_effect(x, y, effect_type, duration=2): combat_effects.append((x, y, effect_type, duration))
def update_combat_effects():
    global combat_effects; combat_effects[:] = [(x,y,e,d-1) for x,y,e,d in combat_effects if d > 1]

def get_char_at(x, y):
    for ex, ey, eft, _ in combat_effects:
        if ex == x and ey == y: return EFFECT_CHARS[eft]
    if x == player_x and y == player_y: return f"{player_class_info.get('color_code', Colors.RESET)}{player_char}{Colors.RESET}"
    if any(c[0] == x and c[1] == y for c in chests): return f"{CHEST_COLOR}{CHEST_CHAR}{Colors.RESET}"
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: return f"{enemy['color_code']}{enemy['char']}{Colors.RESET}"
    char = game_map[y][x]
    color_map = {FLOOR_CHAR: FLOOR_COLOR, WALL_CHAR: WALL_COLOR, STAIRS_DOWN_CHAR: STAIRS_COLOR, DEAD_ENEMY_CHAR: DEAD_ENEMY_COLOR}
    return f"{color_map.get(char, Colors.WHITE)}{char}{Colors.RESET}"

# --- Combat System ---
def player_attack_enemy(enemy_obj):
    global enemies, player_current_hp; current_player_atk = get_player_attack_power()
    enemy_def = enemy_obj.get('defense', 0); damage = max(0, current_player_atk - enemy_def)
    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)
    enemy_obj['current_hp'] -= damage
    if enemy_obj['current_hp'] <= 0:
        add_message(f"{Colors.BRIGHT_GREEN}You defeated the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET}!{Colors.RESET}")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        gain_xp(enemy_obj.get('xp_value', 0))
        if enemy_obj['name'] == 'The Balrog': return "won"
        enemies[:] = [e for e in enemies if e != enemy_obj]
    else:
        add_message(f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET} for {Colors.BRIGHT_RED}{damage}{Colors.RESET} damage.")
    return "playing"

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
        draw_game(); choice = input("> Your choice: ").lower()
        if choice == '1': player_max_hp += 20; player_current_hp = player_max_hp; add_message("Your maximum health increases!"); break
        elif choice == '2': player_class_info['base_attack'] += 2; add_message("Your base attack increases!"); break
        else: add_message("Invalid choice.")

def gain_xp(amount):
    global player_xp, xp_to_next_level, player_level, player_current_hp
    player_xp += amount; add_message(f"You gain {amount} XP.")
    if player_xp >= xp_to_next_level:
        player_xp -= xp_to_next_level; player_level += 1; xp_to_next_level = int(xp_to_next_level * 1.5)
        player_current_hp = player_max_hp
        add_message(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}LEVEL UP! You are now level {player_level}!{Colors.RESET}")
        level_up_bonus()

# --- AI and Turns ---
def enemy_turn():
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
    weapon_display = f"{Colors.BOLD}Weapon:{Colors.RESET} {equipped_weapon.name if equipped_weapon else 'None'}"
    dungeon_display = f"{Colors.BOLD}Dungeon:{Colors.RESET} {Colors.BRIGHT_MAGENTA}{dungeon_level}{Colors.RESET}"
    
    print(f"{Colors.BOLD}Class:{Colors.RESET} {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET} | {hp_display} | {attack_display}")
    print(f"{level_display} | {dungeon_display} | {weapon_display}")
    
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}")
    for msg in game_message: print(msg)
    print(f"{Colors.BOLD}Move:{Colors.YELLOW}W,A,S,D{Colors.RESET} | {Colors.BOLD}Quit:{Colors.RED}Q{Colors.RESET}")

# --- Main Game Logic ---
def open_chest(chest_pos):
    global chests, equipped_weapon, inventory
    loot = random.choice(CHEST_LOOT_TABLE)
    add_message(f"You open the chest and find a {loot.name}!")
    if isinstance(loot, Weapon):
        if not equipped_weapon or loot.damage_bonus > equipped_weapon.damage_bonus:
            add_message(f"You equip the {loot.name}.")
            equipped_weapon = loot
        else:
            add_message(f"You stash the {loot.name} in your pack.")
            inventory.append(loot)
    else:
        inventory.append(loot)
        add_message(f"You add the {loot.name} to your inventory.")
    chests.remove(chest_pos)

def handle_input():
    global player_x, player_y, turns, dungeon_level
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
        chest_pos = next((c for c in chests if c[0] == target_x and c[1] == target_y), None)
        if chest_pos:
            open_chest(chest_pos)
        elif not is_blocked(target_x, target_y):
            player_x, player_y = target_x, target_y
            update_fov()
        else:
            bumped_enemy = next((e for e in enemies if e['x'] == target_x and e['y'] == target_y), None)
            if bumped_enemy:
                game_state = player_attack_enemy(bumped_enemy)
                if game_state == "won": return "won"
            else: add_message(f"{Colors.BRIGHT_RED}Ouch! A wall.{Colors.RESET}")
    
    if game_map[player_y][player_x] == STAIRS_DOWN_CHAR:
        dungeon_level += 1
        add_message(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}You descend to dungeon level {dungeon_level}...{Colors.RESET}")
        generate_map()
        return "playing"

    enemy_turn()

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
    if game_state == "won": final_message = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 VICTORY! The Balrog is defeated! You have conquered the dungeon! 🎉{Colors.RESET}"
    elif game_state == "lost": final_message = f"{Colors.BOLD}{Colors.BRIGHT_RED}💀 DEFEAT! Died on level {dungeon_level} after {turns} turns. 💀{Colors.RESET}"
    elif game_state == "quit": final_message = f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}You quit on level {dungeon_level} after {turns} turns. Farewell!{Colors.RESET}"
    
    print(final_message)


if __name__ == "__main__":
    try: game_loop()
    except Exception as e:
        print(f"\n--- PYTHON ROGUE: UNEXPECTED ERROR ---"); print(f"Error: {e}"); import traceback; traceback.print_exc(); print(f"------------------------------------------\n")
    finally: print(Colors.RESET)
