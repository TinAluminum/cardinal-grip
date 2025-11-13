import serial
import time

PORT = "/dev/cu.usbserial-0001"  # your ESP32 port
BAUD = 115200

def main():
    print(f"Opening {PORT} at {BAUD} baud...")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # let ESP32 reset

    print("Reading FSR values (Ctrl+C to stop):")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(line)
        # tiny sleep to avoid going crazy fast
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
