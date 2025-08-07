// auto_update.js - Auto Update System JavaScript

// Global variables
let logEntries = [];
let currentSessionId = null;
let pollingInterval = null;
let progressStartTime = null;
let stepStartTimes = {};
let stepAccumulatedTimes = {}; // Track accumulated time for each step
let stepAttemptCounts = {}; // Track number of attempts for each step
let currentRunningStep = null;
let timeUpdateInterval = null;
let lastPollingTime = null;

// Step names mapping
const stepNames = {
    1: "Chuẩn bị dữ liệu và khởi tạo AI",
    2: "Thu thập dữ liệu từ internet", 
    3: "Xác thực dữ liệu với hệ thống thời gian thực",
    4: "Tạo giao diện báo cáo",
    5: "Trích xuất mã nguồn",
    6: "Lưu báo cáo vào database",
    7: "Hoàn thành"
};

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
        
        // Do NOT hide progress card here - keep it visible to show final results
        // hideProgressCard(); // Removed this line
    }
}

// Show progress card
function showProgressCard(sessionId) {
    const progressCard = document.getElementById('progress-card');
    const sessionIdElement = document.getElementById('progress-session-id');
    
    // Show the card
    progressCard.style.display = 'block';
    sessionIdElement.textContent = `Session: ${sessionId.substring(0, 8)}...`;
    
    // ONLY reset steps when starting a NEW report (not when just showing the card)
    resetProgressSteps();
    
    // Initialize progress bar
    updateProgressBar(0, "Đang khởi tạo...");
    updateProgressDetails("Chuẩn bị bắt đầu quy trình tạo báo cáo...");
    
    // Record start time for overall progress
    progressStartTime = Date.now();
    lastPollingTime = Date.now();
    
    // Start timing for first step immediately and mark it as running
    stepStartTimes[1] = Date.now();
    stepAccumulatedTimes[1] = 0;
    currentRunningStep = 1;
    updateStepStatus(1, 'running');
    startTimeUpdateInterval();
}

// Hide progress card
function hideProgressCard() {
    const progressCard = document.getElementById('progress-card');
    progressCard.style.display = 'none';
    
    // Reset variables
    progressStartTime = null;
    stepStartTimes = {};
    stepAccumulatedTimes = {};
    stepAttemptCounts = {};
    currentRunningStep = null;
    lastPollingTime = null;
    
    // Stop time update interval
    stopTimeUpdateInterval();
}

// Reset all progress steps
function resetProgressSteps() {
    for (let i = 1; i <= 7; i++) {
        updateStepStatus(i, 'pending');
        updateStepTime(i, '--:--');
    }
    // Reset current running step but don't stop timer here
    // Timer will be managed by showProgressCard
    currentRunningStep = null;
    stepAccumulatedTimes = {};
    stepAttemptCounts = {};
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

// Update step status
function updateStepStatus(stepNumber, status) {
    const rows = document.querySelectorAll('#progress-steps-table tr');
    if (rows[stepNumber - 1]) {
        const statusElement = rows[stepNumber - 1].querySelector('.step-status');
        statusElement.className = `step-status ${status}`;
        
        let icon = '';
        switch (status) {
            case 'pending':
                icon = '<i class="fas fa-clock text-gray-400"></i>';
                break;
            case 'running':
                icon = '<i class="fas fa-spinner fa-spin text-blue-500"></i>';
                break;
            case 'completed':
                icon = '<i class="fas fa-check text-green-500"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-times text-red-500"></i>';
                break;
        }
        statusElement.innerHTML = icon;
        
        // Handle step timing
        if (status === 'running') {
            // Set current running step and initialize accumulated time
            currentRunningStep = stepNumber;
            
            // Initialize accumulated time if not exists
            if (typeof stepAccumulatedTimes[stepNumber] === 'undefined') {
                stepAccumulatedTimes[stepNumber] = 0;
                stepAttemptCounts[stepNumber] = 1;
            } else {
                // Step is being retried, increment attempt count
                stepAttemptCounts[stepNumber] = (stepAttemptCounts[stepNumber] || 1) + 1;
                console.log(`[RETRY] Step ${stepNumber} attempt #${stepAttemptCounts[stepNumber]}`);
                addLogEntry(`🔄 Thử lại bước ${stepNumber} (lần ${stepAttemptCounts[stepNumber]})`, 'info');
            }
            
            // Start real-time timer for this step
            startTimeUpdateInterval();
        } else if (status === 'completed') {
            // For completed steps, finalize their time with attempt count
            if (typeof stepAccumulatedTimes[stepNumber] !== 'undefined') {
                // Use accumulated time with attempt count
                const timeString = formatTimeWithAttempts(stepNumber, stepAccumulatedTimes[stepNumber]);
                updateStepTime(stepNumber, timeString);
            } else {
                // If no accumulated time (completed too fast), use minimum 1 second
                stepAccumulatedTimes[stepNumber] = 1;
                stepAttemptCounts[stepNumber] = 1;
                const timeString = formatTimeWithAttempts(stepNumber, 1);
                updateStepTime(stepNumber, timeString);
            }
            
            // Clear running step if this was the running step
            if (currentRunningStep === stepNumber) {
                currentRunningStep = null;
            }
        } else if (status === 'error') {
            // Clear running step on error and finalize time
            if (currentRunningStep === stepNumber) {
                currentRunningStep = null;
            }
            // Finalize time for error step with attempt count
            if (typeof stepAccumulatedTimes[stepNumber] !== 'undefined') {
                const timeString = formatTimeWithAttempts(stepNumber, stepAccumulatedTimes[stepNumber]);
                updateStepTime(stepNumber, timeString);
            }
        }
    }
}

// Update step time
function updateStepTime(stepNumber, timeString) {
    const rows = document.querySelectorAll('#progress-steps-table tr');
    if (rows[stepNumber - 1]) {
        const timeElement = rows[stepNumber - 1].querySelector('td:last-child');
        timeElement.textContent = timeString;
    }
}

// Update running step time in real-time
function updateRunningStepTime() {
    // Only update if we have a current running step AND it has accumulated time tracking
    if (currentRunningStep && typeof stepAccumulatedTimes[currentRunningStep] !== 'undefined') {
        // Add 1 second to accumulated time
        stepAccumulatedTimes[currentRunningStep] += 1;
        
        const timeString = formatTimeWithAttempts(currentRunningStep, stepAccumulatedTimes[currentRunningStep]);
        updateStepTime(currentRunningStep, timeString);
    } else {
        // If no running step, stop the timer
        stopTimeUpdateInterval();
    }
}

// Format accumulated time to display string
function formatAccumulatedTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Format time with attempt count
function formatTimeWithAttempts(stepNumber, totalSeconds) {
    const timeString = formatAccumulatedTime(totalSeconds);
    const attempts = stepAttemptCounts[stepNumber] || 1;
    
    if (attempts > 1) {
        return `${timeString} (x${attempts})`;
    }
    return timeString;
}

// Update accumulated time for running step based on polling interval
function updateAccumulatedTimeFromPolling() {
    const currentTime = Date.now();
    const pollingInterval = 2; // 2 seconds between polls
    
    if (currentRunningStep && typeof stepAccumulatedTimes[currentRunningStep] !== 'undefined') {
        // Add polling interval to accumulated time
        stepAccumulatedTimes[currentRunningStep] += pollingInterval;
        
        const timeString = formatTimeWithAttempts(currentRunningStep, stepAccumulatedTimes[currentRunningStep]);
        updateStepTime(currentRunningStep, timeString);
    }
    
    lastPollingTime = currentTime;
}

// Start time update interval
function startTimeUpdateInterval() {
    if (timeUpdateInterval) {
        clearInterval(timeUpdateInterval);
    }
    timeUpdateInterval = setInterval(updateRunningStepTime, 1000); // Update every second
}

// Stop time update interval
function stopTimeUpdateInterval() {
    if (timeUpdateInterval) {
        clearInterval(timeUpdateInterval);
        timeUpdateInterval = null;
    }
}

// Update progress from server
function updateProgressFromServer(data) {
    console.log('[PROGRESS] Received update for session:', data.session_id, 'current session:', currentSessionId);
    if (data.session_id !== currentSessionId) return;
    
    const progress = data.progress;
    console.log('[PROGRESS] Processing progress update:', progress);
    
    // Update progress bar
    const stepName = stepNames[progress.step] || progress.current_step_name;
    updateProgressBar(progress.percentage, stepName);
    
    // Update progress details
    if (progress.details) {
        updateProgressDetails(progress.details);
        addLogEntry(progress.details, 'info');
    }
    
    // Update step statuses
    if (progress.step > 0) {
        // Update accumulated time for currently running step from polling
        updateAccumulatedTimeFromPolling();
        
        // Handle step backward movement (retry scenario)
        if (currentRunningStep && progress.step < currentRunningStep) {
            console.log(`[STEP_BACKWARD] Moving from step ${currentRunningStep} back to step ${progress.step}`);
            addLogEntry(`↩️ Quay lại bước ${progress.step} từ bước ${currentRunningStep}`, 'info');
            
            // Mark steps after current step as pending again
            for (let i = progress.step + 1; i <= 7; i++) {
                if (typeof stepAccumulatedTimes[i] !== 'undefined') {
                    // Keep accumulated time but reset status to pending
                    const timeString = formatTimeWithAttempts(i, stepAccumulatedTimes[i]);
                    updateStepTime(i, timeString);
                }
                updateStepStatus(i, 'pending');
            }
        }
        
        // Mark previous steps as completed and ensure they have timing
        for (let i = 1; i < progress.step; i++) {
            // If step doesn't have accumulated time, give it minimum 1 second (for fast-completed steps)
            if (typeof stepAccumulatedTimes[i] === 'undefined') {
                stepAccumulatedTimes[i] = 1; // Minimum time for fast-completed steps
                stepAttemptCounts[i] = 1;
            }
            
            const timeString = formatTimeWithAttempts(i, stepAccumulatedTimes[i]);
            updateStepTime(i, timeString);
            updateStepStatus(i, 'completed');
        }
        
        // Mark current step as running (if not completed/error)
        if (progress.status === 'running') {
            // Initialize accumulated time for new running step if not exists
            if (typeof stepAccumulatedTimes[progress.step] === 'undefined') {
                stepAccumulatedTimes[progress.step] = 0;
                stepAttemptCounts[progress.step] = 1;
            }
            updateStepStatus(progress.step, 'running');
        }
    }
    
    // Handle completion
    if (progress.status === 'completed') {
        console.log('[PROGRESS] Workflow completed!');
        
        // Stop time update interval
        stopTimeUpdateInterval();
        
        // Mark all steps as completed
        for (let i = 1; i <= 7; i++) {
            updateStepStatus(i, 'completed');
        }
        
        updateProgressBar(100, 'Hoàn thành!');
        updateProgressDetails(`Báo cáo #${progress.report_id} đã được tạo thành công!`);
        
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
        
        // Stop time update interval
        stopTimeUpdateInterval();
        
        // Mark current step as error
        if (progress.step > 0) {
            updateStepStatus(progress.step, 'error');
        }
        
        updateProgressBar(progress.percentage, 'Lỗi xảy ra');
        updateProgressDetails(progress.details || 'Có lỗi xảy ra trong quá trình tạo báo cáo');
        
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
            
            // Show progress card (this will reset all steps for new report)
            showProgressCard(currentSessionId);
            
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
        if (confirm('Bạn có chắc chắn muốn dừng quá trình tạo báo cáo?')) {
            addLogEntry('🛑 Người dùng đã dừng quá trình tạo báo cáo', 'info');
            
            // Clean up session and hide progress card when manually cancelled
            leaveProgressRoom();
            hideProgressCard();
            
            // Restore button
            const btn = document.getElementById('trigger-report-btn');
            btn.innerHTML = '<i class="fas fa-play mr-2"></i>Tạo Báo Cáo Ngay';
            btn.disabled = false;
        }
    }
}
