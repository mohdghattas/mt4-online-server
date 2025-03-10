import os
import psycopg2
import pytz
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ✅ Initialize Flask App
app = Flask(__name__)
CORS(app)

# ✅ Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ PostgreSQL Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@postgres.railway.internal:5432/railway")

def get_db_connection():
    """ Creates a fresh connection to PostgreSQL database """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True  # ✅ Ensures all changes are saved instantly
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

# ✅ Route to Receive MT4 Data
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.get_json()
        
        # ✅ Log Incoming Data for Debugging
        logging.debug(f"Received Payload: {data}")

        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # ✅ Extract Data (Handling Edge Cases)
        try:
            account_number = data["account_number"]
            balance = data["balance"]
            equity = data["equity"]
            margin_used = data["margin_used"]
            free_margin = data["free_margin"]
            margin_level = data["margin_level"]
            open_trades = data["open_trades"]
        except KeyError as e:
            return jsonify({"error": f"Missing key: {str(e)}"}), 400

        if not account_number:
            return jsonify({"error": "Missing account_number"}), 400

        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        
        # ✅ Insert or Update Data
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

        # ✅ Execute & Log SQL Query
        cur.execute(sql_query, (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))
        logging.debug(f"SQL Executed: {sql_query}")
        logging.debug(f"Rows Affected: {cur.rowcount}")

        conn.commit()  # ✅ Ensure transaction is saved
        
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except psycopg2.DatabaseError as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.error(f"Error in /api/mt4data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Route to Get Account Data (Dashboard)
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("SELECT account_number, balance, equity, margin_used, free_margin, margin_level, open_trades FROM accounts")
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        # ✅ Format Data for API Response
        accounts_list = [
            {
                "account_number": row[0],
                "balance": row[1],
                "equity": row[2],
                "margin_used": row[3],
                "free_margin": row[4],
                "margin_level": row[5],
                "open_trades": row[6]
            }
            for row in accounts
        ]
        return jsonify({"accounts": accounts_list}), 200
    except Exception as e:
        logging.error(f"Error in /api/accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
