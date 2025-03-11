import os
import psycopg2
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ✅ Use Railway's PostgreSQL database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@postgres.railway.internal:5432/railway")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    """Handles data sent from MT4 EA"""
    try:
        if not request.is_json:
            logger.error("❌ Request is not in JSON format")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        logger.debug(f"📥 Incoming Payload: {json.dumps(data, indent=2)}")

        # Validate required fields
        required_fields = [
            "account_number", "balance", "equity", "margin_used",
            "free_margin", "margin_level", "open_trades"
        ]
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        account_number = data["account_number"]
        balance = data["balance"]
        equity = data["equity"]
        margin_used = data["margin_used"]
        free_margin = data["free_margin"]
        margin_level = data["margin_level"]
        open_trades = data["open_trades"]

        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or update data for each account
        sql_query = """
            INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, last_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades,
                last_update = NOW();
        """
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))
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
    """Fetches all account data"""
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
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
