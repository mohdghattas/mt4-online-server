import os
import psycopg2
import pytz
import requests  # Required for Telegram notifications
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ✅ Use Railway PostgreSQL database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

# ✅ Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7785508845:AAFUKJCZdQ6MUTzkDXrANH-05O_1IjT3kWc"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # Replace with your actual Telegram chat ID

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        if not account_number:
            return jsonify({"error": "Missing account_number"}), 400

        # ✅ Store timestamps in UTC
        timestamp = datetime.now(pytz.utc)

        # ✅ Print debug logs for tracking
        print(f"[DEBUG] Incoming Data: {data}")

        conn = get_db_connection()
        cur = conn.cursor()

        sql_query = """
            INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades,
                timestamp = EXCLUDED.timestamp;
        """
        
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))
        conn.commit()

        # ✅ Print confirmation that data was saved
        print(f"[DEBUG] Data updated successfully for Account: {account_number}")

        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        print(f"[ERROR] Database Update Failed: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
