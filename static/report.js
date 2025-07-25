// --- report.js ---


/**
 * Hàm chính để khởi tạo tất cả các thành phần trực quan trong báo cáo
 */
function initializeAllVisuals_report() {
    // Dữ liệu mẫu lấy từ báo cáo
    const rsiValue = 54.86;
    const fearAndGreedValue = 70;
    const btcDominanceData = [66, 65, 63, 61.5, 60, 60.5];

    // Sử dụng hàm createGauge từ chart.js
    const rsiContainer = document.getElementById('rsi-gauge-container');
    const rsiConfig = {
        min: 0, max: 100,
        segments: [
            { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá Bán' },
            { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
            { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá Mua' }
        ]
    };
    createGauge(rsiContainer, rsiValue, rsiConfig);

    const fngContainer = document.getElementById('fear-greed-gauge-container');
    const fngConfig = {
        min: 0, max: 100,
        segments: [
            { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cực độ' },
            { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
            { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung tính' },
            { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
            { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cực độ' }
        ]
    };
    createGauge(fngContainer, fearAndGreedValue, fngConfig);

    // Sử dụng hàm createLineChart từ chart.js
    const btcDominanceContainer = document.getElementById('btc-dominance-chart-container');
    createLineChart(btcDominanceContainer, btcDominanceData, { color: 'var(--accent-color)' });
}

// Khởi chạy các hàm vẽ khi DOM đã sẵn sàng
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllVisuals_report);
} else {
    initializeAllVisuals_report();
}

