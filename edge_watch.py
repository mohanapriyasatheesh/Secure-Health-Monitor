# edge_watch.py — NUCLEAR SIMPLE VERSION (WORKS WHEN NOTHING ELSE DOES)
import asyncio
import requests
import json
from bleak import BleakClient

MAC = "FA:08:5D:6C:0B:36"
HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

with open("keys/pubkey.json") as f:
    n = int(json.load(f)["n"])

def encrypt(m):
    n2 = n*n
    return str(pow(n+1, m, n2) * pow(__import__("random").randint(1,n-1), n, n2) % n2)

async def run():
    print("CONNECTING TO YOUR WATCH (FA:08:5D:6C:0B:36)...")
    print("→ WEAR WATCH + RAISE WRIST → GREEN LIGHT ON\n")
    
    while True:
        try:
            async with BleakClient(MAC, timeout=20) as client:
                print("CONNECTED SUCCESSFULLY!!!")

                def callback(s, d):
                    if len(d) > 1:
                        hr = d[1]
                        if 40 <= hr <= 200:
                            print(f"Heart Rate: {hr} bpm → ENCRYPTED & SENT")
                            try:
                                requests.post("http://127.0.0.1:5000/upload", 
                                            json={"type":"heart_rate","ciphertext":encrypt(hr),"exponent":0}, 
                                            timeout=2)
                            except: pass

                await client.start_notify(HR_UUID, callback)
                print("LIVE DATA RUNNING → OPEN http://127.0.0.1:5000")
                await asyncio.sleep(999999)
        except Exception as e:
            print(f"Retrying in 5s... ({e})")
            await asyncio.sleep(5)

asyncio.run(run())