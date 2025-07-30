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