// progress-tracker.js - WebSocket-based Progress Tracking
import { APIClient } from './api-client.js';
import { LogManager } from './log-manager.js';
import { wsClient } from './websocket-client.js';

export class ProgressTracker {
    constructor() {
        this.sessionId = null;
        this.processedLogIds = new Set();
        this.lastUpdateTime = 0;
        this.wsUnsubscribeFunc = null;
        this.pollingInterval = null;
        this.useWebSocket = true;
    }
    
    startTracking(sessionId) {
        this.sessionId = sessionId;
        this.showProgressCard();
        
        if (this.useWebSocket && wsClient.isConnected) {
            this.startWebSocketTracking();
            LogManager.add('📡 Bắt đầu theo dõi tiến độ qua WebSocket', 'info');
        } else {
            this.startPollingFallback();
            LogManager.add('📡 Bắt đầu theo dõi tiến độ qua Polling (fallback)', 'info');
        }
    }
    
    stopTracking() {
        // Stop WebSocket tracking
        if (this.wsUnsubscribeFunc) {
            this.wsUnsubscribeFunc();
            this.wsUnsubscribeFunc = null;
            LogManager.add('⏹️ Dừng theo dõi tiến độ WebSocket', 'info');
        }
        
        // Stop polling fallback
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            LogManager.add('⏹️ Dừng theo dõi tiến độ Polling', 'info');
        }
        
        // Unsubscribe from WebSocket channel
        if (this.sessionId) {
            wsClient.unsubscribe(`progress_${this.sessionId}`);
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

    async startWebSocketTracking() {
        try {
            // Ensure WebSocket is connected
            if (!wsClient.isConnected) {
                await wsClient.connect();
            }
            
            // Subscribe to progress updates for this session
            wsClient.subscribe(`progress_${this.sessionId}`);
            
            // Register message handler for progress updates
            this.wsUnsubscribeFunc = wsClient.onMessage('progress_update', (data) => {
                if (data.session_id === this.sessionId) {
                    this.processUpdate(data.data);
                }
            });
            
            // Also get initial progress state via API as fallback
            const progress = await APIClient.getProgress(this.sessionId);
            if (progress) {
                this.processUpdate(progress);
            }
        } catch (error) {
            console.warn('[ProgressTracker] WebSocket tracking failed, falling back to polling:', error);
            LogManager.add('⚠️ WebSocket thất bại, chuyển sang polling', 'warning');
            this.startPollingFallback();
        }
    }
    
    startPollingFallback() {
        this.useWebSocket = false;
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
            this.stopTracking(); // Stop WebSocket tracking
        } else if (progress.status === 'error') {
            this.handleError(progress);
            this.stopTracking(); // Stop WebSocket tracking
        }
    }
    
    updateProgressBar(progress) {
        // Hiển thị đúng tên bước theo workflow mới
        let cleanStepName = (progress.current_step_name || "").replace(/^[\d\[\]: ]*/, '');
        // Nếu là bước mới, dùng formatStepName để chuyển đổi
        cleanStepName = this.formatStepName(cleanStepName);
        const percentage = progress.percentage || 0;

        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressStepName = document.getElementById('progress-step-name');

        // Đổi màu progress bar theo từng bước (ví dụ: màu khác cho HTML, JS, CSS)
        if (progress.current_step_name && progress.current_step_name.includes('html')) {
            progressBar.style.backgroundColor = '#4F46E5'; // Indigo cho HTML
        } else if (progress.current_step_name && progress.current_step_name.includes('javascript')) {
            progressBar.style.backgroundColor = '#F59E42'; // Orange cho JS
        } else if (progress.current_step_name && progress.current_step_name.includes('css')) {
            progressBar.style.backgroundColor = '#10B981'; // Green cho CSS
        } else {
            progressBar.style.backgroundColor = '#2563EB'; // Blue mặc định
        }

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
        
        // Check if user was scrolled to bottom before adding new entries
        const wasScrolledToBottom = this.isScrolledToBottom(progressLogContainer);
        let newEntriesAdded = false;
        
        stepQueue.forEach(logEntry => {
            const logId = `${this.sessionId}_${logEntry.type}_${logEntry.timestamp}_${logEntry.details}`;
            
            if (!this.processedLogIds.has(logId)) {
                const logDiv = this.createLogElement(logEntry);
                if (logDiv) {
                    progressLogContainer.appendChild(logDiv);
                    this.processedLogIds.add(logId);
                    newEntriesAdded = true;
                }
            }
        });
        
        // Keep only last 20 log entries
        while (progressLogContainer.children.length > 20) {
            progressLogContainer.removeChild(progressLogContainer.firstChild);
        }
        
        // Auto-scroll to bottom if user was at bottom and new entries were added
        if (newEntriesAdded && wasScrolledToBottom) {
            this.scrollToBottom(progressLogContainer);
        } else if (newEntriesAdded && !wasScrolledToBottom) {
            // Show indicator if user is not at bottom and there are new entries
            this.showProgressLogIndicator();
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
        // Workflow v2 step mappings
        const stepMappings = {
            "prepare_data": "📋 Chuẩn bị dữ liệu",
            "research_deep": "🔬 Nghiên cứu sâu",
            "validate_report": "✅ Kiểm tra kết quả",
            "generate_report_content": "📝 Tạo nội dung báo cáo",
            "create_html": "🎨 Tạo HTML giao diện",
            "create_javascript": "💻 Tạo JavaScript giao diện",
            "create_css": "🎨 Tạo CSS giao diện",
            "save_database": "💾 Lưu báo cáo"
        };
        // Legacy mappings giữ nguyên
        const legacyMappings = {
            "Research + Validation": "🔬 Nghiên cứu sâu + Validation",
            "Parse validation": "✅ Kiểm tra kết quả",
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
        for (const [key, value] of Object.entries(legacyMappings)) {
            if (details.includes(key)) {
                details = details.replace(key, value);
            }
        }
        return details;
    }

    formatDetailMessage(details) {
        // Workflow v2 detail mappings
        const detailMappings = {
            "inject real-time data": "📊 Đã inject real-time data",
            "Combined Research + Validation": "🔬 Combined Research + Validation",
            "Combined response": "📝 Phản hồi Combined",
            "Parse validation": "✅ Kiểm tra kết quả",
            "Parsed validation result": "✅ Đã parse kết quả validation",
            "PASS": "✅ PASS",
            "FAIL": "❌ FAIL",
            "UNKNOWN": "⚠️ UNKNOWN",
            "Chuẩn bị dữ liệu": "📋 Chuẩn bị dữ liệu",
            "Nghiên cứu sâu": "🔬 Nghiên cứu sâu",
            "Tạo giao diện": "🎨 Tạo giao diện",
            "Trích xuất mã nguồn": "📄 Trích xuất mã nguồn",
            "Lưu báo cáo": "💾 Lưu báo cáo",
            // Thêm các bước mới
            "Tạo nội dung báo cáo": "📝 Tạo nội dung báo cáo",
            "Tạo HTML giao diện": "🎨 Tạo HTML giao diện",
            "Tạo JavaScript giao diện": "💻 Tạo JavaScript giao diện",
            "Tạo CSS giao diện": "🎨 Tạo CSS giao diện",
            "retry_html": "🔄 Đang thử lại HTML",
            "retry_js": "🔄 Đang thử lại JavaScript",
            "retry_css": "🔄 Đang thử lại CSS"
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
        
        // Auto-scroll to show completion message
        this.scrollToBottom(progressLogContainer);
        
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
        
        // Auto-scroll to show error message
        this.scrollToBottom(progressLogContainer);
        
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
        
        // Setup scroll listener for progress log
        this.setupProgressLogScrollListener();
    }
    
    hideProgressCard() {
        const progressCard = document.getElementById('progress-card');
        progressCard.style.display = 'none';
        this.lastUpdateTime = 0;
        this.processedLogIds.clear();
        
        // Hide progress log indicator
        this.hideProgressLogIndicator();
    }
    
    initializeProgressLog() {
        const progressLogContainer = document.getElementById('progress-log');
        progressLogContainer.innerHTML = '<div class="log-entry log-info"><span class="log-timestamp">[Khởi tạo]</span> 🚀 Bắt đầu quy trình tạo báo cáo (Combined Research + Validation)</div>';
        
        // Auto-scroll to bottom for initial log
        this.scrollToBottom(progressLogContainer);
    }
    
    restoreButton() {
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
    }
    
    // Scroll helper methods for progress log
    isScrolledToBottom(container) {
        // Check if user is scrolled to bottom (within 5px tolerance)
        const threshold = 5;
        return container.scrollTop >= (container.scrollHeight - container.clientHeight - threshold);
    }
    
    scrollToBottom(container) {
        // Smooth scroll to bottom with slight delay to ensure content is rendered
        setTimeout(() => {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
        }, 150); // Slightly longer delay for progress updates
    }
    
    // Progress log indicator methods
    showProgressLogIndicator() {
        const progressLogContainer = document.getElementById('progress-log');
        if (!progressLogContainer || this.isScrolledToBottom(progressLogContainer)) {
            return;
        }
        
        // Create or show progress log indicator
        let indicator = document.getElementById('progress-log-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'progress-log-indicator';
            indicator.className = 'new-log-indicator';
            indicator.innerHTML = '<i class="fas fa-arrow-down mr-1"></i>Tiến độ mới';
            indicator.onclick = () => this.scrollToBottomAndHideProgressIndicator();
            
            const progressLogSection = progressLogContainer.closest('.mt-4');
            if (progressLogSection) {
                progressLogSection.style.position = 'relative';
                progressLogSection.appendChild(indicator);
            }
        }
        
        indicator.style.display = 'flex';
    }
    
    hideProgressLogIndicator() {
        const indicator = document.getElementById('progress-log-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    scrollToBottomAndHideProgressIndicator() {
        const progressLogContainer = document.getElementById('progress-log');
        if (progressLogContainer) {
            this.scrollToBottom(progressLogContainer);
            this.hideProgressLogIndicator();
        }
    }
    
    setupProgressLogScrollListener() {
        // Setup scroll listener to hide indicator when user scrolls to bottom
        setTimeout(() => {
            const progressLogContainer = document.getElementById('progress-log');
            if (progressLogContainer) {
                progressLogContainer.addEventListener('scroll', () => {
                    if (this.isScrolledToBottom(progressLogContainer)) {
                        this.hideProgressLogIndicator();
                    }
                });
            }
        }, 500); // Wait for progress card to be fully shown
    }
}
