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

def ensure_columns():
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Create core table structure
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number INTEGER PRIMARY KEY,
                broker TEXT,
                balance NUMERIC(20,2),
                equity NUMERIC(20,2),
                free_margin NUMERIC(20,2),
                margin_percent NUMERIC(20,2),
                profit_loss NUMERIC(20,2),
                realized_pl_daily NUMERIC(20,2),
                realized_pl_weekly NUMERIC(20,2),
                realized_pl_monthly NUMERIC(20,2),
                realized_pl_yearly NUMERIC(20,2),
                open_charts INTEGER,
                open_trades INTEGER
            )
        """)
        
        # Add newer columns
        additional_columns = {
            "margin_used": "NUMERIC(20,2) DEFAULT 0",
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

        for col, dtype in additional_columns.items():
            cur.execute(f"""
                ALTER TABLE accounts 
                ADD COLUMN IF NOT EXISTS {col} {dtype}
            """)
        
        conn.commit()
        logger.info("✅ Database schema verified")
        
    except Exception as e:
        logger.error(f"❌ Database setup error: {str(e)}")
        conn.rollback()
    finally:
        if conn: conn.close()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        json_chunks = re.findall(r"\{.*?\}(?=\{|\Z)", raw_data)

        if not json_chunks:
            return jsonify({"error": "Invalid data format"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        for chunk in json_chunks:
            try:
                data = json.loads(chunk)
                columns = [
                    'broker', 'account_number', 'balance', 'equity', 'margin_used',
                    'free_margin', 'margin_percent', 'profit_loss', 'realized_pl_daily',
                    'realized_pl_weekly', 'realized_pl_monthly', 'realized_pl_yearly',
                    'realized_pl_alltime', 'deposits_alltime', 'withdrawals_alltime',
                    'holding_fee_daily', 'holding_fee_weekly', 'holding_fee_monthly',
                    'holding_fee_yearly', 'holding_fee_alltime', 'open_charts',
                    'open_trades', 'empty_charts', 'autotrading'
                ]
                values = [data.get(col) for col in columns]

                query = f"""
                    INSERT INTO accounts ({",".join(columns)})
                    VALUES ({",".join(["%s"]*len(columns))})
                    ON CONFLICT (account_number) DO UPDATE SET
                        {",".join([f"{col}=EXCLUDED.{col}" for col in columns if col != "account_number"])}
                """
                cur.execute(query, values)

            except json.JSONDecodeError:
                logger.error("Invalid JSON chunk: {chunk}")
        
        conn.commit()
        return jsonify({"message": "Data processed"}), 200

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({"error": "Server error"}), 500
    finally:
        if 'conn' in locals(): conn.close()

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                account_number, broker, balance, equity, free_margin,
                margin_percent, profit_loss, realized_pl_daily,
                realized_pl_weekly, realized_pl_monthly, realized_pl_yearly,
                open_charts, open_trades
            FROM accounts
            ORDER BY profit_loss DESC
        """)
        
        columns = [desc[0] for desc in cur.description]
        accounts = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        logger.debug(f"Returning {len(accounts)} accounts")
        return jsonify({"accounts": accounts})

    except Exception as e:
        logger.error(f"Fetch error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    ensure_columns()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
