// static/chart.js

/**
 * -----------------------------------------------------------------------------
 * THƯ VIỆN VẼ BIỂU ĐỒ SVG NÂNG CAO
 * -----------------------------------------------------------------------------
 * Phiên bản cải tiến với hiệu ứng (animation), thiết kế đẹp hơn và
 * tính toán chính xác hơn cho các biểu đồ.
 *
 * - Sử dụng các biến CSS (--text-primary, --accent-color, v.v.) để tự động
 * thích ứng với Light/Dark mode.
 * - Thêm hiệu ứng chuyển động khi vẽ.
 * - Cải thiện thẩm mỹ và độ rõ ràng của các biểu đồ.
 */

/**
 * Hàm trợ giúp: Chuyển đổi tọa độ cực sang Descartes cho cung tròn.
 * @returns {{x: number, y: number}}
 */
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
        x: centerX + radius * Math.cos(angleInRadians),
        y: centerY + radius * Math.sin(angleInRadians),
    };
}

/**
 * Hàm trợ giúp: Tạo chuỗi "d" cho thuộc tính path của SVG để vẽ cung tròn.
 * @returns {string}
 */
function describeArc(x, y, radius, startAngle, endAngle) {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

/**
 * [CẢI TIẾN] TẠO BIỂU ĐỒ ĐỒNG HỒ (GAUGE)
 * Thiết kế mới tinh tế hơn, kim chỉ mượt mà và có hiệu ứng.
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {number} value - Giá trị hiện tại.
 * @param {object} config - Cấu hình chi tiết cho biểu đồ.
 */
function createGauge(container, value, config) {
    if (!container) return;

    // --- CẤU HÌNH GAUGE ---
    const { min = 0, max = 100, segments } = config;
    const GAUGE_START_ANGLE = -120; // Bắt đầu từ -120 độ (phía dưới bên trái)
    const GAUGE_END_ANGLE = 120;   // Kết thúc ở 120 độ (phía dưới bên phải)
    const ANGLE_SPAN = GAUGE_END_ANGLE - GAUGE_START_ANGLE; // Tổng số độ của vòng cung (240)

    // --- TÍNH TOÁN ---
    const clampedValue = Math.max(min, Math.min(max, value));
    const percentage = (clampedValue - min) / (max - min);
    const valueAngle = GAUGE_START_ANGLE + (percentage * ANGLE_SPAN); // Góc của kim chỉ báo

    const currentSegment = segments.find(s => clampedValue <= s.limit) || segments[segments.length - 1];
    const valueColor = currentSegment.color;
    const classification = currentSegment.label || '';

    // --- VẼ CÁC ĐOẠN MÀU ---
    let segmentPaths = '';
    let lastPercentage = 0;

    segments.forEach(segment => {
        const segmentEndPercentage = (segment.limit - min) / (max - min);
        // [SỬA LỖI CỐT LÕI] Tính toán góc bắt đầu và kết thúc cho mỗi đoạn
        // dựa trên tỷ lệ của nó trong toàn bộ vòng cung 240 độ.
        const start = GAUGE_START_ANGLE + (lastPercentage * ANGLE_SPAN);
        const end = GAUGE_START_ANGLE + (segmentEndPercentage * ANGLE_SPAN);

        segmentPaths += `<path d="${describeArc(100, 100, 85, start, end)}"
                             fill="none" stroke="${segment.color}" stroke-width="22" />`;
        lastPercentage = segmentEndPercentage;
    });

    const svg = `
        <svg viewBox="0 0 200 165" style="width: 100%; height: auto; overflow: visible;">
            <path d="${describeArc(100, 100, 85, GAUGE_START_ANGLE, GAUGE_END_ANGLE)}"
                  fill="none" stroke="var(--bg-primary)" stroke-width="22" stroke-linecap="round"/>

            <g>${segmentPaths}</g>

            <g transform="rotate(${valueAngle} 100 100)" class="gauge-needle">
                <path d="M 100 20 L 97 100 L 103 100 Z" fill="var(--text-primary)"/>
                <circle cx="100" cy="100" r="6" fill="var(--text-primary)"/>
            </g>

            <text x="100" y="105" text-anchor="middle" font-size="32px" font-weight="800"
                  fill="var(--text-primary)">
                ${value.toFixed(1)}
            </text>
            <text x="100" y="130" text-anchor="middle" font-size="16px" font-weight="600"
                  fill="${valueColor}">
                ${classification}
            </text>
        </svg>
        <style>
            .gauge-needle {
                /* Hiệu ứng xoay mượt mà cho kim */
                transition: transform 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
        </style>
    `;
    container.innerHTML = svg;
}

/**
 * [CẢI TIẾN] TẠO BIỂU ĐỒ ĐƯỜNG (LINE CHART)
 * Phiên bản mới này sẽ hiển thị giá trị tại mỗi điểm dữ liệu trên biểu đồ.
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<number>} data - Mảng dữ liệu.
 * @param {object} options - Các tùy chọn bổ sung.
 * @param {string} [options.color='var(--accent-color)'] - Màu chính của biểu đồ.
 * @param {string} [options.valuePrefix=''] - Tiền tố cho giá trị (vd: '$').
 * @param {string} [options.valueSuffix=''] - Hậu tố cho giá trị (vd: '%').
 */
function createLineChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) return;

    // --- Cấu hình và Tùy chọn ---
    const {
        color = 'var(--accent-color)',
        valuePrefix = '',
        valueSuffix = ''
    } = options;
    const width = 320, height = 160, p = 35; // Tăng padding để có không gian cho nhãn

    // --- Tính toán Tọa độ ---
    const maxValue = Math.max(...data);
    const minValue = Math.min(...data);
    // Thêm một khoảng đệm nhỏ vào dải giá trị để nhãn không bị cắt ở đỉnh và đáy
    const valueRange = (maxValue - minValue) * 1.2 || 1;
    const rangeMin = minValue - (maxValue - minValue) * 0.1;

    const toX = i => (i / (data.length - 1)) * (width - 2 * p) + p;
    const toY = val => height - p - ((val - rangeMin) / valueRange) * (height - 2 * p);

    // --- Tạo các thành phần SVG ---
    const points = data.map((d, i) => `${toX(i)},${toY(d)}`).join(' ');
    const areaPoints = `${p},${height - p} ${points} ${width - p},${height - p}`;

    let valueLabels = '';
    data.forEach((d, i) => {
        const x = toX(i);
        const y = toY(d);
        valueLabels += `
            <text x="${x}" y="${y - 10}" text-anchor="middle" font-size="11px"
                  fill="var(--text-primary)" font-weight="600" class="value-label">
                ${valuePrefix}${d.toFixed(1)}${valueSuffix}
            </text>
        `;
    });

    const svg = `
        <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; overflow: visible;">
            <defs>
                <linearGradient id="areaGradient-${container.id}" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stop-color="${color}" stop-opacity="0.25" />
                    <stop offset="100%" stop-color="${color}" stop-opacity="0" />
                </linearGradient>
            </defs>

            <polygon fill="url(#areaGradient-${container.id})" points="${areaPoints}" class="line-area" />

            <polyline fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round"
                      stroke-linejoin="round" points="${points}" class="line-path" />

            ${data.map((d, i) => `
                <circle cx="${toX(i)}" cy="${toY(d)}" r="4" fill="${color}"
                        stroke="var(--bg-secondary)" stroke-width="2" class="line-dot"
                        style="animation-delay: ${i * 80}ms"/>
            `).join('')}

            <g class="value-labels-group">${valueLabels}</g>
        </svg>

        <style>
            .line-path {
                stroke-dasharray: 1000;
                stroke-dashoffset: 1000;
                animation: draw-path 1.2s 0.2s forwards cubic-bezier(0.45, 0.05, 0.55, 0.95);
            }
            @keyframes draw-path { to { stroke-dashoffset: 0; } }

            .line-dot, .value-label {
                opacity: 0;
                transform: translateY(10px);
                animation: fade-in-up 0.5s forwards cubic-bezier(0.34, 1.56, 0.64, 1);
            }
             .value-label { animation-delay: 0.8s; }
            @keyframes fade-in-up {
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        </style>
    `;
    container.innerHTML = svg;
}

/**
 * [CẢI TIẾN] TẠO BIỂU ĐỒ CỘT (BAR CHART)
 * Thêm hiệu ứng và nhãn cho các cột.
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<object>} data - Dữ liệu, vd: [{value: 10, label: 'A', color: 'red'}]
 */
function createBarChart(container, data) {
    if (!container) return;
    const width = 300, height = 150, p = 20;
    const maxValue = Math.max(...data.map(d => d.value));
    const barWidth = (width - 2 * p) / data.length * 0.7;
    const gap = (width - 2 * p) / data.length * 0.3;

    let bars = '';
    data.forEach((d, i) => {
        const barHeight = (d.value / maxValue) * (height - 2 * p);
        const x = p + i * (barWidth + gap) + gap/2;
        const y = height - p - barHeight;
        bars += `
            <g transform="translate(${x}, ${y})">
                <rect width="${barWidth}" height="${barHeight}"
                      fill="${d.color || 'var(--accent-color)'}" rx="2" class="bar-rect"
                      style="animation-delay: ${i * 100}ms;" />
                <text x="${barWidth/2}" y="-5" text-anchor="middle" font-size="10"
                      fill="var(--text-primary)">${d.value}</text>
            </g>
        `;
    });

    container.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto;">
            <line x1="${p}" y1="${height-p}" x2="${width-p}" y2="${height-p}" stroke="var(--border-color)" />
            ${bars}
        </svg>
        <style>
            .bar-rect {
                transform: scaleY(0);
                transform-origin: bottom;
                animation: grow-bar 0.7s forwards cubic-bezier(0.34, 1.56, 0.64, 1);
            }
            @keyframes grow-bar { to { transform: scaleY(1); } }
        </style>
    `;
}

/**
 * [ĐÃ SỬA] TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART)
 * Hiển thị tiêu đề ở giữa, chú giải động và bỏ giá trị trên các phần.
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {Array<object>} data - Dữ liệu, vd: [{value: 10, color: 'blue', label: 'Mục A'}]
 * @param {string} [title=''] - Tiêu đề hiển thị ở giữa biểu đồ.
 */
function createDoughnutChart(container, data, title = '') {
    if (!container || !data || data.length === 0) return;

    const width = 180, height = 180, hole = 55;
    const radius = Math.min(width, height) / 2 - 5;
    const strokeWidth = radius - hole;
    const cx = width / 2;
    const cy = height / 2;

    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) return;

    const circumference = 2 * Math.PI * radius;
    let startAngle = 0;
    let segments = '';
    let legendItems = '';

    data.forEach((d, i) => {
        const percentage = d.value / total;
        if (percentage === 0) return;

        const finalDashoffset = circumference * (1 - percentage);
        const rotation = startAngle;
        const endAngle = startAngle + percentage * 360;

        segments += `
            <circle r="${radius}" cx="${cx}" cy="${cy}"
                    fill="transparent" stroke="${d.color}" stroke-width="${strokeWidth}"
                    stroke-dasharray="${circumference}"
                    stroke-dashoffset="${circumference}"
                    transform="rotate(${rotation - 90} ${cx} ${cy})"
                    class="doughnut-segment"
                    style="--final-offset: ${finalDashoffset}; animation-delay: ${i * 150}ms;" />`;

        const displayValue = (percentage * 100).toFixed(1) + '%';

        legendItems += `
            <span class="legend-item">
                <span class="legend-color-box" style="background-color: ${d.color};"></span>
                <span>${d.label}: <strong>${displayValue}</strong></span>
            </span>`;
        
        startAngle = endAngle;
    });

    container.innerHTML = `
        <div style="position: relative; width: ${width}px; height: ${height}px; margin: auto;">
            <svg viewBox="0 0 ${width} ${height}" style="position: absolute; top: 0; left: 0; overflow: visible;">
                ${segments}
            </svg>
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; width: ${hole * 2 * 0.85}px; pointer-events: none;">
                <span style="font-size: 1rem; font-weight: 600; color: var(--text-primary); line-height: 1.25;">
                    ${title}
                </span>
            </div>
        </div>
        <div class="doughnut-legend">
            ${legendItems}
        </div>
        <style>
            .doughnut-segment {
                animation: fill-doughnut 1s forwards cubic-bezier(0.4, 0, 0.2, 1);
            }
            @keyframes fill-doughnut {
                to { stroke-dashoffset: var(--final-offset); }
            }
            .doughnut-legend {
                display: flex;
                flex-direction: column;
                justify-content: center;
                gap: 0.6rem;
                margin-top: 1.25rem;
                font-size: 0.85rem;
                color: var(--text-secondary);
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .legend-color-box {
                width: 12px;
                height: 12px;
                border-radius: 3px;
                flex-shrink: 0;
            }
        </style>
    `;
}