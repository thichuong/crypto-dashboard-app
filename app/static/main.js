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

        // Cập nhật chỉ số Sợ hãi & Tham lam bằng hàm createGauge
        const fngValue = parseInt(data.fng_value, 10);
        if (!isNaN(fngValue)) {
            const fngConfig = {
                min: 0,
                max: 100,
                segments: [
                    { limit: 24, color: 'var(--fng-extreme-fear-color)', label: 'Sợ hãi Cực độ' },
                    { limit: 49, color: 'var(--fng-fear-color)', label: 'Sợ hãi' },
                    { limit: 54, color: 'var(--fng-neutral-color)', label: 'Trung tính' },
                    { limit: 74, color: 'var(--fng-greed-color)', label: 'Tham lam' },
                    { limit: 100, color: 'var(--fng-extreme-greed-color)', label: 'Tham lam Cực độ' }
                ]
            };
            createGauge(fngContainer, fngValue, fngConfig);
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
        
        const rsiConfig = {
            min: 0,
            max: 100,
            segments: [
                { limit: 30, color: 'var(--rsi-oversold-color)', label: 'Quá bán' },
                { limit: 70, color: 'var(--rsi-neutral-color)', label: 'Trung tính' },
                { limit: 100, color: 'var(--rsi-overbought-color)', label: 'Quá mua' }
            ]
        };
        createGauge(container, rsiValue, rsiConfig);

    } catch (error) {
        console.error('Lỗi fetchBtcRsi_index:', error);
        displayError('rsi-container', error.message);
    }
}


/**
 * Tải nội dung báo cáo từ file tĩnh và tạo mục lục điều hướng.
 */
async function CreateNav() {
    try {

        const reportContainer = document.getElementById('report-container');
        const navLinksContainer = document.getElementById('report-nav-links');

        // Thoát sớm nếu các container chính không tồn tại để tránh lỗi
        if (!reportContainer || !navLinksContainer) {
            console.error("Không tìm thấy container cho báo cáo (#report-container) hoặc mục lục (#report-nav-links).");
            return;
        }
        
        // Xóa nội dung cũ của mục lục trước khi tạo mới để tránh trùng lặp
        navLinksContainer.innerHTML = '';

        const reportSections = reportContainer.querySelectorAll('section');

        reportSections.forEach(section => {
            const h2 = section.querySelector('h2');
            if (h2 && section.id) {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#${section.id}`;
                const h2Text = h2.cloneNode(true);
                h2Text.querySelector('i')?.remove(); // Sửa selector cho icon để chính xác hơn
                a.textContent = h2Text.textContent.trim();
                li.appendChild(a);
                navLinksContainer.appendChild(li);
            }
        });

        const navLinks = navLinksContainer.querySelectorAll('a');

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
    CreateNav();
    
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