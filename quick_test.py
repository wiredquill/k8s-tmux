#!/usr/bin/env python3
"""
Quick test to simulate what the browser JavaScript should be doing
"""
import requests
import json

def test_api_endpoints():
    base_url = "http://10.9.0.106"
    
    print("🔍 Testing k8s-tmux Demo Functionality")
    print("=" * 50)
    
    # Test 1: Main page loads
    print("1. Testing main page...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Main page loads successfully")
            if "Loading files..." in response.text:
                print("   📝 Found 'Loading files...' placeholder")
            if "loadFiles(" in response.text:
                print("   📝 Found loadFiles JavaScript function")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Main page error: {e}")
    
    # Test 2: File browser API
    print("\n2. Testing file browser API...")
    try:
        response = requests.get(f"{base_url}/api/files", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ File browser API responds")
            print(f"   📂 Found {len(data.get('files', []))} items:")
            for file in data.get('files', []):
                print(f"      - {file['name']} ({file['type']})")
        else:
            print(f"   ❌ File browser API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ File browser API error: {e}")
    
    # Test 3: Terminal redirect
    print("\n3. Testing terminal redirect...")
    try:
        response = requests.get(f"{base_url}/terminal", timeout=5, allow_redirects=False)
        if response.status_code == 302:
            print("   ✅ Terminal redirect working")
            print(f"   🔗 Redirects to: {response.headers.get('Location')}")
        else:
            print(f"   ❌ Terminal redirect failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Terminal redirect error: {e}")
    
    # Test 4: Direct terminal access
    print("\n4. Testing direct terminal access...")
    try:
        response = requests.get("http://10.9.0.106:7681", timeout=5)
        if response.status_code == 200:
            print("   ✅ Direct terminal access works")
        else:
            print(f"   ❌ Direct terminal failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Direct terminal error: {e}")
    
    # Test 5: MQTT test endpoint
    print("\n5. Testing MQTT endpoint...")
    try:
        response = requests.post(f"{base_url}/api/test-mqtt", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ MQTT endpoint responds")
            print(f"   📡 Status: {data.get('status')}")
            print(f"   💬 Message: {data.get('message')}")
        else:
            print(f"   ❌ MQTT endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ MQTT endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS:")
    print("If all APIs work but browser shows 'Loading files...', the issue is likely:")
    print("1. JavaScript not executing (console errors)")
    print("2. CORS issues preventing fetch() calls")
    print("3. Content-Security-Policy blocking scripts")
    print("4. Network connectivity from browser to server")
    print("\n💡 Recommended: Check browser console for JavaScript errors")

if __name__ == "__main__":
    test_api_endpoints()