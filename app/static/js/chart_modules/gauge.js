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

    // Tạo SVG element chính với viewBox tối ưu cho responsive
    const svg = createSvgElement('svg', {
        viewBox: "0 0 200 140",
        preserveAspectRatio: "xMidYMid meet",
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

    // d. Tạo các nhãn văn bản với vị trí tối ưu hơn
    const valueText = createSvgElement('text', {
        x: 100,
        y: 100,
        class: 'gauge-text gauge-value-text'
    });
    valueText.textContent = value.toFixed(1);

    const labelText = createSvgElement('text', {
        x: 100,
        y: 120,
        fill: valueColor, // Color được đặt trực tiếp vì nó là dữ liệu động
        class: 'gauge-text gauge-label-text'
    });
    labelText.textContent = classification;

    svg.append(valueText, labelText);

    // --- 5. RENDER BIỂU ĐỒ ---
    container.appendChild(svg);
}