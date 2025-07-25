/**
 * report.js
 * Chứa logic trực quan hóa dữ liệu cho báo cáo thị trường.
 * Các hàm vẽ biểu đồ thực tế (createGauge, createBarChart, etc.) được giả định là có sẵn trong một file khác (vd: chart.js).
 */

/**
 * Khởi tạo biểu đồ đồng hồ đo cho Chỉ số Sợ hãi và Tham lam.
 * @private
 */
function initializeFearGreedGauge_report() {
    const container = document.getElementById('fear-greed-gauge-container');
    if (!container) return;

    const value = 71; // Giá trị "Tham lam" từ báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ Hãi Tột Độ' },
            { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ Hãi' },
            { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung Lập' },
            { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham Lam' },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham Lam Tột Độ' }
        ]
    };
    
    // Giả định hàm createGauge tồn tại
    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    } else {
        container.innerHTML = `<p>Lỗi: Không tìm thấy hàm createGauge().</p>`;
    }
}

/**
 * Khởi tạo biểu đồ đồng hồ đo cho Chỉ số Sức mạnh Tương đối (RSI).
 * @private
 */
function initializeRsiGauge_report() {
    const container = document.getElementById('rsi-gauge-container');
    if (!container) return;

    const value = 75; // Giá trị "Hơi quá mua" trong khoảng 70-80 từ báo cáo
    const config = {
        min: 0,
        max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá Bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung Lập' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá Mua' }
        ]
    };

    if (typeof createGauge === 'function') {
        createGauge(container, value, config);
    }
}

/**
 * Khởi tạo biểu đồ tròn cho Tỷ lệ thống trị của Bitcoin.
 * @private
 */
function initializeBtcDominanceChart_report() {
    const container = document.getElementById('btc-dominance-chart-container');
    if (!container) return;
    
    // Dựa trên dữ liệu báo cáo (~59-61%), lấy trung bình là 59%
    const data = [
        { value: 59, color: 'var(--neutral-color)' }, // Bitcoin
        { value: 41, color: 'var(--accent-color)' }    // Altcoins
    ];

    if (typeof createDoughnutChart === 'function') {
        createDoughnutChart(container, data);
    }
}

/**
 * Khởi tạo biểu đồ cột cho dòng vốn ETF.
 * @private
 */
function initializeEtfFlowChart_report() {
    const container = document.getElementById('etf-flow-chart-container');
    if (!container) return;

    // Dữ liệu từ báo cáo (tính đến ngày 21-23/7)
    const data = [
        { label: 'Bitcoin ETFs', value: 5.65, color: 'var(--neutral-color)' },
        { label: 'Ethereum ETFs', value: 4.07, color: 'var(--accent-color)' }
    ];
    
    // Ghi chú: Trục Y biểu thị Tỷ USD
    if (typeof createBarChart === 'function') {
        createBarChart(container, data, { valueSuffix: 'B', title: 'Dòng vốn ròng (Tỷ USD)' });
    }
}

/**
 * Khởi tạo biểu đồ đường cho giá Bitcoin giả định.
 * @private
 */
function initializeBtcPriceChart_report() {
    const container = document.getElementById('btc-price-chart-container');
    if (!container) return;
    
    // Dữ liệu giả định dựa trên mô tả trong báo cáo (tăng và củng cố)
    const data = [118500, 119200, 121500, 120800, 122500, 119000, 120000];
    const options = {
        valuePrefix: '$',
        color: 'var(--accent-color)'
    };
    
    if (typeof createLineChart === 'function') {
        createLineChart(container, data, options);
    }
}


/**
 * Hàm chính để khởi tạo tất cả các thành phần trực quan hóa trong báo cáo.
 * Sẽ được gọi sau khi report.html được tải vào DOM.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");
    initializeFearGreedGauge_report();
    initializeRsiGauge_report();
    initializeBtcDominanceChart_report();
    initializeEtfFlowChart_report();
    initializeBtcPriceChart_report();
    console.log("Report visuals initialized.");
}