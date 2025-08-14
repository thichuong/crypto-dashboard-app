// language-toggle.js
// Simple language toggle between Vietnamese (vi) and English (en)
(function(){
    const LANG_KEY = 'preferred_language';
    const BACKUP_KEY = 'language';
    const DEFAULT_LANG = 'vi';

    // Minimal translation map for elements used in dashboard/report
    const translations = {
        'create-report': { vi: 'Tạo Báo cáo Mới', en: 'Create New Report' },
        'view-report-history': { vi: 'Xem Lịch Sử Báo Cáo', en: 'View Report History' },
        'print-report': { vi: 'In Báo cáo', en: 'Print Report' },
        'whole-market': { vi: 'Toàn bộ thị trường', en: 'Whole market' },
        'loading': { vi: 'Đang tải...', en: 'Loading...' },
        'connection-issue': { vi: 'Lỗi kết nối', en: 'Connection issue' },
        // Fear & Greed / RSI labels
        'extreme-fear': { vi: 'Sợ hãi Tột độ', en: 'Extreme Fear' },
        'fear': { vi: 'Sợ hãi', en: 'Fear' },
        'neutral': { vi: 'Trung lập', en: 'Neutral' },
        'greed': { vi: 'Tham lam', en: 'Greed' },
        'extreme-greed': { vi: 'Tham lam Tột độ', en: 'Extreme Greed' },
        'oversold': { vi: 'Quá bán', en: 'Oversold' },
    'overbought': { vi: 'Quá mua', en: 'Overbought' },
    'bitcoin': { vi: 'Bitcoin', en: 'Bitcoin' },
    'altcoins': { vi: 'Altcoins', en: 'Altcoins' }
    };

    function getPreferredLanguage(){
        try { return localStorage.getItem(LANG_KEY) || DEFAULT_LANG; } catch(e){ return DEFAULT_LANG; }
    }

    function setPreferredLanguage(lang){
        try {
            localStorage.setItem(LANG_KEY, lang);
            localStorage.setItem(BACKUP_KEY, lang);
        } catch(e){}
        updateUI(lang);
        // Notify other scripts that language changed
        try {
            const ev = new CustomEvent('languageChanged', { detail: { language: lang } });
            window.dispatchEvent(ev);
        } catch(e) {
            // ignore
        }
    }

    function updateUI(lang){
        // update html lang attribute
        document.documentElement.lang = (lang === 'en') ? 'en' : 'vi';

        // update button text
        const btnText = document.querySelector('#language-toggle .lang-text');
        if (btnText) btnText.textContent = (lang === 'en') ? 'EN' : 'VI';

        // swap report content if both versions exist
        const viContainer = document.getElementById('report-content-vi');
        const enContainer = document.getElementById('report-content-en');
        if (viContainer) viContainer.style.display = (lang === 'vi') ? 'block' : 'none';
        if (enContainer) enContainer.style.display = (lang === 'en') ? 'block' : 'none';

        // translate elements that use data-i18n
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (!key) return;
            const map = translations[key];
            if (map && map[lang]) {
                el.textContent = map[lang];
            }
        });
        // expose a minimal languageManager for other scripts
        try {
            window.languageManager = window.languageManager || {};
            window.languageManager.currentLanguage = lang;
            window.languageManager.getTranslatedText = function(key) {
                const m = translations[key];
                if (m && m[lang]) return m[lang];
                return key;
            };
            window.languageManager.formatNumberLocalized = function(num) {
                if (num === null || num === undefined) return 'N/A';
                // simple large-number formatting with locale
                if (lang === 'vi') {
                    if (num >= 1e12) return (num / 1e12).toFixed(2) + ' nghìn tỷ';
                    if (num >= 1e9) return (num / 1e9).toFixed(2) + ' tỷ';
                    if (num >= 1e6) return (num / 1e6).toFixed(2) + ' triệu';
                    return new Intl.NumberFormat('vi-VN').format(num);
                } else {
                    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
                    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
                    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
                    return new Intl.NumberFormat('en-US').format(num);
                }
            };
        } catch (e) {
            // ignore
        }
    }

    function toggleLanguage(){
        const current = getPreferredLanguage();
        const next = (current === 'vi') ? 'en' : 'vi';
        setPreferredLanguage(next);
    }

    document.addEventListener('DOMContentLoaded', function(){
        const initial = getPreferredLanguage();
        // set initial UI
        updateUI(initial);

        // Notify other scripts about initial language so they can initialize correctly
        try {
            const evInit = new CustomEvent('languageChanged', { detail: { language: initial } });
            window.dispatchEvent(evInit);
        } catch(e) {}

        const toggleBtn = document.getElementById('language-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function(e){
                e.preventDefault();
                toggleLanguage();
            });
        }
    });
})();
