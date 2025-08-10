/**
 * simple-report-init.js
 * 
 * File JavaScript đơn giản để khởi tạo visualization báo cáo.
 * Sử dụng cho các trang cần call initializeAllVisuals_report() một cách đơn giản.
 */

(function() {
    'use strict';
    
    /**
     * Hàm đơn giản để gọi initializeAllVisuals_report
     */
    function callInitializeAllVisuals() {
        if (typeof initializeAllVisuals_report === 'function') {
            console.log("✅ Gọi initializeAllVisuals_report()");
            initializeAllVisuals_report();
        } else {
            console.warn("⚠️ Hàm initializeAllVisuals_report không tồn tại");
        }
    }
    
    /**
     * Kiểm tra và gọi hàm với timeout
     */
    function initWithDelay() {
        // Thử gọi ngay lập tức
        callInitializeAllVisuals();
        
        // Thử lại sau 1 giây để đảm bảo
        setTimeout(callInitializeAllVisuals, 1000);
        
        // Thử lại sau 3 giây nếu vẫn chưa được
        setTimeout(callInitializeAllVisuals, 3000);
    }
    
    // Gọi khi DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWithDelay);
    } else {
        // DOM đã sẵn sàng
        initWithDelay();
    }
    
    // Export để có thể gọi manually
    window.callInitializeAllVisuals = callInitializeAllVisuals;
    
})();
