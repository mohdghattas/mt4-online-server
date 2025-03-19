@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # Always decode raw data
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # Parse JSON manually
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decode Error: {e}")
            return jsonify({"error": f"Invalid JSON format: {e}"}), 400

        # Check required fields
        required_fields = [
            "broker", "account_number", "balance", "equity", "margin_used", "free_margin",
            "margin_percent", "profit_loss", "realized_pl_daily", "realized_pl_weekly",
            "realized_pl_monthly", "realized_pl_yearly", "open_charts", "open_trades",
            "autotrading_status", "ea_status", "terminal_errors", "empty_charts_count",
            "empty_charts_symbols", "open_pairs_charts", "deposits_today", "withdrawals_today",
            "deposits_weekly", "withdrawals_weekly", "deposits_monthly", "withdrawals_monthly",
            "deposits_yearly", "withdrawals_yearly", "deposits_all_time", "withdrawals_all_time"
        ]
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Proceed to DB logic (same as before)
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute(""" 
            -- INSERT QUERY HERE
        """, tuple(data[field] for field in required_fields))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully for account {data['account_number']}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
