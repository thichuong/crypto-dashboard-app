/**
 * report.js
 * Chứa các hàm để vẽ biểu đồ cho báo cáo phân tích thị trường crypto.
 * Phụ thuộc vào chart.js để vẽ các biểu đồ thực tế.
 */

// Hàm khởi tạo chính cho tất cả các hình ảnh trong báo cáo
function initializeAllVisuals_report() {
    try {
        setupFearGreedGauge_report();
        setupRsiGauge_report();
        setupDominanceDoughnut_report();
        setupEtfFlowBarChart_report();
    } catch (error) {
        console.error("Lỗi khi khởi tạo các biểu đồ báo cáo:", error);
    }
}

/**
 * Thiết lập biểu đồ đồng hồ cho Chỉ số Sợ hãi & Tham lam.
 */
function setupFearGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (!container || typeof createGauge !== 'function') return;

    const value = 71; // Tham lam
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cực độ' },
            { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
            { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung tính' },
            { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cực độ' }
        ]
    };
    createGauge(container, value, config);
}

/**
 * Thiết lập biểu đồ đồng hồ cho Chỉ số Sức mạnh Tương đối (RSI).
 */
function setupRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (!container || typeof createGauge !== 'function') return;
    
    const value = 55; // Trung tính
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };
    createGauge(container, value, config);
}

/**
 * [ĐÃ SỬA] Thiết lập biểu đồ tròn (Doughnut) cho Tỷ lệ Thống trị Thị trường.
 */
function setupDominanceDoughnut_report() {
    const container = document.getElementById('dominance-doughnut-container');
    if (!container || typeof createDoughnutChart !== 'function') return;

    const btcDominance = 59.7;
    const ethDominance = 11.5;
    const otherDominance = 100 - btcDominance - ethDominance;

    const data = [
        { value: btcDominance, color: 'var(--neutral-color)', label: 'Bitcoin' },
        { value: ethDominance, color: 'var(--accent-color)', label: 'Ethereum' },
        { value: otherDominance, color: 'var(--text-secondary)', label: 'Altcoins khác' }
    ];

    createDoughnutChart(container, data, 'Tỷ lệ Thống trị');
}

/**
 * Thiết lập biểu đồ cột so sánh dòng vốn ròng ETF.
 */
function setupEtfFlowBarChart_report() {
    const container = document.getElementById('etf-flow-bar-chart-container');
    if (!container || typeof createBarChart !== 'function') return;

    const data = [
        { label: 'Bitcoin ETFs', value: 827, color: 'var(--neutral-color)'},
        { label: 'Ethereum ETFs', value: 2400, color: 'var(--accent-color)'}
    ];

    createBarChart(container, data);
}