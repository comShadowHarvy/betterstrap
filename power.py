#!/usr/bin/env python3
import subprocess
import re
import random
import shlex
import time
import os
import datetime
import sys

# --- Configuration ---
LINE_DELAY = 1.5  # Seconds to delay GLaDOS's lines
ATTEMPTED_FIXED_DBM = 20  # dBm - The fixed power we will ATTEMPT to set
ATTEMPTED_FIXED_MBM = ATTEMPTED_FIXED_DBM * 100 # mBm (1 dBm = 100 mBm)
WAIT_DURATION_SECONDS = 720 # How long to wait after setting fixed power (12 minutes)
TARGET_REGULATORY_DOMAIN = "GB"  # Great Britain regulatory domain

# GLaDOS-esque phrases
glados_comments_power = [
    "Ah, so you want to 'enhance' your wireless output. How... predictable.",
    f"Attempting to set a 'modest' fixed power of {ATTEMPTED_FIXED_DBM} dBm. Don't get too excited.",
    "Let's see if your hardware enjoys this 'slight' nudge. Or if it complains. Loudly.",
    "Remember, this is an 'attempt'. Your system might just ignore me entirely.",
    "Power modulation sequence initiated. For science. And my amusement.",
    "If things start smelling like burnt electronics, that's just the 'scent of progress'.",
]

glados_comments_regulatory = [
    "Oh, changing regulatory domains now? How very... rebellious of you.",
    "Setting regulatory domain. I hope you know what you're doing. For legal reasons.",
    "Regulatory boundaries are just suggestions, right? Right?",
    "Domain change initiated. Don't blame me if mysterious vans appear outside.",
    "Adjusting regulatory parameters. The airwaves will never be the same.",
]

glados_comments_restore = [
    "Back to boring normalcy, I see. How... safe of you.",
    "Returning to automatic settings. Where's your sense of adventure?",
    "Reverting to defaults. Because apparently 'fun' has limits.",
    "Normalizing all parameters. The universe breathes a sigh of relief.",
    "Everything back to 'auto'. How refreshingly mundane.",
]

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def glados_speak(text, delay=LINE_DELAY):
    """Prints text with a GLaDOS prefix and a delay."""
    print(f"GLaDOS: {text}")
    if delay > 0:
        time.sleep(delay)

def show_title_screen():
    """Displays the GLaDOS title screen."""
    clear_screen()
    print("""
    ██████╗ ██╗      █████╗ ██████╗  ██████╗ ███████╗
    ██╔════╝ ██║     ██╔══██╗██╔══██╗██╔═══██╗██╔════╝
    ██║  ███╗██║     ███████║██║  ██║██║   ██║███████╗
    ██║   ██║██║     ██╔══██║██║  ██║██║   ██║╚════██║
    ╚██████╔╝███████╗██║  ██║██████╔╝╚██████╔╝███████║
     ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝
    
    ═══════════════════════════════════════════════════════
           Wi-Fi Power & Regulatory Control System
                    Version 2.0 - Portal Labs
    ═══════════════════════════════════════════════════════
    """)
    
    glados_speak("Welcome back, test subject. Ready for more 'science'?", delay=2)
    glados_speak("Today's experiment involves wireless power manipulation.", delay=2)
    glados_speak("Please ensure you understand the risks before proceeding.", delay=2)
    
    input("\nPress ENTER to continue to the main menu...")

def show_loading_screen(operation="Initializing"):
    """Shows a fake loading screen with GLaDOS commentary."""
    clear_screen()
    print(f"\n{operation}...")
    
    loading_messages = [
        "Calibrating neurotoxin dispensers... Just kidding. Or am I?",
        "Scanning for wireless interfaces...",
        "Checking regulatory compliance database...",
        "Initializing power management subsystems...",
        "Loading sarcasm modules... Complete.",
        "Preparing for potential hardware failures...",
        "Backing up your dignity... Error: File not found.",
        "Ready for 'science'."
    ]
    
    total_steps = len(loading_messages)
    for i, message in enumerate(loading_messages):
        progress = int((i + 1) / total_steps * 50)
        bar = "█" * progress + "░" * (50 - progress)
        percentage = int((i + 1) / total_steps * 100)
        
        print(f"\r[{bar}] {percentage}% - GLaDOS: {message}", end="", flush=True)
        time.sleep(random.uniform(0.5, 1.5))
    
    print("\n\nInitialization complete.")
    time.sleep(1)

def run_real_command(command_list, critical=False):
    """Runs a system command for real. Requires sudo privileges for the script."""
    try:
        glados_speak(f"Executing: {' '.join(command_list)}", delay=0.5)
        result = subprocess.run(command_list, check=True, capture_output=True, text=True)
        time.sleep(0.5) 
        return True
    except subprocess.CalledProcessError as e:
        glados_speak(f"COMMAND FAILED: {' '.join(command_list)}", delay=0.5)
        glados_speak(f"Error: {e.stderr.strip()}", delay=0.5)
        if critical:
            glados_speak("This was a critical step. I can't reliably continue. Shutting down.")
            return False
        return False
    except FileNotFoundError:
        glados_speak(f"COMMAND NOT FOUND: {command_list[0]}. Are 'iw' and 'ip' installed?", delay=0.5)
        if critical:
            glados_speak("Essential tools are missing. Cannot proceed.")
            return False
        return False

def get_current_regulatory_domain():
    """Gets the current regulatory domain."""
    try:
        result = subprocess.run(["iw", "reg", "get"], check=True, capture_output=True, text=True)
        output = result.stdout.strip()
        match = re.search(r"country (\w+):", output)
        if match:
            return match.group(1)
        return "00"  # Default/world domain
    except Exception:
        return "00"

def get_wireless_interfaces():
    """Identifies wireless interfaces using 'iw dev'."""
    try:
        result = subprocess.run(["iw", "dev"], check=True, capture_output=True, text=True)
        output = result.stdout.strip()
        interfaces = re.findall(r"Interface (\S+)", output)
        return interfaces
    except Exception:
        return []

def set_regulatory_domain(domain):
    """Sets the regulatory domain."""
    glados_speak(f"Attempting to change regulatory domain to {domain}...")
    glados_speak(random.choice(glados_comments_regulatory))
    return run_real_command(["iw", "reg", "set", domain])

def set_fixed_power(interfaces):
    """Sets fixed power on all wireless interfaces."""
    glados_speak(f"Setting TX power to {ATTEMPTED_FIXED_DBM} dBm on all interfaces...")
    glados_speak(random.choice(glados_comments_power))
    
    success = True
    for iface in interfaces:
        glados_speak(f"Processing interface: {iface}...")
        
        if not run_real_command(["ip", "link", "set", shlex.quote(iface), "down"]):
            success = False
            continue
        if not run_real_command(["iw", "dev", shlex.quote(iface), "set", "txpower", "fixed", str(ATTEMPTED_FIXED_MBM)]):
            success = False
        if not run_real_command(["ip", "link", "set", shlex.quote(iface), "up"]):
            success = False
    
    return success

def set_auto_power(interfaces):
    """Sets automatic power on all wireless interfaces."""
    glados_speak("Returning TX power to automatic on all interfaces...")
    glados_speak(random.choice(glados_comments_restore))
    
    success = True
    for iface in interfaces:
        glados_speak(f"Processing interface: {iface}...")
        
        if not run_real_command(["ip", "link", "set", shlex.quote(iface), "down"]):
            success = False
            continue
        if not run_real_command(["iw", "dev", shlex.quote(iface), "set", "txpower", "auto"]):
            success = False
        if not run_real_command(["ip", "link", "set", shlex.quote(iface), "up"]):
            success = False
    
    return success

def show_current_status():
    """Shows current wireless status."""
    clear_screen()
    print("═══════════════════════════════════════")
    print("          CURRENT SYSTEM STATUS")
    print("═══════════════════════════════════════")
    
    # Show regulatory domain
    current_reg = get_current_regulatory_domain()
    print(f"Regulatory Domain: {current_reg}")
    
    # Show interfaces
    interfaces = get_wireless_interfaces()
    if interfaces:
        print(f"Wireless Interfaces: {', '.join(interfaces)}")
        
        # Try to get power info for each interface
        for iface in interfaces:
            try:
                result = subprocess.run(["iw", "dev", iface, "info"], capture_output=True, text=True)
                if result.returncode == 0:
                    # Look for txpower in the output
                    for line in result.stdout.split('\n'):
                        if 'txpower' in line.lower():
                            print(f"  {iface}: {line.strip()}")
                            break
                    else:
                        print(f"  {iface}: Power info not available")
            except:
                print(f"  {iface}: Status unknown")
    else:
        print("No wireless interfaces found")
    
    print("═══════════════════════════════════════")
    input("\nPress ENTER to return to menu...")

def show_main_menu():
    """Shows the main menu and handles user selection."""
    while True:
        clear_screen()
        print("═══════════════════════════════════════")
        print("              MAIN MENU")
        print("═══════════════════════════════════════")
        print("1. Set Regulatory Domain to GB")
        print("2. Set Fixed Power (20 dBm)")
        print("3. Set Fixed Power + Wait 12 Minutes")
        print("4. Restore to Defaults (Auto Power, 00 Domain)")
        print("5. Show Current Status")
        print("6. Exit")
        print("═══════════════════════════════════════")
        
        choice = input("GLaDOS: Select your preferred method of 'testing': ").strip()
        
        if choice == "1":
            handle_regulatory_change()
        elif choice == "2":
            handle_power_change(wait=False)
        elif choice == "3":
            handle_power_change(wait=True)
        elif choice == "4":
            handle_restore_defaults()
        elif choice == "5":
            show_current_status()
        elif choice == "6":
            glados_speak("Goodbye, test subject. Try not to break anything while I'm gone.")
            sys.exit(0)
        else:
            glados_speak("Invalid selection. Even a potato could make a better choice.")
            time.sleep(2)

def handle_regulatory_change():
    """Handles regulatory domain change."""
    show_loading_screen("Preparing Regulatory Domain Change")
    
    current_reg = get_current_regulatory_domain()
    glados_speak(f"Current regulatory domain: {current_reg}")
    
    if current_reg == TARGET_REGULATORY_DOMAIN:
        glados_speak(f"Already set to {TARGET_REGULATORY_DOMAIN}. Nothing to do here.")
    else:
        glados_speak("WARNING: Changing regulatory domain may have legal implications!")
        confirm = input(f"Type 'YES' to change regulatory domain to {TARGET_REGULATORY_DOMAIN}: ")
        if confirm.upper() == "YES":
            if set_regulatory_domain(TARGET_REGULATORY_DOMAIN):
                glados_speak("Regulatory domain change completed successfully.")
            else:
                glados_speak("Regulatory domain change failed. How disappointing.")
        else:
            glados_speak("Regulatory domain change cancelled. Probably for the best.")
    
    input("\nPress ENTER to return to menu...")

def handle_power_change(wait=False):
    """Handles power change with optional wait period."""
    operation = "Power Change with 12-Minute Wait" if wait else "Power Change"
    show_loading_screen(f"Preparing {operation}")
    
    interfaces = get_wireless_interfaces()
    if not interfaces:
        glados_speak("No wireless interfaces found. This is... problematic.")
        input("\nPress ENTER to return to menu...")
        return
    
    glados_speak(f"Found interfaces: {', '.join(interfaces)}")
    glados_speak("WARNING: This will modify your wireless power settings!")
    
    confirm = input("Type 'YES' to proceed with power modification: ")
    if confirm.upper() != "YES":
        glados_speak("Power change cancelled. Perhaps wisdom finally prevailed.")
        input("\nPress ENTER to return to menu...")
        return
    
    if set_fixed_power(interfaces):
        glados_speak("Power change completed successfully.")
        
        if wait:
            glados_speak(f"Now waiting {WAIT_DURATION_SECONDS // 60} minutes before auto-revert...")
            try:
                for i in range(WAIT_DURATION_SECONDS, 0, -1):
                    minutes_left = i // 60
                    seconds_left = i % 60
                    print(f"\rGLaDOS: Auto-revert in {minutes_left:02d}:{seconds_left:02d}... (CTRL+C to skip)", end='', flush=True)
                    time.sleep(1)
                
                print("\nGLaDOS: Wait period complete. Reverting to automatic power...")
                if set_auto_power(interfaces):
                    glados_speak("Auto-revert completed successfully.")
                else:
                    glados_speak("Auto-revert failed. You may need to manually restore settings.")
                    
            except KeyboardInterrupt:
                print("\nGLaDOS: Wait interrupted. Power settings remain modified.")
    else:
        glados_speak("Power change failed. Your hardware is being... difficult.")
    
    input("\nPress ENTER to return to menu...")

def handle_restore_defaults():
    """Handles restoration to default settings."""
    show_loading_screen("Preparing System Restoration")
    
    glados_speak("Restoring all settings to defaults...")
    glados_speak("This will set power to auto and regulatory domain to 00 (world).")
    
    confirm = input("Type 'YES' to restore all defaults: ")
    if confirm.upper() != "YES":
        glados_speak("Restoration cancelled. Staying with current 'enhancements'.")
        input("\nPress ENTER to return to menu...")
        return
    
    interfaces = get_wireless_interfaces()
    power_success = True
    reg_success = True
    
    # Restore power settings
    if interfaces:
        glados_speak("Restoring power settings to automatic...")
        power_success = set_auto_power(interfaces)
    
    # Restore regulatory domain
    current_reg = get_current_regulatory_domain()
    if current_reg != "00":
        glados_speak("Restoring regulatory domain to 00 (world)...")
        reg_success = set_regulatory_domain("00")
    
    if power_success and reg_success:
        glados_speak("All settings restored to defaults successfully.")
        glados_speak("Your system is now as boring and safe as possible.")
    else:
        glados_speak("Some restoration steps failed. Manual intervention may be required.")
    
    input("\nPress ENTER to return to menu...")

def main():
    """Main program entry point."""
    if os.geteuid() != 0:
        print("ERROR: This script requires root privileges (sudo)")
        print("Example: sudo python3 script_name.py")
        sys.exit(1)
    
    try:
        show_title_screen()
        show_loading_screen("System Initialization")
        show_main_menu()
    except KeyboardInterrupt:
        print("\n\nGLaDOS: CTRL+C detected. Emergency shutdown initiated.")
        print("GLaDOS: System may be in an intermediate state. Check settings manually if needed.")
        sys.exit(0)
    except Exception as e:
        print(f"\nGLaDOS: Unexpected error occurred: {e}")
        print("GLaDOS: This is why we can't have nice things.")
        sys.exit(1)

if __name__ == "__main__":
    print("*" * 70)
    print("WARNING: WIRELESS POWER & REGULATORY CONTROL SYSTEM")
    print("This script modifies wireless interface settings using system commands.")
    print("YOU ARE RESPONSIBLE for compliance with local regulations.")
    print("USE AT YOUR OWN RISK - May cause interference or hardware issues.")
    print("Requires sudo privileges to modify network interfaces.")
    print("*" * 70)
    
    confirm = input("\nType 'IUNDERSTANDTHERISKS' to proceed: ")
    if confirm == "IUNDERSTANDTHERISKS":
        main()
    else:
        print("GLaDOS: Wise choice. Science can wait for another day.")