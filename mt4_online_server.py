import os
import json
import psycopg2
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# ✅ Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

app = Flask(__name__)
CORS(app)

# ✅ Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ Fix: Improved API to Handle JSON Properly
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # ✅ Parse JSON with better error handling
        try:
            data = json.loads(raw_data.strip("\x00"))  # Remove any NULL characters
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decode Error: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # ✅ Extract account details
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        if not account_number:
            logger.error("❌ Missing 'account_number' in request payload")
            return jsonify({"error": "Missing account_number"}), 400

        # ✅ Store in database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades;
        """, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully: {data}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Fix `/api/accounts` to return correct data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_list = [{"account_number": row[0], "balance": row[1], "equity": row[2], "margin_used": row[3], "free_margin": row[4], "margin_level": row[5], "open_trades": row[6]} for row in accounts]

        return jsonify({"accounts": accounts_list}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
