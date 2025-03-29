from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psycopg2
import logging
import os
import json
import re
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSocket support

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_tables():
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot create tables: No database connection")
        return
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                broker TEXT NOT NULL,
                account_number BIGINT PRIMARY KEY,
                balance DOUBLE PRECISION DEFAULT 0,
                equity DOUBLE PRECISION DEFAULT 0,
                margin_used DOUBLE PRECISION DEFAULT 0,
                free_margin DOUBLE PRECISION DEFAULT 0,
                margin_percent DOUBLE PRECISION DEFAULT 0,
                profit_loss DOUBLE PRECISION DEFAULT 0,
                realized_pl_daily DOUBLE PRECISION DEFAULT 0,
                realized_pl_weekly DOUBLE PRECISION DEFAULT 0,
                realized_pl_monthly DOUBLE PRECISION DEFAULT 0,
                realized_pl_yearly DOUBLE PRECISION DEFAULT 0,
                realized_pl_alltime DOUBLE PRECISION DEFAULT 0,
                deposits_alltime DOUBLE PRECISION DEFAULT 0,
                withdrawals_alltime DOUBLE PRECISION DEFAULT 0,
                holding_fee_daily DOUBLE PRECISION DEFAULT 0,
                holding_fee_weekly DOUBLE PRECISION DEFAULT 0,
                holding_fee_monthly DOUBLE PRECISION DEFAULT 0,
                holding_fee_yearly DOUBLE PRECISION DEFAULT 0,
                holding_fee_alltime DOUBLE PRECISION DEFAULT 0,
                open_charts INTEGER DEFAULT 0,
                empty_charts INTEGER DEFAULT 0,
                open_trades INTEGER DEFAULT 0,
                autotrading BOOLEAN DEFAULT FALSE,
                swap_daily DOUBLE PRECISION DEFAULT 0,
                swap_weekly DOUBLE PRECISION DEFAULT 0,
                swap_monthly DOUBLE PRECISION DEFAULT 0,
                swap_yearly DOUBLE PRECISION DEFAULT 0,
                swap_alltime DOUBLE PRECISION DEFAULT 0,
                deposits_daily DOUBLE PRECISION DEFAULT 0,
                deposits_weekly DOUBLE PRECISION DEFAULT 0,
                deposits_monthly DOUBLE PRECISION DEFAULT 0,
                deposits_yearly DOUBLE PRECISION DEFAULT 0,
                withdrawals_daily DOUBLE PRECISION DEFAULT 0,
                withdrawals_weekly DOUBLE PRECISION DEFAULT 0,
                withdrawals_monthly DOUBLE PRECISION DEFAULT 0,
                withdrawals_yearly DOUBLE PRECISION DEFAULT 0,
                prev_day_pl DOUBLE PRECISION DEFAULT 0,
                prev_day_holding_fee DOUBLE PRECISION DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_accounts_account_number ON accounts (account_number);
            CREATE INDEX IF NOT EXISTS idx_accounts_broker ON accounts (broker);
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id TEXT PRIMARY KEY,
                sort_state JSON,
                is_numbers_masked BOOLEAN DEFAULT FALSE,
                gmt_offset INTEGER DEFAULT 3,
                period_resets JSON,
                main_refresh_rate INTEGER DEFAULT 5,
                critical_margin INTEGER DEFAULT 0,
                warning_margin INTEGER DEFAULT 500,
                is_dark_mode BOOLEAN DEFAULT FALSE,
                mask_timer TEXT DEFAULT '300',
                font_size TEXT DEFAULT '14',
                notes JSON,
                broker_offsets JSON DEFAULT '{"Raw Trading Ltd": -5, "Swissquote": -1, "XTB International": -6}',
                alert_thresholds JSON DEFAULT '{"equity": 500, "profit_loss": -1000, "margin_percent": 20}'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                account_number BIGINT,
                balance DOUBLE PRECISION,
                equity DOUBLE PRECISION,
                margin_used DOUBLE PRECISION,
                free_margin DOUBLE PRECISION,
                margin_level DOUBLE PRECISION,
                open_trade INTEGER,
                profit_loss DOUBLE PRECISION,
                open_charts INTEGER,
                deposit_withdrawal DOUBLE PRECISION,
                margin_percent DOUBLE PRECISION,
                realized_pl_daily DOUBLE PRECISION,
                realized_pl_weekly DOUBLE PRECISION,
                realized_pl_monthly DOUBLE PRECISION,
                realized_pl_yearly DOUBLE PRECISION,
                autotrading BOOLEAN,
                empty_charts INTEGER,
                deposits_alltime DOUBLE PRECISION,
                withdrawals_alltime DOUBLE PRECISION,
                realized_pl_alltime DOUBLE PRECISION,
                holding_fee_daily DOUBLE PRECISION,
                broker TEXT,
                traded_pairs TEXT,
                open_pairs_charts TEXT,
                ea_names TEXT,
                snapshot_time TIMESTAMP WITH TIME ZONE,
                last_update TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_history_snapshot_time ON history (snapshot_time);
        """)
        conn.commit()
        logger.info("Tables created with indexes")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
    finally:
        cur.close()
        conn.close()

def clean_json_string(raw_data):
    decoded = raw_data.decode("utf-8", errors="replace")
    cleaned = re.sub(r'[^\x20-\x7E]', '', decoded)
    return cleaned.strip()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = clean_json_string(request.data)
        logger.debug(f"Raw Request Data: {raw_data}")
        json_data = json.loads(raw_data)
        required_fields = [
            "broker", "account_number", "balance", "equity", "margin_used",
            "free_margin", "margin_percent", "profit_loss", "realized_pl_daily",
            "realized_pl_weekly", "realized_pl_monthly", "realized_pl_yearly",
            "realized_pl_alltime", "deposits_alltime", "withdrawals_alltime",
            "holding_fee_daily", "holding_fee_weekly", "holding_fee_monthly",
            "holding_fee_yearly", "holding_fee_alltime", "open_charts",
            "empty_charts", "open_trades", "autotrading", "swap_daily",
            "swap_weekly", "swap_monthly", "swap_yearly", "swap_alltime",
            "deposits_daily", "deposits_weekly", "deposits_monthly",
            "deposits_yearly", "withdrawals_daily", "withdrawals_weekly",
            "withdrawals_monthly", "withdrawals_yearly", "prev_day_pl",
            "prev_day_holding_fee"
        ]
        for field in required_fields:
            if field not in json_data:
                logger.error(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400
        json_data["autotrading"] = json_data["autotrading"] == "true" or json_data["autotrading"] == True
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                deposits_alltime, withdrawals_alltime, holding_fee_daily,
                holding_fee_weekly, holding_fee_monthly, holding_fee_yearly,
                holding_fee_alltime, open_charts, empty_charts, open_trades,
                autotrading, swap_daily, swap_weekly, swap_monthly, swap_yearly,
                swap_alltime, deposits_daily, deposits_weekly, deposits_monthly,
                deposits_yearly, withdrawals_daily, withdrawals_weekly,
                withdrawals_monthly, withdrawals_yearly, prev_day_pl,
                prev_day_holding_fee
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker, balance = EXCLUDED.balance,
                equity = EXCLUDED.equity, margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_percent = EXCLUDED.margin_percent,
                profit_loss = EXCLUDED.profit_loss,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                realized_pl_yearly = EXCLUDED.realized_pl_yearly,
                realized_pl_alltime = EXCLUDED.realized_pl_alltime,
                deposits_alltime = EXCLUDED.deposits_alltime,
                withdrawals_alltime = EXCLUDED.withdrawals_alltime,
                holding_fee_daily = EXCLUDED.holding_fee_daily,
                holding_fee_weekly = EXCLUDED.holding_fee_weekly,
                holding_fee_monthly = EXCLUDED.holding_fee_monthly,
                holding_fee_yearly = EXCLUDED.holding_fee_yearly,
                holding_fee_alltime = EXCLUDED.holding_fee_alltime,
                open_charts = EXCLUDED.open_charts,
                empty_charts = EXCLUDED.empty_charts,
                open_trades = EXCLUDED.open_trades,
                autotrading = EXCLUDED.autotrading,
                swap_daily = EXCLUDED.swap_daily,
                swap_weekly = EXCLUDED.swap_weekly,
                swap_monthly = EXCLUDED.swap_monthly,
                swap_yearly = EXCLUDED.swap_yearly,
                swap_alltime = EXCLUDED.swap_alltime,
                deposits_daily = EXCLUDED.deposits_daily,
                deposits_weekly = EXCLUDED.deposits_weekly,
                deposits_monthly = EXCLUDED.deposits_monthly,
                deposits_yearly = EXCLUDED.deposits_yearly,
                withdrawals_daily = EXCLUDED.withdrawals_daily,
                withdrawals_weekly = EXCLUDED.withdrawals_weekly,
                withdrawals_monthly = EXCLUDED.withdrawals_monthly,
                withdrawals_yearly = EXCLUDED.withdrawals_yearly,
                prev_day_pl = EXCLUDED.prev_day_pl,
                prev_day_holding_fee = EXCLUDED.prev_day_holding_fee;
        """, tuple(json_data[field] for field in required_fields))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Data stored for account {json_data['account_number']}")
        socketio.emit('account_update', json_data)  # Push update via WebSocket
        check_alerts(json_data)  # Check for alerts
        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def check_alerts(account_data):
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("SELECT alert_thresholds FROM settings WHERE user_id = 'default';")
    thresholds = cur.fetchone()
    thresholds = json.loads(thresholds[0]) if thresholds else {"equity": 500, "profit_loss": -1000, "margin_percent": 20}
    alerts = []
    if account_data['equity'] < thresholds['equity']:
        alerts.append({"account_number": account_data['account_number'], "issue": f"Low Equity: {account_data['equity']}", "severity": "critical"})
    if account_data['profit_loss'] < thresholds['profit_loss']:
        alerts.append({"account_number": account_data['account_number'], "issue": f"High Loss: {account_data['profit_loss']}", "severity": "warning"})
    if account_data['margin_percent'] < thresholds['margin_percent']:
        alerts.append({"account_number": account_data['account_number'], "issue": f"Low Margin: {account_data['margin_percent']}%", "severity": "critical"})
    if alerts:
        socketio.emit('alert', alerts)  # Push alerts via WebSocket
    cur.close()
    conn.close()

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts;")
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return jsonify({"accounts": [dict(zip(columns, row)) for row in rows]})
    except Exception as e:
        logger.error(f"API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        # Balance per Broker
        cur.execute("""
            SELECT broker, SUM(balance) as total_balance, SUM(equity) as total_equity, SUM(profit_loss) as total_pl
            FROM accounts GROUP BY broker;
        """)
        balance_data = [{"broker": row[0], "balance": row[1], "equity": row[2], "profit_loss": row[3]} for row in cur.fetchall()]
        # Yearly Profits per Broker
        cur.execute("""
            SELECT broker, SUM(realized_pl_yearly) as yearly_pl FROM accounts GROUP BY broker;
        """)
        yearly_pl_data = [{"broker": row[0], "yearly_pl": row[1]} for row in cur.fetchall()]
        # Margin Health
        cur.execute("""
            SELECT COUNT(*) FILTER (WHERE free_margin < 0) as below_zero,
                   COUNT(*) FILTER (WHERE free_margin >= 0 AND free_margin <= 500) as zero_to_500,
                   COUNT(*) FILTER (WHERE free_margin > 500 AND free_margin <= 1000) as five_hundred_to_1000,
                   COUNT(*) FILTER (WHERE free_margin > 1000) as above_1000
            FROM accounts;
        """)
        margin_health = cur.fetchone()
        margin_health_data = {
            "below_zero": margin_health[0], "zero_to_500": margin_health[1],
            "five_hundred_to_1000": margin_health[2], "above_1000": margin_health[3]
        }
        # Top Performing Accounts
        cur.execute("""
            SELECT account_number, realized_pl_daily FROM accounts ORDER BY realized_pl_daily DESC LIMIT 5;
        """)
        top_daily = [{"account_number": row[0], "pl": row[1]} for row in cur.fetchall()]
        cur.execute("""
            SELECT account_number, realized_pl_monthly FROM accounts ORDER BY realized_pl_monthly DESC LIMIT 5;
        """)
        top_monthly = [{"account_number": row[0], "pl": row[1]} for row in cur.fetchall()]
        cur.execute("""
            SELECT account_number, realized_pl_yearly FROM accounts ORDER BY realized_pl_yearly DESC LIMIT 5;
        """)
        top_yearly = [{"account_number": row[0], "pl": row[1]} for row in cur.fetchall()]
        # Drawdown per Broker
        cur.execute("""
            SELECT broker, SUM(balance) as total_balance, SUM(equity) as total_equity
            FROM accounts GROUP BY broker;
        """)
        drawdown_data = [{"broker": row[0], "drawdown": ((row[1] - row[2]) / row[1] * 100) if row[1] > 0 else 0} for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({
            "balance_per_broker": balance_data,
            "yearly_profits": yearly_pl_data,
            "margin_health": margin_health_data,
            "top_daily": top_daily,
            "top_monthly": top_monthly,
            "top_yearly": top_yearly,
            "drawdown": drawdown_data
        })
    except Exception as e:
        logger.error(f"Analytics Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings", methods=["GET"])
def get_settings():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            SELECT sort_state, is_numbers_masked, gmt_offset, period_resets,
                   main_refresh_rate, critical_margin, warning_margin, is_dark_mode,
                   mask_timer, font_size, notes, broker_offsets, alert_thresholds
            FROM settings WHERE user_id = 'default';
        """)
        settings = cur.fetchone()
        cur.close()
        conn.close()
        if settings:
            columns = [desc[0] for desc in cur.description]
            return jsonify(dict(zip(columns, settings)))
        return jsonify({})
    except Exception as e:
        logger.error(f"Settings Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings", methods=["POST"])
def save_settings():
    try:
        settings = request.get_json()
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO settings (
                user_id, sort_state, is_numbers_masked, gmt_offset, period_resets,
                main_refresh_rate, critical_margin, warning_margin, is_dark_mode,
                mask_timer, font_size, notes, broker_offsets, alert_thresholds
            ) VALUES ('default', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                sort_state = EXCLUDED.sort_state,
                is_numbers_masked = EXCLUDED.is_numbers_masked,
                gmt_offset = EXCLUDED.gmt_offset,
                period_resets = EXCLUDED.period_resets,
                main_refresh_rate = EXCLUDED.main_refresh_rate,
                critical_margin = EXCLUDED.critical_margin,
                warning_margin = EXCLUDED.warning_margin,
                is_dark_mode = EXCLUDED.is_dark_mode,
                mask_timer = EXCLUDED.mask_timer,
                font_size = EXCLUDED.font_size,
                notes = EXCLUDED.notes,
                broker_offsets = EXCLUDED.broker_offsets,
                alert_thresholds = EXCLUDED.alert_thresholds;
        """, (
            json.dumps(settings.get('sortState', {})),
            settings.get('isNumbersMasked', False),
            settings.get('gmtOffset', 3),
            json.dumps(settings.get('periodResets', {})),
            settings.get('mainRefreshRate', 5),
            settings.get('criticalMargin', 0),
            settings.get('warningMargin', 500),
            settings.get('isDarkMode', False),
            settings.get('maskTimer', '300'),
            settings.get('fontSize', '14'),
            json.dumps(settings.get('notes', {})),
            json.dumps(settings.get('brokerOffsets', {"Raw Trading Ltd": -5, "Swissquote": -1, "XTB International": -6})),
            json.dumps(settings.get('alertThresholds', {"equity": 500, "profit_loss": -1000, "margin_percent": 20}))
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Settings saved successfully")
        return jsonify({"message": "Settings saved"}), 200
    except Exception as e:
        logger.error(f"Settings Save Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["POST"])
def save_history():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            data = [data]
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        for entry in data:
            local_tz = pytz.timezone('Asia/Beirut')
            snapshot_time = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
            utc_time = snapshot_time.astimezone(pytz.UTC)
            cur.execute("""
                INSERT INTO history (
                    account_number, balance, equity, margin_used, free_margin, margin_level,
                    open_trade, profit_loss, open_charts, deposit_withdrawal, margin_percent,
                    realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly,
                    autotrading, empty_charts, deposits_alltime, withdrawals_alltime,
                    realized_pl_alltime, holding_fee_daily, broker, traded_pairs,
                    open_pairs_charts, ea_names, snapshot_time, last_update
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                entry.get('account_number'),
                entry.get('balance'),
                entry.get('equity'),
                entry.get('margin_used'),
                entry.get('free_margin'),
                entry.get('margin_percent', 0),
                entry.get('open_trades', 0),
                entry.get('profit_loss'),
                entry.get('open_charts'),
                0,
                entry.get('margin_percent'),
                entry.get('realized_pl_daily'),
                entry.get('realized_pl_weekly'),
                entry.get('realized_pl_monthly'),
                entry.get('realized_pl_yearly'),
                entry.get('autotrading'),
                entry.get('empty_charts'),
                entry.get('deposits_alltime'),
                entry.get('withdrawals_alltime'),
                entry.get('realized_pl_alltime'),
                entry.get('holding_fee_daily'),
                entry.get('broker'),
                None,
                None,
                None,
                utc_time,
                utc_time
            ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"History saved for {len(data)} accounts")
        return jsonify({"message": "History saved"}), 200
    except Exception as e:
        logger.error(f"History Save Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        account = request.args.get('account')
        start = request.args.get('start')
        end = request.args.get('end')
        broker = request.args.get('broker')
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        query = "SELECT * FROM history WHERE 1=1"
        params = []
        if account:
            query += " AND account_number = %s"
            params.append(account)
        if start:
            query += " AND snapshot_time >= %s"
            params.append(start)
        if end:
            query += " AND snapshot_time <= %s"
            params.append(end)
        if broker:
            query += " AND broker = %s"
            params.append(broker)
        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return jsonify({"history": [dict(zip(columns, row)) for row in rows]})
    except Exception as e:
        logger.error(f"History Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

create_tables()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
