/**
 * report.js
 * Chứa các hàm để khởi tạo và vẽ các biểu đồ cho báo cáo.
 * Tất cả các hàm trong tệp này đều có hậu tố _report để tránh xung đột.
 */

/**
 * Hàm chính để khởi tạo tất cả các thành phần trực quan trong báo cáo.
 * Hàm này sẽ được gọi sau khi report.html được tải vào DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");
    drawFearAndGreedGauge_report();
    drawRsiGauge_report();
    drawBtcDominanceChart_report();
    drawScenarioProbabilityChart_report();
}

/**
 * Vẽ biểu đồ Gauge cho Chỉ số Sợ hãi & Tham lam.
 */
function drawFearAndGreedGauge_report() {
    const container = document.getElementById('fng-gauge-container');
    if (!container) return;

    const value = 70; // Giá trị "Tham lam" từ báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cực độ' },
            { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
            { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung lập' },
            { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cực độ' }
        ]
    };

    // Giả sử hàm createGauge tồn tại trong chart.js
    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    }
}

/**
 * Vẽ biểu đồ Gauge cho Chỉ số Sức mạnh Tương đối (RSI).
 */
function drawRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (!container) return;

    const value = 65; // Giá trị RSI tuần từ báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };
    
    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    }
}

/**
 * Vẽ biểu đồ Doughnut cho Tỷ lệ thống trị của Bitcoin.
 */
function drawBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-chart');
    if (!container) return;

    const dominance = 61; // Giá trị từ báo cáo (~60.5% - 61.2%)
    const data = [
        { label: 'Bitcoin', value: dominance, color: 'var(--neutral-color)' },
        { label: 'Altcoins', value: 100 - dominance, color: 'var(--text-accent)' }
    ];

    if (typeof createDoughnutChart === 'function') {
        createDoughnutChart(container, data, 'BTC.D');
    }
}

/**
 * Vẽ biểu đồ Doughnut cho xác suất các kịch bản thị trường.
 */
function drawScenarioProbabilityChart_report() {
    const container = document.getElementById('scenario-probability-chart');
    if (!container) return;

    const data = [
        { label: 'Tăng giá', value: 45, color: 'var(--positive-color)' },
        { label: 'Đi ngang', value: 35, color: 'var(--neutral-color)' },
        { label: 'Giảm giá', value: 20, color: 'var(--negative-color)' }
    ];
    
    if (typeof createDoughnutChart === 'function') {
        createDoughnutChart(container, data, 'Xác suất');
    }
}

// Lưu ý: Đoạn mã này giả định rằng các hàm `createGauge` và `createDoughnutChart`
// đã được định nghĩa và có sẵn trong tệp `chart.js` được tải toàn cục.