// static/chart_modules/doughnut.js

/**
 * TẠO BIỂU ĐỒ TRÒN (DOUGHNUT CHART)
 * Phụ thuộc: utils.js (describeDoughnutArc)
 * @param {HTMLElement} container - Element DOM để chứa biểu đồ.
 * @param {Array<object>} data - Dữ liệu. Vd: [{ value: 30, label: 'A', color: '#FF6384' }]
 * @param {string} [title=''] - Tiêu đề hiển thị ở giữa biểu đồ.
 */
function createDoughnutChart(container, data, title = '') {
    if (!container || !data || data.length === 0) {
        if (container) container.innerHTML = 'Không có dữ liệu để hiển thị.';
        return;
    }

    const total = data.reduce((sum, d) => sum + d.value, 0);
    if (total === 0) {
        if (container) container.innerHTML = 'Tổng giá trị bằng 0, không thể vẽ biểu đồ.';
        return;
    }

    const width = 180, height = 180;
    const cx = width / 2;
    const cy = height / 2;
    const outerRadius = 80;
    const innerRadius = 50;
    const chartId = `doughnut-${Math.random().toString(36).substring(2, 9)}`;

    let startAngle = 0;
    let segmentsHTML = '';
    let legendHTML = '';

    data.forEach((d, i) => {
        if (d.value <= 0) return;

        const percentage = d.value / total;
        const angleSpan = percentage * 360;
        const endAngle = startAngle + angleSpan;
        const segmentId = `${chartId}-segment-${i}`;
        const legendId = `${chartId}-legend-${i}`;
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

        const percentageDisplay = (percentage * 100).toFixed(1);
        legendHTML += `
            <div id="${legendId}" class="legend-item" data-segment-id="${segmentId}">
                <span class="legend-color-box" style="background-color: ${d.color};"></span>
                <span>${d.label}: <strong>${percentageDisplay}%</strong></span>
            </div>`;
        
        startAngle = endAngle;
    });

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
    
    const chartContainer = container.querySelector('.doughnut-chart-container');
    const interactiveElements = container.querySelectorAll('.doughnut-segment, .legend-item');

    const handleMouseEnter = (event) => {
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
        if (chartContainer) chartContainer.classList.remove('is-highlighted');
        container.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));
    };

    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', handleMouseEnter);
        el.addEventListener('mouseleave', handleMouseLeave);
    });
}