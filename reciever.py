import threading
import time
import sys
import serial
from serial.tools import list_ports
from forward_kin import calculate_tip_xy

# Dummy lengths for the arm segments (L1-L6)
DUMMY_LENGTHS = [10, 10, 10, 5, 5, 2]

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
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
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
        # Use the logic requested:
        # P0 = pitch, P1 = pitch, P2 = yaw, P3 = roll, P4 = yaw, P5 = yaw
        
        parts = line_str.split()
        parsed = {}
        for part in parts:
            if ":" in part:
                key, val = part.split(":", 1)
                try:
                    parsed[key] = int(val)
                except ValueError:
                    continue
        
        with self.lock:
            self.values["raw"] = parsed
            
            # Use P0 for pitch, P3 for roll, P2 for yaw as primary controls for now
            # scaling factor ~ 1024 / 360  (approx 2.84)
            
            p0 = parsed.get("POT0", 0) # Pitch
            p1 = parsed.get("POT1", 0) # Pitch
            p2 = parsed.get("POT2", 0) # Yaw
            p3 = parsed.get("POT3", 0) # Roll
            p4 = parsed.get("POT4", 0) # Yaw
            p5 = parsed.get("POT5", 0) # Yaw
            
            # Map raw values to degrees (0-360)
            self.values["pitch"] = p0 * 360 / 1024
            self.values["roll"]  = p3 * 360 / 1024  # P3 is Roll per request
            self.values["yaw"]   = p2 * 360 / 1024  # P2 is Yaw per request
            
            # Calculate tip position using forward kinematics
            # Angles list: [p0, p1, p2, p3, p4, p5] mapped as [Pitch, Pitch, Yaw, Roll, Yaw, Yaw]
            # Convert raw 0-1024 to degrees 0-360
            scaler = 360 / 1024
            angles_deg = [
                p0 * scaler,
                p1 * scaler,
                p2 * scaler,
                p3 * scaler,
                p4 * scaler,
                p5 * scaler
            ]
            
            x, y, z = calculate_tip_xy(angles_deg, DUMMY_LENGTHS)
            self.values["x"] = x
            self.values["y"] = y
            self.values["z"] = z
            
            # Print formatted output
            print(self._format_output(parsed))

    def _format_output(self, values):
        """Format potentiometer values into a readable string with labels."""
        # P0=pitch, P1=pitch, P2=yaw, P3=roll, P4=yaw, P5=yaw
        labels = {
            "POT0": "Pitch",
            "POT1": "Pitch",
            "POT2": "Yaw",
            "POT3": "Roll",
            "POT4": "Yaw",
            "POT5": "Yaw"
        }
        
        keys = [f"POT{i}" for i in range(6)]
        output_parts = []
        for k in keys:
            val = values.get(k, "----")
            label = labels.get(k, "")
            # Format: 'POT0(Pitch): 123'
            output_parts.append(f"{k}({label}): {str(val):>4}")
            
        return " | ".join(output_parts) + f" | XYZ: ({values.get('x', 0):.2f}, {values.get('y', 0):.2f}, {values.get('z', 0):.2f})"

    def get_orientation(self):
        with self.lock:
            return {
                "pitch": self.values["pitch"],
                "roll": self.values["roll"],
                "yaw": self.values["yaw"],
                "x": self.values["x"],
                "y": self.values["y"],
                "z": self.values["z"]
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
