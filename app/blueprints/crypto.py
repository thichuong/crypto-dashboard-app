from flask import Blueprint, jsonify
from ..utils.cache import cache
from ..services import coingecko, alternative_me, taapi
import time

crypto_bp = Blueprint('crypto', __name__)


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
@cache.cached(timeout=600) # Cache trong 10 phút
def dashboard_summary():
    """
    Endpoint tổng hợp, trả về tất cả dữ liệu cần thiết cho dashboard chính
    chỉ trong một lần gọi API để tối ưu tốc độ tải trang.
    """
    # Lấy dữ liệu từ các service
    global_data, global_error, global_status = coingecko.get_global_market_data()
    btc_data, btc_error, btc_status = coingecko.get_btc_price()
    fng_data, fng_error, fng_status = alternative_me.get_fng_index()
    rsi_data, rsi_error, rsi_status = taapi.get_btc_rsi()

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