# TeleBuddy

TeleBuddy is a robotic arm teleoperation system built for HackTheCoast. A set of potentiometers maps to servo motors on a 6-DOF arm; the ESP32-S3 firmware bridges the physical controls to the actuators over WiFi/UDP, and a Python simulation provides an optional 3D visualisation of the arm's end-effector.

---

## Hardware

| Component | Detail |
|---|---|
| Microcontroller | Freenove ESP32-S3 WROOM |
| Input devices | 6× potentiometers (raw ADC range 0–1024, mapped to 0–270°) |
| Actuators | 2× micro-servos, 1× Gobilda 1-turn servo, 1× Gobilda 5-turn servo |

### Pin assignments

| Signal | GPIO |
|---|---|
| Servo 1 (micro) | 14 |
| Servo 2 (micro) | 47 |
| Gobilda 1-turn  | 13 |
| Gobilda 5-turn  | 41 |

---

## Firmware

The firmware lives in `HackTheCoast_FW.zip` and is built with **PlatformIO** targeting the `freenove_esp32_s3_wroom` board using the Arduino framework.

### What it does

1. Connects to WiFi on boot.
2. Opens a **UDP socket on port 8888** and waits for incoming packets.
3. Parses each packet as JSON:
   ```json
   {"pots": [v0, v1, v2, v3, v4, v5]}
   ```
   where each value is in the range 0–270.
4. Maps `pots[3]` → Servo 1 angle and `pots[4]` → Servo 2 angle using Arduino's `map()` (0–270 → 0–180°).
5. Outputs debug information over UART at **115 200 baud**.

### Libraries

| Library | Purpose |
|---|---|
| `ESP32Servo` | PWM servo control |
| `WiFi` / `WiFiUdp` | Network connectivity |
| `ArduinoJson` | JSON deserialisation |
| `AccelStepper` / `Stepper` | Available for stepper support (unused in current build) |

### Building and flashing

```bash
# install PlatformIO CLI if needed
pip install platformio

# unzip the firmware, enter the project directory
unzip HackTheCoast_FW.zip
cd HackTheCoast

# build
pio run

# flash (connect ESP32-S3 via USB)
pio run --target upload

# open serial monitor
pio device monitor
```

### WiFi configuration

Edit `src/main.cpp` and update the SSID/password constants before flashing:

```cpp
const char* ssid     = "YourSSID";
const char* password = "YourPassword";
```

---

## Python simulation (UI)

A lightweight 3D visualisation runs on the host PC. It renders a virtual soldering-iron above a PCB and moves the iron in real time using **forward kinematics** fed from the same UDP potentiometer data.

### Files

| File | Purpose |
|---|---|
| `main.py` | Ursina 3D simulation (scene, iron, solder-pad detection) |
| `reciever.py` | UDP receiver – reads packets and exposes potentiometer values thread-safely |
| `forward_kin.py` | 6-DOF forward kinematics using 4×4 homogeneous matrices |
| `test_receiver.py` | Unit tests for serial parsing and kinematics |

### Setup

```bash
# create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# run the simulation
python main.py
```

### Runtime flow

```
Potentiometers → ESP32-S3 ADC
    → UDP/JSON (port 8888)
        → reciever.py (background thread)
            → forward_kin.py (6-DOF FK)
                → main.py (Ursina 3D scene)
```

---

## Running tests

```bash
python -m pytest test_receiver.py
```
