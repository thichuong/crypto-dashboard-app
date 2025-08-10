/**
 * report-initializer.js
 * 
 * File chuyên dụng để khởi tạo các visualization trong báo cáo.
 * Được sử dụng riêng cho trang PDF template và các trang báo cáo khác.
 */

/**
 * Khởi tạo tất cả các visualization cho báo cáo
 * Đảm bảo gọi hàm này sau khi DOM và các thư viện cần thiết đã được tải
 */
function initializeReportVisuals() {
    console.log("🎨 Bắt đầu khởi tạo report visuals...");
    
    // Kiểm tra xem các thư viện cần thiết đã được tải chưa
    if (typeof createGauge !== 'function' || 
        typeof createDoughnutChart !== 'function' || 
        typeof createBarChart !== 'function') {
        console.warn("⚠️ Thư viện charting chưa được tải. Đợi và thử lại...");
        
        // Thử lại sau 500ms
        setTimeout(initializeReportVisuals, 500);
        return;
    }
    
    // Kiểm tra xem hàm initializeAllVisuals_report có tồn tại không
    if (typeof initializeAllVisuals_report !== 'function') {
        console.warn("⚠️ Hàm initializeAllVisuals_report chưa được tải. Đợi và thử lại...");
        
        // Thử lại sau 500ms
        setTimeout(initializeReportVisuals, 500);
        return;
    }
    
    try {
        // Gọi hàm khởi tạo từ report.js
        initializeAllVisuals_report();
        console.log("✅ Đã khởi tạo thành công tất cả report visuals");
    } catch (error) {
        console.error("❌ Lỗi khi khởi tạo report visuals:", error);
    }
}

/**
 * Khởi tạo với retry mechanism
 * Đảm bảo các visualization được tạo thành công
 */
function initializeReportVisualsWithRetry(maxRetries = 5, retryDelay = 1000) {
    let attempts = 0;
    
    function attempt() {
        attempts++;
        console.log(`🔄 Thử khởi tạo report visuals (lần ${attempts}/${maxRetries})`);
        
        // Kiểm tra các điều kiện cần thiết
        const hasChartLibrary = typeof createGauge === 'function' && 
                               typeof createDoughnutChart === 'function' && 
                               typeof createBarChart === 'function';
        
        const hasReportFunction = typeof initializeAllVisuals_report === 'function';
        
        if (hasChartLibrary && hasReportFunction) {
            try {
                initializeAllVisuals_report();
                console.log("✅ Khởi tạo report visuals thành công!");
                return true;
            } catch (error) {
                console.error("❌ Lỗi khi khởi tạo:", error);
            }
        } else {
            console.log("⏳ Chưa đủ điều kiện để khởi tạo:", {
                hasChartLibrary,
                hasReportFunction
            });
        }
        
        // Thử lại nếu chưa đạt max retries
        if (attempts < maxRetries) {
            setTimeout(attempt, retryDelay);
        } else {
            console.warn("⚠️ Đã thử tối đa nhưng không thể khởi tạo report visuals");
        }
        
        return false;
    }
    
    attempt();
}

/**
 * Khởi tạo khi DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("📄 DOM đã sẵn sàng, chuẩn bị khởi tạo report visuals...");
    
    // Đợi một chút để đảm bảo tất cả script khác đã được tải
    setTimeout(() => {
        initializeReportVisualsWithRetry();
    }, 100);
});

/**
 * Khởi tạo khi window load (backup)
 */
window.addEventListener('load', function() {
    console.log("🌐 Window đã load hoàn toàn");
    
    // Chỉ thử lại nếu chưa được khởi tạo
    if (typeof window.reportVisualsInitialized === 'undefined') {
        setTimeout(() => {
            initializeReportVisualsWithRetry(3, 500);
        }, 200);
    }
});

// Export functions for manual use
window.initializeReportVisuals = initializeReportVisuals;
window.initializeReportVisualsWithRetry = initializeReportVisualsWithRetry;
