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

# ✅ Fix: Ensure the 'broker' column exists before inserting data
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS broker TEXT;")  # ✅ Add 'broker' column if missing
        cur.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS profit_loss FLOAT;")  # ✅ Add 'profit_loss' column if missing
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated: Added missing columns if they did not exist.")
    except Exception as e:
        logger.error(f"❌ Database schema update error: {str(e)}")

# ✅ Ensure the database has the correct columns before starting
ensure_column_exists()

# ✅ Fix: API to handle incoming JSON properly
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # ✅ Parse JSON while stripping NULL characters
        try:
            data = json.loads(raw_data.strip("\x00"))
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decode Error: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # ✅ Extract account details
        broker = data.get("broker", "Unknown Broker")  # Default to "Unknown Broker" if missing
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        free_margin = data.get("free_margin")
        profit_loss = data.get("profit_loss")

        if not account_number:
            logger.error("❌ Missing 'account_number' in request payload")
            return jsonify({"error": "Missing account_number"}), 400

        # ✅ Store in database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss;
        """, (broker, account_number, balance, equity, free_margin, profit_loss))
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
            SELECT broker, account_number, balance, equity, free_margin, profit_loss FROM accounts
        """)
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
                "profit_loss": row[5],
            } for row in accounts
        ]

        return jsonify({"accounts": accounts_list}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
