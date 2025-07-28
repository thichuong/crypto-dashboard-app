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
 * - Thêm hiệu ứng chuyển động khi vẽ và hiệu ứng tương tác khi di chuột.
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
    // Gán một class riêng để CSS có thể nhắm mục tiêu chính xác
    container.classList.add('gauge-container');
}


/**
 * [CẢI TIẾN] TẠO BIỂU ĐỒ CỘT (BAR CHART)
 * Thêm hiệu ứng, nhãn giá trị cho các cột và tương tác khi di chuột.
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<object>} data - Dữ liệu, vd: [{value: 10, label: 'A', color: 'red'}].
 * @param {object} [options] - Các tùy chọn, vd: { valuePrefix: '$', valueSuffix: 'M', yAxisLabel: 'Triệu USD' }.
 */
function createBarChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) return;

    const { valuePrefix = '', valueSuffix = '', yAxisLabel = '' } = options;

    const width = 300, height = 180, pTop = 25, pBottom = 10; // Giảm padding dưới vì không còn nhãn trục X
    const pLeft = yAxisLabel ? 45 : 20;
    const pRight = 20;

    const chartWidth = width - pLeft - pRight;
    const maxValue = Math.max(...data.map(d => d.value));
    const barWidth = chartWidth / data.length * 0.65;
    const gap = chartWidth / data.length * 0.35;

    let bars = '';
    let legendItems = '';
    let yAxisUnit = '';

    if (yAxisLabel) {
        yAxisUnit = `
            <text x="${-(pTop + (height - pTop - pBottom) / 2)}" y="15"
                  transform="rotate(-90)" text-anchor="middle" font-size="12px"
                  font-weight="500" fill="var(--text-secondary)">
                ${yAxisLabel}
            </text>
        `;
    }

    data.forEach((d, i) => {
        const barHeight = (d.value / maxValue) * (height - pTop - pBottom);
        const x = pLeft + i * (barWidth + gap) + gap / 2;
        const y = height - pBottom - barHeight;
        bars += `
            <g transform="translate(${x}, ${y})" class="bar-group">
                <rect width="${barWidth}" height="${barHeight}"
                      fill="${d.color || 'var(--accent-color)'}" rx="3" class="bar-rect"
                      style="animation-delay: ${i * 100}ms;" />
                <text x="${barWidth / 2}" y="-8" text-anchor="middle" font-size="12px" font-weight="600"
                      fill="var(--text-primary)" class="bar-value-label">${valuePrefix}${d.value}${valueSuffix}</text>
            </g>
        `;

        legendItems += `
            <span class="legend-item">
                <span class="legend-color-box" style="background-color: ${d.color || 'var(--accent-color)'};"></span>
                <span>${d.label}</span>
            </span>
        `;
    });

    container.innerHTML = `
        <div class="bar-chart-layout">
            <div class="bar-chart-svg-wrapper">
                <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:auto; overflow: visible;">
                    ${yAxisUnit}
                    <line x1="${pLeft}" y1="${height - pBottom}" x2="${width - pRight}" y2="${height - pBottom}" stroke="var(--border-color)" />
                    ${bars}
                </svg>
            </div>
            <div class="bar-chart-legend doughnut-legend">
                ${legendItems}
            </div>
        </div>
    `;
    container.classList.add('bar-chart-container');
}


/**
 * [CẢI TIẾN] TẠO BIỂU ĐỒ ĐƯỜNG (LINE CHART)
 * Phiên bản mới này sẽ hiển thị giá trị tại mỗi điểm dữ liệu và có hiệu ứng hover.
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<number>} data - Mảng dữ liệu.
 * @param {object} options - Các tùy chọn bổ sung.
 */
function createLineChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) return;

    const { color = 'var(--accent-color)', valuePrefix = '', valueSuffix = '' } = options;
    const width = 320, height = 160, p = 35;

    const maxValue = Math.max(...data);
    const minValue = Math.min(...data);
    const valueRange = (maxValue - minValue) * 1.2 || 1;
    const rangeMin = minValue - (maxValue - minValue) * 0.1;

    const toX = i => (i / (data.length - 1)) * (width - 2 * p) + p;
    const toY = val => height - p - ((val - rangeMin) / valueRange) * (height - 2 * p);

    const points = data.map((d, i) => `${toX(i)},${toY(d)}`).join(' ');
    const areaPoints = `${p},${height - p} ${points} ${width - p},${height - p}`;

    const svg = `
        <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; overflow: visible;" class="line-chart-interactive">
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
                <g class="line-point-group">
                    <circle cx="${toX(i)}" cy="${toY(d)}" r="9" fill="transparent" />
                     <circle cx="${toX(i)}" cy="${toY(d)}" r="4" fill="${color}"
                            stroke="var(--bg-secondary)" stroke-width="2" class="line-dot"
                            style="animation-delay: ${i * 80}ms"/>
                    <text x="${toX(i)}" y="${toY(d) - 15}" text-anchor="middle" font-size="12px"
                          fill="var(--text-primary)" font-weight="600" class="value-label">
                        ${valuePrefix}${d.toFixed(1)}${valueSuffix}
                    </text>
                </g>
            `).join('')}
        </svg>
    `;
    container.innerHTML = svg;
    // Gán một class riêng để CSS có thể nhắm mục tiêu chính xác
    container.classList.add('line-chart-container');
}


/**
 * [ĐÃ SỬA & CẢI TIẾN] TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART)
 * Hiển thị tiêu đề ở giữa, chú giải động và hiệu ứng hover tương tác hai chiều.
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {Array<object>} data - Dữ liệu.
 * @param {string} [title=''] - Tiêu đề hiển thị ở giữa.
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
        const segmentId = `segment-${container.id}-${i}`;
        const legendId = `legend-${container.id}-${i}`;

        segments += `
            <circle id="${segmentId}" r="${radius}" cx="${cx}" cy="${cy}"
                    fill="transparent" stroke="${d.color}" stroke-width="${strokeWidth}"
                    stroke-dasharray="${circumference}"
                    stroke-dashoffset="${circumference}"
                    transform="rotate(${rotation - 90} ${cx} ${cy})"
                    class="doughnut-segment"
                    data-legend-id="${legendId}"
                    style="--final-offset: ${finalDashoffset}; animation-delay: ${i * 150}ms;" />`;

        const displayValue = (percentage * 100).toFixed(1) + '%';

        legendItems += `
            <span id="${legendId}" class="legend-item" data-segment-id="${segmentId}">
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
    `;

    // --- [THÊM MỚI] LOGIC TƯƠNG TÁC HAI CHIỀU KHI HOVER ---
    // Lấy tất cả các segment của biểu đồ và các mục chú giải
    const allSegments = container.querySelectorAll('.doughnut-segment');
    const allLegends = container.querySelectorAll('.legend-item');

    // Hàm để highlight cặp segment-legend tương ứng
    const highlightPair = (element) => {
        // Dựa vào data-attributes để tìm ID của các thành phần liên quan
        const segmentId = element.dataset.segmentId || element.id;
        const legendId = element.dataset.legendId || element.id;

        const segment = container.querySelector(`#${segmentId}`);
        const legend = container.querySelector(`#${legendId}`);

        // Thêm class 'highlight' để CSS có thể áp dụng hiệu ứng
        if (segment) segment.classList.add('highlight');
        if (legend) legend.classList.add('highlight');
    };

    // Hàm để xóa tất cả các highlight
    const clearHighlights = () => {
        allSegments.forEach(s => s.classList.remove('highlight'));
        allLegends.forEach(l => l.classList.remove('highlight'));
    };

    // Gán sự kiện 'mouseenter' và 'mouseleave' cho cả segment và legend
    [...allSegments, ...allLegends].forEach(el => {
        el.addEventListener('mouseenter', () => highlightPair(el));
        el.addEventListener('mouseleave', clearHighlights);
    });
}