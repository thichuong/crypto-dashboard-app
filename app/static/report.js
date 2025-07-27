/**
 * Khởi tạo tất cả các thành phần trực quan hóa cho báo cáo.
 * Hàm này tìm các container placeholder trong report.html và vẽ các biểu đồ tương ứng.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // Gọi các hàm để vẽ từng biểu đồ
    createFearAndGreedGauge_report();
    createBtcDominanceChart_report();
    createBtcRsiGauge_report();
}

/**
 * Tạo biểu đồ đồng hồ đo cho Chỉ số Sợ hãi & Tham lam.
 */
function createFearAndGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (container && typeof createGauge === 'function') {
        const value = 70; // Giá trị ví dụ từ báo cáo (dao động 64-74)
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
}

/**
 * Tạo biểu đồ tròn (Doughnut) cho Tỷ lệ thống trị của Bitcoin.
 */
function createBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-doughnut-container');
    if (container && typeof createDoughnutChart === 'function') {
        const btcDominance = 61; // Giá trị ví dụ từ báo cáo (60-61%)
        const data = [
            { value: btcDominance, color: 'var(--icon-color-btc)', label: 'Bitcoin' },
            { value: 100 - btcDominance, color: 'var(--text-accent)', label: 'Altcoins' }
        ];
        createDoughnutChart(container, data, `${btcDominance}%`);
    }
}

/**
 * Tạo biểu đồ đồng hồ đo cho Chỉ số Sức mạnh Tương đối (RSI) của Bitcoin.
 */
function createBtcRsiGauge_report() {
    const container = document.getElementById('btc-rsi-gauge-container');
    if (container && typeof createGauge === 'function') {
        const value = 70; // Giá trị ví dụ từ báo cáo (tiến gần 70)
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
}