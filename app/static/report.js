// BẮT ĐẦU NỘI DUNG REPORT.JS

/**
 * Khởi tạo tất cả các thành phần trực quan hóa cho báo cáo.
 * Hàm này sẽ tìm các placeholder trong report.html và vẽ biểu đồ vào đó.
 * Cần được gọi sau khi report.html đã được tải vào DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // 1. Vẽ biểu đồ Fear & Greed Gauge
    drawFearAndGreedGauge_report();

    // 2. Vẽ biểu đồ RSI Gauge
    drawRsiGauge_report();

    // 3. Vẽ biểu đồ BTC Dominance Doughnut
    drawBtcDominanceChart_report();
}

/**
 * Vẽ biểu đồ đồng hồ đo cho chỉ số Sợ hãi & Tham lam.
 */
function drawFearAndGreedGauge_report() {
    const container = document.getElementById('fng-gauge-container');
    if (container && typeof createGauge === 'function') {
        const value = 70; // Giá trị "Tham lam" từ báo cáo
        const config = {
            min: 0,
            max: 100,
            segments: [
                { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cùng cực' },
                { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
                { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung tính' },
                { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
                { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cùng cực' }
            ]
        };
        createGauge(container, value, config);
    } else {
        console.error("Container #fng-gauge-container not found or createGauge function is not available.");
    }
}

/**
 * Vẽ biểu đồ đồng hồ đo cho chỉ số RSI.
 */
function drawRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (container && typeof createGauge === 'function') {
        const value = 58; // Giá trị RSI khung ngày từ báo cáo
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
    } else {
        console.error("Container #rsi-gauge-container not found or createGauge function is not available.");
    }
}

/**
 * Vẽ biểu đồ tròn cho Tỷ lệ Thống trị của Bitcoin (BTC.D).
 */
function drawBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-chart-container');
    if (container && typeof createDoughnutChart === 'function') {
        const btcDominance = 61; // Lấy giá trị trung bình từ báo cáo (60.5% - 61.2%)
        const data = [
            { value: btcDominance, color: 'var(--accent-color)', label: 'Bitcoin' },
            { value: 100 - btcDominance, color: 'var(--neutral-color)', label: 'Altcoins' }
        ];
        const title = `${btcDominance}%`;
        createDoughnutChart(container, data, title);
    } else {
        console.error("Container #btc-dominance-chart-container not found or createDoughnutChart function is not available.");
    }
}

// KẾT THÚC NỘI DUNG REPORT.JS