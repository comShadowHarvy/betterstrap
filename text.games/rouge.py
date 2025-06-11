import os
import random
import math
from getch import getch # Import the getch library for instant key presses

# --- Game Settings ---
MAP_WIDTH = 60
MAP_HEIGHT = 28
FLOOR_CHAR = "."
WALL_CHAR = "#"
STAIRS_DOWN_CHAR = ">"
DEAD_ENEMY_CHAR = "%"
UNSEEN_CHAR = ' '
CHEST_CHAR = "C"
BOSS_FLOOR = 20
FOUNTAIN_CHAR = "F"
ALTAR_CHAR = "A"
TRAP_CHAR = "^"

# --- Color Definitions ---
class Colors:
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = (f"\033[3{i}m" for i in range(8))
    BRIGHT_BLACK, BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE, BRIGHT_MAGENTA, BRIGHT_CYAN, BRIGHT_WHITE = (f"\033[9{i}m" for i in range(8))
    BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
    BRIGHT_PURPLE = "\033[95m"
    FOUNTAIN_COLOR = BOLD + BRIGHT_BLUE
    ALTAR_COLOR = BOLD + BRIGHT_YELLOW
    TRAP_COLOR = RED

# --- Environment Color Settings ---
FLOOR_COLOR = Colors.BRIGHT_BLACK
WALL_COLOR = Colors.WHITE
STAIRS_COLOR = Colors.BOLD + Colors.BRIGHT_MAGENTA
DEAD_ENEMY_COLOR = Colors.DIM + Colors.RED
UNSEEN_COLOR = Colors.BLACK
CHEST_COLOR = Colors.BOLD + Colors.YELLOW

# --- Combat Effects ---
EFFECT_ATTACK = 1; EFFECT_CRIT = 2; EFFECT_HEAL = 3
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
    def __init__(self, name, char='!'):
        self.name, self.char = name, char

class Weapon(Item):
    def __init__(self, name, damage_bonus, weapon_type, char='/'):
        super().__init__(name, char)
        self.damage_bonus = damage_bonus
        self.weapon_type = weapon_type

class Potion(Item):
    def __init__(self, name, effect, value, char='!'):
        super().__init__(name, char)
        self.effect = effect
        self.value = value

class Scroll(Item):
     def __init__(self, name, effect, value=0, char='?'):
        super().__init__(name, char)
        self.effect = effect
        self.value = value

# --- Item/Weapon Definitions ---
POTION_TYPES = [ Potion("Healing Potion", 'heal', 15), Potion("Greater Healing Potion", 'heal', 30), Potion("Superior Healing Potion", 'heal', 50), Potion("Elixir of Health", 'full_heal', 999), Potion("Potion of Experience", 'xp_boost', 50) ]
SCROLL_TYPES = [ Scroll("Scroll of Teleportation", 'teleport', 0), Scroll("Scroll of Map Reveal", 'map_reveal', 0) ]
MELEE_WEAPON_TYPES = [ Weapon("Dagger", 2, 'melee'), Weapon("Serrated Dagger", 3, 'melee'), Weapon("Shortsword", 4, 'melee'), Weapon("Longsword", 6, 'melee'), Weapon("Battle Axe", 8, 'melee'), Weapon("Warhammer", 9, 'melee'), Weapon("Greatsword", 11, 'melee'), Weapon("Glimmering Blade", 13, 'melee') ]
RANGED_WEAPON_TYPES = [ Weapon("Sling", 2, 'ranged'), Weapon("Shortbow", 4, 'ranged'), Weapon("Elven Shortbow", 5, 'ranged'), Weapon("Longbow", 6, 'ranged'), Weapon("Composite Bow", 7, 'ranged'), Weapon("Heavy Crossbow", 9, 'ranged'), Weapon("Repeating Crossbow", 10, 'ranged') ]
CHEST_LOOT_TABLE = ( POTION_TYPES * 4 + SCROLL_TYPES * 3 + MELEE_WEAPON_TYPES * 2 + RANGED_WEAPON_TYPES * 2 )

# --- Player Class Definitions ---
PLAYER_CLASSES = [
    {"name": "Warrior", "char": "W", "hp": 30, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_BLUE, "passives": {"name": "Improved Fortitude", "desc": "Takes 1 less damage from melee attacks"}},
    {"name": "Rogue", "char": "R", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.GREEN, "passives": {"name": "Evasion Master", "desc": "15% dodge chance and deals +2 damage to enemies below 50% HP"}},
    {"name": "Mage", "char": "M", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_MAGENTA, "passives": {"name": "Arcane Mastery", "desc": "Deals +2 damage and has 20% chance to deal 2 bonus damage"}, "range": 5},
    {"name": "Cleric", "char": "C", "hp": 26, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_CYAN, "passives": {"name": "Divine Blessing", "desc": "Heals 1 HP every 20 turns and deals +1 damage to undead"}},
    {"name": "Ranger", "char": "N", "hp": 24, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_GREEN, "passives": {"name": "Keen Eyes", "desc": "Increased Field of View (+2 radius)"}, "range": 6},
    {"name": "Barbarian", "char": "B", "hp": 35, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "passives": {"name": "Berserker", "desc": "+3 Attack when below 30% HP and 10% lifesteal on hits"}},
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW, "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has 15% chance to strike twice"}},
    {"name": "Paladin", "char": "P", "hp": 28, "base_attack": 6, "color_code": Colors.BOLD + Colors.WHITE, "passives": {"name": "Smite Evil", "desc": "Deals +3 bonus damage to undead enemies"}},
    {"name": "Assassin", "char": "A", "hp": 20, "base_attack": 5, "color_code": Colors.DIM + Colors.WHITE, "passives": {"name": "Assassinate", "desc": "First attack on any enemy is a guaranteed critical hit"}},
    {"name": "Necromancer", "char": "Y", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.MAGENTA, "passives": {"name": "Raise Dead", "desc": "30% chance to raise a slain enemy as a loyal Zombie minion"}},
    {"name": "Lich", "char": "L", "hp": 40, "base_attack": 7, "color_code": Colors.BOLD + Colors.MAGENTA, "passives": {"name": "Phylactery", "desc": "On death, resurrect with 50% HP. Can only occur once per floor. All attacks drain 15% of damage dealt as life."}, "range": 7},
    {"name": "Golem", "char": "G", "hp": 60, "base_attack": 8, "color_code": Colors.DIM + Colors.WHITE, "passives": {"name": "Iron Form", "desc": "Immune to critical hits. Reduces all incoming damage by a flat 2 points."}},
    {"name": "Archangel", "char": "V", "hp": 45, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW, "passives": {"name": "Divine Judgement", "desc": "Attacks have a 20% chance to be 'divine', healing you for 10 HP and dealing double damage."}, "range": 6},
    {"name": "Dragoon", "char": "D", "hp": 32, "base_attack": 7, "color_code": Colors.BOLD + Colors.BLUE, "passives": {"name": "Dragon's Blood", "desc": "Regenerates 1 HP every 15 turns. Takes 1 less damage from enemies with more than 80% HP."}},
    {"name": "Gunslinger", "char": "S", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.YELLOW, "passives": {"name": "Fan the Hammer", "desc": "Ranged attacks have a 10% chance to strike an additional random enemy in view."}, "range": 8},
    {"name": "Elementalist", "char": "E", "hp": 20, "base_attack": 5, "color_code": Colors.BOLD + Colors.CYAN, "passives": {"name": "Elemental Surge", "desc": "Every attack has a 25% chance to surge with energy, dealing 4 bonus damage."}, "range": 6},
    {"name": "Vampire", "char": "v", "hp": 25, "base_attack": 6, "color_code": Colors.DIM + Colors.RED, "passives": {"name": "Lesser Thirst", "desc": "Heals for 1 HP for every 8 damage dealt. Deals +2 damage to living enemies."}},
    {"name": "Druid", "char": "U", "hp": 28, "base_attack": 5, "color_code": Colors.BOLD + Colors.GREEN, "passives": {"name": "Call of the Wild", "desc": "Has a 20% chance on entering a new room to summon a loyal wolf minion (10hp/4atk)."}},
    {"name": "Psion", "char": "I", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.BRIGHT_PURPLE, "passives": {"name": "Mind Blast", "desc": "Attacks have a 15% chance to bypass all enemy defense entirely."}, "range": 7},
    {"name": "Chronomancer", "char": "@", "hp": 20, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_CYAN, "passives": {"name": "Temporal Slip", "desc": "15% chance to act again immediately after your turn."}, "range": 5},
    {"name": "Death Knight", "char": "K", "hp": 30, "base_attack": 6, "color_code": Colors.DIM + Colors.BRIGHT_BLACK, "passives": {"name": "Necrotic Strike", "desc": "Melee attacks have a 20% chance to deal 5 bonus unholy damage."}},
    {"name": "Inquisitor", "char": "Q", "hp": 26, "base_attack": 6, "color_code": Colors.BOLD + Colors.WHITE, "passives": {"name": "Judge the Unworthy", "desc": "Deals +3 bonus damage to Undead and Demon type enemies."}},
    {"name": "Juggernaut", "char": "J", "hp": 40, "base_attack": 5, "color_code": Colors.BOLD + Colors.RED, "passives": {"name": "Retaliation", "desc": "When hit by a melee attack, has a 25% chance to strike back instantly."}},
    {"name": "Artificer", "char": "T", "hp": 24, "base_attack": 5, "color_code": Colors.BOLD + Colors.YELLOW, "passives": {"name": "Well Supplied", "desc": "Starts the game with 2 random potions and 1 random scroll."}},
    {"name": "Priest", "char": "H", "hp": 26, "base_attack": 4, "color_code": Colors.BRIGHT_WHITE, "passives": {"name": "Potent Healing", "desc": "All healing from potions is increased by 50%."}},
    {"name": "Shaman", "char": "h", "hp": 22, "base_attack": 5, "color_code": Colors.BRIGHT_BLUE, "passives": {"name": "Ancestral Favor", "desc": "Gains a random permanent bonus at the start of each floor (+5 max HP or +1 base attack)."}},
    {"name": "Spellblade", "char": "F", "hp": 28, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_PURPLE, "passives": {"name": "Spell-Charged Strike", "desc": "Every 4th melee attack deals +10 bonus magic damage."}},
    {"name": "Templar", "char": "t", "hp": 30, "base_attack": 6, "color_code": Colors.DIM + Colors.WHITE, "passives": {"name": "Divine Shield", "desc": "15% chance to completely block all damage from any single attack."}},
    {"name": "Warlock", "char": "w", "hp": 20, "base_attack": 5, "color_code": Colors.BOLD + Colors.MAGENTA, "passives": {"name": "Pact-Bound Imp", "desc": "Starts with a loyal Imp minion (8 HP, 5 ATK)."}, "range": 5},
    {"name": "Gladiator", "char": "g", "hp": 30, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "passives": {"name": "Victory Rush", "desc": "Heals 5 HP after killing an enemy."}},
    {"name": "Shadow", "char": "x", "hp": 22, "base_attack": 5, "color_code": Colors.DIM + Colors.BRIGHT_BLACK, "passives": {"name": "Shadow Dance", "desc": "If you don't attack for a turn, your next melee attack is a guaranteed critical hit."}},
    {"name": "Titan", "char": "Θ", "hp": 70, "base_attack": 10, "color_code": Colors.BOLD + Colors.BRIGHT_BLUE, "passives": {"name": "Colossal Cleave", "desc": "Melee attacks damage the target and all adjacent enemies."}},
    {"name": "Reality Bender", "char": "§", "hp": 30, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_PURPLE, "passives": {"name": "Causal Rejection", "desc": "The first time you would die each floor, your death is rejected and you are healed to full HP."}, "range": 6},
    {"name": "Void Terror", "char": "X", "hp": 40, "base_attack": 8, "color_code": Colors.DIM + Colors.BRIGHT_BLACK, "passives": {"name": "Erase", "desc": "Attacks have a 20% chance to instantly annihilate non-boss enemies below 30% HP."}},
    {"name": "Demigod", "char": "Δ", "hp": 50, "base_attack": 8, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW, "passives": {"name": "Divine Spark", "desc": "Starts with superior stats. Every 50 turns, gain a powerful divine blessing."}},
    {"name": "World Serpent", "char": "S", "hp": 60, "base_attack": 7, "color_code": Colors.BOLD + Colors.GREEN, "passives": {"name": "Corrosive Acid", "desc": "Attacks permanently reduce enemy defense by 1. Can shed skin once per floor to fully heal."}},
    {"name": "Phoenix", "char": "Φ", "hp": 35, "base_attack": 7, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "passives": {"name": "Rebirth in Flame", "desc": "Upon death, resurrect to full HP and deal 25 damage to all enemies in view."}, "range": 5},
    {"name": "Chaos Jester", "char": "J", "hp": 40, "base_attack": 6, "color_code": Colors.BOLD + Colors.BRIGHT_MAGENTA, "passives": {"name": "Pandora's Box", "desc": "Every action triggers a powerful, wildly random effect."}},
    {"name": "Hivemind", "char": "H", "hp": 25, "base_attack": 3, "color_code": Colors.BOLD + Colors.GREEN, "passives": {"name": "One from Many", "desc": "Starts with two loyal Drones. Gain +2 attack for each living Drone."}},
    {"name": "Singularity", "char": "o", "hp": 50, "base_attack": 0, "color_code": Colors.DIM + Colors.WHITE, "passives": {"name": "Event Horizon", "desc": "Does not attack. At the end of your turn, all adjacent enemies take 8 damage."}},
]


# --- Enemy Definitions with XP Value ---
ENEMY_TYPES = [
    {"name": "Goblin", "char": "g", "hp": 7, "attack": 3, "defense": 1, "xp_value": 10, "color_code": Colors.BOLD + Colors.RED, "spawn_level": 1, "type": "living"},
    {"name": "Orc", "char": "o", "hp": 15, "attack": 5, "defense": 2, "xp_value": 25, "color_code": Colors.BOLD + Colors.YELLOW, "spawn_level": 2, "type": "living"},
    {"name": "Skeleton", "char": "s", "hp": 10, "attack": 4, "defense": 1, "xp_value": 15, "color_code": Colors.BOLD + Colors.WHITE, "spawn_level": 1, "type": "undead"},
    {"name": "Troll", "char": "T", "hp": 30, "attack": 7, "defense": 3, "xp_value": 50, "color_code": Colors.BOLD + Colors.GREEN, "spawn_level": 5, "type": "living"},
    {"name": "Ogre", "char": "O", "hp": 40, "attack": 8, "defense": 4, "xp_value": 75, "color_code": Colors.BOLD + Colors.BLUE, "spawn_level": 10, "type": "living"},
    {"name": "The Balrog", "char": "B", "hp": 150, "attack": 12, "defense": 5, "xp_value": 500, "color_code": Colors.BOLD + Colors.BRIGHT_RED, "spawn_level": BOSS_FLOOR, "type": "demon"},
    {"name": "Goblin Shaman", "char": "g", "hp": 10, "attack": 2, "defense": 1, "xp_value": 20, "color_code": Colors.BOLD + Colors.GREEN, "spawn_level": 3, "type": "living", "behavior": "healer"},
    {"name": "Orc Berserker", "char": "o", "hp": 25, "attack": 4, "defense": 1, "xp_value": 40, "color_code": Colors.BOLD + Colors.RED, "spawn_level": 4, "type": "living", "behavior": "enrage"},
    {"name": "Slime", "char": "p", "hp": 12, "attack": 3, "defense": 3, "xp_value": 15, "color_code": Colors.GREEN, "spawn_level": 2, "type": "ooze", "behavior": "split"},
    {"name": "Small Slime", "char": "p", "hp": 6, "attack": 2, "defense": 1, "xp_value": 5, "color_code": Colors.DIM + Colors.GREEN, "spawn_level": 2, "type": "ooze"},
    {"name": "Skeleton Mage", "char": "s", "hp": 8, "attack": 0, "defense": 1, "xp_value": 25, "color_code": Colors.DIM + Colors.WHITE, "spawn_level": 5, "type": "undead", "behavior": "ranged_caster", "ranged_attack": 5},
]

# --- Global Player and Game State Variables ---
player_x, player_y = 0, 0
player_class_info = {}
player_char = "@"; player_max_hp, player_current_hp = 0, 0
player_fov_radius = BASE_FOV_RADIUS
turns = 0; dungeon_level = 1
enemies = []; chests = []; inventory = []; equipped_melee = None; equipped_ranged = None; minions = []
traps = []
game_message = ["Welcome! Explore and survive."];
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
player_level = 1; player_xp = 0; xp_to_next_level = 50
hit_enemy_ids = set()
lich_resurrected_this_floor = False
player_state = {}

# --- Rect Class for Map Generation ---
class Rect:
    def __init__(self, x, y, w, h): self.x1, self.y1, self.x2, self.y2 = x,y,x+w,y+h
    def center(self): return ((self.x1+self.x2)//2, (self.y1+self.y2)//2)
    def intersects(self, other): return (self.x1<=other.x2 and self.x2>=other.x1 and self.y1<=other.y2 and self.y2>=other.y1)

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')

# --- Helper Functions ---
def chaos_jester_effect():
    global player_current_hp, player_max_hp, enemies, game_map, chests
    effects = ["heal", "damage_self", "empower", "summon_monster", "confuse", "polymorph", "gold_fever", "fumble"]
    effect = random.choice(effects)
    if effect == "heal":
        add_message(f"{Colors.GREEN}A soothing melody heals you completely!{Colors.RESET}"); player_current_hp = player_max_hp
    elif effect == "damage_self":
        dmg = random.randint(5, 15); add_message(f"{Colors.RED}The joke's on you! You take {dmg} damage.{Colors.RESET}"); player_current_hp -= dmg
    elif effect == "empower":
        add_message(f"{Colors.YELLOW}A surge of cosmic laughter empowers you! Your next attack will be a critical hit.{Colors.RESET}"); player_state["shadow_critz"] = True
    elif effect == "summon_monster":
        add_message(f"{Colors.RED}A hostile Ogre materializes from a bad joke!{Colors.RESET}")
        ogre_type = next((e for e in ENEMY_TYPES if e['name'] == 'Ogre'), None)
        if ogre_type:
            for _ in range(10):
                nx, ny = player_x + random.randint(-2, 2), player_y + random.randint(-2, 2)
                if 0 < nx < MAP_WIDTH -1 and 0 < ny < MAP_HEIGHT-1 and game_map[ny][nx] == FLOOR_CHAR and not is_blocked(nx, ny):
                    new_enemy = ogre_type.copy(); new_enemy.update({'x': nx, 'y': ny, 'current_hp': ogre_type['hp'], 'id': len(enemies) + len(minions)}); enemies.append(new_enemy); break
    elif effect == "confuse":
        add_message(f"{Colors.MAGENTA}A confusing tune makes all enemies wander aimlessly for a moment.{Colors.RESET}")
        for enemy in enemies:
            nx, ny = enemy['x'] + random.randint(-1, 1), enemy['y'] + random.randint(-1, 1)
            if not is_blocked(nx, ny): enemy['x'], enemy['y'] = nx, ny
    elif effect == "polymorph":
        if enemies:
            target = random.choice(enemies)
            add_message(f"{Colors.CYAN}A puff of logic turns the {target['name']} into a healing potion!{Colors.RESET}")
            game_map[target['y']][target['x']] = '!'; enemies[:] = [e for e in enemies if e != target]
    elif effect == "gold_fever":
        add_message(f"{Colors.YELLOW}A chest full of treasure appears!{Colors.RESET}")
        for _ in range(10):
            nx, ny = player_x + random.randint(-2, 2), player_y + random.randint(-2, 2)
            if 0 < nx < MAP_WIDTH-1 and 0 < ny < MAP_HEIGHT-1 and game_map[ny][nx] == FLOOR_CHAR and not is_blocked(nx, ny): chests.append((nx,ny)); break
    elif effect == "fumble":
         add_message(f"{Colors.DIM}You slip on a banana peel and waste your turn.{Colors.RESET}")

def drink_from_fountain():
    global player_current_hp, player_max_hp, inventory
    add_message(f"You drink from the {Colors.BRIGHT_BLUE}fountain...{Colors.RESET}")
    effects = ["heal", "poison", "identify", "spawn_monster"]
    effect = random.choice(effects)
    if effect == "heal":
        add_message("The water is pure and refreshing. You are fully healed!"); player_current_hp = player_max_hp
    elif effect == "poison":
        add_message("The water tastes foul! You feel sick."); player_take_damage(10)
    elif effect == "identify":
        add_message("The water grants you a moment of clarity! You feel more experienced."); gain_xp(50)
    elif effect == "spawn_monster":
        add_message("The water ripples and an angry Goblin emerges!")
        goblin_type = next((e for e in ENEMY_TYPES if e['name'] == 'Goblin'), None)
        if goblin_type:
             for _ in range(10):
                nx, ny = player_x + random.randint(-1, 1), player_y + random.randint(-1, 1)
                if game_map[ny][nx] == FLOOR_CHAR and not is_blocked(nx, ny):
                    new_enemy = goblin_type.copy(); new_enemy.update({'x': nx, 'y': ny, 'current_hp': goblin_type['hp'], 'id': len(enemies) + len(minions)}); enemies.append(new_enemy); break
    game_map[player_y][player_x] = FLOOR_CHAR

def pray_at_altar():
    global player_current_hp, player_max_hp, player_class_info
    add_message(f"You kneel and pray at the {Colors.BRIGHT_YELLOW}altar...{Colors.RESET}")
    effect = "blessing" if random.random() < 0.7 else "curse"
    if effect == "blessing":
        add_message("The gods smile upon you! Your base attack and max HP permanently increase.")
        player_class_info['base_attack'] += 1; player_max_hp += 5; player_current_hp += 5
    elif effect == "curse":
        add_message("The gods are displeased! You feel weakened.")
        player_take_damage(15); player_max_hp = max(10, player_max_hp - 5)
    game_map[player_y][player_x] = FLOOR_CHAR

def spring_trap(trap):
    global player_current_hp
    trap['revealed'] = True; trap_type = trap['type']
    if trap_type == "arrow":
        dmg = random.randint(5, 15); add_message(f"{Colors.RED}An arrow flies from the wall and hits you for {dmg} damage!{Colors.RESET}"); player_take_damage(dmg)
    elif trap_type == "gas":
        add_message(f"{Colors.GREEN}A cloud of poisonous gas erupts from the floor!{Colors.RESET}"); player_take_damage(10)
    elif trap_type == "pit":
        add_message(f"{Colors.DIM}The floor gives way and you fall into a pit!{Colors.RESET}"); player_take_damage(5)

# --- Initialization & Game Logic ---
def initialize_player():
    global player_class_info, player_max_hp, player_current_hp, player_char, player_fov_radius
    global player_level, player_xp, xp_to_next_level, equipped_melee, equipped_ranged, inventory, hit_enemy_ids, player_state, minions
    player_class_info = random.choice(PLAYER_CLASSES)
    player_max_hp = player_class_info["hp"]; player_current_hp = player_max_hp
    player_char = player_class_info["char"]; player_fov_radius = BASE_FOV_RADIUS
    player_level, player_xp, xp_to_next_level = 1, 0, 50
    inventory, hit_enemy_ids, minions = [], set(), []
    player_state = {"spellblade_charges": 0, "shadow_critz": False, "demigod_buff_turns": 0, "serpent_shed_skin": True}
    if player_class_info["passives"]["name"] == "Divine Spark":
        player_max_hp += 10; player_current_hp += 10; player_class_info['base_attack'] += 2
    equipped_melee = Weapon("Fists", 1, 'melee')
    if "range" in player_class_info:
        equipped_ranged = Weapon("Sling", 2, 'ranged') if player_class_info["name"] != "Mage" else Weapon("Magic Bolt", 3, 'ranged')
    else: equipped_ranged = None
    if player_class_info["passives"]["name"] == "Keen Eyes": player_fov_radius += 2
    if player_class_info["passives"]["name"] == "Well Supplied":
        for _ in range(2): inventory.append(random.choice(POTION_TYPES))
        inventory.append(random.choice(SCROLL_TYPES)); add_message(f"{Colors.YELLOW}Your Artificer's bag came well-supplied!{Colors.RESET}")
    if player_class_info["passives"]["name"] == "Pact-Bound Imp":
        minions.append({'name': 'Imp', 'char': 'i', 'hp': 8, 'attack': 5, 'x': -1, 'y': -1, 'id': len(enemies) + len(minions)}); add_message(f"{Colors.MAGENTA}A fiendish Imp appears by your side!{Colors.RESET}")
    if player_class_info["passives"]["name"] == "One from Many":
        for _ in range(2): minions.append({'name': 'Drone', 'char': 'd', 'hp': 10, 'attack': 4, 'x': -1, 'y': -1, 'id': len(enemies) + len(minions)})
        add_message(f"{Colors.GREEN}Drones emerge to serve the Hivemind!{Colors.RESET}")
    add_message(f"You are a {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET}!"); add_message(f"{Colors.BRIGHT_CYAN}Passive:{Colors.RESET} {player_class_info['passives']['name']}{Colors.RESET} - {player_class_info['passives']['desc']}")

def get_player_attack_power(attack_type='melee'):
    base_atk = player_class_info["base_attack"]
    if player_class_info["passives"]["name"] == "One from Many":
        base_atk += (2 * sum(1 for m in minions if m['name'] == 'Drone'))
    weapon = equipped_melee if attack_type == 'melee' else equipped_ranged
    weapon_bonus = weapon.damage_bonus if weapon else 0
    passive = player_class_info["passives"]["name"]
    if passive == "Arcane Mastery": base_atk += 2
    elif passive == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3): base_atk += 3
    if player_state.get("demigod_buff_turns", 0) > 0 and player_state.get("demigod_buff_type") == "damage":
        return (base_atk + weapon_bonus) * 2
    return base_atk + weapon_bonus

def generate_map():
    global game_map, player_x, player_y, fov_map, enemies, chests, minions, lich_resurrected_this_floor, player_max_hp, player_class_info, player_state, traps
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]; fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    rooms, chests, traps = [], [], []; lich_resurrected_this_floor = False; player_state["serpent_shed_skin"] = True
    if player_class_info.get("passives", {}).get("name") == "Ancestral Favor":
        if random.random() < 0.5:
            player_max_hp += 5; add_message(f"{Colors.BRIGHT_BLUE}An ancestral spirit bolsters your health!{Colors.RESET}")
        else:
            player_class_info['base_attack'] += 1; add_message(f"{Colors.BRIGHT_BLUE}An ancestral spirit sharpens your attacks!{Colors.RESET}")
        player_current_hp = player_max_hp
    for _ in range(MAX_ROOMS):
        w,h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x,y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
        new_room = Rect(x, y, w, h)
        if any(new_room.intersects(other) for other in rooms): continue
        create_room(new_room)
        (new_cx, new_cy) = new_room.center()
        if not rooms:
            player_x, player_y = new_cx, new_cy
            for minion in minions: minion['x'], minion['y'] = player_x + random.randint(-1, 1), player_y + random.randint(-1, 1)
        else:
            (prev_cx, prev_cy) = rooms[-1].center()
            if random.randint(0,1): create_h_tunnel(prev_cx, new_cx, prev_cy); create_v_tunnel(prev_cy, new_cy, new_cx)
            else: create_v_tunnel(prev_cy, new_cy, prev_cx); create_h_tunnel(prev_cx, new_cx, new_cy)
        spawn_entities(new_room); rooms.append(new_room)
    if not rooms:
        player_x, player_y = MAP_WIDTH // 2, MAP_HEIGHT // 2; game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    if rooms:
        final_room_center = rooms[-1].center()
        if dungeon_level == BOSS_FLOOR:
            enemies.clear(); boss_type = next(e for e in ENEMY_TYPES if e['name'] == 'The Balrog'); boss = boss_type.copy()
            boss.update({'x': final_room_center[0], 'y': final_room_center[1], 'current_hp': boss_type['hp'], 'id': len(enemies)})
            enemies.append(boss); add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}You have entered the Balrog's Lair!{Colors.RESET}")
        else: game_map[final_room_center[1]][final_room_center[0]] = STAIRS_DOWN_CHAR
    update_fov()

def player_attack_enemy(enemy_obj, attack_type):
    global enemies, player_current_hp, hit_enemy_ids, player_state, game_map
    if player_class_info["passives"]["name"] == "Event Horizon": return "playing"
    current_player_atk = get_player_attack_power(attack_type); enemy_def = enemy_obj.get('defense', 0); is_critical = False; passive_name = player_class_info["passives"]["name"]
    if player_state.get("shadow_critz") and attack_type == 'melee':
        is_critical = True; add_message(f"{Colors.DIM}You strike from the shadows!{Colors.RESET}"); player_state["shadow_critz"] = False
    elif passive_name == "Assassinate" and enemy_obj['id'] not in hit_enemy_ids:
        is_critical = True; add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}Assassinate!{Colors.RESET}")
    if passive_name == "Smite Evil" and enemy_obj.get('type') == 'undead': current_player_atk += 3
    if passive_name == "Judge the Unworthy" and enemy_obj.get('type') in ['undead', 'demon']: current_player_atk += 3
    damage = max(0, current_player_atk - enemy_def)
    if is_critical: damage *= 2
    if enemy_obj.get("behavior") == "enrage":
        enemy_obj['attack'] += 1; add_message(f"The {enemy_obj['name']} roars in fury, growing stronger!")
    if passive_name == "Necrotic Strike" and attack_type == 'melee' and random.random() < 0.20:
        damage += 5; add_message(f"{Colors.MAGENTA}Necrotic energy bursts forth!{Colors.RESET}")
    if passive_name == "Spell-Charged Strike" and attack_type == 'melee':
        player_state["spellblade_charges"] = (player_state.get("spellblade_charges", 0) + 1) % 4
        if player_state["spellblade_charges"] == 0:
            damage += 10; add_message(f"{Colors.BRIGHT_PURPLE}Your blade discharges arcane energy!{Colors.RESET}")
    if passive_name == "Phylactery": player_current_hp = min(player_max_hp, player_current_hp + math.ceil(damage * 0.15))
    if passive_name == "Berserker" and player_current_hp <= math.floor(player_max_hp * 0.3): player_current_hp = min(player_max_hp, player_current_hp + math.ceil(damage * 0.10))
    if passive_name == "Lesser Thirst": player_current_hp = min(player_max_hp, player_current_hp + math.floor(damage / 8))
    if passive_name == "Divine Judgement" and random.random() < 0.20:
        add_message(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}Divine Judgement!{Colors.RESET}"); player_current_hp = min(player_max_hp, player_current_hp + 10); damage *= 2
    if passive_name == "Corrosive Acid": enemy_obj['defense'] = max(0, enemy_obj['defense'] - 1)
    add_combat_effect(enemy_obj['x'], enemy_obj['y'], EFFECT_ATTACK)
    if passive_name == "Colossal Cleave" and attack_type == 'melee':
        add_message(f"Your {Colors.BRIGHT_BLUE}Colossal Cleave{Colors.RESET} hits multiple foes!")
        for ex, ey in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1,-1), (-1,1), (1,-1), (1,1)]:
            check_x, check_y = enemy_obj['x'] + ex, enemy_obj['y'] + ey
            aoe_target = next((e for e in enemies if e['x'] == check_x and e['y'] == check_y), None)
            if aoe_target and aoe_target != enemy_obj: aoe_target['current_hp'] -= damage; add_combat_effect(check_x, check_y, EFFECT_ATTACK)
    enemy_obj['current_hp'] -= damage; hit_enemy_ids.add(enemy_obj['id'])
    if passive_name == "Erase" and enemy_obj['name'] != 'The Balrog' and enemy_obj['current_hp'] > 0 and (enemy_obj['current_hp'] / enemy_obj['hp']) < 0.3 and random.random() < 0.20:
        add_message(f"The {enemy_obj['name']} is {Colors.BOLD}{Colors.BRIGHT_PURPLE}erased from reality!{Colors.RESET}"); enemies[:] = [e for e in enemies if e != enemy_obj]; return "playing"
    if enemy_obj['current_hp'] <= 0:
        if enemy_obj.get("behavior") == "split":
            add_message(f"The {enemy_obj['name']} splits in two!"); enemies[:] = [e for e in enemies if e != enemy_obj]
            slime_type = next((e for e in ENEMY_TYPES if e['name'] == 'Small Slime'), None)
            if slime_type:
                for _ in range(2):
                    for _attempt in range(5):
                        nx, ny = enemy_obj['x'] + random.randint(-1, 1), enemy_obj['y'] + random.randint(-1, 1)
                        if game_map[ny][nx] == FLOOR_CHAR and not is_blocked(nx, ny):
                            new_enemy = slime_type.copy(); new_enemy.update({'x': nx, 'y': ny, 'current_hp': slime_type['hp'], 'id': len(enemies) + len(minions)}); enemies.append(new_enemy); break
            return "playing"
        add_message(f"{Colors.BRIGHT_GREEN}You defeated the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET}!")
        if game_map[enemy_obj['y']][enemy_obj['x']] == FLOOR_CHAR: game_map[enemy_obj['y']][enemy_obj['x']] = DEAD_ENEMY_CHAR
        gain_xp(enemy_obj.get('xp_value', 0))
        if passive_name == "Victory Rush":
            player_current_hp = min(player_max_hp, player_current_hp + 5); add_message(f"{Colors.BRIGHT_RED}The thrill of victory restores you!{Colors.RESET}")
        if passive_name == "Raise Dead" and random.random() < 0.3:
            add_message(f"You raise the {enemy_obj['name']} as a zombie!"); minions.append({'name': 'Zombie', 'char': 'z', 'hp': 10, 'attack': 4, 'x': enemy_obj['x'], 'y': enemy_obj['y'], 'id': len(enemies) + len(minions)})
        if enemy_obj['name'] == 'The Balrog': return "won"
        enemies[:] = [e for e in enemies if e != enemy_obj]
    else: add_message(f"You attack the {enemy_obj['color_code']}{enemy_obj['name']}{Colors.RESET} for {Colors.BRIGHT_RED}{damage}{Colors.RESET} damage.")
    return "playing"

def player_take_damage(damage_amount):
    global player_current_hp
    add_combat_effect(player_x, player_y, EFFECT_ATTACK); passive = player_class_info["passives"]["name"]
    if passive == "Divine Shield" and random.random() < 0.15:
        add_message(f"{Colors.BOLD}{Colors.WHITE}Your Divine Shield blocks all damage!{Colors.RESET}"); return
    if passive == "Improved Fortitude": damage_amount = max(1, damage_amount - 1)
    if passive == "Iron Form": damage_amount = max(0, damage_amount - 2)
    if passive == "Evasion Master" and random.random() < 0.15:
        add_message(f"{Colors.BRIGHT_CYAN}You deftly evade the attack!{Colors.RESET}"); return
    player_current_hp -= damage_amount; add_message(f"{Colors.BRIGHT_RED}You take {damage_amount} damage!{Colors.RESET}")
    if player_current_hp < 0: player_current_hp = 0
    if passive == "Retaliation" and random.random() < 0.25:
        attacker = next((e for e in enemies if max(abs(e['x']-player_x), abs(e['y']-player_y)) <= 1), None)
        if attacker: add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}You retaliate!"); player_attack_enemy(attacker, 'melee')
    auto_use_potion()

def handle_input():
    global player_x, player_y, turns, dungeon_level, lich_resurrected_this_floor, player_current_hp, player_max_hp, player_state, enemies
    action = getch().lower(); target_x, target_y = player_x, player_y; moved, turn_spent, acted = False, False, False
    if action in 'wasd':
        if action == 'w': target_y -= 1
        elif action == 's': target_y += 1
        elif action == 'a': target_x -= 1
        elif action == 'd': target_x += 1
        moved = True
    elif action == 'p' and player_class_info["passives"]["name"] == "Corrosive Acid" and player_state.get("serpent_shed_skin", False):
        player_state["serpent_shed_skin"] = False; player_current_hp = player_max_hp
        add_message(f"You {Colors.BOLD}{Colors.GREEN}shed your skin{Colors.RESET}, feeling renewed!"); turn_spent = True; acted = True
    elif action == 'u':
        if use_item_menu() == "used_item": turn_spent = True; acted = True
    elif action == 'q': return "quit"
    else: return "playing"
    if moved:
        turn_spent = True
        trap = next((t for t in traps if t['x'] == target_x and t['y'] == target_y and not t['revealed']), None)
        if trap:
            spring_trap(trap); player_x, player_y = target_x, target_y; update_fov()
        else:
            chest_pos = next((c for c in chests if c[0] == target_x and c[1] == target_y), None)
            bumped_enemy = next((e for e in enemies if e['x'] == target_x and e['y'] == target_y), None)
            if chest_pos: open_chest(chest_pos)
            elif bumped_enemy:
                acted = True; game_state = player_attack_enemy(bumped_enemy, 'melee')
                if game_state == "won": return "won"
            elif not is_blocked(target_x, target_y):
                player_x, player_y = target_x, target_y; update_fov()
                tile_char = game_map[player_y][player_x]
                if tile_char == FOUNTAIN_CHAR: drink_from_fountain()
                elif tile_char == ALTAR_CHAR: pray_at_altar()
                acted = auto_combat_action()
            else: add_message(f"{Colors.BRIGHT_RED}Ouch! A wall.{Colors.RESET}")
    if turn_spent:
        passive_name = player_class_info["passives"]["name"]
        if not acted and passive_name == "Shadow Dance":
            player_state["shadow_critz"] = True; add_message("You blend into the shadows, preparing to strike...")
        elif acted: player_state["shadow_critz"] = False
        if player_state.get("demigod_buff_turns", 0) > 0: player_state["demigod_buff_turns"] -= 1
        turns += 1
        if passive_name == "Divine Spark" and turns % 50 == 0 and turns > 0:
            if random.random() < 0.5:
                add_message(f"A {Colors.YELLOW}Divine Blessing{Colors.RESET} fully heals you!"); player_current_hp = player_max_hp
            else:
                add_message(f"A {Colors.YELLOW}Divine Blessing{Colors.RESET} doubles your damage for 5 turns!"); player_state["demigod_buff_turns"] = 5; player_state["demigod_buff_type"] = "damage"
        if passive_name == "Event Horizon":
            add_message(f"Your {Colors.DIM}Event Horizon{Colors.RESET} crushes nearby enemies.")
            for enemy in list(enemies):
                if max(abs(enemy['x'] - player_x), abs(enemy['y'] - player_y)) <= 1:
                    enemy['current_hp'] -= 8
                    add_combat_effect(enemy['x'], enemy['y'], EFFECT_ATTACK)
                    if enemy['current_hp'] <= 0:
                        add_message(f"The {enemy['name']} is crushed by the gravity."); enemies[:] = [e for e in enemies if e != enemy]
        if passive_name == "Pandora's Box": chaos_jester_effect()
        if passive_name == "Temporal Slip" and random.random() < 0.15:
            add_message(f"{Colors.BRIGHT_CYAN}Time slips, granting you another turn!{Colors.RESET}"); draw_game(); return "playing"
        enemy_turn(); minion_turn()
        if game_map[player_y][player_x] == STAIRS_DOWN_CHAR:
            dungeon_level += 1; add_message(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}You descend...{Colors.RESET}"); generate_map(); return "playing"
    if player_current_hp <= 0:
        passive_name = player_class_info.get("passives", {}).get("name")
        if not lich_resurrected_this_floor:
            if passive_name == "Phylactery":
                lich_resurrected_this_floor = True; player_current_hp = math.floor(player_max_hp * 0.5); add_message(f"{Colors.BOLD}{Colors.MAGENTA}Your phylactery glows...{Colors.RESET}"); return "playing"
            if passive_name == "Causal Rejection":
                lich_resurrected_this_floor = True; player_current_hp = player_max_hp; add_message(f"{Colors.BOLD}{Colors.BRIGHT_PURPLE}You reject reality...{Colors.RESET}"); return "playing"
            if passive_name == "Rebirth in Flame":
                lich_resurrected_this_floor = True; player_current_hp = player_max_hp; add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}You are reborn from the ashes!{Colors.RESET}")
                for enemy in list(enemies):
                    if fov_map[enemy['y']][enemy['x']] == 2:
                        enemy['current_hp'] -= 25
                        if enemy['current_hp'] <= 0: add_message(f"The {enemy['name']} is incinerated!"); 
                enemies[:] = [e for e in enemies if e['current_hp'] > 0]; return "playing"
        return "lost"
    return "playing"

def game_loop():
    initialize_player(); generate_map()
    game_state = "playing"
    while game_state == "playing":
        draw_game(); game_state = handle_input()
    draw_game()
    final_message = ""
    if game_state == "won": final_message = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 VICTORY! The Balrog is defeated! You have conquered the dungeon! 🎉{Colors.RESET}"
    elif game_state == "lost": final_message = f"{Colors.BOLD}{Colors.BRIGHT_RED}💀 DEFEAT! Died on level {dungeon_level} after {turns} turns. 💀{Colors.RESET}"
    elif game_state == "quit": final_message = f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}You quit on level {dungeon_level} after {turns} turns. Farewell!{Colors.RESET}"
    print(final_message)

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
    return any(enemy['x'] == x and enemy['y'] == y for enemy in enemies) or any(minion['x'] == x and minion['y'] == y for minion in minions)

def spawn_entities(room):
    global enemies, chests, traps
    eligible_enemies = [e for e in ENEMY_TYPES if e['spawn_level'] <= dungeon_level and e['name'] != 'The Balrog']
    if eligible_enemies:
        for _ in range(random.randint(0, MAX_ENEMIES_PER_ROOM + dungeon_level // 3)):
            for _attempt in range(10):
                x = random.randint(room.x1 + 1, room.x2 - 1); y = random.randint(room.y1 + 1, room.y2 - 1)
                if not is_blocked(x, y):
                    enemy_type = random.choice(eligible_enemies); new_enemy = enemy_type.copy()
                    new_enemy.update({'x': x, 'y': y, 'current_hp': new_enemy['hp'], 'id': len(enemies) + len(minions)}); enemies.append(new_enemy); break
    for _ in range(random.randint(0, MAX_CHESTS_PER_ROOM)):
        for _attempt in range(10):
            x, y = random.randint(room.x1 + 1, room.x2 - 1), random.randint(room.y1 + 1, room.y2 - 1)
            if not is_blocked(x, y) and game_map[y][x] == FLOOR_CHAR:
                feature_roll = random.random()
                if feature_roll < 0.6: chests.append((x,y))
                elif feature_roll < 0.8: game_map[y][x] = FOUNTAIN_CHAR
                else: game_map[y][x] = ALTAR_CHAR
                break
    for _ in range(random.randint(0, 2)):
        for _attempt in range(10):
            x, y = random.randint(room.x1 + 1, room.x2 - 1), random.randint(room.y1 + 1, room.y2 - 1)
            if not is_blocked(x, y) and game_map[y][x] == FLOOR_CHAR:
                 traps.append({'x': x, 'y': y, 'type': random.choice(["arrow", "gas", "pit"]), 'revealed': False}); break

def get_line(x1, y1, x2, y2):
    points = []; dx = abs(x2 - x1); dy = abs(y2 - y1)
    x, y, sx, sy = x1, y1, 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
    if dx > dy:
        err = dx / 2.0
        while True:
            points.append((x, y));
            if x == x2: break
            err -= dy
            if err < 0: y += sy; err += dx
            x += sx
    else:
        err = dy / 2.0
        while True:
            points.append((x, y));
            if y == y2: break
            err -= dx
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
            if x_offset**2 + y_offset**2 > player_fov_radius**2: continue
            target_x, target_y = player_x + x_offset, player_y + y_offset
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
            for lx, ly in get_line(player_x, player_y, target_x, target_y):
                fov_map[ly][lx] = 2
                if game_map[ly][lx] == WALL_CHAR: break

def add_message(msg):
    global game_message; game_message.append(msg)
    if len(game_message) > 5: game_message.pop(0)

def add_combat_effect(x, y, effect_type, duration=2): combat_effects.append((x, y, effect_type, duration))
def update_combat_effects():
    global combat_effects; combat_effects[:] = [(x,y,e,d-1) for x,y,e,d in combat_effects if d > 1]

def get_char_at(x, y):
    if next((t for t in traps if t['x'] == x and t['y'] == y and t['revealed']), None):
        return f"{Colors.TRAP_COLOR}{TRAP_CHAR}{Colors.RESET}"
    if next((eff for eff in combat_effects if eff[0] == x and eff[1] == y), None):
        return EFFECT_CHARS[next(eff for eff in combat_effects if eff[0] == x and eff[1] == y)[2]]
    if x == player_x and y == player_y: return f"{player_class_info.get('color_code', Colors.RESET)}{player_char}{Colors.RESET}"
    for minion in minions:
        if minion['x'] == x and minion['y'] == y: return f"{Colors.DIM}{Colors.GREEN}{minion['char']}{Colors.RESET}"
    if any(c[0] == x and c[1] == y for c in chests): return f"{CHEST_COLOR}{CHEST_CHAR}{Colors.RESET}"
    char = game_map[y][x]
    if char == FOUNTAIN_CHAR: return f"{Colors.FOUNTAIN_COLOR}{char}{Colors.RESET}"
    if char == ALTAR_CHAR: return f"{Colors.ALTAR_COLOR}{char}{Colors.RESET}"
    for enemy in enemies:
        if enemy['x'] == x and enemy['y'] == y: return f"{enemy['color_code']}{enemy['char']}{Colors.RESET}"
    color_map = {FLOOR_CHAR: FLOOR_COLOR, WALL_CHAR: WALL_COLOR, STAIRS_DOWN_CHAR: STAIRS_COLOR, DEAD_ENEMY_CHAR: DEAD_ENEMY_COLOR}
    return f"{color_map.get(char, Colors.WHITE)}{char}{Colors.RESET}"

def level_up_bonus():
    global player_max_hp, player_current_hp
    add_message("Choose a bonus: (1) +20 Max HP, (2) +2 Attack")
    while True:
        draw_game(); choice = getch().lower()
        if choice == '1': player_max_hp += 20; player_current_hp = player_max_hp; add_message("Your maximum health increases!"); break
        elif choice == '2': player_class_info['base_attack'] += 2; add_message("Your base attack increases!"); break
        else: add_message("Invalid choice.")

def gain_xp(amount):
    global player_xp, xp_to_next_level, player_level, player_current_hp
    if amount <= 0: return
    player_xp += amount; add_message(f"You gain {amount} XP.")
    if player_xp >= xp_to_next_level:
        player_xp -= xp_to_next_level; player_level += 1; xp_to_next_level = int(xp_to_next_level * 1.5)
        player_current_hp = player_max_hp; add_message(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}LEVEL UP! You are now level {player_level}!{Colors.RESET}"); level_up_bonus()

def minion_turn():
    for minion in list(minions):
        if minion['x'] < 0 or minion['y'] < 0: continue
        closest_enemy, closest_dist = None, float('inf')
        for enemy in enemies:
            if fov_map[enemy['y']][enemy['x']] == 2:
                dist = max(abs(enemy['x'] - minion['x']), abs(enemy['y'] - minion['y']))
                if dist < closest_dist: closest_dist, closest_enemy = dist, enemy
        if closest_enemy:
            if closest_dist <= 1:
                 minion_atk = minion.get('attack', 4); enemy_def = closest_enemy.get('defense', 0); dmg = max(0, minion_atk - enemy_def)
                 closest_enemy['current_hp'] -= dmg; add_message(f"Your {minion['name']} attacks the {closest_enemy['name']} for {dmg} damage.")
                 if closest_enemy['current_hp'] <= 0:
                     add_message(f"The {closest_enemy['name']} was slain by your minion!"); enemies[:] = [e for e in enemies if e != closest_enemy]
            else:
                dx = 1 if closest_enemy['x'] > minion['x'] else -1 if closest_enemy['x'] < minion['x'] else 0
                dy = 1 if closest_enemy['y'] > minion['y'] else -1 if closest_enemy['y'] < minion['y'] else 0
                new_x, new_y = minion['x'] + dx, minion['y'] + dy
                if not is_blocked(new_x, new_y): minion['x'], minion['y'] = new_x, new_y

def enemy_turn():
    for enemy in list(enemies):
        if enemy['current_hp'] <= 0: continue
        ex, ey = enemy['x'], enemy['y']; behavior = enemy.get("behavior")
        if fov_map[ey][ex] != 2: continue
        if behavior == "healer":
            target_ally = next((ally for ally in enemies if ally != enemy and ally['current_hp'] < ally['hp']), None)
            if target_ally:
                if max(abs(ex - target_ally['x']), abs(ey - target_ally['y'])) <= 1:
                    heal_amount = 5; target_ally['current_hp'] = min(target_ally['hp'], target_ally['current_hp'] + heal_amount)
                    add_message(f"The {enemy['name']} heals the {target_ally['name']} for {heal_amount} HP!"); add_combat_effect(target_ally['x'], target_ally['y'], EFFECT_HEAL)
                else:
                    dx = 1 if target_ally['x'] > ex else -1 if target_ally['x'] < ex else 0; dy = 1 if target_ally['y'] > ey else -1 if target_ally['y'] < ey else 0
                    if not is_blocked(ex + dx, ey + dy): enemy['x'] += dx; enemy['y'] += dy
                continue
        elif behavior == "ranged_caster":
            player_dist = max(abs(ex - player_x), abs(ey - player_y))
            if player_dist > 2:
                add_message(f"The {enemy['name']} fires a bolt of magic at you!"); player_take_damage(enemy.get("ranged_attack", 5))
            else:
                dx = -1 if player_x > ex else 1 if player_x < ex else 0; dy = -1 if player_y > ey else 1 if player_y < ey else 0
                if not is_blocked(ex + dx, ey + dy): enemy['x'] += dx; enemy['y'] += dy
                else: player_take_damage(enemy['attack'])
            continue
        player_dist = max(abs(ex - player_x), abs(ey - player_y))
        if player_dist <= 1: player_take_damage(enemy['attack'])
        else:
            dx = 1 if player_x > ex else -1 if player_x < ex else 0; dy = 1 if player_y > ey else -1 if player_y < ey else 0
            nx, ny = ex + dx, ey + dy
            if not is_blocked(nx, ny): enemy['x'], enemy['y'] = nx, ny

def draw_game():
    clear_screen(); update_combat_effects()
    border = "═" * (MAP_WIDTH + 2); print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    for y in range(MAP_HEIGHT):
        row_str = f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
        for x in range(MAP_WIDTH):
            if fov_map[y][x] == 2: row_str += get_char_at(x,y)
            elif fov_map[y][x] == 1:
                row_str += f"{Colors.DIM}{get_char_at(x, y)}{Colors.RESET}"
            else: row_str += f"{UNSEEN_COLOR}{UNSEEN_CHAR}{Colors.RESET}"
        row_str += f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"; print(row_str)
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    hp_perc = player_current_hp / player_max_hp if player_max_hp > 0 else 0
    hp_color = Colors.BRIGHT_GREEN if hp_perc > 0.7 else Colors.BRIGHT_YELLOW if hp_perc > 0.3 else Colors.BRIGHT_RED
    hp_display = f"{Colors.BOLD}HP:{Colors.RESET} {hp_color}{player_current_hp}/{player_max_hp}{Colors.RESET}"; attack_display = f"{Colors.BOLD}Atk:{Colors.RESET} {Colors.BRIGHT_RED}{get_player_attack_power('melee')}{Colors.RESET}"
    level_display = f"{Colors.BOLD}Lvl:{Colors.RESET} {Colors.BRIGHT_YELLOW}{player_level}{Colors.RESET} ({player_xp}/{xp_to_next_level} XP)"; melee_weapon_display = f"{Colors.BOLD}Melee:{Colors.RESET} {equipped_melee.name if equipped_melee else 'None'}"
    ranged_weapon_display = f"{Colors.BOLD}Ranged:{Colors.RESET} {equipped_ranged.name if equipped_ranged else 'None'}"; dungeon_display = f"{Colors.BOLD}Dungeon:{Colors.RESET} {Colors.BRIGHT_MAGENTA}{dungeon_level}{Colors.RESET}"
    print(f"{Colors.BOLD}Class:{Colors.RESET} {player_class_info['color_code']}{player_class_info['name']}{Colors.RESET} | {hp_display} | {attack_display}"); print(f"{level_display} | {dungeon_display}"); print(f"{melee_weapon_display} | {ranged_weapon_display}")
    if minions: print(f"{Colors.BOLD}Minions:{Colors.RESET} {', '.join([f'{m['name']}({m['hp']}hp)' for m in minions])}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}")
    for msg in game_message: print(msg)
    controls = f"{Colors.BOLD}Move:{Colors.YELLOW}W,A,S,D{Colors.RESET} | {Colors.BOLD}Use Item:{Colors.YELLOW}U{Colors.RESET}"
    if player_class_info.get("passives", {}).get("name") == "Corrosive Acid": controls += f" | {Colors.BOLD}Shed Skin:{Colors.YELLOW}P{Colors.RESET}"
    controls += f" | {Colors.BOLD}Quit:{Colors.RED}Q{Colors.RESET}"; print(controls)

def use_item_menu():
    global inventory, player_current_hp, player_x, player_y, fov_map
    if not inventory: add_message("Your inventory is empty."); return "no_action"
    while True:
        draw_game(); print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}--- USE ITEM ---{Colors.RESET}")
        for i, item in enumerate(inventory): print(f"({Colors.YELLOW}{i}{Colors.RESET}) {item.name}")
        print(f"({Colors.RED}ESC{Colors.RESET}) to cancel")
        choice = getch()
        if choice.isdigit() and 0 <= int(choice) < len(inventory):
            item_to_use = inventory[int(choice)]
            if isinstance(item_to_use, Potion):
                heal_multiplier = 1.5 if player_class_info.get("passives",{}).get("name") == "Potent Healing" else 1.0
                if item_to_use.effect == 'heal':
                    heal_amount = int(item_to_use.value * heal_multiplier); player_current_hp = min(player_max_hp, player_current_hp + heal_amount)
                    add_message(f"You drink the {item_to_use.name} and restore {heal_amount} HP."); add_combat_effect(player_x, player_y, EFFECT_HEAL)
                elif item_to_use.effect == 'full_heal':
                    player_current_hp = player_max_hp; add_message(f"You drink the {item_to_use.name} and feel fully restored!"); add_combat_effect(player_x, player_y, EFFECT_HEAL)
                elif item_to_use.effect == 'xp_boost':
                    gain_xp(item_to_use.value); add_message(f"You drink the {item_to_use.name} and feel more experienced!")
                inventory.remove(item_to_use); return "used_item"
            elif isinstance(item_to_use, Scroll):
                if item_to_use.effect == 'teleport':
                    for _ in range(100):
                        nx, ny = random.randint(1, MAP_WIDTH - 2), random.randint(1, MAP_HEIGHT - 2)
                        if game_map[ny][nx] == FLOOR_CHAR and not is_blocked(nx, ny): player_x, player_y = nx, ny; break
                    add_message("The world blurs and reforms around you!"); update_fov()
                elif item_to_use.effect == 'map_reveal':
                    for y in range(MAP_HEIGHT):
                        for x in range(MAP_WIDTH):
                             if game_map[y][x] != WALL_CHAR: fov_map[y][x] = 2
                    add_message("The scroll reveals the layout of the dungeon floor!"); update_fov()
                inventory.remove(item_to_use); return "used_item"
            else: add_message("You can't use that item.")
        elif choice == '\x1b': add_message("You decide against using an item."); return "no_action"

def open_chest(chest_pos):
    global chests, equipped_melee, equipped_ranged, inventory
    loot = random.choice(CHEST_LOOT_TABLE); add_message(f"You open the chest and find a {loot.name}!")
    if isinstance(loot, Weapon):
        if loot.weapon_type == 'melee':
            if not equipped_melee or loot.damage_bonus > equipped_melee.damage_bonus:
                add_message(f"You equip the {loot.name}."); equipped_melee = loot
            else: add_message(f"You stash the {loot.name}."); inventory.append(loot)
        elif loot.weapon_type == 'ranged':
            if "range" in player_class_info:
                if not equipped_ranged or loot.damage_bonus > equipped_ranged.damage_bonus:
                    add_message(f"You equip the {loot.name}."); equipped_ranged = loot
                else: add_message(f"You stash the {loot.name}."); inventory.append(loot)
            else: add_message("You can't use this ranged weapon.")
    else: inventory.append(loot); add_message(f"You add the {loot.name} to your inventory.")
    chests.remove(chest_pos)

def auto_use_potion():
    global player_current_hp, inventory
    if player_current_hp / player_max_hp < 0.25:
        potion_to_use = next((item for item in inventory if isinstance(item, Potion) and item.effect == 'heal'), None)
        if potion_to_use:
            heal_multiplier = 1.5 if player_class_info.get("passives",{}).get("name") == "Potent Healing" else 1.0
            heal_amount = int(potion_to_use.value * heal_multiplier); add_message(f"{Colors.BRIGHT_YELLOW}Health critical! Auto-using {potion_to_use.name}.{Colors.RESET}")
            player_current_hp = min(player_max_hp, player_current_hp + heal_amount); inventory.remove(potion_to_use)

def auto_combat_action():
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1,-1), (-1,1), (1,-1), (1,1)]:
        check_x, check_y = player_x + dx, player_y + dy
        if 0 <= check_x < MAP_WIDTH and 0 <= check_y < MAP_HEIGHT and fov_map[check_y][check_x] == 2:
            target_enemy = next((e for e in enemies if e['x'] == check_x and e['y'] == check_y), None)
            if target_enemy: player_attack_enemy(target_enemy, 'melee'); return True
    if equipped_ranged:
        visible_enemies = [e for e in enemies if fov_map[e['y']][e['x']] == 2 and max(abs(e['x']-player_x), abs(e['y']-player_y)) > 1]
        if visible_enemies:
            target = min(visible_enemies, key=lambda e: max(abs(e['x'] - player_x), abs(e['y'] - player_y)))
            if max(abs(target['x'] - player_x), abs(target['y'] - player_y)) <= player_class_info.get("range", 0):
                 player_attack_enemy(target, 'ranged'); return True
    return False

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