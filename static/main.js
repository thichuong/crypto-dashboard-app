// static/main.js

/**
 * Định dạng số lớn thành dạng ngắn gọn (nghìn tỷ, tỷ, triệu).
 * @param {number} num - Số cần định dạng.
 * @returns {string} - Chuỗi đã được định dạng.
 */
function formatNumber(num) {
    if (!num) return 'N/A';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + ' nghìn tỷ';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + ' tỷ';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + ' triệu';
    return num.toLocaleString('en-US');
}

/**
 * Fetch dữ liệu tổng quan thị trường (vốn hóa, khối lượng).
 */
async function fetchCryptoData() {
    try {
        const response = await fetch('/api/crypto/global');
        if (!response.ok) throw new Error('Lỗi khi lấy dữ liệu global.');
        const data = await response.json();
        
        // Cập nhật Tổng Vốn Hóa
        const marketCapContainer = document.getElementById('market-cap-container');
        marketCapContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data['market-cap'])}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

        // Cập nhật Khối Lượng Giao Dịch
        const volumeContainer = document.getElementById('volume-24h-container');
        volumeContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + formatNumber(data['volume-24h'])}</p>
            <p class="text-sm text-gray-500">Toàn thị trường</p>
        `;

    } catch (error) {
        console.error('Lỗi fetchCryptoData:', error);
        document.getElementById('market-cap-container').innerHTML = `<p class="text-red-600">Error</p>`;
        document.getElementById('volume-24h-container').innerHTML = `<p class="text-red-600">Error</p>`;
    }
}

/**
 * Fetch giá Bitcoin và chỉ số Sợ hãi & Tham lam.
 */
async function fetchBtcAndFearGreed() {
    try {
        const response = await fetch('/api/crypto/btc-and-fng');
        if (!response.ok) throw new Error('Lỗi khi lấy dữ liệu BTC và F&G.');
        const data = await response.json();

        // Cập nhật giá BTC
        const bitcoin = data.bitcoin.bitcoin;
        const btcContainer = document.getElementById('btc-price-container');
        const change = bitcoin.usd_24h_change;
        const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
        btcContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${'$' + bitcoin.usd.toLocaleString('en-US')}</p>
            <p class="text-sm font-semibold ${changeClass}">${change.toFixed(2)}% (24h)</p>
        `;

        // Cập nhật chỉ số Sợ hãi & Tham lam
        const fearGreed = data.fear_and_greed.data[0];
        const fngContainer = document.getElementById('fear-greed-container');
        const value = parseInt(fearGreed.value);
        let colorClass = 'text-yellow-500';
        if (value <= 25) colorClass = 'text-red-600';
        if (value >= 75) colorClass = 'text-green-600';
        fngContainer.innerHTML = `
            <p class="text-3xl font-bold text-gray-900">${fearGreed.value}</p>
            <p class="text-sm font-medium ${colorClass}">${fearGreed.value_classification}</p>
        `;

    } catch (error) {
        console.error('Lỗi fetchBtcAndFearGreed:', error);
        document.getElementById('btc-price-container').innerHTML = `<p class="text-red-600">Error</p>`;
        document.getElementById('fear-greed-container').innerHTML = `<p class="text-red-600">Error</p>`;
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
    fetchCryptoData();
    fetchBtcAndFearGreed();
    setInterval(fetchCryptoData, 300000); // 5 phút
    setInterval(fetchBtcAndFearGreed, 300000); // 5 phút
}

// Chạy hàm init khi toàn bộ nội dung trang đã sẵn sàng
document.addEventListener('DOMContentLoaded', init);