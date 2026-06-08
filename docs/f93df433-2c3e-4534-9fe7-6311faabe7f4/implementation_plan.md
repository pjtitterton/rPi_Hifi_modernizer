# Implementation Plan: Acurus RL11 IR Scanner

This document details the design and implementation plan for a Python 3 command-line utility to brute-force scan an Acurus RL11 preamplifier for IR codes using the system's `ir-ctl` tool on a Raspberry Pi 3 B.

## Proposed Subdirectory

We will create a subdirectory for the project under the scratch directory:
- [acurus_ir_scanner](file:///C:/Users/pj.titterton/.gemini/antigravity/scratch/acurus_ir_scanner)

We recommend setting this subdirectory as the active workspace before running the script.

## User Review Required

> [!IMPORTANT]
> **Command Template & Customization**
> The `ir-ctl` tool natively transmits IR signals via a protocol and scancode syntax like `ir-ctl -d /dev/lirc0 -S <protocol>:<scancode>`. The prompt requests executing:
> `ir-ctl --send-system=rc5:<ADDRESS>:<COMMAND>`
>
> We will implement the scanner to support both the requested format and the standard `ir-ctl -S` (or a fully customizable template) to ensure maximum compatibility and robustness. By default, it will attempt the requested format:
> `ir-ctl --send-system=<protocol>:<ADDRESS>:<COMMAND>`

---

## Key Questions Answered

### 1. How do I make inputs to confirm that a command worked?
Because a human observer might have a reaction delay (or the motorized volume knob takes a moment to turn), the script might have fired 1 or 2 subsequent codes before you realize a code worked. To handle this elegantly:
- Every 5 iterations, or when a protocol shifts, the script pauses and prompts:
  `"Press Enter to continue to next block, or type 'FOUND' to lock in the current address parameters."`
- If you type `'FOUND'` (or press `Ctrl+C` to pause/interrupt execution at any time), the script enters an **Interactive Confirmation Menu**:
  1. **Show History:** Displays the last 5 transmitted commands with their index numbers.
  2. **Re-transmit/Test:** Let you enter an index to re-send that specific code to verify if it was the one that triggered the physical change.
  3. **Test Other Commands:** Let you test other command IDs (like Mute, Power, Volume Down) for the selected address/protocol combination to verify full control.
  4. **Lock In & Save:** Save the confirmed protocol and address to a file, or output it as a successful result and exit.

### 2. What is the interval of the commands?
- The default transmission interval is **0.7 seconds**, which gives motorized potentiometers and control relays sufficient time to react.
- This interval is fully configurable:
  - You can specify it at startup via the command line (e.g. `--delay 1.0` or `-d 1.0`).
  - You can adjust it on the fly from the interactive menu.

---

## Proposed Changes

### Component: Acurus IR Scanner Tool

#### [NEW] [scanner.py](file:///C:/Users/pj.titterton/.gemini/antigravity/scratch/acurus_ir_scanner/scanner.py)
This is the core interactive CLI Python script. It handles startup initialization, chip markings detection, protocol scoping/prioritization, interactive loop control, error handling, and subprocess execution.

##### Features & Mechanics:
1. **User Initialization Prompt:**
   - Prompt: `"Enter any markings, logos, or numbers found on the internal control IC chip (e.g., Philips, NEC, µPD), or press Enter to skip:"`
   - Prioritizes protocols based on the chip identifier (Philips/NEC/µPD/etc.).
   - Standard fallback priorities if skipped: **Philips RC5** -> **NEC** -> **Philips RC6**.

2. **Informed Scan Protocol Targets:**
   - **Philips RC5:**
     - Device Addresses: `16` (highest priority), followed by `0` through `31` (excluding `16`).
     - Command IDs: `16` (Volume Up), `17` (Volume Down), `12` (Power), `13` (Mute).
   - **NEC Protocol:**
     - Device Addresses: Focus heavily on common 8-bit audio addresses first (e.g., `0x01`, `0x02`, `0x08`, `0x0E`, `0x10`, `0x1F`, `0x40`, `0x5F`, `0x7F`, `0x80`, `0x81`, `0x83`, `0xD2`), followed by the remaining addresses from `0` to `255`.
     - Command IDs: Standard Volume Up/Down bit patterns (e.g., `0x16`, `0x1A`, `0x02`, `0x14`, `0x0E`, `0x15`, `0x0A`, `0x10`, `0x0F`, `0x05`, `0x40`, `0x45`, `0x01` and their matches/opposites for Volume Down).
   - **Philips RC6:**
     - Device Addresses: `16` (highest priority), followed by `0` through `255`.
     - Command IDs: `16` (Volume Up), `17` (Volume Down), `12` (Power), `13` (Mute).

3. **Interactive Looping Engine:**
   - Iterates through the scoped protocols and address-command matrices.
   - For each iteration, constructs and runs the `ir-ctl` command.
   - Prints status clearly to stdout with high readability (Protocol, Address, Command, Hex/Dec format).
   - Delays `0.7` seconds (configurable) between commands.
   - Every 5 iterations, or when a protocol shifts, prompts:
     `"Press Enter to continue to next block, or type 'FOUND' to lock in the current address parameters."`
   - If `'FOUND'` is typed, it enters the confirmation/backtracking menu.

4. **Exception & Error Handling:**
   - Catches `FileNotFoundError` if `ir-ctl` is missing.
   - Catches `subprocess.CalledProcessError` if the exit code is non-zero (e.g., permission issues, device busy).
   - Gracefully reports errors and asks the user whether to skip the step, retry, or pause.

---

## Verification Plan

### Automated/Local Tests
- Run unit tests to mock `subprocess.run` and verify that the prioritization queues and address ranges are correctly scoped based on different user inputs at startup.
- Validate argument parsing, config handling, and command execution logic via a dry-run mode (where `ir-ctl` commands are printed but not executed).

### Manual Verification
- Execute `python scanner.py --dry-run` to inspect CLI behavior and printing.
- Execute command with real `/dev/lirc0` on Raspberry Pi.
