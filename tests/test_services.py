#!/usr/bin/env python3
"""
Test script for individual services to debug issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import coingecko, alternative_me, taapi
from app.utils.cache import is_serverless_environment
import traceback

def test_service(name, func):
    """Test a service function and report results"""
    print(f"\n--- Testing {name} ---")
    try:
        data, error, status = func()
        print(f"Status: {status}")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Success: {data}")
        return data, error, status
    except Exception as e:
        print(f"Exception: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None, str(e), 500

def main():
    print("=== Crypto Services Test ===")
    print(f"Serverless environment: {is_serverless_environment()}")
    print(f"VERCEL env var: {os.getenv('VERCEL')}")
    print(f"AWS_LAMBDA_FUNCTION_NAME: {os.getenv('AWS_LAMBDA_FUNCTION_NAME')}")
    
    # Test each service
    results = {}
    
    results['coingecko_global'] = test_service("CoinGecko Global Data", coingecko.get_global_market_data)
    results['coingecko_btc'] = test_service("CoinGecko BTC Price", coingecko.get_btc_price)
    results['alternative_fng'] = test_service("Alternative.me F&G", alternative_me.get_fng_index)
    results['taapi_rsi'] = test_service("TAAPI RSI", taapi.get_btc_rsi)
    
    # Summary
    print("\n=== SUMMARY ===")
    for service, (data, error, status) in results.items():
        status_icon = "✅" if not error else "❌"
        print(f"{status_icon} {service}: {'OK' if not error else 'FAILED'}")
    
    # Check if all critical services work
    critical_services = ['coingecko_global', 'coingecko_btc']
    all_critical_ok = all(not results[s][1] for s in critical_services)
    
    if all_critical_ok:
        print("\n✅ All critical services working")
        return 0
    else:
        print("\n❌ Some critical services failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
