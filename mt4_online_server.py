from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Enable CORS for cross-origin requests
import psycopg2
import logging
import os
import json

# ✅ Initialize Flask App
app = Flask(__name__)
CORS(app)  # ✅ Allow API access from external origins

# ✅ Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Database Connection Function
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

# ✅ Ensure All Necessary Columns Exist in Database
def ensure_column_exists():
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        columns = [
            "margin_used FLOAT",
            "open_charts INT",
            "open_trades INT",
            "realized_pl_daily FLOAT",
            "realized_pl_weekly FLOAT",
            "realized_pl_monthly FLOAT",
            "realized_pl_yearly FLOAT",
            "floating_pl FLOAT"  # Previously "profit_loss"
        ]
        for col in columns:
            cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated successfully")
    except Exception as e:
        logger.error(f"❌ Database Schema Error: {str(e)}")

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # ✅ Read and sanitize raw request data
        raw_data = request.data.decode("utf-8", errors="replace").strip()
        logger.debug(f"📥 Raw Request Data: {repr(raw_data)}")  # Logs actual received JSON

        # ✅ Check if request contains JSON data
        if not request.is_json:
            logger.error(f"❌ Invalid Content-Type: {request.content_type}")
            return jsonify({"error": "Content-Type must be application/json"}), 415

        # ✅ Detect multiple JSON objects in one request
        if raw_data.count("{") > 1:
            logger.error(f"❌ JSON Decoding Error: Multiple JSON objects detected in request!")
            return jsonify({"error": "Multiple JSON objects detected. Wrap data in an array []"}), 400

        # ✅ Parse JSON safely
        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error: {str(e)}")
            return jsonify({"error": "Invalid JSON format. Ensure proper structure."}), 400

        # ✅ Validate required fields
        required_fields = ["account_number", "broker", "balance", "equity", "margin_used", "free_margin", "margin_percent", "floating_pl"]
        missing_fields = [field for field in required_fields if field not in json_data]

        if missing_fields:
            logger.error(f"❌ Missing required fields: {missing_fields}")
            return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400

        # ✅ Extract data fields
        broker = json_data.get("broker", "Unknown")
        account_number = json_data["account_number"]
        balance = json_data.get("balance", 0.0)
        equity = json_data.get("equity", 0.0)
        margin_used = json_data.get("margin_used", 0.0)
        free_margin = json_data.get("free_margin", 0.0)
        margin_percent = json_data.get("margin_percent", 0.0)
        floating_pl = json_data.get("floating_pl", 0.0)
        realized_pl_daily = json_data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = json_data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = json_data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = json_data.get("realized_pl_yearly", 0.0)
        open_charts = json_data.get("open_charts", 0)
        open_trades = json_data.get("open_trades", 0)

        # ✅ Insert or Update Database
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, floating_pl, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, open_charts, open_trades
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE 
            SET broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_percent = EXCLUDED.margin_percent,
                floating_pl = EXCLUDED.floating_pl,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                realized_pl_yearly = EXCLUDED.realized_pl_yearly,
                open_charts = EXCLUDED.open_charts,
                open_trades = EXCLUDED.open_trades;
        """, (
            broker, account_number, balance, equity, margin_used, free_margin,
            margin_percent, floating_pl, realized_pl_daily, realized_pl_weekly,
            realized_pl_monthly, realized_pl_yearly, open_charts, open_trades
        ))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully for account {account_number}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ✅ API Endpoint: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin,
                   margin_percent, floating_pl, realized_pl_daily, realized_pl_weekly,
                   realized_pl_monthly, realized_pl_yearly, open_charts, open_trades
            FROM accounts 
            ORDER BY floating_pl DESC;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [{
            "broker": row[0],
            "account_number": row[1],
            "balance": row[2],
            "equity": row[3],
            "margin_used": row[4],
            "free_margin": row[5],
            "margin_percent": row[6],
            "floating_pl": row[7],
            "realized_pl_daily": row[8],
            "realized_pl_weekly": row[9],
            "realized_pl_monthly": row[10],
            "realized_pl_yearly": row[11],
            "open_charts": row[12],
            "open_trades": row[13]
        } for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Initialize Database on Startup
if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
