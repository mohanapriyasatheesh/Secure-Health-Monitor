"""
edge_manual_console.py
Manual input edge device (console version)
Works with your Flask + Paillier prototype.
Type values → encrypted on-the-fly → sent to server.
"""

import json
import requests
from phe import paillier
import os
from dotenv import load_dotenv

# Load environment variables (optional, only needed if you change URL)
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5000/upload")

# Load public key (same location as the rest of the project)
try:
    with open("keys/pubkey.json", "r") as f:
        key_data = json.load(f)
    public_key = paillier.PaillierPublicKey(n=int(key_data["n"]))
    print("Public key loaded successfully.")
except Exception as e:
    print(f"ERROR: Could not load public key → {e}")
    print("Run: python keygen.py first!")
    exit(1)

def encrypt_value(value: int):
    """Encrypt a plain integer using Paillier (same logic as browser & watch)"""
    enc = public_key.encrypt(value)
    return str(enc.ciphertext()), enc.exponent

def send_reading(metric: str, value: float, sensor_id: str = "console-manual"):
    """Scale → encrypt → POST to server"""
    if metric == "temperature":
        scaled = int(round(value * 10))   # 1 decimal precision (37.6 → 376)
    else:
        scaled = int(round(value))        # heart_rate & spo2 are integers

    ciphertext, exponent = encrypt_value(scaled)

    payload = {
        "sensor_id": sensor_id,
        "type": metric,
        "ciphertext": ciphertext,
        "exponent": exponent
    }

    try:
        r = requests.post(SERVER_URL, json=payload, timeout=3)
        r.raise_for_status()
        unit = "°C" if metric == "temperature" else "bpm" if metric == "heart_rate" else "%"
        print(f"Sent → {metric}: {value}{unit} (encrypted & sent) → Server {r.status_code}")
    except requests.RequestException as e:
        print(f"Failed to send {metric}: {e}")

def main():
    print("\nSecure Health Monitor — Manual Console Input")
    print("Type a value and press Enter. Leave blank to skip that metric.")
    print("Supported: heart_rate, spo2, temperature")
    print("Type 'quit' or press Ctrl+C to exit.\n")

    while True:
        try:
            hr = input("Heart Rate (bpm)    : ").strip()
            if hr.lower() in {"quit", "q", "exit"}:
                break
            spo2 = input("SpO₂ (%)            : ").strip()
            temp = input("Temperature (°C)    : ").strip()

            if not (hr or spo2 or temp):
                print("No values entered — try again.\n")
                continue

            if hr:
                hr_val = float(hr)
                if not 30 <= hr_val <= 220:
                    print("Warning: Heart rate looks unrealistic (30–220 bpm)")
                send_reading("heart_rate", hr_val)

            if spo2:
                spo2_val = float(spo2)
                if not 70 <= spo2_val <= 100:
                    print("Warning: SpO₂ usually 70–100%")
                send_reading("spo2", spo2_val)

            if temp:
                temp_val = float(temp)
                if not 30 <= temp_val <= 45:
                    print("Warning: Temperature usually 35–42°C")
                send_reading("temperature", temp_val)

            print("-" * 50)

        except ValueError:
            print("Invalid number — please enter numeric values.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()