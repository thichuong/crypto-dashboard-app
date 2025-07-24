// --- report.js ---


/**
 * Hàm chính để khởi tạo tất cả các thành phần trực quan trong báo cáo
 */
function initializeAllVisuals_report() {
    // Dữ liệu mẫu lấy từ báo cáo
    const rsiValue = 54.86;
    const fearAndGreedValue = 70; // Giả định giá trị trong khoảng 67-74
    const btcDominanceData = [66, 65, 63, 61.5, 60, 60.5]; // Dữ liệu minh họa xu hướng giảm

    createRsiGauge_report(rsiValue);
    createFearAndGreedGauge_report(fearAndGreedValue);
    createBtcDominanceChart_report(btcDominanceData);
}

/**
 * Tạo biểu đồ dạng đồng hồ đo (gauge) cho chỉ số RSI
 * @param {number} value - Giá trị RSI hiện tại (0-100)
 */
function createRsiGauge_report(value) {
    const segments = [
        { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá Bán' },
        { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
        { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá Mua' }
    ];
    createGauge_report('rsi-gauge-container', 'RSI', value, 0, 100, segments);
}

/**
 * Tạo biểu đồ dạng đồng hồ đo (gauge) cho Chỉ số Sợ hãi & Tham lam
 * @param {number} value - Giá trị hiện tại của chỉ số (0-100)
 */
function createFearAndGreedGauge_report(value) {
    const segments = [
        { limit: 25, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cực độ' },
        { limit: 45, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
        { limit: 55, color: 'var(--fng-neutral-color)', label: 'Trung tính' },
        { limit: 75, color: 'var(--fng-greed-color)', label: 'Tham lam' },
        { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cực độ' }
    ];
    createGauge_report('fear-greed-gauge-container', 'Fear & Greed', value, 0, 100, segments);
}

/**
 * Hàm chung để tạo biểu đồ gauge SVG
 * @param {string} containerId - ID của div chứa
 * @param {string} label - Nhãn chính của biểu đồ
 * @param {number} value - Giá trị hiện tại
 * @param {number} min - Giá trị tối thiểu
 * @param {number} max - Giá trị tối đa
 * @param {Array<object>} segments - Các đoạn màu và nhãn
 */
function createGauge_report(containerId, label, value, min, max, segments) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const angle = Math.max(0, Math.min(180, (value - min) / (max - min) * 180));
    const svgNamespace = "http://www.w3.org/2000/svg";

    let segmentPaths = '';
    let startAngle = -90;

    segments.forEach(segment => {
        const range = (segment.limit - (segments[segments.indexOf(segment) - 1]?.limit || 0)) / (max - min);
        const endAngle = startAngle + (range * 180);
        segmentPaths += `<path d="${describeArc_report(100, 100, 80, startAngle, endAngle)}" fill="none" stroke="${segment.color}" stroke-width="20"/>`;
        startAngle = endAngle;
    });

    const svg = `
        <svg viewBox="0 0 200 120" xmlns="${svgNamespace}" style="width: 100%; height: auto;">
            <g transform="translate(0, 10)">
                ${segmentPaths}
                <text x="100" y="90" text-anchor="middle" font-size="28" font-weight="bold" fill="var(--text-primary)">${value.toFixed(2)}</text>
                <text x="100" y="110" text-anchor="middle" font-size="14" fill="var(--text-secondary)">${label}</text>
                <g transform="translate(100, 100) rotate(${angle - 90})">
                    <path d="M 0,-70 L 5,0 L -5,0 Z" fill="var(--text-primary)"/>
                </g>
                <circle cx="100" cy="100" r="8" fill="var(--text-primary)"/>
            </g>
        </svg>
    `;
    container.innerHTML = svg;
}

/**
 * Tạo biểu đồ đường SVG đơn giản cho BTC Dominance
 * @param {Array<number>} data - Mảng dữ liệu về % thống trị
 */
function createBtcDominanceChart_report(data) {
    const container = document.getElementById('btc-dominance-chart-container');
    if (!container) return;

    const svgWidth = 300;
    const svgHeight = 150;
    const padding = 20;
    
    const maxValue = Math.max(...data);
    const minValue = Math.min(...data);
    const range = maxValue - minValue;

    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * (svgWidth - 2 * padding) + padding;
        const y = svgHeight - padding - ((d - minValue) / range) * (svgHeight - 2 * padding);
        return `${x},${y}`;
    }).join(' ');

    const svg = `
        <svg viewBox="0 0 ${svgWidth} ${svgHeight}" style="width: 100%; height: auto;">
            <text x="${svgWidth/2}" y="15" text-anchor="middle" font-size="12" fill="var(--text-secondary)">Xu hướng BTC Dominance (%)</text>
            <polyline
                fill="none"
                stroke="var(--accent-color)"
                stroke-width="2"
                points="${points}"
            />
            <circle cx="${points.split(' ')[points.split(' ').length-1].split(',')[0]}" cy="${points.split(' ')[points.split(' ').length-1].split(',')[1]}" r="4" fill="var(--accent-color)" />
            <text x="${padding}" y="${svgHeight - 5}" font-size="10" fill="var(--text-secondary)">${minValue.toFixed(1)}%</text>
            <text x="${svgWidth - padding}" y="${svgHeight - 5}" text-anchor="end" font-size="10" fill="var(--text-secondary)">Tuần gần nhất</text>
        </svg>
    `;

    container.innerHTML = svg;
}


// --- SVG Helper Functions ---
function polarToCartesian_report(centerX, centerY, radius, angleInDegrees) {
    const angleInRadians = (angleInDegrees) * Math.PI / 180.0;
    return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
    };
}

function describeArc_report(x, y, radius, startAngle, endAngle) {
    const start = polarToCartesian_report(x, y, radius, endAngle);
    const end = polarToCartesian_report(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

// Khởi chạy các hàm vẽ khi DOM đã sẵn sàng
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllVisuals_report);
} else {
    initializeAllVisuals_report();
}

