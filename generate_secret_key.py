#!/usr/bin/env python3
"""
Utility script để tạo random secret key cho AUTO_UPDATE_SECRET_KEY
Chạy script này để tạo key mới khi cần
"""

import secrets
import string

def generate_secret_key(length=32):
    """
    Tạo random secret key an toàn
    
    Args:
        length (int): Độ dài của key (mặc định: 32)
        
    Returns:
        str: Random secret key
    """
    # Sử dụng chữ cái, số và một số ký tự đặc biệt an toàn
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_multiple_keys(count=5, length=32):
    """
    Tạo nhiều secret key để lựa chọn
    
    Args:
        count (int): Số lượng key cần tạo
        length (int): Độ dài của mỗi key
    """
    print(f"Generated {count} random secret keys ({length} characters each):")
    print("=" * 50)
    
    for i in range(count):
        key = generate_secret_key(length)
        print(f"{i+1}. {key}")
    
    print("=" * 50)
    print("Copy one of the above keys to your .env file:")
    print("AUTO_UPDATE_SECRET_KEY=<selected_key>")
    print("\nThen access your auto update system at:")
    print("http://your-domain.com/auto-update-system-<selected_key>")

if __name__ == "__main__":
    print("🔐 AUTO UPDATE SECRET KEY GENERATOR")
    print("")
    
    # Tạo 5 key options
    generate_multiple_keys()
    
    print("\n💡 Tips:")
    print("- Keep your secret key confidential")
    print("- Change it periodically for better security") 
    print("- Use a different key for production vs development")
    print("- Don't commit the key to version control")
