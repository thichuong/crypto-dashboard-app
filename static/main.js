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
            // Ném lỗi nếu response không 'ok' để khối catch có thể xử lý
            const errorData = await response.json();
            throw new Error(errorData.error || `Lỗi server ${response.status}`);
        }
        const data = await response.json();
        
        // Cập nhật Tổng Vốn Hóa - SỬ DỤNG KEY MỚI 'market_cap'
        const marketCapContainer = document.getElementById('market-cap-container');
        marketCapContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data.market_cap)}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

        // Cập nhật Khối Lượng Giao Dịch - SỬ DỤNG KEY MỚI 'volume_24h'
        const volumeContainer = document.getElementById('volume-24h-container');
        volumeContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data.volume_24h)}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

    } catch (error) {
        console.error('Lỗi fetchCryptoData:', error);
        // HIỂN THỊ LỖI THÂN THIỆN
        displayError('market-cap-container', error.message);
        displayError('volume-24h-container', error.message);
    }
}

/**
 * Fetch giá Bitcoin và chỉ số Sợ hãi & Tham lam.
 */
async function fetchBtcAndFearGreed() {
    try {
        const response = await fetch('/api/crypto/btc-and-fng');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Lỗi server ${response.status}`);
        }
        const data = await response.json();

        // Cập nhật giá BTC - SỬ DỤNG KEY MỚI 'btc_price_usd' và 'btc_change_24h'
        const btcContainer = document.getElementById('btc-price-container');
        const change = data.btc_change_24h;
        const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
        btcContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + (data.btc_price_usd ? data.btc_price_usd.toLocaleString('en-US') : 'N/A')}</p>
            <p class="text-sm font-semibold ${changeClass}">${change !== null ? change.toFixed(2) : 'N/A'}% (24h)</p>
        `;

        // Cập nhật chỉ số Sợ hãi & Tham lam - SỬ DỤNG KEY MỚI 'fng_value' và 'fng_classification'
        const fngContainer = document.getElementById('fear-greed-container');
        const value = parseInt(data.fng_value, 10);
        let colorClass = 'text-yellow-500'; // Mặc định
        if (!isNaN(value)) {
            if (value <= 25) colorClass = 'text-red-600';
            else if (value >= 75) colorClass = 'text-green-600';
        }
        
        fngContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${data.fng_value || 'N/A'}</p>
            <p class="text-sm font-medium ${colorClass}">${data.fng_classification || 'Unknown'}</p>
        `;

    } catch (error) {
        console.error('Lỗi fetchBtcAndFearGreed:', error);
        // HIỂN THỊ LỖI THÂN THIỆN
        displayError('btc-price-container', error.message);
        displayError('fear-greed-container', error.message);
    }
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
        reportContainer.innerHTML = ''; // Xóa nội dung cũ

        const sections = tempDiv.querySelectorAll('section');

        sections.forEach(section => {
            const h2 = section.querySelector('h2');
            if (h2 && section.id) {
                // Thêm section vào container chính
                reportContainer.appendChild(section);

                // Tạo mục lục
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = `#${section.id}`;
                // Lấy text của h2 bỏ qua icon
                const h2Text = h2.cloneNode(true);
                h2Text.querySelector('.icon')?.remove();
                a.textContent = h2Text.textContent.trim();
                li.appendChild(a);
                navLinksContainer.appendChild(li);
            }
        });

        // Scroll Spy Logic
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

    } catch (error) {
        console.error('Lỗi tải báo cáo:', error);
        document.getElementById('report-container').innerHTML = '<p class="text-red-600 font-semibold">Lỗi: Không thể tải nội dung báo cáo chi tiết.</p>';
    }
}

/**
 * Hàm khởi tạo chính, được gọi khi trang tải xong.
 */
function init() {
    loadReportAndCreateNav();
    
    // Gọi lần đầu để tải dữ liệu ngay lập tức
    fetchCryptoData();
    fetchBtcAndFearGreed();
    
    // Thiết lập tự động cập nhật sau mỗi 5 phút
    setInterval(fetchCryptoData, 300000); 
    setInterval(fetchBtcAndFearGreed, 300000);
}


function setupThemeSwitcher() {
    const themeToggleButton = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    // 1. Kiểm tra theme đã lưu trong localStorage khi tải trang
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        htmlElement.setAttribute('data-theme', currentTheme);
    }

    // 2. Lắng nghe sự kiện click trên nút
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

// Chạy hàm init khi toàn bộ nội dung trang đã sẵn sàng
document.addEventListener('DOMContentLoaded', () => {
    init();
    setupThemeSwitcher(); // Gọi hàm cài đặt theme switcher
});