#!/usr/bin/env python3
"""
CLI tool để test database health và connection trên Railway
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.utils.database_health import DatabaseHealthChecker, print_health_status


def main():
    """Main CLI function"""
    print("🚀 Starting Database Health Check...")
    
    try:
        # Tạo Flask app với config
        app = create_app()
        
        with app.app_context():
            # Run comprehensive health check
            health_data = DatabaseHealthChecker.full_health_check()
            
            # Print results
            print_health_status(health_data)
            
            # Return appropriate exit code
            connection_healthy = health_data.get('connection', {}).get('healthy', False)
            operations_success = health_data.get('operations', {}).get('success', False)
            
            if connection_healthy and operations_success:
                print("\n✅ Overall Status: HEALTHY")
                return 0
            else:
                print("\n❌ Overall Status: UNHEALTHY")
                return 1
                
    except Exception as e:
        print(f"\n💥 Critical Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
