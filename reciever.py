import threading
import time
import sys
import serial
from serial.tools import list_ports

class SerialController:
    def __init__(self, port=None, baud=115200):
        self.port = port
        self.baud = baud
        self.serial_connection = None
        self.running = False
        self.thread = None
        
        # Data storage - thread safe access should be considered if complex, 
        # but for simple atomic overwrites of a dict/list in Python it's often okay.
        # We'll use a lock to be safe.
        self.lock = threading.Lock()
        self.values = {
            "pitch": 0.0,
            "roll": 0.0,
            "yaw": 0.0,
            "raw": {}
        }
        
    def choose_port(self):
        """Interactive port selection."""
        ports = list(list_ports.comports())
        if not ports:
            print("No serial ports found.")
            return None
            
        print("Available ports:")
        for i, p in enumerate(ports):
            print(f"  {i}: {p.device} - {p.description}")
            
        try:
            selection = input("Select port index [0] (or press Enter for default): ")
            idx = int(selection) if selection else 0
        except ValueError:
            idx = 0
            
        if 0 <= idx < len(ports):
            return ports[idx].device
        return None

    def start(self):
        """Start the serial reader thread."""
        if not self.port:
            self.port = self.choose_port()
            
        if not self.port:
            print("No port selected. Running in Mock Mode.")
            return

        try:
            self.serial_connection = serial.Serial(self.port, self.baud, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            print(f"SerialController started on {self.port}")
        except Exception as e:
            print(f"Failed to open serial port: {e}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.serial_connection:
            self.serial_connection.close()

    def _read_loop(self):
        while self.running and self.serial_connection and self.serial_connection.is_open:
            try:
                line = self.serial_connection.readline()
                if not line:
                    continue
                
                try:
                    line_str = line.decode(errors="ignore").strip()
                except:
                    continue

                if "POT" in line_str:
                    self._parse_line(line_str)
                    
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(0.1)

    def _parse_line(self, line_str):
        parts = line_str.split()
        parsed = {}
        for part in parts:
            if ":" in part:
                key, val = part.split(":", 1)
                try:
                    parsed[key] = int(val)
                except ValueError:
                    continue
        
        # Map to Pitch/Roll/Yaw
        # Assuming P0 = pitch, P1 = pitch, p2 - yaw, p3- roll, p4 - yaw , p5 - yaw
        # Scaling factor: 2.49 (from original code's `int(val / 2.49)`)
        # Original code mapped 0-1023 (likely) to something generic.
        # We'll store raw values or mapped degrees. 
        # Let's clean it up to be 0-100 or -180 to 180 depending on the pot.
        # For now, precise mapping can be tuned.
        
        with self.lock:
            self.values["raw"] = parsed
            # Example mapping: simply storing the raw values for the game to interpret, 
            # or doing basic normalization here.
            # Let's normalize to 0-360 range for rotation if inputs are 0-1023
            # 1023 / 2.84 ~= 360
            
            p0 = parsed.get("POT0", 0)
            p1 = parsed.get("POT1", 0)
            p2 = parsed.get("POT2", 0)
            
            self.values["pitch"] = p0 * 360 / 1024
            self.values["roll"]  = p1 * 360 / 1024
            self.values["yaw"]   = p2 * 360 / 1024

    def get_orientation(self):
        with self.lock:
            return {
                "pitch": self.values["pitch"],
                "roll": self.values["roll"],
                "yaw": self.values["yaw"]
            }

if __name__ == "__main__":
    # Test stub
    controller = SerialController()
    controller.start()
    try:
        while True:
            print(controller.get_orientation())
            time.sleep(0.5)
    except KeyboardInterrupt:
        controller.stop()
