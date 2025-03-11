import os
import psycopg2
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

# Configure Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

app = Flask(__name__)
CORS(app)

# ✅ Correct DATABASE URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:yourpassword@postgres.railway.internal:5432/railway"
)


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# ✅ Fix API Route for Posting Data
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()

        # ✅ Validate JSON structure
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON payload"}), 400

        required_fields = [
            "account_number",
            "balance",
            "equity",
            "margin_used",
            "free_margin",
            "margin_level",
            "open_trades"
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        logger.debug(f"📥 Incoming Payload: {data}")

        # Extract values
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")
        last_update = datetime.utcnow()  # Store in UTC

        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or Update the record
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

        cur.execute(
            sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, last_update)
        )
        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Data stored successfully")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ✅ Fix API Route for Fetching Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # ✅ Remove inactive accounts (no update for 5+ minutes)
        timeout = datetime.utcnow() - timedelta(minutes=5)
        cur.execute("DELETE FROM accounts WHERE last_update < %s", (timeout,))
        conn.commit()

        cur.execute(
            "SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts"
        )
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
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
