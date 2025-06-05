import os
import random
import math

# --- Game Settings (mostly same) ---
MAP_WIDTH = 50
MAP_HEIGHT = 25
FLOOR_CHAR = "."
WALL_CHAR = "#"
GOAL_CHAR = "G"
DEAD_ENEMY_CHAR = "%"
UNSEEN_CHAR = ' '

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 20
MAX_ENEMIES_PER_ROOM = 2

BASE_FOV_RADIUS = 8 # Base FOV, can be modified by passives

# --- Player Class Definitions ---
PLAYER_CLASSES = [
    {"name": "Warrior", "char": "W", "hp": 30, "base_attack": 7, "color_code": "\033[94m",
     "passives": {"name": "Improved Fortitude", "desc": "Takes 1 less damage from melee attacks."}},
    {"name": "Rogue", "char": "R", "hp": 22, "base_attack": 5, "color_code": "\033[92m",
     "passives": {"name": "Evasion", "desc": "15% chance to dodge melee attacks."}},
    {"name": "Mage", "char": "M", "hp": 18, "base_attack": 4, "color_code": "\033[95m",
     "passives": {"name": "Arcane Potency", "desc": "Deals +2 bonus damage with attacks."}},
    {"name": "Cleric", "char": "C", "hp": 26, "base_attack": 5, "color_code": "\033[96m", # Cyan
     "passives": {"name": "Minor Regeneration", "desc": "Heals 1 HP every 20 turns."}},
    {"name": "Ranger", "char": "N", "hp": 24, "base_attack": 6, "color_code": "\033[32m", # Dark Green
     "passives": {"name": "Keen Eyes", "desc": "Increased Field of View (+2 radius)."}},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": "\033[91m",
     "passives": {"name": "Rage", "desc": "+3 Attack when below 30% HP."}},
    {"name": "Druid", "char": "D", "hp": 25, "base_attack": 5, "color_code": "\033[33m", # Orange/Yellow
     "passives": {"name": "Thorns Aura", "desc": "Enemies take 1 damage when they hit you in melee."}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": "\033[93m", # Light Yellow
     "passives": {"name": "Precise Strikes", "desc": "Attacks ignore 1 enemy defense."}}
]
ANSI_RESET = "\033[0m"

# --- Enemy Definitions (can be expanded) ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "color_code": "\033[31m"},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "color_code": "\033[33m"},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "color_code": "\033[97m"},
]

# --- Player Stats (Global) ---
player_x, player_y = 0, 0
player_class_info = {} # Will store the chosen class dict
player_char = "@"
player_max_hp, player_current_hp = 0, 0
# player_attack_power will be calculated dynamically
player_fov_radius = BASE_FOV_RADIUS
turns_since_regen = 0 # For Cleric

# --- Goal, Enemies, Game State, Maps (mostly same) ---
goal_x, goal_y = 0, 0
enemies = []
turns = 0
game_message = ["Welcome! Explore and survive."]
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

# --- Rect Class (same) ---
class Rect:
    def __init__(self, x, y, w, h): self.x1,self.y1,self.x2,self.y2 = x,y,x+w,y+h
    def center(self): return ((self.x1+self.x2)//2, (self.y1+self.y2)//2)
    def intersects(self, other): return (self.x1<=other.x2 and self.x2>=other.x1 and self.y1<=other.y2 and self.y2>=other.y1)

# --- Player Initialization ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius, turns_since_regen
    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]
    player_current_hp = player_max_hp
    player_char = player_class_info["char"]
    player_fov_radius = BASE_FOV_RADIUS # Reset before applying passive
    turns_since_regen = 0

    # Apply Ranger's "Keen Eyes" passive for FOV
    if player_class_info["passives"]["name"] == "Keen Eyes":
        player_fov_radius += 2
    
    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{ANSI_RESET}!")
    add_message(f"Passive: {player_class_info['passives']['name']} - {player_class_info['passives']['desc']}")


def get_player_attack_power():
    base_atk = player_class_info["base_attack"]
    # Mage: Arcane Potency
    if player_class_info["passives"]["name"] == "Arcane Potency":
        base_atk += 2
    # Barbarian: Rage
    if player_class_info["passives"]["name"] == "Rage":
        if player_current_hp <= math.floor(player_max_hp * 0.3):
            base_atk += 3
    return base_atk

# --- Map Generation & Enemy Spawning (mostly same, ensure player_x,y are set before spawn_enemies) ---
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

def is_blocked(x, y, check_player=True): # Added check_player flag
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT): return True # Out of bounds is blocked
    if game_map[y][x] == WALL_CHAR: return True
    if check_player and x == player_x and y == player_y: return True
    if x == goal_x and y == goal_y : return True
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: return True
    return False

def spawn_enemies(room):
    global enemies
    num_spawn = random.randint(0, MAX_ENEMIES_PER_ROOM)
    for _ in range(num_spawn):
        # Try a few times to find an empty spot in the room
        for _attempt in range(5): # Max 5 attempts to place an enemy in a room
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and \
               game_map[y][x] == FLOOR_CHAR and not is_blocked(x, y, check_player=False): # Don't check player during initial spawn
                enemy_type = random.choice(ENEMY_TYPES)
                new_enemy = enemy_type.copy()
                new_enemy['x'], new_enemy['y'] = x, y
                new_enemy['current_hp'] = enemy_type['hp']
                enemies.append(new_enemy)
                break # Placed enemy, move to next spawn

def generate_map():
    global game_map, player_x, player_y, goal_x, goal_y, fov_map, enemies
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    enemies = []
    rooms = []
    
    # Initial player placement to allow is_blocked to work before final placement
    player_x_init, player_y_init = -1,-1

    for r_idx in range(MAX_ROOMS):
        w,h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x,y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(other_room) for other_room in rooms): continue
        
        create_room(new_room)
        (new_cx, new_cy) = new_room.center()
        if not rooms: # First room
            player_x, player_y = new_cx, new_cy # Set actual player_x, player_y here
        else:
            (prev_cx, prev_cy) = rooms[-1].center()
            if random.randint(0,1) == 1:
                create_h_tunnel(prev_cx, new_cx, prev_cy); create_v_tunnel(prev_cy, new_cy, new_cx)
            else:
                create_v_tunnel(prev_cy, new_cy, prev_cx); create_h_tunnel(prev_cx, new_cx, new_cy)
            spawn_enemies(new_room) # Spawn in subsequent rooms
        rooms.append(new_room)

    if not rooms: # Fallback
        player_x, player_y = MAP_WIDTH//2, MAP_HEIGHT//2
        game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    
    if len(rooms) > 1:
        last_room = rooms[-1]
        for _ in range(10): # Try to place goal
            gx, gy = random.randint(last_room.x1 + 1, last_room.x2 - 1), random.randint(last_room.y1 + 1, last_room.y2 - 1)
            if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT and game_map[gy][gx] == FLOOR_CHAR and not (gx == player_x and gy == player_y) :
                goal_x, goal_y = gx,gy
                game_map[goal_y][goal_x] = GOAL_CHAR
                break
        else: # Fallback if can't place goal in last room
            if rooms[0].center() != (player_x,player_y):
                goal_x,goal_y = rooms[0].center()
                if game_map[goal_y][goal_x] == FLOOR_CHAR : game_map[goal_y][goal_x] = GOAL_CHAR
    elif rooms: # Only one room
        for _ in range(10):
            gx,gy = random.randint(rooms[0].x1+1, rooms[0].x2-1), random.randint(rooms[0].y1+1, rooms[0].y2-1)
            if game_map[gy][gx] == FLOOR_CHAR and not (gx == player_x and gy == player_y):
                goal_x, goal_y = gx, gy; game_map[goal_y][goal_x] = GOAL_CHAR; break

    update_fov()

# --- FOV Calculation (uses player_fov_radius) ---
def get_line(x1,y1,x2,y2): # (same)
    p,dx,dy,x,y,sx,sy = [],abs(x2-x1),abs(y2-y1),x1,y1,-1 if x1>x2 else 1,-1 if y1>y2 else 1
    if dx>dy: err=dx/2.0; شرط=lambda:x!=x2; op=lambda: (p.append((x,y)), setattr(locals(),'err',err-dy), (y:=y+sy, err:=err+dx) if err<0 else None, x:=x+sx)
    else: err=dy/2.0; شرط=lambda:y!=y2; op=lambda: (p.append((x,y)), setattr(locals(),'err',err-dx), (x:=x+sx, err:=err+dy) if err<0 else None, y:=y+sy)
    while شرط(): op()
    p.append((x,y)); return p

def update_fov(): # (same, but uses player_fov_radius)
    global fov_map
    for y_ in range(MAP_HEIGHT):
        for x_ in range(MAP_WIDTH):
            if fov_map[y_][x_] == 2: fov_map[y_][x_] = 1
    for x_offset in range(-player_fov_radius, player_fov_radius + 1):
        for y_offset in range(-player_fov_radius, player_fov_radius + 1):
            if x_offset*x_offset + y_offset*y_offset > player_fov_radius*player_fov_radius: continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                if not (0 <= lx < MAP_WIDTH and 0 <= ly < MAP_HEIGHT): break
                fov_map[ly][lx] = 2
                if game_map[ly][lx] == WALL_CHAR: break
                
# --- Messaging (same) ---
def add_message(msg):
    global game_message
    game_message.append(msg)
    if len(game_message) > 5: game_message = game_message[-5:]

# --- Combat & Player Taking Damage ---
def player_attack_enemy(enemy_obj):
    global enemies
    current_player_atk = get_player_attack_power()
    enemy_def = enemy_obj.get('defense', 0)

    # Monk: Precise Strikes
    if player_class_info["passives"]["name"] == "Precise Strikes":
        enemy_def = max(0, enemy_def - 1)
        # add_message("Your precise strike bypasses some defense!") # Optional flavor

    damage = current_player_atk - enemy_def
    damage = max(0, damage) 
    
    enemy_obj['current_hp'] -= damage
    hit_msg = f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{ANSI_RESET} for {damage} damage."
    
    if enemy_obj['current_hp'] <= 0:
        add_message(f"{hit_msg} It collapses!")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        enemies.remove(enemy_obj)
    else:
        add_message(f"{hit_msg} ({enemy_obj['current_hp']}/{enemy_obj['hp']} HP)")

def player_take_damage(damage_amount, enemy_attacker=None): # enemy_attacker for Thorns
    global player_current_hp
    
    # Warrior: Improved Fortitude
    if player_class_info["passives"]["name"] == "Improved Fortitude":
        damage_amount = max(1, damage_amount - 1)
        # add_message("Your fortitude lessens the blow!") # Optional flavor

    # Rogue: Evasion
    if player_class_info["passives"]["name"] == "Evasion":
        if random.random() < 0.15: # 15% chance
            add_message(f"You deftly evade the attack from {enemy_attacker['name'] if enemy_attacker else 'an enemy'}!")
            return # No damage taken

    player_current_hp -= damage_amount
    add_message(f"You take {damage_amount} damage!")

    # Druid: Thorns Aura (if enemy attacker is provided)
    if player_class_info["passives"]["name"] == "Thorns Aura" and enemy_attacker:
        if enemy_attacker in enemies: # Check if enemy is still alive and in list
            enemy_attacker['current_hp'] -= 1
            thorns_msg = f"Your thorns prick the {enemy_attacker['color_code']}{enemy_attacker['name']}{ANSI_RESET} for 1 damage."
            if enemy_attacker['current_hp'] <= 0:
                add_message(f"{thorns_msg} It succumbs to the thorns!")
                game_map[enemy_attacker['y']][enemy_attacker['x']] = DEAD_ENEMY_CHAR
                enemies.remove(enemy_attacker)
            else:
                add_message(thorns_msg)

    if player_current_hp < 0: player_current_hp = 0


# --- Drawing (updated for passives in UI) ---
def clear_screen():
    if os.name == 'nt': _ = os.system('cls')
    else: _ = os.system('clear')

def get_char_at(x, y): # (same)
    if x == player_x and y == player_y: return f"{player_class_info['color_code']}{player_char}{ANSI_RESET}"
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: return f"{enemy['color_code']}{enemy['char']}{ANSI_RESET}"
    return game_map[y][x]

def draw_game(): # (Updated UI Panel)
    clear_screen()
    for y_disp in range(MAP_HEIGHT):
        row_str = "".join(
            get_char_at(x_disp, y_disp) if fov_map[y_disp][x_disp] == 2 else
            (game_map[y_disp][x_disp] if fov_map[y_disp][x_disp] == 1 and game_map[y_disp][x_disp] != WALL_CHAR else
             (WALL_CHAR if fov_map[y_disp][x_disp] == 1 and game_map[y_disp][x_disp] == WALL_CHAR else UNSEEN_CHAR))
            for x_disp in range(MAP_WIDTH)
        )
        print(row_str)
    
    print("-" * MAP_WIDTH)
    class_display = f"Class: {player_class_info['color_code']}{player_class_info['name']}{ANSI_RESET}"
    hp_display = f"HP: {player_class_info['color_code']}{player_current_hp}/{player_max_hp}{ANSI_RESET}"
    
    current_attack = get_player_attack_power()
    attack_display = f"Atk: {current_attack}"
    if player_class_info["passives"]["name"] == "Rage" and player_current_hp <= math.floor(player_max_hp * 0.3):
        attack_display += " (Raging!)"

    turns_display = f"Turns: {turns}"
    print(f"{class_display:<25} {hp_display:<20} {attack_display:<20} {turns_display:<10}")
    passive_display = f"Passive: {player_class_info['passives']['name']}"
    print(f"{passive_display:<50} FOV: {player_fov_radius}")
    print("-" * MAP_WIDTH)
    for msg in game_message: print(msg)
    print("Move:W,A,S,D | Q:Quit")


# --- Game Logic (Handle Cleric Regen, Barbarian Rage message) ---
def handle_input():
    global player_x, player_y, turns, game_message, player_current_hp, turns_since_regen
    
    action = input("> ").lower()
    old_px, old_py = player_x, player_y
    moved = False

    if len(game_message) > 0 and not any(kw in game_message[-1] for kw in ["Ouch!", "Invalid", "You are", "Passive:"]):
         game_message = [] # Clear general action messages, keep initial/important ones

    if action == 'w': player_y -= 1; moved = True
    elif action == 's': player_y += 1; moved = True
    elif action == 'a': player_x -= 1; moved = True
    elif action == 'd': player_x += 1; moved = True
    elif action == 'q': return "quit"
    else: add_message("Invalid command."); return "playing"

    turns += 1
    turns_since_regen += 1

    # Cleric: Minor Regeneration
    if player_class_info["passives"]["name"] == "Minor Regeneration":
        if turns_since_regen >= 20:
            if player_current_hp < player_max_hp:
                player_current_hp += 1
                add_message("You feel a divine warmth, regenerating 1 HP.")
            turns_since_regen = 0
            
    # Collision & Movement
    if not (0 <= player_x < MAP_WIDTH and 0 <= player_y < MAP_HEIGHT) or \
       game_map[player_y][player_x] == WALL_CHAR:
        add_message("Ouch! A wall.")
        player_x, player_y = old_px, old_py
        moved = False
    
    if moved:
        update_fov()
        if player_x == goal_x and player_y == goal_y: return "won"

        # Barbarian Rage Message (if activated by moving and taking damage, or just state change)
        # This is more of a status effect display rather than turn-based trigger
        if player_class_info["passives"]["name"] == "Rage":
            is_raging = player_current_hp <= math.floor(player_max_hp * 0.3)
            # Check if rage state *just changed* to message it, or rely on Atk display
            # For now, the attack display handles "Raging!" status

        # Auto-attack (same logic as before, but uses get_player_attack_power())
        attacked_this_turn = False
        for dx_check in range(-1, 2):
            for dy_check in range(-1, 2):
                if dx_check == 0 and dy_check == 0: continue
                target_x, target_y = player_x + dx_check, player_y + dy_check
                if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
                if fov_map[target_y][target_x] == 2:
                    for enemy in list(enemies):
                        if enemy['x'] == target_x and enemy['y'] == target_y:
                            player_attack_enemy(enemy)
                            attacked_this_turn = True; break
            if attacked_this_turn: break
            
    # Placeholder for enemy turn / attacks (where player_take_damage would be called by enemies)
    # for enemy in list(enemies):
    #     if enemy_can_attack_player(enemy): # hypothetical function
    #         damage = enemy['attack']
    #         player_take_damage(damage, enemy_attacker=enemy) 
    #         if player_current_hp <= 0: break


    if player_current_hp <= 0: return "lost"
    return "playing"

# --- Main Game Loop (same) ---
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
    if game_state == "won": add_message(f"VICTORY! Goal reached in {turns} turns as a {end_color}{end_name}{ANSI_RESET}!")
    elif game_state == "lost": add_message(f"DEFEAT! Died after {turns} turns as a {end_color}{end_name}{ANSI_RESET}. Game Over.")
    elif game_state == "quit": add_message(f"You quit after {turns} turns. Farewell, {end_color}{end_name}{ANSI_RESET}!")
    print("-" * MAP_WIDTH); [print(msg) for msg in game_message]; print(ANSI_RESET)

if __name__ == "__main__":
    try: game_loop()
    finally: print(ANSI_RESET) # Ensure color reset
