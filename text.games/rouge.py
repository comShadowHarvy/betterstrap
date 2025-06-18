import os
import random
import math
import textwrap
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
    def __init__(self, name, description="", char='!'):
        self.name = name
        self.description = description
        self.char = char

class Weapon(Item):
    def __init__(self, name, damage_bonus, weapon_type, description="", char='/'):
        super().__init__(name, description, char)
        self.damage_bonus = damage_bonus
        self.weapon_type = weapon_type

class Potion(Item):
    def __init__(self, name, effect, value, description="", char='!'):
        super().__init__(name, description, char)
        self.effect = effect
        self.value = value

class Scroll(Item):
     def __init__(self, name, effect, value=0, description="", char='?'):
        super().__init__(name, description, char)
        self.effect = effect
        self.value = value

# --- Item/Weapon Definitions ---
POTION_TYPES = [ Potion("Healing Potion", 'heal', 15, "A common potion that restores a small amount of health."), Potion("Greater Healing Potion", 'heal', 30), Potion("Superior Healing Potion", 'heal', 50), Potion("Elixir of Health", 'full_heal', 999), Potion("Potion of Experience", 'xp_boost', 50) ]
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
    {"name": "Monk", "char": "O", "hp": 22, "base_attack": 5, "color_code": Colors.BOLD + Colors.BRIGHT_YELLOW, "passives": {"name": "Ki Master", "desc": "Ignores 1 defense and has a 15% chance to Stun for 1 turn."}},
    {"name": "Paladin", "char": "P", "hp": 28, "base_attack": 6, "color_code": Colors.BOLD + Colors.WHITE, "passives": {"name": "Smite Evil", "desc": "Deals +3 bonus damage to undead enemies"}},
    {"name": "Assassin", "char": "A", "hp": 20, "base_attack": 5, "color_code": Colors.DIM + Colors.WHITE, "passives": {"name": "Assassinate", "desc": "First attack on any enemy is a guaranteed critical hit"}},
    {"name": "Necromancer", "char": "Y", "hp": 18, "base_attack": 4, "color_code": Colors.BOLD + Colors.MAGENTA, "passives": {"name": "Raise Dead", "desc": "30% chance to raise a slain enemy as a loyal Zombie minion"}},
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
    {"name": "Slime", "char": "p", "hp": 12, "attack": 3, "defense": 3, "xp_value": 15, "color_code": Colors.GREEN, "spawn_level": 2, "type": "ooze", "behavior": "split", "on_hit_effect": {"name": "Poison", "duration": 3, "potency": 1, "chance": 0.3}},
    {"name": "Small Slime", "char": "p", "hp": 6, "attack": 2, "defense": 1, "xp_value": 5, "color_code": Colors.DIM + Colors.GREEN, "spawn_level": 2, "type": "ooze"},
    {"name": "Skeleton Mage", "char": "s", "hp": 8, "attack": 0, "defense": 1, "xp_value": 25, "color_code": Colors.DIM + Colors.WHITE, "spawn_level": 5, "type": "undead", "behavior": "ranged_caster", "ranged_attack": 5},
]

# --- Rect Class for Map Generation ---
class Rect:
    def __init__(self, x, y, w, h): self.x1, self.y1, self.x2, self.y2 = x,y,x+w,y+h
    def center(self): return ((self.x1+self.x2)//2, (self.y1+self.y2)//2)
    def intersects(self, other): return (self.x1<=other.x2 and self.x2>=other.x1 and self.y1<=other.y2 and self.y2>=other.y1)

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')

class Entity:
    def __init__(self, x, y, char, color, name):
        self.x, self.y, self.char, self.color, self.name = x, y, char, color, name

class Actor(Entity):
    def __init__(self, x, y, char, color, name, hp, attack, defense=0):
        super().__init__(x, y, char, color, name)
        self.max_hp, self.current_hp = hp, hp
        self.base_attack, self.defense = attack, defense
        self.status_effects = []

    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)

    def has_status(self, status_name):
        return any(effect['name'] == status_name for effect in self.status_effects)

class Player(Actor):
    def __init__(self, class_info):
        super().__init__(0, 0, class_info['char'], class_info['color_code'], class_info['name'], class_info['hp'], class_info['base_attack'])
        self.class_info = class_info
        self.passives = class_info['passives']
        self.level, self.xp, self.xp_to_next_level = 1, 0, 50
        self.inventory, self.equipped_melee, self.equipped_ranged = [], None, None
        self.fov_radius = BASE_FOV_RADIUS
        self.minions, self.hit_enemy_ids = [], set()
        self.state = {"shadow_critz": False}
        self.lich_resurrected_this_floor = False

    def get_attack_power(self, attack_type='melee'):
        base_atk = self.base_attack
        weapon = self.equipped_melee if attack_type == 'melee' else self.equipped_ranged
        weapon_bonus = weapon.damage_bonus if weapon else 0
        passive = self.passives["name"]
        if passive == "Arcane Mastery": base_atk += 2
        elif passive == "Berserker" and self.current_hp <= math.floor(self.max_hp * 0.3): base_atk += 3
        return base_atk + weapon_bonus

class Enemy(Actor):
    _id_counter = 0
    def __init__(self, x, y, enemy_info):
        super().__init__(x, y, enemy_info['char'], enemy_info['color_code'], enemy_info['name'], enemy_info['hp'], enemy_info['attack'], enemy_info.get('defense', 0))
        self.xp_value = enemy_info.get('xp_value', 0)
        self.type = enemy_info.get('type', 'monster')
        self.behavior = enemy_info.get('behavior')
        self.ranged_attack = enemy_info.get('ranged_attack')
        self.on_hit_effect = enemy_info.get('on_hit_effect')
        self.id = Enemy._id_counter
        Enemy._id_counter += 1

class Game:
    def __init__(self):
        self.player = None
        self.enemies, self.chests, self.traps, self.minions = [], [], [], []
        self.dungeon_level, self.turns = 1, 0
        self.game_map, self.fov_map = [], []
        self.game_message = ["Welcome! Explore and survive."]
        self.combat_effects = []
        self.game_state = 'PLAYING'
        self.look_cursor_x, self.look_cursor_y = 0, 0
        self.inventory_cursor_pos = 0

    def initialize_player(self):
        player_class_info = random.choice(PLAYER_CLASSES)
        self.player = Player(player_class_info)
        self.player.equipped_melee = Weapon("Fists", 1, 'melee')
        if "range" in self.player.class_info: self.player.equipped_ranged = Weapon("Sling", 2, 'ranged')
        if self.player.passives["name"] == "Keen Eyes": self.player.fov_radius += 2
        self.add_message(f"You are a {self.player.color}{self.player.name}{Colors.RESET}!")
        self.add_message(f"{Colors.BRIGHT_CYAN}Passive:{Colors.RESET} {self.player.passives['name']}{Colors.RESET} - {self.player.passives['desc']}")

    def generate_map(self):
        self.game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        rooms, self.chests, self.traps, self.enemies, self.minions = [], [], [], [], []
        self.player.lich_resurrected_this_floor = False
        self.player.state = {"shadow_critz": False}
        for _ in range(MAX_ROOMS):
            w, h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE), random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x, y = random.randint(1, MAP_WIDTH - w - 2), random.randint(1, MAP_HEIGHT - h - 2)
            new_room = Rect(x, y, w, h)
            if any(new_room.intersects(other) for other in rooms): continue
            self.create_room(new_room)
            (new_cx, new_cy) = new_room.center()
            if not rooms: self.player.x, self.player.y = new_cx, new_cy
            else:
                (prev_cx, prev_cy) = rooms[-1].center()
                if random.randint(0,1): self.create_h_tunnel(prev_cx, new_cx, prev_cy); self.create_v_tunnel(prev_cy, new_cy, new_cx)
                else: self.create_v_tunnel(prev_cy, new_cy, prev_cx); self.create_h_tunnel(prev_cx, new_cx, new_cy)
            self.spawn_entities(new_room)
            rooms.append(new_room)
        if rooms:
            final_room_center = rooms[-1].center()
            if self.dungeon_level == BOSS_FLOOR:
                self.enemies.clear(); boss_type = next(e for e in ENEMY_TYPES if e['name'] == 'The Balrog'); boss = Enemy(final_room_center[0], final_room_center[1], boss_type)
                self.enemies.append(boss); self.add_message(f"{Colors.BOLD}{Colors.BRIGHT_RED}You have entered the Balrog's Lair!{Colors.RESET}")
            else: self.game_map[final_room_center[1]][final_room_center[0]] = STAIRS_DOWN_CHAR
        self.update_fov()

    def handle_input(self):
        if self.game_state == 'PLAYING': return self.handle_playing_input()
        elif self.game_state == 'LOOK_MODE': return self.handle_look_input()
        elif self.game_state == 'INVENTORY': return self.handle_inventory_input()
        return self.game_state

    def handle_playing_input(self):
        action = getch().lower()
        if action == 'l':
            self.look_cursor_x, self.look_cursor_y = self.player.x, self.player.y
            self.game_state = 'LOOK_MODE'
            self.add_message(f"Entering Look Mode. Move with [WASD], exit with [L] or [ESC].")
            return 'playing'
        if action == 'i':
             self.inventory_cursor_pos = 0; self.game_state = 'INVENTORY'
             return 'playing'

        target_x, target_y = self.player.x, self.player.y
        turn_spent = False
        if action in 'wasd':
            if action == 'w': target_y -= 1
            elif action == 's': target_y += 1
            elif action == 'a': target_x -= 1
            elif action == 'd': target_x += 1
            
            bumped_enemy = next((e for e in self.enemies if e.x == target_x and e.y == target_y), None)
            chest_pos = next((c for c in self.chests if c[0] == target_x and c[1] == target_y), None)

            if bumped_enemy:
                game_state = self.player_attack_enemy(bumped_enemy, 'melee')
                if game_state == "won": return "won"
            elif chest_pos:
                self.open_chest(chest_pos)
            elif not self.is_blocked(target_x, target_y):
                self.player.x, self.player.y = target_x, target_y
                self.update_fov()
                tile_char = self.game_map[self.player.y][self.player.x]
                if tile_char == FOUNTAIN_CHAR: self.drink_from_fountain()
                elif tile_char == ALTAR_CHAR: self.pray_at_altar()
            else:
                self.add_message(f"{Colors.BRIGHT_RED}Ouch! A wall.{Colors.RESET}")
                return 'playing'
            turn_spent = True
        elif action == 'q': return "quit"
        else: return "playing"
        
        if turn_spent:
            self.process_actor_turn(self.player)
            if self.player.has_status('Stun'): 
                self.add_message("You are stunned and cannot act!")
            else:
                self.turns += 1
                self.enemy_turn()
                self.minion_turn()
            if self.game_map[self.player.y][self.player.x] == STAIRS_DOWN_CHAR:
                self.dungeon_level += 1; self.add_message(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}You descend...{Colors.RESET}"); self.generate_map()
        
        if self.player.current_hp <= 0: return "lost"
        return "playing"

    def handle_look_input(self):
        action = getch().lower()
        if action in 'wasd':
            if action == 'w': self.look_cursor_y = max(0, self.look_cursor_y - 1)
            elif action == 's': self.look_cursor_y = min(MAP_HEIGHT - 1, self.look_cursor_y + 1)
            elif action == 'a': self.look_cursor_x = max(0, self.look_cursor_x - 1)
            elif action == 'd': self.look_cursor_x = min(MAP_WIDTH - 1, self.look_cursor_x + 1)
        elif action == 'l' or action == '\x1b':
            self.game_state = 'PLAYING'; self.add_message("Exited Look Mode.")
        return 'playing'

    def handle_inventory_input(self):
        action = getch().lower()
        num_items = len(self.player.inventory)
        if action == 'i' or action == '\x1b': self.game_state = 'PLAYING'; return 'playing'
        if num_items == 0: return 'playing'
        if action == 'w': self.inventory_cursor_pos = (self.inventory_cursor_pos - 1 + num_items) % num_items
        elif action == 's': self.inventory_cursor_pos = (self.inventory_cursor_pos + 1) % num_items
        elif action == 'd':
            item_to_drop = self.player.inventory[self.inventory_cursor_pos]; self.player.inventory.pop(self.inventory_cursor_pos)
            self.add_message(f"You drop the {item_to_drop.name}."); self.inventory_cursor_pos = min(self.inventory_cursor_pos, len(self.player.inventory) - 1) if self.player.inventory else 0
        elif action == 'u':
            item_to_use = self.player.inventory[self.inventory_cursor_pos]
            if self.use_item(item_to_use):
                self.game_state = 'PLAYING'; self.turns += 1; self.enemy_turn(); self.minion_turn()
        return 'playing'

    def run(self):
        self.initialize_player(); self.generate_map()
        game_state = "playing"
        while game_state == "playing": self.draw(); game_state = self.handle_input()
        self.draw(); final_message = ""
        if game_state == "won": final_message = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 VICTORY! 🎉{Colors.RESET}"
        elif game_state == "lost": final_message = f"{Colors.BOLD}{Colors.BRIGHT_RED}💀 DEFEAT! 💀{Colors.RESET}"
        elif game_state == "quit": final_message = f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}Farewell!{Colors.RESET}"
        print(final_message)

    def draw(self):
        clear_screen()
        if self.game_state in ['PLAYING', 'LOOK_MODE']:
            self.draw_main_map()
            if self.game_state == 'LOOK_MODE': self.draw_look_info()
        elif self.game_state == 'INVENTORY': self.draw_inventory_screen()

    def draw_main_map(self):
        self.update_combat_effects(); border = "═" * (MAP_WIDTH + 2); print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
        for y in range(MAP_HEIGHT):
            row_str = f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
            for x in range(MAP_WIDTH):
                if self.game_state == 'LOOK_MODE' and x == self.look_cursor_x and y == self.look_cursor_y: row_str += f"{Colors.BOLD}{Colors.YELLOW}X{Colors.RESET}"
                elif self.fov_map[y][x] == 2: row_str += self.get_char_at(x,y)
                elif self.fov_map[y][x] == 1: row_str += f"{Colors.DIM}{self.get_char_at(x, y)}{Colors.RESET}"
                else: row_str += f"{UNSEEN_COLOR}{UNSEEN_CHAR}{Colors.RESET}"
            row_str += f"{Colors.BOLD}{Colors.BRIGHT_CYAN}║{Colors.RESET}"; print(row_str)
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
        
        hp_perc = self.player.current_hp / self.player.max_hp if self.player.max_hp > 0 else 0
        hp_color = Colors.BRIGHT_GREEN if hp_perc > 0.7 else Colors.BRIGHT_YELLOW if hp_perc > 0.3 else Colors.BRIGHT_RED
        hp_display = f"{Colors.BOLD}HP:{Colors.RESET} {hp_color}{self.player.current_hp}/{self.player.max_hp}{Colors.RESET}"
        attack_display = f"{Colors.BOLD}Atk:{Colors.RESET} {Colors.BRIGHT_RED}{self.player.get_attack_power('melee')}{Colors.RESET}"
        level_display = f"{Colors.BOLD}Lvl:{Colors.RESET} {Colors.BRIGHT_YELLOW}{self.player.level}{Colors.RESET} ({self.player.xp}/{self.player.xp_to_next_level} XP)"
        dungeon_display = f"{Colors.BOLD}Dungeon:{Colors.RESET} {Colors.BRIGHT_MAGENTA}{self.dungeon_level}{Colors.RESET}"
        status_display = f"{Colors.BOLD}Status:{Colors.RESET} {self.get_status_effects_string(self.player)}" if self.player.status_effects else ""
        
        print(f"{Colors.BOLD}Class:{Colors.RESET} {self.player.color}{self.player.name}{Colors.RESET} | {hp_display} | {attack_display}")
        if status_display: print(status_display)
        print(f"{level_display} | {dungeon_display}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}")
        for msg in self.game_message: print(msg)
        controls = f"{Colors.BOLD}Move:{Colors.YELLOW}WASD{Colors.RESET} | {Colors.BOLD}Look:{Colors.YELLOW}L{Colors.RESET} | {Colors.BOLD}Inventory:{Colors.YELLOW}I{Colors.RESET} | {Colors.BOLD}Quit:{Colors.RED}Q{Colors.RESET}"; print(controls)

    def draw_look_info(self):
        x, y = self.look_cursor_x, self.look_cursor_y; info = ""
        if self.fov_map[y][x] == 0: info = "You see nothing but darkness."
        elif self.fov_map[y][x] == 1: info = "You remember seeing " + self.get_name_at_location(x, y) + " here."
        else: info = "You see " + self.get_name_at_location(x, y) + "."
        print(f"{Colors.BOLD}{Colors.CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}"); print(f"{Colors.YELLOW}{info}{Colors.RESET}")

    def get_name_at_location(self, x, y):
        if x == self.player.x and y == self.player.y: return f"yourself, the {self.player.name}"
        entity = next((e for e in self.enemies if e.x == x and e.y == y), None)
        if entity: return f"a {entity.name} ({entity.current_hp}/{entity.max_hp} HP){self.get_status_effects_string(entity)}"
        entity = next((m for m in self.minions if m.x == x and m.y == y), None)
        if entity: return f"your loyal {entity.name} ({entity.current_hp}/{entity.max_hp} HP)"
        if any(c[0] == x and c[1] == y for c in self.chests): return "a chest"
        char = self.game_map[y][x]
        return {"#": "a stone wall", ".": "the floor", ">": "stairs leading down", "F": "a shimmering fountain", "A": "a mysterious altar", "^": "a revealed trap", "%": "the corpse of a slain foe"}.get(char, "something unknown")

    def draw_inventory_screen(self):
        print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}--- INVENTORY ---{Colors.RESET}\n{Colors.BOLD}{Colors.WHITE}Equipped Gear{Colors.RESET}\n{'─' * 20}")
        melee_name = self.player.equipped_melee.name if self.player.equipped_melee else "Nothing"
        ranged_name = self.player.equipped_ranged.name if self.player.equipped_ranged else "Nothing"
        print(f"Melee:  {melee_name}\nRanged: {ranged_name}\n\n{Colors.BOLD}{Colors.WHITE}Carried Items{Colors.RESET}\n{'─' * 20}")
        if not self.player.inventory: print(f"{Colors.DIM}Your inventory is empty.{Colors.RESET}")
        else:
            for i, item in enumerate(self.player.inventory):
                prefix = f"{Colors.YELLOW}> {Colors.RESET}" if i == self.inventory_cursor_pos else "  "
                print(f"{prefix}{item.name}")
        print(f"\n\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'─' * (MAP_WIDTH + 2)}{Colors.RESET}\n{Colors.BOLD}Controls:{Colors.RESET} [{Colors.YELLOW}W/S{Colors.RESET}] Navigate | [{Colors.YELLOW}U{Colors.RESET}] Use/Equip | [{Colors.YELLOW}D{Colors.RESET}] Drop | [{Colors.YELLOW}I/ESC{Colors.RESET}] Close")
    
    def use_item(self, item_to_use):
        if isinstance(item_to_use, Potion):
            if item_to_use.effect == 'heal':
                heal_amount = int(item_to_use.value * (1.5 if self.player.passives.get("name") == "Potent Healing" else 1.0))
                self.player.current_hp = min(self.player.max_hp, self.player.current_hp + heal_amount)
                self.add_message(f"You drink the {item_to_use.name} and restore {heal_amount} HP."); self.add_combat_effect(self.player.x, self.player.y, EFFECT_HEAL)
            self.player.inventory.remove(item_to_use); return True
        elif isinstance(item_to_use, Scroll):
            self.player.inventory.remove(item_to_use); return True
        elif isinstance(item_to_use, Weapon):
            if item_to_use.weapon_type == 'melee':
                if self.player.equipped_melee: self.player.inventory.append(self.player.equipped_melee)
                self.player.equipped_melee = item_to_use; self.player.inventory.remove(item_to_use); self.add_message(f"You equip the {item_to_use.name}.")
            elif item_to_use.weapon_type == 'ranged' and "range" in self.player.class_info:
                if self.player.equipped_ranged: self.player.inventory.append(self.player.equipped_ranged)
                self.player.equipped_ranged = item_to_use; self.player.inventory.remove(item_to_use); self.add_message(f"You equip the {item_to_use.name}.")
            else: self.add_message(f"You cannot equip the {item_to_use.name}.")
        return False

    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: self.game_map[y][x] = FLOOR_CHAR

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: self.game_map[y][x] = FLOOR_CHAR

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT: self.game_map[y][x] = FLOOR_CHAR
    
    def is_blocked(self, x, y):
        if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT) or self.game_map[y][x] == WALL_CHAR: return True
        if x == self.player.x and y == self.player.y: return True
        return any(enemy.x == x and enemy.y == y for enemy in self.enemies) or any(minion.x == x and minion.y == y for minion in self.minions)
    
    def get_char_at(self, x, y):
        if next((eff for eff in self.combat_effects if eff[0] == x and eff[1] == y), None): return EFFECT_CHARS[next(eff for eff in self.combat_effects if eff[0] == x and eff[1] == y)[2]]
        if x == self.player.x and y == self.player.y: return f"{self.player.color}{self.player.char}{Colors.RESET}"
        for enemy in self.enemies:
            if enemy.x == x and enemy.y == y: return f"{enemy.color}{enemy.char}{Colors.RESET}"
        if any(c[0] == x and c[1] == y for c in self.chests): return f"{CHEST_COLOR}{CHEST_CHAR}{Colors.RESET}"
        char = self.game_map[y][x]
        return {FLOOR_CHAR: FLOOR_COLOR, WALL_CHAR: WALL_COLOR, STAIRS_DOWN_CHAR: STAIRS_COLOR, DEAD_ENEMY_CHAR: DEAD_ENEMY_COLOR, FOUNTAIN_CHAR: Colors.FOUNTAIN_COLOR, ALTAR_CHAR: Colors.ALTAR_COLOR, TRAP_CHAR: Colors.TRAP_COLOR}.get(char, Colors.WHITE) + char + Colors.RESET

    def add_combat_effect(self, x, y, effect_type, duration=2): self.combat_effects.append((x, y, effect_type, duration))
    def update_combat_effects(self): self.combat_effects[:] = [(x,y,e,d-1) for x,y,e,d in self.combat_effects if d > 1]
    def add_message(self, msg): self.game_message.append(msg); self.game_message = self.game_message[-5:]
    
    def enemy_turn(self):
        for enemy in list(self.enemies):
            if enemy.current_hp <= 0: continue
            self.process_actor_turn(enemy)
            if enemy.has_status('Stun'): self.add_message(f"The {enemy.name} is stunned!"); continue
            if self.fov_map[enemy.y][enemy.x] != 2: continue
            player_dist = max(abs(enemy.x - self.player.x), abs(enemy.y - self.player.y))
            if player_dist <= 1:
                self.player_take_damage(enemy.base_attack, enemy)
            else:
                dx = 1 if self.player.x > enemy.x else -1 if self.player.x < enemy.x else 0
                dy = 1 if self.player.y > enemy.y else -1 if self.player.y < enemy.y else 0
                nx, ny = enemy.x + dx, enemy.y + dy
                if not self.is_blocked(nx, ny): enemy.x, enemy.y = nx, ny

    def minion_turn(self): pass

    def spawn_entities(self, room):
        eligible_enemies = [e for e in ENEMY_TYPES if e['spawn_level'] <= self.dungeon_level and e['name'] != 'The Balrog']
        if eligible_enemies:
            for _ in range(random.randint(0, MAX_ENEMIES_PER_ROOM + self.dungeon_level // 3)):
                for _attempt in range(10):
                    x, y = random.randint(room.x1 + 1, room.x2 - 1), random.randint(room.y1 + 1, room.y2 - 1)
                    if not self.is_blocked(x, y): self.enemies.append(Enemy(x, y, random.choice(eligible_enemies))); break
        for _ in range(random.randint(0, MAX_CHESTS_PER_ROOM)):
            for _attempt in range(10):
                x, y = random.randint(room.x1 + 1, room.x2 - 1), random.randint(room.y1 + 1, room.y2 - 1)
                if not self.is_blocked(x, y) and self.game_map[y][x] == FLOOR_CHAR:
                    feature_roll = random.random()
                    if feature_roll < 0.7: self.chests.append((x,y))
                    elif feature_roll < 0.85: self.game_map[y][x] = FOUNTAIN_CHAR
                    else: self.game_map[y][x] = ALTAR_CHAR
                    break

    def player_attack_enemy(self, enemy, attack_type):
        damage = max(0, self.player.get_attack_power(attack_type) - enemy.defense)
        self.add_combat_effect(enemy.x, enemy.y, EFFECT_ATTACK); enemy.take_damage(damage)
        self.add_message(f"You attack the {enemy.name} for {damage} damage.")
        if self.player.passives['name'] == 'Ki Master' and random.random() < 0.15: self.apply_status_effect(enemy, 'Stun', 2)
        if enemy.current_hp <= 0:
            self.add_message(f"{Colors.BRIGHT_GREEN}You defeated the {enemy.name}!{Colors.RESET}"); self.game_map[enemy.y][enemy.x] = DEAD_ENEMY_CHAR
            self.gain_xp(enemy.xp_value)
            if enemy.name == 'The Balrog': return "won"
            self.enemies.remove(enemy)
        return "playing"
        
    def player_take_damage(self, damage_amount, attacker):
        if isinstance(attacker, Actor):
            self.add_message(f"The {attacker.name} hits you for {damage_amount} damage!")
            if attacker.on_hit_effect and random.random() < attacker.on_hit_effect['chance']:
                self.apply_status_effect(self.player, attacker.on_hit_effect['name'], attacker.on_hit_effect['duration'], attacker.on_hit_effect['potency'])
        else: # The attacker is a string description, e.g. from a trap or altar
            self.add_message(f"You take {damage_amount} damage from {attacker}!")

        if self.player.passives["name"] == "Improved Fortitude": damage_amount = max(1, damage_amount - 1)
        
        self.player.take_damage(damage_amount)
        self.add_combat_effect(self.player.x, self.player.y, EFFECT_ATTACK)
        
        self.auto_use_potion()

    def gain_xp(self, amount):
        if amount <= 0: return
        self.player.xp += amount; self.add_message(f"You gain {amount} XP.")
        if self.player.xp >= self.player.xp_to_next_level:
            self.player.xp -= self.player.xp_to_next_level; self.player.level += 1; self.player.xp_to_next_level = int(self.player.xp_to_next_level * 1.5)
            self.player.current_hp = self.player.max_hp; self.add_message(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}LEVEL UP! You are now level {self.player.level}!{Colors.RESET}"); self.level_up_bonus()

    def level_up_bonus(self):
        self.add_message("Choose a bonus: (1) +20 Max HP, (2) +2 Attack")
        while True:
            self.draw(); choice = getch().lower()
            if choice == '1': self.player.max_hp += 20; self.player.current_hp = self.player.max_hp; self.add_message("Your maximum health increases!"); break
            elif choice == '2': self.player.base_attack += 2; self.add_message("Your base attack increases!"); break
            else: self.add_message("Invalid choice.")
            
    def open_chest(self, chest_pos):
        loot = random.choice(CHEST_LOOT_TABLE); self.add_message(f"You open the chest and find a {loot.name}!")
        self.player.inventory.append(loot); self.chests.remove(chest_pos)

    def auto_use_potion(self):
        if self.player.current_hp > 0 and self.player.current_hp / self.player.max_hp < 0.25:
            potion = next((item for item in self.player.inventory if isinstance(item, Potion) and item.effect == 'heal'), None)
            if potion: self.add_message(f"{Colors.BRIGHT_YELLOW}Health critical! Auto-using {potion.name}.{Colors.RESET}"); self.use_item(potion)

    def apply_status_effect(self, target, name, duration, potency=0):
        if not target.has_status(name):
            target.status_effects.append({'name': name, 'duration': duration, 'potency': potency})
            self.add_message(f"The {target.name} is afflicted with {name}!")

    def process_actor_turn(self, actor):
        for effect in list(actor.status_effects):
            if effect['name'] == 'Poison':
                actor.take_damage(effect['potency'])
                self.add_message(f"The {actor.name} takes {effect['potency']} damage from poison.")
                self.add_combat_effect(actor.x, actor.y, EFFECT_ATTACK)
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                actor.status_effects.remove(effect)
                self.add_message(f"The {actor.name} is no longer {effect['name'].lower()}.")

    def get_status_effects_string(self, actor):
        if not actor.status_effects: return ""
        effect_colors = {'Stun': Colors.RED, 'Poison': Colors.GREEN}
        effects_str = ", ".join([f"{effect_colors.get(e['name'], Colors.YELLOW)}{e['name']}{Colors.RESET}({e['duration']})" for e in actor.status_effects])
        return f" ({effects_str})"

    def update_fov(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.fov_map[y][x] == 2: self.fov_map[y][x] = 1
        for x_offset in range(-self.player.fov_radius, self.player.fov_radius + 1):
            for y_offset in range(-self.player.fov_radius, self.player.fov_radius + 1):
                if x_offset**2 + y_offset**2 > self.player.fov_radius**2: continue
                target_x, target_y = self.player.x + x_offset, self.player.y + y_offset
                if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT): continue
                for lx, ly in self.get_line(self.player.x, self.player.y, target_x, target_y):
                    self.fov_map[ly][lx] = 2;
                    if self.game_map[ly][lx] == WALL_CHAR: break
    
    def get_line(self, x1, y1, x2, y2):
        points, dx, dy = [], abs(x2 - x1), abs(y2 - y1)
        x, y, sx, sy = x1, y1, 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            points.append((x, y))
            if x == x2 and y == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x += sx
            if e2 < dx: err += dx; y += sy
        return points

    def drink_from_fountain(self):
        self.add_message(f"You drink from the {Colors.BRIGHT_BLUE}fountain...{Colors.RESET}")
        effects = ["heal", "poison", "xp_boost"]
        effect = random.choice(effects)
        if effect == "heal":
            self.add_message("The water is pure and refreshing. You are fully healed!")
            self.player.current_hp = self.player.max_hp
        elif effect == "poison":
            self.add_message("The water tastes foul! You feel sick.")
            self.apply_status_effect(self.player, 'Poison', 5, 1)
        elif effect == "xp_boost":
            self.add_message("The water grants you a moment of clarity! You feel more experienced.")
            self.gain_xp(50)
        self.game_map[self.player.y][self.player.x] = FLOOR_CHAR

    def pray_at_altar(self):
        self.add_message(f"You kneel and pray at the {Colors.BRIGHT_YELLOW}altar...{Colors.RESET}")
        if random.random() < 0.7:
            self.add_message("The gods smile upon you! Your base attack and max HP permanently increase.")
            self.player.base_attack += 1; self.player.max_hp += 5; self.player.current_hp += 5
        else:
            self.add_message("The gods are displeased! You feel weakened.")
            self.player_take_damage(15, "a divine curse") 
            self.player.max_hp = max(10, self.player.max_hp - 5)
        self.game_map[self.player.y][self.player.x] = FLOOR_CHAR

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        clear_screen(); print(f"\n--- PYTHON ROGUE: UNEXPECTED ERROR ---\nError: {e}\n")
        import traceback; traceback.print_exc(); print(f"\n------------------------------------------\n")
    finally:
        print(Colors.RESET)
