/**
 * Khởi tạo tất cả các yếu tố trực quan hóa cho báo cáo.
 * Hàm này sẽ được gọi sau khi report.html được tải vào DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // 1. Vẽ biểu đồ đồng hồ đo cho Chỉ số Sợ hãi & Tham lam
    drawFearAndGreedGauge_report();

    // 2. Vẽ biểu đồ đồng hồ đo cho Chỉ số RSI
    drawRsiGauge_report();

    // 3. Vẽ biểu đồ đường cho Tỷ lệ Thống trị của Bitcoin
    drawBtcDominanceChart_report();

    // 4. Vẽ biểu đồ tròn cho các Kịch bản Thị trường
    drawScenarioChart_report();

    console.log("Report visuals initialized.");
}

/**
 * Vẽ biểu đồ đồng hồ đo cho Chỉ số Sợ hãi & Tham lam.
 */
function drawFearAndGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (!container) return;

    const value = 70; // Giá trị "Greed" được đề cập trong báo cáo
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
    // Giả sử hàm createGauge tồn tại trong chart.js
    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    }
}

/**
 * Vẽ biểu đồ đồng hồ đo cho Chỉ số RSI của Bitcoin.
 */
function drawRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (!container) return;

    const value = 65; // Giá trị RSI tuần được đề cập trong báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung lập' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };
    // Giả sử hàm createGauge tồn tại trong chart.js
    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    }
}

/**
 * Vẽ biểu đồ đường cho Tỷ lệ Thống trị của Bitcoin (BTC.D).
 */
function drawBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-chart-container');
    if (!container) return;
    
    // Dữ liệu giả định mô phỏng xu hướng giảm nhẹ như mô tả
    const data = [62.5, 62.1, 61.8, 61.5, 61.2, 60.8]; 
    const options = {
        color: 'var(--accent-color)',
        valueSuffix: '%'
    };
    
    // Giả sử hàm createLineChart tồn tại trong chart.js
    if (typeof createLineChart === 'function') {
        createLineChart(container, data, options);
    }
}

/**
 * Vẽ biểu đồ tròn thể hiện xác suất của các kịch bản thị trường.
 */
function drawScenarioChart_report() {
    const container = document.getElementById('scenario-probability-chart-container');
    if (!container) return;

    // Dữ liệu từ phần đánh giá tổng thể
    const data = [
        { value: 45, label: 'Tăng giá', color: 'var(--positive-color)' },
        { value: 35, label: 'Đi ngang', color: 'var(--neutral-color)' },
        { value: 20, label: 'Giảm giá', color: 'var(--negative-color)' }
    ];
    const title = 'Xác suất';

    // Giả sử hàm createDoughnutChart tồn tại trong chart.js
    if (typeof createDoughnutChart === 'function') {
        createDoughnutChart(container, data, title);
    }
}