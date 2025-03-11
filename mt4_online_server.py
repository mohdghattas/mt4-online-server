import os
import psycopg2
import pytz
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# ✅ Configure Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ PostgreSQL Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres.railway.internal:5432/railway")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# ✅ API to Receive MT4 Data
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # ✅ Ensure Content-Type is JSON
        if request.content_type != "application/json":
            logger.error("❌ Invalid Content-Type: %s", request.content_type)
            return jsonify({"error": "Invalid Content-Type. Expected application/json"}), 400
        
        data = request.get_json()
        
        if not data:
            logger.error("❌ Invalid JSON Payload: Received empty data")
            return jsonify({"error": "Invalid JSON payload"}), 400
        
        logger.info(f"📥 Incoming Payload: {json.dumps(data, indent=4)}")

        # Extract & Validate Data
        try:
            account_number = int(data["account_number"])
            balance = float(data["balance"])
            equity = float(data["equity"])
            margin_used = float(data["margin_used"])
            free_margin = float(data["free_margin"])
            margin_level = float(data["margin_level"])
            open_trades = int(data["open_trades"])
        except (KeyError, ValueError) as e:
            logger.error(f"❌ Data Parsing Error: {e}")
            return jsonify({"error": "Invalid data format"}), 400
        
        # ✅ Store timestamps in UTC
        timestamp = datetime.now(pytz.utc)

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
                timestamp = EXCLUDED.timestamp;
        """
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades, timestamp))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data Stored Successfully for Account: {account_number}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
