// ui-controller.js - UI State Management
import { APIClient } from './api-client.js';
import { LogManager } from './log-manager.js';
import { ProgressTracker } from './progress-tracker.js';
import { StatusManager } from './status-manager.js';

export class UIController {
    constructor() {
        this.progressTracker = new ProgressTracker();
        this.statusManager = new StatusManager();
    }
    
    async init() {
        LogManager.init();
        await this.statusManager.init();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Global functions for HTML onclick handlers
        window.triggerManualReport = () => this.triggerManualReport();
        window.viewLatestReport = () => this.viewLatestReport();
        window.clearLog = () => LogManager.clear();
        window.refreshStatus = () => this.statusManager.refresh();
        window.closeSuccessOverlay = () => this.closeSuccessOverlay();
        window.closeErrorOverlay = () => this.closeErrorOverlay();
        window.cancelProgress = () => this.cancelProgress();
    }
    
    async triggerManualReport() {
        // Confirmation dialog
        if (!confirm('Bạn có chắc chắn muốn tạo báo cáo mới với Combined Research + Validation? Quá trình này có thể mất vài phút.')) {
            return;
        }
        
        const btn = document.getElementById('trigger-report-btn');
        const originalContent = btn.innerHTML;
        
        // Show loading state
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Đang tạo báo cáo (Combined)...';
        btn.disabled = true;
        
        LogManager.add('🚀 Bắt đầu tạo báo cáo với Combined Research + Validation', 'info');
        
        try {
            const data = await APIClient.triggerReport();
            
            if (data.success) {
                LogManager.add(`📡 Đã kết nối Combined Workflow tracking: ${data.session_id}`, 'info');
                this.progressTracker.startTracking(data.session_id);
                LogManager.add('✅ Combined Research + Validation Workflow đã được khởi chạy', 'success');
            } else {
                this.showError(data.message);
                LogManager.add(`❌ Lỗi Combined Workflow: ${data.message}`, 'error');
                this.restoreButton(btn, originalContent);
            }
            
        } catch (error) {
            const errorMsg = `Lỗi kết nối Combined Workflow: ${error.message}`;
            this.showError(errorMsg);
            LogManager.add(`🔌 ${errorMsg}`, 'error');
            this.restoreButton(btn, originalContent);
        }
    }
    
    viewLatestReport() {
        LogManager.add('📄 Chuyển đến trang chủ để xem báo cáo mới nhất', 'info');
        window.open('/', '_blank');
    }
    
    closeSuccessOverlay() {
        document.getElementById('success-overlay').style.display = 'none';
        this.progressTracker.stopTracking();
        this.statusManager.refresh(); // Refresh to show new report count
    }
    
    closeErrorOverlay() {
        document.getElementById('error-overlay').style.display = 'none';
        this.progressTracker.stopTracking();
    }
    
    cancelProgress() {
        if (this.progressTracker.sessionId) {
            if (confirm('Bạn có chắc chắn muốn dừng quá trình Combined Research + Validation?')) {
                LogManager.add('🛑 Người dùng đã dừng Combined Workflow', 'info');
                this.progressTracker.cancelTracking();
            }
        }
    }
    
    showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('error-overlay').style.display = 'flex';
    }
    
    restoreButton(btn, originalContent) {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}
