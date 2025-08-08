// log-manager.js - Activity Log Management
export class LogManager {
    static logEntries = [];
    
    static init() {
        this.add('🔐 Phiên truy cập an toàn được khởi tạo', 'info');
        this.add('🚀 Khởi tạo Auto Update System với Combined Research + Validation', 'info');
        
        // Security reminder
        setTimeout(() => {
            this.add('⚠️ Nhắc nhở: Không chia sẻ URL này với người khác', 'info');
        }, 5000);
    }
    
    static add(message, type = 'info') {
        const timestamp = new Date().toLocaleString('vi-VN');
        const entry = {
            timestamp: timestamp,
            message: message,
            type: type
        };
        
        this.logEntries.unshift(entry);
        
        // Keep only last 50 entries
        if (this.logEntries.length > 50) {
            this.logEntries = this.logEntries.slice(0, 50);
        }
        
        this.updateDisplay();
    }
    
    static updateDisplay() {
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;
        
        logContainer.innerHTML = '';
        
        // Insert entries from newest to oldest
        this.logEntries.forEach(entry => {
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry log-${entry.type}`;
            logDiv.innerHTML = `<span class="log-timestamp">[${entry.timestamp}]</span> ${entry.message}`;
            logContainer.insertBefore(logDiv, logContainer.firstChild);
        });
    }
    
    static clear() {
        this.logEntries = [];
        this.updateDisplay();
        this.add('Đã xóa nhật ký hoạt động', 'info');
    }
}
