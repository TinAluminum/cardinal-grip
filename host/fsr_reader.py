# host/fsr_reader.py

import serial
import time
from collections import deque


class FSRReader:
    """
    Reads integer ADC values from the ESP32 over USB serial.
    Expects one integer per line, as in esp32_fsr_serial.ino.
    """

    def __init__(self, port="/dev/cu.usbserial-0001", baud=115200,
                 smooth_window=5):
        self.port = port
        self.baud = baud
        self.smooth_window = smooth_window
        self.ser = serial.Serial(self.port, self.baud, timeout=1)
        time.sleep(2)  # let ESP32 reset
        self._window = deque(maxlen=self.smooth_window)

    def read_raw(self):
        """Return one raw int from serial, or None if no valid line."""
        line = self.ser.readline().decode(errors="ignore").strip()
        if not line:
            return None
        try:
            return int(line)
        except ValueError:
            return None

    def read(self):
        """Return a smoothed value (moving average) or None."""
        val = self.read_raw()
        if val is None:
            return None
        self._window.append(val)
        return int(sum(self._window) / len(self._window))

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    reader = FSRReader()
    print(f"Reading from {reader.port} at {reader.baud}...")
    try:
        while True:
            v = reader.read()
            if v is not None:
                print(v)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        reader.close()
