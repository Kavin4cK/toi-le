#!/usr/bin/env python3
# crane_control.py — Nano (Theta) only

import serial
import time

NANO_PORT = "/dev/ttyUSB0"
BAUD      = 9600

def get_input(prompt):
    val = input(prompt).strip()
    if val == "" or val == "-":
        return None
    try:
        return float(val)
    except ValueError:
        print("  Invalid — skipping.")
        return None

def send_and_wait(ser, command, ack, label):
    ser.reset_input_buffer()
    ser.write((command + "\n").encode())
    print(f"  [{label}] sent: {command}")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(f"  [{label}] response: {line}")
        if ack in line:
            print(f"  [{label}] done")
            break

def main():
    print("\n=== Crane Controller — Theta (Rotation) ===")
    print("Positive = Clockwise | Negative = Anti-clockwise | Blank = Skip\n")

    theta = get_input("Rotation (θ) degrees: ")

    if theta is None:
        print("Nothing entered. Exiting.")
        return

    try:
        print(f"\nConnecting to Nano on {NANO_PORT}...")
        nano = serial.Serial(NANO_PORT, BAUD, timeout=30)
        time.sleep(2)
        nano.reset_input_buffer()
        print("Connected.\n")

        send_and_wait(nano, f"T{theta:.2f}", "T_DONE", "THETA")

        nano.close()
        print("\nDone.\n")

    except serial.SerialException as e:
        print(f"\nError: {e}")
        print("Run:  ls /dev/ttyUSB*  to check port name.")

if __name__ == "__main__":
    while True:
        main()
        again = input("Run again? (y/n): ").strip().lower()
        if again != "y":
            break