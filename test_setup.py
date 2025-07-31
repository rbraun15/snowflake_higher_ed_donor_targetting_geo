#!/usr/bin/env python3
"""
Test script to verify the Higher Ed Alumni Targeting Demo setup.
This script tests key dependencies and connections before running the main application.
"""

import sys
import importlib
import pandas as pd

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - FAILED: {e}")
        return False

def test_h3_functionality():
    """Test H3 library functionality"""
    try:
        import h3
        # Test basic H3 functionality
        lat, lon = 34.8526, -82.3940  # Greenville, SC coordinates
        h3_7 = h3.geo_to_h3(lat, lon, 7)
        h3_8 = h3.geo_to_h3(lat, lon, 8)
        h3_9 = h3.geo_to_h3(lat, lon, 9)
        
        # Test boundary calculation
        try:
            boundary = h3.h3_to_geo_boundary(h3_8)
            print(f"✅ H3 functionality - OK")
            print(f"   Sample H3 indices: {h3_7[:8]}..., {h3_8[:8]}..., {h3_9[:8]}...")
            return True
        except:
            try:
                boundary = h3.h3_to_geo_boundary(h3_8, geo_json=True)
                print(f"✅ H3 functionality (legacy API) - OK")
                return True
            except Exception as e:
                print(f"❌ H3 boundary calculation - FAILED: {e}")
                return False
    except Exception as e:
        print(f"❌ H3 functionality test - FAILED: {e}")
        return False

def test_snowflake_connection():
    """Test Snowflake connection (if secrets are configured)"""
    try:
        import streamlit as st
        from pathlib import Path
        
        secrets_path = Path(".streamlit/secrets.toml")
        if not secrets_path.exists():
            print("⚠️  Snowflake connection - SKIPPED (no secrets.toml found)")
            print("   Create .streamlit/secrets.toml from template to test connection")
            return True
        
        # Try to load secrets
        try:
            import toml
            secrets = toml.load(secrets_path)
            if 'snowflake' in secrets:
                print("✅ Snowflake secrets found - OK")
                print("   Run the main application to test actual connection")
            else:
                print("⚠️  Snowflake secrets - Missing [snowflake] section")
            return True
        except ImportError:
            print("⚠️  TOML parser not available - install with: pip install toml")
            return True
            
    except Exception as e:
        print(f"❌ Snowflake connection test - FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Higher Ed Alumni Targeting Demo Setup\n")
    
    # Test core dependencies
    print("📦 Testing Core Dependencies:")
    results = []
    
    # Core packages
    results.append(test_import("streamlit"))
    results.append(test_import("pandas"))
    results.append(test_import("plotly.express", "plotly"))
    results.append(test_import("numpy"))
    results.append(test_import("h3"))
    results.append(test_import("folium"))
    results.append(test_import("streamlit_folium"))
    
    # Snowflake packages
    results.append(test_import("snowflake.connector", "snowflake-connector-python"))
    
    # Visualization packages
    results.append(test_import("matplotlib"))
    results.append(test_import("seaborn"))
    
    print(f"\n🧪 Testing Functionality:")
    results.append(test_h3_functionality())
    results.append(test_snowflake_connection())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the demo.")
        print("   Next steps:")
        print("   1. Set up Snowflake database with provided SQL scripts")
        print("   2. Configure .streamlit/secrets.toml with your credentials")
        print("   3. Run: streamlit run streamlit_app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 