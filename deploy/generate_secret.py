#!/usr/bin/env python3
"""
Generate SECRET_KEY for Railway production deployment
"""
import secrets

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_hex(32)

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"Generated SECRET_KEY: {secret_key}")
    print("\nAdd this to Railway environment variables:")
    print(f"SECRET_KEY={secret_key}")
