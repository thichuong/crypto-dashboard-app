// static/main.js

/**
 * Định dạng số lớn thành dạng ngắn gọn (nghìn tỷ, tỷ, triệu).
 * @param {number} num - Số cần định dạng.
 * @returns {string} - Chuỗi đã được định dạng.
 */
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + ' nghìn tỷ';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + ' tỷ';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + ' triệu';
    return num.toLocaleString('en-US');
}

/**
 * Hiển thị thông báo lỗi thân thiện trên một card cụ thể.
 * @param {string} containerId - ID của container cần hiển thị lỗi.
 * @param {string} message - Thông báo lỗi.
 */
function displayError(containerId, message = 'Không thể tải dữ liệu.') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<p class="text-sm text-red-600">${message}</p>`;
    }
}

/**
 * Fetch dữ liệu tổng quan thị trường (vốn hóa, khối lượng).
 */
async function fetchCryptoData() {
    try {
        const response = await fetch('/api/crypto/global');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Lỗi server ${response.status}`);
        }
        const data = await response.json();
        
        const marketCapContainer = document.getElementById('market-cap-container');
        marketCapContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data.market_cap)}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

        const volumeContainer = document.getElementById('volume-24h-container');
        volumeContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data.volume_24h)}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

    } catch (error) {
        console.error('Lỗi fetchCryptoData:', error);
        displayError('market-cap-container', error.message);
        displayError('volume-24h-container', error.message);
    }
}

/**
 * Fetch giá Bitcoin và chỉ số Sợ hãi & Tham lam.
 */
async function fetchBtcAndFearGreed() {
    const btcContainer = document.getElementById('btc-price-container');
    const fngContainer = document.getElementById('fear-greed-container');

    try {
        const response = await fetch('/api/crypto/btc-and-fng');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Lỗi server ${response.status}`);
        }
        const data = await response.json();

        // Cập nhật giá BTC
        const change = data.btc_change_24h;
        const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
        btcContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + (data.btc_price_usd ? data.btc_price_usd.toLocaleString('en-US') : 'N/A')}</p>
            <p class="text-sm font-semibold ${changeClass}">${change !== null ? change.toFixed(2) : 'N/A'}% (24h)</p>
        `;

        // Cập nhật chỉ số Sợ hãi & Tham lam bằng đồng hồ đo
        const fngValue = parseInt(data.fng_value, 10);
        if (!isNaN(fngValue)) {
            createFngGauge_index(fngContainer, fngValue, data.fng_classification);
        } else {
            throw new Error('Giá trị F&G không hợp lệ.');
        }

    } catch (error) {
        console.error('Lỗi fetchBtcAndFearGreed:', error);
        displayError('btc-price-container', error.message);
        displayError('fear-greed-container', error.message);
    }
}

/**
 * Fetch và hiển thị chỉ số RSI
 */
async function fetchBtcRsi_index() {
    const container = document.getElementById('rsi-container');
    try {
        const response = await fetch('/api/crypto/btc-rsi');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Lỗi server ${response.status}`);
        }
        const data = await response.json();
        const rsiValue = data.rsi_14;

        if (rsiValue === null || rsiValue === undefined) {
            throw new Error('Không nhận được giá trị RSI.');
        }
        
        createRsiGauge_index(container, rsiValue);

    } catch (error) {
        console.error('Lỗi fetchBtcRsi_index:', error);
        displayError('rsi-container', error.message);
    }
}

/**
 * Hàm chung để tạo đồng hồ đo
 * @param {HTMLElement} container - Element chứa biểu đồ
 * @param {number} value - Giá trị (0-100)
 * @param {string} label - Nhãn hiển thị
 * @param {string} colorVar - Biến màu CSS
 * @param {string} gaugeClass - Lớp CSS riêng cho đồng hồ đo
 */
function createGauge_index(container, value, label, colorVar, gaugeClass) {
    const val = Math.max(0, Math.min(100, value));
    const radius = 80;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (val / 100) * circumference;

    container.innerHTML = `
        <div class="gauge">
            <svg class="gauge__body" viewBox="0 0 180 180">
                <circle class="gauge__track" r="${radius}" cx="90" cy="90" style="stroke-dasharray: ${circumference};"></circle>
                <circle class="gauge__fill ${gaugeClass}" r="${radius}" cx="90" cy="90" 
                        style="stroke: ${colorVar}; stroke-dasharray: ${circumference}; stroke-dashoffset: ${offset};">
                </circle>
            </svg>
            <div class="gauge__cover">
                <div class="gauge__value">${Math.round(val)}</div>
                <div class="gauge__label" style="color: ${colorVar};">${label}</div>
            </div>
        </div>
    `;
}

/**
 * Tạo đồng hồ đo cho Fear & Greed Index
 * @param {HTMLElement} container
 * @param {number} value
 * @param {string} classification
 */
function createFngGauge_index(container, value, classification) {
    let colorVar;
    if (value <= 24) colorVar = 'var(--fng-extreme-fear-color)';
    else if (value <= 49) colorVar = 'var(--fng-fear-color)';
    else if (value <= 54) colorVar = 'var(--fng-neutral-color)';
    else if (value <= 74) colorVar = 'var(--fng-greed-color)';
    else colorVar = 'var(--fng-extreme-greed-color)';
    
    createGauge_index(container, value, classification || 'N/A', colorVar, 'gauge__fill--fng');
}

/**
 * Tạo đồng hồ đo cho RSI
 * @param {HTMLElement} container
 * @param {number} value
 */
function createRsiGauge_index(container, value) {
    let label = 'Trung tính';
    let colorVar = 'var(--rsi-neutral-color)';
    if (value >= 70) {
        label = 'Quá mua';
        colorVar = 'var(--rsi-overbought-color)';
    } else if (value <= 30) {
        label = 'Quá bán';
        colorVar = 'var(--rsi-oversold-color)';
    }
    
    createGauge_index(container, value, label, colorVar, 'gauge__fill--rsi');
}


/**
 * Tải nội dung báo cáo từ file tĩnh và tạo mục lục điều hướng.
 */
async function loadReportAndCreateNav() {
    try {
        const response = await fetch("/static/report.html");
        if (!response.ok) throw new Error('Không thể tải tệp báo cáo.');
        const reportHtml = await response.text();

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = reportHtml;

        const navLinksContainer = document.getElementById('report-nav-links');
        const reportContainer = document.getElementById('report-container');
        reportContainer.innerHTML = '';

        const sections = tempDiv.querySelectorAll('section');

        sections.forEach(section => {
            const h2 = section.querySelector('h2');
            if (h2 && section.id) {
                reportContainer.appendChild(section);

                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#${section.id}`;
                const h2Text = h2.cloneNode(true);
                h2Text.querySelector('.icon')?.remove();
                a.textContent = h2Text.textContent.trim();
                li.appendChild(a);
                navLinksContainer.appendChild(li);
            }
        });

        const navLinks = navLinksContainer.querySelectorAll('a');
        const reportSections = reportContainer.querySelectorAll('section');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href').substring(1) === entry.target.id) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        }, { rootMargin: "-30% 0px -70% 0px" });

        reportSections.forEach(section => {
            observer.observe(section);
        });

        // Gọi hàm vẽ các biểu đồ từ report.js SAU KHI nội dung đã được tải.
        // Điều này đảm bảo các phần tử DOM đã tồn tại để các biểu đồ có thể được vẽ.
        if (typeof initializeAllVisuals === 'function') {
            initializeAllVisuals();
        }
        else if (typeof initializeAllVisuals_report === 'function') {
            initializeAllVisuals_report();
        }


    } catch (error) {
        console.error('Lỗi tải báo cáo:', error);
        document.getElementById('report-container').innerHTML = '<p class="text-red-600 font-semibold">Lỗi: Không thể tải nội dung báo cáo chi tiết.</p>';
    }
}

/**
 * Hàm khởi tạo chính
 */
function init() {
    loadReportAndCreateNav();
    
    fetchCryptoData();
    fetchBtcAndFearGreed();
    fetchBtcRsi_index(); 
    
    setInterval(fetchCryptoData, 300000); 
    setInterval(fetchBtcAndFearGreed, 300000); 
    setInterval(fetchBtcRsi_index, 900000); 
}


function setupThemeSwitcher() {
    const themeToggleButton = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        htmlElement.setAttribute('data-theme', currentTheme);
    }

    themeToggleButton.addEventListener('click', () => {
        if (htmlElement.getAttribute('data-theme') === 'dark') {
            htmlElement.removeAttribute('data-theme');
            localStorage.removeItem('theme');
        } else {
            htmlElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    init();
    setupThemeSwitcher();
});