// progress-tracker.js - Simplified Progress Tracking
import { APIClient } from './api-client.js';
import { LogManager } from './log-manager.js';

export class ProgressTracker {
    constructor() {
        this.sessionId = null;
        this.pollingInterval = null;
        this.processedLogIds = new Set();
        this.lastUpdateTime = 0;
    }
    
    startTracking(sessionId) {
        this.sessionId = sessionId;
        this.showProgressCard();
        this.startPolling();
        LogManager.add('📡 Bắt đầu theo dõi tiến độ', 'info');
    }
    
    stopTracking() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            LogManager.add('⏹️ Dừng theo dõi tiến độ', 'info');
        }
        this.sessionId = null;
        this.processedLogIds.clear();
        this.lastUpdateTime = 0;
    }
    
    cancelTracking() {
        this.stopTracking();
        this.hideProgressCard();
        this.restoreButton();
    }
    
    async startPolling() {
        this.pollingInterval = setInterval(async () => {
            const progress = await APIClient.getProgress(this.sessionId);
            if (progress) {
                this.processUpdate(progress);
                
                if (['completed', 'error'].includes(progress.status)) {
                    this.stopTracking();
                }
            }
        }, 2000);
    }
    
    processUpdate(progress) {
        // Only update if there's actual change
        const currentUpdateTime = progress.last_update || 0;
        if (currentUpdateTime <= this.lastUpdateTime) {
            return;
        }
        this.lastUpdateTime = currentUpdateTime;
        
        // Update UI
        this.updateProgressBar(progress);
        this.updateProgressDetails(progress);
        this.processLogEntries(progress.step_queue || []);
        
        // Handle completion states
        if (progress.status === 'completed') {
            this.handleCompletion(progress);
        } else if (progress.status === 'error') {
            this.handleError(progress);
        }
    }
    
    updateProgressBar(progress) {
        const cleanStepName = (progress.current_step_name || "").replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
        const percentage = progress.percentage || 0;
        
        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressStepName = document.getElementById('progress-step-name');
        
        progressBar.style.width = `${percentage}%`;
        progressPercentage.textContent = `${percentage}%`;
        progressStepName.textContent = cleanStepName;
    }
    
    updateProgressDetails(progress) {
        const cleanDetails = (progress.details || "").replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
        if (cleanDetails) {
            const progressDetailsText = document.getElementById('progress-details-text');
            progressDetailsText.textContent = cleanDetails;
        }
    }
    
    processLogEntries(stepQueue) {
        const progressLogContainer = document.getElementById('progress-log');
        
        stepQueue.forEach(logEntry => {
            const logId = `${this.sessionId}_${logEntry.type}_${logEntry.timestamp}_${logEntry.details}`;
            
            if (!this.processedLogIds.has(logId)) {
                const logDiv = this.createLogElement(logEntry);
                if (logDiv) {
                    progressLogContainer.appendChild(logDiv);
                    this.processedLogIds.add(logId);
                }
            }
        });
        
        // Keep only last 20 log entries
        while (progressLogContainer.children.length > 20) {
            progressLogContainer.removeChild(progressLogContainer.firstChild);
        }
    }
    
    createLogElement(logEntry) {
        let cleanDetails = logEntry.details.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
        
        // Format step entries
        if (logEntry.type === 'step') {
            cleanDetails = this.formatStepName(cleanDetails);
            const logDiv = document.createElement('div');
            logDiv.className = 'log-entry log-info';
            logDiv.innerHTML = `<span class="log-timestamp">${cleanDetails}</span>`;
            return logDiv;
        }
        
        // Format detail entries
        if (logEntry.type === 'detail') {
            cleanDetails = this.formatDetailMessage(cleanDetails);
            const logType = this.determineLogType(cleanDetails);
            
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry ${logType}`;
            logDiv.innerHTML = `<span class="log-timestamp">📋 ${cleanDetails}</span>`;
            return logDiv;
        }
        
        return null;
    }
    
    formatStepName(details) {
        const stepMappings = {
            "Research + Validation": "🔬 Research + Validation",
            "Parse validation": "✅ Parse Validation",
            "Chuẩn bị dữ liệu": "📋 Chuẩn bị dữ liệu",
            "Tạo giao diện": "🎨 Tạo giao diện",
            "Trích xuất mã nguồn": "📄 Trích xuất mã nguồn",
            "Lưu báo cáo": "💾 Lưu báo cáo"
        };
        
        for (const [key, value] of Object.entries(stepMappings)) {
            if (details.includes(key)) {
                details = details.replace(key, value);
            }
        }
        return details;
    }
    
    formatDetailMessage(details) {
        const detailMappings = {
            "inject real-time data": "📊 inject real-time data",
            "Combined Research + Validation": "🔬 Combined Research + Validation",
            "Combined response": "📝 Combined response",
            "Parse validation": "✅ Parse validation",
            "Parsed validation result": "✅ Parsed validation result"
        };
        
        for (const [key, value] of Object.entries(detailMappings)) {
            if (details.includes(key)) {
                details = details.replace(key, value);
            }
        }
        return details;
    }
    
    determineLogType(details) {
        if (details.includes('✓') || details.includes('Hoàn thành') || details.includes('thành công') || details.includes('PASS')) {
            return 'log-success';
        } else if (details.includes('✗') || details.includes('Lỗi') || details.includes('thất bại') || details.includes('FAIL')) {
            return 'log-error';
        } else if (details.includes('⚠️') || details.includes('UNKNOWN')) {
            return 'log-info';
        } else if (details.includes('🔬') || details.includes('📊') || details.includes('📝')) {
            return 'log-info';
        }
        return 'log-step-complete';
    }
    
    handleCompletion(progress) {
        this.updateProgressBar({ percentage: 100, current_step_name: 'Hoàn thành!' });
        this.updateProgressDetails({ details: `Báo cáo #${progress.report_id} đã được tạo thành công với Combined Research + Validation!` });
        
        // Add success log
        const progressLogContainer = document.getElementById('progress-log');
        const successLogDiv = document.createElement('div');
        successLogDiv.className = 'log-entry log-success';
        successLogDiv.innerHTML = `<i class="fas fa-check-circle text-green-500 mr-2"></i><span class="log-timestamp">🎉 Hoàn thành tạo báo cáo #${progress.report_id} (Combined Workflow)</span>`;
        progressLogContainer.appendChild(successLogDiv);
        
        // Show success overlay
        document.getElementById('success-message').textContent = 
            `Báo cáo #${progress.report_id} đã được tạo thành công với Combined Research + Validation!`;
        document.getElementById('success-overlay').style.display = 'flex';
        
        this.restoreButton();
        LogManager.add('🎉 Hoàn thành tạo báo cáo với Combined Workflow!', 'success');
    }
    
    handleError(progress) {
        this.updateProgressBar({ percentage: progress.percentage || 0, current_step_name: 'Lỗi xảy ra' });
        this.updateProgressDetails({ details: progress.details || 'Có lỗi xảy ra trong quá trình Combined Research + Validation' });
        
        // Add error log
        const progressLogContainer = document.getElementById('progress-log');
        const errorLogDiv = document.createElement('div');
        errorLogDiv.className = 'log-entry log-error';
        errorLogDiv.innerHTML = `<i class="fas fa-times text-red-500 mr-2"></i><span class="log-timestamp">💥 Lỗi Combined Workflow: ${progress.details || 'Có lỗi xảy ra'}</span>`;
        progressLogContainer.appendChild(errorLogDiv);
        
        // Show error overlay
        document.getElementById('error-message').textContent = 
            progress.details || 'Có lỗi xảy ra trong quá trình Combined Research + Validation';
        document.getElementById('error-overlay').style.display = 'flex';
        
        this.restoreButton();
        LogManager.add('💥 Có lỗi xảy ra trong Combined Workflow!', 'error');
    }
    
    showProgressCard() {
        const progressCard = document.getElementById('progress-card');
        const sessionIdElement = document.getElementById('progress-session-id');
        
        progressCard.style.display = 'block';
        sessionIdElement.textContent = `Session: ${this.sessionId.substring(0, 8)}...`;
        
        // Reset state
        this.lastUpdateTime = 0;
        this.processedLogIds.clear();
        
        // Initialize progress display
        this.updateProgressBar({ percentage: 0, current_step_name: "Đang khởi tạo..." });
        this.updateProgressDetails({ details: "Chuẩn bị bắt đầu quy trình tạo báo cáo..." });
        this.initializeProgressLog();
    }
    
    hideProgressCard() {
        const progressCard = document.getElementById('progress-card');
        progressCard.style.display = 'none';
        this.lastUpdateTime = 0;
        this.processedLogIds.clear();
    }
    
    initializeProgressLog() {
        const progressLogContainer = document.getElementById('progress-log');
        progressLogContainer.innerHTML = '<div class="log-entry log-info"><span class="log-timestamp">[Khởi tạo]</span> 🚀 Bắt đầu quy trình tạo báo cáo (Combined Research + Validation)</div>';
    }
    
    restoreButton() {
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
    }
}
