/**
 * =================================================================
 * SCRIPT FOR REPORT VISUALIZATIONS
 * Contains functions to draw charts and visuals for the report.
 * Assumes a chart library (chart.js) with createGauge, createDoughnutChart, etc. is available.
 * =================================================================
 */

/**
 * Main initialization function to be called after the report HTML is loaded.
 * It orchestrates the creation of all visual elements in the report.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // Call individual chart creation functions
    createFearAndGreedGauge_report();
    createBtcRsiGauge_report();
    createBtcDominanceDoughnut_report();
    createEtfInflowChart_report();

    console.log("Report visuals initialized successfully.");
}

/**
 * Creates the Fear & Greed Index gauge chart.
 */
function createFearAndGreedGauge_report() {
    const container = document.getElementById('fng-gauge-container');
    if (!container) return;

    // Value from the report text (oscillating around 70)
    const value = 70; 

    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Tột độ' },
            { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
            { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung lập' },
            { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Tột độ' }
        ]
    };

    // Assuming createGauge is globally available from chart.js
    createGauge(container, value, config);
}

/**
 * Creates the Bitcoin RSI gauge chart.
 */
function createBtcRsiGauge_report() {
    const container = document.getElementById('btc-rsi-gauge');
    if (!container) return;

    // Value from the report text ("nearing 70")
    const value = 68;

    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán (Oversold)' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung lập (Neutral)' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua (Overbought)' }
        ]
    };

    createGauge(container, value, config);
}


/**
 * Creates the Bitcoin Dominance doughnut chart.
 */
function createBtcDominanceDoughnut_report() {
    const container = document.getElementById('btc-dominance-doughnut');
    if (!container) return;

    // Data based on the report text (BTC.D ~60-61%, with ETH and others making up the rest)
    const data = [
        { value: 61, label: 'Bitcoin (BTC)', color: '#F7931A' },
        { value: 21, label: 'Ethereum (ETH)', color: '#627EEA' },
        { value: 18, label: 'Các Altcoin khác', color: 'var(--text-secondary)' }
    ];

    const title = 'BTC.D ~61%';

    // Assuming createDoughnutChart is globally available from chart.js
    createDoughnutChart(container, data, title);
}


/**
 * Creates the ETF Net Inflow bar chart.
 */
function createEtfInflowChart_report() {
    const container = document.getElementById('etf-inflow-bar-chart');
    if (!container) return;

    // Data derived from report text, in Billions USD
    const data = [
        { label: 'Tổng Net Inflow (BTC)', value: 19, color: 'var(--positive-color)' },
        { label: 'BTC (Tháng qua)', value: 8, color: 'var(--accent-color)' },
        { label: 'IBIT (Tháng qua)', value: 6, color: 'var(--text-primary)' },
        { label: 'ETH (Tháng qua)', value: 3, color: '#627EEA' }
    ];
    
    // Assuming createBarChart is globally available from chart.js
    createBarChart(container, data);
    
    // Add a small note about the units
    const note = document.createElement('p');
    note.textContent = 'Ghi chú: Giá trị được tính bằng tỷ đô la Mỹ ($B).';
    note.style.textAlign = 'center';
    note.style.fontSize = '0.8rem';
    note.style.color = 'var(--text-secondary)';
    note.style.marginTop = '1rem';
    container.appendChild(note);
}