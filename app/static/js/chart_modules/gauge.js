// static/chart_modules/gauge.js

/**
 * TẠO BIỂU ĐỒ ĐỒNG HỒ (GAUGE)
 * Phụ thuộc: utils.js (polarToCartesian, describeArc)
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {number} value - Giá trị hiện tại.
 * @param {object} config - Cấu hình chi tiết cho biểu đồ.
 */
function createGauge(container, value, config) {
    if (!container) return;

    // --- CẤU HÌNH GAUGE ---
    const { min = 0, max = 100, segments } = config;
    const GAUGE_START_ANGLE = -120;
    const GAUGE_END_ANGLE = 120;
    const ANGLE_SPAN = GAUGE_END_ANGLE - GAUGE_START_ANGLE;

    // --- TÍNH TOÁN ---
    const clampedValue = Math.max(min, Math.min(max, value));
    const percentage = (clampedValue - min) / (max - min);
    const valueAngle = GAUGE_START_ANGLE + (percentage * ANGLE_SPAN);

    const currentSegment = segments.find(s => clampedValue <= s.limit) || segments[segments.length - 1];
    const valueColor = currentSegment.color;
    const classification = currentSegment.label || '';

    // --- VẼ CÁC ĐOẠN MÀU ---
    let segmentPaths = '';
    let lastPercentage = 0;

    segments.forEach(segment => {
        const segmentEndPercentage = (segment.limit - min) / (max - min);
        const start = GAUGE_START_ANGLE + (lastPercentage * ANGLE_SPAN);
        const end = GAUGE_START_ANGLE + (segmentEndPercentage * ANGLE_SPAN);

        segmentPaths += `<path d="${describeArc(100, 100, 85, start, end)}"
                             fill="none" stroke="${segment.color}" stroke-width="22" />`;
        lastPercentage = segmentEndPercentage;
    });

    const svg = `
        <svg viewBox="0 0 200 165" style="width: 100%; height: auto; overflow: visible;" class="gauge-interactive">
            <path d="${describeArc(100, 100, 85, GAUGE_START_ANGLE, GAUGE_END_ANGLE)}"
                  fill="none" stroke="var(--bg-primary)" stroke-width="22" stroke-linecap="round"/>
            <g>${segmentPaths}</g>
            <g transform="rotate(${valueAngle} 100 100)" class="gauge-needle">
                <path d="M 100 20 L 97 100 L 103 100 Z" fill="var(--text-primary)"/>
                <circle cx="100" cy="100" r="6" fill="var(--text-primary)"/>
            </g>
            <text x="100" y="105" text-anchor="middle" font-size="32px" font-weight="800"
                  fill="var(--text-primary)" class="gauge-value-text">
                ${value.toFixed(1)}
            </text>
            <text x="100" y="130" text-anchor="middle" font-size="16px" font-weight="600"
                  fill="${valueColor}" class="gauge-label-text">
                ${classification}
            </text>
        </svg>
    `;
    container.innerHTML = svg;
    container.classList.add('gauge-container');
}