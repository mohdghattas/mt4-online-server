import os
import psycopg2
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

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
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        logger.debug(f"📥 Incoming Payload: {data}")

        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        if not account_number:
            return jsonify({"error": "Missing account_number"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

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

        cur.execute(
            sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades)
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
