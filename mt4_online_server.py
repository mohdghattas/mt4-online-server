<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MT4 Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        :root {
            --primary-color: #2c3e50;
            --positive-color: #27ae60;
            --negative-color: #c0392b;
            --light-red: #f8d7da;
            --background: #f8f9fa;
            --border-color: #dee2e6;
            --highlight-color: #fff3cd;
            --dark-background: #1a252f;
            --dark-primary: #ffffff;
            --warning-color: #ff9800;
            --critical-highlight: #ffcccc;
            --warning-highlight: #ffe6e6;
            --light-font: #2c3e50;
            --dark-font: #ffffff;
        }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 20px;
        background: var(--background);
        color: var(--light-font);
        transition: background 0.3s, color 0.3s;
    }

    body.dark-mode {
        background: var(--dark-background);
        color: var(--dark-font);
    }

    .container {
        max-width: 1400px;
        margin: 0 auto;
    }

    .tabs {
        display: flex;
        margin-bottom: 20px;
        border-bottom: 2px solid var(--primary-color);
        flex-wrap: wrap;
    }

    .tab {
        padding: 10px 20px;
        cursor: pointer;
        background: #f0f0f0;
        border: none;
        border-radius: 4px 4px 0 0;
        margin-right: 5px;
        margin-bottom: 5px;
        transition: all 0.3s ease;
    }

    .tab.active {
        background: var(--primary-color);
        color: white;
    }

    body.dark-mode .tab {
        background: #34495e;
        color: var(--dark-font);
    }

    body.dark-mode .tab.active {
        background: var(--positive-color);
    }

    .tab-content {
        display: none;
    }

    .tab-content.active {
        display: block;
    }

    .table-container {
        overflow-x: auto;
        margin-bottom: 20px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }

    body.dark-mode table {
        background: #34495e;
    }

    th, td {
        padding: 12px 15px;
        text-align: center;
        border-bottom: 1px solid var(--border-color);
    }

    body.dark-mode th, body.dark-mode td {
        border-bottom: 1px solid #4a6278;
    }

    th {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
        cursor: pointer;
        user-select: none;
    }

    body.dark-mode th {
        background-color: #2c3e50;
    }

    #brokersTable th:first-child,
    #brokersTable td:first-child {
        position: sticky;
        left: 0;
        z-index: 2;
        background: var(--primary-color);
        color: white;
        min-width: 120px;
    }

    #brokersTable td:first-child {
        background: white;
        color: var(--light-font);
    }

    body.dark-mode #brokersTable th:first-child {
        background: #2c3e50;
    }

    body.dark-mode #brokersTable td:first-child {
        background: #34495e;
        color: var(--dark-font);
    }

    #accountsTable th:nth-child(2),
    #accountsTable td:nth-child(2) {
        position: sticky;
        left: 0;
        z-index: 2;
        background: var(--primary-color);
        color: white;
        min-width: 120px;
    }

    #accountsTable td:nth-child(2) {
        background: white;
        color: var(--light-font);
    }

    body.dark-mode #accountsTable th:nth-child(2) {
        background: #2c3e50;
    }

    body.dark-mode #accountsTable td:nth-child(2) {
        background: #34495e;
        color: var(--dark-font);
    }

    .error {
        color: var(--negative-color);
        padding: 15px;
        text-align: center;
        margin: 20px 0;
        border-radius: 5px;
        background: var(--light-red);
        display: none;
    }

    .loading {
        text-align: center;
        padding: 20px;
        color: #6c757d;
    }

    .negative { color: var(--negative-color); font-weight: bold; }
    .positive { color: var(--positive-color); font-weight: bold; }
    .warning { background: var(--highlight-color); }
    .critical-row { background: var(--critical-highlight); }
    .warning-row { background: var(--warning-highlight); }

    body.dark-mode .warning { background: #e67e22; }
    body.dark-mode .critical-row { background: #ff6666; }
    body.dark-mode .warning-row { background: #ff9999; }

    .notes-section, .chart-container, .quick-stats {
        margin: 20px 0;
        padding: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .note-block {
        flex: 1;
        min-width: 200px;
        display: flex;
        flex-direction: column;
    }

    .note-title {
        padding: 5px;
        border: 1px solid var(--border-color);
        border-radius: 4px 4px 0 0;
        background: #f0f0f0;
        font-weight: bold;
    }

    body.dark-mode .notes-section,
    body.dark-mode .chart-container,
    body.dark-mode .quick-stats {
        background: #34495e;
    }

    body.dark-mode .note-title {
        background: #2c3e50;
        border-color: #4a6278;
        color: var(--dark-font);
    }

    textarea {
        width: 100%;
        height: 100px;
        padding: 10px;
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 4px 4px;
        resize: vertical;
        font-family: inherit;
        box-sizing: border-box;
        color: var(--light-font);
    }

    body.dark-mode textarea {
        border-color: #4a6278;
        background: #2c3e50;
        color: var(--dark-font);
    }

    .settings-section {
        max-width: 600px;
        margin: 20px auto;
        padding: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
    }

    body.dark-mode .settings-section {
        background: #34495e;
    }

    .toggle-buttons button, .refresh-button, #exportButton {
        padding: 8px 16px;
        margin: 5px;
        border: none;
        border-radius: 4px;
        background-color: var(--primary-color);
        color: white;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .toggle-buttons button.active {
        background-color: var(--positive-color);
    }

    .refresh-button:hover, #exportButton:hover {
        background-color: var(--positive-color);
    }

    .mask-numbers {
        background-color: #f8f9fa;
        color: transparent;
        text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
    }

    body.dark-mode .mask-numbers {
        background-color: #34495e;
    }

    .sort-indicator {
        margin-left: 5px;
        font-size: 0.8em;
    }

    .chart-section {
        margin: 20px 0;
        width: 100%;
        max-height: 450px;
    }

    canvas {
        width: 100% !important;
        height: 400px !important;
    }

    body.dark-mode .chart-container h2,
    body.dark-mode .chart-section h3 {
        color: var(--dark-font);
    }

    .quick-stats div {
        display: inline-block;
        margin-right: 20px;
        font-weight: bold;
    }

    .settings-row {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }

    .settings-row label {
        flex: 1;
        margin-right: 10px;
    }

    .settings-row input, .settings-row select {
        flex: 1;
        padding: 5px;
    }

    @media (max-width: 768px) {
        th, td { padding: 8px 10px; }
        h1 { font-size: 1.5rem; }
        h2 { font-size: 1.2rem; }
        .chart-section { max-height: 350px; }
        canvas { height: 300px !important; }
        .quick-stats div { display: block; margin: 10px 0; }
        .tabs { justify-content: center; }
        .note-block { min-width: 100%; }
        .settings-row { flex-direction: column; align-items: flex-start; }
        .settings-row label { margin-bottom: 5px; }
    }
</style>

</head>
<body>
    <div class="container">
        <h1> MT4 Accounts Monitor</h1>
        <div class="refresh-info">Auto-refreshing every 5 seconds (Analytics: manual)</div>
        <div id="error" class="error"></div>
        <div id="loading" class="loading">Loading account data...</div>
    <!-- Tabs -->
    <div class="tabs">
        <button class="tab active" onclick="switchTab('main')">Main</button>
        <button class="tab" onclick="switchTab('analytics')">Analytics</button>
        <button class="tab" onclick="switchTab('settings')">Settings</button>
    </div>

    <!-- Main Tab -->
    <div id="mainTab" class="tab-content active">
        <div class="quick-stats">
            <div>Total Balance: <span id="totalBalance">0</span></div>
            <div>Total Equity: <span id="totalEquity">0</span></div>
            <div>Total P/L: <span id="totalPL">0</span></div>
        </div>

        <div class="notes-section">
            <div class="note-block">
                <input type="text" class="note-title" id="noteTitle1" value="Notes">
                <textarea id="notes1" placeholder="Add your notes here..."></textarea>
            </div>
            <div class="note-block">
                <input type="text" class="note-title" id="noteTitle2" value="Things to Watch">
                <textarea id="notes2" placeholder="Things to watch..."></textarea>
            </div>
            <div class="note-block">
                <input type="text" class="note-title" id="noteTitle3" value="New Ideas">
                <textarea id="notes3" placeholder="New ideas..."></textarea>
            </div>
            <div class="note-block">
                <input type="text" class="note-title" id="noteTitle4" value="Miscellaneous">
                <textarea id="notes4" placeholder="Anything else..."></textarea>
            </div>
        </div>

        <h2>🔹 Brokers Summary</h2>
        <div class="table-container">
            <table id="brokersTable">
                <thead>
                    <tr>
                        <th>Broker</th>
                        <th>Accounts</th>
                        <th>Balance</th>
                        <th>Equity</th>
                        <th>Floating P/L</th>
                        <th>Daily P/L</th>
                        <th>Weekly P/L</th>
                        <th>Monthly P/L</th>
                        <th>Yearly P/L</th>
                    </tr>
                </thead>
                <tbody id="summaryTableBody"></tbody>
                <tfoot id="grandTotal"></tfoot>
            </table>
        </div>

        <h2>🔹 Accounts Details</h2>
        <div class="table-container">
            <table id="accountsTable">
                <thead>
                    <tr>
                        <th data-sort="index">#</th>
                        <th data-sort="broker">Broker</th>
                        <th data-sort="account_number">Account #</th>
                        <th data-sort="balance">Balance</th>
                        <th data-sort="equity">Equity</th>
                        <th data-sort="free_margin">Free Margin</th>
                        <th data-sort="margin_percent">Margin %</th>
                        <th data-sort="profit_loss">Floating P/L</th>
                        <th data-sort="realized_pl_daily">Daily P/L</th>
                        <th data-sort="realized_pl_weekly">Weekly P/L</th>
                        <th data-sort="realized_pl_monthly">Monthly P/L</th>
                        <th data-sort="realized_pl_yearly">Yearly P/L</th>
                        <th data-sort="open_charts">Charts</th>
                        <th data-sort="open_trades">Trades</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="accountTableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- Analytics Tab -->
    <div id="analyticsTab" class="tab-content">
        <button class="refresh-button" onclick="updateCharts()">Refresh Charts</button>
        <div class="chart-container">
            <h2>📊 Analytics Dashboard</h2>
            
            <div class="chart-section" data-filter="balance">
                <h3>Total Balance per Broker</h3>
                <canvas id="balanceChart"></canvas>
            </div>
            
            <div class="chart-section" data-filter="yearlyProfit">
                <h3>Yearly Profits per Broker</h3>
                <canvas id="yearlyProfitChart"></canvas>
            </div>
            
            <div class="chart-section">
                <h3>Margin Health</h3>
                <canvas id="marginHealthChart"></canvas>
            </div>
            
            <div class="chart-section">
                <h3>Top Performing Accounts (Daily)</h3>
                <canvas id="topDailyChart"></canvas>
            </div>
            
            <div class="chart-section">
                <h3>Top Performing Accounts (Monthly)</h3>
                <canvas id="topMonthlyChart"></canvas>
            </div>
            
            <div class="chart-section">
                <h3>Top Performing Accounts (Yearly)</h3>
                <canvas id="topYearlyChart"></canvas>
            </div>

            <div class="chart-section" data-filter="drawdown">
                <h3>Drawdown per Broker (%)</h3>
                <canvas id="drawdownChart"></canvas>
            </div>

            <div class="chart-section">
                <h3>Floating P/L Daily Curve</h3>
                <canvas id="floatingPLCurve"></canvas>
            </div>
        </div>
    </div>

    <!-- Settings Tab -->
    <div id="settingsTab" class="tab-content">
        <div class="settings-section">
            <h2>🔧 Settings</h2>

            <div class="dark-mode-toggle">
                <h3>Appearance</h3>
                <div class="toggle-buttons">
                    <button id="toggleDarkMode">Toggle Dark Mode</button>
                </div>
            </div>

            <div class="timezone-settings">
                <h3>Timezone Configuration</h3>
                <label for="gmtOffset">GMT Offset:</label>
                <select id="gmtOffset"></select>
            </div>

            <div class="refresh-settings">
                <h3>Refresh Rate</h3>
                <label for="refreshRate">Refresh Interval (seconds):</label>
                <select id="refreshRate">
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="30">30</option>
                </select>
            </div>

            <div class="alert-settings">
                <h3>Highlight Thresholds</h3>
                <div class="settings-row">
                    <label for="criticalMargin">Critical Free Margin (below):</label>
                    <input type="number" id="criticalMargin" min="-10000" value="0">
                </div>
                <div class="settings-row">
                    <label for="warningMargin">Warning Free Margin (below):</label>
                    <input type="number" id="warningMargin" min="0" value="500">
                </div>
            </div>

            <div class="masking-settings">
                <h3>Number Masking</h3>
                <div class="toggle-buttons">
                    <button id="toggleBrokersNumbers">Toggle Brokers Numbers</button>
                    <button id="toggleAccountsNumbers">Toggle Accounts Numbers</button>
                </div>
                <div class="settings-row">
                    <label for="maskTimer">Auto-Mask Timer:</label>
                    <select id="maskTimer">
                        <option value="300">5 Minutes</option>
                        <option value="600">10 Minutes</option>
                        <option value="1800">30 Minutes</option>
                        <option value="3600">1 Hour</option>
                        <option value="never">Never</option>
                    </select>
                </div>
            </div>

            <div class="export-settings">
                <h3>Export</h3>
                <button id="exportButton">Export to PDF</button>
            </div>
        </div>
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        const API_ENDPOINT = 'https://mt4-server.up.railway.app/api/accounts';
        let currentSort = JSON.parse(localStorage.getItem('sortState')) || { column: 'profit_loss', direction: 'asc' };
        let isBrokersMasked = false;
        let isAccountsMasked = false;
        let gmtOffset = parseInt(localStorage.getItem('gmtOffset')) || 0;
        let periodResets = JSON.parse(localStorage.getItem('periodResets') || '{}');
        let currentAccounts = [];
        let charts = {};
        let refreshRate = parseInt(localStorage.getItem('refreshRate')) || 5;
        let criticalMargin = parseInt(localStorage.getItem('criticalMargin')) || 0;
        let warningMargin = parseInt(localStorage.getItem('warningMargin')) || 500;
        let isDarkMode = localStorage.getItem('darkMode') === 'true';
        let maskTimer = localStorage.getItem('maskTimer') || '300';
        let maskTimeout;

        // Helper functions
        const showError = (message) => {
            const errorDiv = document.getElementById('error');
            if (errorDiv) {
                errorDiv.textContent = `⚠️ ${message}`;
                errorDiv.style.display = 'block';
                document.getElementById('loading').style.display = 'none';
            }
        };

        const formatNumber = (value) => value !== undefined && value !== null ? new Intl.NumberFormat('en-US').format(value) : 'N/A';
        const formatPercentage = (value) => value !== undefined && value !== null ? `${value.toFixed(2)}%` : 'N/A';
        const getPLClass = (value) => (value !== undefined && value >= 0) ? 'positive' : 'negative';

        const getAccountStatus = (account) => {
            const freeMargin = account.free_margin || 0;
            if (freeMargin < criticalMargin) return 'Critical';
            if (freeMargin < warningMargin) return 'Warning';
            return 'Safe';
        };

        // Chart configuration
        const getChartOptions = () => ({
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'top',
                    labels: { color: isDarkMode ? '#ffffff' : '#2c3e50' }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    formatter: (value) => formatNumber(value),
                    font: { weight: 'bold', size: 10 },
                    color: isDarkMode ? '#ffffff' : '#2c3e50'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: isDarkMode ? '#4a6278' : '#eee' },
                    ticks: { color: isDarkMode ? '#ffffff' : '#2c3e50' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: isDarkMode ? '#ffffff' : '#2c3e50' }
                }
            }
        });

        // Sorting functionality
        const sortAccounts = (accounts) => {
            return [...accounts].sort((a, b) => {
                const aVal = a[currentSort.column] || 0;
                const bVal = b[currentSort.column] || 0;

                if (currentSort.column === 'profit_loss') {
                    return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
                }

                if (typeof aVal === 'string') {
                    return currentSort.direction === 'asc' ?
                        aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }
                return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
            });
        };

        const updateSortIndicator = () => {
            document.querySelectorAll('th').forEach(header => {
                header.querySelector('.sort-indicator')?.remove();
                if (header.dataset.sort === currentSort.column) {
                    const indicator = document.createElement('span');
                    indicator.className = 'sort-indicator';
                    indicator.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
                    header.appendChild(indicator);
                }
            });
        };

        // Table updates
        const updateQuickStats = (accounts) => {
            const totalBalance = accounts.reduce((sum, a) => sum + (a.balance || 0), 0);
            const totalEquity = accounts.reduce((sum, a) => sum + (a.equity || 0), 0);
            const totalPL = accounts.reduce((sum, a) => sum + (a.profit_loss || 0), 0);

            document.getElementById('totalBalance').textContent = formatNumber(totalBalance);
            document.getElementById('totalEquity').textContent = formatNumber(totalEquity);
            document.getElementById('totalPL').textContent = formatNumber(totalPL);
            document.getElementById('totalPL').className = getPLClass(totalPL);
        };

        const updateBrokerSummary = (accounts) => {
            const brokerSummary = {};
            let grandTotal = {
                accountsCount: 0,
                balance: 0,
                equity: 0,
                floatingPL: 0,
                dailyPL: 0,
                weeklyPL: 0,
                monthlyPL: 0,
                yearlyPL: 0
            };

            accounts.forEach(account => {
                const broker = account.broker || 'Unknown';
                if (!brokerSummary[broker]) {
                    brokerSummary[broker] = {
                        count: 0,
                        balance: 0,
                        equity: 0,
                        floatingPL: 0,
                        dailyPL: 0,
                        weeklyPL: 0,
                        monthlyPL: 0,
                        yearlyPL: 0
                    };
                }

                const brokerEntry = brokerSummary[broker];
                brokerEntry.count++;
                brokerEntry.balance += account.balance || 0;
                brokerEntry.equity += account.equity || 0;
                brokerEntry.floatingPL += account.profit_loss || 0;
                brokerEntry.dailyPL += account.realized_pl_daily || 0;
                brokerEntry.weeklyPL += account.realized_pl_weekly || 0;
                brokerEntry.monthlyPL += account.realized_pl_monthly || 0;
                brokerEntry.yearlyPL += account.realized_pl_yearly || 0;

                grandTotal.accountsCount++;
                grandTotal.balance += account.balance || 0;
                grandTotal.equity += account.equity || 0;
                grandTotal.floatingPL += account.profit_loss || 0;
                grandTotal.dailyPL += account.realized_pl_daily || 0;
                grandTotal.weeklyPL += account.realized_pl_weekly || 0;
                grandTotal.monthlyPL += account.realized_pl_monthly || 0;
                grandTotal.yearlyPL += account.realized_pl_yearly || 0;
            });

            const summaryBody = document.getElementById('summaryTableBody');
            summaryBody.innerHTML = Object.entries(brokerSummary).map(([broker, totals]) => `
                <tr>
                    <td>${broker}</td>
                    <td>${totals.count}</td>
                    <td>${formatNumber(totals.balance)}</td>
                    <td>${formatNumber(totals.equity)}</td>
                    <td class="${getPLClass(totals.floatingPL)}">${formatNumber(totals.floatingPL)}</td>
                    <td class="${getPLClass(totals.dailyPL)}">${formatNumber(totals.dailyPL)}</td>
                    <td class="${getPLClass(totals.weeklyPL)}">${formatNumber(totals.weeklyPL)}</td>
                    <td class="${getPLClass(totals.monthlyPL)}">${formatNumber(totals.monthlyPL)}</td>
                    <td class="${getPLClass(totals.yearlyPL)}">${formatNumber(totals.yearlyPL)}</td>
                </tr>
            `).join('');

            document.getElementById('grandTotal').innerHTML = `
                <tr class="total-row">
                    <td>Grand Total</td>
                    <td>${grandTotal.accountsCount}</td>
                    <td>${formatNumber(grandTotal.balance)}</td>
                    <td>${formatNumber(grandTotal.equity)}</td>
                    <td class="${getPLClass(grandTotal.floatingPL)}">${formatNumber(grandTotal.floatingPL)}</td>
                    <td class="${getPLClass(grandTotal.dailyPL)}">${formatNumber(grandTotal.dailyPL)}</td>
                    <td class="${getPLClass(grandTotal.weeklyPL)}">${formatNumber(grandTotal.weeklyPL)}</td>
                    <td class="${getPLClass(grandTotal.monthlyPL)}">${formatNumber(grandTotal.monthlyPL)}</td>
                    <td class="${getPLClass(grandTotal.yearlyPL)}">${formatNumber(grandTotal.yearlyPL)}</td>
                </tr>
            `;
        };

        const updateAccountDetails = (accounts) => {
            const accountTable = document.getElementById('accountTableBody');
            if (!accountTable) return;
            accountTable.innerHTML = accounts.map((account, index) => {
                const status = getAccountStatus(account);
                const freeMargin = account.free_margin || 0;
                const floatingPL = account.profit_loss || 0;
                let rowClass = '';
                if (floatingPL < 0) {
                    if (freeMargin < 0) rowClass = 'critical-row';
                    else if (freeMargin < warningMargin) rowClass = 'warning-row';
                }
                return `
                    <tr class="${rowClass}">
                        <td>${index + 1}</td>
                        <td>${account.broker || 'N/A'}</td>
                        <td>${account.account_number || 'N/A'}</td>
                        <td>${formatNumber(account.balance)}</td>
                        <td>${formatNumber(account.equity)}</td>
                        <td>${formatNumber(account.free_margin)}</td>
                        <td>${formatPercentage(account.margin_percent)}</td>
                        <td class="${getPLClass(account.profit_loss)}">${formatNumber(account.profit_loss)}</td>
                        <td class="${getPLClass(account.realized_pl_daily)}">${formatNumber(account.realized_pl_daily)}</td>
                        <td class="${getPLClass(account.realized_pl_weekly)}">${formatNumber(account.realized_pl_weekly)}</td>
                        <td class="${getPLClass(account.realized_pl_monthly)}">${formatNumber(account.realized_pl_monthly)}</td>
                        <td class="${getPLClass(account.realized_pl_yearly)}">${formatNumber(account.realized_pl_yearly)}</td>
                        <td>${account.open_charts || 'N/A'}</td>
                        <td>${account.open_trades || 'N/A'}</td>
                        <td>${status}</td>
                    </tr>
                `;
            }).join('');
        };

        const updateNumberMasking = () => {
            document.querySelectorAll('#mainTab td, #analyticsTab td').forEach(cell => {
                const isNumeric = !isNaN(parseFloat(cell.textContent));
                if (cell.closest('#brokersTable')) {
                    cell.classList.toggle('mask-numbers', isBrokersMasked && isNumeric);
                } else if (cell.closest('#accountsTable')) {
                    cell.classList.toggle('mask-numbers', isAccountsMasked && isNumeric);
                }
            });
        };

        const resetMaskTimer = () => {
            clearTimeout(maskTimeout);
            if (maskTimer !== 'never') {
                maskTimeout = setTimeout(() => {
                    isBrokersMasked = true;
                    isAccountsMasked = true;
                    document.getElementById('toggleBrokersNumbers').classList.add('active');
                    document.getElementById('toggleAccountsNumbers').classList.add('active');
                    updateNumberMasking();
                }, parseInt(maskTimer) * 1000);
            }
        };

        // Period tracking
        const calculatePeriods = () => {
            const now = new Date();
            const tzNow = new Date(now.getTime() + gmtOffset * 3600000);

            const dailyReset = new Date(tzNow);
            dailyReset.setHours(0,0,0,0);

            const weeklyReset = new Date(dailyReset);
            weeklyReset.setDate(dailyReset.getDate() - dailyReset.getDay());

            const monthlyReset = new Date(dailyReset);
            monthlyReset.setDate(1);

            const yearlyReset = new Date(dailyReset);
            yearlyReset.setMonth(0, 1);

            return {
                daily: dailyReset.getTime(),
                weekly: weeklyReset.getTime(),
                monthly: monthlyReset.getTime(),
                yearly: yearlyReset.getTime()
            };
        };

        const checkPeriodResets = () => {
            const currentPeriods = calculatePeriods();
            const needsReset = {};

            Object.keys(currentPeriods).forEach(period => {
                if (!periodResets[period] || currentPeriods[period] > periodResets[period]) {
                    needsReset[period] = currentPeriods[period];
                }
            });

            if (Object.keys(needsReset).length > 0) {
                periodResets = {...periodResets, ...needsReset};
                localStorage.setItem('periodResets', JSON.stringify(periodResets));
                return needsReset;
            }
            return null;
        };

        const resetPeriodTracking = () => {
            periodResets = calculatePeriods();
            localStorage.setItem('periodResets', JSON.stringify(periodResets));
        };

        // Data processing
        const processAccountData = (accounts) => {
            const resets = checkPeriodResets();
            return accounts.map(account => ({
                ...account,
                realized_pl_daily: resets?.daily ? 0 : account.realized_pl_daily,
                realized_pl_weekly: resets?.weekly ? 0 : account.realized_pl_weekly,
                realized_pl_monthly: resets?.monthly ? 0 : account.realized_pl_monthly,
                realized_pl_yearly: resets?.yearly ? 0 : account.realized_pl_yearly
            }));
        };

        // Chart updates
        const updateCharts = () => {
            if (!currentAccounts.length) {
                console.error('No accounts data available for charts');
                return;
            }

            const chartOptions = getChartOptions();
            const brokerData = {};
            currentAccounts.forEach(account => {
                const broker = account.broker || 'Unknown';
                if (!brokerData[broker]) {
                    brokerData[broker] = {
                        balance: 0,
                        yearlyPL: 0,
                        equity: 0,
                        maxBalance: account.balance || 0
                    };
                }
                brokerData[broker].balance += account.balance || 0;
                brokerData[broker].yearlyPL += account.realized_pl_yearly || 0;
                brokerData[broker].equity += account.equity || 0;
                brokerData[broker].maxBalance = Math.max(brokerData[broker].maxBalance, account.balance || 0);
            });

            try {
                // Balance per Broker with Grand Total
                if (charts.balance) charts.balance.destroy();
                charts.balance = new Chart(document.getElementById('balanceChart'), {
                    type: 'bar',
                    data: {
                        labels: [...Object.keys(brokerData), 'Grand Total'],
                        datasets: [{
                            label: 'Total Balance',
                            data: [...Object.values(brokerData).map(d => d.balance),
                                   Object.values(brokerData).reduce((sum, d) => sum + d.balance, 0)],
                            backgroundColor: isDarkMode ? 'rgba(52, 152, 219, 0.8)' : 'rgba(44, 62, 80, 0.8)',
                            borderColor: isDarkMode ? 'rgba(52, 152, 219, 1)' : 'rgba(44, 62, 80, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });

                // Yearly Profits per Broker
                if (charts.yearlyProfit) charts.yearlyProfit.destroy();
                charts.yearlyProfit = new Chart(document.getElementById('yearlyProfitChart'), {
                    type: 'bar',
                    data: {
                        labels: [...Object.keys(brokerData), 'Total'],
                        datasets: [{
                            label: 'Yearly P/L',
                            data: [...Object.values(brokerData).map(d => d.yearlyPL), 
                                   Object.values(brokerData).reduce((sum, d) => sum + d.yearlyPL, 0)],
                            backgroundColor: [...Object.values(brokerData).map(d => d.yearlyPL >= 0 ? (isDarkMode ? 'rgba(46, 204, 113, 0.8)' : 'rgba(39, 174, 96, 0.8)') : (isDarkMode ? 'rgba(231, 76, 60, 0.8)' : 'rgba(192, 57, 43, 0.8)')),
                                            Object.values(brokerData).reduce((sum, d) => sum + d.yearlyPL, 0) >= 0 ? (isDarkMode ? 'rgba(46, 204, 113, 0.8)' : 'rgba(39, 174, 96, 0.8)') : (isDarkMode ? 'rgba(231, 76, 60, 0.8)' : 'rgba(192, 57, 43, 0.8)')],
                            borderColor: [...Object.values(brokerData).map(d => d.yearlyPL >= 0 ? (isDarkMode ? 'rgba(46, 204, 113, 1)' : 'rgba(39, 174, 96, 1)') : (isDarkMode ? 'rgba(231, 76, 60, 1)' : 'rgba(192, 57, 43, 1)')),
                                          Object.values(brokerData).reduce((sum, d) => sum + d.yearlyPL, 0) >= 0 ? (isDarkMode ? 'rgba(46, 204, 113, 1)' : 'rgba(39, 174, 96, 1)') : (isDarkMode ? 'rgba(231, 76, 60, 1)' : 'rgba(192, 57, 43, 1)')],
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });

                // Margin Health
                const marginRanges = {
                    belowZero: currentAccounts.filter(a => (a.free_margin || 0) < 0).length,
                    zeroTo500: currentAccounts.filter(a => (a.free_margin || 0) >= 0 && (a.free_margin || 0) <= 500).length,
                    '500to1000': currentAccounts.filter(a => (a.free_margin || 0) > 500 && (a.free_margin || 0) <= 1000).length,
                    above1000: currentAccounts.filter(a => (a.free_margin || 0) > 1000).length
                };
                if (charts.marginHealth) charts.marginHealth.destroy();
                charts.marginHealth = new Chart(document.getElementById('marginHealthChart'), {
                    type: 'bar',
                    data: {
                        labels: ['Below 0', '0-500', '500-1000', 'Above 1000'],
                        datasets: [{
                            label: 'Number of Accounts',
                            data: Object.values(marginRanges),
                            backgroundColor: [isDarkMode ? 'rgba(231, 76, 60, 0.8)' : 'rgba(192, 57, 43, 0.8)', 
                                           isDarkMode ? 'rgba(243, 156, 18, 0.8)' : 'rgba(255, 159, 64, 0.8)', 
                                           isDarkMode ? 'rgba(241, 196, 15, 0.8)' : 'rgba(255, 205, 86, 0.8)', 
                                           isDarkMode ? 'rgba(46, 204, 113, 0.8)' : 'rgba(39, 174, 96, 0.8)'],
                            borderColor: [isDarkMode ? 'rgba(231, 76, 60, 1)' : 'rgba(192, 57, 43, 1)', 
                                        isDarkMode ? 'rgba(243, 156, 18, 1)' : 'rgba(255, 159, 64, 1)', 
                                        isDarkMode ? 'rgba(241, 196, 15, 1)' : 'rgba(255, 205, 86, 1)', 
                                        isDarkMode ? 'rgba(46, 204, 113, 1)' : 'rgba(39, 174, 96, 1)'],
                            borderWidth: 1
                        }]
                    },
                    options: chartOptions
                });

                // Top Performing Accounts
                const createTopChart = (id, field, label) => {
                    const sortedAccounts = [...currentAccounts]
                        .sort((a, b) => (b[field] || 0) - (a[field] || 0))
                        .slice(0, 5);
                    if (charts[id]) charts[id].destroy();
                    charts[id] = new Chart(document.getElementById(id), {
                        type: 'bar',
                        data: {
                            labels: sortedAccounts.map(a => a.account_number || 'N/A'),
                            datasets: [{
                                label,
                                data: sortedAccounts.map(a => a[field] || 0),
                                backgroundColor: isDarkMode ? 'rgba(52, 152, 219, 0.8)' : 'rgba(44, 62, 80, 0.8)',
                                borderColor: isDarkMode ? 'rgba(52, 152, 219, 1)' : 'rgba(44, 62, 80, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: chartOptions
                    });
                };

                createTopChart('topDailyChart', 'realized_pl_daily', 'Daily P/L');
                createTopChart('topMonthlyChart', 'realized_pl_monthly', 'Monthly P/L');
                createTopChart('topYearlyChart', 'realized_pl_yearly', 'Yearly P/L');

                // Drawdown per Broker (%)
                const drawdownData = Object.entries(brokerData).map(([broker, data]) => ({
                    broker,
                    drawdown: data.balance ? ((data.maxBalance - data.equity) / data.maxBalance * 100) : 0
                }));
                const totalDrawdown = currentAccounts.reduce((sum, a) => sum + (a.balance || 0), 0) ?
                    ((currentAccounts.reduce((sum, a) => sum + (a.balance || 0), 0) - 
                      currentAccounts.reduce((sum, a) => sum + (a.equity || 0), 0)) /
                     currentAccounts.reduce((sum, a) => sum + (a.balance || 0), 0) * 100) : 0;

                if (charts.drawdown) charts.drawdown.destroy();
                charts.drawdown = new Chart(document.getElementById('drawdownChart'), {
                    type: 'bar',
                    data: {
                        labels: [...drawdownData.map(d => d.broker), 'Total'],
                        datasets: [{
                            label: 'Drawdown %',
                            data: [...drawdownData.map(d => d.drawdown), totalDrawdown],
                            backgroundColor: isDarkMode ? 'rgba(231, 76, 60, 0.8)' : 'rgba(192, 57, 43, 0.8)',
                            borderColor: isDarkMode ? 'rgba(231, 76, 60, 1)' : 'rgba(192, 57, 43, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        ...chartOptions,
                        plugins: {
                            ...chartOptions.plugins,
                            datalabels: {
                                formatter: (value) => value.toFixed(2) + '%'
                            }
                        }
                    }
                });

                // Floating P/L Daily Curve
                const dailyPLData = JSON.parse(localStorage.getItem('dailyPLData')) || {};
                const today = new Date().toISOString().split('T')[0];
                dailyPLData[today] = currentAccounts.reduce((sum, a) => sum + (a.profit_loss || 0), 0);
                localStorage.setItem('dailyPLData', JSON.stringify(dailyPLData));

                const labels = Object.keys(dailyPLData).slice(-7);
                const data = labels.map(date => dailyPLData[date]);

                if (charts.floatingPLCurve) charts.floatingPLCurve.destroy();
                charts.floatingPLCurve = new Chart(document.getElementById('floatingPLCurve'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Floating P/L',
                            data: data,
                            borderColor: isDarkMode ? 'rgba(52, 152, 219, 1)' : 'rgba(44, 62, 80, 1)',
                            backgroundColor: isDarkMode ? 'rgba(52, 152, 219, 0.2)' : 'rgba(44, 62, 80, 0.2)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        ...chartOptions,
                        plugins: {
                            ...chartOptions.plugins,
                            datalabels: { display: false }
                        }
                    }
                });
            } catch (error) {
                console.error('Error updating charts:', error);
            }
        };

        // Data fetching
        let refreshInterval;
        const fetchData = async () => {
            try {
                const response = await fetch(API_ENDPOINT);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                const data = await response.json();

                if (!data?.accounts?.length) {
                    showError('No account data available');
                    return;
                }

                currentAccounts = processAccountData(data.accounts);
                const sorted = sortAccounts(currentAccounts);
                updateQuickStats(sorted);
                updateBrokerSummary(sorted);
                updateAccountDetails(sorted);
                updateNumberMasking();
                document.getElementById('loading').style.display = 'none';
                updateSortIndicator();

                // Fix: Update charts if analytics tab is active
                if (document.getElementById('analyticsTab').classList.contains('active')) {
                    updateCharts();
                }
            } catch (error) {
                showError(error.message);
                console.error('Fetch error:', error);
            }
        };

        const setRefreshInterval = () => {
            clearInterval(refreshInterval);
            refreshInterval = setInterval(fetchData, refreshRate * 1000);
        };

        // Export to PDF
        const exportToPDF = () => {
            const mainTab = document.getElementById('mainTab');
            const analyticsTab = document.getElementById('analyticsTab');
            const settingsTab = document.getElementById('settingsTab');
            const container = document.querySelector('.container');

            // Temporarily show Main and Analytics tabs, hide Settings
            const originalMainDisplay = mainTab.style.display;
            const originalAnalyticsDisplay = analyticsTab.style.display;
            const originalSettingsDisplay = settingsTab.style.display;

            mainTab.style.display = 'block';
            analyticsTab.style.display = 'block';
            settingsTab.style.display = 'none';

            const exportContainer = document.createElement('div');
            exportContainer.appendChild(mainTab.cloneNode(true));
            exportContainer.appendChild(analyticsTab.cloneNode(true));
            document.body.appendChild(exportContainer);

            const opt = {
                margin: 1,
                filename: 'MT4_Dashboard.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };

            html2pdf().from(exportContainer).set(opt).save().then(() => {
                // Restore original state
                mainTab.style.display = originalMainDisplay;
                analyticsTab.style.display = originalAnalyticsDisplay;
                settingsTab.style.display = originalSettingsDisplay;
                document.body.removeChild(exportContainer);
            });
        };

        // Initialization
        const initialize = () => {
            // Dark Mode
            if (isDarkMode) document.body.classList.add('dark-mode');
            document.getElementById('toggleDarkMode').addEventListener('click', () => {
                document.body.classList.toggle('dark-mode');
                isDarkMode = document.body.classList.contains('dark-mode');
                localStorage.setItem('darkMode', isDarkMode);
                updateCharts();
            });

            // GMT Selector
            const gmtSelect = document.getElementById('gmtOffset');
            for(let i = -12; i <= 14; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.text = `GMT${i >= 0 ? '+' : ''}${i}`;
                gmtSelect.appendChild(option);
            }
            gmtSelect.value = gmtOffset;
            gmtSelect.addEventListener('change', function() {
                gmtOffset = parseInt(this.value);
                localStorage.setItem('gmtOffset', gmtOffset);
                resetPeriodTracking();
                fetchData();
            });

            // Refresh Rate
            const refreshSelect = document.getElementById('refreshRate');
            refreshSelect.value = refreshRate;
            refreshSelect.addEventListener('change', function() {
                refreshRate = parseInt(this.value);
                localStorage.setItem('refreshRate', refreshRate);
                setRefreshInterval();
            });

            // Highlight Thresholds
            const criticalMarginInput = document.getElementById('criticalMargin');
            const warningMarginInput = document.getElementById('warningMargin');
            criticalMarginInput.value = criticalMargin;
            warningMarginInput.value = warningMargin;

            criticalMarginInput.addEventListener('change', function() {
                criticalMargin = parseInt(this.value);
                localStorage.setItem('criticalMargin', criticalMargin);
                updateAccountDetails(currentAccounts);
            });
            warningMarginInput.addEventListener('change', function() {
                warningMargin = parseInt(this.value);
                localStorage.setItem('warningMargin', warningMargin);
                updateAccountDetails(currentAccounts);
            });

            // Notes persistence
            const noteTitles = ['noteTitle1', 'noteTitle2', 'noteTitle3', 'noteTitle4'];
            const noteTextareas = ['notes1', 'notes2', 'notes3', 'notes4'];
            noteTitles.forEach((id, index) => {
                const titleInput = document.getElementById(id);
                const savedTitle = localStorage.getItem(`mt4-${id}`);
                if (savedTitle) titleInput.value = savedTitle;
                titleInput.addEventListener('input', () => {
                    localStorage.setItem(`mt4-${id}`, titleInput.value);
                });

                const textarea = document.getElementById(noteTextareas[index]);
                textarea.value = localStorage.getItem(`mt4-${noteTextareas[index]}`) || '';
                textarea.addEventListener('input', () => {
                    localStorage.setItem(`mt4-${noteTextareas[index]}`, textarea.value);
                });
            });

            // Number masking toggles
            document.getElementById('toggleBrokersNumbers').addEventListener('click', function() {
                isBrokersMasked = !isBrokersMasked;
                this.classList.toggle('active', isBrokersMasked);
                updateNumberMasking();
                resetMaskTimer();
            });

            document.getElementById('toggleAccountsNumbers').addEventListener('click', function() {
                isAccountsMasked = !isAccountsMasked;
                this.classList.toggle('active', isAccountsMasked);
                updateNumberMasking();
                resetMaskTimer();
            });

            // Mask Timer
            const maskTimerSelect = document.getElementById('maskTimer');
            maskTimerSelect.value = maskTimer;
            maskTimerSelect.addEventListener('change', function() {
                maskTimer = this.value;
                localStorage.setItem('maskTimer', maskTimer);
                resetMaskTimer();
            });
            document.addEventListener('mousemove', resetMaskTimer);
            resetMaskTimer();

            // Export Button
            document.getElementById('exportButton').addEventListener('click', exportToPDF);

            // Column sorting
            document.querySelectorAll('#accountsTable th[data-sort]').forEach(header => {
                header.addEventListener('click', () => {
                    const column = header.dataset.sort;
                    currentSort.direction = currentSort.column === column ?
                        (currentSort.direction === 'asc' ? 'desc' : 'asc') : 'asc';
                    currentSort.column = column;
                    localStorage.setItem('sortState', JSON.stringify(currentSort));
                    const sorted = sortAccounts(currentAccounts);
                    updateBrokerSummary(sorted);
                    updateAccountDetails(sorted);
                    updateSortIndicator();
                });
            });

            // Chart filtering
            document.querySelectorAll('.chart-section[data-filter]').forEach(section => {
                section.addEventListener('click', (e) => {
                    const filterType = section.dataset.filter;
                    let broker;
                    if (e.target.tagName === 'CANVAS') {
                        const chart = charts[filterType];
                        const elements = chart.getElementsAtEventForMode(e, 'nearest', { intersect: true }, true);
                        if (elements.length) {
                            broker = chart.data.labels[elements[0].index];
                            if (broker === 'Grand Total' || broker === 'Total') return;
                            currentAccounts = currentAccounts.filter(acc => acc.broker === broker);
                            updateQuickStats(currentAccounts);
                            updateBrokerSummary(currentAccounts);
                            updateAccountDetails(currentAccounts);
                            switchTab('main');
                        }
                    }
                });
            });

            // Initial load and intervals
            if (!localStorage.getItem('periodResets')) resetPeriodTracking();
            fetchData().then(() => {
                setRefreshInterval();
                updateCharts(); // Moved here to ensure data is loaded first
            });
        };

        // Tab switching
        window.switchTab = (tabName) => {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
           
