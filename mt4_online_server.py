from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

# Automatically adds missing columns
def ensure_columns():
    columns = {
        "realized_pl_alltime": "NUMERIC(20,2) DEFAULT 0",
        "holding_fee_daily": "NUMERIC(20,2) DEFAULT 0",
        "holding_fee_weekly": "NUMERIC(20,2) DEFAULT 0",
        "holding_fee_monthly": "NUMERIC(20,2) DEFAULT 0",
        "holding_fee_yearly": "NUMERIC(20,2) DEFAULT 0",
        "holding_fee_alltime": "NUMERIC(20,2) DEFAULT 0",
        "deposits_alltime": "NUMERIC(20,2) DEFAULT 0",
        "withdrawals_alltime": "NUMERIC(20,2) DEFAULT 0",
        "autotrading": "BOOLEAN DEFAULT FALSE",
        "empty_charts": "INTEGER DEFAULT 0"
    }
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        for col, dtype in columns.items():
            cur.execute(f"""
                DO $$ BEGIN
                    BEGIN
                        ALTER TABLE accounts ADD COLUMN {col} {dtype};
                    EXCEPTION WHEN duplicate_column THEN
                        NULL;
                    END;
                END $$;
            """)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f"❌ Column Ensuring Error: {str(e)}")
    finally:
        conn.close()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = re.findall(r"\{.*?\}(?=\{|\Z)", raw_data)
        if not json_chunks:
            return jsonify({"error": "No valid JSON objects found"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()

        for chunk in json_chunks:
            try:
                json_data = json.loads(chunk)
                account_number = json_data.get("account_number")

                columns = [
                    "broker", "account_number", "balance", "equity", "margin_used", "free_margin",
                    "margin_percent", "profit_loss", "realized_pl_daily", "realized_pl_weekly",
                    "realized_pl_monthly", "realized_pl_yearly", "realized_pl_alltime",
                    "deposits_alltime", "withdrawals_alltime", "holding_fee_daily",
                    "holding_fee_weekly", "holding_fee_monthly", "holding_fee_yearly",
                    "holding_fee_alltime", "open_charts", "open_trades", "empty_charts", "autotrading"
                ]

                values = [json_data.get(col) for col in columns]

                placeholders = ", ".join(["%s"] * len(columns))
                columns_str = ", ".join(columns)

                update_stmt = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "account_number"])

                cur.execute(f"""
                    INSERT INTO accounts ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT (account_number) DO UPDATE SET {update_stmt}
                """, values)

                logger.info(f"✅ Data stored successfully for account {account_number}")

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON Decoding Error in chunk: {e}")

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Data processed successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM accounts ORDER BY profit_loss DESC;
        """)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        accounts_data = [dict(zip(colnames, row)) for row in rows]
        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    logger.error("❌ 404 Not Found")
    return jsonify({"error": "404 Not Found"}), 404

if __name__ == "__main__":
    ensure_columns()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
