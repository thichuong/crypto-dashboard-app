// static/chart_modules/utils.js

/**
 * -----------------------------------------------------------------------------
 * TIỆN ÍCH CHUNG CHO BIỂU ĐỒ
 * -----------------------------------------------------------------------------
 * Chứa các hàm tính toán dùng chung cho việc vẽ các biểu đồ SVG.
 */

/**
 * Chuyển đổi tọa độ cực sang Descartes.
 * Dùng cho việc tính toán vị trí trên một đường tròn hoặc cung tròn.
 * @param {number} centerX - Tọa độ X của tâm.
 * @param {number} centerY - Tọa độ Y của tâm.
 * @param {number} radius - Bán kính.
 * @param {number} angleInDegrees - Góc (tính bằng độ).
 * @returns {{x: number, y: number}} Tọa độ Descartes.
 */
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
        x: centerX + radius * Math.cos(angleInRadians),
        y: centerY + radius * Math.sin(angleInRadians),
    };
}

/**
 * Tạo chuỗi path data 'd' cho một cung tròn SVG.
 * Hàm này đã được tối ưu để dễ đọc và sử dụng đúng cờ SVG.
 * @param {number} x - Tọa độ X của tâm.
 * @param {number} y - Tọa độ Y của tâm.
 * @param {number} radius - Bán kính của cung tròn.
 * @param {number} startAngle - Góc bắt đầu (độ).
 * @param {number} endAngle - Góc kết thúc (độ).
 * @returns {string} Chuỗi data cho thuộc tính 'd' của thẻ <path>.
 */
function describeArc(x, y, radius, startAngle, endAngle) {
    const startPoint = polarToCartesian(x, y, radius, startAngle);
    const endPoint = polarToCartesian(x, y, radius, endAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    const sweepFlag = '1'; // Vẽ cung theo chiều dương (cùng chiều kim đồng hồ)

    const d = [
        'M', startPoint.x, startPoint.y,
        'A', radius, radius, 0, largeArcFlag, sweepFlag, endPoint.x, endPoint.y
    ].join(' ');

    return d;
}

/**
 * Tạo chuỗi path data 'd' cho một cung của biểu đồ Doughnut.
 * @returns {string}
 */
function describeDoughnutArc(x, y, outerRadius, innerRadius, startAngle, endAngle) {
    const startOuter = polarToCartesian(x, y, outerRadius, endAngle);
    const endOuter = polarToCartesian(x, y, outerRadius, startAngle);
    const startInner = polarToCartesian(x, y, innerRadius, endAngle);
    const endInner = polarToCartesian(x, y, innerRadius, startAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

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
 * =============================================================================
 * TẠO BIỂU ĐỒ ĐỒNG HỒ (GAUGE) ĐƯỢC CẢI TIẾN
 * =============================================================================
 * Phụ thuộc vào các hàm trong 'utils.js'.
 * Kiểu dáng được điều khiển bởi 'gauge-chart.css'.
 *
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {number} value - Giá trị hiện tại để hiển thị trên biểu đồ.
 * @param {object} config - Đối tượng cấu hình cho biểu đồ.
 * @param {number} [config.min=0] - Giá trị tối thiểu của gauge.
 * @param {number} [config.max=100] - Giá trị tối đa của gauge.
 * @param {Array<object>} [config.segments=[]] - Mảng các đoạn màu.
 */
function createGauge(container, value, config) {
    // --- 1. KIỂM TRA ĐẦU VÀO ---
    if (!container) {
        console.error("Lỗi: Container element không được cung cấp cho createGauge.");
        return;
    }

    // --- 2. CẤU HÌNH & HẰNG SỐ ---
    const cfg = {
        min: 0,
        max: 100,
        segments: [],
        ...config,
    };
    const GAUGE_START_ANGLE = -120;
    const GAUGE_END_ANGLE = 120;
    const ANGLE_SPAN = GAUGE_END_ANGLE - GAUGE_START_ANGLE;
    const SVG_NS = "http://www.w3.org/2000/svg"; // Namespace cho SVG

    // --- 3. TÍNH TOÁN LOGIC ---
    const clampedValue = Math.max(cfg.min, Math.min(cfg.max, value));
    const percentage = (clampedValue - cfg.min) / (cfg.max - cfg.min);
    const valueAngle = GAUGE_START_ANGLE + (percentage * ANGLE_SPAN);

    const currentSegment = cfg.segments.find(s => clampedValue <= s.limit) ||
                           cfg.segments[cfg.segments.length - 1] ||
                           { color: '#ccc', label: '' };
    const valueColor = currentSegment.color;
    const classification = currentSegment.label || '';

    // --- 4. TẠO CÁC THÀNH PHẦN SVG ---

    // Hàm trợ giúp để tạo phần tử SVG và đặt thuộc tính
    function createSvgElement(tag, attributes) {
        const element = document.createElementNS(SVG_NS, tag);
        for (const key in attributes) {
            element.setAttribute(key, attributes[key]);
        }
        return element;
    }

    // Xóa nội dung cũ và thêm class vào container
    container.innerHTML = '';
    container.classList.add('gauge-container');

    // Tạo SVG element chính
    const svg = createSvgElement('svg', {
        viewBox: "0 0 200 165",
        class: 'gauge-svg'
    });

    // a. Tạo đường track nền
    const trackPath = createSvgElement('path', {
        d: describeArc(100, 100, 85, GAUGE_START_ANGLE, GAUGE_END_ANGLE),
        class: 'gauge-track'
    });
    svg.appendChild(trackPath);

    // b. Tạo các đoạn màu
    const segmentsGroup = createSvgElement('g', { class: 'gauge-segments-group' });
    let lastPercentage = 0;
    cfg.segments.forEach(segment => {
        const segmentEndPercentage = (segment.limit - cfg.min) / (cfg.max - cfg.min);
        const start = GAUGE_START_ANGLE + (lastPercentage * ANGLE_SPAN);
        const end = GAUGE_START_ANGLE + (Math.min(segmentEndPercentage, 1) * ANGLE_SPAN);
        
        const segmentPath = createSvgElement('path', {
            d: describeArc(100, 100, 85, start, end),
            stroke: segment.color, // Color được đặt trực tiếp vì nó là dữ liệu động
            class: 'gauge-segment'
        });
        segmentsGroup.appendChild(segmentPath);
        lastPercentage = segmentEndPercentage;
    });
    svg.appendChild(segmentsGroup);

    // c. Tạo kim chỉ
    const needleGroup = createSvgElement('g', {
        class: 'gauge-needle-group',
        transform: `rotate(${valueAngle} 100 100)`
    });
    const needlePointer = createSvgElement('path', {
        d: 'M 100 20 L 97 100 L 103 100 Z',
        class: 'gauge-needle-pointer'
    });
    const needlePivot = createSvgElement('circle', {
        cx: 100,
        cy: 100,
        r: 6,
        class: 'gauge-needle-pivot'
    });
    needleGroup.append(needlePointer, needlePivot);
    svg.appendChild(needleGroup);

    // d. Tạo các nhãn văn bản
    const valueText = createSvgElement('text', {
        x: 100,
        y: 105,
        class: 'gauge-text gauge-value-text'
    });
    valueText.textContent = value.toFixed(1);

    const labelText = createSvgElement('text', {
        x: 100,
        y: 130,
        fill: valueColor, // Color được đặt trực tiếp vì nó là dữ liệu động
        class: 'gauge-text gauge-label-text'
    });
    labelText.textContent = classification;

    svg.append(valueText, labelText);

    // --- 5. RENDER BIỂU ĐỒ ---
    container.appendChild(svg);
}

// static/chart_modules/bar.js

/**
 * TẠO BIỂU ĐỒ CỘT (BAR CHART) HỖ TRỢ GIÁ TRỊ ÂM
 * @param {HTMLElement} container - Element DOM.
 * @param {Array<object>} data - Dữ liệu, vd: [{value: 10, label: 'A', color: 'red'}].
 * @param {object} [options] - Các tùy chọn, vd: { valuePrefix: '$', valueSuffix: 'M', yAxisLabel: 'Triệu USD' }.
 */
function createBarChart(container, data, options = {}) {
    if (!container || !data || data.length === 0) return;

    const { valuePrefix = '', valueSuffix = '', yAxisLabel = '' } = options;

    // Lấy kích thước động từ container để biểu đồ co giãn theo card
    const availableWidth = container.clientWidth || 450; // Lấy chiều rộng thực tế, có fallback
    const width = availableWidth;
    const height = availableWidth * 0.5; // Giữ tỷ lệ khung hình ~2:1, có thể điều chỉnh

    const pTop = 25, pBottom = 20;
    const pLeft = yAxisLabel ? 45 : 20;
    const pRight = 20;

    const allValues = data.map(d => d.value);
    const minValue = Math.min(0, ...allValues);
    const maxValue = Math.max(0, ...allValues);
    const totalRange = maxValue - minValue;

    if (totalRange === 0) return;

    const chartAreaHeight = height - pTop - pBottom;
    const chartWidth = width - pLeft - pRight;
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
        let y, labelY;

        if (d.value >= 0) {
            y = zeroY - barHeight;
            labelY = -8;
        } else {
            y = zeroY;
            labelY = barHeight + 15;
        }

        bars += `
            <g transform="translate(${x}, ${y})" class="bar-group" data-index="${i}">
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
                    <!-- Custom Tooltip -->
                    <g class="bar-chart-tooltip" style="visibility: hidden;">
                        <rect class="tooltip-bg" rx="4" ry="4" height="28" />
                        <text class="tooltip-text" x="10" y="18"></text>
                    </g>
                </svg>
            </div>
            <div class="bar-chart-legend doughnut-legend">
                ${legendItems}
            </div>
        </div>
    `;
    container.classList.add('bar-chart-container');

    // --- THÊM TƯƠNG TÁC CHO TOOLTIP ---
    const svg = container.querySelector('svg');
    const tooltip = svg.querySelector('.bar-chart-tooltip');
    const tooltipBg = tooltip.querySelector('.tooltip-bg');
    const tooltipText = tooltip.querySelector('.tooltip-text');
    const barGroups = svg.querySelectorAll('.bar-group');
    const svgPoint = svg.createSVGPoint();

    function getMousePosition(event) {
        svgPoint.x = event.clientX;
        svgPoint.y = event.clientY;
        // Chuyển đổi tọa độ chuột sang hệ tọa độ của SVG
        return svgPoint.matrixTransform(svg.getScreenCTM().inverse());
    }

    barGroups.forEach(bar => {
        bar.addEventListener('mouseover', (e) => {
            const index = parseInt(bar.dataset.index);
            const d = data[index];
            const content = `${d.label}: ${valuePrefix}${d.value}${valueSuffix}`;
            
            tooltipText.textContent = content;
            tooltip.style.visibility = 'visible';

            // Tự động điều chỉnh chiều rộng tooltip
            const textBBox = tooltipText.getBBox();
            tooltipBg.setAttribute('width', textBBox.width + 20); // 10px padding mỗi bên
        });

        bar.addEventListener('mousemove', (e) => {
            const pos = getMousePosition(e);
            tooltip.setAttribute('transform', `translate(${pos.x + 12}, ${pos.y - 30})`);
        });

        bar.addEventListener('mouseout', () => {
            tooltip.style.visibility = 'hidden';
        });
    });
}

// static/chart_modules/line.js

/**
 * TẠO BIỂU ĐỒ ĐƯỜNG VỚI CÁC TÙY CHỌN NÂNG CAO
 * Hàm này sẽ vẽ một biểu đồ đường SVG bên trong một element container được chỉ định.
 *
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ (ví dụ: document.getElementById('myChart')).
 * @param {Array<number>} data - Mảng các giá trị số để vẽ biểu đồ.
 * @param {object} [options={}] - Một đối tượng chứa các tùy chọn cấu hình cho biểu đồ.
 * @param {string} [options.color='var(--accent-color)'] - Màu chính của đường, vùng tô và các điểm. Có thể dùng bất kỳ biến màu nào từ colors.css.
 * @param {string} [options.valuePrefix=''] - Tiền tố để thêm vào trước nhãn giá trị (ví dụ: '$').
 * @param {string} [options.valueSuffix=''] - Hậu tố để thêm vào sau nhãn giá trị (ví dụ: '%').
 * @param {number} [options.strokeWidth=2.5] - Độ dày của đường biểu đồ.
 */
function createLineChart(container, data, options = {}) {
    // Kiểm tra đầu vào để đảm bảo hàm hoạt động chính xác
    if (!container || !Array.isArray(data) || data.length === 0) {
        console.error("Container hoặc dữ liệu không hợp lệ để vẽ biểu đồ.");
        return;
    }

    // Thiết lập các giá trị mặc định cho options
    const {
        color = 'var(--accent-color)',
        valuePrefix = '',
        valueSuffix = '',
        strokeWidth = 2.5
    } = options;

    // Kích thước và padding của SVG
    const width = 320;
    const height = 160;
    const p = 35; // Padding

    // Tính toán các giá trị cần thiết để xác định tỷ lệ
    const maxValue = Math.max(...data);
    const minValue = Math.min(...data);
    // Thêm một chút khoảng đệm (10% trên và 10% dưới) để biểu đồ không bị cắt
    const valueRange = (maxValue - minValue) * 1.2 || 1;
    const rangeMin = minValue - (maxValue - minValue) * 0.1;

    // Hàm chuyển đổi tọa độ: từ chỉ số mảng và giá trị dữ liệu sang tọa độ (x, y) trên SVG
    const toX = i => (i / (data.length - 1)) * (width - 2 * p) + p;
    const toY = val => height - p - ((val - rangeMin) / valueRange) * (height - 2 * p);

    // Tạo chuỗi tọa độ cho đường và vùng tô
    const points = data.map((d, i) => `${toX(i)},${toY(d)}`).join(' ');
    const areaPoints = `${p},${height - p} ${points} ${width - p},${height - p}`;

    // Tạo mã SVG động
    const svg = `
        <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: auto; overflow: visible;" class="line-chart-interactive">
            <defs>
                <linearGradient id="areaGradient-${container.id}" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stop-color="${color}" stop-opacity="0.25" />
                    <stop offset="100%" stop-color="${color}" stop-opacity="0" />
                </linearGradient>
            </defs>

            <polygon fill="url(#areaGradient-${container.id})" points="${areaPoints}" class="line-area" />

            <polyline fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"
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

    // Gán SVG vào container và thêm class
    container.innerHTML = svg;
    container.classList.add('line-chart-container');
}

// static/chart_modules/doughnut.js

/**
 * =============================================================================
 * TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART) ĐƯỢC CẢI TIẾN
 * =============================================================================
 * Phụ thuộc vào các hàm trong 'utils.js'.
 * Kiểu dáng được điều khiển bởi 'doughnut-chart.css'.
 *
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {Array<object>} data - Dữ liệu. Vd: [{ value: 30, label: 'A', color: '#FF6384' }]
 * @param {object|string} config - Đối tượng cấu hình cho biểu đồ hoặc title string (backward compatibility).
 * @param {string} [config.title=''] - Tiêu đề hiển thị ở giữa biểu đồ.
 * @param {number} [config.outerRadius=80] - Bán kính ngoài của biểu đồ.
 * @param {number} [config.innerRadius=50] - Bán kính trong của biểu đồ.
 * @param {boolean} [config.showLegend=true] - Có hiển thị chú thích hay không.
 */
function createDoughnutChart(container, data, config = {}) {
    // --- BACKWARD COMPATIBILITY ---
    // Nếu tham số thứ 3 là string, tạo config object với title
    if (typeof config === 'string') {
        config = { title: config, showLegend: true };
    }
    // --- 1. KIỂM TRA ĐẦU VÀO ---
    if (!container) {
        console.error("Lỗi: Container element không được cung cấp cho createDoughnutChart.");
        return;
    }

    if (!data || data.length === 0) {
        container.innerHTML = '<div class="doughnut-error">Không có dữ liệu để hiển thị.</div>';
        return;
    }

    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) {
        container.innerHTML = '<div class="doughnut-error">Tổng giá trị bằng 0, không thể vẽ biểu đồ.</div>';
        return;
    }

    // --- 2. CẤU HÌNH & HẰNG SỐ ---
    const cfg = {
        title: '',
        outerRadius: 80,
        innerRadius: 50,
        showLegend: true,
        ...config,
    };

    const SVG_SIZE = 180;
    const CENTER_X = SVG_SIZE / 2;
    const CENTER_Y = SVG_SIZE / 2;
    const SVG_NS = "http://www.w3.org/2000/svg";

    // --- 3. TÍNH TOÁN LOGIC ---
    const validData = data.filter(d => d.value > 0);
    
    // --- 4. TẠO CÁC THÀNH PHẦN SVG ---

    // Hàm trợ giúp để tạo phần tử SVG và đặt thuộc tính
    function createSvgElement(tag, attributes) {
        const element = document.createElementNS(SVG_NS, tag);
        for (const key in attributes) {
            element.setAttribute(key, attributes[key]);
        }
        return element;
    }

    // Xóa nội dung cũ và thêm class vào container
    container.innerHTML = '';
    container.classList.add('doughnut-container');

    // Tạo wrapper chính
    const wrapper = document.createElement('div');
    wrapper.className = 'doughnut-chart-wrapper';

    // Tạo phần biểu đồ
    const chartSection = document.createElement('div');
    chartSection.className = 'doughnut-chart-section';

    // Tạo SVG element chính
    const svg = createSvgElement('svg', {
        viewBox: `0 0 ${SVG_SIZE} ${SVG_SIZE}`,
        class: 'doughnut-svg'
    });

    // Tạo group cho các segments
    const segmentsGroup = createSvgElement('g', { class: 'doughnut-segments-group' });

    // a. Tạo các segments
    let currentAngle = 0;
    const segments = [];

    validData.forEach((d, i) => {
        const percentage = d.value / total;
        const angleSpan = percentage * 360;
        const endAngle = currentAngle + angleSpan;
        
        const pathData = describeDoughnutArc(CENTER_X, CENTER_Y, cfg.outerRadius, cfg.innerRadius, currentAngle, endAngle);
        
        const segmentPath = createSvgElement('path', {
            d: pathData,
            fill: d.color,
            class: 'doughnut-segment',
            'data-index': i,
            'data-value': d.value,
            'data-percentage': (percentage * 100).toFixed(1),
            'data-label': d.label
        });

        segments.push({
            element: segmentPath,
            data: d,
            percentage: percentage * 100,
            index: i
        });

        segmentsGroup.appendChild(segmentPath);
        currentAngle = endAngle;
    });

    svg.appendChild(segmentsGroup);

    // b. Tạo title ở giữa (nếu có)
    if (cfg.title) {
        const titleText = createSvgElement('text', {
            x: CENTER_X,
            y: CENTER_Y,
            class: 'doughnut-title-text'
        });
        titleText.textContent = cfg.title;
        svg.appendChild(titleText);
    }

    chartSection.appendChild(svg);
    wrapper.appendChild(chartSection);

    // c. Tạo legend (nếu được yêu cầu)
    let legendItems = [];
    if (cfg.showLegend) {
        const legendSection = document.createElement('div');
        legendSection.className = 'doughnut-legend-section';

        validData.forEach((d, i) => {
            const percentage = (d.value / total * 100).toFixed(1);
            
            const legendItem = document.createElement('div');
            legendItem.className = 'doughnut-legend-item';
            legendItem.dataset.index = i;

            const colorBox = document.createElement('span');
            colorBox.className = 'doughnut-legend-color';
            colorBox.style.backgroundColor = d.color;

            const labelSpan = document.createElement('span');
            labelSpan.className = 'doughnut-legend-label';
            labelSpan.textContent = `${d.label}: ${percentage}%`;

            legendItem.appendChild(colorBox);
            legendItem.appendChild(labelSpan);
            legendSection.appendChild(legendItem);

            legendItems.push(legendItem);
        });

        wrapper.appendChild(legendSection);
    }

    // --- 5. THIẾT LẬP HIỆU ỨNG HOVER ---
    function handleMouseEnter(event) {
        const target = event.currentTarget;
        const index = parseInt(target.dataset.index);
        
        // Thêm class highlight cho container
        wrapper.classList.add('is-highlighted');
        
        // Highlight segment tương ứng
        segments.forEach((seg, i) => {
            if (i === index) {
                seg.element.classList.add('highlight');
            } else {
                seg.element.classList.add('dimmed');
            }
        });

        // Highlight legend item tương ứng
        if (cfg.showLegend) {
            legendItems.forEach((item, i) => {
                if (i === index) {
                    item.classList.add('highlight');
                } else {
                    item.classList.add('dimmed');
                }
            });
        }
    }

    function handleMouseLeave(event) {
        // Xóa tất cả highlight và dimmed classes
        wrapper.classList.remove('is-highlighted');
        segments.forEach(seg => {
            seg.element.classList.remove('highlight', 'dimmed');
        });
        
        if (cfg.showLegend) {
            legendItems.forEach(item => {
                item.classList.remove('highlight', 'dimmed');
            });
        }
    }

    // Thêm event listeners cho segments
    segments.forEach(seg => {
        seg.element.addEventListener('mouseenter', handleMouseEnter);
        seg.element.addEventListener('mouseleave', handleMouseLeave);
    });

    // Thêm event listeners cho legend items
    if (cfg.showLegend) {
        legendItems.forEach(item => {
            item.addEventListener('mouseenter', handleMouseEnter);
            item.addEventListener('mouseleave', handleMouseLeave);
        });
    }

    // --- 6. RENDER BIỂU ĐỒ ---
    container.appendChild(wrapper);
}

