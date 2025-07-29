// static/chart_modules/line.js

/**
 * TẠO BIỂU ĐỒ ĐƯỜNG (LINE CHART)
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
    container.classList.add('line-chart-container');
}