from flask import Blueprint, jsonify
from ..utils.cache import cache
from ..services import coingecko, alternative_me, taapi

crypto_bp = Blueprint('crypto', __name__)



@crypto_bp.route('/dashboard-summary')
@cache.cached(timeout=600) # Cache trong 10 phút
def dashboard_summary():
    """
    Endpoint tổng hợp, trả về tất cả dữ liệu cần thiết cho dashboard chính
    chỉ trong một lần gọi API để tối ưu tốc độ tải trang.
    """
    # Lấy dữ liệu từ các service
    global_data, global_error, _ = coingecko.get_global_market_data()
    btc_data, btc_error, _ = coingecko.get_btc_price()
    fng_data, fng_error, _ = alternative_me.get_fng_index()
    rsi_data, rsi_error, _ = taapi.get_btc_rsi()

    # Kiểm tra và gom lỗi nếu có
    errors = {
        "global_data": global_error,
        "btc_data": btc_error,
        "fng_data": fng_error,
        "rsi_data": rsi_error
    }
    actual_errors = {k: v for k, v in errors.items() if v}
    if actual_errors:
        return jsonify({"errors": actual_errors}), 500

    # Kết hợp tất cả dữ liệu thành một object duy nhất
    combined_data = {
        **(global_data or {}),
        **(btc_data or {}),
        **(fng_data or {}),
        **(rsi_data or {}),
    }

    return jsonify(combined_data)