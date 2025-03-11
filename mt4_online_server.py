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
DATABASE_URL = os.getenv("DATABASE_URL", "your_postgres_url")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        data = json.loads(raw_data.strip("\x00"))

        broker = data.get("broker", "Unknown Broker")
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        free_margin = data.get("free_margin")
        profit_loss = data.get("profit_loss")
        open_charts = data.get("open_charts")
        ea_names = data.get("ea_names")
        traded_pairs = data.get("traded_pairs")
        deposit = data.get("deposit")
        withdrawal = data.get("withdrawal")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, open_charts, ea_names, traded_pairs, deposit, withdrawal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss;
        """, (broker, account_number, balance, equity, free_margin, profit_loss, open_charts, ea_names, traded_pairs, deposit, withdrawal))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
