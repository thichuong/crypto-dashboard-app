/**
 * Khởi tạo tất cả các thành phần trực quan hóa cho báo cáo.
 * Hàm này sẽ được gọi bởi main.js sau khi nội dung báo cáo được tải.
 */
function initializeAllVisuals_report() {
    try {
        // Kiểm tra xem thư viện chart đã được tải chưa
        if (typeof createGauge === 'undefined' || typeof createDoughnutChart === 'undefined' || typeof createBarChart === 'undefined') {
            console.error("Lỗi: Thư viện 'chart.js' chưa được tải. Không thể vẽ biểu đồ.");
            return;
        }

        console.log("Đang khởi tạo các biểu đồ cho báo cáo...");

        initializeFearGreedGauge_report();
        initializeBtcDominanceDoughnut_report();
        initializeRsiGauge_report();
        initializeEtfInflowBarChart_report();

        console.log("Tất cả biểu đồ đã được khởi tạo thành công.");

    } catch (error) {
        console.error("Đã xảy ra lỗi trong quá trình khởi tạo biểu đồ báo cáo:", error);
    }
}

/**
 * Vẽ biểu đồ đồng hồ đo Chỉ số Sợ hãi & Tham lam.
 */
function initializeFearGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (!container) return;

    const fearGreedValue = 70; // Giá trị từ báo cáo
    const fearGreedConfig = {
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

    createGauge(container, fearGreedValue, fearGreedConfig);
}

/**
 * Vẽ biểu đồ tròn Tỷ lệ Thống trị của Bitcoin (BTC.D).
 */
function initializeBtcDominanceDoughnut_report() {
    const container = document.getElementById('btc-dominance-doughnut-container');
    if (!container) return;

    const btcDominanceData = [
        { label: 'Bitcoin', value: 61, color: 'var(--icon-color-btc)' },
        { label: 'Altcoins', value: 39, color: 'var(--text-secondary)' }
    ];

    createDoughnutChart(container, btcDominanceData, 'BTC.D');
}

/**
 * Vẽ biểu đồ đồng hồ đo Chỉ số Sức mạnh Tương đối (RSI).
 */
function initializeRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (!container) return;

    const rsiValue = 68; // Giá trị "tiến gần 70" từ báo cáo
    const rsiConfig = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
        ]
    };
    createGauge(container, rsiValue, rsiConfig);
}

/**
 * Vẽ biểu đồ cột Dòng tiền vào các Quỹ ETF.
 */
function initializeEtfInflowBarChart_report() {
    const container = document.getElementById('etf-inflow-bar-chart-container');
    if (!container) return;

    const etfData = [
        { label: 'BTC ETF (Tổng)', value: 19, color: 'var(--icon-color-btc)' },
        { label: 'BTC ETF (Tháng qua)', value: 8, color: 'hsla(36, 96%, 53%, 0.7)' },
        { label: 'ETH ETF (Tháng qua)', value: 3, color: 'var(--icon-color-eth)' }
    ];
    
    const etfOptions = {
        valueSuffix: ' Tỷ USD',
        yAxisLabel: 'Dòng tiền ròng'
    };

    createBarChart(container, etfData, etfOptions);
}