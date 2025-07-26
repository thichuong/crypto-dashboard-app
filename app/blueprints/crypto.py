from flask import Blueprint, jsonify
from ..utils.cache import cache
from ..services import coingecko, alternative_me, taapi

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route('/global')
@cache.cached(timeout=300)
def get_global_data():
    """Lấy dữ liệu tổng quan thị trường."""
    data, error, status_code = coingecko.get_global_market_data()
    if error:
        return jsonify({"error": error}), status_code
    return jsonify(data)

@crypto_bp.route('/btc-and-fng')
@cache.cached(timeout=300)
def get_btc_and_fng_data():
    """Lấy giá BTC và chỉ số Fear & Greed."""
    # Lấy giá BTC
    btc_data, btc_error, btc_status = coingecko.get_btc_price()
    if btc_error:
        return jsonify({"error": btc_error}), btc_status

    # Lấy chỉ số F&G
    fng_data, fng_error, fng_status = alternative_me.get_fng_index()
    if fng_error:
        return jsonify({"error": fng_error}), fng_status

    # Kết hợp dữ liệu
    combined_data = {**btc_data, **fng_data}
    return jsonify(combined_data)


@crypto_bp.route('/btc-rsi')
@cache.cached(timeout=3600)
def get_btc_rsi():
    """Lấy chỉ số RSI(14) của Bitcoin."""
    data, error, status_code = taapi.get_btc_rsi()
    if error:
        return jsonify({"error": error}), status_code
    return jsonify(data)