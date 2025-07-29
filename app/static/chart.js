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
 * [CẢI TIẾN & NÂNG CẤP] TẠO BIỂU ĐỒ CỘT (BAR CHART) HỖ TRỢ GIÁ TRỊ ÂM
 * Cho phép vẽ biểu đồ với các giá trị âm. Cột âm sẽ được dựng theo hướng ngược lại với cột dương.
 * Thêm hiệu ứng, nhãn giá trị cho các cột và tương tác khi di chuột.
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<object>} data - Dữ liệu, vd: [{value: 10, label: 'A', color: 'red'}].
 * @param {object} [options] - Các tùy chọn, vd: { valuePrefix: '$', valueSuffix: 'M', yAxisLabel: 'Triệu USD' }.
 */
function createBarChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) return;

    const { valuePrefix = '', valueSuffix = '', yAxisLabel = '' } = options;

    const width = 300, height = 180, pTop = 25, pBottom = 20;
    const pLeft = yAxisLabel ? 45 : 20;
    const pRight = 20;

    // --- [THAY ĐỔI] TÍNH TOÁN DẢI GIÁ TRỊ ĐỂ HỖ TRỢ SỐ ÂM ---
    const allValues = data.map(d => d.value);
    const minValue = Math.min(0, ...allValues); // Luôn bao gồm 0
    const maxValue = Math.max(0, ...allValues); // Luôn bao gồm 0
    const totalRange = maxValue - minValue;
    
    // Nếu không có sự thay đổi (tất cả giá trị là 0), không cần vẽ
    if (totalRange === 0) return;

    const chartAreaHeight = height - pTop - pBottom;
    const chartWidth = width - pLeft - pRight;

    // --- [THAY ĐỔI] TÍNH TOÁN VỊ TRÍ TRỤC ZERO ---
    const zeroY = pTop + (maxValue / totalRange) * chartAreaHeight;

    const barWidth = chartWidth / data.length * 0.65;
    const gap = chartWidth / data.length * 0.35;
    const scale = chartAreaHeight / totalRange;

    let bars = '';
    let legendItems = '';
    let yAxisUnit = '';

    if (yAxisLabel) {
        yAxisUnit = `
            <text x="${-(pTop + chartAreaHeight / 2)}" y="15"
                  transform="rotate(-90)" text-anchor="middle" font-size="12px"
                  font-weight="500" fill="var(--text-secondary)">
                ${yAxisLabel}
            </text>
        `;
    }

    data.forEach((d, i) => {
        const barHeight = Math.abs(d.value) * scale;
        const x = pLeft + i * (barWidth + gap) + gap / 2;
        
        // --- [THAY ĐỔI] XÁC ĐỊNH VỊ TRÍ Y VÀ NHÃN DỰA TRÊN GIÁ TRỊ ÂM/DƯƠNG ---
        let y, labelY, labelAnchor;

        if (d.value >= 0) {
            y = zeroY - barHeight;
            labelY = -8; // Phía trên cột
        } else {
            y = zeroY;
            labelY = barHeight + 15; // Phía dưới cột
        }

        bars += `
            <g transform="translate(${x}, ${y})" class="bar-group">
                <rect width="${barWidth}" height="${barHeight}"
                      fill="${d.color || 'var(--accent-color)'}" rx="3" class="bar-rect"
                      style="animation-delay: ${i * 100}ms;" />
                <text x="${barWidth / 2}" y="${labelY}" text-anchor="middle" font-size="12px" font-weight="600"
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
                    <line x1="${pLeft}" y1="${zeroY}" x2="${width - pRight}" y2="${zeroY}" stroke="var(--border-color)" />
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
 * @param {Array<object>} data - Dữ liệu  `value`, `label`, and `color`.
 * @param {string} [title=''] - Tiêu đề hiển thị ở giữa.
 */
/**
 * [REWRITTEN] TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART)
 * Tạo biểu đồ tròn với tiêu đề ở giữa, chú giải động và hiệu ứng tương tác hai chiều khi di chuột.
 *
 * @param {HTMLElement} container - The DOM element to render the chart into.
 * @param {Array<object>} data - The dataset. Example: [{ value: 30, label: 'A', color: '#FF6384' }]
 * @param {string} [title=''] - The title to display in the center of the chart.
 */
/**
 * HÀM TRỢ GIÚP
 * Chuyển đổi tọa độ cực sang Descartes.
 */
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
        x: centerX + radius * Math.cos(angleInRadians),
        y: centerY + radius * Math.sin(angleInRadians),
    };
}

/**
 * HÀM TRỢ GIÚP [MỚI]
 * Tạo chuỗi path data 'd' cho một cung tròn của biểu đồ Doughnut.
 * @returns {string} - Chuỗi 'd' để dùng trong thuộc tính path của SVG.
 */
function describeDoughnutArc(x, y, outerRadius, innerRadius, startAngle, endAngle) {
    const startOuter = polarToCartesian(x, y, outerRadius, endAngle);
    const endOuter = polarToCartesian(x, y, outerRadius, startAngle);
    const startInner = polarToCartesian(x, y, innerRadius, endAngle);
    const endInner = polarToCartesian(x, y, innerRadius, startAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

    // Path: Di chuyển đến điểm bắt đầu bên ngoài -> Vẽ cung bên ngoài ->
    // Đi thẳng vào cung bên trong -> Vẽ cung bên trong ngược lại -> Đóng path.
    const d = [
        'M', startOuter.x, startOuter.y,
        'A', outerRadius, outerRadius, 0, largeArcFlag, 0, endOuter.x, endOuter.y,
        'L', endInner.x, endInner.y,
        'A', innerRadius, innerRadius, 0, largeArcFlag, 1, startInner.x, startInner.y,
        'Z'
    ].join(' ');

    return d;
}


/**
 * [VIẾT LẠI] TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART)
 * Phiên bản cải tiến sử dụng <path> để vẽ các cung tròn, giúp mã nguồn rõ ràng hơn.
 * Giữ nguyên hiệu ứng tương tác hai chiều và chú giải động.
 *
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {Array<object>} data - Dữ liệu. Vd: [{ value: 30, label: 'A', color: '#FF6384' }]
 * @param {string} [title=''] - Tiêu đề hiển thị ở giữa biểu đồ.
 */
function createDoughnutChart(container, data, title = '') {
    // --- 1. KIỂM TRA ĐẦU VÀO ---
    if (!container || !data || data.length === 0) {
        if (container) container.innerHTML = 'Không có dữ liệu để hiển thị.';
        return;
    }

    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) {
        if (container) container.innerHTML = 'Tổng giá trị bằng 0, không thể vẽ biểu đồ.';
        return;
    }

    // --- 2. CẤU HÌNH BIỂU ĐỒ ---
    const width = 180, height = 180;
    const cx = width / 2;
    const cy = height / 2;
    const outerRadius = 80;
    const innerRadius = 50;
    // ID duy nhất cho biểu đồ để tránh xung đột khi có nhiều biểu đồ trên trang
    const chartId = `doughnut-${Math.random().toString(36).substring(2, 9)}`;

    // --- 3. TẠO CÁC SEGMENT SVG VÀ CHÚ GIẢI HTML ---
    let startAngle = 0;
    let segmentsHTML = '';
    let legendHTML = '';

    data.forEach((d, i) => {
        if (d.value <= 0) return; // Bỏ qua các segment có giá trị bằng 0 hoặc âm

        const percentage = d.value / total;
        const angleSpan = percentage * 360;
        const endAngle = startAngle + angleSpan;
        
        // ID để liên kết segment và chú giải
        const segmentId = `${chartId}-segment-${i}`;
        const legendId = `${chartId}-legend-${i}`;

        // Tạo path cho segment
        const pathData = describeDoughnutArc(cx, cy, outerRadius, innerRadius, startAngle, endAngle);
        segmentsHTML += `
            <path
                id="${segmentId}"
                class="doughnut-segment"
                d="${pathData}"
                fill="${d.color}"
                data-legend-id="${legendId}"
                style="--animation-delay: ${i * 100}ms;"
            />`;

        // Tạo chú giải tương ứng
        const percentageDisplay = (percentage * 100).toFixed(1);
        legendHTML += `
            <div id="${legendId}" class="legend-item" data-segment-id="${segmentId}">
                <span class="legend-color-box" style="background-color: ${d.color};"></span>
                <span>${d.label}: <strong>${percentageDisplay}%</strong></span>
            </div>`;
        
        startAngle = endAngle;
    });

    // --- 4. GHÉP VÀ HIỂN THỊ HTML ---
    container.innerHTML = `
        <div class="doughnut-chart-container">
            <div class="doughnut-svg-wrapper">
                <svg viewBox="0 0 ${width} ${height}" class="doughnut-svg">
                    <g class="doughnut-segments-group">
                        ${segmentsHTML}
                    </g>
                </svg>
                <div class="doughnut-title">
                    ${title}
                </div>
            </div>
            <div class="doughnut-legend">
                ${legendHTML}
            </div>
        </div>`;
    
    // --- 5. THIẾT LẬP SỰ KIỆN TƯƠNG TÁC (HOVER) ---
    const chartContainer = container.querySelector('.doughnut-chart-container');
    const interactiveElements = container.querySelectorAll('.doughnut-segment, .legend-item');

    const handleMouseEnter = (event) => {
        // Thêm class để kích hoạt trạng thái "đang tương tác"
        if (chartContainer) chartContainer.classList.add('is-highlighted');

        const target = event.currentTarget;
        const segmentId = target.dataset.segmentId || target.id;
        const legendId = target.dataset.legendId || target.id;

        const segment = container.querySelector('#' + segmentId);
        const legend = container.querySelector('#' + legendId);

        if (segment) segment.classList.add('highlight');
        if (legend) legend.classList.add('highlight');
    };

    const handleMouseLeave = () => {
        // Xóa tất cả các class highlight và trạng thái "đang tương tác"
        if (chartContainer) chartContainer.classList.remove('is-highlighted');
        container.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));
    };

    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', handleMouseEnter);
        el.addEventListener('mouseleave', handleMouseLeave);
    });
}