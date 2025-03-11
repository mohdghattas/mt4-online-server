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
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@postgres.railway.internal:5432/railway")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    """Handles data sent from MT4 EA"""
    try:
        # Log raw request data
        raw_data = request.data.decode("utf-8").strip("\x00")  # ✅ Remove null character
        logger.debug(f"📥 Raw Request Data (Processed): {raw_data}")

        # Convert to JSON
        data = json.loads(raw_data)  # ✅ Parse JSON safely

        # Validate required fields
        required_fields = [
            "account_number", "balance", "equity", "margin_used",
            "free_margin", "margin_level", "open_trades"
        ]
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Extract and convert data
        account_number = int(data["account_number"])
        balance = float(data["balance"])
        equity = float(data["equity"])
        margin_used = float(data["margin_used"])
        free_margin = float(data["free_margin"])
        margin_level = float(data["margin_level"])
        open_trades = int(data["open_trades"])

        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or update data
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

    except json.JSONDecodeError:
        logger.error("❌ Failed to decode JSON")
        return jsonify({"error": "Invalid JSON format"}), 400

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
