#!/usr/bin/env python3
"""
Script test API để kiểm tra response từ dashboard-summary endpoint
"""

import requests
import json
import sys

def test_dashboard_api(base_url="http://127.0.0.1:8080"):
    """Test the dashboard-summary API endpoint"""
    
    endpoint = f"{base_url}/api/crypto/dashboard-summary"
    
    print(f"Testing endpoint: {endpoint}")
    print("-" * 50)
    
    try:
        response = requests.get(endpoint, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        # Kiểm tra nếu response có content
        if len(response.content) == 0:
            print("ERROR: Empty response")
            return False
            
        # Kiểm tra content type
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            print(f"WARNING: Unexpected content type: {content_type}")
            print("Response content (first 500 chars):")
            print(response.text[:500])
            return False
            
        # Thử parse JSON
        try:
            data = response.json()
            print("SUCCESS: JSON parsed successfully")
            print("Data keys:", list(data.keys()) if isinstance(data, dict) else "Not a dict")
            
            # In ra data với format đẹp
            print("\nResponse data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON decode failed: {e}")
            print("Raw response (first 500 chars):")
            print(response.text[:500])
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return False

if __name__ == "__main__":
    # Cho phép truyền URL qua command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    
    success = test_dashboard_api(base_url)
    sys.exit(0 if success else 1)
