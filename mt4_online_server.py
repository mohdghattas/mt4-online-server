import os
import psycopg2
import pytz
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ Secure API Key (Replace with your own)
API_KEY = os.getenv("API_KEY", "your-secure-api-key")  # Set a secure API key

# ✅ PostgreSQL Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Middleware to enforce API authentication
def require_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 403  # Forbidden access
        return func(*args, **kwargs)
    return wrapper

@app.route("/api/mt4data", methods=["POST"])
@require_api_key  # 🔒 Protect this route
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

        timestamp = datetime.utcnow()  # Store timestamp in UTC

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
                timestamp = NOW();
        """
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/accounts", methods=["GET"])
@require_api_key  # 🔒 Protect this route
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp FROM accounts ORDER BY timestamp DESC")
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        lebanon_tz = pytz.timezone("Asia/Beirut")

        accounts_list = []
        for row in accounts:
            timestamp_str = str(row[8])
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            timestamp = timestamp.replace(tzinfo=pytz.utc).astimezone(lebanon_tz).strftime("%I:%M:%S %p")

            accounts_list.append({
                "id": row[0],
                "account_number": row[1],
                "balance": row[2],
                "equity": row[3],
                "margin_used": row[4],
                "free_margin": row[5],
                "margin_level": row[6],
                "open_trades": row[7],
                "timestamp": timestamp
            })

        return jsonify({"accounts": accounts_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
