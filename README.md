# Raspberry Pi Hi-Fi Modernizer (Acurus RL11)

A project to breathe new life into vintage audio gear. Specifically, this utilizes a Raspberry Pi 3 B equipped with an infrared (IR) transmitter to mimic the IR commands of the classic **Acurus RL11 Preamplifier** (whose remote controls are now rare or deceased) and integrate automation features like a 12V power trigger.

---

## 🛠️ Current Status: IR Scanner Utility

We have implemented an **informed IR code scanner** (`scanner.py`) to brute-force and locate the system codes for the Acurus RL11. It is designed around 1990s audio component engineering standards and structures the scans efficiently:
- **Philips RC5 / RC6** (standard preamplifier addresses like `16` and common commands like Volume Up, Volume Down, Power, Mute).
- **NEC Protocol** (standard 8-bit audio customer addresses and volume scancodes).

### How to Run the Scanner

#### Option 1: Dry-Run Mode (Local Testing)
To verify the scanning engine, priority queue generation, and the backtracking confirmation menu locally on Windows/macOS without hardware dependencies:
```powershell
python scanner.py --dry-run
```

#### Option 2: Live Hardware Scanning (On the Raspberry Pi)
Execute the script with root privileges to send signals directly to `/dev/lirc0`:
```bash
sudo python3 scanner.py
```

*Note: If the motorized volume knob twitches but the script moves past it due to mechanical latency, simply hit `Ctrl+C` or wait for the block-pause and select the **Interactive Backtracking Menu** to re-transmit and test recent commands.*

---

## 🚀 Roadmap: What is Next?

Here is the recommended development roadmap to complete the modernizer project:

### Phase 1: Physical Scan & Parameters Match
- [ ] **Hardware Setup**: Wire up the IR transmitter LED to a Raspberry Pi GPIO pin (via a driving transistor to maximize IR range) and configure the device overlay in `/boot/config.txt` (e.g., `dtoverlay=gpio-ir-tx,gpio_pin=17`).
- [ ] **Run the Scan**: Run the `scanner.py` script on the Pi, pointing it at the Acurus RL11.
- [ ] **Lock In Config**: Find the volume/power trigger commands, open the backtracking menu, and choose **FOUND** to save them to `acurus_found.json`.
- [ ] **Discover Aux Commands**: Once the correct Address and Protocol are found, use the custom transmission mode (`T <cmd>`) to map out secondary commands (such as Input Selectors: CD, Tuner, Aux, Tape).

### Phase 2: Core Control Daemon (`control.py`)
- [ ] Implement a lightweight Python daemon/script that reads `acurus_found.json` and exposes simple control functions (e.g., `volume_up()`, `volume_down()`, `power_toggle()`, `set_input(name)`).
- [ ] Wrap these commands in standard `ir-ctl` subprocess invocations.

### Phase 3: 12V Power Trigger Integration
- [ ] Preamplifiers often need to control the power state of external power amplifiers via a 12V trigger port.
- [ ] **Hardware**: Connect a relay module or Optocoupler to a Pi GPIO pin to switch a 12V power supply.
- [ ] **Logic**: Write a script to detect when the Acurus RL11 powers on (either by listening to the Acurus power LED state or by wrapping the IR power command) and toggle the GPIO pin to switch the 12V trigger high/low.

### Phase 4: Smart Home & Web Interface
- [ ] **API Endpoint**: Create a micro web server using Flask or FastAPI to trigger IR commands via HTTP (e.g., `GET /api/volume/up`).
- [ ] **Home Assistant / MQTT**: Integrate with Home Assistant using MQTT Discovery, allowing you to control your classic hi-fi preamp from your phone, smart speakers, or automation routines.

---

## 📂 Project Structure

- [scanner.py](scanner.py): The interactive IR brute-forcer and backtracking confirmation utility.
- `docs/f93df433-2c3e-4534-9fe7-6311faabe7f4/`: Archives of the design phases:
  - [chat_history.md](docs/f93df433-2c3e-4534-9fe7-6311faabe7f4/chat_history.md): Full design conversation log.
  - [implementation_plan.md](docs/f93df433-2c3e-4534-9fe7-6311faabe7f4/implementation_plan.md): Architectural design document.
  - [walkthrough.md](docs/f93df433-2c3e-4534-9fe7-6311faabe7f4/walkthrough.md): Script dry-run verification results.
