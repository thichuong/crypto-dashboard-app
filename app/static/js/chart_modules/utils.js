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