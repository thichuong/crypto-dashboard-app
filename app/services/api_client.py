import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

def fetch_json(url, timeout=10):
    """
    Hàm chung để gửi yêu cầu GET và trả về dữ liệu JSON.
    Bao gồm xử lý lỗi chi tiết.

    Args:
        url (str): URL của API.
        timeout (int): Thời gian chờ tối đa cho request.

    Returns:
        tuple: (data, error, status_code)
               - data (dict or None): Dữ liệu JSON nếu thành công.
               - error (str or None): Thông báo lỗi nếu thất bại.
               - status_code (int): HTTP status code.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json(), None, response.status_code
    except HTTPError as http_err:
        return None, f"Lỗi HTTP: {http_err}", http_err.response.status_code
    except ConnectionError as conn_err:
        return None, f"Lỗi kết nối: {conn_err}", 503
    except Timeout:
        return None, "Request timed out", 504
    except RequestException as e:
        return None, f"Lỗi không xác định: {e}", 500
    except ValueError: # Bắt lỗi khi JSON decode thất bại
        return None, "Lỗi giải mã JSON từ API", 500