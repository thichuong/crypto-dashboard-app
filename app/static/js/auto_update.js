// auto_update.js - Simplified Progress Tracking

// Global variables
let logEntries = [];
let currentSessionId = null;
let pollingInterval = null;

// Progress tracking variables
let lastUpdateTime = 0;
let processedSubstepIds = new Set(); // Track processed substeps

// Polling API for progress tracking
function startPollingAPI() {
    if (!currentSessionId) {
        return;
    }
    
    console.log('[POLLING] Starting for session:', currentSessionId);
    addLogEntry('📡 Bắt đầu theo dõi tiến độ', 'info');
    
    pollingInterval = setInterval(async function() {
        try {
            const response = await fetch(`/api/progress/${currentSessionId}`);
            const data = await response.json();
            
            if (data.success && data.progress) {
                updateProgressFromServer(data.progress);
                
                // Stop polling if completed or error
                if (data.progress.status === 'completed' || data.progress.status === 'error') {
                    stopPollingAPI();
                }
            }
        } catch (error) {
            console.error('[POLLING] Error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function stopPollingAPI() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('[POLLING] Stopped');
        addLogEntry('⏹️ Dừng theo dõi tiến độ', 'info');
    }
}

// Show progress card
function showProgressCard(sessionId) {
    const progressCard = document.getElementById('progress-card');
    const sessionIdElement = document.getElementById('progress-session-id');
    
    // Show the card
    progressCard.style.display = 'block';
    sessionIdElement.textContent = `Session: ${sessionId.substring(0, 8)}...`;
    
    // Reset state
    lastUpdateTime = 0;
    processedSubstepIds.clear(); // Reset processed substeps
    
    // Initialize progress display
    updateProgressBar(0, "Đang khởi tạo...");
    updateProgressDetails("Chuẩn bị bắt đầu quy trình tạo báo cáo...");
    initializeProgressLog();
}

// Hide progress card
function hideProgressCard() {
    const progressCard = document.getElementById('progress-card');
    progressCard.style.display = 'none';
    lastUpdateTime = 0;
    processedSubstepIds.clear(); // Reset processed substeps
}

// Initialize progress log
function initializeProgressLog() {
    const progressLogContainer = document.getElementById('progress-log');
    progressLogContainer.innerHTML = '<div class="log-entry log-info"><span class="log-timestamp">[Khởi tạo]</span> 🚀 Bắt đầu quy trình tạo báo cáo (Combined Research + Validation)</div>';
}

// Update progress bar
function updateProgressBar(percentage, stepName) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressStepName = document.getElementById('progress-step-name');
    
    progressBar.style.width = `${percentage}%`;
    progressPercentage.textContent = `${percentage}%`;
    progressStepName.textContent = stepName;
}

// Update progress details
function updateProgressDetails(details) {
    const progressDetailsText = document.getElementById('progress-details-text');
    progressDetailsText.textContent = details;
}

// Update progress from server - simplified version with substep queue
function updateProgressFromServer(progress) {
    console.log('[PROGRESS] Update:', progress);
    
    // Only update if there's actual change (based on last_update timestamp)
    const currentUpdateTime = progress.last_update || 0;
    if (currentUpdateTime <= lastUpdateTime) {
        return; // No new updates
    }
    lastUpdateTime = currentUpdateTime;
    
    // Update progress bar - remove timestamp from step name for UI
    const cleanStepName = (progress.current_step_name || "").replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
    updateProgressBar(progress.percentage || 0, cleanStepName);
    
    // Update details - remove timestamp from details for UI
    const cleanDetails = (progress.details || "").replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
    if (cleanDetails) {
        updateProgressDetails(cleanDetails);
    }
    
    // Add log entry for major updates only
    const progressLogContainer = document.getElementById('progress-log');
    
    // Show step name as main log entry (with original timestamp)
    if (progress.current_step_name) {
        const stepLogDiv = document.createElement('div');
        stepLogDiv.className = 'log-entry log-info';
        
        // Enhanced step name formatting for combined workflow
        let stepDisplayName = progress.current_step_name;
        if (stepDisplayName.includes("Research + Validation")) {
            stepDisplayName = stepDisplayName.replace("Research + Validation", "🔬 Research + Validation");
        } else if (stepDisplayName.includes("Parse validation")) {
            stepDisplayName = stepDisplayName.replace("Parse validation", "✅ Parse Validation");
        } else if (stepDisplayName.includes("Chuẩn bị dữ liệu")) {
            stepDisplayName = stepDisplayName.replace("Chuẩn bị dữ liệu", "📋 Chuẩn bị dữ liệu");
        } else if (stepDisplayName.includes("Tạo giao diện")) {
            stepDisplayName = stepDisplayName.replace("Tạo giao diện", "🎨 Tạo giao diện");
        } else if (stepDisplayName.includes("Trích xuất mã nguồn")) {
            stepDisplayName = stepDisplayName.replace("Trích xuất mã nguồn", "📄 Trích xuất mã nguồn");
        } else if (stepDisplayName.includes("Lưu báo cáo")) {
            stepDisplayName = stepDisplayName.replace("Lưu báo cáo", "💾 Lưu báo cáo");
        }
        
        stepLogDiv.innerHTML = `<span class="log-timestamp">${stepDisplayName}</span>`;
        progressLogContainer.appendChild(stepLogDiv);
    }
    
    // Process substep queue - hiển thị tất cả substeps với enhanced formatting
    const substepQueue = progress.substep_queue || [];
    substepQueue.forEach(substepEntry => {
        const substepId = `${currentSessionId}_${substepEntry.step}_${substepEntry.timestamp}_${substepEntry.details}`;
        
        // Only process new substeps that haven't been shown yet
        if (!processedSubstepIds.has(substepId)) {
            let cleanSubstepDetails = substepEntry.details.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
            
            // Enhanced substep message formatting for combined workflow
            if (cleanSubstepDetails.includes("inject real-time data")) {
                cleanSubstepDetails = cleanSubstepDetails.replace("inject real-time data", "📊 inject real-time data");
            } else if (cleanSubstepDetails.includes("Combined Research + Validation")) {
                cleanSubstepDetails = cleanSubstepDetails.replace("Combined Research + Validation", "🔬 Combined Research + Validation");
            } else if (cleanSubstepDetails.includes("Combined response")) {
                cleanSubstepDetails = cleanSubstepDetails.replace("Combined response", "📝 Combined response");
            } else if (cleanSubstepDetails.includes("Parse validation")) {
                cleanSubstepDetails = cleanSubstepDetails.replace("Parse validation", "✅ Parse validation");
            } else if (cleanSubstepDetails.includes("Parsed validation result")) {
                cleanSubstepDetails = cleanSubstepDetails.replace("Parsed validation result", "✅ Parsed validation result");
            }
            
            let logType = 'log-step-complete';
            if (cleanSubstepDetails.includes('✓') || cleanSubstepDetails.includes('Hoàn thành') || cleanSubstepDetails.includes('thành công') || cleanSubstepDetails.includes('PASS')) {
                logType = 'log-success';
            } else if (cleanSubstepDetails.includes('✗') || cleanSubstepDetails.includes('Lỗi') || cleanSubstepDetails.includes('thất bại') || cleanSubstepDetails.includes('FAIL')) {
                logType = 'log-error';
            } else if (cleanSubstepDetails.includes('⚠️') || cleanSubstepDetails.includes('UNKNOWN')) {
                logType = 'log-info';
            } else if (cleanSubstepDetails.includes('🔬') || cleanSubstepDetails.includes('📊') || cleanSubstepDetails.includes('📝')) {
                logType = 'log-info';
            }
            
            const substepLogDiv = document.createElement('div');
            substepLogDiv.className = `log-entry ${logType}`;
            substepLogDiv.innerHTML = `<span class="log-timestamp">📋 ${cleanSubstepDetails}</span>`;
            progressLogContainer.appendChild(substepLogDiv);
            
            // Mark this substep as processed
            processedSubstepIds.add(substepId);
        }
    });
    
    // Keep only last 20 log entries (increased for combined workflow)
    while (progressLogContainer.children.length > 20) {
        progressLogContainer.removeChild(progressLogContainer.firstChild);
    }
    
    // Handle completion
    if (progress.status === 'completed') {
        console.log('[PROGRESS] Combined workflow completed!');
        
        updateProgressBar(100, 'Hoàn thành!');
        updateProgressDetails(`Báo cáo #${progress.report_id} đã được tạo thành công với Combined Research + Validation!`);
        
        // Add success log entry
        const successLogDiv = document.createElement('div');
        successLogDiv.className = 'log-entry log-success';
        successLogDiv.innerHTML = `<i class="fas fa-check-circle text-green-500 mr-2"></i><span class="log-timestamp">🎉 Hoàn thành tạo báo cáo #${progress.report_id} (Combined Workflow)</span>`;
        progressLogContainer.appendChild(successLogDiv);
        
        document.getElementById('success-message').textContent = 
            `Báo cáo #${progress.report_id} đã được tạo thành công với Combined Research + Validation!`;
        document.getElementById('success-overlay').style.display = 'flex';
        
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
        
        addLogEntry('🎉 Hoàn thành tạo báo cáo với Combined Workflow!', 'success');
    } else if (progress.status === 'error') {
        console.log('[PROGRESS] Combined workflow error:', progress.details);
        
        updateProgressBar(progress.percentage || 0, 'Lỗi xảy ra');
        updateProgressDetails(progress.details || 'Có lỗi xảy ra trong quá trình Combined Research + Validation');
        
        // Add error log entry
        const errorLogDiv = document.createElement('div');
        errorLogDiv.className = 'log-entry log-error';
        errorLogDiv.innerHTML = `<i class="fas fa-times text-red-500 mr-2"></i><span class="log-timestamp">💥 Lỗi Combined Workflow: ${progress.details || 'Có lỗi xảy ra'}</span>`;
        progressLogContainer.appendChild(errorLogDiv);
        
        document.getElementById('error-message').textContent = 
            progress.details || 'Có lỗi xảy ra trong quá trình Combined Research + Validation';
        document.getElementById('error-overlay').style.display = 'flex';
        
        // Restore button
        const btn = document.getElementById('trigger-report-btn');
        btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
        btn.disabled = false;
        
        addLogEntry('💥 Có lỗi xảy ra trong Combined Workflow!', 'error');
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    addLogEntry('🔐 Phiên truy cập an toàn được khởi tạo', 'info');
    addLogEntry('🚀 Khởi tạo Auto Update System với Combined Research + Validation', 'info');
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
    
    // Insert entries from newest to oldest (like progress log)
    logEntries.forEach(entry => {
        const logDiv = document.createElement('div');
        logDiv.className = `log-entry log-${entry.type}`;
        logDiv.innerHTML = `<span class="log-timestamp">[${entry.timestamp}]</span> ${entry.message}`;
        // Insert at the beginning to show newest entries at top
        logContainer.insertBefore(logDiv, logContainer.firstChild);
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
    if (!confirm('Bạn có chắc chắn muốn tạo báo cáo mới với Combined Research + Validation? Quá trình này có thể mất vài phút.')) {
        return;
    }
    
    const btn = document.getElementById('trigger-report-btn');
    const originalContent = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Đang tạo báo cáo (Combined)...';
    btn.disabled = true;
    
    addLogEntry('🚀 Bắt đầu tạo báo cáo với Combined Research + Validation', 'info');
    
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
            console.log('[COMBINED WORKFLOW] Started with session ID:', currentSessionId);
            
            addLogEntry(`📡 Đã kết nối Combined Workflow tracking: ${currentSessionId}`, 'info');
            
            // Show progress card (this will reset all steps for new report)
            showProgressCard(currentSessionId);
            
            startPollingAPI();
            
            addLogEntry('✅ Combined Research + Validation Workflow đã được khởi chạy', 'success');
        } else {
            document.getElementById('error-message').textContent = data.message;
            document.getElementById('error-overlay').style.display = 'flex';
            addLogEntry(`❌ Lỗi Combined Workflow: ${data.message}`, 'error');
            
            // Restore button
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
        
    } catch (error) {
        document.getElementById('error-message').textContent = `Lỗi kết nối Combined Workflow: ${error.message}`;
        document.getElementById('error-overlay').style.display = 'flex';
        addLogEntry(`🔌 Lỗi kết nối Combined Workflow: ${error.message}`, 'error');
        
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
    // Clean up session but keep progress card visible
    if (currentSessionId) {
        stopPollingAPI();
        currentSessionId = null;
    }
    refreshStatus(); // Refresh to show new report count
}

function closeErrorOverlay() {
    document.getElementById('error-overlay').style.display = 'none';
    // Clean up session but keep progress card visible
    if (currentSessionId) {
        stopPollingAPI();
        currentSessionId = null;
    }
}

// Cancel progress
function cancelProgress() {
    if (currentSessionId) {
        if (confirm('Bạn có chắc chắn muốn dừng quá trình Combined Research + Validation?')) {
            addLogEntry('🛑 Người dùng đã dừng Combined Workflow', 'info');
            
            // Clean up session and hide progress card when manually cancelled
            stopPollingAPI();
            currentSessionId = null;
            hideProgressCard();
            
            // Restore button
            const btn = document.getElementById('trigger-report-btn');
            btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
            btn.disabled = false;
        }
    }
}
