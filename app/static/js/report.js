/**
 * Initializes all visualizations for the crypto report.
 * This function should be called after the report's HTML is loaded into the DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // Check if charting library is available
    if (typeof createGauge !== 'function' || typeof createDoughnutChart !== 'function' || typeof createBarChart !== 'function') {
        console.error("Charting library (chart.js) is not loaded. Cannot initialize report visuals.");
        return;
    }

    try {
        setupFearGreedGauge_report();
        setupBtcDominanceChart_report();
        setupBtcRsiGauge_report();
        setupEtfInflowChart_report();
    } catch (error) {
        console.error("An error occurred during report visualization setup:", error);
    }
}

/**
 * Sets up the Fear & Greed Index Gauge.
 */
function setupFearGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (!container) return;

    const value = 68; // Based on the text "dao động từ 64 đến 74"
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

    createGauge(container, value, config);
}

/**
 * Sets up the BTC Dominance Doughnut Chart.
 */
function setupBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-doughnut-container');
    if (!container) return;

    const btcDominance = 61; // Based on the text "dao động quanh ngưỡng 60-61%"
    const data = [
        { value: btcDominance, color: 'var(--icon-color-btc)', label: 'Bitcoin' },
        { value: 100 - btcDominance, color: 'var(--text-secondary)', label: 'Altcoins' }
    ];
    const config = { title: 'BTC.D', showLegend: true };

    createDoughnutChart(container, data, config);
}

/**
 * Sets up the BTC RSI Gauge.
 */
function setupBtcRsiGauge_report() {
    const container = document.getElementById('btc-rsi-gauge-container');
    if (!container) return;

    const value = 69; // Based on the text "tiến gần đến vùng quá mua (mức 70)"
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung lập' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };

    createGauge(container, value, config);
}

/**
 * Sets up the ETF Net Inflow Bar Chart.
 */
function setupEtfInflowChart_report() {
    const container = document.getElementById('etf-inflow-bar-chart-container');
    if (!container) return;

    // Data extracted from the report text
    const data = [
        { label: 'IBIT (Tháng qua)', value: 6, color: 'var(--positive-color)' },
        { label: 'ETH ETFs (Tháng qua)', value: 3, color: 'var(--positive-color)' },
        { label: 'BTC ETFs (Tháng qua)', value: 8, color: 'var(--accent-color)' },
        { label: 'BTC ETFs (Tổng)', value: 19, color: 'var(--text-primary)' }
    ];

    const options = {
        valueSuffix: ' Tỷ',
        yAxisLabel: 'Dòng vốn ròng (USD)'
    };

    createBarChart(container, data, options);
}

// Example of how this might be called from main.js after loading the report
// document.addEventListener('DOMContentLoaded', () => {
//    // Assume report content is loaded into #report-container
//    // Then call:
//    // initializeAllVisuals_report();
// });