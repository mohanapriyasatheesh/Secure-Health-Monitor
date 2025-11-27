# app.py  ← FINAL VERSION WITH WORKING EMAIL ALERTS
from flask import Flask, request, jsonify, render_template
import os
import json
import pickle
import time
import smtplib
import traceback
from phe import paillier
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# ==================== LOAD KEYS ====================
try:
    with open('keys/pubkey.json') as f:
        public_key = paillier.PaillierPublicKey(n=int(json.load(f)['n']))
    with open('keys/privkey.pkl', 'rb') as f:
        private_key = pickle.load(f)
    print("Keys loaded successfully")
except Exception as e:
    print("ERROR: Keys not found! Run: python keygen.py")
    exit(1)

# ==================== GLOBAL STORAGE ====================
aggregates = {}    # encrypted sum
counts = {}        # number of readings
last_alert = {}    # prevent spam (timestamp)

# ==================== THRESHOLDS ====================
THRESHOLDS = {
    'heart_rate': (60,100),
    'spo2': (95, 100),
    'temperature': (35.5, 38.0)
}

# ==================== EMAIL CONFIG ====================
EMAIL_USER = os.getenv('ALERT_EMAIL_USER')
EMAIL_PASS = os.getenv('ALERT_EMAIL_PASS')
ALERT_TO = os.getenv('ALERT_TO')

def send_alert(metric: str, avg: float):
    """Send email alert (only once every 5 minutes per metric)"""
    if not (EMAIL_USER and EMAIL_PASS and ALERT_TO):
        print("Email not configured in .env")
        return

    now = time.time()
    if metric in last_alert and now - last_alert[metric] < 300:  # 5 minutes cooldown
        return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        subject = f"HEALTH ALERT: {metric.replace('_', ' ').upper()} ABNORMAL"
        body = f"""
URGENT HEALTH ALERT

Metric: {metric.replace('_', ' ').title()}
Current Average: {avg:.2f}
Total Readings: {counts.get(metric, 0)}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Please check the patient immediately!

Dashboard: http://127.0.0.1:5000
        """.strip()

        msg = f"Subject: {subject}\n\n{body}"
        server.sendmail(EMAIL_USER, ALERT_TO, msg)
        server.quit()

        last_alert[metric] = now
        print(f"EMAIL ALERT SENT → {metric} = {avg:.2f}")

    except Exception as e:
        print(f"Failed to send email: {e}")

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pubkey')
def pubkey():
    return jsonify({"n": str(public_key.n)})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        metric = data.get('type')
        ciphertext = data.get('ciphertext')
        exponent = data.get('exponent', 0)

        if not metric or ciphertext is None:
            return jsonify({"error": "Missing fields"}), 400

        # Reconstruct encrypted number
        enc_num = paillier.EncryptedNumber(public_key, int(ciphertext), int(exponent))

        # Initialize if first time
        if metric not in aggregates:
            aggregates[metric] = public_key.encrypt(0)
            counts[metric] = 0

        # Homomorphic addition
        aggregates[metric] = aggregates[metric] + enc_num
        counts[metric] += 1

        # Decrypt current average
        total_plain = private_key.decrypt(aggregates[metric])
        scale = 10 if metric == 'temperature' else 1
        current_avg = total_plain / counts[metric] / scale

        print(f"Received → {metric}: {current_avg:.2f} (count: {counts[metric]})")

        # CHECK FOR ABNORMAL & SEND ALERT
        limits = THRESHOLDS.get(metric)
        if limits and (current_avg < limits[0] or current_avg > limits[1]):
            send_alert(metric, current_avg)

        return jsonify({"status": "ok", "avg": round(current_avg, 2)})

    except Exception as e:
        print("Upload error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def status():
    result = {}
    for metric in ['heart_rate', 'spo2', 'temperature']:
        if metric not in counts or counts[metric] == 0:
            result[metric] = {"count": 0, "avg": None, "status": "No data"}
        else:
            total = private_key.decrypt(aggregates[metric])
            scale = 10 if metric == 'temperature' else 1
            avg = round(total / counts[metric] / scale, 1)
            limits = THRESHOLDS.get(metric)
            status = "ABNORMAL" if limits and (avg < limits[0] or avg > limits[1]) else "Normal"
            result[metric] = {"count": counts[metric], "avg": avg, "status": status}
    return jsonify(result)

@app.route('/reset', methods=['POST'])
def reset():
    global aggregates, counts, last_alert
    aggregates.clear()
    counts.clear()
    last_alert.clear()
    print("All data reset")
    return jsonify({"status": "reset"})

# ==================== START SERVER ====================
if __name__ == '__main__':
    print("\nSecure Health Monitor STARTED")
    print("   Dashboard → http://127.0.0.1:5000")
    print("   Submit abnormal value (e.g. Heart Rate 180) → GET EMAIL ALERT!\n")
    app.run(host='127.0.0.1', port=5000, debug=True)