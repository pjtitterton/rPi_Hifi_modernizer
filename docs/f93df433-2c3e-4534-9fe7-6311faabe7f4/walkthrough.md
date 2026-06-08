# Walkthrough: Acurus RL11 IR Scanner

We have created the Python IR scanning utility for the Acurus RL11 preamplifier and initialized the Git repository in your chosen workspace folder:
- Project folder: [rPi_Hifi_modernizer](file:///C:/Users/pj.titterton/PJPythonMessaround/rPi_Hifi_modernizer)
- Primary script: [scanner.py](file:///C:/Users/pj.titterton/PJPythonMessaround/rPi_Hifi_modernizer/scanner.py)

---

## 1. Accomplished Work

1. **Repository Setup**: Cloned the empty `rPi_Hifi_modernizer` repository into your active python playground directory `C:\Users\pj.titterton\PJPythonMessaround`.
2. **Scanner Implementation**: Wrote the robust, interactive `scanner.py` command-line utility.
3. **Dry-Run Local Verification**: Verified the script's prioritization queue, the step-by-step block pausing mechanism, and the backtracking/interactive menu using a dry-run local test.
4. **Clean Workspace**: Removed the temporary folders from the scratch directory.

---

## 2. Script Capabilities

### Startup IC Chip Marking Priorities
- When launched, the script prompts:
  `Enter any markings, logos, or numbers found on the internal control IC chip...`
- Depending on the user input:
  - If **Philips** or **NXP** is provided, the queue priority is **RC5 -> RC6 -> NEC**.
  - If **NEC** or **µPD** is provided, the queue priority is **NEC -> RC5 -> RC6**.
  - If skipped, the script defaults to **RC5 -> NEC -> RC6**.

### Standardized Audio Mappings (1990s Engineering)
- **Philips RC5/RC6**: Addresses priority starts with `16` (Audio/Preamp standard), then scans `0` to `31`/`255`. Commands tested: `16` (Vol Up), `17` (Vol Down), `12` (Power), `13` (Mute).
- **NEC**: Addresses prioritized based on common 8-bit audio addresses (`0x01`, `0x02`, `0x08`, `0x0E`, `0x10`, `0x1F`, etc.), followed by the remaining `0` to `255` range. Commands tested: common volume up/down/power candidate codes.

### Interactive Confirmation & Backtracking Menu
Because motorized volume knobs have physical movement latency, the script might have fired 1 or 2 commands past the matching code before you notice the movement.
- **Block Pause**: Every 5 iterations (or on protocol change), the scan pauses. You can hit Enter to continue, type `FOUND`, or press `Ctrl+C` at any time to open the **Interactive Confirmation Menu**.
- **The Backtracking Menu** allows you to:
  - View the last 10 fired commands with their Protocol, Address, and Command ID.
  - Re-transmit a specific past code (e.g., `R 3`) to verify if it was the one that triggered the knob.
  - Test a custom command ID on the latest address (e.g., `T 12` to see if Mute or Power works).
  - Lock in the parameters (e.g., `F 3`) to write them to `acurus_found.json` and exit.

---

## 3. How to Execute the Script

### Option A: Local Dry Run (Windows / Local machine)
To test the scanning sequence and the interactive menu interface locally without requiring hardware or LIRC drivers, run with the `--dry-run` flag:

```powershell
# Run using your Anaconda Python interpreter
& "C:\Users\pj.titterton\Anaconda3\python.exe" C:\Users\pj.titterton\PJPythonMessaround\rPi_Hifi_modernizer\scanner.py --dry-run
```

### Option B: On the Raspberry Pi 3 B (Real Hardware Scan)
Deploy the script to your Pi. Make sure you have the LIRC interface and `v4l-utils` installed.

1. **Check or install `v4l-utils`**:
   ```bash
   sudo apt-get install v4l-utils
   ```
2. **Execute the scanner with default settings**:
   ```bash
   sudo python3 scanner.py
   ```
   *Note: Using `sudo` is recommended so the subprocess has permissions to read/write `/dev/lirc0` directly.*

3. **Configure custom parameters if needed**:
   ```bash
   # Custom lirc interface and delay:
   sudo python3 scanner.py --device /dev/lirc1 --delay 1.0 --block-size 10
   ```
