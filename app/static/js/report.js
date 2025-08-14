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

        // Lắng nghe sự kiện thay đổi ngôn ngữ để refresh charts (chỉ thêm listener 1 lần)
        if (!window._reportLangListenerAdded) {
            window._reportLangListenerAdded = true;
            window.addEventListener('languageChanged', () => {
                // Re-run full initialization for the report visuals on language change
                try {
                    initializeAllVisuals_report();
                } catch (err) {
                    console.error('Error re-initializing report visuals after language change:', err);
                }
            });
        }
    } catch (error) {
        console.error("An error occurred during report visualization setup:", error);
    }
}

// Helper: return the active report content container (vi or en) or report-container as fallback
function getActiveReportRoot() {
    const reportContainer = document.getElementById('report-container');
    if (!reportContainer) return document;
    const vi = document.getElementById('report-content-vi');
    const en = document.getElementById('report-content-en');
    try {
        if (vi && window.getComputedStyle(vi).display !== 'none') return vi;
        if (en && window.getComputedStyle(en).display !== 'none') return en;
    } catch (e) {
        // fallback
    }
    return reportContainer;
}

/**
 * Hàm lấy text đã dịch cho report charts
 */
function getTranslatedText_report(key) {
    if (window.languageManager && window.languageManager.getTranslatedText) {
        return window.languageManager.getTranslatedText(key);
    }
    
    // Fallback translations
    const fallback = {
        'extreme-fear': 'Sợ hãi Tột độ',
        'fear': 'Sợ hãi',
        'neutral': 'Trung lập',
        'greed': 'Tham lam',
        'extreme-greed': 'Tham lam Tột độ',
        'oversold': 'Quá bán',
        'overbought': 'Quá mua'
    };
    return fallback[key] || key;
}

/**
 * Refresh tất cả charts trong report khi ngôn ngữ thay đổi
 */
function refreshReportCharts() {
    try {
        setupFearGreedGauge_report();
        setupBtcDominanceChart_report();
        setupBtcRsiGauge_report();
        setupEtfInflowChart_report();
    } catch (error) {
        console.error("Error refreshing report charts:", error);
    }
}

/**
 * Sets up the Fear & Greed Index Gauge.
 */
function setupFearGreedGauge_report() {
    const root = getActiveReportRoot();
    const container = root.querySelector ? root.querySelector('#fear-greed-gauge-container') : document.getElementById('fear-greed-gauge-container');
    if (!container) return;

    const value = 68; // Based on the text "dao động từ 64 đến 74"
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: getTranslatedText_report('extreme-fear') },
            { limit: 45, color: 'var(--fng-fear-color)', label: getTranslatedText_report('fear') },
            { limit: 55, color: 'var(--fng-neutral-color)', label: getTranslatedText_report('neutral') },
            { limit: 75, color: 'var(--fng-greed-color)', label: getTranslatedText_report('greed') },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: getTranslatedText_report('extreme-greed') }
        ]
    };

    createGauge(container, value, config);
}

/**
 * Sets up the BTC Dominance Doughnut Chart.
 */
function setupBtcDominanceChart_report() {
    const root = getActiveReportRoot();
    const container = root.querySelector ? root.querySelector('#btc-dominance-doughnut-container') : document.getElementById('btc-dominance-doughnut-container');
    if (!container) return;

    const btcDominance = 61; // Based on the text "dao động quanh ngưỡng 60-61%"
    const data = [
    { value: btcDominance, color: 'var(--icon-color-btc)', label: getTranslatedText_report('bitcoin') || 'Bitcoin' },
    { value: 100 - btcDominance, color: 'var(--text-secondary)', label: getTranslatedText_report('altcoins') || 'Altcoins' }
    ];
    const config = { title: 'BTC.D', showLegend: true };

    createDoughnutChart(container, data, config);
}

/**
 * Sets up the BTC RSI Gauge.
 */
function setupBtcRsiGauge_report() {
    const root = getActiveReportRoot();
    const container = root.querySelector ? root.querySelector('#btc-rsi-gauge-container') : document.getElementById('btc-rsi-gauge-container');
    if (!container) return;

    const value = 69; // Based on the text "tiến gần đến vùng quá mua (mức 70)"
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: getTranslatedText_report('oversold') },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: getTranslatedText_report('neutral') },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: getTranslatedText_report('overbought') }
        ]
    };

    createGauge(container, value, config);
}

/**
 * Sets up the ETF Net Inflow Bar Chart.
 */
function setupEtfInflowChart_report() {
    const root = getActiveReportRoot();
    const container = root.querySelector ? root.querySelector('#etf-inflow-bar-chart-container') : document.getElementById('etf-inflow-bar-chart-container');
    if (!container) return;

    // Determine current language from languageManager or localStorage
    const currentLanguage = (window.languageManager && window.languageManager.currentLanguage) || localStorage.getItem('preferred_language') || localStorage.getItem('language') || 'vi';

    // Data extracted from the report text
    const data = currentLanguage === 'en' ? [
        { label: 'IBIT (Last Month)', value: 6, color: 'var(--positive-color)' },
        { label: 'ETH ETFs (Last Month)', value: 3, color: 'var(--positive-color)' },
        { label: 'BTC ETFs (Last Month)', value: 8, color: 'var(--accent-color)' },
        { label: 'BTC ETFs (Total)', value: 19, color: 'var(--text-primary)' }
    ] : [
        { label: 'IBIT (Tháng qua)', value: 6, color: 'var(--positive-color)' },
        { label: 'ETH ETFs (Tháng qua)', value: 3, color: 'var(--positive-color)' },
        { label: 'BTC ETFs (Tháng qua)', value: 8, color: 'var(--accent-color)' },
        { label: 'BTC ETFs (Tổng)', value: 19, color: 'var(--text-primary)' }
    ];

    const options = {
        valueSuffix: currentLanguage === 'en' ? 'B' : ' Tỷ',
        yAxisLabel: currentLanguage === 'en' ? 'Net Inflow (USD)' : 'Dòng vốn ròng (USD)'
    };

    createBarChart(container, data, options);
}

// Example of how this might be called from main.js after loading the report
// document.addEventListener('DOMContentLoaded', () => {
//    // Assume report content is loaded into #report-container
//    // Then call:
//    // initializeAllVisuals_report();
// });