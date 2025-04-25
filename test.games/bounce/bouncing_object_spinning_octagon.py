import os
import subprocess
import pygame
import math

def install_requirements():
    try:
        # Check if pip is installed
        subprocess.run(["pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("Pip is not installed. Please install pip to proceed.")
        return

    # Install pygame
    try:
        subprocess.run(["pip", "install", "pygame"], check=True)
        print("Pygame installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install Pygame. Please install it manually.")

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Object in Spinning Octagon")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Octagon properties
octagon_radius = 200
center_x, center_y = WIDTH // 2, HEIGHT // 2
rotation_angle = 0
rotation_speed = 2  # degrees per frame

# Bouncing object properties
ball_radius = 10
ball_x, ball_y = center_x, center_y - octagon_radius + ball_radius
ball_dx, ball_dy = 4, 3

# Function to draw a spinning octagon
def draw_octagon(surface, center, radius, angle):
    points = []
    for i in range(8):
        theta = math.radians(angle + i * 45)
        x = center[0] + radius * math.cos(theta)
        y = center[1] + radius * math.sin(theta)
        points.append((x, y))
    pygame.draw.polygon(surface, WHITE, points, 2)
    return points

# Main game loop
if __name__ == "__main__":
    install_requirements()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill(BLACK)

        # Draw the spinning octagon
        octagon_points = draw_octagon(screen, (center_x, center_y), octagon_radius, rotation_angle)

        # Update rotation angle
        rotation_angle = (rotation_angle + rotation_speed) % 360

        # Move the ball
        ball_x += ball_dx
        ball_y += ball_dy

        # Check for collisions with the screen edges
        if ball_x - ball_radius < 0 or ball_x + ball_radius > WIDTH:
            ball_dx = -ball_dx
        if ball_y - ball_radius < 0 or ball_y + ball_radius > HEIGHT:
            ball_dy = -ball_dy

        # Draw the ball
        pygame.draw.circle(screen, RED, (int(ball_x), int(ball_y)), ball_radius)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    # Quit Pygame
    pygame.quit()