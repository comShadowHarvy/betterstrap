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

# --- Pet System ---
class Pet:
    def __init__(self, name, char, hp, attack, color_code, abilities=None):
        self.name = name
        self.char = char
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.color_code = color_code
        self.abilities = abilities or []
        self.x = 0
        self.y = 0
        self.id = -1 # Unique pet id if needed later

# --- Pet Definitions ---
PET_TYPES = {
    "wolf": Pet("Wolf", "w", 12, 4, Colors.BOLD + Colors.BRIGHT_BLACK, ["Pack Hunter"]),
    "hawk": Pet("Hawk", "h", 8, 3, Colors.BOLD + Colors.YELLOW, ["Keen Sight", "Aerial Strike"]),
    "bear": Pet("Bear", "b", 20, 5, Colors.BOLD + Colors.RED, ["Thick Hide", "Maul"]),
    "snake": Pet("Snake", "~", 6, 2, Colors.BOLD + Colors.GREEN, ["Poison Bite", "Stealth"]),
    "eidolon": Pet("Eidolon", "E", 15, 6, Colors.BOLD + Colors.BRIGHT_MAGENTA, ["Spectral", "Bond"]),
    "horse": Pet("Warhorse", "H", 18, 4, Colors.BOLD + Colors.YELLOW, ["Charge", "Trample"])
}

# --- Expanded Player Class Definitions ---
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
     "passives": {"name": "Animal Companion", "desc": "Has a loyal pet companion that fights alongside you"}, "range": 5, "pet": "wolf"},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_RED,
     "passives": {"name": "Berserker", "desc": "+3 Attack when below 30% HP and 10% lifesteal on hits"}},
    {"name": "Druid", "char": "D", "hp": 25, "base_attack": 5, "color_code": Colors.BOLD + Colors.YELLOW,
     "passives": {"name": "Nature's Wrath", "desc": "Enemies take 1-2 damage on hit and heal 1 HP every 40 turns"}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW,
     "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has 15% chance to strike twice"}},
    {"name": "Archer", "char": "A", "hp": 20, "base_attack": 5, "color_code": Colors.BOLD + Colors.CYAN,
     "passives": {"name": "Deadly Aim", "desc": "Can attack at range 5 and deals +2 damage to unaware enemies"}, "range": 5},
    {"name": "Sorcerer", "char": "S", "hp": 16, "base_attack": 6, "color_code": Colors.BOLD + Colors.MAGENTA,
     "passives": {"name": "Spell Mastery", "desc": "Range 6 attacks and 25% chance to hit all adjacent enemies"}, "range": 6},
    {"name": "Paladin", "char": "P", "hp": 32, "base_attack": 6, "color_code": Colors.BOLD + Colors.WHITE,
     "passives": {"name": "Divine Grace", "desc": "Immune to poison, +2 damage vs undead, heals 1 HP when killing undead"}},
    {"name": "Witch", "char": "X", "hp": 19, "base_attack": 4, "color_code": Colors.BOLD + Colors.MAGENTA + Colors.DIM,
     "passives": {"name": "Hex Master", "desc": "Enemies take -1 attack penalty when adjacent, 20% chance to curse on hit"}, "range": 3},
    {"name": "Alchemist", "char": "L", "hp": 21, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW,
     "passives": {"name": "Mutagen", "desc": "Gains +2 attack but takes +1 damage for 10 turns after first combat"}, "range": 4},
    {"name": "Inquisitor", "char": "I", "hp": 27, "base_attack": 6, "color_code": Colors.BOLD + Colors.RED,
     "passives": {"name": "Divine Judgment", "desc": "+3 damage vs enemies below 25% HP, immune to fear effects"}},
    {"name": "Oracle", "char": "Q", "hp": 23, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_CYAN,
     "passives": {"name": "Foresight", "desc": "20% chance to dodge any attack, can see enemies through walls"}, "range": 5},
    {"name": "Summoner", "char": "U", "hp": 17, "base_attack": 3, "color_code": Colors.BOLD + Colors.BRIGHT_MAGENTA,
     "passives": {"name": "Eidolon Bond", "desc": "Summons a spectral ally that appears near enemies"}, "range": 4, "pet": "eidolon"},
    {"name": "Gunslinger", "char": "G", "hp": 24, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_BLACK,
     "passives": {"name": "Deadeye", "desc": "Critical hits deal double damage, +1 range per kill (max +3)"}, "range": 6},
    {"name": "Ninja", "char": "J", "hp": 20, "base_attack": 5, "color_code": Colors.DIM + Colors.BRIGHT_BLACK,
     "passives": {"name": "Shadow Step", "desc": "30% chance to teleport behind enemies when attacking"}},
    {"name": "Cavalier", "char": "K", "hp": 29, "base_attack": 6, "color_code": Colors.BOLD + Colors.BLUE,
     "passives": {"name": "Mounted Combat", "desc": "Charges deal +3 damage, +1 defense when not moving"}, "pet": "horse"},
    {"name": "Magus", "char": "V", "hp": 24, "base_attack": 6, "color_code": Colors.BOLD + Colors.CYAN,
     "passives": {"name": "Spell Combat", "desc": "Melee attacks have 25% chance to trigger magic missile"}, "range": 3},
    {"name": "Antipaladin", "char": "Z", "hp": 30, "base_attack": 7, "color_code": Colors.BOLD + Colors.RED + Colors.DIM,
     "passives": {"name": "Unholy Might", "desc": "Heals 2 HP when killing living enemies, +2 damage vs good aligned"}},
    {"name": "Bard", "char": "Y", "hp": 22, "base_attack": 4, "color_code": Colors.BOLD + Colors.YELLOW,
     "passives": {"name": "Inspire Courage", "desc": "All attacks have +1 damage, enemies have -1 attack when adjacent"}},
    {"name": "Investigator", "char": "T", "hp": 25, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_WHITE,
     "passives": {"name": "Studied Combat", "desc": "First attack on each enemy deals +3 damage, sees enemy HP"}},
    {"name": "Shaman", "char": "F", "hp": 23, "base_attack": 4, "color_code": Colors.BOLD + Colors.GREEN,
     "passives": {"name": "Spirit Guide", "desc": "20% chance for spirits to heal 1 HP or deal 1 damage to nearby enemies"}, "range": 4},
    {"name": "Warpriest", "char": "E", "hp": 28, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW,
     "passives": {"name": "Divine Weapon", "desc": "Weapon glows, providing light +1 FOV, +1 damage vs undead"}},
    {"name": "Bloodrager", "char": "H", "hp": 33, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_RED,
     "passives": {"name": "Bloodline Power", "desc": "Rage grants +4 attack but -1 defense, magical resistance"}},
    {"name": "Hunter", "char": "9", "hp": 26, "base_attack": 6, "color_code": Colors.BOLD + Colors.GREEN,
     "passives": {"name": "Pack Leader", "desc": "Animal companion shares combat bonuses"}, "range": 5, "pet": "hawk"},
    {"name": "Skald", "char": "8", "hp": 27, "base_attack": 6, "color_code": Colors.BOLD + Colors.BLUE,
     "passives": {"name": "Raging Song", "desc": "Combat triggers battle fury: +2 attack, regenerate 1 HP per kill"}},
    {"name": "Arcanist", "char": "7", "hp": 19, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_BLUE,
     "passives": {"name": "Arcane Reservoir", "desc": "Stores spell energy: +1 damage per spell cast (max +5)"}, "range": 5},
    {"name": "Swashbuckler", "char": "6", "hp": 26, "base_attack": 6, "color_code": Colors.BOLD + Colors.CYAN,
     "passives": {"name": "Panache", "desc": "Critical hits restore 1 HP and grant +1 attack until end of combat"}},
]

# --- Enemy Definitions ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "color_code": Colors.BOLD + Colors.RED, "ai": "melee", "type": "living"},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "color_code": Colors.BOLD + Colors.YELLOW, "ai": "melee", "type": "living"},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "color_code": Colors.BOLD + Colors.WHITE, "ai": "melee", "type": "undead"},
    {"name": "Archer", "char": "a", "hp": 8, "attack": 3, "defense": 0, "color_code": Colors.BOLD + Colors.GREEN, "ai": "ranged", "range": 5, "type": "living"},
    {"name": "Mage", "char": "m", "hp": 12, "attack": 6, "defense": 0, "color_code": Colors.BOLD + Colors.MAGENTA, "ai": "ranged", "range": 6, "type": "living"},
    {"name": "Zombie", "char": "z", "hp": 12, "attack": 4, "defense": 2, "color_code": Colors.BOLD + Colors.BRIGHT_BLACK, "ai": "melee", "type": "undead"}
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
seen_enemy_ids = set()
enemy_id_counter = 0
player_pet = None
gunslinger_range_bonus = 0
alchemist_mutagen_timer = 0
arcanist_reservoir = 0
swashbuckler_panache = False
goal_x, goal_y = 0, 0
enemies = []
turns = 0
game_message = ["Welcome! Explore and survive."]
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

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

# --- Title Screen ---
def show_title_screen():
    clear_screen()
    # Corrected alignment for title art
    title_art = f"""
{Colors.BOLD}{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      {Colors.BRIGHT_RED}███████{Colors.BRIGHT_YELLOW}╗ {Colors.BRIGHT_GREEN}██████{Colors.BRIGHT_BLUE}╗ {Colors.BRIGHT_MAGENTA}██{Colors.BRIGHT_CYAN}╗  {Colors.BRIGHT_RED}██{Colors.BRIGHT_YELLOW}╗ {Colors.BRIGHT_GREEN}███████{Colors.BRIGHT_BLUE}╗{Colors.BRIGHT_MAGENTA}███████{Colors.BRIGHT_CYAN}╗      ║
║      {Colors.BRIGHT_RED}██{Colors.BRIGHT_YELLOW}╔════╝{Colors.BRIGHT_GREEN}██{Colors.BRIGHT_BLUE}╔══{Colors.BRIGHT_MAGENTA}██{Colors.BRIGHT_CYAN}╗{Colors.BRIGHT_RED}██{Colors.BRIGHT_YELLOW}║  {Colors.BRIGHT_GREEN}██{Colors.BRIGHT_BLUE}║ {Colors.BRIGHT_MAGENTA}██{Colors.BRIGHT_CYAN}╔════╝{Colors.BRIGHT_RED}██{Colors.BRIGHT_YELLOW}╔════╝      ║
║      {Colors.BRIGHT_YELLOW}███████{Colors.BRIGHT_GREEN}╗{Colors.BRIGHT_BLUE}██{Colors.BRIGHT_MAGENTA}║  {Colors.BRIGHT_CYAN}██{Colors.BRIGHT_RED}║{Colors.BRIGHT_YELLOW}╚█████{Colors.BRIGHT_GREEN}╔╝ {Colors.BRIGHT_BLUE}███████{Colors.BRIGHT_MAGENTA}╗{Colors.BRIGHT_CYAN}█████{Colors.BRIGHT_RED}╗        ║
║      {Colors.BRIGHT_GREEN}╚════{Colors.BRIGHT_BLUE}██{Colors.BRIGHT_MAGENTA}║{Colors.BRIGHT_CYAN}██{Colors.BRIGHT_RED}║  {Colors.BRIGHT_YELLOW}██{Colors.BRIGHT_GREEN}║ {Colors.BRIGHT_BLUE}██{Colors.BRIGHT_MAGENTA}╔══██{Colors.BRIGHT_CYAN}╗ {Colors.BRIGHT_RED}██{Colors.BRIGHT_YELLOW}╔══╝ {Colors.BRIGHT_GREEN}██{Colors.BRIGHT_BLUE}╔══╝        ║
║      {Colors.BRIGHT_BLUE}███████{Colors.BRIGHT_MAGENTA}╔╝{Colors.BRIGHT_CYAN}╚██████{Colors.BRIGHT_RED}╔╝ {Colors.BRIGHT_YELLOW}██{Colors.BRIGHT_GREEN}║  {Colors.BRIGHT_BLUE}██{Colors.BRIGHT_MAGENTA}║ {Colors.BRIGHT_CYAN}███████{Colors.BRIGHT_RED}╗{Colors.BRIGHT_YELLOW}███████{Colors.BRIGHT_GREEN}╗      ║
║      {Colors.BRIGHT_MAGENTA}╚══════╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝╚══════╝      ║
║                                                                              ║
║           {Colors.BOLD}{Colors.BRIGHT_YELLOW}🎲 A Pathfinder-Inspired Terminal Adventure 🎲{Colors.BRIGHT_CYAN}           ║
║                                                                              ║
║      {Colors.BRIGHT_WHITE}🏹 30 Unique Character Classes  {Colors.BRIGHT_GREEN}🐺 Loyal Pet Companions{Colors.BRIGHT_CYAN}      ║
║      {Colors.BRIGHT_RED}⚔️  Advanced Combat System      {Colors.BRIGHT_BLUE}🎨 Colorful Interface{Colors.BRIGHT_CYAN}          ║
║      {Colors.BRIGHT_MAGENTA}🗺️  Procedural Dungeons         {Colors.BRIGHT_YELLOW}✨ Epic Adventures{Colors.BRIGHT_CYAN}            ║
║                                                                              ║
║                     {Colors.BRIGHT_GREEN}Created by: {Colors.BOLD}{Colors.BRIGHT_YELLOW}ShadowHarvy{Colors.BRIGHT_CYAN}                     ║
║                                                                              ║
║   {Colors.BRIGHT_WHITE}Controls:{Colors.BRIGHT_CYAN}                                                                   ║
║   {Colors.BRIGHT_YELLOW}W,A,S,D{Colors.BRIGHT_WHITE} - Move your character through the dungeon{Colors.BRIGHT_CYAN}                          ║
║   {Colors.BRIGHT_MAGENTA}F{Colors.BRIGHT_WHITE} - Use ranged attacks (if your class can){Colors.BRIGHT_CYAN}                               ║
║   {Colors.BRIGHT_RED}Q{Colors.BRIGHT_WHITE} - Quit the game{Colors.BRIGHT_CYAN}                                                       ║
║                                                                              ║
║            {Colors.BLINK}{Colors.BRIGHT_GREEN}Press ENTER to begin your adventure!{Colors.RESET}{Colors.BRIGHT_CYAN}             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}"""
    print(title_art)
    input(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}>> {Colors.RESET}")

# --- Initialization ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius
    global turns_since_regen, warrior_regen_timer, druid_regen_timer, player_pet
    global gunslinger_range_bonus, alchemist_mutagen_timer, arcanist_reservoir, swashbuckler_panache

    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]
    player_current_hp = player_max_hp
    player_char = player_class_info["char"]
    player_fov_radius = BASE_FOV_RADIUS
    turns_since_regen, warrior_regen_timer, druid_regen_timer = 0, 0, 0
    gunslinger_range_bonus, alchemist_mutagen_timer, arcanist_reservoir = 0, 0, 0
    swashbuckler_panache = False
    player_pet = None

    if player_class_info["passives"]["name"] in ["Hunter's Precision", "Divine Weapon", "Keen Eyes"]:
        if player_class_info["passives"]["name"] == "Keen Eyes": player_fov_radius += 2
        else: player_fov_radius += 1

    if "pet" in player_class_info and player_class_info["pet"] in PET_TYPES:
        pet_type = player_class_info["pet"]
        player_pet = Pet(PET_TYPES[pet_type].name, PET_TYPES[pet_type].char, PET_TYPES[pet_type].max_hp, PET_TYPES[pet_type].attack, PET_TYPES[pet_type].color_code, PET_TYPES[pet_type].abilities)
        # Place pet nearby, finding an open spot
        for dx, dy in [(0,-1), (-1,0), (0,1), (1,0)]:
            pet_x, pet_y = player_x + dx, player_y + dy
            if not is_blocked(pet_x, pet_y, check_pet=False):
                player_pet.x, player_pet.y = pet_x, pet_y
                break
        else: # Default if no spot found
            player_pet.x, player_pet.y = player_x, player_y


    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET}!")
    add_message(f"{Colors.BRIGHT_CYAN}Passive:{Colors.RESET} {Colors.BRIGHT_YELLOW}{player_class_info['passives']['name']}{Colors.RESET} - {player_class_info['passives']['desc']}")
    if player_pet:
        add_message(f"{Colors.BRIGHT_GREEN}Your {player_pet.name} companion joins you!{Colors.RESET}")

def get_player_attack_power():
    base_atk = player_class_info["base_attack"]
    passive = player_class_info["passives"]["name"]

    if passive == "Arcane Mastery": base_atk += 2
    elif passive == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3): base_atk += 3
    elif passive == "Mutagen" and alchemist_mutagen_timer > 0: base_atk += 2
    elif passive == "Inspire Courage": base_atk += 1
    elif passive == "Arcane Reservoir": base_atk += arcanist_reservoir
    elif passive == "Panache" and swashbuckler_panache: base_atk += 1
    elif passive == "Bloodline Power" and player_current_hp <= math.floor(player_max_hp * 0.5): base_atk += 4
    elif passive == "Raging Song": base_atk += 2

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

def is_blocked(x, y, check_player=True, check_pet=True):
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT) or game_map[y][x] == WALL_CHAR: return True
    if check_player and x == player_x and y == player_y: return True
    if check_pet and player_pet and x == player_pet.x and y == player_pet.y: return True
    # The goal should NOT block movement. The win condition is checked after a move.
    # if x == goal_x and y == goal_y: return True # <-- THIS WAS THE BUG
    return any(enemy['x'] == x and enemy['y'] == y for enemy in enemies)

def spawn_enemies(room):
    global enemies, enemy_id_counter
    num_spawn = random.randint(0, MAX_ENEMIES_PER_ROOM)
    for _ in range(num_spawn):
        for _attempt in range(10):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT and game_map[y][x] == FLOOR_CHAR and not is_blocked(x, y):
                enemy_type = random.choice(ENEMY_TYPES)
                new_enemy = enemy_type.copy()
                new_enemy.update({'x': x, 'y': y, 'current_hp': enemy_type['hp'], 'id': enemy_id_counter})
                enemy_id_counter += 1
                enemies.append(new_enemy)
                break

def generate_map():
    global game_map, player_x, player_y, goal_x, goal_y, fov_map, enemies, seen_enemy_ids, enemy_id_counter
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    enemies, rooms, seen_enemy_ids = [], [], set()
    enemy_id_counter = 0

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

    placed_goal = False
    if rooms:
        target_room = rooms[-1]
        for _ in range(50):
            gx, gy = random.randint(target_room.x1 + 1, target_room.x2 - 1), random.randint(target_room.y1 + 1, target_room.y2 - 1)
            if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT and game_map[gy][gx] == FLOOR_CHAR and not (gx == player_x and gy == player_y):
                goal_x, goal_y = gx, gy; game_map[gy][gx] = GOAL_CHAR; placed_goal = True; break
    if not placed_goal:
        for _ in range(100):
            gx, gy = random.randint(1, MAP_WIDTH - 2), random.randint(1, MAP_HEIGHT - 2)
            if game_map[gy][gx] == FLOOR_CHAR and not (gx == player_x and gy == player_y):
                goal_x, goal_y = gx, gy; game_map[gy][gx] = GOAL_CHAR; break
    update_fov()

# --- FOV Calculation ---
def get_line(x1, y1, x2, y2):
    points, dx, dy = [], abs(x2 - x1), abs(y2 - y1)
    x, y, sx, sy = x1, y1, 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
    if dx > dy:
        err = dx / 2.0
        while True:
            points.append((x, y))
            if x == x2: break
            err -= dy
            if err < 0: y += sy; err += dx
            x += sx
    else:
        err = dy / 2.0
        while True:
            points.append((x, y))
            if y == y2: break
            err -= dx
            if err < 0: x += sx; err += dy
            y += sy
    return points

def update_fov():
    global fov_map, seen_enemy_ids
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if fov_map[y][x] == 2: fov_map[y][x] = 1

    if player_class_info["passives"]["name"] == "Foresight":
        for enemy in enemies: seen_enemy_ids.add(enemy['id'])

    for x_offset in range(-player_fov_radius, player_fov_radius + 1):
        for y_offset in range(-player_fov_radius, player_fov_radius + 1):
            if x_offset * x_offset + y_offset * y_offset > player_fov_radius ** 2: continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue

            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                fov_map[ly][lx] = 2
                for enemy in enemies:
                    if enemy['x'] == lx and enemy['y'] == ly: seen_enemy_ids.add(enemy['id'])
                if game_map[ly][lx] == WALL_CHAR: break

# --- Messaging & Combat Effects ---
def add_message(msg):
    global game_message
    game_message.append(msg)
    if len(game_message) > 5: game_message = game_message[-5:]

def add_combat_effect(x, y, effect_type, duration=2):
    combat_effects.append((x, y, effect_type, duration))

def update_combat_effects():
    global combat_effects
    combat_effects[:] = [(x, y, effect, dur - 1) for x, y, effect, dur in combat_effects if dur > 1]

# --- Drawing ---
def get_char_at(x, y):
    for effect_x, effect_y, effect_type, _ in combat_effects:
        if effect_x == x and effect_y == y and effect_type in EFFECT_CHARS:
            return EFFECT_CHARS[effect_type]

    if x == player_x and y == player_y:
        return f"{player_class_info.get('color_code', Colors.RESET)}{player_char}{Colors.RESET}"
    
    if player_pet and x == player_pet.x and y == player_pet.y:
        return f"{player_pet.color_code}{player_pet.char}{Colors.RESET}"

    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y:
            return f"{enemy['color_code']}{enemy['char']}{Colors.RESET}"

    char = game_map[y][x]
    if char == FLOOR_CHAR: return f"{FLOOR_COLOR}{FLOOR_CHAR}{Colors.RESET}"
    elif char == WALL_CHAR: return f"{WALL_COLOR}{WALL_CHAR}{Colors.RESET}"
    elif char == GOAL_CHAR: return f"{GOAL_COLOR}{GOAL_CHAR}{Colors.RESET}"
    elif char == DEAD_ENEMY_CHAR: return f"{DEAD_ENEMY_COLOR}{DEAD_ENEMY_CHAR}{Colors.RESET}"

    return char

# --- Combat System ---
def player_attack_enemy(enemy_obj):
    global enemies, player_current_hp, gunslinger_range_bonus, arcanist_reservoir, swashbuckler_panache
    current_player_atk = get_player_attack_power()
    enemy_def = enemy_obj.get('defense', 0)
    is_critical = False
    passive_name = player_class_info["passives"]["name"]

    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)
    dist = max(abs(enemy_obj['x'] - player_x), abs(enemy_obj['y'] - player_y))

    if passive_name == "Ki Master": enemy_def = max(0, enemy_def - 1)
    elif passive_name == "Deadly Aim" and enemy_obj['id'] not in seen_enemy_ids: current_player_atk += 2; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
    elif passive_name == "Evasion Master" and enemy_obj['current_hp'] < enemy_obj['hp'] / 2: current_player_atk += 2
    elif passive_name in ["Divine Blessing", "Divine Weapon"] and enemy_obj.get('type') == 'undead': current_player_atk += 1
    elif passive_name == "Divine Grace" and enemy_obj.get('type') == 'undead': current_player_atk += 2
    elif passive_name == "Divine Judgment" and enemy_obj['current_hp'] < enemy_obj['hp'] * 0.25: current_player_atk += 3; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
    elif passive_name == "Studied Combat" and enemy_obj['id'] not in seen_enemy_ids: current_player_atk += 3; add_message(f"{Colors.BRIGHT_CYAN}You study your target carefully!{Colors.RESET}")
    elif passive_name == "Deadeye" and random.random() < 0.25: is_critical = True; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
    elif passive_name == "Unholy Might" and enemy_obj.get('type') == 'living': current_player_atk += 2
    elif passive_name == "Hunter's Precision" and dist >= 3: current_player_atk += 1; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)

    damage = max(0, current_player_atk - enemy_def)
    if is_critical and passive_name == "Deadeye": damage *= 2; add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}CRITICAL SHOT!{Colors.RESET}")
    if not is_critical and random.random() < 0.1: is_critical = True; damage = int(damage * 1.5); add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT)
    if passive_name == "Arcane Mastery" and random.random() < 0.20: damage += 2; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT); add_message(f"{Colors.BRIGHT_GREEN}Your spell crackles with extra power!{Colors.RESET}")

    enemy_obj['current_hp'] -= damage
    
    if passive_name == "Berserker":
        heal = max(1, math.floor(damage * 0.1)); player_current_hp = min(player_max_hp, player_current_hp + heal); add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_MAGENTA}You drain {heal} life!{Colors.RESET}")
    elif passive_name == "Ki Master" and random.random() < 0.15: enemy_obj['current_hp'] -= damage; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT); add_message(f"{Colors.BRIGHT_YELLOW}Your ki flows into a second strike!{Colors.RESET}")
    elif passive_name == "Nature's Wrath": nature_damage = random.randint(1, 2); enemy_obj['current_hp'] -= nature_damage; add_message(f"{Colors.BRIGHT_GREEN}Nature strikes for {nature_damage} additional damage!{Colors.RESET}")
    elif passive_name == "Hex Master" and random.random() < 0.20: add_message(f"{Colors.BOLD}{Colors.MAGENTA}You curse the {enemy_obj['name']}!{Colors.RESET}"); enemy_obj['cursed'] = True
    elif passive_name == "Spell Combat" and random.random() < 0.25: magic_damage = random.randint(2, 4); enemy_obj['current_hp'] -= magic_damage; add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_CRIT); add_message(f"{Colors.BRIGHT_BLUE}Magic missile deals {magic_damage} bonus damage!{Colors.RESET}")
    elif passive_name == "Panache" and is_critical: swashbuckler_panache = True; player_current_hp = min(player_max_hp, player_current_hp + 1); add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_YELLOW}Your panache is restored!{Colors.RESET}")
    elif passive_name == "Spell Mastery" and random.random() < 0.25:
        add_message(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}Your spell erupts in a magical explosion!{Colors.RESET}")
        for other_enemy in [e for e in enemies if abs(e['x'] - enemy_obj['x']) <= 1 and abs(e['y'] - enemy_obj['y']) <= 1 and e['id'] != enemy_obj['id']]:
            splash_damage = damage // 2; other_enemy['current_hp'] -= splash_damage; add_combat_effect(other_enemy['x'], other_enemy['y'], EFFECT_ATTACK)
            if other_enemy['current_hp'] <= 0: add_message(f"{Colors.BRIGHT_GREEN}The explosion kills a {other_enemy['name']}!{Colors.RESET}")

    if enemy_obj['current_hp'] <= 0:
        add_message(f"{Colors.BRIGHT_GREEN}You defeated the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET}!{Colors.RESET}")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        
        if passive_name == "Deadeye" and gunslinger_range_bonus < 3: gunslinger_range_bonus += 1; add_message(f"{Colors.BRIGHT_YELLOW}Your aim improves! (+1 range){Colors.RESET}")
        elif passive_name == "Divine Grace" and enemy_obj.get('type') == 'undead': player_current_hp = min(player_max_hp, player_current_hp+1); add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_CYAN}Divine grace restores 1 HP!{Colors.RESET}")
        elif passive_name == "Unholy Might" and enemy_obj.get('type') == 'living': player_current_hp = min(player_max_hp, player_current_hp + 2); add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_RED}You feast on life force! (+2 HP){Colors.RESET}")
        elif passive_name == "Raging Song": player_current_hp = min(player_max_hp, player_current_hp+1); add_combat_effect(player_x, player_y, EFFECT_HEAL)
        
        enemies[:] = [e for e in enemies if e['id'] != enemy_obj['id']]
    else:
        add_message(f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET} for {Colors.BRIGHT_RED}{damage}{Colors.RESET} damage. ({Colors.BRIGHT_YELLOW}{enemy_obj['current_hp']}{Colors.RESET}/{Colors.BRIGHT_GREEN}{enemy_obj['hp']}{Colors.RESET} HP)")
        if passive_name == "Studied Combat": add_message(f"{Colors.DIM}[Analysis: HP: {enemy_obj['current_hp']}/{enemy_obj['hp']}, Atk: {enemy_obj['attack']}, Def: {enemy_obj['defense']}]{Colors.RESET}")

def player_take_damage(damage_amount, enemy_attacker=None):
    global player_current_hp
    add_combat_effect(player_x, player_y, EFFECT_ATTACK)
    passive = player_class_info["passives"]["name"]
    
    if passive == "Improved Fortitude": damage_amount = max(1, damage_amount - 1)
    elif passive == "Mutagen" and alchemist_mutagen_timer > 0: damage_amount += 1
    elif passive in ["Bloodline Power", "Mounted Combat"]: damage_amount = max(1, damage_amount - 1)
    
    dodge_chance = 0
    if passive == "Evasion Master": dodge_chance = 0.15
    elif passive == "Foresight": dodge_chance = 0.20
    elif passive == "Shadow Step": dodge_chance = 0.10
    
    if random.random() < dodge_chance: add_message(f"{Colors.BRIGHT_CYAN}You deftly evade the attack!{Colors.RESET}"); return
    
    if passive == "Shadow Step" and random.random() < 0.30:
        add_message(f"{Colors.DIM}You fade into shadows and reappear behind your foe!{Colors.RESET}")
        if enemy_attacker and enemy_attacker in enemies:
            counter_damage = player_class_info["base_attack"] // 2
            enemy_attacker['current_hp'] -= counter_damage
            add_message(f"{Colors.BRIGHT_RED}Sneak attack for {counter_damage} damage!{Colors.RESET}")
        return
    
    player_current_hp -= damage_amount
    add_message(f"{Colors.BRIGHT_RED}You take {damage_amount} damage!{Colors.RESET}")
    
    if passive == "Nature's Wrath" and enemy_attacker and enemy_attacker in enemies:
        thorns_damage = random.randint(1, 2)
        enemy_attacker['current_hp'] -= thorns_damage
        add_combat_effect(enemy_attacker['x'], enemy_attacker['y'], EFFECT_ATTACK)
        add_message(f"{Colors.BRIGHT_GREEN}Nature's thorns deal {thorns_damage} damage to the {enemy_attacker['name']}!{Colors.RESET}")
        if enemy_attacker['current_hp'] <= 0:
            add_message(f"{Colors.BRIGHT_GREEN}The {enemy_attacker['name']} succumbs to the thorns!{Colors.RESET}")
            game_map[enemy_attacker['y']][enemy_attacker['x']] = DEAD_ENEMY_CHAR
            enemies[:] = [e for e in enemies if e['id'] != enemy_attacker['id']]

    if player_current_hp < 0: player_current_hp = 0

# --- Pet & Enemy AI ---
def pet_turn():
    if not player_pet or player_pet.current_hp <= 0: return

    closest_enemy, closest_dist = None, float('inf')
    for enemy in enemies:
        if fov_map[enemy['y']][enemy['x']] == 2:
            dist = max(abs(enemy['x'] - player_pet.x), abs(enemy['y'] - player_pet.y))
            if dist < closest_dist: closest_dist, closest_enemy = dist, enemy
    
    if closest_enemy:
        if closest_dist <= 1: pet_attack_enemy(closest_enemy)
        else:
            dx = 1 if closest_enemy['x'] > player_pet.x else -1 if closest_enemy['x'] < player_pet.x else 0
            dy = 1 if closest_enemy['y'] > player_pet.y else -1 if closest_enemy['y'] < player_pet.y else 0
            new_x, new_y = player_pet.x + dx, player_pet.y + dy
            if not is_blocked(new_x, new_y, check_pet=False): player_pet.x, player_pet.y = new_x, new_y
    elif max(abs(player_x - player_pet.x), abs(player_y - player_pet.y)) > 2:
        dx = 1 if player_x > player_pet.x else -1 if player_x < player_pet.x else 0
        dy = 1 if player_y > player_pet.y else -1 if player_y < player_pet.y else 0
        new_x, new_y = player_pet.x + dx, player_pet.y + dy
        if not is_blocked(new_x, new_y, check_pet=False): player_pet.x, player_pet.y = new_x, new_y

def pet_attack_enemy(enemy_obj):
    if not player_pet: return
    damage = player_pet.attack
    if "Pack Hunter" in player_pet.abilities and max(abs(enemy_obj['x'] - player_x), abs(enemy_obj['y'] - player_y)) <= 1:
        damage += 2; add_message(f"{Colors.BRIGHT_GREEN}Pack tactics! Your {player_pet.name} deals extra damage!{Colors.RESET}")
    
    enemy_obj['current_hp'] -= damage
    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)
    if enemy_obj['current_hp'] <= 0:
        add_message(f"{Colors.BRIGHT_GREEN}Your {player_pet.color_code}{player_pet.name}{Colors.RESET} defeats the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET}!{Colors.RESET}")
        game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        enemies[:] = [e for e in enemies if e['id'] != enemy_obj['id']]
    else: add_message(f"Your {player_pet.color_code}{player_pet.name}{Colors.RESET} attacks the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET} for {Colors.BRIGHT_RED}{damage}{Colors.RESET} damage.")

def enemy_turn():
    global player_current_hp
    for enemy in list(enemies):
        if enemy['current_hp'] <= 0: continue
        ex, ey = enemy['x'], enemy['y']

        if fov_map[ey][ex] != 2: continue

        player_dist = max(abs(ex - player_x), abs(ey - player_y))
        
        if player_dist <= 1:
            player_take_damage(enemy['attack'], enemy_attacker=enemy)
        else:
            dx = 1 if player_x > ex else -1 if player_x < ex else 0
            dy = 1 if player_y > ey else -1 if player_y < ey else 0
            nx, ny = ex + dx, ey + dy
            if not is_blocked(nx, ny): enemy['x'], enemy['y'] = nx, ny

# --- Drawing ---
def draw_game():
    clear_screen()
    update_combat_effects()
    
    border = "═" * (MAP_WIDTH + 2)
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    for y in range(MAP_HEIGHT):
        row_str = f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
        for x in range(MAP_WIDTH):
            # This logic determines what to show: visible, explored, or unseen
            if fov_map[y][x] == 2: # Currently visible: show exactly what's there.
                row_str += get_char_at(x,y)
            elif fov_map[y][x] == 1: # Explored: show the static map dimmed, but not live entities.
                char = game_map[y][x]
                if char == WALL_CHAR: row_str += f"{Colors.DIM}{WALL_COLOR}{char}{Colors.RESET}"
                else: row_str += f"{Colors.DIM}{FLOOR_COLOR}{char}{Colors.RESET}"
            else: # Unseen
                row_str += f"{UNSEEN_COLOR}{UNSEEN_CHAR}{Colors.RESET}"
        row_str += f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
        print(row_str)
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    
    # --- UI Panel ---
    hp_perc = player_current_hp / player_max_hp if player_max_hp > 0 else 0
    hp_color = Colors.BRIGHT_GREEN if hp_perc > 0.7 else Colors.BRIGHT_YELLOW if hp_perc > 0.3 else Colors.BRIGHT_RED
    hp_display = f"{Colors.BOLD}HP:{Colors.RESET} {hp_color}{player_current_hp}{Colors.RESET}/{Colors.BRIGHT_GREEN}{player_max_hp}{Colors.RESET}"
    attack_display = f"{Colors.BOLD}Atk:{Colors.RESET} {Colors.BRIGHT_RED}{get_player_attack_power()}{Colors.RESET}"
    
    print(f"{Colors.BOLD}Class:{Colors.RESET} {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET} | {hp_display} | {attack_display} | {Colors.BOLD}Turns:{Colors.RESET} {Colors.BRIGHT_CYAN}{turns}{Colors.RESET}")
    
    if player_pet and player_pet.current_hp > 0:
        pet_hp_perc = player_pet.current_hp / player_pet.max_hp if player_pet.max_hp > 0 else 0
        pet_hp_color = Colors.BRIGHT_GREEN if pet_hp_perc > 0.5 else Colors.BRIGHT_YELLOW if pet_hp_perc > 0.25 else Colors.BRIGHT_RED
        print(f"{Colors.BOLD}Pet:{Colors.RESET} {player_pet.color_code}{player_pet.name}{Colors.RESET} | {Colors.BOLD}HP:{Colors.RESET} {pet_hp_color}{player_pet.current_hp}{Colors.RESET}/{Colors.BRIGHT_GREEN}{player_pet.max_hp}{Colors.RESET}")

    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}")
    for msg in game_message: print(msg)
    print(f"{Colors.BOLD}Move:{Colors.BRIGHT_YELLOW}W,A,S,D{Colors.RESET} | {Colors.BOLD}F:{Colors.BRIGHT_MAGENTA}Ranged Attack{Colors.RESET} | {Colors.BOLD}Q:{Colors.BRIGHT_RED}Quit{Colors.RESET}")

# --- Main Game Logic ---
def player_can_ranged_attack():
    return "range" in player_class_info

def player_ranged_attack():
    if not player_can_ranged_attack():
        add_message(f"{Colors.BRIGHT_RED}Your class cannot perform ranged attacks.{Colors.RESET}"); return False
    
    target, min_dist = None, float('inf')
    for enemy in enemies:
        if fov_map[enemy['y']][enemy['x']] == 2:
            dist = max(abs(enemy['x'] - player_x), abs(enemy['y'] - player_y))
            if dist <= player_class_info['range'] and dist < min_dist:
                has_los = not any(game_map[ly][lx] == WALL_CHAR for lx,ly in get_line(player_x, player_y, enemy['x'], enemy['y'])[1:-1])
                if has_los: min_dist, target = dist, enemy
    
    if target: player_attack_enemy(target); return True
    else: add_message(f"{Colors.BRIGHT_YELLOW}No enemy in range/line of sight.{Colors.RESET}"); return False

def handle_regeneration():
    global player_current_hp, turns_since_regen, warrior_regen_timer, druid_regen_timer
    passive = player_class_info['passives']['name']
    turns_since_regen += 1
    
    if passive == "Divine Blessing" and turns_since_regen >= 20:
        if player_current_hp < player_max_hp: player_current_hp += 1; add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_CYAN}Divine blessing restores 1 HP.{Colors.RESET}")
        turns_since_regen = 0
    elif passive == "Improved Fortitude":
        warrior_regen_timer += 1
        if warrior_regen_timer >= 30:
            if player_current_hp < player_max_hp: player_current_hp += 1; add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_BLUE}Your fortitude restores 1 HP.{Colors.RESET}")
            warrior_regen_timer = 0
    elif passive == "Nature's Wrath":
        druid_regen_timer += 1
        if druid_regen_timer >= 40:
            if player_current_hp < player_max_hp: player_current_hp += 1; add_combat_effect(player_x, player_y, EFFECT_HEAL); add_message(f"{Colors.BRIGHT_GREEN}Nature's energy restores 1 HP.{Colors.RESET}")
            druid_regen_timer = 0

def auto_attack_adjacent():
    attacked = False
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0: continue
            check_x, check_y = player_x + dx, player_y + dy
            
            if not (0 <= check_x < MAP_WIDTH and 0 <= check_y < MAP_HEIGHT and fov_map[check_y][check_x] == 2):
                continue

            target_enemy = next((e for e in enemies if e['x'] == check_x and e['y'] == check_y), None)
            if target_enemy:
                add_message(f"{Colors.YELLOW}With swiftness, you strike an adjacent {target_enemy['name']}!{Colors.RESET}")
                player_attack_enemy(target_enemy)
                attacked = True
                break
        if attacked:
            break

def handle_input():
    global player_x, player_y, turns
    action = input("> ").lower()
    
    target_x, target_y = player_x, player_y
    is_move_action = False

    if action == 'w': target_y -= 1; is_move_action = True
    elif action == 's': target_y += 1; is_move_action = True
    elif action == 'a': target_x -= 1; is_move_action = True
    elif action == 'd': target_x += 1; is_move_action = True
    elif action == 'f':
        player_ranged_attack()
    elif action == 'q': return "quit"
    else:
        add_message(f"{Colors.BRIGHT_RED}Invalid command.{Colors.RESET}"); return "playing"

    turns += 1
    handle_regeneration()

    if is_move_action:
        # Check if destination is blocked
        if not is_blocked(target_x, target_y):
            # Move to empty tile
            player_x, player_y = target_x, target_y
            update_fov()
            auto_attack_adjacent()
        else:
            # Destination is blocked, check if it's an enemy for bump attack
            bumped_enemy = next((e for e in enemies if e['x'] == target_x and e['y'] == target_y), None)
            if bumped_enemy:
                player_attack_enemy(bumped_enemy)
            else: # It's a wall or other obstacle
                add_message(f"{Colors.BRIGHT_RED}Ouch! You bump into something.{Colors.RESET}")
    
    # After player action, other actors take their turn
    enemy_turn()
    pet_turn()

    if player_x == goal_x and player_y == goal_y: return "won"
    if player_current_hp <= 0: return "lost"
    return "playing"

# --- Main Game Loop ---
def game_loop():
    show_title_screen()
    initialize_player()
    generate_map()
    game_state = "playing"
    
    while game_state == "playing":
        draw_game()
        game_state = handle_input()

    draw_game()
    end_color = player_class_info.get('color_code', Colors.RESET)
    end_name = player_class_info.get('name', 'Adventurer')
    final_message = ""
    if game_state == "won": final_message = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 VICTORY! Goal reached in {turns} turns as a {end_color}{end_name}{Colors.RESET}!"
    elif game_state == "lost": final_message = f"{Colors.BOLD}{Colors.BRIGHT_RED}💀 DEFEAT! Died after {turns} turns as a {end_color}{end_name}{Colors.RESET}."
    elif game_state == "quit": final_message = f"{Colors.BRIGHT_YELLOW}You quit after {turns} turns. Farewell, {end_color}{end_name}{Colors.RESET}!"
    
    print(final_message)


if __name__ == "__main__":
    try: 
        game_loop()
    except Exception as e:
        print(f"\n--- PYTHON ROGUE: UNEXPECTED ERROR ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"------------------------------------------\n")
    finally: 
        print(Colors.RESET)
