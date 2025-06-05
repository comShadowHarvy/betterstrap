import os
import random
import math # For FOV distance calculation

# --- Game Settings ---
MAP_WIDTH = 50  # Wider map
MAP_HEIGHT = 25 # Taller map
PLAYER_CHAR = "@"
FLOOR_CHAR = "."
WALL_CHAR = "#"
GOAL_CHAR = "G"

# Room generation settings
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 20

# FOV settings
FOV_RADIUS = 8
UNSEEN_CHAR = ' ' # What to show for tiles not yet explored/visible

# --- Player ---
player_x = 0
player_y = 0

# --- Goal ---
goal_x = 0
goal_y = 0

# --- Game State ---
turns = 0
game_message = "Explore the dungeon. Find the Goal (G)!"

# --- Map ---
game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
# FOV map: 0 = unseen, 1 = explored (not visible), 2 = currently visible
fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]


# --- Room Class (same as before) ---
class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

# --- Map Generation (similar to before, minor adjustments for player/goal placement) ---
def create_room(room):
    global game_map
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                game_map[y][x] = FLOOR_CHAR

def create_h_tunnel(x1, x2, y):
    global game_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            game_map[y][x] = FLOOR_CHAR

def create_v_tunnel(y1, y2, x):
    global game_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            game_map[y][x] = FLOOR_CHAR

def generate_map():
    global game_map, player_x, player_y, goal_x, goal_y, fov_map
    game_map = [[WALL_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    fov_map = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)] # Reset FOV map
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, MAP_WIDTH - w - 2) # Ensure rooms aren't at the very edge
        y = random.randint(1, MAP_HEIGHT - h - 2)

        new_room = Rect(x, y, w, h)
        failed = False
        for other_room in rooms:
            if new_room.intersects(other_room):
                failed = True
                break
        
        if not failed:
            create_room(new_room)
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                player_x = new_x
                player_y = new_y
            else:
                (prev_x, prev_y) = rooms[num_rooms - 1].center()
                if random.randint(0, 1) == 1:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            
            rooms.append(new_room)
            num_rooms += 1

    if rooms:
        # Ensure player is on a floor tile (center might rarely be a wall if room is 1 wide/tall)
        if game_map[player_y][player_x] == WALL_CHAR:
            for r_idx, room_obj in enumerate(rooms): # find first room with floor
                px, py = room_obj.center()
                if game_map[py][px] == FLOOR_CHAR:
                    player_x, player_y = px, py
                    break
        
        # Place goal in the center of the last room, ensuring it's on a floor tile
        last_room = rooms[-1]
        goal_x, goal_y = last_room.center()
        if game_map[goal_y][goal_x] == WALL_CHAR: # If center is wall, find floor in room
            found_goal_spot = False
            for gx_offset in range(last_room.x1 + 1, last_room.x2):
                for gy_offset in range(last_room.y1 + 1, last_room.y2):
                    if game_map[gy_offset][gx_offset] == FLOOR_CHAR:
                        goal_x, goal_y = gx_offset, gy_offset
                        found_goal_spot = True
                        break
                if found_goal_spot: break
        game_map[goal_y][goal_x] = GOAL_CHAR

    else: # Fallback
        game_map = [[FLOOR_CHAR for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        player_x, player_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        goal_x, goal_y = player_x + 2, player_y
        if 0 <= goal_x < MAP_WIDTH and 0 <= goal_y < MAP_HEIGHT:
             game_map[goal_y][goal_x] = GOAL_CHAR
        else:
            goal_x, goal_y = player_x, player_y
    
    update_fov() # Initial FOV calculation

# --- FOV Calculation ---
def get_line(x1, y1, x2, y2):
    """Bresenham's Line Algorithm: returns a list of (x,y) tuples from (x1,y1) to (x2,y2)"""
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = -1 if x1 > x2 else 1
    sy = -1 if y1 > y2 else 1

    if dx > dy:
        err = dx / 2.0
        while x != x2:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y2:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x, y)) # Ensure the last point is added
    return points

def update_fov():
    global fov_map
    # Set all previously visible tiles to "explored"
    for y_ in range(MAP_HEIGHT):
        for x_ in range(MAP_WIDTH):
            if fov_map[y_][x_] == 2: # Was visible
                fov_map[y_][x_] = 1   # Now explored

    # Cast rays to all tiles within FOV_RADIUS
    # Iterate through a square area and then check distance for a circular FOV
    for x_offset in range(-FOV_RADIUS, FOV_RADIUS + 1):
        for y_offset in range(-FOV_RADIUS, FOV_RADIUS + 1):
            # Optional: circular FOV
            if x_offset * x_offset + y_offset * y_offset > FOV_RADIUS * FOV_RADIUS:
                continue

            target_x = player_x + x_offset
            target_y = player_y + y_offset

            # Ensure target is within map bounds
            if not (0 <= target_x < MAP_WIDTH and 0 <= target_y < MAP_HEIGHT):
                continue
            
            line_to_target = get_line(player_x, player_y, target_x, target_y)
            
            for i, (lx, ly) in enumerate(line_to_target):
                if not (0 <= lx < MAP_WIDTH and 0 <= ly < MAP_HEIGHT): # Should not happen if target is in bounds and line algo is good
                    break 
                
                fov_map[ly][lx] = 2 # Mark this tile as visible
                if game_map[ly][lx] == WALL_CHAR:
                    break # Light stops at walls
                    
# --- Drawing ---
def clear_screen():
    if os.name == 'nt': _ = os.system('cls')
    else: _ = os.system('clear')

def draw_game():
    clear_screen()
    display_map_chars = []

    for y_disp in range(MAP_HEIGHT):
        row_chars = []
        for x_disp in range(MAP_WIDTH):
            if fov_map[y_disp][x_disp] == 2: # Currently visible
                if y_disp == player_y and x_disp == player_x:
                    row_chars.append(PLAYER_CHAR)
                else:
                    row_chars.append(game_map[y_disp][x_disp])
            elif fov_map[y_disp][x_disp] == 1: # Explored but not visible
                row_chars.append(game_map[y_disp][x_disp]) # Could make this dimmer later
            else: # Unseen
                row_chars.append(UNSEEN_CHAR)
        display_map_chars.append("".join(row_chars))
    
    for row_str in display_map_chars:
        print(row_str)
    
    print(f"\nTurns: {turns}")
    # print(f"Player: ({player_x},{player_y}) Goal: ({goal_x},{goal_y})") # Optional: for debugging
    print(game_message)
    print("Move with W, A, S, D. Press Q to quit.")

# --- Game Logic ---
def handle_input():
    global player_x, player_y, turns, game_message
    
    action = input("> ").lower()
    
    # Don't increment turns for invalid commands or quit
    moved = False
    new_x, new_y = player_x, player_y

    if action == 'w': new_y -= 1; moved = True
    elif action == 's': new_y += 1; moved = True
    elif action == 'a': new_x -= 1; moved = True
    elif action == 'd': new_x += 1; moved = True
    elif action == 'q': return "quit"
    else:
        game_message = "Invalid command. Use W, A, S, D or Q."
        return "playing" # No turn taken for invalid command

    turns += 1 # Increment turns only if a move key was pressed
    game_message = "" 

    if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT):
        if game_map[new_y][new_x] != WALL_CHAR:
            player_x, player_y = new_x, new_y
            update_fov() # Update FOV after moving
            if player_x == goal_x and player_y == goal_y:
                return "won"
        else:
            game_message = "Ouch! You bumped into a wall."
    else:
        game_message = "You can't move outside the map."
        
    return "playing"

# --- Main Game Loop ---
def game_loop():
    global game_message
    game_state = "playing"
    generate_map() # This now calls update_fov() internally for the first view

    while game_state == "playing":
        draw_game()
        game_state = handle_input()

    draw_game() 
    if game_state == "won":
        print(f"\nCongratulations! You reached the goal ('{GOAL_CHAR}') in {turns} turns!")
    elif game_state == "quit":
        print(f"\nYou quit after {turns} turns. Thanks for playing!")

if __name__ == "__main__":
    game_loop()

