#!/usr/bin/env python3
"""
Acurus RL11 IR Scanner
----------------------
A robust, interactive Python command-line utility for Raspberry Pi to scan
and brute-force Acurus RL11 preamplifier IR codes using the 'ir-ctl' tool.

Adheres to 1990s audio engineering priorities (Philips RC5, NEC, Philips RC6).
"""

import os
import sys
import time
import subprocess
import argparse
import collections
import json

# --- 1990s Audio Engineering Defaults ---
# Philips RC5: Address 16 is standard for Audio/Preamplifiers.
RC5_PRIORITY_ADDR = 16
RC5_ALL_ADDRS = [RC5_PRIORITY_ADDR] + [a for a in range(32) if a != RC5_PRIORITY_ADDR]
RC5_COMMANDS = [16, 17, 12, 13]  # 16: Vol Up, 17: Vol Down, 12: Power, 13: Mute

# NEC: Focus heavily on common 8-bit audio addresses.
NEC_PRIORITY_ADDRS = [0x01, 0x02, 0x08, 0x0E, 0x10, 0x1F, 0x40, 0x5F, 0x7F, 0x80, 0x81, 0x83, 0xD2, 0x00, 0xFF]
NEC_ALL_ADDRS = NEC_PRIORITY_ADDRS + [a for a in range(256) if a not in NEC_PRIORITY_ADDRS]
# Common NEC command candidates for Vol Up, Vol Down, Power, Mute
NEC_COMMANDS = [16, 17, 2, 3, 26, 27, 12, 13, 0x14, 0x15, 0x1A, 0x1B, 0x0E, 0x0F]

# Philips RC6: Address 16 is standard.
RC6_PRIORITY_ADDR = 16
RC6_ALL_ADDRS = [RC6_PRIORITY_ADDR] + [a for a in range(32) if a != RC6_PRIORITY_ADDR] + [a for a in range(32, 256)]
RC6_COMMANDS = [16, 17, 12, 13]

def get_command_label(protocol, command):
    """Returns a friendly description of the command function."""
    if protocol in ('rc5', 'rc6'):
        labels = {16: "Volume Up", 17: "Volume Down", 12: "Power", 13: "Mute"}
        return labels.get(command, f"Command {command}")
    elif protocol == 'nec':
        vol_up = [16, 2, 26, 0x14, 0x0E, 0x10, 0x40]
        vol_down = [17, 3, 27, 0x15, 0x0F, 0x11, 0x41]
        power_mute = [12, 13, 0x0C, 0x08, 0x09, 0x0D]
        if command in vol_up:
            return "Volume Up candidate"
        elif command in vol_down:
            return "Volume Down candidate"
        elif command in power_mute:
            return "Power/Mute candidate"
        else:
            return f"Command {command}"
    return f"Command {command}"

def fire_command(protocol, address, command, args):
    """Constructs and executes the ir-ctl command."""
    # Build template
    cmd_str = args.template.format(
        device=args.device,
        protocol=protocol,
        address=address,
        command=command
    )
    
    label = get_command_label(protocol, command)
    print(f"\n>>> [TRANSMITTING] Protocol: {protocol.upper()} | Address: {address} (0x{address:02X}) | {label}")
    print(f"    Command: {cmd_str}")
    
    if args.dry_run:
        print("    [DRY RUN] Skipping hardware transmission.")
        return True
        
    try:
        result = subprocess.run(cmd_str, shell=True, check=True, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        print(f"    [ERROR] The program/shell command could not be resolved.")
        print(f"            Ensure that the utility is installed and in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"            Stderr: {e.stderr.strip()}")
        
        err_msg = e.stderr.lower() if e.stderr else ""
        if "permission" in err_msg or "permitted" in err_msg or e.returncode == 1:
            print("            Tip: Run this script with 'sudo' to access /dev/lirc0.")
        elif "busy" in err_msg:
            print("            Tip: Stop any conflicting daemon (e.g., 'sudo systemctl stop lircd').")
        
        # Give user options in case of execution failure
        while True:
            choice = input("    [Prompt] [R]etry, [S]kip, or [P]ause & open menu? ").strip().upper()
            if choice == 'R':
                return fire_command(protocol, address, command, args)
            elif choice == 'S':
                return False
            elif choice == 'P':
                raise KeyboardInterrupt  # Triggers the interactive menu
            else:
                print("Invalid choice. Enter R, S, or P.")

def lock_in_parameters(item):
    """Saves confirmed parameters to a JSON file and outputs a success block."""
    filename = "acurus_found.json"
    data = {
        "protocol": item['protocol'],
        "address_dec": item['address'],
        "address_hex": f"0x{item['address']:02X}",
        "confirmed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print("\n" + "="*80)
    print("                     SUCCESS: IR PARAMETERS MATCHED!")
    print("="*80)
    print(f"  PROTOCOL: {item['protocol'].upper()}")
    print(f"  ADDRESS : {item['address']} (0x{item['address']:02X})")
    print(f"  COMMAND : {item['command']} (0x{item['command']:02X})")
    print("-" * 80)
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"  Successfully saved matched configuration to: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"  Warning: Could not save parameters to file: {e}")
    print("="*80 + "\n")

def interactive_menu(history, args, latest_item):
    """Displays the backtracking confirmation menu."""
    while True:
        print("\n" + "="*60)
        print("                INTERACTIVE CONFIRMATION MENU")
        print("="*60)
        
        if not history:
            print("  No transmission history recorded yet.")
        else:
            print("  Recently Fired Commands (most recent first):")
            print(f"  {'ID':<4} | {'Protocol':<8} | {'Address (Dec)':<14} | {'Address (Hex)':<14} | {'Command':<8} | {'Label':<20}")
            print("  " + "-" * 76)
            for item in reversed(history):
                proto = item['protocol']
                addr = item['address']
                cmd = item['command']
                h_id = item['history_id']
                lbl = get_command_label(proto, cmd)
                addr_hex = f"0x{addr:02X}"
                print(f"  [{h_id}] | {proto:<8} | {addr:<14} | {addr_hex:<12} | {cmd:<8} | {lbl:<20}")
        
        print("-" * 60)
        print("  Options:")
        print("    R <id>   - Re-transmit a recently fired command (e.g., 'R 1')")
        print("    T <cmd>  - Test a custom command ID on latest address/protocol (e.g., 'T 12')")
        print("    F <id>   - FOUND: Lock in and save parameters from a history ID (e.g., 'F 1')")
        print("    D <sec>  - Change transmission delay interval (e.g., 'D 0.5')")
        print("    C        - Continue scanning")
        print("    Q        - Quit / Exit scanner")
        print("-" * 60)
        
        try:
            user_input = input("Enter command: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting scanner.")
            sys.exit(0)
            
        if not user_input:
            continue
            
        parts = user_input.split()
        cmd_char = parts[0].upper()
        
        if cmd_char == 'C':
            print("Resuming scan...")
            return 'continue'
        elif cmd_char == 'Q':
            print("Exiting scanner.")
            sys.exit(0)
        elif cmd_char == 'D':
            if len(parts) < 2:
                print("Error: Specify delay in seconds. e.g. 'D 0.5'")
                continue
            try:
                new_val = float(parts[1])
                if new_val < 0:
                    raise ValueError
                args.delay = new_val
                print(f"Transmission delay set to {new_val} seconds.")
            except ValueError:
                print("Error: Delay must be a positive number.")
        elif cmd_char == 'R':
            if len(parts) < 2:
                print("Error: Specify history ID. e.g. 'R 1'")
                continue
            try:
                target_id = int(parts[1])
                target_item = next((item for item in history if item['history_id'] == target_id), None)
                if not target_item:
                    print(f"Error: History ID [{target_id}] not found.")
                    continue
                fire_command(target_item['protocol'], target_item['address'], target_item['command'], args)
            except ValueError:
                print("Error: History ID must be an integer.")
        elif cmd_char == 'T':
            if len(parts) < 2:
                print("Error: Specify command ID (0-255). e.g. 'T 12'")
                continue
            if not latest_item:
                print("Error: No latest transmission available.")
                continue
            try:
                custom_cmd = int(parts[1])
                if not (0 <= custom_cmd <= 255):
                    raise ValueError
                fire_command(latest_item['protocol'], latest_item['address'], custom_cmd, args)
            except ValueError:
                print("Error: Command ID must be an integer between 0 and 255.")
        elif cmd_char == 'F':
            if len(parts) < 2:
                print("Error: Specify history ID. e.g. 'F 1'")
                continue
            try:
                target_id = int(parts[1])
                target_item = next((item for item in history if item['history_id'] == target_id), None)
                if not target_item:
                    print(f"Error: History ID [{target_id}] not found.")
                    continue
                lock_in_parameters(target_item)
                sys.exit(0)
            except ValueError:
                print("Error: History ID must be an integer.")
        else:
            print(f"Unknown menu option: '{user_input}'. Please try again.")

def main():
    parser = argparse.ArgumentParser(
        description="Brute-force scan IR codes for an Acurus RL11 preamplifier using ir-ctl.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.path = "scanner.py"
    parser.add_argument("-d", "--device", default="/dev/lirc0", help="LIRC device interface path.")
    parser.add_argument("-t", "--delay", type=float, default=0.7, help="Delay interval between transmissions in seconds.")
    parser.add_argument("-b", "--block-size", type=int, default=5, help="Number of iterations per block before pausing.")
    parser.add_argument("--dry-run", action="store_true", help="Print transmission details without running ir-ctl.")
    parser.add_argument(
        "--template",
        default="ir-ctl -d {device} --send-system={protocol}:{address}:{command}",
        help="Command execution template string."
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("           Acurus RL11 IR Scanner & Brute-Forcer")
    print("="*60)
    print("  [Notice] If hardwiring Raspberry Pi GPIO to the Acurus IR receiver:")
    print("           1. Use a level-shifter/transistor/optocoupler circuit.")
    print("              Pi GPIO is 3.3V; Acurus circuitry is likely 5V.")
    print("           2. Direct baseband input (after TSOP demodulator) requires")
    print("              demodulated pulses. Use custom --template if needed.")
    print("="*60)
    
    # Step 1: Context Gathering
    try:
        chip_stamping = input(
            "Enter any markings, logos, or numbers found on the internal control IC chip\n"
            "(e.g., Philips, NEC, µPD), or press Enter to skip: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting scanner.")
        sys.exit(0)
        
    # Determine protocol priority
    if "philips" in chip_stamping or "nxp" in chip_stamping:
        protocol_order = ["rc5", "rc6", "nec"]
        print("\nPrioritizing Philips architecture based on chip markings: RC5 -> RC6 -> NEC")
    elif "nec" in chip_stamping or "µpd" in chip_stamping or "upd" in chip_stamping:
        protocol_order = ["nec", "rc5", "rc6"]
        print("\nPrioritizing NEC architecture based on chip markings: NEC -> RC5 -> RC6")
    else:
        protocol_order = ["rc5", "nec", "rc6"]
        print("\nNo matching markings detected. Using standard default order: RC5 -> NEC -> RC6")
        
    # Generate scanning queue
    queue = []
    for proto in protocol_order:
        if proto == "rc5":
            for addr in RC5_ALL_ADDRS:
                for cmd in RC5_COMMANDS:
                    queue.append((proto, addr, cmd))
        elif proto == "nec":
            for addr in NEC_ALL_ADDRS:
                for cmd in NEC_COMMANDS:
                    queue.append((proto, addr, cmd))
        elif proto == "rc6":
            for addr in RC6_ALL_ADDRS:
                for cmd in RC6_COMMANDS:
                    queue.append((proto, addr, cmd))
                    
    print(f"Total structured transmissions queued: {len(queue)}")
    print(f"Initial transmission delay: {args.delay} seconds")
    print(f"Block size (pause interval): {args.block_size} transmissions")
    if args.dry_run:
        print("*** RUNNING IN DRY RUN MODE (No hardware modifications will occur) ***")
    print("Press Ctrl+C at any time during scanning to open the interactive backtracking menu.")
    print("="*60)
    
    input("Press Enter to begin scanning...")
    
    # State tracking
    history = collections.deque(maxlen=10)
    history_counter = 0
    current_index = 0
    total_items = len(queue)
    
    while current_index < total_items:
        # Pause conditions: every block_size iterations OR when the protocol changes
        if current_index > 0:
            proto_changed = (queue[current_index][0] != queue[current_index - 1][0])
            block_reached = (current_index % args.block_size == 0)
            
            if proto_changed or block_reached:
                reason = "Protocol changed" if proto_changed else f"Block of {args.block_size} completed"
                print(f"\n--- PAUSED ({reason}) ---")
                try:
                    user_val = input(
                        "Press Enter to continue, type 'FOUND' to open confirmation menu, or 'Q' to quit: "
                    ).strip().upper()
                except (KeyboardInterrupt, EOFError):
                    user_val = 'FOUND'  # Fallback to menu on interrupt
                    
                if user_val == 'Q':
                    print("Exiting scanner.")
                    sys.exit(0)
                elif user_val == 'FOUND':
                    latest_item = history[-1] if history else None
                    interactive_menu(history, args, latest_item)
                    
        # Extract next scanning target
        proto, addr, cmd = queue[current_index]
        
        # Handle transmission and tracking
        try:
            success = fire_command(proto, addr, cmd, args)
            
            if success:
                history_counter += 1
                history.append({
                    "history_id": history_counter,
                    "protocol": proto,
                    "address": addr,
                    "command": cmd
                })
                
            # Configurable delay
            time.sleep(args.delay)
            current_index += 1
            
        except KeyboardInterrupt:
            # Handle user hitting Ctrl+C
            print("\n\n[PAUSED] Scan interrupted by user.")
            latest_item = history[-1] if history else None
            interactive_menu(history, args, latest_item)
            
    print("\nScan completed! No additional matching codes were processed.")

if __name__ == "__main__":
    main()
