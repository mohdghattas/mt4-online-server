import os
import psycopg2
import json
import logging
from datetime import datetime
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
    return psycopg2.connect(DATABASE_URL)

# ✅ Route: Receive MT4 Data
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()
        if not data:
            logging.error("Received empty JSON payload.")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # ✅ Log the incoming payload
        logging.debug(f"Incoming Payload: {json.dumps(data, indent=2)}")

        account_number = data.get("account_number")
        balance = float(data.get("balance", 0.0))
        equity = float(data.get("equity", 0.0))
        margin_used = float(data.get("margin_used", 0.0))
        free_margin = float(data.get("free_margin", 0.0))
        margin_level = float(data.get("margin_level", 0.0))
        open_trades = int(data.get("open_trades", 0))

        if not account_number:
            logging.error("Missing account_number field.")
            return jsonify({"error": "Missing account_number"}), 400

        # ✅ Store timestamps in UTC
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

        # ✅ Log success
        logging.info(f"✅ Data stored successfully for account: {account_number}")

        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200

    except psycopg2.Error as db_error:
        logging.error(f"❌ Database Error: {str(db_error)}")
        return jsonify({"error": "Database Error", "details": str(db_error)}), 500

    except Exception as e:
        logging.error(f"❌ API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Route: Retrieve Account Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts ORDER BY last_update DESC")
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
