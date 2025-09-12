#!/usr/bin/env python3
"""
IMEI Atlas - IMEI Generator and Validator Tool
Supports MikroTik and FiberHome router AT commands
Author: ﺐﻴﻐﻟﺍ ﺮﻬﻈﺑ ﻲﻟ ﻮﻋﺪﺗ نﺍ ﻞﻤﻌﻟﺍ اﺬﻫ مﺍﺪﺨﺘﺳﺍ ﻦﻤﺛ
Telegram: @VHSPC
"""

import sys
import os
import random
import secrets
from datetime import datetime

# ----- Configuration -----
AUTHOR_NAME = "ﺐﻴﻐﻟﺍ ﺮﻬﻈﺑ ﻲﻟ ﻮﻋﺪﺗ نﺍ ﻞﻤﻌﻟﺍ اﺬﻫ مﺍﺪﺨﺘﺳﺍ ﻦﻤﺛ"
DEFAULT_COUNT = 3
LTE_INTERFACE = "lte1"

# Device TAC database
TACS = [
    ("86600507", "U60 PRO,MU5250"),
    ("35461444", "iPhone 16 Pro Max"),
    ("35500828", "16 Pro Max Unlocked"),
    ("35204553", "Apple iPad Pro 13 m4 2024"),
    ("35890743", "Nighthawk M7 Pro MR7400"),
    ("86278507", "FiberHome 5G CPE Pro"),
    ("86073604", "mikrotik"),
    ("86167907", "ZTE G5 ULTRA"),
    ("35573167", "Galaxy S24 Ultra"),
    ("35554513", "S24 Ultra"),
    ("35886618", "Asus ROG Phone 9 Pro"),
    ("35948965", "Google Pixel 10 Pro XL"),
    ("01602600", "M6 NETGEAR MR6150"),
    ("01634700", "M6 Pro NETGEAR MR6400 MR6450 MR6550"),
    ("86316707", "FiberHome 5G Outdoor LG6121D"),
    ("35190977", "ZYXEL NR5103EV2"),
    ("86717306", "H158-381"),
    ("86968607", "Pro 5 E6888-982"),
    ("86335904", "hAP ax lite LTE6"),
    ("35666210", "R11E-LTE6"),
    ("86073604", "RG502Q-EA"),
    ("86945405", "RG520F-EU 5g R16"),
    ("86395505", "ZTE MF297D Router"),
    ("86694906", "zte MC888B"),
    ("86343807", "Suncomm 08 Pro SDX75 5G CPE"),
    ("86824905", "TP-LINK / X80-5G"),
    ("86510304", "5G Outdoor CPE Max N5368X"),
    ("35548843", "DECO BE48-5G"),
    ("01634700", "M6 ProMR6550"),
    ("99001889", "Inseego MiFi X Pro M3000 5G"),
    ("86689704", "Milesight 5G CPE Router UF51"),
    ("86881703", "Huawei B2368-66 outdoor"),
    ("86406705", "N5368X 5G Outdoor CPE Max"),
    ("86638307", "ZTE G5 Ultra MC8531"),
    ("86473406", "zte 888 ultra"),
    ("35062735", "Verizon Internet Gateway ASK-NCQ1338"),
    ("86633903", "ZTE MF288 LTE Turbo Hub"),
    ("86762605", "5g cpe KL501"),
    ("35916017", "Asus Predator x5 5G Router"),
    ("86030205", "RUTX50"),
    ("35435111", "Zyxel 5G Outdoor Router"),
]

# ----- Color Configuration -----
USE_COLOR = True
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN = "\x1b[36m"
YELLOW = "\x1b[33m"

def color(s, code):
    """Apply color to text if enabled"""
    return s if not USE_COLOR else f"{code}{s}{RESET}"

# ----- Luhn Algorithm Functions -----
def luhn_checksum_mod10(s):
    """Calculate Luhn checksum modulo 10"""
    if not s.isdigit():
        raise ValueError("non-digit in Luhn input")
    total = 0
    for i, ch in enumerate(s[::-1]):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10

def calc_check_digit14(first14):
    """Calculate check digit for 14-digit IMEI base"""
    if not (isinstance(first14, str) and first14.isdigit() and len(first14) == 14):
        raise ValueError("first14 must be 14 digits")
    mod = luhn_checksum_mod10(first14 + "0")
    return str((10 - mod) % 10)

def is_valid_imei(i):
    """Validate IMEI using Luhn algorithm"""
    return isinstance(i, str) and len(i) == 15 and i.isdigit() and luhn_checksum_mod10(i) == 0

# ----- IMEI Generation Functions -----
def gen_serial6(rng):
    """Generate 6-digit serial number"""
    return f"{rng.randrange(0, 10**6):06d}"

def gen_imei_for_tac(tac, rng):
    """Generate IMEI for given TAC"""
    s6 = gen_serial6(rng)
    first14 = tac + s6
    return first14 + calc_check_digit14(first14)

def gen_random_tac(rng):
    """Generate random 8-digit TAC"""
    return f"{rng.randrange(10**7, 10**8):08d}"

def gen_completely_random_imei(rng):
    """Generate completely random IMEI with random TAC"""
    tac = gen_random_tac(rng)
    return gen_imei_for_tac(tac, rng)

# ----- AT Command Formatting -----
def at_command_for_imei(imei, interface=LTE_INTERFACE):
    """Format IMEI for MikroTik AT command"""
    return f'interface lte at-chat {interface} input="AT+EGMR=1,7,\\"{imei}\\""'

def fiberhome_at_command_for_imei(imei):
    """Format IMEI for FiberHome AT command"""
    return f'AT+EGMR=1,7,"{imei}"'

# ----- Utility Functions -----
def clear_screen():
    """Clear terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="Press Enter to continue..."):
    """Pause execution until user presses Enter"""
    try:
        input(msg)
    except KeyboardInterrupt:
        pass

def safe_filename(name):
    """Convert string to safe filename"""
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()

def save_at_block(device_name, tac, imeis):
    """Save AT commands to file"""
    safe = safe_filename(device_name)
    fname = f"at_{safe}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"# AT commands for {device_name} (TAC {tac})\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        for im in imeis:
            f.write(at_command_for_imei(im) + "\n")
        f.write("\n/system reboot\n")
    return fname

# ----- IMEI Generation Functions -----
def generate_random_imeis(rng, count=10):
    """Generate IMEIs with random TACs"""
    imeis = [gen_completely_random_imei(rng) for _ in range(count)]
    return {"tac": "Various", "name": "Random IMEIs (different TACs)", "imeis": imeis}

def generate_custom_tac_imeis(rng, count=10):
    """Generate IMEIs with custom TAC"""
    while True:
        try:
            tac_input = input(color("Enter the first 8 digits (TAC) of the IMEI: ", YELLOW)).strip()
            if not tac_input:
                print(color("No TAC provided. Returning to menu.", RED))
                return None
            if len(tac_input) != 8 or not tac_input.isdigit():
                print(color("TAC must be exactly 8 digits. Try again.", RED))
                continue
            break
        except KeyboardInterrupt:
            print(color("\nOperation cancelled.", DIM))
            return None
    
    imeis = [gen_imei_for_tac(tac_input, rng) for _ in range(count)]
    return {"tac": tac_input, "name": f"Custom TAC: {tac_input}", "imeis": imeis}

# ----- Luhn Algorithm Step-by-Step Analysis -----
def luhn_step_by_step():
    """Display step-by-step Luhn algorithm analysis for a given number"""
    clear_screen()
    print(color("Luhn Algorithm Step-by-Step Analysis", BOLD + CYAN))
    print(color("=" * 50, DIM))
    
    # Get input from user
    number = input(color("Enter a number to analyze: ", YELLOW)).strip()
    
    if not number.isdigit():
        print(color("Input must contain only digits!", RED))
        pause()
        return
    
    print("\n" + color("Step-by-step analysis:", BOLD))
    print(color("-" * 30, DIM))
    
    # Convert to list of integers
    digits = [int(d) for d in number]
    n = len(digits)
    
    # Display original number
    print(f"Original number: {' '.join(str(d) for d in digits)}")
    print(f"Number of digits: {n}")
    
    # Step 1: Reverse the number
    reversed_digits = list(reversed(digits))
    print(f"\n1. Reverse the number: {' '.join(str(d) for d in reversed_digits)}")
    
    # Step 2: Double every second digit
    doubled_digits = []
    operations = []
    for i, digit in enumerate(reversed_digits):
        if i % 2 == 1:  # Every second digit (starting from the second)
            doubled = digit * 2
            doubled_digits.append(doubled)
            operations.append(f"Position {i}: {digit} × 2 = {doubled}")
        else:
            doubled_digits.append(digit)
            operations.append(f"Position {i}: {digit} (no change)")
    
    print("2. Double every second digit (starting from the second):")
    for op in operations:
        print(f"   {op}")
    
    # Display the doubled digits
    print(f"   After doubling: {' '.join(str(d) for d in doubled_digits)}")
    
    # Step 3: Adjust numbers greater than 9
    adjusted_digits = []
    operations = []
    for i, digit in enumerate(doubled_digits):
        if digit > 9:
            adjusted = digit - 9
            adjusted_digits.append(adjusted)
            operations.append(f"Position {i}: {digit} → {digit}-9 = {adjusted}")
        else:
            adjusted_digits.append(digit)
            operations.append(f"Position {i}: {digit} (no adjustment)")
    
    print("3. Adjust numbers greater than 9 (subtract 9):")
    for op in operations:
        print(f"   {op}")
    
    # Display the adjusted digits
    print(f"   After adjustment: {' '.join(str(d) for d in adjusted_digits)}")
    
    # Step 4: Sum all digits
    total = sum(adjusted_digits)
    print(f"4. Sum all digits: {' + '.join(str(d) for d in adjusted_digits)} = {total}")
    
    # Step 5: Check if divisible by 10
    is_valid = total % 10 == 0
    print(f"5. Check if sum is divisible by 10: {total} % 10 == {total % 10}")
    
    # Final result
    if is_valid:
        print(color(f"\nResult: The number {number} is VALID ✅", GREEN))
    else:
        print(color(f"\nResult: The number {number} is INVALID ❌", RED))
    
    pause()

# ----- Device View Function -----
def device_view(g, count, rng):
    """Display device details and handle commands"""
    while True:
        clear_screen()
        print(color(f"Device: {g['name']}  (TAC {g['tac']})", BOLD + CYAN))
        print(color("-" * 44, DIM))
        for i, im in enumerate(g["imeis"], 1):
            print(f"{i:2d}. {color(im, GREEN if is_valid_imei(im) else RED)}")
        print()
        print(color("Commands: a=mikrotik  f=fiberhome  s=save  v=validate  r=regenerate  b=back  q=quit", DIM))
        cmd = input(color("Enter command: ", YELLOW)).strip().lower()
        
        if cmd in ("b", "0", "back"):
            return False
        if cmd in ("q", "quit", "exit"):
            return True
            
        if cmd in ("a", "at", "show"):
            print()
            print(color("# MikroTik AT commands:", BOLD + CYAN))
            for im in g["imeis"]:
                print(at_command_for_imei(im))
            print()
            print("/system reboot")
            print()
            pause()
            continue

        if cmd in ("f", "fiberhome"):
            print()
            print(color("# FiberHome AT commands:", BOLD + CYAN))
            for im in g["imeis"]:
                print(fiberhome_at_command_for_imei(im))
            print()
            pause()
            continue

        if cmd in ("s", "save"):
            fname = save_at_block(g["name"], g["tac"], g["imeis"])
            print(color(f"Saved AT commands to {fname}", GREEN))
            pause()
            continue

        if cmd in ("v", "validate"):
            print()
            print(color(f"{'IMEI':16s} {'CHK':^4s} {'MOD':^4s} {'STATUS':>6s}", BOLD + CYAN))
            for imei in g["imeis"]:
                chk = imei[-1]
                mod = str(luhn_checksum_mod10(imei))
                ok = "VALID" if is_valid_imei(imei) else "INVALID"
                stat_col = GREEN if ok == "VALID" else RED
                print(f"{imei:16s} {chk:^4s} {mod:^4s} {color(ok, stat_col):>6s}")
            pause()
            continue

        if cmd in ("r", "regen", "regenerate"):
            try:
                new_count_input = input(color(f"Enter new count [current: {count}]: ", YELLOW)).strip()
                if new_count_input:
                    new_count = int(new_count_input)
                    if new_count < 1:
                        print(color("Count must be at least 1. Keeping current count.", RED))
                    else:
                        count = new_count
            except ValueError:
                print(color("Invalid number. Keeping current count.", RED))
            
            if g["tac"] == "Various":
                g["imeis"] = [gen_completely_random_imei(rng) for _ in range(count)]
            else:
                g["imeis"] = [gen_imei_for_tac(g["tac"], rng) for _ in range(count)]
                
            print(color(f"Regenerated {count} IMEIs for this device.", GREEN))
            pause()
            continue

        print(color("Unknown command.", YELLOW))
        pause()

# ----- IMEI Validation Function -----
def check_user_imei():
    """Validate user-provided IMEI"""
    clear_screen()
    print(color("IMEI VALIDATOR (Luhn Check)", BOLD + CYAN))
    print(color("=" * 44, DIM))
    imei = input(color("Enter IMEI to validate: ", YELLOW)).strip()
    if not imei.isdigit():
        print(color("IMEI must contain only digits!", RED))
    elif len(imei) != 15:
        print(color("IMEI must be exactly 15 digits!", RED))
    else:
        if is_valid_imei(imei):
            print(color(f"IMEI {imei} is VALID ✅", GREEN))
        else:
            print(color(f"IMEI {imei} is INVALID ❌", RED))
    pause()

# ----- Main Application -----
def main(count=DEFAULT_COUNT, seed=None, no_color=False):
    """Main application function"""
    global USE_COLOR
    if no_color:
        USE_COLOR = False

    rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))

    # Pre-generate IMEIs for all devices
    groups = []
    for tac, name in TACS:
        imeis = [gen_imei_for_tac(tac, rng) for _ in range(count)]
        groups.append({"tac": tac, "name": name, "imeis": imeis})

    while True:
        clear_screen()
        print(color("IMEI Atlas", BOLD + CYAN))
        print(color("=" * 44, DIM))
        print(color(f"Author: {AUTHOR_NAME}", DIM))
        print(color(f"Devices: {len(groups)} | IMEIs per device: {count}", DIM))
        
        # Display device list
        for i, g in enumerate(groups, start=1):
            print(color(f"{i:2d}. {g['name']}", CYAN))
        
        # Display special options
        random_option = len(groups) + 1
        custom_tac_option = len(groups) + 2
        check_imei_option = len(groups) + 3
        luhn_option = len(groups) + 4
        
        print(color(f"{random_option:2d}. Generate random IMEIs (different TACs)", CYAN))
        print(color(f"{custom_tac_option:2d}. Generate IMEIs with custom TAC", CYAN))
        print(color(f"{check_imei_option:2d}. Check your IMEI (Luhn)", CYAN))
        print(color(f"{luhn_option:2d}. Luhn Algorithm Step-by-Step Analysis", CYAN))
        
        print()
        print(color("Select a device number to view (q to quit).", DIM))
        choice = input(color("Enter choice: ", YELLOW)).strip().lower()
        
        # Handle special options
        if choice == str(check_imei_option):
            check_user_imei()
            continue
            
        if choice == str(luhn_option):
            luhn_step_by_step()
            continue

        if choice in ("q", "quit", "exit"):
            print(color("Goodbye.", DIM))
            return

        if not choice.isdigit():
            print(color("Please enter a number.", RED))
            pause()
            continue

        idx = int(choice) - 1

        # Handle special options
        if idx == len(groups):  # Random IMEIs
            try:
                random_count_input = input(color("Enter number of random IMEIs to generate (default 10): ", YELLOW)).strip()
                random_count = 10 if not random_count_input else int(random_count_input)
                if random_count < 1:
                    print(color("Count must be at least 1. Using default 10.", RED))
                    random_count = 10
            except ValueError:
                print(color("Invalid number. Using default 10.", RED))
                random_count = 10
                
            temp_group = generate_random_imeis(rng, random_count)
            if temp_group:
                should_quit = device_view(temp_group, random_count, rng)
                if should_quit:
                    return
            continue
            
        if idx == len(groups) + 1:  # Custom TAC
            temp_group = generate_custom_tac_imeis(rng, 10)
            if temp_group:
                should_quit = device_view(temp_group, 10, rng)
                if should_quit:
                    return
            continue
        
        # Handle regular device selection
        if idx < 0 or idx >= len(groups):
            print(color("Invalid selection.", RED))
            pause()
            continue

        # Regular device view
        should_quit = device_view(groups[idx], count, rng)
        if should_quit:
            return

if __name__ == "__main__":
    # Parse command line arguments
    cnt = DEFAULT_COUNT
    seed = None
    no_color = False
    
    argv = sys.argv[1:]
    if "--count" in argv:
        try:
            i = argv.index("--count")
            cnt = int(argv[i+1])
        except (ValueError, IndexError):
            pass
            
    if "--seed" in argv:
        try:
            i = argv.index("--seed")
            seed = int(argv[i+1])
        except (ValueError, IndexError):
            pass
            
    if "--no-color" in argv:
        no_color = True
        
    try:
        main(count=cnt, seed=seed, no_color=no_color)
    except KeyboardInterrupt:
        print("\nInterrupted. Bye.")