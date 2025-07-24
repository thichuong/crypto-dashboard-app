/* FILE: report.js */
/* Contains functions to draw charts and gauges for the report. */

/**
 * Creates a semi-circular gauge chart in a specified container.
 * @param {string} elementId - The ID of the container element for the gauge.
 * @param {string} label - The text label to display below the gauge.
 * @param {number} value - The current value to display on the gauge.
 * @param {number} min - The minimum value of the gauge.
 * @param {number} max - The maximum value of the gauge.
 * @param {Array<object>} zones - An array of zone objects { color, from, to }.
 */
function createGauge(elementId, label, value, min, max, zones) {
    const container = document.getElementById(elementId);
    if (!container) return;

    // Clear previous content
    container.innerHTML = '';

    const viewBoxSize = 200;
    const strokeWidth = 20;
    const cx = viewBoxSize / 2;
    const cy = viewBoxSize / 2 + 30; // Move center down
    const radius = (viewBoxSize / 2) - strokeWidth;

    const angleOffset = -180; // Start from the left

    const valueToAngle = (val) => {
        return angleOffset + ((val - min) / (max - min)) * 180;
    };

    const polarToCartesian = (centerX, centerY, r, angleInDegrees) => {
        const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
        return {
            x: centerX + (r * Math.cos(angleInRadians)),
            y: centerY + (r * Math.sin(angleInRadians))
        };
    };

    const describeArc = (x, y, r, startAngle, endAngle) => {
        const start = polarToCartesian(x, y, r, endAngle);
        const end = polarToCartesian(x, y, r, startAngle);
        const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
        return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
    };

    let svg = `<svg viewBox="0 0 ${viewBoxSize} ${cy + 10}" class="gauge-container" role="img" aria-label="${label}: ${value}">`;

    // Draw zones
    zones.forEach(zone => {
        const startAngle = valueToAngle(zone.from);
        const endAngle = valueToAngle(zone.to);
        svg += `<path d="${describeArc(cx, cy, radius, startAngle, endAngle)}" fill="none" stroke="${zone.color}" stroke-width="${strokeWidth}" />`;
    });

    // Draw needle
    const valueAngle = valueToAngle(value);
    const needleLength = radius - 5;
    const needleTip = polarToCartesian(cx, cy, needleLength, valueAngle);
    svg += `<line x1="${cx}" y1="${cy}" x2="${needleTip.x}" y2="${needleTip.y}" stroke="var(--text-primary)" stroke-width="3" />`;
    svg += `<circle cx="${cx}" cy="${cy}" r="5" fill="var(--text-primary)" />`;
    
    // Add value text
    svg += `<text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="24" font-weight="bold" fill="var(--text-accent)">${value.toFixed(2)}</text>`;
    
    // Add min/max labels
    svg += `<text x="${cx - radius - 5}" y="${cy + 15}" text-anchor="middle" font-size="12" fill="var(--text-secondary)">${min}</text>`;
    svg += `<text x="${cx + radius + 5}" y="${cy + 15}" text-anchor="middle" font-size="12" fill="var(--text-secondary)">${max}</text>`;

    svg += '</svg>';
    svg += `<div class="gauge-label">${label}</div>`;

    container.innerHTML = svg;
}

/**
 * Initializes all gauges present in the report.
 * This function should be called after the HTML content is loaded.
 */
function initializeAllGauges() {
    // --- RSI Gauge ---
    const rsiValue = 54.86;
    const rsiZones = [
        { color: 'var(--rsi-oversold-color)', from: 0, to: 30 },
        { color: 'var(--rsi-neutral-color)', from: 30, to: 70 },
        { color: 'var(--rsi-overbought-color)', from: 70, to: 100 }
    ];
    createGauge(
        'rsi-gauge-container',
        'Chỉ số Sức mạnh Tương đối (RSI)',
        rsiValue, 0, 100, rsiZones
    );

    // --- Fear & Greed Gauge ---
    const fngValue = 72; // Representative value from the 67-74 range
    const fngZones = [
        { color: 'var(--fng-extreme-fear-color)', from: 0, to: 25 },
        { color: 'var(--fng-fear-color)', from: 25, to: 45 },
        { color: 'var(--fng-neutral-color)', from: 45, to: 55 },
        { color: 'var(--fng-greed-color)', from: 55, to: 75 },
        { color: 'var(--fng-extreme-greed-color)', from: 75, to: 100 }
    ];
    createGauge(
        'fng-gauge-container',
        'Chỉ số Sợ hãi & Tham lam',
        fngValue, 0, 100, fngZones
    );
}

// Note: The main script (e.g., main.js) should call initializeAllGauges()
// after successfully loading report.html into the DOM.