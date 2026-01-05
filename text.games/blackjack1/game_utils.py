
"""
This module provides utility functions for the game, such as screen clearing,
text effects, and animations.
"""


import os
import sys
import time
import re
import random

from card import CARD_BACK, COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN, COLOR_YELLOW, COLOR_MAGENTA, COLOR_CYAN, COLOR_BOLD, COLOR_RESET

# --- Helper Functions (Global Scope) ---
def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.03, color=COLOR_RESET, newline=True):
    """Prints text with a typing effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char); sys.stdout.flush(); time.sleep(delay)
    sys.stdout.write(COLOR_RESET)
    if newline: print()

def strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_visible_width(text):
    """Calculates the visible width of a string after stripping ANSI codes."""
    return len(strip_ansi_codes(text))

def center_text(text, width):
    """Centers text within a given width, accounting for ANSI codes."""
    visible_width = get_visible_width(text)
    padding = (width - visible_width) // 2
    if padding < 0: padding = 0
    return " " * padding + text

def shuffle_animation(duration=1.5):
    """Displays a visual shuffling animation."""
    clear_screen(); print(f"{COLOR_YELLOW}Shuffling Deck...{COLOR_RESET}")
    symbols = ['♠', '♥', '♦', '♣', CARD_BACK, '?']; colors = [COLOR_RED, COLOR_BLACK, COLOR_DIM, COLOR_BLUE, COLOR_GREEN]
    width = 40; lines = 5; end_time = time.time() + duration
    while time.time() < end_time:
        output_lines = []
        for _ in range(lines):
            line = "".join(f"{random.choice(colors)}{random.choice(symbols)}{COLOR_RESET}" if random.random() < 0.3 else " " for _ in range(width))
            output_lines.append(line)
        sys.stdout.write(f"\033[{lines}A")
        for line in output_lines: sys.stdout.write(f"\r{line.ljust(width)}\n")
        sys.stdout.flush(); time.sleep(0.05)
    clear_screen(); print(f"{COLOR_GREEN}Deck Shuffled!{COLOR_RESET}"); time.sleep(0.5)

