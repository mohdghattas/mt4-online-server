import os
import psycopg2
import pytz
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ Configure Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Use Railway's PostgreSQL database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        broker = data.get("broker")
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        free_margin = data.get("free_margin")
        profit_loss = data.get("profit_loss")

        if not account_number or not broker:
            return jsonify({"error": "Missing required fields"}), 400

        # ✅ Store timestamps in UTC
        timestamp = datetime.now(pytz.utc)

        conn = get_db_connection()
        cur = conn.cursor()
        sql_query = """
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss,
                timestamp = EXCLUDED.timestamp;
        """
        cur.execute(sql_query, (broker, account_number, balance, equity, free_margin, profit_loss, timestamp))
        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Data stored successfully")
        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT broker, account_number, balance, equity, free_margin, profit_loss FROM accounts ORDER BY timestamp DESC")
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_list = [
            {
                "broker": row[0],
                "account_number": row[1],
                "balance": row[2],
                "equity": row[3],
                "free_margin": row[4],
                "profit_loss": row[5]
            }
            for row in accounts
        ]
        return jsonify({"accounts": accounts_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
