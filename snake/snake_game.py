import pygame, sys, random, time

# Game constants
TILE_SIZE = 20
GRID_WIDTH = 40    # 40 columns = 800 px width
GRID_HEIGHT = 30   # 30 rows = 600 px height
WIDTH = GRID_WIDTH * TILE_SIZE
HEIGHT = GRID_HEIGHT * TILE_SIZE
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255,255,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)
GRAY = (40,40,40)

# Direction vectors mapping for human control
DIRECTIONS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0)
}

class Snake:
    def __init__(self, body, direction, color, is_human=False):
        self.body = body[:]         # list of (x, y); head is first element
        self.direction = direction  # (dx, dy)
        self.color = color
        self.is_human = is_human
        self.alive = True
        self.score = 0

    def next_head(self):
        head = self.body[0]
        dx, dy = self.direction
        return (head[0] + dx, head[1] + dy)
    
    def move(self, food):
        new_head = self.next_head()
        # Check collisions with board borders
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.alive = False
            return
        # Check self-collision
        if new_head in self.body:
            self.alive = False
            return
        
        self.body.insert(0, new_head)
        # If food is eaten, keep tail; otherwise remove tail for movement
        if new_head == food:
            self.score += 1
        else:
            self.body.pop()
    
    def draw(self, surface):
        for part in self.body:
            rect = pygame.Rect(part[0]*TILE_SIZE, part[1]*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, self.color, rect)

def draw_grid(surface):
    for x in range(0, WIDTH, TILE_SIZE):
        pygame.draw.line(surface, GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, TILE_SIZE):
        pygame.draw.line(surface, GRAY, (0, y), (WIDTH, y))

def place_food(snakes):
    positions = set()
    for s in snakes:
        positions.update(s.body)
    while True:
        pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
        if pos not in positions:
            return pos

def ai_decision(snake, food):
    # Simple AI: move in the direction of the food
    head = snake.body[0]
    dx = food[0] - head[0]
    dy = food[1] - head[1]
    if abs(dx) > abs(dy):
        new_dir = (1, 0) if dx > 0 else (-1, 0)
    else:
        new_dir = (0, 1) if dy > 0 else (0, -1)
    # Prevent reverse if length > 1
    if len(snake.body) > 1:
        rev = (-snake.direction[0], -snake.direction[1])
        if new_dir == rev:
            new_dir = snake.direction
    snake.direction = new_dir

def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.setCaption("Ultimate Snake Showdown")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    
    # Create a human snake and an AI snake
    human_snake = Snake(body=[(GRID_WIDTH//2, GRID_HEIGHT//2)], 
                        direction=(1, 0), color=GREEN, is_human=True)
    ai_snake = Snake(body=[(5,5)], direction=(1, 0), color=RED, is_human=False)
    snakes = [human_snake, ai_snake]
    food = place_food(snakes)
    
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if human_snake.is_human and event.key in DIRECTIONS:
                    new_dir = DIRECTIONS[event.key]
                    if len(human_snake.body) > 1 and new_dir == (-human_snake.direction[0], -human_snake.direction[1]):
                        continue
                    human_snake.direction = new_dir
        
        # AI snake decision making
        if ai_snake.alive:
            ai_decision(ai_snake, food)
        
        for s in snakes:
            if s.alive:
                s.move(food)
                if s.body[0] == food:
                    food = place_food(snakes)
        
        # Check collisions between snakes (head against other's body)
        if human_snake.body[0] in ai_snake.body:
            human_snake.alive = False
        if ai_snake.body[0] in human_snake.body:
            ai_snake.alive = False
        
        if not any(s.alive for s in snakes):
            running = False
        
        screen.fill(BLACK)
        draw_grid(screen)
        for s in snakes:
            s.draw(screen)
        food_rect = pygame.Rect(food[0]*TILE_SIZE, food[1]*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.ellipse(screen, YELLOW, food_rect)
        score_text = font.render(f"Human: {human_snake.score}  AI: {ai_snake.score}", True, WHITE)
        screen.blit(score_text, (10,10))
        pygame.display.flip()
    
    # Game Over screen
    screen.fill(BLACK)
    over_text = font.render("Game Over!", True, WHITE)
    screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 50))
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()

if __name__ == "__main__":
    game_loop()
