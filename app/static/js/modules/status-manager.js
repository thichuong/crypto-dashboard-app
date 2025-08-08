// status-manager.js - System Status Management
import { APIClient } from './api-client.js';
import { LogManager } from './log-manager.js';

export class StatusManager {
    constructor() {
        this.refreshInterval = null;
    }
    
    async init() {
        await this.refresh();
        this.startAutoRefresh();
    }
    
    startAutoRefresh() {
        // Auto refresh status every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refresh();
        }, 30000);
    }
    
    async refresh() {
        try {
            const data = await APIClient.getSchedulerStatus();
            this.updateUI(data);
            LogManager.add(`Cập nhật trạng thái: ${data.status}`, 'info');
        } catch (error) {
            LogManager.add(`Lỗi khi tải trạng thái: ${error.message}`, 'error');
        }
    }
    
    updateUI(data) {
        this.updateSchedulerStatus(data);
        this.updateInterval(data);
        this.updateAPIKeyStatus(data);
        this.updateReportStats(data);
    }
    
    updateSchedulerStatus(data) {
        const statusElement = document.getElementById('scheduler-status');
        if (!statusElement) return;
        
        if (data.status === 'active') {
            statusElement.className = 'status-indicator status-active';
            statusElement.innerHTML = '<i class="fas fa-circle mr-2"></i>Đang hoạt động';
        } else {
            statusElement.className = 'status-indicator status-inactive';
            statusElement.innerHTML = '<i class="fas fa-circle mr-2"></i>Không hoạt động';
        }
    }
    
    updateInterval(data) {
        const intervalElement = document.getElementById('interval-info');
        if (intervalElement) {
            intervalElement.textContent = `${data.interval_hours} giờ`;
        }
    }
    
    updateAPIKeyStatus(data) {
        const apiKeyElement = document.getElementById('api-key-status');
        if (apiKeyElement) {
            apiKeyElement.textContent = data.has_api_key ? 'Đã cấu hình' : 'Chưa cấu hình';
            apiKeyElement.style.color = data.has_api_key ? 'var(--positive-color)' : 'var(--negative-color)';
        }
    }
    
    updateReportStats(data) {
        // Update total reports
        const totalReportsElement = document.getElementById('total-reports');
        if (totalReportsElement) {
            totalReportsElement.textContent = data.total_reports || 0;
        }
        
        // Update latest report time
        const latestTimeElement = document.getElementById('latest-report-time');
        if (latestTimeElement) {
            if (data.latest_report_time) {
                const date = new Date(data.latest_report_time);
                latestTimeElement.textContent = date.toLocaleString('vi-VN');
            } else {
                latestTimeElement.textContent = 'Chưa có báo cáo';
            }
        }
    }
}
