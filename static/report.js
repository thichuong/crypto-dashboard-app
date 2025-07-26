/**
 * Khởi tạo tất cả các thành phần trực quan hóa dữ liệu cho báo cáo.
 * Hàm này sẽ được gọi bởi main.js sau khi nội dung report.html được tải.
 * Các hàm vẽ biểu đồ (createGauge, createDoughnutChart, createBarChart) được giả định là tồn tại trong file chart.js
 */
function initializeAllVisuals_report() {
    console.log("Initializing report visuals...");

    // 1. Biểu đồ Gauge: Chỉ số Sợ hãi & Tham lam
    const fngGaugeContainer = document.getElementById('fng-gauge-container');
    if (fngGaugeContainer) {
        createGauge(fngGaugeContainer, 71, {
            min: 0,
            max: 100,
            segments: [
                { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Tột độ' },
                { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
                { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung lập' },
                { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
                { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Tột độ' }
            ]
        });
    }

    // 2. Biểu đồ Gauge: RSI cho Bitcoin (BTC)
    const rsiGaugeBtcContainer = document.getElementById('rsi-gauge-container-btc');
    if (rsiGaugeBtcContainer) {
        createGauge(rsiGaugeBtcContainer, 65, {
            min: 0,
            max: 100,
            segments: [
                { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá Bán' },
                { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung Lập' },
                { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá Mua' }
            ]
        });
    }
    
    // 3. Biểu đồ Gauge: RSI cho Ethereum (ETH)
    const rsiGaugeEthContainer = document.getElementById('rsi-gauge-container-eth');
    if (rsiGaugeEthContainer) {
        createGauge(rsiGaugeEthContainer, 79, {
            min: 0,
            max: 100,
            segments: [
                { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá Bán' },
                { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung Lập' },
                { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá Mua' }
            ]
        });
    }

    // 4. Biểu đồ Doughnut: Tỷ lệ thống trị của Bitcoin
    const btcDominanceContainer = document.getElementById('btc-dominance-chart');
    if (btcDominanceContainer) {
        const btcDominanceData = [
            { value: 60.6, label: 'Bitcoin', color: 'var(--neutral-color)' },
            { value: 100 - 60.6, label: 'Altcoins', color: 'var(--accent-color)' }
        ];
        createDoughnutChart(btcDominanceContainer, btcDominanceData, '60.6%');
    }
    
    // 5. Biểu đồ cột: Dòng vốn ETF
    const etfFlowContainer = document.getElementById('etf-flow-chart');
    if (etfFlowContainer) {
        const etfFlowData = [
            { label: 'Bitcoin ETF (Dòng ra)', value: 131, color: 'var(--negative-color)' },
            { label: 'Ethereum ETF (Dòng vào)', value: 296, color: 'var(--positive-color)' }
        ];
        createBarChart(etfFlowContainer, etfFlowData);
    }

    console.log("Report visuals initialized.");
}