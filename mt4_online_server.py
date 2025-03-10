import os
import psycopg2
import pytz
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

# ✅ Database Connection Function
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Auto-Fix Missing last_update Column
def ensure_db_schema():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_update TIMESTAMP DEFAULT NOW();")
        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] Database schema verified.")
    except Exception as e:
        print(f"[ERROR] Failed to modify DB schema: {e}")

# ✅ Ensure DB is Properly Structured
ensure_db_schema()

# ✅ Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        print(f"[DEBUG] Incoming Payload: {raw_data}")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        timestamp = datetime.utcnow()

        conn = get_db_connection()
        cur = conn.cursor()

        sql_query = """
            INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, last_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades,
                last_update = EXCLUDED.last_update;
        """
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))
        conn.commit()
        cur.close()
        conn.close()

        print(f"[INFO] Account {account_number} updated successfully.")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        print(f"[ERROR] API error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
