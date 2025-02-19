try:
    import pygame
except ImportError:
    import sys
    print("Pygame not found. Please install it using: pip install pygame")
    sys.exit(1)
import sys

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
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 5
        self.direction = pygame.Vector2(0, 0)
        
    def update(self):
        self.x += self.direction.x * self.speed
        self.y += self.direction.y * self.speed
        # Clamp within screen boundaries
        if self.x < self.radius:
            self.x = self.radius
        if self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
        if self.y < self.radius:
            self.y = self.radius
        if self.y > HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            
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
        
    def update(self):
        self.x += self.direction.x * self.speed
        self.y += self.direction.y * self.speed
        # Bounce off window edges
        if self.x < 0 or self.x > WIDTH - self.width:
            self.direction.x *= -1
        if self.y < 0 or self.y > HEIGHT - self.height:
            self.direction.y *= -1
            
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.width, self.height))

def main():
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
        
        pacman.update()
        ghost.update()
        ghost2.update()
        
        screen.fill(BLACK)
        pacman.draw(screen)
        ghost.draw(screen)
        ghost2.draw(screen)
        
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
