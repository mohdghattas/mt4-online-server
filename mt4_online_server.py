@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data()
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        data = request.get_json()
        if not data:
            logger.error("❌ Invalid JSON payload received.")
            return jsonify({"error": "Invalid JSON payload"}), 400

        logger.info(f"✅ Processed Request Data: {data}")

        # ✅ Extract data
        broker = data.get("broker")
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        free_margin = data.get("free_margin")
        profit_loss = data.get("profit_loss")

        if not account_number or not broker:
            return jsonify({"error": "Missing required fields"}), 400

        # ✅ Store timestamps in UTC
        timestamp = datetime.now(pytz.utc)

        conn = get_db_connection()
        cur = conn.cursor()

        sql_query = """
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss,
                timestamp = EXCLUDED.timestamp;
        """
        cur.execute(sql_query, (broker, account_number, balance, equity, free_margin, profit_loss, timestamp))
        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Data stored successfully")
        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
