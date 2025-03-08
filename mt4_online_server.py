import os
import json
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Use PostgreSQL from Railway
DATABASE_URL = "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway"

def initialize_database():
    print("[DEBUG] Initializing PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            account_number BIGINT UNIQUE,
            balance FLOAT,
            equity FLOAT,
            margin_used FLOAT,
            free_margin FLOAT,
            margin_level FLOAT,
            open_trades INT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("[DEBUG] Database initialized successfully.")

initialize_database()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="ignore").strip()
        print("[DEBUG] Raw Request Data:", raw_data)

        try:
            raw_data = raw_data.split("\x00")[0]
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            print("[ERROR] JSON Parsing Failed:", str(e))
            return jsonify({"error": "Invalid JSON format"}), 400

        print("[DEBUG] Parsed JSON:", data)

        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        if not account_number:
            print("[ERROR] Missing account_number")
            return jsonify({"error": "Missing account_number"}), 400

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM accounts WHERE account_number = %s", (account_number,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE accounts
                SET balance = %s, equity = %s, margin_used = %s, free_margin = %s, margin_level = %s, open_trades = %s, timestamp = CURRENT_TIMESTAMP
                WHERE account_number = %s
            ''', (balance, equity, margin_used, free_margin, margin_level, open_trades, account_number))
        else:
            cursor.execute('''
                INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))

        conn.commit()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        print("[DEBUG] Fetching account data from database...")

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("[DEBUG] No account data found.")
            return jsonify({"accounts": []}), 200

        accounts = [
            {
                "id": row[0],
                "account_number": row[1],
                "balance": row[2],
                "equity": row[3],
                "margin_used": row[4],
                "free_margin": row[5],
                "margin_level": row[6],
                "open_trades": row[7],
                "timestamp": row[8]
            }
            for row in rows
        ]

        print("[DEBUG] Returning account data:", accounts)
        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        print("[ERROR] Exception occurred while fetching accounts:", str(e))
        return jsonify({"error": "Failed to fetch account data"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("[DEBUG] Starting Flask on port:", port)
    app.run(host="0.0.0.0", port=port)
