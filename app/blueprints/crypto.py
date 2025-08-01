from flask import Blueprint, jsonify
from ..utils.cache import cache
from ..services import coingecko, alternative_me, taapi
import time
import concurrent.futures
import threading

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.after_request
def after_request(response):
    """Đảm bảo tất cả response từ crypto blueprint có Content-Type là JSON"""
    if not response.content_type:
        response.content_type = 'application/json'
    return response


@crypto_bp.route('/health')
def health_check():
    """Health check endpoint để verify service availability"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time())
    })


@crypto_bp.route('/api-status')
def api_status():
    """
    Endpoint để kiểm tra trạng thái các API và rate limiting.
    """
    current_time = time.time()
    
    # Lấy thông tin rate limiting từ TAAPI
    time_since_last_taapi = current_time - taapi._last_request_time if hasattr(taapi, '_last_request_time') else 0
    min_interval = getattr(taapi, '_min_request_interval', 60)
    
    status = {
        "taapi": {
            "last_request_ago": int(time_since_last_taapi),
            "min_interval": min_interval,
            "can_request_now": time_since_last_taapi >= min_interval,
            "wait_time": max(0, int(min_interval - time_since_last_taapi))
        },
        "timestamp": int(current_time)
    }
    
    return jsonify(status)



@crypto_bp.route('/dashboard-summary')
@cache.cached(timeout=300)  # Cache trong 5 phút thay vì 10 phút để cân bằng fresh data vs performance
def dashboard_summary():
    """
    Endpoint tổng hợp, trả về tất cả dữ liệu cần thiết cho dashboard chính
    chỉ trong một lần gọi API để tối ưu tốc độ tải trang.
    Sử dụng parallel API calls để giảm thời gian xử lý.
    """
    try:
        # Định nghĩa các service calls
        def call_global_data():
            return coingecko.get_global_market_data()
        
        def call_btc_data():
            return coingecko.get_btc_price()
        
        def call_fng_data():
            return alternative_me.get_fng_index()
        
        def call_rsi_data():
            return taapi.get_btc_rsi()
        
        # Gọi tất cả API song song với timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_global = executor.submit(call_global_data)
            future_btc = executor.submit(call_btc_data)
            future_fng = executor.submit(call_fng_data)
            future_rsi = executor.submit(call_rsi_data)
            
            # Chờ tất cả hoàn thành với timeout 7 giây
            try:
                global_data, global_error, global_status = future_global.result(timeout=7)
                btc_data, btc_error, btc_status = future_btc.result(timeout=7)
                fng_data, fng_error, fng_status = future_fng.result(timeout=7)
                rsi_data, rsi_error, rsi_status = future_rsi.result(timeout=7)
            except concurrent.futures.TimeoutError:
                # Nếu timeout, sử dụng giá trị mặc định
                return jsonify({
                    "error": "Request timeout",
                    "message": "API calls took too long, using default values",
                    "market_cap": None,
                    "volume_24h": None,
                    "btc_price_usd": None,
                    "btc_change_24h": None,
                    "fng_value": 50,
                    "fng_classification": "Neutral",
                    "rsi_14": 50
                }), 200

        # Phân loại lỗi: critical vs non-critical
        critical_errors = {}
        warnings = {}
        
        # Kiểm tra từng service
        if global_error:
            if global_status == 429:
                warnings["global_data"] = "Rate limit reached - using cached data"
            else:
                critical_errors["global_data"] = global_error
                
        if btc_error:
            if btc_status == 429:
                warnings["btc_data"] = "Rate limit reached - using cached data"
            else:
                critical_errors["btc_data"] = btc_error
                
        if fng_error:
            if fng_status == 429:
                warnings["fng_data"] = "Rate limit reached - using default value"
                fng_data = {"fng_value": 50, "fng_value_classification": "Neutral"}
            else:
                warnings["fng_data"] = fng_error
                fng_data = {"fng_value": 50, "fng_value_classification": "Neutral"}
                
        if rsi_error:
            if rsi_status == 429:
                warnings["rsi_data"] = "Rate limit reached - using default value"
                rsi_data = {"rsi_14": 50}
            else:
                warnings["rsi_data"] = rsi_error
                rsi_data = {"rsi_14": 50}

        # Chỉ fail request nếu có critical error (không phải rate limit)
        if critical_errors:
            return jsonify({
                "errors": critical_errors,
                "warnings": warnings
            }), 500

        # Kết hợp tất cả dữ liệu thành một object duy nhất
        combined_data = {
            **(global_data or {}),
            **(btc_data or {}),
            **(fng_data or {}),
            **(rsi_data or {}),
        }
        
        # Thêm thông tin warnings nếu có
        if warnings:
            combined_data["warnings"] = warnings

        return jsonify(combined_data)
    
    except Exception as e:
        # Log lỗi để debug
        import traceback
        print(f"Error in dashboard_summary: {e}")
        print(traceback.format_exc())
        
        # Trả về JSON error response với fallback data
        return jsonify({
            "error": "Internal server error", 
            "message": str(e),
            "status": 500,
            # Fallback data để frontend vẫn có thể hiển thị
            "market_cap": None,
            "volume_24h": None,
            "btc_price_usd": None,
            "btc_change_24h": None,
            "fng_value": 50,
            "fng_classification": "Neutral",
            "rsi_14": 50
        }), 500