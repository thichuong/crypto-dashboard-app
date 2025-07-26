/**
 * Hàm chính để khởi tạo tất cả các thành phần trực quan cho báo cáo.
 * Sẽ được gọi từ main.js sau khi report.html được tải.
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");
    initFearAndGreedGauge_report();
    initBtcDominanceChart_report();
    initEtfFlowChart_report();
    initBtcPriceTargetChart_report();
}

/**
 * Khởi tạo biểu đồ đồng hồ đo cho Chỉ số Sợ hãi & Tham lam.
 */
function initFearAndGreedGauge_report() {
    try {
        const container = document.getElementById('fear-greed-gauge-container');
        if (!container) return;

        const value = 70;
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
        // Giả sử hàm createGauge tồn tại trong chart.js
        createGauge(container, value, config);
    } catch (error) {
        console.error("Error initializing Fear & Greed gauge:", error);
    }
}

/**
 * Khởi tạo biểu đồ tròn cho Tỷ lệ thống trị của Bitcoin.
 */
function initBtcDominanceChart_report() {
    try {
        const container = document.getElementById('btc-dominance-chart-container');
        if (!container) return;

        const data = [
            { value: 60.6, label: 'Bitcoin', color: 'var(--neutral-color)' },
            { value: 39.4, label: 'Altcoins', color: 'var(--text-accent)' }
        ];
        const title = '60.6%';

        // Giả sử hàm createDoughnutChart tồn tại trong chart.js
        createDoughnutChart(container, data, title);
    } catch (error) {
        console.error("Error initializing BTC Dominance chart:", error);
    }
}

/**
 * Khởi tạo biểu đồ cột cho Dòng vốn ETF.
 */
function initEtfFlowChart_report() {
     try {
        const container = document.getElementById('etf-flow-bar-chart-container');
        if (!container) return;

        const data = [
            { 
                label: 'Bitcoin ETF', 
                value: -131.35, 
                color: 'var(--negative-color)' 
            },
            { 
                label: 'Ethereum ETF', 
                value: 296.60, 
                color: 'var(--positive-color)' 
            }
        ];
        
        // Giả sử hàm createBarChart tồn tại trong chart.js
        // Lưu ý: Cần một phiên bản createBarChart có thể xử lý giá trị âm.
        createBarChart(container, data);
    } catch (error) {
        console.error("Error initializing ETF Flow chart:", error);
    }
}

/**
 * Khởi tạo biểu đồ cột cho Mục tiêu giá BTC của các chuyên gia.
 */
function initBtcPriceTargetChart_report() {
     try {
        const container = document.getElementById('btc-price-target-chart-container');
        if (!container) return;
        
        const data = [
            { label: 'Standard Chartered', value: 200000, color: '#6366f1' },
            { label: 'Bernstein', value: 200000, color: '#818cf8' },
            { label: 'Citigroup (Base)', value: 135000, color: '#a5b4fc' }
        ];

        // Giả sử hàm createLineChart tồn tại trong chart.js
        createBarChart(container, data);
    } catch (error) {
        console.error("Error initializing BTC Price Target chart:", error);
    }
}

// Hàm giả định (để kiểm tra độc lập nếu cần)
// function createGauge(container, value, config) { container.innerHTML = `<p>Gauge: ${value}</p>`; }
// function createDoughnutChart(container, data, title) { container.innerHTML = `<p>Doughnut: ${title}</p>`; }
// function createBarChart(container, data) { container.innerHTML = `<p>Bar Chart with ${data.length} bars</p>`; }