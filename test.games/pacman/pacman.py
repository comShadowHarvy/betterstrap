try:
    import pygame
except ImportError:
    import sys
    print("Pygame not found. Please install it using: pip install pygame")
    sys.exit(1)
import sys
from collections import deque

# Initialize pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 560, 620
FPS = 60

# Colors
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pacman")
clock = pygame.time.Clock()

class Pacman:
    def __init__(self, x, y):
        # Reduced radius from 15 to 10 for better fit in the maze passages
        self.x = x
        self.y = y
        self.radius = 10
        self.speed = 5
        self.direction = pygame.Vector2(0, 0)
        
    def update(self, walls):
        # Move horizontally and check collisions
        old_x = self.x
        self.x += self.direction.x * self.speed
        pac_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        for wall in walls:
            if pac_rect.colliderect(wall):
                self.x = old_x
                break
        # Move vertically and check collisions
        old_y = self.y
        self.y += self.direction.y * self.speed
        pac_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        for wall in walls:
            if pac_rect.colliderect(wall):
                self.y = old_y
                break
        # Clamp within screen boundaries
        if self.x < self.radius: self.x = self.radius
        if self.x > WIDTH - self.radius: self.x = WIDTH - self.radius
        if self.y < self.radius: self.y = self.radius
        if self.y > HEIGHT - self.radius: self.y = HEIGHT - self.radius
            
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)

class Ghost:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 3
        self.color = color
        self.direction = pygame.Vector2(1, 0)
        
    def update(self, target, maze_layout, tile_size):
        # Use grid-based pathfinding
        ghost_cell = get_grid_pos(self.x, self.y, tile_size)
        target_cell = get_grid_pos(target.x, target.y, tile_size)
        path = bfs(maze_layout, ghost_cell, target_cell)
        if len(path) > 1:
            next_cell = path[1]
            # Calculate the center of the target cell
            target_x = next_cell[0] * tile_size + tile_size / 2
            target_y = next_cell[1] * tile_size + tile_size / 2
            direction = pygame.Vector2(target_x - self.x, target_y - self.y)
            if direction.length() != 0:
                direction = direction.normalize()
            self.x += direction.x * self.speed
            self.y += direction.y * self.speed
        # Note: Removing old wall collision check – maze walls are implicit in the grid
            
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.width, self.height))

# New helper functions for maze and pathfinding
def build_walls(maze_layout, tile_size):
    walls = []
    for row_idx, row in enumerate(maze_layout):
        for col_idx, char in enumerate(row):
            if char == "#":
                walls.append(pygame.Rect(col_idx * tile_size,
                                          row_idx * tile_size,
                                          tile_size, tile_size))
    return walls

def get_grid_pos(x, y, tile_size):
    return (int(x // tile_size), int(y // tile_size))

def bfs(maze, start, goal):
    rows = len(maze)
    cols = len(maze[0])
    queue = deque([start])
    came_from = {start: None}
    moves = [(0,1),(0,-1),(1,0),(-1,0)]
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for dx, dy in moves:
            neighbor = (current[0] + dx, current[1] + dy)
            if (0 <= neighbor[0] < cols and 0 <= neighbor[1] < rows and
                    maze[neighbor[1]][neighbor[0]] == "." and neighbor not in came_from):
                queue.append(neighbor)
                came_from[neighbor] = current
    # Reconstruct path
    if goal not in came_from:
        return []
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path

def main():
    # New maze layout covering the entire play area (20 cols x 22 rows)
    maze_layout = [
        "####################",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.####.##.##.####..#",
        "#..................#",
        "#.################.#",
        "####################"
    ]
    tile_size = 28  # 20 columns * 28 = 560, 22 rows * 28 = 616 (close to 620)
    
    # Build walls for drawing
    walls = build_walls(maze_layout, tile_size)
    
    pacman = Pacman(WIDTH / 2, HEIGHT / 2)
    ghost = Ghost(50, 50, RED)
    ghost2 = Ghost(WIDTH - 80, HEIGHT - 80, BLUE)
    
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    pacman.direction = pygame.Vector2(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    pacman.direction = pygame.Vector2(1, 0)
                elif event.key == pygame.K_UP:
                    pacman.direction = pygame.Vector2(0, -1)
                elif event.key == pygame.K_DOWN:
                    pacman.direction = pygame.Vector2(0, 1)
        
        pacman.update(walls)  # Using wall rects from build_walls
        ghost.update(pacman, maze_layout, tile_size)
        ghost2.update(pacman, maze_layout, tile_size)

        # Check if any ghost touches pacman (using bounding boxes)
        pac_rect = pygame.Rect(pacman.x - pacman.radius, pacman.y - pacman.radius, pacman.radius*2, pacman.radius*2)
        ghost_rect = pygame.Rect(ghost.x, ghost.y, ghost.width, ghost.height)
        ghost2_rect = pygame.Rect(ghost2.x, ghost2.y, ghost2.width, ghost2.height)
        if pac_rect.colliderect(ghost_rect) or pac_rect.colliderect(ghost2_rect):
            print("Game Over!")
            running = False
        
        screen.fill(BLACK)

        # Draw maze walls
        for wall in walls:
            pygame.draw.rect(screen, (100,100,100), wall)

        pacman.draw(screen)
        ghost.draw(screen)
        ghost2.draw(screen)
        
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
