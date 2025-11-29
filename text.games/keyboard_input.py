"""
Keyboard input utilities for single-key input without pressing Enter.
Works on Linux/Unix and Windows systems.
"""

import sys
import os

# Platform-specific imports
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Linux/Mac
    import termios
    import tty


def get_single_key():
    """
    Get a single keypress without requiring Enter.
    Returns the key as a string (lowercase for letters).
    """
    if os.name == 'nt':  # Windows
        key = msvcrt.getch()
        if isinstance(key, bytes):
            try:
                key = key.decode('utf-8').lower()
            except:
                key = ''
        return key
    else:  # Unix/Linux/Mac
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            return key.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_key_or_string(prompt, allowed_keys=None, allow_number_input=False):
    """
    Advanced input that accepts either:
    - Single keypress (for quick actions)
    - Full string input ending with Enter (for numbers/text)
    
    Args:
        prompt: The prompt to display
        allowed_keys: List of single keys that trigger immediate action (e.g., ['h', 's', 'd'])
        allow_number_input: If True, allows typing multi-digit numbers
    
    Returns:
        String input (either single key or full entered text)
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    if allowed_keys is None:
        allowed_keys = []
    
    # Convert to lowercase
    allowed_keys = [k.lower() for k in allowed_keys]
    
    input_buffer = ""
    
    while True:
        key = get_single_key()
        
        # Handle Enter key
        if key in ['\r', '\n']:
            if input_buffer:
                print()  # Newline after input
                return input_buffer
            else:
                # Empty enter - just return empty string
                print()
                return ""
        
        # Handle backspace
        elif key in ['\x7f', '\x08']:  # Backspace/Delete
            if input_buffer:
                input_buffer = input_buffer[:-1]
                # Clear line and reprint
                sys.stdout.write('\r' + ' ' * (len(prompt) + len(input_buffer) + 5))
                sys.stdout.write('\r' + prompt + input_buffer)
                sys.stdout.flush()
        
        # Handle Ctrl+C
        elif key == '\x03':
            raise KeyboardInterrupt
        
        # Single-key shortcut
        elif key in allowed_keys and not input_buffer:
            print(key)  # Echo the key
            return key
        
        # Building multi-character input (numbers, etc.)
        elif key.isprintable():
            input_buffer += key
            sys.stdout.write(key)
            sys.stdout.flush()
            
            # If we're not allowing number input and we got a non-allowed key, continue
            # This allows typing but won't trigger instant action
