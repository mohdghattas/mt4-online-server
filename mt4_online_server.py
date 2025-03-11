const express = require('express');
const app = express();

// Middleware to parse JSON bodies and log requests
app.use(express.json());  // parse JSON body
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url} - Content-Type: ${req.headers['content-type']}`);
    next();
});

// POST handler for /api/mt4data
app.post('/api/mt4data', (req, res) => {
    // Enforce Content-Type: application/json
    if (!req.is('application/json')) {
        console.error('Rejecting request with wrong Content-Type');
        return res.status(400).json({ error: 'Content-Type must be application/json' });
    }
    // Validate request body exists and is JSON
    const data = req.body;
    if (!data || Object.keys(data).length === 0) {
        console.error('Rejecting request with no JSON body');
        return res.status(400).json({ error: 'Request JSON body is required' });
    }
    // (Optional) Validate expected fields in data, e.g.:
    // if (!data.account || !data.balance) { ... respond with 400 ... }

    // Process the data (e.g., save to database)
    try {
        // db.saveMT4Data(data);  // Pseudo-code for database save
        console.log('Received MT4 data:', JSON.stringify(data));
        // On success, send a confirmation response
        res.status(200).json({ status: 'success', message: 'Data received' });
    } catch (err) {
        console.error('Database save error:', err);
        res.status(500).json({ status: 'error', message: 'Server error saving data' });
    }
});

// (Optional) GET handler for /api/mt4data to support dashboard data retrieval
app.get('/api/mt4data', (req, res) => {
    try {
        // const records = db.fetchMT4Data();  // fetch data from DB (pseudo-code)
        const records = [];  // placeholder for fetched records
        res.status(200).json({ records: records });
    } catch (err) {
        console.error('Database fetch error:', err);
        res.status(500).json({ status: 'error', message: 'Server error fetching data' });
    }
});

// Start the server (adjust port as needed)
app.listen(3000, () => {
    console.log('API server is running on port 3000');
});
