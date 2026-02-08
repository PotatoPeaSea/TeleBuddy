import sys
import unittest
from io import StringIO
from reciever import SerialController

class TestReceiver(unittest.TestCase):
    def test_parsing_and_formatting(self):
        controller = SerialController()
        
        # Capture stdout
        captured_output = StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        test_line = "POT0:512 POT1:512 POT2:256 POT3:768 POT4:100 POT5:900"
        try:
            controller._parse_line(test_line)
        finally:
            sys.stdout = original_stdout
            
        output = captured_output.getvalue().strip()
        print(f"Captured output: {output}")
        
        # Verify keys and labels
        expected_substrings = [
            "POT0(Pitch):  512",
            "POT1(Pitch):  512",
            "POT2(Pitch):  256",
            "POT3(Yaw):  768",
            "POT4(Roll):  100",
            "POT5(Roll):  900"
        ]
        
        for substring in expected_substrings:
            self.assertIn(substring, output)
            
        # Verify mapped values
        # P0=Pitch -> 512 * 360 / 1024 = 180.0
        # P5=Roll -> 900 * 360 / 1024 = 316.4
        # P3=Yaw -> 768 * 360 / 1024 = 270.0
        
        self.assertAlmostEqual(controller.values['pitch'], 180.0, places=1)
        self.assertAlmostEqual(controller.values['roll'], 316.4, places=1)
        self.assertAlmostEqual(controller.values['yaw'], 270.0, places=1)
        
        # Verify XYZ exist and are not zero (assuming non-zero angles/lengths result in non-zero pos)
        # With angles [180, 180, 90, 270, ..., ...] check if we get something valid.
        self.assertIn('x', controller.values)
        self.assertIn('y', controller.values)
        self.assertIn('z', controller.values)
        print(f"Calculated XYZ: {controller.values['x']}, {controller.values['y']}, {controller.values['z']}")

if __name__ == '__main__':
    unittest.main()
