import os
import psycopg2
import pytz
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ Use PostgreSQL database from Railway
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Ensure tables exist before inserting data
def initialize_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # ✅ Create the accounts table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            account_number BIGINT UNIQUE NOT NULL,
            balance DECIMAL(18,2) NOT NULL,
            equity DECIMAL(18,2) NOT NULL,
            margin_used DECIMAL(18,2) NOT NULL,
            free_margin DECIMAL(18,2) NOT NULL,
            margin_level DECIMAL(18,2) NOT NULL,
            open_trades INT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # ✅ Create the history table for tracking balance/equity over time
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            account_number BIGINT NOT NULL,
            balance DECIMAL(18,2) NOT NULL,
            equity DECIMAL(18,2) NOT NULL,
            margin_used DECIMAL(18,2) NOT NULL,
            free_margin DECIMAL(18,2) NOT NULL,
            margin_level DECIMAL(18,2) NOT NULL,
            open_trades INT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# ✅ Initialize database on startup
initialize_database()

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

        timestamp = datetime.now(pytz.utc)  # Always store in UTC

        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Store every balance update in the history table
        cur.execute("""
            INSERT INTO history (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))

        # ✅ Update latest values in the accounts table
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

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
                "balance": float(row[1]),
                "equity": float(row[2]),
                "margin_used": float(row[3]),
                "free_margin": float(row[4]),
                "margin_level": float(row[5]),
                "open_trades": row[6],
                "timestamp": row[7].astimezone(lebanon_tz).strftime("%I:%M:%S %p")
            }
            for row in history
        ]
        return jsonify({"history": history_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
