/**
 * Khởi tạo tất cả các thành phần trực quan hóa cho báo cáo.
 * Hàm này sẽ được gọi sau khi report.html được tải vào DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");
    
    // An toàn: chỉ chạy các hàm nếu element tồn tại
    const runIfPresent = (id, func) => {
        const element = document.getElementById(id);
        if (element) {
            func(element);
        } else {
            console.warn(`Element with ID #${id} not found. Skipping visualization.`);
        }
    };

    runIfPresent('fearGreedGaugeContainer', initializeFearGreedGauge_report);
    runIfPresent('btcDominanceDoughnut', initializeBtcDominanceDoughnut_report);
    runIfPresent('btcRsiGaugeContainer', initializeBtcRsiGauge_report);
    runIfPresent('etfFlowsBarChart', initializeEtfFlowsBarChart_report);
}

/**
 * Vẽ biểu đồ Gauge cho Chỉ số Sợ hãi & Tham lam.
 * @param {HTMLElement} container - Element để vẽ biểu đồ.
 */
function initializeFearGreedGauge_report(container) {
    const value = 70; // Giá trị ví dụ từ báo cáo (64-74)
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
    // Giả sử hàm createGauge có sẵn trong chart.js
    createGauge(container, value, config);
}

/**
 * Vẽ biểu đồ Doughnut cho Tỷ lệ Thống trị của Bitcoin.
 * @param {HTMLElement} container - Element để vẽ biểu đồ.
 */
function initializeBtcDominanceDoughnut_report(container) {
    const data = [
        { value: 61, color: 'var(--icon-color-btc)', label: 'Bitcoin (BTC)' },
        { value: 39, color: 'var(--text-secondary)', label: 'Altcoins' }
    ];
    // Giả sử hàm createDoughnutChart có sẵn trong chart.js
    createDoughnutChart(container, data, '61%');
}

/**
 * Vẽ biểu đồ Gauge cho chỉ số RSI của Bitcoin.
 * @param {HTMLElement} container - Element để vẽ biểu đồ.
 */
function initializeBtcRsiGauge_report(container) {
    const value = 68; // Giá trị ví dụ "gần 70" từ báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };
    // Giả sử hàm createGauge có sẵn trong chart.js
    createGauge(container, value, config);
}

/**
 * Vẽ biểu đồ cột cho Dòng tiền vào các Quỹ ETF.
 * @param {HTMLElement} container - Element để vẽ biểu đồ.
 */
function initializeEtfFlowsBarChart_report(container) {
    const data = [
        { value: 19, label: 'BTC ETF Tổng', color: 'var(--icon-color-btc)' },
        { value: 8, label: 'BTC ETF (Tháng qua)', color: 'var(--icon-color-btc-analysis)' },
        { value: 3, label: 'ETH ETF (Gần đây)', color: 'var(--icon-color-eth)' }
    ];

    // Giả sử hàm createBarChart có sẵn trong chart.js
    // Chúng ta cần một phiên bản của createBarChart hỗ trợ giá trị
    // hoặc một hàm khác như createLineChart. Ở đây, ta dùng Bar Chart để so sánh.
    createBarChart(container, data);
    // Thêm một ghi chú về đơn vị
    const note = document.createElement('p');
    note.textContent = 'Đơn vị: Tỷ USD ($B)';
    note.style.textAlign = 'center';
    note.style.fontSize = '0.8rem';
    note.style.color = 'var(--text-secondary)';
    note.style.marginTop = '0.5rem';
    container.appendChild(note);
}