#!/usr/bin/env python3
# crane_control.py

import serial
import time
import threading

# ── Port config ──────────────────────────────────────────────────────────────
NANO_PORT  = "/dev/ttyUSB0"   # Theta  (Arduino Nano)
STM32_PORT = "/dev/ttyUSB1"   # Height + Radius (Nucleo)
BAUD       = 9600

def open_serial(port, baud=9600):
    s = serial.Serial(port, baud, timeout=30)
    time.sleep(2)  # wait for MCU reset
    s.reset_input_buffer()
    return s

def send_and_wait(ser, command, ack, label):
    ser.reset_input_buffer()
    ser.write((command + "\n").encode())
    print(f"  [{label}] sent: {command}")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"  [{label}] response: {line}")
        if ack in line:
            print(f"  [{label}] ✓ done")
            break

def get_input(prompt):
    """Returns float or None if user leaves blank."""
    val = input(prompt).strip()
    if val == "" or val == "-":
        return None
    try:
        return float(val)
    except ValueError:
        print("  Invalid — skipping.")
        return None

def main():
    print("\n=== Autonomous Crane Controller ===")
    print("Enter degrees for each axis.")
    print("Positive = Clockwise | Negative = Anti-clockwise | Blank = Skip\n")

    height = get_input("Height   (H) degrees: ")
    radius = get_input("Radius   (R) degrees: ")
    theta  = get_input("Rotation (θ) degrees: ")

    # Nothing entered
    if height is None and radius is None and theta is None:
        print("\nNothing entered. Exiting.")
        return

    print("\nOpening serial ports...")
    
    # Only open ports we actually need
    stm32 = None
    nano  = None

    try:
        if height is not None or radius is not None:
            stm32 = open_serial(STM32_PORT)
            print(f"  STM32 connected on {STM32_PORT}")

        if theta is not None:
            nano = open_serial(NANO_PORT)
            print(f"  Nano  connected on {NANO_PORT}")

        print("\nStarting motors...\n")

        threads = []

        # Theta runs in its own thread (parallel with STM32)
        if theta is not None:
            def run_theta():
                send_and_wait(nano, f"T{theta:.2f}", "T_DONE", "THETA")
            t = threading.Thread(target=run_theta)
            threads.append(t)
            t.start()

        # STM32: Height then Radius — sequential on same serial port
        if stm32 is not None:
            def run_stm32():
                if height is not None:
                    send_and_wait(stm32, f"H{height:.2f}", "H_DONE", "HEIGHT")
                if radius is not None:
                    send_and_wait(stm32, f"R{radius:.2f}", "R_DONE", "RADIUS")
            t = threading.Thread(target=run_stm32)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print("\n✓ All motors completed.\n")

    except serial.SerialException as e:
        print(f"\nSerial error: {e}")
        print("Check USB connections and port names.")

    finally:
        if stm32: stm32.close()
        if nano:  nano.close()

if __name__ == "__main__":
    while True:
        main()
        again = input("Run again? (y/n): ").strip().lower()
        if again != 'y':
            print("Bye.")
            break