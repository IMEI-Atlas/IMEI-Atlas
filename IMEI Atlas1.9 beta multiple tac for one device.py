#!/usr/bin/env python3
"""
IMEI Atlas - Single-file IMEI Generator & Validator (Multi-TAC support)

Features:
- Devices may have multiple TACs (list of 8-digit strings).
- Device view shows IMEIs grouped by TAC on the same page.
- --add-tac CLI edits this .py to append a new device entry (creates backup).
- --generate-at produces combined AT file (mikrotik/fiberhome/both).
- Export formats: txt, csv, json, sqlite.
- Luhn validation, safe generation caps, deterministic RNG seed option.

DISCLAIMER: Educational/testing only. Don't misuse IMEIs.
"""

from __future__ import annotations
import argparse
import os
import random
import secrets
import csv
import json
import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum

# -------------------------
# Config & constants
# -------------------------
AUTHOR_NAME: str = "IMEI Atlas (single-file)"
DEFAULT_IMEIS_PER_DEVICE: int = 3
DEFAULT_LTE_INTERFACE: str = "lte1"
USE_COLOR_BY_DEFAULT: bool = True
AT_OUTPUT_DIRECTORY: str = r"./exports"
DB_OUTPUT_DIRECTORY: str = r"./database"
MAX_IMEI_GENERATION: int = 1000  # Safety limit

DISCLAIMER = (
    "WARNING: This tool is for educational and testing purposes only. "
    "Misuse of IMEI numbers may violate laws in your jurisdiction.\n"
    "Use only on devices you own and have permission to modify."
)

# -------------------------
# Device DB (single-file)
# each entry's 'tac' can be a string or a list of strings
# -------------------------
class DeviceType(Enum):
    SMARTPHONE = "Smartphone"
    TABLET = "Tablet"
    ROUTER = "Router"
    HOTSPOT = "Hotspot"
    IOT = "IoT Device"
    OTHER = "Other"

# Example devices (mix of single and multi-tac examples)
DEVICE_DATABASE: List[Dict[str, Any]] = [
    {"tac": ["35006781","35010872","35052389","35091250","35110451","35461444","35500828"], "name": "iPhone", "model": "6 Pro Max", "type": DeviceType.SMARTPHONE},
    {"tac": "86600507", "name": "U60 PRO", "model": "MU5250", "type": DeviceType.ROUTER},
    {"tac": "35204553", "name": "Apple iPad Pro", "model": "13 m4 2024", "type": DeviceType.TABLET},
    {"tac": "35890743", "name": "Nighthawk M7 Pro", "model": "MR7400", "type": DeviceType.ROUTER},
    {"tac": "86278507", "name": "FiberHome", "model": "5G CPE Pro LG6851F ", "type": DeviceType.ROUTER},
    {"tac": "86073604", "name": "Mikrotik", "model": "5g ax", "type": DeviceType.ROUTER},
    {"tac": "86167907", "name": "ZTE", "model": "G5 ULTRA", "type": DeviceType.ROUTER},
    {"tac": ["35573167","35554513"], "name": "Samsung Galaxy", "model": "S24 Ultra", "type": DeviceType.SMARTPHONE},
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
    {"tac": "35986104", "name": "asuse", "model": "gane", "type": DeviceType.ROUTER},
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
    return text if not enabled else f"{code}{text}{Colors.RESET}"

# -------------------------
# Luhn algorithm utilities
# -------------------------
def luhn_checksum_mod10(number_string: str) -> int:
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
    if not (isinstance(first_14_digits, str) and first_14_digits.isdigit() and len(first_14_digits) == 14):
        raise ValueError("first_14_digits must be a 14-digit numeric string")
    mod = luhn_checksum_mod10(first_14_digits + "0")
    return str((10 - mod) % 10)

def validate_imei(imei_string: str) -> bool:
    return isinstance(imei_string, str) and len(imei_string) == 15 and imei_string.isdigit() and luhn_checksum_mod10(imei_string) == 0

# -------------------------
# IMEI Generator
# -------------------------
class IMEIGenerator:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))

    def generate_six_digit_serial(self) -> str:
        return f"{self.rng.randrange(0, 10**6):06d}"

    def generate_imei_from_tac(self, tac_8_digits: str) -> str:
        if not (isinstance(tac_8_digits, str) and tac_8_digits.isdigit() and len(tac_8_digits) == 8):
            raise ValueError("TAC must be exactly 8 digits")
        serial6 = self.generate_six_digit_serial()
        first14 = tac_8_digits + serial6
        check_digit = calculate_imei_check_digit(first14)
        return first14 + check_digit

    def generate_random_8digit_tac(self) -> str:
        return f"{self.rng.randrange(10**7, 10**8):08d}"

    def generate_completely_random_imei(self) -> str:
        tac = self.generate_random_8digit_tac()
        return self.generate_imei_from_tac(tac)

    def generate_batch_imeis(self, tac: Union[str, List[str]], count: int) -> Union[List[str], Dict[str, List[str]]]:
        if count > MAX_IMEI_GENERATION:
            raise ValueError(f"Cannot generate more than {MAX_IMEI_GENERATION} IMEIs at once")
        if isinstance(tac, list):
            out: Dict[str, List[str]] = {}
            for t in tac:
                if not (isinstance(t, str) and t.isdigit() and len(t) == 8):
                    raise ValueError(f"Invalid TAC in list: {t}")
                out[t] = [self.generate_imei_from_tac(t) for _ in range(count)]
            return out
        else:
            if tac == "Various":
                return [self.generate_completely_random_imei() for _ in range(count)]
            return [self.generate_imei_from_tac(tac) for _ in range(count)]

# -------------------------
# AT-command formatting
# -------------------------
def mikrotik_at_command_for_imei(imei: str, interface: str = DEFAULT_LTE_INTERFACE) -> str:
    return f'interface lte at-chat {interface} input="AT+EGMR=1,7,\\\"{imei}\\\""'

def fiberhome_at_command_for_imei(imei: str) -> str:
    return f'AT+EGMR=1,7,\"{imei}\"'

# -------------------------
# File utilities & exports (multi-TAC aware)
# -------------------------
def make_safe_filename(desired_name: str) -> str:
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ")
    return "".join((c if c in allowed_chars else "_") for c in desired_name).strip()

def save_at_commands_to_file(device_name: str, tac: str, imei_list: List[str],
                             output_dir: str = AT_OUTPUT_DIRECTORY,
                             include_both: Union[bool,str] = True,
                             interface: str = DEFAULT_LTE_INTERFACE) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    safe_name = make_safe_filename(device_name) or "device"
    file_path = Path(output_dir) / f"at_{safe_name}_{tac}.txt"
    with file_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# AT commands for {device_name} (TAC {tac})\n")
        fh.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
        fh.write(f"# {DISCLAIMER}\n\n")
        for imei in imei_list:
            if include_both in (True, "mikrotik", "both"):
                fh.write(mikrotik_at_command_for_imei(imei, interface) + "\n")
            if include_both in (True, "fiberhome", "both"):
                fh.write(fiberhome_at_command_for_imei(imei) + "\n")
        fh.write("\n# End of AT commands\n")
    return str(file_path.resolve())

def save_all_devices_imeis_to_file(
    device_groups: List[Dict[str, object]],
    output_dir: str = AT_OUTPUT_DIRECTORY,
    filename: Optional[str] = None,
    include_timestamps: bool = True,
    include_at_commands: bool = False,
    format_type: str = "txt"
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if filename:
        safe_filename = make_safe_filename(filename)
        if not safe_filename.endswith(f".{format_type}"):
            safe_filename = f"{safe_filename}.{format_type}"
    else:
        safe_filename = f"all_imeis_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.{format_type}"
    output_path = Path(output_dir) / safe_filename

    if format_type == "txt":
        with output_path.open("w", encoding="utf-8") as fh:
            fh.write("# IMEI Atlas - All devices export\n")
            if include_timestamps:
                fh.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
            fh.write(f"# Devices: {len(device_groups)}\n")
            fh.write(f"# {DISCLAIMER}\n\n")
            for group in device_groups:
                device_name = group.get("name", "Unknown Device")
                tacs = group.get("tacs", [])
                imeis_map: Dict[str, List[str]] = group.get("imeis", {})
                fh.write(f"Device: {device_name}\n")
                fh.write("-" * 60 + "\n")
                for tac_val in tacs:
                    fh.write(f"TAC: {tac_val}\n")
                    for imei_val in imeis_map.get(tac_val, []):
                        if include_at_commands:
                            at_cmd = mikrotik_at_command_for_imei(imei_val)
                            fh.write(f"{imei_val}    {at_cmd}\n")
                        else:
                            fh.write(f"{imei_val}\n")
                    fh.write("\n")
    elif format_type == "csv":
        with output_path.open("w", newline='', encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Device Name", "TAC", "IMEI", "AT Command" if include_at_commands else ""])
            for group in device_groups:
                device_name = group.get("name", "Unknown Device")
                imeis_map: Dict[str, List[str]] = group.get("imeis", {})
                for tac_val, imeis in imeis_map.items():
                    for imei_val in imeis:
                        if include_at_commands:
                            writer.writerow([device_name, tac_val, imei_val, mikrotik_at_command_for_imei(imei_val)])
                        else:
                            writer.writerow([device_name, tac_val, imei_val])
    elif format_type == "json":
        data = {
            "metadata": {
                "generated": datetime.utcnow().isoformat() + "Z",
                "device_count": len(device_groups),
                "disclaimer": DISCLAIMER
            },
            "devices": []
        }
        for group in device_groups:
            device_obj = {
                "name": group.get("name", "Unknown Device"),
                "tacs": group.get("tacs", []),
                "imeis": group.get("imeis", {})
            }
            if include_at_commands:
                # include sample at_commands per imei if requested
                at_map = {}
                for tac_val, imeis in device_obj["imeis"].items():
                    at_map[tac_val] = [mikrotik_at_command_for_imei(i) for i in imeis]
                device_obj["at_commands"] = at_map
            data["devices"].append(device_obj)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    elif format_type == "sqlite":
        Path(DB_OUTPUT_DIRECTORY).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(output_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS imeis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER,
                tac TEXT,
                imei TEXT NOT NULL UNIQUE,
                at_command TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices (id)
            )
        ''')
        conn.commit()
        for group in device_groups:
            device_name = group.get("name", "Unknown Device")
            cur.execute("INSERT INTO devices (name) VALUES (?)", (device_name,))
            device_id = cur.lastrowid
            imeis_map: Dict[str, List[str]] = group.get("imeis", {})
            for tac_val, imeis in imeis_map.items():
                for imei_val in imeis:
                    at_cmd = mikrotik_at_command_for_imei(imei_val) if include_at_commands else None
                    try:
                        cur.execute("INSERT OR IGNORE INTO imeis (device_id, tac, imei, at_command) VALUES (?, ?, ?, ?)",
                                    (device_id, tac_val, imei_val, at_cmd))
                    except sqlite3.IntegrityError:
                        # skip duplicates gracefully
                        continue
        conn.commit()
        conn.close()
    return str(output_path.resolve())

def generate_combined_at_file(device_groups: List[Dict[str, object]], output_path: str, which: str = "both", interface: str = DEFAULT_LTE_INTERFACE) -> str:
    Path(Path(output_path).parent).mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Combined AT commands ({which})\n")
        fh.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        for group in device_groups:
            device_name = group.get("name", "Unknown Device")
            imeis_map: Dict[str, List[str]] = group.get("imeis", {})
            fh.write(f"# Device: {device_name}\n")
            for tac_val, imeis in imeis_map.items():
                fh.write(f"# TAC: {tac_val}\n")
                for imei in imeis:
                    if which in ("mikrotik", "both"):
                        fh.write(mikrotik_at_command_for_imei(imei, interface) + "\n")
                    if which in ("fiberhome", "both"):
                        fh.write(fiberhome_at_command_for_imei(imei) + "\n")
                fh.write("\n")
    return str(Path(output_path).resolve())

# -------------------------
# Source editing: add device into this .py
# -------------------------
def add_device_to_source_file(tacs: List[str], name: str, model: str, type_str: str, source_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Insert a new device dict into DEVICE_DATABASE inside this source file.
    Creates timestamped backup first.
    """
    if source_path is None:
        source_path = globals().get("__file__") or os.path.abspath(sys.argv[0])
    source_file = Path(source_path)
    if not source_file.exists():
        return False, f"Source file not found: {source_file}"

    # Normalize type
    chosen_type = "OTHER"
    ts = type_str.strip().upper()
    for t in DeviceType:
        if t.name == ts:
            chosen_type = t.name
            break
    if chosen_type == "OTHER" and ts in ("IOT", "IOT DEVICE"):
        chosen_type = "IOT"

    # Read source
    content = source_file.read_text(encoding="utf-8")

    # Find insertion point: locate the DEVICE_DATABASE definition and its closing bracket
    start_marker = "DEVICE_DATABASE: List[Dict[str, Any]] = ["
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return False, "Could not locate DEVICE_DATABASE block in source."
    # find the closing bracket ']' that ends the list (search from start_idx)
    close_idx = content.find("\n]", start_idx)
    if close_idx == -1:
        # fallback: find the last ']' before next major section
        # try finding the pattern that follows (Terminal color helpers)
        follow_marker = "\n# -------------------------\n# Terminal color helpers"
        follow_idx = content.find(follow_marker, start_idx)
        if follow_idx == -1:
            return False, "Could not determine end of DEVICE_DATABASE block."
        close_idx = content.rfind("]", start_idx, follow_idx)
        if close_idx == -1:
            return False, "Could not determine end of DEVICE_DATABASE block."

    # Build new entry text: keep consistent 4-space indent
    # Format tac list as JSON-like Python list
    tacs_literal = "[" + ", ".join(f'"{t}"' for t in tacs) + "]" if len(tacs) > 1 else f'"{tacs[0]}"'
    new_entry = f'    {{"tac": {tacs_literal}, "name": "{name}", "model": "{model}", "type": DeviceType.{chosen_type}}},\n'

    # Backup
    backup_path = source_file.with_suffix(source_file.suffix + f".bak.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
    shutil.copy2(source_file, backup_path)

    # Insert before close_idx
    insert_idx = close_idx
    new_content = content[:insert_idx] + new_entry + content[insert_idx:]
    source_file.write_text(new_content, encoding="utf-8")
    return True, f"Inserted new device into source. Backup saved at: {backup_path}"

# -------------------------
# UI helpers & interactive view
# -------------------------
def clear_terminal_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def pause_for_user(message: str = "Press Enter to continue...") -> None:
    try:
        input(message)
    except KeyboardInterrupt:
        pass

def show_help_menu(use_color: bool) -> None:
    clear_terminal_screen()
    print(apply_color("IMEI Atlas - Help Menu", Colors.BOLD + Colors.CYAN, use_color))
    print(apply_color("=" * 40, Colors.DIM, use_color))
    print("Commands:")
    print("  a/mikrotik  - Show MikroTik AT commands (all TACs)")
    print("  f/fiberhome - Show FiberHome AT commands (all TACs)")
    print("  s/save      - Save AT commands to file (per TAC file)")
    print("  v/validate  - Validate IMEIs with Luhn algorithm")
    print("  r/regenerate - Regenerate IMEIs for all TACs of this device")
    print("  b/back      - Return to main menu")
    print("  q/quit      - Exit program")
    print()
    print(apply_color(DISCLAIMER, Colors.YELLOW, use_color))
    pause_for_user()

def device_menu_view(device_group: Dict[str, object], imei_generator: IMEIGenerator, use_color: bool) -> bool:
    """
    Show device IMEIs and accept commands.
    device_group contains:
      - 'name'
      - 'tacs': List[str]
      - 'imeis': Dict[tac] -> List[str]
    """
    while True:
        clear_terminal_screen()
        name = device_group.get("name", "Unknown Device")
        tacs = device_group.get("tacs", [])
        imeis_map: Dict[str, List[str]] = device_group.get("imeis", {})
        print(apply_color(f"Device: {name}", Colors.BOLD + Colors.CYAN, use_color))
        print(apply_color("-" * 44, Colors.DIM, use_color))

        # Print IMEIs grouped by TAC
        for tac in tacs:
            imei_list = imeis_map.get(tac, [])
            print(apply_color(f"TAC: {tac}  —  {len(imei_list)} IMEI(s)", Colors.BOLD + Colors.YELLOW, use_color))
            for idx, imei_value in enumerate(imei_list, start=1):
                color_code = Colors.GREEN if validate_imei(imei_value) else Colors.RED
                print(f"  {idx:2d}. {apply_color(imei_value, color_code, use_color)}")
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
            for tac, imei_list in imeis_map.items():
                for imei in imei_list:
                    print(mikrotik_at_command_for_imei(imei))
            print("\n/system reboot\n")
            pause_for_user()
            continue

        if cmd in ("f", "fiberhome"):
            print()
            print(apply_color("# FiberHome AT commands:", Colors.BOLD + Colors.CYAN, use_color))
            for tac, imei_list in imeis_map.items():
                for imei in imei_list:
                    print(fiberhome_at_command_for_imei(imei))
            print()
            pause_for_user()
            continue

        if cmd in ("s", "save"):
            # Save per TAC file
            include_both_resp = input(apply_color("Include both Mikrotik & FiberHome commands? (Y/n): ", Colors.YELLOW, use_color)).strip().lower()
            include_both = True if include_both_resp in ("", "y", "yes") else "mikrotik" if include_both_resp == "m" else "fiberhome"
            saved_files = []
            for tac, imei_list in imeis_map.items():
                saved = save_at_commands_to_file(name, tac, imei_list, output_dir=AT_OUTPUT_DIRECTORY, include_both=include_both)
                saved_files.append(saved)
            print(apply_color("Saved AT files:", Colors.GREEN, use_color))
            for sf in saved_files:
                print(sf)
            pause_for_user()
            continue

        if cmd in ("v", "validate"):
            print()
            header = f"{'TAC':10s} {'IMEI':16s} {'CHK':^4s} {'MOD':^4s} {'STATUS':>6s}"
            print(apply_color(header, Colors.BOLD + Colors.CYAN, use_color))
            for tac, imei_list in imeis_map.items():
                for imei in imei_list:
                    chk_digit = imei[-1]
                    mod_value = str(luhn_checksum_mod10(imei))
                    ok_text = "VALID" if validate_imei(imei) else "INVALID"
                    color_code = Colors.GREEN if ok_text == "VALID" else Colors.RED
                    print(f"{tac:10s} {imei:16s} {chk_digit:^4s} {mod_value:^4s} {apply_color(ok_text, color_code, use_color):>6s}")
            pause_for_user()
            continue

        if cmd in ("r", "regen", "regenerate"):
            try:
                new_count_input = input(apply_color(f"Enter new count per TAC (current: {len(next(iter(imeis_map.values()))) if imeis_map else 0}): ", Colors.YELLOW, use_color)).strip()
                if new_count_input:
                    new_count = int(new_count_input)
                else:
                    new_count = len(next(iter(imeis_map.values()))) if imeis_map else DEFAULT_IMEIS_PER_DEVICE
                if new_count < 1 or new_count > MAX_IMEI_GENERATION:
                    print(apply_color(f"Count must be between 1 and {MAX_IMEI_GENERATION}. Aborting.", Colors.RED, use_color))
                    pause_for_user()
                    continue
            except Exception:
                print(apply_color("Invalid number. Keeping current count.", Colors.RED, use_color))
                pause_for_user()
                continue

            try:
                for tac in tacs:
                    device_group["imeis"][tac] = imei_generator.generate_batch_imeis(tac, new_count)
                print(apply_color(f"Regenerated {new_count} IMEIs per TAC for this device.", Colors.GREEN, use_color))
            except Exception as e:
                print(apply_color(f"Error during regeneration: {e}", Colors.RED, use_color))
            pause_for_user()
            continue

        print(apply_color("Unknown command. Type 'h' for help.", Colors.YELLOW, use_color))
        pause_for_user()

# -------------------------
# Non-interactive helpers
# -------------------------
def run_imei_validator_prompt(use_color: bool) -> None:
    clear_terminal_screen()
    print(apply_color("IMEI VALIDATOR (Luhn Check)", Colors.BOLD + Colors.CYAN, use_color))
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

def run_luhn_step_by_step(use_color: bool) -> None:
    clear_terminal_screen()
    print(apply_color("Luhn Algorithm Step-by-Step Analysis", Colors.BOLD + Colors.CYAN, use_color))
    number = input(apply_color("Enter a number to analyze: ", Colors.YELLOW, use_color)).strip()
    if not number.isdigit():
        print(apply_color("Input must contain only digits!", Colors.RED, use_color))
        pause_for_user()
        return
    digits = [int(d) for d in number]
    print("\n" + apply_color("Step-by-step analysis:", Colors.BOLD, use_color))
    reversed_digits = digits[::-1]
    print(f"Original number: {' '.join(str(d) for d in digits)}")
    print(f"Number of digits: {len(digits)}")
    print(f"\n1. Reverse the number: {' '.join(str(d) for d in reversed_digits)}")
    doubled = []
    for idx, digit in enumerate(reversed_digits):
        if idx % 2 == 1:
            doubled.append(digit * 2)
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
# Main
# -------------------------
def main(imeis_per_device: int = DEFAULT_IMEIS_PER_DEVICE,
         seed: Optional[int] = None,
         no_color: bool = False,
         non_interactive_at: Optional[str] = None,
         at_output: Optional[str] = None,
         at_interface: str = DEFAULT_LTE_INTERFACE,
         add_tac_tuple: Optional[Tuple[List[str], str, str, str]] = None):
    use_color = (not no_color) and USE_COLOR_BY_DEFAULT

    clear_terminal_screen()
    print(apply_color(DISCLAIMER, Colors.YELLOW + Colors.BOLD, use_color))
    print()
    pause_for_user("Press Enter to acknowledge and continue...")

    imei_generator = IMEIGenerator(seed)

    # Pre-generate device_groups with tacs list and imeis mapping
    device_groups: List[Dict[str, object]] = []
    for device in DEVICE_DATABASE:
        tacs_raw = device.get("tac", [])
        if isinstance(tacs_raw, str):
            # allow '|' separated string as legacy
            tacs_list = [t.strip() for t in tacs_raw.split("|") if t.strip()]
        elif isinstance(tacs_raw, (list, tuple)):
            tacs_list = list(tacs_raw)
        else:
            tacs_list = []

        imeis_map: Dict[str, List[str]] = {}
        for tac_val in tacs_list:
            imeis_map[tac_val] = imei_generator.generate_batch_imeis(tac_val, imeis_per_device)  # returns list

        device_groups.append({
            "tacs": tacs_list,
            "name": f"{device.get('name','Unknown')} {device.get('model','')}".strip(),
            "imeis": imeis_map,
            "type": device.get("type").value if isinstance(device.get("type"), DeviceType) else str(device.get("type", "Unknown"))
        })

    # If add_tac_tuple provided, add to source and exit
    if add_tac_tuple:
        try:
            tacs_list, name_val, model_val, type_val = add_tac_tuple
            ok, msg = add_device_to_source_file(tacs_list, name_val, model_val, type_val)
            print(msg)
        except Exception as e:
            print(f"Failed to add TAC to source: {e}")
        return

    # If non-interactive AT generation requested
    if non_interactive_at:
        if not at_output:
            at_output = os.path.join(AT_OUTPUT_DIRECTORY, f"combined_at_{non_interactive_at}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.txt")
        try:
            saved = generate_combined_at_file(device_groups, at_output, which=non_interactive_at, interface=at_interface)
            print(f"Saved combined AT commands to: {saved}")
        except Exception as e:
            print(f"Failed to generate AT file: {e}")
        return

    # Interactive loop
    search_term = ""
    filtered_devices = device_groups

    while True:
        clear_terminal_screen()
        print(apply_color("IMEI Atlas", Colors.BOLD + Colors.CYAN, use_color))
        print(apply_color("=" * 44, Colors.DIM, use_color))
        print(apply_color(f"Author: {AUTHOR_NAME}", Colors.DIM, use_color))
        print(apply_color(f"Devices: {len(filtered_devices)}/{len(device_groups)} | IMEIs per TAC: {imeis_per_device}", Colors.DIM, use_color))
        if search_term:
            print(apply_color(f"Filter: '{search_term}'", Colors.YELLOW, use_color))
        print()

        for index, group in enumerate(filtered_devices, start=1):
            device_type = group.get("type", "Unknown")
            print(apply_color(f"{index:2d}. {group['name']} [{device_type}]", Colors.GREEN, use_color))

        random_option_index = len(filtered_devices) + 1
        custom_tac_index = len(filtered_devices) + 2
        check_imei_index = len(filtered_devices) + 3
        luhn_index = len(filtered_devices) + 4
        all_export_index = len(filtered_devices) + 5
        search_index = len(filtered_devices) + 6
        help_index = len(filtered_devices) + 7

        print(apply_color(f"{random_option_index:2d}. Generate random IMEIs (different TACs)", Colors.CYAN, use_color))
        print(apply_color(f"{custom_tac_index:2d}. Generate IMEIs with custom TAC(s)", Colors.CYAN, use_color))
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
            filtered_devices = [d for d in device_groups if search_term.lower() in d.get("name","").lower()] if search_term else device_groups
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
            temp_group = {"tacs": ["Various"], "name": "Random IMEIs (different TACs)", "imeis": {"Various": imei_generator.generate_batch_imeis("Various", random_count)}}
            should_quit = device_menu_view(temp_group, imei_generator, use_color)
            if should_quit:
                return
            continue

        # Custom TAC(s) option
        if idx == len(filtered_devices) + 1:
            tac_input = input(apply_color("Enter the TAC(s) (8 digits each). For multiple, separate with '|': ", Colors.YELLOW, use_color)).strip()
            if not tac_input:
                print(apply_color("No TAC provided. Returning to menu.", Colors.RED, use_color))
                pause_for_user()
                continue
            tac_list = [t.strip() for t in tac_input.split("|") if t.strip()]
            invalid = [t for t in tac_list if not (t.isdigit() and len(t) == 8)]
            if invalid:
                print(apply_color(f"Invalid TACs: {invalid}. Returning to menu.", Colors.RED, use_color))
                pause_for_user()
                continue
            imeis_map: Dict[str, List[str]] = {}
            for t in tac_list:
                imeis_map[t] = imei_generator.generate_batch_imeis(t, imeis_per_device)
            temp_group = {"tacs": tac_list, "name": f"Custom TAC(s): {','.join(tac_list)}", "imeis": imeis_map}
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
# Tests
# -------------------------
def run_tests():
    print("Running IMEI Atlas tests...")
    gen = IMEIGenerator(seed=1)
    imei = gen.generate_imei_from_tac("35461444")
    print(f"Generated IMEI: {imei} Valid? {validate_imei(imei)}")
    try:
        gen.generate_imei_from_tac("123")
    except ValueError as e:
        print(f"Expected error for invalid TAC: {e}")
    print("Tests complete.")

# -------------------------
# CLI entrypoint
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IMEI Atlas - IMEI Generator & Validator (single-file, multi-TAC)")
    parser.add_argument("--count", type=int, default=DEFAULT_IMEIS_PER_DEVICE, help="IMEIs per TAC (default: %(default)s)")
    parser.add_argument("--seed", type=int, default=None, help="Optional integer seed for deterministic RNG")
    parser.add_argument("--no-color", action="store_true", help="Disable colored terminal output")
    parser.add_argument("--test", action="store_true", help="Run quick tests")
    parser.add_argument("--generate-at", choices=["mikrotik", "fiberhome", "both"], help="Generate combined AT commands for all pre-generated IMEIs")
    parser.add_argument("--at-output", type=str, help="Output path for combined AT commands (used with --generate-at)")
    parser.add_argument("--at-interface", type=str, default=DEFAULT_LTE_INTERFACE, help="LTE interface name used for MikroTik AT commands")
    parser.add_argument("--add-tac", type=str, help="Add TAC/device into this python source: 'TAC1|TAC2,Name,Model,Type' (creates backup)")
    args = parser.parse_args()

    if args.test:
        run_tests()
        sys.exit(0)

    add_tuple = None
    if args.add_tac:
        parts = [p.strip() for p in args.add_tac.split(",", 3)]
        if len(parts) != 4:
            print("Invalid --add-tac format. Use: --add-tac 'TAC1|TAC2,Name,Model,Type'")
            sys.exit(1)
        tac_field = parts[0]
        tacs_list = [t.strip() for t in tac_field.split("|") if t.strip()]
        invalids = [t for t in tacs_list if not (t.isdigit() and len(t) == 8)]
        if invalids:
            print(f"Invalid TAC(s): {invalids}. Each TAC must be 8 digits.")
            sys.exit(1)
        add_tuple = (tacs_list, parts[1], parts[2], parts[3])

    try:
        main(
            imeis_per_device=args.count,
            seed=args.seed,
            no_color=args.no_color,
            non_interactive_at=args.generate_at,
            at_output=args.at_output,
            at_interface=args.at_interface,
            add_tac_tuple=add_tuple
        )
    except KeyboardInterrupt:
        print("\nInterrupted. Bye.")
