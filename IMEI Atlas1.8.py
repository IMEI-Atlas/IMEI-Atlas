#!/usr/bin/env python3
"""
IMEI Atlas - IMEI Generator and Validator Tool (Enhanced Version)
Includes: export ALL IMEIs to multiple formats, improved security, and better code organization.

Author: ﺐﻴﻐﻟﺍ ﺮﻬﻈﺑ ﻲﻟ ﻮﻋﺪﺗ نﺍ ﻞﻤﻌﻟﺍ اﺬﻫ مﺍﺪﺨﺘﺳﺍ ﻦﻤﺛ
Telegram: @VHSPC

DISCLAIMER: This tool is for educational and testing purposes only. 
Misuse of IMEI numbers may violate laws in your jurisdiction .


"""

from __future__ import annotations
import argparse
import os
import random
import secrets
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# -------------------------
# Security Disclaimer
# -------------------------
DISCLAIMER = """
WARNING: This tool is for educational and testing purposes only. 
Misuse of IMEI numbers may violate laws in your jurisdiction.
Use only on devices you own and have permission to modify.
ﻂﻘﻓ ﺔﻳﺭﺎﺒﺘﺧﻻﺍﻭ ﺔﻴﻤﻴﻠﻌﺘﻟﺍ ضﺍﺮﻏﻸﻟ ﺎًﻳﺮﺼﺣ ﺔﻤﻤﺼُﻣ ةﺍﺩﻷﺍ هﺬﻫ :ﺔﻴﻟﻭﺆﺴﻤﻟﺍ ءﻼﺧﺇ
"""

# -------------------------
# Configuration
# -------------------------
AUTHOR_NAME: str = "ﺐﻴﻐﻟﺍ ﺮﻬﻈﺑ ﻲﻟ ﻮﻋﺪﺗ نﺍ ﻞﻤﻌﻟﺍ اﺬﻫ مﺍﺪﺨﺘﺳﺍ ﻦﻤﺛ"
DEFAULT_IMEIS_PER_DEVICE: int = 3
DEFAULT_LTE_INTERFACE: str = "lte1"
USE_COLOR_BY_DEFAULT: bool = True
AT_OUTPUT_DIRECTORY: str = r"./exports"
DB_OUTPUT_DIRECTORY: str = r"./database"
MAX_IMEI_GENERATION: int = 1000  # Safety limit

# -------------------------
# Device Database with Enhanced Structure
# -------------------------
class DeviceType(Enum):
    SMARTPHONE = "Smartphone"
    TABLET = "Tablet"
    ROUTER = "Router"
    HOTSPOT = "Hotspot"
    IOT = "IoT Device"
    OTHER = "Other"

DEVICE_DATABASE: List[Dict[str, Any]] = [
    {"tac": "86600507", "name": "U60 PRO", "model": "MU5250", "type": DeviceType.ROUTER},
    {"tac": "35461444", "name": "iPhone", "model": "16 Pro Max", "type": DeviceType.SMARTPHONE},
    {"tac": "35500828", "name": "iPhone", "model": "16 Pro Max Unlocked", "type": DeviceType.SMARTPHONE},
    {"tac": "35204553", "name": "Apple iPad Pro", "model": "13 m4 2024", "type": DeviceType.TABLET},
    {"tac": "35890743", "name": "Nighthawk M7 Pro", "model": "MR7400", "type": DeviceType.ROUTER},
    {"tac": "86278507", "name": "FiberHome", "model": "5G CPE Pro", "type": DeviceType.ROUTER},
    {"tac": "86073604", "name": "Mikrotik", "model": "Unknown", "type": DeviceType.ROUTER},
    {"tac": "86167907", "name": "ZTE", "model": "G5 ULTRA", "type": DeviceType.ROUTER},
    {"tac": "35573167", "name": "Samsung Galaxy", "model": "S24 Ultra", "type": DeviceType.SMARTPHONE},
    {"tac": "35554513", "name": "Samsung", "model": "S24 Ultra", "type": DeviceType.SMARTPHONE},
    {"tac": "35886618", "name": "Asus", "model": "ROG Phone 9 Pro", "type": DeviceType.SMARTPHONE},
    {"tac": "35948965", "name": "Google Pixel", "model": "10 Pro XL", "type": DeviceType.SMARTPHONE},
    {"tac": "01602600", "name": "NETGEAR", "model": "M6 MR6150", "type": DeviceType.ROUTER},
    {"tac": "01634700", "name": "NETGEAR", "model": "M6 Pro MR6400/MR6450/MR6550", "type": DeviceType.ROUTER},
    {"tac": "86316707", "name": "FiberHome", "model": "5G Outdoor LG6121D", "type": DeviceType.ROUTER},
    {"tac": "35190977", "name": "ZYXEL", "model": "NR5103EV2", "type": DeviceType.ROUTER},
    {"tac": "86717306", "name": "Huawei", "model": "H158-381", "type": DeviceType.ROUTER},
    {"tac": "86968607", "name": "Unknown", "model": "Pro 5 E6888-982", "type": DeviceType.ROUTER},
    {"tac": "86335904", "name": "Mikrotik", "model": "hAP ax lite LTE6", "type": DeviceType.ROUTER},
    {"tac": "35666210", "name": "Unknown", "model": "R11E-LTE6", "type": DeviceType.ROUTER},
    {"tac": "86073604", "name": "ZTE", "model": "RG502Q-EA", "type": DeviceType.ROUTER},
    {"tac": "86945405", "name": "ZTE", "model": "RG520F-EU 5g R16", "type": DeviceType.ROUTER},
    {"tac": "86395505", "name": "ZTE", "model": "MF297D Router", "type": DeviceType.ROUTER},
    {"tac": "86694906", "name": "ZTE", "model": "MC888B", "type": DeviceType.ROUTER},
    {"tac": "86343807", "name": "Suncomm", "model": "08 Pro SDX75 5G CPE", "type": DeviceType.ROUTER},
    {"tac": "86824905", "name": "TP-LINK", "model": "X80-5G", "type": DeviceType.ROUTER},
    {"tac": "86510304", "name": "Unknown", "model": "5G Outdoor CPE Max N5368X", "type": DeviceType.ROUTER},
    {"tac": "35548843", "name": "TP-LINK", "model": "DECO BE48-5G", "type": DeviceType.ROUTER},
    {"tac": "01634700", "name": "NETGEAR", "model": "M6 ProMR6550", "type": DeviceType.ROUTER},
    {"tac": "99001889", "name": "Inseego", "model": "MiFi X Pro M3000 5G", "type": DeviceType.HOTSPOT},
    {"tac": "86689704", "name": "Milesight", "model": "5G CPE Router UF51", "type": DeviceType.ROUTER},
    {"tac": "86881703", "name": "Huawei", "model": "B2368-66 outdoor", "type": DeviceType.ROUTER},
    {"tac": "86406705", "name": "Unknown", "model": "N5368X 5G Outdoor CPE Max", "type": DeviceType.ROUTER},
    {"tac": "86638307", "name": "ZTE", "model": "G5 Ultra MC8531", "type": DeviceType.ROUTER},
    {"tac": "86473406", "name": "ZTE", "model": "888 ultra", "type": DeviceType.ROUTER},
    {"tac": "35062735", "name": "Verizon", "model": "Internet Gateway ASK-NCQ1338", "type": DeviceType.ROUTER},
    {"tac": "86633903", "name": "ZTE", "model": "MF288 LTE Turbo Hub", "type": DeviceType.ROUTER},
    {"tac": "86762605", "name": "Unknown", "model": "5g cpe KL501", "type": DeviceType.ROUTER},
    {"tac": "35916017", "name": "Asus", "model": "Predator x5 5G Router", "type": DeviceType.ROUTER},
    {"tac": "86030205", "name": "Teltonika", "model": "RUTX50", "type": DeviceType.ROUTER},
    {"tac": "35435111", "name": "Zyxel", "model": "5G Outdoor Router", "type": DeviceType.ROUTER},
    {"tac": "86415504", "name": "ZTE", "model": "Netbox MC7010 5G Outdoor", "type": DeviceType.ROUTER},
    {"tac": "86676006", "name": "ZTE", "model": "ZLT X25 Pro", "type": DeviceType.ROUTER},
    {"tac": "86278507", "name": "Fiberhome", "model": "LG6851F BE7200", "type": DeviceType.ROUTER},
    {"tac": "86120006", "name": "Huawei", "model": "5G Outdoor CPE Max 5 H352-381", "type": DeviceType.ROUTER},
    {"tac": "35922762", "name": "TP-LINK", "model": "Deco BE65-5G BE9300", "type": DeviceType.ROUTER},
]

# -------------------------
# Terminal color helpers
# -------------------------
class Colors:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    CYAN = "\x1b[36m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"

def apply_color(text: str, code: str, enabled: bool) -> str:
    """Return colored text if enabled, otherwise plain text."""
    return text if not enabled else f"{code}{text}{Colors.RESET}"

# -------------------------
# Luhn algorithm utilities
# -------------------------
def luhn_checksum_mod10(number_string: str) -> int:
    """
    Calculate Luhn checksum (mod 10) for the given numeric string.
    Raises ValueError for invalid inputs.
    """
    if not number_string.isdigit():
        raise ValueError("Luhn input contains non-digit characters")
    total = 0
    for position_from_right, ch in enumerate(reversed(number_string)):
        digit = ord(ch) - ord("0")
        if position_from_right % 2 == 1:
            doubled = digit * 2
            if doubled > 9:
                doubled -= 9
            total += doubled
        else:
            total += digit
    return total % 10

def calculate_imei_check_digit(first_14_digits: str) -> str:
    """Calculate the 15th IMEI check digit for a 14-digit base using Luhn."""
    if not (isinstance(first_14_digits, str) and first_14_digits.isdigit() and len(first_14_digits) == 14):
        raise ValueError("first_14_digits must be a 14-digit numeric string")
    mod = luhn_checksum_mod10(first_14_digits + "0")
    return str((10 - mod) % 10)

def validate_imei(imei_string: str) -> bool:
    """Return True if imei_string is a valid 15-digit IMEI using Luhn."""
    return isinstance(imei_string, str) and len(imei_string) == 15 and imei_string.isdigit() and luhn_checksum_mod10(imei_string) == 0

# -------------------------
# IMEI Generator Class
# -------------------------
class IMEIGenerator:
    """Class to handle IMEI generation with safety limits."""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))
    
    def generate_six_digit_serial(self) -> str:
        """Return a zero-padded 6-digit serial from the provided RNG."""
        return f"{self.rng.randrange(0, 10**6):06d}"
    
    def generate_imei_from_tac(self, tac_8_digits: str) -> str:
        """Given an 8-digit TAC, produce a valid 15-digit IMEI."""
        if not (tac_8_digits.isdigit() and len(tac_8_digits) == 8):
            raise ValueError("TAC must be exactly 8 digits")
        serial6 = self.generate_six_digit_serial()
        first14 = tac_8_digits + serial6
        check_digit = calculate_imei_check_digit(first14)
        return first14 + check_digit
    
    def generate_random_8digit_tac(self) -> str:
        """Return a random 8-digit TAC (first digit not zero)."""
        return f"{self.rng.randrange(10**7, 10**8):08d}"
    
    def generate_completely_random_imei(self) -> str:
        """Generate an IMEI using a random TAC."""
        tac = self.generate_random_8digit_tac()
        return self.generate_imei_from_tac(tac)
    
    def generate_batch_imeis(self, tac: str, count: int) -> List[str]:
        """Generate multiple IMEIs with safety limit."""
        if count > MAX_IMEI_GENERATION:
            raise ValueError(f"Cannot generate more than {MAX_IMEI_GENERATION} IMEIs at once")
        
        if tac == "Various":
            return [self.generate_completely_random_imei() for _ in range(count)]
        else:
            return [self.generate_imei_from_tac(tac) for _ in range(count)]

# -------------------------
# AT-command formatting
# -------------------------
def mikrotik_at_command_for_imei(imei: str, interface: str = DEFAULT_LTE_INTERFACE) -> str:
    """Return MikroTik interface lte at-chat command to set IMEI."""
    return f'interface lte at-chat {interface} input="AT+EGMR=1,7,\\\"{imei}\\\""'

def fiberhome_at_command_for_imei(imei: str) -> str:
    """Return FiberHome AT command to set IMEI."""
    return f'AT+EGMR=1,7,\"{imei}\"'

# -------------------------
# File utilities
# -------------------------
def make_safe_filename(desired_name: str) -> str:
    """Return a filesystem-safe version of a string."""
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ")
    return "".join((c if c in allowed_chars else "_") for c in desired_name).strip()

def save_at_commands_to_file(device_name: str, tac: str, imei_list: List[str], output_dir: str = AT_OUTPUT_DIRECTORY) -> str:
    """Save AT commands for a device to a text file and return the file path."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = make_safe_filename(device_name) or "device"
    file_path = Path(output_dir) / f"at_{safe_name}.txt"
    with file_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# AT commands for {device_name} (TAC {tac})\n")
        fh.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
        fh.write(f"# {DISCLAIMER.strip()}\n\n")
        for imei in imei_list:
            fh.write(mikrotik_at_command_for_imei(imei) + "\n")
        fh.write("\n/system reboot\n")
    return str(file_path.resolve())

def save_all_devices_imeis_to_file(
    device_groups: List[Dict[str, object]],
    output_dir: str = AT_OUTPUT_DIRECTORY,
    filename: Optional[str] = None,
    include_timestamps: bool = True,
    include_at_commands: bool = False,
    format_type: str = "txt"
) -> str:
    """
    Save all device names, TACs and their IMEIs to a file in various formats.
    Returns the absolute path to the saved file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if filename:
        safe_filename = make_safe_filename(filename)
        # Add appropriate extension if not present
        if not safe_filename.endswith(f".{format_type}"):
            safe_filename = f"{safe_filename}.{format_type}"
    else:
        safe_filename = f"all_imeis_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.{format_type}"
    
    output_path = Path(output_dir) / safe_filename

    if format_type == "txt":
        with output_path.open("w", encoding="utf-8") as file_handle:
            file_handle.write("# IMEI Atlas - All devices export\n")
            if include_timestamps:
                file_handle.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
            file_handle.write(f"# Devices: {len(device_groups)}\n")
            file_handle.write(f"# {DISCLAIMER.strip()}\n\n")

            for group in device_groups:
                device_name = group.get("name", "Unknown Device")
                tac_value = group.get("tac", "Unknown TAC")
                imei_list: List[str] = group.get("imeis", [])
                file_handle.write(f"Device: {device_name}  (TAC {tac_value})\n")
                file_handle.write("-" * 60 + "\n")
                for imei_value in imei_list:
                    if include_at_commands:
                        at_cmd = mikrotik_at_command_for_imei(imei_value)
                        file_handle.write(f"{imei_value}    {at_cmd}\n")
                    else:
                        file_handle.write(f"{imei_value}\n")
                file_handle.write("\n")
    
    elif format_type == "csv":
        with output_path.open("w", newline='', encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(["Device Name", "TAC", "IMEI", "AT Command" if include_at_commands else ""])
            for group in device_groups:
                device_name = group.get("name", "Unknown Device")
                tac_value = group.get("tac", "Unknown TAC")
                for imei_value in group.get("imeis", []):
                    if include_at_commands:
                        at_cmd = mikrotik_at_command_for_imei(imei_value)
                        writer.writerow([device_name, tac_value, imei_value, at_cmd])
                    else:
                        writer.writerow([device_name, tac_value, imei_value])
    
    elif format_type == "json":
        data = {
            "metadata": {
                "generated": datetime.utcnow().isoformat() + "Z",
                "device_count": len(device_groups),
                "disclaimer": DISCLAIMER.strip()
            },
            "devices": []
        }
        
        for group in device_groups:
            device_data = {
                "name": group.get("name", "Unknown Device"),
                "tac": group.get("tac", "Unknown TAC"),
                "imeis": group.get("imeis", [])
            }
            if include_at_commands:
                device_data["at_commands"] = [mikrotik_at_command_for_imei(imei) for imei in device_data["imeis"]]
            data["devices"].append(device_data)
        
        with output_path.open("w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, ensure_ascii=False)
    
    elif format_type == "sqlite":
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tac TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imeis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                imei TEXT NOT NULL UNIQUE,
                at_command TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')
        
        # Insert data
        for group in device_groups:
            device_name = group.get("name", "Unknown Device")
            tac_value = group.get("tac", "Unknown TAC")
            
            cursor.execute(
                "INSERT INTO devices (name, tac) VALUES (?, ?)",
                (device_name, tac_value)
            )
            device_id = cursor.lastrowid
            
            for imei_value in group.get("imeis", []):
                at_cmd = mikrotik_at_command_for_imei(imei_value) if include_at_commands else None
                cursor.execute(
                    "INSERT INTO imeis (device_id, imei, at_command) VALUES (?, ?, ?)",
                    (device_id, imei_value, at_cmd)
                )
        
        conn.commit()
        conn.close()

    return str(output_path.resolve())

# -------------------------
# UI / Console helpers
# -------------------------
def clear_terminal_screen() -> None:
    """Clear the console."""
    os.system("cls" if os.name == "nt" else "clear")

def pause_for_user(message: str = "Press Enter to continue...") -> None:
    """Pause until user presses Enter (KeyboardInterrupt is swallowed)."""
    try:
        input(message)
    except KeyboardInterrupt:
        pass

def show_help_menu(use_color: bool) -> None:
    """Display help information."""
    clear_terminal_screen()
    print(apply_color("IMEI Atlas - Help Menu", Colors.BOLD + Colors.CYAN, use_color))
    print(apply_color("=" * 40, Colors.DIM, use_color))
    print(apply_color("Commands:", Colors.BOLD, use_color))
    print("  a/mikrotik  - Show MikroTik AT commands")
    print("  f/fiberhome - Show FiberHome AT commands")
    print("  s/save     - Save AT commands to file")
    print("  v/validate - Validate IMEIs with Luhn algorithm")
    print("  r/regenerate - Regenerate IMEIs for device")
    print("  b/back     - Return to main menu")
    print("  q/quit     - Exit program")
    print()
    print(apply_color(DISCLAIMER, Colors.YELLOW, use_color))
    pause_for_user()

# -------------------------
# Interactive device view
# -------------------------
def device_menu_view(device_group: Dict[str, object], imei_generator: IMEIGenerator, use_color: bool) -> bool:
    """
    Show device IMEIs and accept commands.
    Returns True if the application should quit, False to go back to main menu.
    """
    while True:
        clear_terminal_screen()
        name = device_group["name"]
        tac = device_group["tac"]
        imei_list: List[str] = device_group["imeis"]
        print(apply_color(f"Device: {name}  (TAC {tac})", Colors.BOLD + Colors.CYAN, use_color))
        print(apply_color("-" * 44, Colors.DIM, use_color))
        for index, imei_value in enumerate(imei_list, start=1):
            color_code = Colors.GREEN if validate_imei(imei_value) else Colors.RED
            print(f"{index:2d}. {apply_color(imei_value, color_code, use_color)}")
        print()
        print(apply_color("Commands: a=mikrotik  f=fiberhome  s=save  v=validate  r=regenerate  h=help  b=back  q=quit", Colors.DIM, use_color))
        cmd = input(apply_color("Enter command: ", Colors.YELLOW, use_color)).strip().lower()

        if cmd in ("b", "0", "back"):
            return False
        if cmd in ("q", "quit", "exit"):
            return True
        if cmd in ("h", "help"):
            show_help_menu(use_color)
            continue

        if cmd in ("a", "at", "show"):
            print()
            print(apply_color("# MikroTik AT commands:", Colors.BOLD + Colors.CYAN, use_color))
            for imei_value in imei_list:
                print(mikrotik_at_command_for_imei(imei_value))
            print("\n/system reboot\n")
            pause_for_user()
            continue

        if cmd in ("f", "fiberhome"):
            print()
            print(apply_color("# FiberHome AT commands:", Colors.BOLD + Colors.CYAN, use_color))
            for imei_value in imei_list:
                print(fiberhome_at_command_for_imei(imei_value))
            print()
            pause_for_user()
            continue

        if cmd in ("s", "save"):
            saved_path = save_at_commands_to_file(name, tac, imei_list)
            print(apply_color(f"Saved AT commands to {saved_path}", Colors.GREEN, use_color))
            pause_for_user()
            continue

        if cmd in ("v", "validate"):
            print()
            header = f"{'IMEI':16s} {'CHK':^4s} {'MOD':^4s} {'STATUS':>6s}"
            print(apply_color(header, Colors.BOLD + Colors.CYAN, use_color))
            for imei_value in imei_list:
                chk_digit = imei_value[-1]
                mod_value = str(luhn_checksum_mod10(imei_value))
                ok_text = "VALID" if validate_imei(imei_value) else "INVALID"
                color_code = Colors.GREEN if ok_text == "VALID" else Colors.RED
                print(f"{imei_value:16s} {chk_digit:^4s} {mod_value:^4s} {apply_color(ok_text, color_code, use_color):>6s}")
            pause_for_user()
            continue

        if cmd in ("r", "regen", "regenerate"):
            try:
                current_count = len(imei_list)
                new_count_input = input(apply_color(f"Enter new count [current: {current_count}]: ", Colors.YELLOW, use_color)).strip()
                if new_count_input:
                    new_count = int(new_count_input)
                    if new_count < 1 or new_count > MAX_IMEI_GENERATION:
                        print(apply_color(f"Count must be between 1 and {MAX_IMEI_GENERATION}. Keeping current count.", Colors.RED, use_color))
                        pause_for_user()
                        continue
                else:
                    new_count = current_count
            except ValueError:
                print(apply_color("Invalid number. Keeping current count.", Colors.RED, use_color))
                pause_for_user()
                continue

            try:
                if device_group["tac"] == "Various":
                    device_group["imeis"] = imei_generator.generate_batch_imeis("Various", new_count)
                else:
                    device_group["imeis"] = imei_generator.generate_batch_imeis(device_group["tac"], new_count)
                
                print(apply_color(f"Regenerated {new_count} IMEIs for this device.", Colors.GREEN, use_color))
            except ValueError as e:
                print(apply_color(f"Error: {e}", Colors.RED, use_color))
            
            pause_for_user()
            continue

        print(apply_color("Unknown command. Type 'h' for help.", Colors.YELLOW, use_color))
        pause_for_user()

# -------------------------
# Non-interactive IMEI check helper
# -------------------------
def run_imei_validator_prompt(use_color: bool) -> None:
    """Prompt the user to enter an IMEI and validate it."""
    clear_terminal_screen()
    print(apply_color("IMEI VALIDATOR (Luhn Check)", Colors.BOLD + Colors.CYAN, use_color))
    print(apply_color("=" * 44, Colors.DIM, use_color))
    imei_input = input(apply_color("Enter IMEI to validate: ", Colors.YELLOW, use_color)).strip()
    if not imei_input.isdigit():
        print(apply_color("IMEI must contain only digits!", Colors.RED, use_color))
    elif len(imei_input) != 15:
        print(apply_color("IMEI must be exactly 15 digits!", Colors.RED, use_color))
    else:
        if validate_imei(imei_input):
            print(apply_color(f"IMEI {imei_input} is VALID ✅", Colors.GREEN, use_color))
        else:
            print(apply_color(f"IMEI {imei_input} is INVALID ❌", Colors.RED, use_color))
    pause_for_user()

# -------------------------
# Luhn step-by-step helper
# -------------------------
def run_luhn_step_by_step(use_color: bool) -> None:
    """Interactive step-by-step explanation of the Luhn algorithm for a number entered by the user."""
    clear_terminal_screen()
    print(apply_color("Luhn Algorithm Step-by-Step Analysis", Colors.BOLD + Colors.CYAN, use_color))
    print(apply_color("=" * 50, Colors.DIM, use_color))

    number = input(apply_color("Enter a number to analyze: ", Colors.YELLOW, use_color)).strip()
    if not number.isdigit():
        print(apply_color("Input must contain only digits!", Colors.RED, use_color))
        pause_for_user()
        return

    digits = [int(d) for d in number]
    print("\n" + apply_color("Step-by-step analysis:", Colors.BOLD, use_color))
    print(apply_color("-" * 30, Colors.DIM, use_color))
    reversed_digits = digits[::-1]
    print(f"Original number: {' '.join(str(d) for d in digits)}")
    print(f"Number of digits: {len(digits)}")
    print(f"\n1. Reverse the number: {' '.join(str(d) for d in reversed_digits)}")

    doubled = []
    for idx, digit in enumerate(reversed_digits):
        if idx % 2 == 1:
            doubled_val = digit * 2
            doubled.append(doubled_val)
        else:
            doubled.append(digit)
    print("2. Double every second digit (starting from the second):")
    print(f"   After doubling: {' '.join(str(d) for d in doubled)}")

    adjusted = [d - 9 if d > 9 else d for d in doubled]
    print("3. Adjust numbers greater than 9 (subtract 9):")
    print(f"   After adjustment: {' '.join(str(d) for d in adjusted)}")

    total_sum = sum(adjusted)
    print(f"4. Sum all digits: {' + '.join(str(d) for d in adjusted)} = {total_sum}")
    print(f"5. Check if sum is divisible by 10: {total_sum} % 10 == {total_sum % 10}")

    if total_sum % 10 == 0:
        print(apply_color(f"\nResult: The number {number} is VALID ✅", Colors.GREEN, use_color))
    else:
        print(apply_color(f"\nResult: The number {number} is INVALID ❌", Colors.RED, use_color))
    pause_for_user()

# -------------------------
# Device filtering function
# -------------------------
def filter_devices(search_term: str, device_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter devices based on search term."""
    if not search_term:
        return device_list
    
    search_term = search_term.lower()
    filtered = []
    
    for device in device_list:
        name = device.get("name", "").lower()
        model = device.get("model", "").lower()
        tac = device.get("tac", "")
        
        if (search_term in name or 
            search_term in model or 
            search_term in tac or
            search_term in f"{name} {model}".lower()):
            filtered.append(device)
    
    return filtered

# -------------------------
# Main application
# -------------------------
def main(imeis_per_device: int = DEFAULT_IMEIS_PER_DEVICE, seed: Optional[int] = None, no_color: bool = False) -> None:
    """Main application entry point (interactive)."""
    use_color = (not no_color) and USE_COLOR_BY_DEFAULT
    
    # Show disclaimer on first run
    clear_terminal_screen()
    print(apply_color(DISCLAIMER, Colors.YELLOW + Colors.BOLD, use_color))
    print()
    pause_for_user("Press Enter to acknowledge and continue...")

    imei_generator = IMEIGenerator(seed)

    # Pre-generate groups
    device_groups: List[Dict[str, object]] = []
    for device in DEVICE_DATABASE:
        imei_list = imei_generator.generate_batch_imeis(device["tac"], imeis_per_device)
        device_groups.append({
            "tac": device["tac"], 
            "name": f"{device['name']} {device['model']}", 
            "imeis": imei_list,
            "type": device["type"].value
        })

    search_term = ""
    filtered_devices = device_groups

    while True:
        clear_terminal_screen()
        print(apply_color("IMEI Atlas", Colors.BOLD + Colors.CYAN, use_color))
        print(apply_color("=" * 44, Colors.DIM, use_color))
        print(apply_color(f"Author: {AUTHOR_NAME}", Colors.DIM, use_color))
        print(apply_color(f"Devices: {len(filtered_devices)}/{len(device_groups)} | IMEIs per device: {imeis_per_device}", Colors.DIM, use_color))
        if search_term:
            print(apply_color(f"Filter: '{search_term}'", Colors.YELLOW, use_color))
        print()

        for index, group in enumerate(filtered_devices, start=1):
            device_type = group.get("type", "Unknown")
            color = Colors.GREEN
            if device_type == "Smartphone":
                color = Colors.GREEN
            elif device_type == "Router":
                color = Colors.GREEN
            elif device_type == "Tablet":
                color = Colors.GREEN
            
            print(apply_color(f"{index:2d}. {group['name']} [{device_type}]", color, use_color))

        random_option_index = len(filtered_devices) + 1
        custom_tac_index = len(filtered_devices) + 2
        check_imei_index = len(filtered_devices) + 3
        luhn_index = len(filtered_devices) + 4
        all_export_index = len(filtered_devices) + 5
        search_index = len(filtered_devices) + 6
        help_index = len(filtered_devices) + 7

        print(apply_color(f"{random_option_index:2d}. Generate random IMEIs (different TACs)", Colors.CYAN, use_color))
        print(apply_color(f"{custom_tac_index:2d}. Generate IMEIs with custom TAC", Colors.CYAN, use_color))
        print(apply_color(f"{check_imei_index:2d}. Check your IMEI (Luhn)", Colors.CYAN, use_color))
        print(apply_color(f"{luhn_index:2d}. Luhn Algorithm Step-by-Step Analysis", Colors.CYAN, use_color))
        print(apply_color(f"{all_export_index:2d}. Export ALL IMEIs (multiple formats)", Colors.CYAN, use_color))
        print(apply_color(f"{search_index:2d}. Search/filter devices", Colors.CYAN, use_color))
        print(apply_color(f"{help_index:2d}. Help", Colors.CYAN, use_color))
        print()
        print(apply_color("Select a device number to view (q to quit).", Colors.DIM, use_color))

        choice = input(apply_color("Enter choice: ", Colors.YELLOW, use_color)).strip().lower()

        if choice in ("q", "quit", "exit"):
            print(apply_color("Goodbye.", Colors.DIM, use_color))
            return

        if choice == str(check_imei_index):
            run_imei_validator_prompt(use_color)
            continue

        if choice == str(luhn_index):
            run_luhn_step_by_step(use_color)
            continue

        if choice == str(all_export_index):
            clear_terminal_screen()
            print(apply_color("Export ALL IMEIs", Colors.BOLD + Colors.CYAN, use_color))
            print()
            print(apply_color("Available formats:", Colors.BOLD, use_color))
            print("1. Text (TXT)")
            print("2. CSV")
            print("3. JSON")
            print("4. SQLite Database")
            format_choice = input(apply_color("Select format [1-4]: ", Colors.YELLOW, use_color)).strip()
            
            format_map = {"1": "txt", "2": "csv", "3": "json", "4": "sqlite"}
            format_type = format_map.get(format_choice, "txt")
            
            default_filename = f"all_imeis_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.{format_type}"
            user_filename = input(apply_color(f"Enter output filename (enter for default: {default_filename}): ", Colors.YELLOW, use_color)).strip()
            filename_to_use = user_filename if user_filename else default_filename
            
            include_at = input(apply_color("Include MikroTik AT commands? (y/N): ", Colors.YELLOW, use_color)).strip().lower() == "y"
            
            try:
                # Use the original device_groups for export, not filtered_devices
                saved_file_path = save_all_devices_imeis_to_file(
                    device_groups,
                    output_dir=AT_OUTPUT_DIRECTORY if format_type != "sqlite" else DB_OUTPUT_DIRECTORY,
                    filename=filename_to_use,
                    include_timestamps=True,
                    include_at_commands=include_at,
                    format_type=format_type
                )
                print(apply_color(f"Saved ALL IMEIs to {saved_file_path}", Colors.GREEN, use_color))
            except Exception as exc:
                print(apply_color(f"Failed to save file: {exc}", Colors.RED, use_color))
            pause_for_user()
            continue

        if choice == str(search_index):
            search_term = input(apply_color("Enter search term (leave empty to clear): ", Colors.YELLOW, use_color)).strip()
            filtered_devices = filter_devices(search_term, device_groups)
            continue

        if choice == str(help_index):
            show_help_menu(use_color)
            continue

        if not choice.isdigit():
            print(apply_color("Please enter a number.", Colors.RED, use_color))
            pause_for_user()
            continue

        idx = int(choice) - 1

        # Random IMEIs option
        if idx == len(filtered_devices):
            try:
                random_count_input = input(apply_color("Enter number of random IMEIs to generate (default 10): ", Colors.YELLOW, use_color)).strip()
                random_count = 10 if not random_count_input else int(random_count_input)
                if random_count < 1 or random_count > MAX_IMEI_GENERATION:
                    print(apply_color(f"Count must be between 1 and {MAX_IMEI_GENERATION}. Using default 10.", Colors.RED, use_color))
                    random_count = 10
            except ValueError:
                print(apply_color("Invalid number. Using default 10.", Colors.RED, use_color))
                random_count = 10

            temp_group = {
                "tac": "Various",
                "name": "Random IMEIs (different TACs)",
                "imeis": imei_generator.generate_batch_imeis("Various", random_count)
            }
            should_quit = device_menu_view(temp_group, imei_generator, use_color)
            if should_quit:
                return
            continue

        # Custom TAC option
        if idx == len(filtered_devices) + 1:
            tac_input = input(apply_color("Enter the first 8 digits (TAC) of the IMEI: ", Colors.YELLOW, use_color)).strip()
            if not tac_input:
                print(apply_color("No TAC provided. Returning to menu.", Colors.RED, use_color))
                pause_for_user()
                continue
            if len(tac_input) != 8 or not tac_input.isdigit():
                print(apply_color("TAC must be exactly 8 digits. Returning to menu.", Colors.RED, use_color))
                pause_for_user()
                continue
            
            # Check if TAC is in our database
            known_tac = any(device["tac"] == tac_input for device in DEVICE_DATABASE)
            if not known_tac:
                print(apply_color("Warning: This TAC is not in the known device database.", Colors.YELLOW, use_color))
                confirm = input(apply_color("Continue anyway? (y/N): ", Colors.YELLOW, use_color)).strip().lower()
                if confirm != 'y':
                    continue
            
            imei_list = imei_generator.generate_batch_imeis(tac_input, imeis_per_device)
            temp_group = {"tac": tac_input, "name": f"Custom TAC: {tac_input}", "imeis": imei_list}
            should_quit = device_menu_view(temp_group, imei_generator, use_color)
            if should_quit:
                return
            continue

        # Normal device selection
        if idx < 0 or idx >= len(filtered_devices):
            print(apply_color("Invalid selection.", Colors.RED, use_color))
            pause_for_user()
            continue

        should_quit = device_menu_view(filtered_devices[idx], imei_generator, use_color)
        if should_quit:
            return

# -------------------------
# Unit Tests
# -------------------------
def run_tests():
    """Run basic validation tests."""
    print("Running IMEI validation tests...")
    
    # Test known valid IMEI
    test_imei = "354614441234567"  # This would need to be a real valid IMEI
    print(f"Testing IMEI validation: {test_imei}")
    print(f"Valid: {validate_imei(test_imei)}")
    
    # Test Luhn algorithm
    test_number = "7992739871"
    print(f"Testing Luhn checksum for {test_number}: {luhn_checksum_mod10(test_number + '0')}")
    
    print("Tests completed.")

# -------------------------
# CLI entrypoint
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IMEI Atlas - IMEI Generator & Validator")
    parser.add_argument("--count", type=int, default=DEFAULT_IMEIS_PER_DEVICE, help="IMEIs per device (default: %(default)s)")
    parser.add_argument("--seed", type=int, default=None, help="Optional integer seed for deterministic RNG")
    parser.add_argument("--no-color", action="store_true", help="Disable colored terminal output")
    parser.add_argument("--test", action="store_true", help="Run validation tests")
    args = parser.parse_args()

    if args.test:
        run_tests()
    else:
        try:
            main(imeis_per_device=args.count, seed=args.seed, no_color=args.no_color)
        except KeyboardInterrupt:
            print("\nInterrupted. Bye.")