import os
import psycopg2
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# ✅ Initialize Flask
app = Flask(__name__)
CORS(app)

# ✅ Setup Logging
logging.basicConfig(level=logging.DEBUG)

# ✅ Use Railway’s PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:eYyOaijFUdLBWDfxXDkQchLCxKVdYcUu@postgres.railway.internal:5432/railway")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as db_error:
        logging.error(f"❌ Database Connection Error: {str(db_error)}")
        return None

# ✅ Route: Receive MT4 Data
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()
        if not data:
            logging.error("❌ Received empty JSON payload.")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # ✅ Log the incoming payload
        logging.debug(f"📥 Incoming Payload: {json.dumps(data, indent=2)}")

        # ✅ Extract and validate fields
        try:
            account_number = int(data.get("account_number"))
            balance = float(data.get("balance", 0.0))
            equity = float(data.get("equity", 0.0))
            margin_used = float(data.get("margin_used", 0.0))
            free_margin = float(data.get("free_margin", 0.0))
            margin_level = float(data.get("margin_level", 0.0))
            open_trades = int(data.get("open_trades", 0))
        except ValueError as e:
            logging.error(f"❌ Data Type Error: {str(e)}")
            return jsonify({"error": "Invalid data format"}), 400

        if not account_number:
            logging.error("❌ Missing account_number field.")
            return jsonify({"error": "Missing account_number"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()

        # ✅ DEBUG: Check if account exists before updating
        cur.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
        existing_data = cur.fetchone()

        logging.debug(f"🔎 Existing Data for {account_number}: {existing_data}")

        sql_query = """
            INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades;
        """

        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))
        conn.commit()

        # ✅ Log success
        logging.info(f"✅ Data stored successfully for account: {account_number}")

        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200

    except psycopg2.Error as db_error:
        logging.error(f"❌ SQL Execution Error: {str(db_error)}")
        return jsonify({"error": "Database Error", "details": str(db_error)}), 500

    except Exception as e:
        logging.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Route: Retrieve Account Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts")
        accounts = cur.fetchall()
        cur.close()
        conn.close()

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
        logging.error(f"❌ Error in /api/accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Run the Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
