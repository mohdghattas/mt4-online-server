import os
import psycopg2
import pytz
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

# Flask App Setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ✅ Use Railway PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

# ✅ Database Connection Function
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Auto-Fix Missing Column: Adds last_update if not found
def ensure_last_update_column():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if last_update column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='accounts' AND column_name='last_update';
        """)
        exists = cur.fetchone()

        if not exists:
            print("[INFO] Adding missing last_update column to accounts table...")
            cur.execute("ALTER TABLE accounts ADD COLUMN last_update TIMESTAMP DEFAULT NOW();")
            conn.commit()
            print("[SUCCESS] last_update column added successfully.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to modify accounts table: {e}")

# ✅ Call to Fix DB Schema Before Running API
ensure_last_update_column()

# ✅ Remove Old Accounts (Inactive for 30 Days)
def remove_stale_accounts(days=30):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cutoff = datetime.utcnow() - timedelta(days=days)
        cur.execute("DELETE FROM accounts WHERE last_update < %s RETURNING account_number;", (cutoff,))
        removed = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

        if removed:
            print(f"[INFO] Removed stale accounts: {[row[0] for row in removed]}")
        return len(removed)
    except Exception as e:
        print(f"[ERROR] Failed to remove stale accounts: {e}")
        return 0

# ✅ POST: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        print(f"[DEBUG] Incoming Raw Payload: {raw_data}")

        # Ensure the request contains JSON
        if request.content_type != "application/json":
            return jsonify({"error": "Invalid content type, expecting application/json"}), 400

        # Parse JSON Payload
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Extract Fields
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        # Validate Required Fields
        required_keys = {"account_number", "balance", "equity", "margin_used", "free_margin", "margin_level", "open_trades"}
        if not required_keys.issubset(data.keys()):
            print("[ERROR] Missing required fields in payload")
            return jsonify({"error": "Malformed payload, missing required fields"}), 400

        # ✅ Store timestamps in UTC
        timestamp = datetime.utcnow()

        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or Update Account Data
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

        # ✅ Remove old inactive accounts
        remove_stale_accounts(days=30)

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        print(f"[ERROR] Error in /api/mt4data: {e}")
        return jsonify({"error": str(e)}), 500

# ✅ GET: Fetch Accounts for Dashboard
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts ORDER BY last_update DESC")
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        # Convert to JSON Response
        accounts_list = [
            {
                "account_number": row[0],
                "balance": row[1],
                "equity": row[2],
                "margin_used": row[3],
                "free_margin": row[4],
                "margin_level": row[5],
                "open_trades": row[6],
            }
            for row in accounts
        ]

        return jsonify({"accounts": accounts_list}), 200

    except Exception as e:
        print(f"[ERROR] Error in /api/accounts: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
