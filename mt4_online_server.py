import os
import psycopg2
import pytz
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ PostgreSQL Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Ensure the necessary tables exist before inserting data
def initialize_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                account_number BIGINT UNIQUE,
                balance FLOAT,
                equity FLOAT,
                margin_used FLOAT,
                free_margin FLOAT,
                margin_level FLOAT,
                open_trades INT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        ""
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                account_number BIGINT,
                balance FLOAT,
                equity FLOAT,
                margin_used FLOAT,
                free_margin FLOAT,
                margin_level FLOAT,
                open_trades INT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        ""
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("[ERROR] Database Initialization Failed:", str(e))

# ✅ API Route to Receive MT4 Data
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

        timestamp = datetime.now(pytz.utc)  # Store in UTC

        conn = get_db_connection()
        cur = conn.cursor()
        
        # ✅ Update `accounts` table with latest data
        cur.execute("""
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
        """, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))

        # ✅ Insert data into `history` table for tracking
        cur.execute("""
            INSERT INTO history (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API Route to Get Current Account Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp FROM accounts ORDER BY timestamp DESC")
        accounts = cur.fetchall()
        cur.close()
        conn.close()
        
        # ✅ Convert timestamps to Lebanon Time (EET/EEST)
        lebanon_tz = pytz.timezone("Asia/Beirut")
        accounts_list = [
            {
                "id": row[0],
                "account_number": row[1],
                "balance": row[2],
                "equity": row[3],
                "margin_used": row[4],
                "free_margin": row[5],
                "margin_level": row[6],
                "open_trades": row[7],
                "timestamp": row[8].astimezone(lebanon_tz).strftime("%I:%M:%S %p")
            }
            for row in accounts
        ]
        return jsonify({"accounts": accounts_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API Route to Get Historical Data
@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp FROM history ORDER BY timestamp DESC LIMIT 100")
        history = cur.fetchall()
        cur.close()
        conn.close()
        
        lebanon_tz = pytz.timezone("Asia/Beirut")
        history_list = [
            {
                "account_number": row[0],
                "balance": row[1],
                "equity": row[2],
                "margin_used": row[3],
                "free_margin": row[4],
                "margin_level": row[5],
                "open_trades": row[6],
                "timestamp": row[7].astimezone(lebanon_tz).strftime("%I:%M:%S %p")
            }
            for row in history
        ]
        return jsonify({"history": history_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    initialize_database()  # Ensure tables exist before running
    app.run(host="0.0.0.0", port=5000)
