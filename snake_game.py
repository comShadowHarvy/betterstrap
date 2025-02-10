import curses, time, random

# Board dimensions will be set in main() based on terminal size
WIDTH, HEIGHT = None, None  # Changed to None initially

# Direction vectors
DIRECTIONS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}
ALL_DIRS = list(DIRECTIONS.values())

# Add a global list for temporary fruits and adjust place_food():
temp_fruits = []  # global list storing tuples (x, y)

def place_food(snakes):
    positions = set()
    for s in snakes:
        positions.update(s.body)
    while True:
        pos = (random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2))
        if pos not in positions:
            return pos

class Snake:
    def __init__(self, body, direction, id):
        self.body = body  # list of (x, y), head is first element
        self.direction = direction  # (dx, dy)
        self.id = id  # 1 or 2
        self.alive = True
        self.strategy = random.choice([1,2,4,5,6,7,8])  # randomly choose among 7 candidate styles
        self.score = 0   # new: count of fruits eaten
        self.body_set = set(body)  # New: maintain a set for faster lookups
        self.prev_direction = direction  # Add tracking of previous direction
        self.target_food = None  # Add food target tracking
        self.current_target = None  # Track current food target (regular or dropped)

    def next_head(self, new_dir=None):
        if new_dir is None:
            new_dir = self.direction
        head = self.body[0]
        return (head[0] + new_dir[0], head[1] + new_dir[1])

    def free_space(self, pos, other_snake_body, food):  # modified signature
        obstacles = self.body_set | other_snake_body
        visited = set()
        to_visit = {pos}  # Using set for faster membership tests
        count = 0
        found_food = False
        
        while to_visit:
            p = to_visit.pop()
            if p in visited or p in obstacles:
                continue
            visited.add(p)
            x, y = p
            if x < 1 or x > WIDTH-2 or y < 1 or y > HEIGHT-2:
                continue
            
            if p == food or p in temp_fruits:
                found_food = True
                if count > 15:  # Early exit if we found food and decent space
                    return count + 75
            count += 1
            
            # Add all valid neighbors at once
            x, y = p
            neighbors = {(x+1,y), (x-1,y), (x,y+1), (x,y-1)} - visited - obstacles
            to_visit.update(neighbors)
            
        return count + (50 if found_food else 0)

    def quick_check_deadend(self, pos, other_snake_body):
        """Check if a position has at least 2 escape routes to avoid obvious traps"""
        escape_routes = 0
        for dx, dy in ALL_DIRS:
            next_pos = (pos[0] + dx, pos[1] + dy)
            if self._is_safe(next_pos, other_snake_body):
                escape_routes += 1
                if escape_routes >= 2:  # Only need 2 escape routes to not be in immediate danger
                    return False
        return True  # Less than 2 escape routes = potential deadend

    def choose_direction(self, food, other_snake_body):
        other_snake_set = set(other_snake_body)
        candidates = []
        head = self.body[0]
        
        # Find closest food source (including dropped fruits)
        head_pos = self.body[0]
        closest_food = food
        min_dist = abs(head_pos[0] - food[0]) + abs(head_pos[1] - food[1])
        
        # Check dropped fruits
        for f in temp_fruits:
            dist = abs(head_pos[0] - f[0]) + abs(head_pos[1] - f[1])
            if dist < min_dist:
                min_dist = dist
                closest_food = f
        
        # Update target if needed
        if self.current_target != closest_food:
            self.current_target = closest_food
        
        # Calculate direction to current target
        food_dx = self.current_target[0] - head[0]
        food_dy = self.current_target[1] - head[1]
        
        for dx, dy in ALL_DIRS:
            if len(self.body) > 1 and (dx, dy) == (-self.direction[0], -self.direction[1]):
                continue
                
            new_head = (head[0] + dx, head[1] + dy)
            if not self._is_safe(new_head, other_snake_set):
                continue
                
            # Calculate distance to current target
            manhattan_food = abs(new_head[0] - self.current_target[0]) + abs(new_head[1] - self.current_target[1])
            space = self.free_space(new_head, other_snake_set, self.current_target)
            
            # Base score with food focus
            score = -15.0 * manhattan_food + 0.2 * space + 100
            
            # Direction consistency bonus
            if (dx, dy) == self.direction:
                score += 50
            elif (dx, dy) == self.prev_direction:
                score += 25
            
            # Directional alignment bonus
            if (food_dx * dx > 0) or (food_dy * dy > 0):
                score += 75
            
            # Close range behavior (same for both regular and dropped food)
            if manhattan_food <= 2:
                if (abs(food_dx) == 1 and dy == 0) or (abs(food_dy) == 1 and dx == 0):
                    score += 500
            elif manhattan_food < 5:
                score += 150
            elif manhattan_food < 10:
                score += 75
            
            # Survival checks
            if space < 3:
                score -= 1000
            elif space < 6:
                score -= 200
            
            candidates.append(((dx, dy), score))
        
        if candidates:
            self.prev_direction = self.direction
            self.direction = max(candidates, key=lambda x: x[1])[0]

    def _is_safe(self, pos, other_snake_set):
        x, y = pos
        # Check wall
        if x < 1 or x > WIDTH-2 or y < 1 or y > HEIGHT-2:
            return False
        # Check self collision (ignoring tail as it will move)
        if pos in self.body[:-1]:
            return False
        # Check collision with part of other snake
        if pos in other_snake_set:
            return False
        return True

    def move(self, food, other_snake_body):
        self.choose_direction(food, other_snake_body)
        new_head = self.next_head()
        self.body.insert(0, new_head)
        self.body_set.add(new_head)  # Update set
        # Check if food is eaten. Caller will handle food collision.
        return new_head

    def remove_tail(self):
        tail = self.body.pop()
        self.body_set.remove(tail)  # Update set


def safe_addch(stdscr, y, x, ch, attr=0):
    try:
        stdscr.addch(y, x, ch, attr)
    except curses.error:
        pass

def draw_board(stdscr, snake1, snake2, snake3, snake4, food):  # updated signature
    stdscr.clear()
    # Header displays candidate style for each snake in the game
    def style_name(s):
        return {1:"FreeSpace-MH", 2:"Manhattan", 4:"Weighted", 5:"Aggressive", 6:"Cautious", 7:"Distance2x", 8:"Balanced"}[s]
    header = ("S1(Green): {} | S2(Blue): {} | S3(Yellow): {} | S4(Magenta): {}"
              .format(style_name(snake1.strategy), style_name(snake2.strategy),
                      style_name(snake3.strategy), style_name(snake4.strategy)))
    stdscr.addstr(0, max(0, WIDTH//2 - len(header)//2), header, curses.A_BOLD)
    # Draw border starting at row offset=1
    offset = 1
    top_border = offset
    bottom_border = HEIGHT
    for x in range(WIDTH):
        safe_addch(stdscr, top_border, x, '#')
        safe_addch(stdscr, bottom_border, x, '#')
    for y in range(top_border, bottom_border+1):
        safe_addch(stdscr, y, 0, '#')
        safe_addch(stdscr, y, WIDTH-1, '#')
    # Draw food and snake1, snake2 (snake3, snake4 are drawn in main loop)
    safe_addch(stdscr, food[1] + offset, food[0], '*', curses.color_pair(3))
    for s, c in [(snake1, 1), (snake2, 2)]:
        for i, cell in enumerate(s.body):
            char = 'H' if i == 0 else 'o'
            safe_addch(stdscr, cell[1] + offset, cell[0], char, curses.color_pair(c))
    # New: draw temporary fruits dropped by dead snakes using char ':'
    for pos in temp_fruits:
        safe_addch(stdscr, pos[1] + 1, pos[0], ':', curses.color_pair(6))
    stdscr.refresh()

# New ranking_screen that shows ranking and then offers Restart/Exit:
def ranking_screen(stdscr, ranking):
    stdscr.clear()
    stdscr.addstr(2, WIDTH//2 - 4, "Ranking", curses.A_BOLD)
    for idx, s in enumerate(ranking):
        rank = idx + 1
        line = "Rank {}: Snake {} (Style: {})".format(rank, s.id,
                    {1:"FreeSpace-MH", 2:"Manhattan", 4:"Weighted", 5:"Aggressive", 6:"Cautious", 7:"Distance2x", 8:"Balanced"}[s.strategy])
        stdscr.addstr(4 + idx, WIDTH//2 - len(line)//2, line)
    options = ["Restart", "Exit"]
    selected = 0
    stdscr.keypad(True)
    while True:
        for idx, option in enumerate(options):
            attr = curses.A_REVERSE if idx == selected else 0
            stdscr.addstr(10 + idx, WIDTH//2 - len(option)//2, option, attr)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(options)
        elif key in [curses.KEY_ENTER, ord("\n"), ord("\r")]:
            return options[selected]

def end_game_screen(stdscr, snake1, snake2):
    stdscr.clear()
    if snake1.alive and not snake2.alive:
        result = "Green wins!"
    elif snake2.alive and not snake1.alive:
        result = "Blue wins!"
    else:
        result = "Draw!"
    message = "Game Over - " + result
    stdscr.addstr(HEIGHT//2, WIDTH//2 - len(message)//2, message, curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def game_over_menu(stdscr, snake1, snake2):
    # Determine game result
    if snake1.alive and not snake2.alive:
        result = "Green wins!"
    elif snake2.alive and not snake1.alive:
        result = "Blue wins!"
    else:
        result = "Draw!"
    message = "Game Over - " + result
    options = ["Restart", "Exit"]
    selected = 0
    stdscr.keypad(True)
    while True:
        stdscr.clear()
        stdscr.addstr(HEIGHT//2-2, WIDTH//2 - len(message)//2, message, curses.A_BOLD)
        for idx, option in enumerate(options):
            if idx == selected:
                stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(HEIGHT//2 + idx, WIDTH//2 - len(option)//2, option)
            if idx == selected:
                stdscr.attroff(curses.A_REVERSE)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(options)
        elif key in [curses.KEY_ENTER, ord("\n"), ord("\r")]:
            return options[selected]

def drop_fruits(snake):
    # Drop fruits equal to snake.score using random positions from its body
    fruits = []
    for _ in range(snake.score):
        pos = random.choice(snake.body) if snake.body else (0,0)
        fruits.append(pos)
    return fruits

def drop_body(snake):
    # Return every segment of the snake's body as fruit positions.
    return snake.body

def main(stdscr):
    global WIDTH, HEIGHT
    curses.curs_set(0)
    stdscr.nodelay(1)
    
    # Get terminal size and set board dimensions once at startup
    term_height, term_width = stdscr.getmaxyx()
    HEIGHT = term_height - 2  # Leave room for header
    WIDTH = term_width - 1    # Leave room for right border
    
    # Ensure minimum size
    if HEIGHT < 15 or WIDTH < 40:
        stdscr.addstr(0, 0, "Terminal too small! Need at least 40x15")
        stdscr.refresh()
        stdscr.getch()
        return

    curses.start_color()
    curses.use_default_colors()
    
    # Initialize colors
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake1
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)     # Snake2
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)      # food remains
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # Snake3
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Snake4
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)    # Temporary fruits
    curses.init_pair(7, curses.COLOR_CYAN, curses.COLOR_BLACK)     # Snake5
    curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLACK)      # Snake6
    curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_BLACK)    # Snake7
    curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Snake8
    curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Snake9
    curses.init_pair(12, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Snake10
    
    while True:  # Outer game loop to support restart
        death_ctr = 1
        global temp_fruits
        temp_fruits = []  # clear dropped fruits at start
        # New: assign distinct strategies for four snakes
        unique_strats = random.sample([1,2,4,5,6,7,8], 4)
        # Initialize four snakes with distinct starting positions, directions, and death_order attribute
        snake1 = Snake(body=[(5,5), (4,5), (3,5)], direction=DIRECTIONS['RIGHT'], id=1)
        snake1.strategy = unique_strats[0]
        snake2 = Snake(body=[(WIDTH-6,5), (WIDTH-5,5), (WIDTH-4,5)], direction=DIRECTIONS['LEFT'], id=2)
        snake2.strategy = unique_strats[1]
        snake3 = Snake(body=[(WIDTH-6,HEIGHT-6), (WIDTH-5,HEIGHT-6), (WIDTH-4,HEIGHT-6)], direction=DIRECTIONS['LEFT'], id=3)
        snake3.strategy = unique_strats[2]
        snake4 = Snake(body=[(5,HEIGHT-6), (4,HEIGHT-6), (3,HEIGHT-6)], direction=DIRECTIONS['RIGHT'], id=4)
        snake4.strategy = unique_strats[3]
        for s in [snake1, snake2, snake3, snake4]:
            s.death_order = None
        snakes = [snake1, snake2, snake3, snake4]
        food = place_food(snakes)  # use updated place_food
        
        stdscr.nodelay(1)
        # Continue until all snakes are dead
        while any(s.alive for s in snakes):
            for s in snakes:
                if not s.alive:
                    continue
                # Gather bodies of all other snakes
                others = []
                for other in snakes:
                    if other is not s:
                        others.extend(other.body)
                new_head = s.move(food, others)
                # Check collision for snake s:
                if (new_head[0] < 1 or new_head[0] > WIDTH-2 or 
                    new_head[1] < 1 or new_head[1] > HEIGHT-2 or 
                    new_head in s.body[1:] or new_head in others):
                    s.alive = False
                    if s.death_order is None:
                        s.death_order = death_ctr
                        death_ctr += 1
                        # Replace entire snake body with fruits and clear the body:
                        temp_fruits.extend(drop_body(s))
                        s.body = []  # clear the snake's body
                else:
                    # Modified: allow snake to eat normal food or a dropped fruit
                    if new_head == food:
                        s.score += 1  # increment fruits eaten
                        food = place_food(snakes)
                    elif new_head in temp_fruits:
                        s.score += 1  # eaten dropped fruit; snake grows
                        temp_fruits.remove(new_head)
                    else:
                        s.remove_tail()
            draw_board(stdscr, snake1, snake2, snake3, snake4, food)  # updated call
            # Also draw snake3 and snake4
            for s in snakes[2:]:
                if not s.alive:
                    continue
                color = 4 if s.id == 3 else 5
                for i, cell in enumerate(s.body):
                    char = 'H' if i==0 else 'X'
                    safe_addch(stdscr, cell[1] + 1, cell[0], char, curses.color_pair(color))
            stdscr.refresh()
            time.sleep(0.1)
        
        stdscr.nodelay(0)
        # Once all snakes are dead, compute ranking; the snake that dies last is best.
        ranking = sorted(snakes, key=lambda s: s.death_order, reverse=True)
        choice = ranking_screen(stdscr, ranking)
        if choice == "Restart":
            continue  # Restart the outer loop
        else:
            break

if __name__ == '__main__':
    curses.wrapper(main)
