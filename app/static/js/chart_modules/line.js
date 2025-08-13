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

    // Kích thước và padding của SVG (tăng kích thước)
    const width = 480;
    const height = 340;
    const p = 60; // Padding tăng để tránh nhãn vẽ ra ngoài

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

    // Xác định các chỉ số cần hiển thị: đầu, cuối, cao nhất, thấp nhất
    const firstIdx = 0;
    const lastIdx = data.length - 1;
    const maxIdx = data.indexOf(maxValue);
    const minIdx = data.indexOf(minValue);
    // Tạo mảng các chỉ số cần hiển thị, loại bỏ trùng lặp
    const showIndices = Array.from(new Set([firstIdx, lastIdx, maxIdx, minIdx]));

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

            ${data.map((d, i) => {
                let label = '';
                if (i === firstIdx) {
                    // Nhãn đầu ở bên trái
                    label = `<text x="${toX(i) - 12}" y="${toY(d) + 3}" text-anchor="end"
                        fill="var(--text-primary)" font-weight="600" class="value-label h3">
                        ${valuePrefix}${d.toFixed(1)}${valueSuffix}
                    </text>`;
                } else if (i === lastIdx) {
                    // Nhãn cuối ở bên phải
                    label = `<text x="${toX(i) + 12}" y="${toY(d) + 3}" text-anchor="start"
                        fill="var(--text-primary)" font-weight="600" class="value-label h3">
                        ${valuePrefix}${d.toFixed(1)}${valueSuffix}
                    </text>`;
                } else if (i === maxIdx || i === minIdx) {
                    // Nhãn max/min ở phía trên
                    label = `<text x="${toX(i)}" y="${toY(d) - 12}" text-anchor="middle"
                        fill="var(--text-primary)" font-weight="600" class="value-label h3">
                        ${valuePrefix}${d.toFixed(1)}${valueSuffix}
                    </text>`;
                }
                return `
                    <g class="line-point-group">
                        <circle cx="${toX(i)}" cy="${toY(d)}" r="9" fill="transparent" />
                        <circle cx="${toX(i)}" cy="${toY(d)}" r="4" fill="${color}"
                                stroke="var(--bg-secondary)" stroke-width="2" class="line-dot"
                                style="animation-delay: ${i * 80}ms"/>
                        ${showIndices.includes(i) ? label : ''}
                    </g>
                `;
            }).join('')}
        </svg>
    `;

    // Gán SVG vào container và thêm class
    container.innerHTML = svg;
    container.classList.add('line-chart-container');

    // Tạo tooltip
    let tooltip = container.querySelector('.line-chart-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'line-chart-tooltip';
        container.appendChild(tooltip);
    }

    // Xử lý tooltip cho các điểm
    const svgEl = container.querySelector('svg');
    const pointGroups = svgEl.querySelectorAll('.line-point-group');
    pointGroups.forEach((group, i) => {
        const dot = group.querySelector('.line-dot');
        dot.addEventListener('mouseenter', (e) => {
            const value = data[i];
            tooltip.textContent = `${valuePrefix}${value.toFixed(2)}${valueSuffix}`;
            tooltip.classList.add('active');
        });
        dot.addEventListener('mousemove', (e) => {
            // Hiển thị tooltip tại vị trí con trỏ chuột
            const rect = container.getBoundingClientRect();
            tooltip.style.left = `${e.clientX - rect.left + 12}px`;
            tooltip.style.top = `${e.clientY - rect.top - 32}px`;
        });
        dot.addEventListener('mouseleave', () => {
            tooltip.classList.remove('active');
        });
    });
}