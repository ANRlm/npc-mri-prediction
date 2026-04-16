#!/usr/bin/env python3
"""
Test script for new backend endpoints
"""
import sys
import os

# Add backend to path
sys.path.insert(0, '/root/MRI/MRI_backend')

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from predict_backend import app, configure_jwt, init_mongodb
        print("✓ Flask app imported successfully")

        from auth_models import create_user, get_user_by_username, verify_password, hash_password
        print("✓ Auth models imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_endpoints_defined():
    """Test that new endpoints are defined"""
    print("\nTesting endpoint definitions...")
    try:
        from predict_backend import app

        endpoints = {
            '/api/change_password': 'POST',
            '/api/statistics': 'GET',
            '/api/images': 'GET',
        }

        # Get all routes
        routes = {rule.rule: list(rule.methods) for rule in app.url_map.iter_rules()}

        for endpoint, method in endpoints.items():
            if endpoint in routes and method in routes[endpoint]:
                print(f"✓ {method} {endpoint} is defined")
            else:
                print(f"✗ {method} {endpoint} is NOT defined")
                return False

        return True
    except Exception as e:
        print(f"✗ Endpoint check failed: {e}")
        return False

def test_auth_models():
    """Test auth_models functions"""
    print("\nTesting auth_models...")
    try:
        from auth_models import hash_password, verify_password

        # Test password hashing
        password = "test123"
        hashed = hash_password(password)

        if verify_password(password, hashed):
            print("✓ Password hashing and verification works")
        else:
            print("✗ Password verification failed")
            return False

        if not verify_password("wrong", hashed):
            print("✓ Password verification correctly rejects wrong password")
        else:
            print("✗ Password verification incorrectly accepted wrong password")
            return False

        return True
    except Exception as e:
        print(f"✗ Auth models test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing New Backend Features")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Endpoints", test_endpoints_defined()))
    results.append(("Auth Models", test_auth_models()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
