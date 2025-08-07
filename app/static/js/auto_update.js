// auto_update.js - Auto Update System JavaScript

// Global variables
let logEntries = [];
let currentSessionId = null;
let pollingInterval = null;

// Polling API for progress tracking
function startPollingAPI() {
    if (!currentSessionId) {
        return;
    }
    
    console.log('[POLLING] Starting polling API for session:', currentSessionId);
    addLogEntry('📡 Bắt đầu theo dõi tiến độ qua API', 'info');
    
    pollingInterval = setInterval(async function() {
        try {
            const response = await fetch(`/api/progress/${currentSessionId}`);
            const data = await response.json();
            
            if (data.success && data.progress) {
                console.log('[POLLING] Received progress update:', data);
                updateProgressFromServer({
                    session_id: data.session_id,
                    progress: data.progress
                });
                
                // Stop polling if completed or error
                if (data.progress.status === 'completed' || data.progress.status === 'error') {
                    stopPollingAPI();
                }
            }
        } catch (error) {
            console.error('[POLLING] Error fetching progress:', error);
            // Continue polling on error
        }
    }, 2000); // Poll every 2 seconds
}

function stopPollingAPI() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('[POLLING] Stopped polling API');
        addLogEntry('⏹️ Dừng theo dõi tiến độ', 'info');
    }
}

// Update progress from server
function updateProgressFromServer(data) {
    console.log('[PROGRESS] Received update for session:', data.session_id, 'current session:', currentSessionId);
    if (data.session_id !== currentSessionId) return;
    
    const progress = data.progress;
    console.log('[PROGRESS] Processing progress update:', progress);
    
    // Update log if details available
    if (progress.details) {
        addLogEntry(progress.details, 'info');
    }
    
    // Handle completion
    if (progress.status === 'completed') {
        console.log('[PROGRESS] Workflow completed!');
        document.getElementById('success-message').textContent = 
            `Báo cáo #${progress.report_id} đã được tạo thành công!`;
        document.getElementById('success-overlay').style.display = 'flex';
        
        // Restore button
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
        
        addLogEntry('🎉 Hoàn thành tạo báo cáo!', 'success');
    } else if (progress.status === 'error') {
        console.log('[PROGRESS] Workflow error:', progress.details);
        document.getElementById('error-message').textContent = 
            progress.details || 'Có lỗi xảy ra trong quá trình tạo báo cáo';
        document.getElementById('error-overlay').style.display = 'flex';
        
        // Restore button
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
        
        addLogEntry('💥 Có lỗi xảy ra!', 'error');
    }
}

// Leave progress room when done
function leaveProgressRoom() {
    if (currentSessionId) {
        stopPollingAPI();
        currentSessionId = null;
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    addLogEntry('🔐 Phiên truy cập an toàn được khởi tạo', 'info');
    addLogEntry('Khởi tạo trang Auto Update System', 'info');
    refreshStatus();
    
    // Auto refresh status every 30 seconds
    setInterval(refreshStatus, 30000);
    
    // Security reminder
    setTimeout(() => {
        addLogEntry('⚠️ Nhắc nhở: Không chia sẻ URL này với người khác', 'info');
    }, 5000);
});

// Add log entry
function addLogEntry(message, type = 'info') {
    const timestamp = new Date().toLocaleString('vi-VN');
    const entry = {
        timestamp: timestamp,
        message: message,
        type: type
    };
    
    logEntries.unshift(entry);
    
    // Keep only last 50 entries
    if (logEntries.length > 50) {
        logEntries = logEntries.slice(0, 50);
    }
    
    updateLogDisplay();
}

// Update log display
function updateLogDisplay() {
    const logContainer = document.getElementById('activity-log');
    logContainer.innerHTML = '';
    
    logEntries.forEach(entry => {
        const logDiv = document.createElement('div');
        logDiv.className = `log-entry log-${entry.type}`;
        logDiv.innerHTML = `<span class="log-timestamp">[${entry.timestamp}]</span> ${entry.message}`;
        logContainer.appendChild(logDiv);
    });
}

// Clear log
function clearLog() {
    logEntries = [];
    updateLogDisplay();
    addLogEntry('Đã xóa nhật ký hoạt động', 'info');
}

// Refresh status
async function refreshStatus() {
    try {
        const response = await fetch('/scheduler-status');
        const data = await response.json();
        
        const statusElement = document.getElementById('scheduler-status');
        const intervalElement = document.getElementById('interval-info');
        const apiKeyElement = document.getElementById('api-key-status');
        
        // Update scheduler status
        if (data.status === 'active') {
            statusElement.className = 'status-indicator status-active';
            statusElement.innerHTML = '<i class="fas fa-circle mr-2"></i>Đang hoạt động';
        } else {
            statusElement.className = 'status-indicator status-inactive';
            statusElement.innerHTML = '<i class="fas fa-circle mr-2"></i>Không hoạt động';
        }
        
        // Update interval
        intervalElement.textContent = `${data.interval_hours} giờ`;
        
        // Update API key status
        apiKeyElement.textContent = data.has_api_key ? 'Đã cấu hình' : 'Chưa cấu hình';
        apiKeyElement.style.color = data.has_api_key ? 'var(--positive-color)' : 'var(--negative-color)';
        
        // Update total reports
        document.getElementById('total-reports').textContent = data.total_reports || 0;
        
        // Update latest report time
        const latestTimeElement = document.getElementById('latest-report-time');
        if (data.latest_report_time) {
            const date = new Date(data.latest_report_time);
            latestTimeElement.textContent = date.toLocaleString('vi-VN');
        } else {
            latestTimeElement.textContent = 'Chưa có báo cáo';
        }
        
        addLogEntry(`Cập nhật trạng thái: ${data.status}`, 'info');
        
    } catch (error) {
        addLogEntry(`Lỗi khi tải trạng thái: ${error.message}`, 'error');
    }
}

// Trigger manual report with simplified UI feedback
async function triggerManualReport() {
    // Confirmation dialog
    if (!confirm('Bạn có chắc chắn muốn tạo báo cáo mới? Quá trình này có thể mất vài phút.')) {
        return;
    }
    
    const btn = document.getElementById('trigger-report-btn');
    const originalContent = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Đang tạo báo cáo...';
    btn.disabled = true;
    
    addLogEntry('🚀 Bắt đầu tạo báo cáo tự động', 'info');
    
    try {
        const response = await fetch('/generate-auto-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Set session ID and start polling for progress updates
            currentSessionId = data.session_id;
            console.log('[WORKFLOW] Started with session ID:', currentSessionId);
            
            addLogEntry(`📡 Đã kết nối progress tracking: ${currentSessionId}`, 'info');
            startPollingAPI();
            
            addLogEntry('✅ Workflow đã được khởi chạy thành công', 'success');
        } else {
            document.getElementById('error-message').textContent = data.message;
            document.getElementById('error-overlay').style.display = 'flex';
            addLogEntry(`❌ Lỗi tạo báo cáo: ${data.message}`, 'error');
            
            // Restore button
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
        
    } catch (error) {
        document.getElementById('error-message').textContent = `Lỗi kết nối: ${error.message}`;
        document.getElementById('error-overlay').style.display = 'flex';
        addLogEntry(`🔌 Lỗi kết nối: ${error.message}`, 'error');
        
        // Restore button
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

// View latest report
function viewLatestReport() {
    addLogEntry('📄 Chuyển đến trang chủ để xem báo cáo mới nhất', 'info');
    window.open('/', '_blank');
}

// Close overlays
function closeSuccessOverlay() {
    document.getElementById('success-overlay').style.display = 'none';
    leaveProgressRoom(); // Clean up session
    refreshStatus(); // Refresh to show new report count
}

function closeErrorOverlay() {
    document.getElementById('error-overlay').style.display = 'none';
    leaveProgressRoom(); // Clean up session
}
