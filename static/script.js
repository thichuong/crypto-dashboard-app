document.addEventListener('DOMContentLoaded', function() {
    const btcPriceEl = document.getElementById('btc-price');
    const marketCapEl = document.getElementById('market-cap');
    const btcDominanceEl = document.getElementById('btc-dominance');
    const fearGreedValueEl = document.getElementById('fear-greed-value');
    const fearGreedTextContainer = document.getElementById('fear-greed-text-container');
    const statusMessageEl = document.getElementById('status-message');

    function updateDisplay(data) {
        if (!data || Object.keys(data).length === 0) {
            statusMessageEl.textContent = 'Không thể tải dữ liệu. Đang thử lại...';
            return;
        }

        statusMessageEl.textContent = ''; // Xóa thông báo trạng thái nếu thành công
        btcPriceEl.textContent = data.btc_price || 'N/A';
        marketCapEl.textContent = data.total_market_cap || 'N/A';
        btcDominanceEl.textContent = data.btc_dominance || 'N/A';
        fearGreedValueEl.textContent = data.fear_greed_value || '--';

        fearGreedTextContainer.innerHTML = '';
        if (data.fear_greed_text) {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = data.fear_greed_text;
            const text = data.fear_greed_text.toLowerCase();
            if (text.includes('greed')) tag.classList.add('tag-green');
            else if (text.includes('fear')) tag.classList.add('tag-red');
            else tag.classList.add('tag-yellow');
            fearGreedTextContainer.appendChild(tag);
        }
    }

    async function handleEmptyCache() {
        console.log("Cache trống. Kích hoạt lệnh nạp dữ liệu từ frontend.");
        statusMessageEl.textContent = 'Dữ liệu đang được khởi tạo, vui lòng chờ trong giây lát...';
        
        // Gửi yêu cầu để backend bắt đầu cập nhật cache
        await fetch('/api/update-cache');
        
        // Đợi một chút để cache được ghi lại, sau đó thử lấy lại dữ liệu
        setTimeout(fetchMarketData, 5000); // Thử lại sau 5 giây
    }

    async function fetchMarketData() {
        try {
            const response = await fetch('/api/market-data');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();

            if (data.status === 'empty_cache') {
                handleEmptyCache();
            } else {
                updateDisplay(data);
            }
        } catch (error) {
            console.error("Không thể lấy dữ liệu thị trường:", error);
            statusMessageEl.textContent = 'Lỗi kết nối. Vui lòng kiểm tra lại mạng.';
        }
    }

    // Lấy dữ liệu ngay khi tải trang
    fetchMarketData();

    // Cập nhật dữ liệu từ cache sau mỗi 15 giây
    setInterval(fetchMarketData, 15000);
});
