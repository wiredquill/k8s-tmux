#!/usr/bin/env python3
"""
Simple Demo Test Runner for k8s-tmux Application

This script provides a simple way to validate that the demo is working properly
and identify issues preventing full functionality. It combines both functional
and debugging tests in a user-friendly format.

Usage:
    python3 run_demo_tests.py                    # Run all tests
    python3 run_demo_tests.py --quick           # Run only quick connectivity tests
    python3 run_demo_tests.py --debug           # Run debugging tests with extra detail
    python3 run_demo_tests.py --no-browser      # Skip browser-based tests
    python3 run_demo_tests.py --url http://...  # Test different URL
"""

import sys
import os
import argparse
import time
import json
import subprocess
from pathlib import Path
import requests
from datetime import datetime

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our test modules
try:
    from test_functional import run_functional_tests, K8sTmuxTestConfig
    from test_demo_functionality import run_demo_debug_tests, DemoTestConfig
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    print("Make sure you're running from the tests directory")
    sys.exit(1)


class DemoTestRunner:
    """Main test runner for demo validation"""
    
    def __init__(self, args):
        self.args = args
        self.config = self._setup_config()
        self.results = {
            'connectivity': None,
            'api': None,
            'ui': None,
            'browser': None,
            'overall': None
        }
        
    def _setup_config(self):
        """Setup test configuration"""
        config = DemoTestConfig()
        if self.args.url:
            config.base_url = self.args.url.rstrip('/')
        return config
        
    def run_quick_validation(self):
        """Run quick validation tests"""
        print("🚀 K8S-TMUX DEMO QUICK VALIDATION")
        print("=" * 50)
        print(f"Target: {self.config.web_url}")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        # Test 1: Basic connectivity
        print("\n1️⃣ Testing Basic Connectivity...")
        connectivity_ok = self._test_basic_connectivity()
        self.results['connectivity'] = connectivity_ok
        
        if not connectivity_ok:
            print("❌ Basic connectivity failed - cannot proceed with other tests")
            return False
            
        # Test 2: API endpoints
        print("\n2️⃣ Testing API Endpoints...")
        api_ok = self._test_api_endpoints()
        self.results['api'] = api_ok
        
        # Test 3: UI content
        print("\n3️⃣ Testing UI Content...")
        ui_ok = self._test_ui_content()
        self.results['ui'] = ui_ok
        
        # Test 4: Browser functionality (if enabled)
        if not self.args.no_browser:
            print("\n4️⃣ Testing Browser Functionality...")
            browser_ok = self._test_browser_basic()
            self.results['browser'] = browser_ok
        else:
            print("\n4️⃣ Skipping Browser Tests (--no-browser)")
            self.results['browser'] = None
            
        # Summary
        self._print_quick_summary()
        
        # Overall result
        failed_tests = [k for k, v in self.results.items() if v is False]
        overall_ok = len(failed_tests) == 0
        self.results['overall'] = overall_ok
        
        return overall_ok
        
    def _test_basic_connectivity(self):
        """Test basic connectivity to the demo"""
        try:
            session = requests.Session()
            session.timeout = 10
            
            # Test web service
            print("  🔍 Testing web service...", end=" ")
            response = session.get(self.config.web_url)
            if response.status_code == 200:
                print("✅ OK")
            else:
                print(f"❌ HTTP {response.status_code}")
                return False
                
            # Test content size
            print("  🔍 Testing content size...", end=" ")
            if len(response.content) > 1000:
                print(f"✅ {len(response.content)} bytes")
            else:
                print(f"❌ Only {len(response.content)} bytes")
                return False
                
            # Test terminal port
            print("  🔍 Testing terminal port...", end=" ")
            import socket
            host = self.config.base_url.replace('http://', '').replace('https://', '')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            try:
                result = sock.connect_ex((host, self.config.terminal_port))
                if result == 0:
                    print("✅ Accessible")
                else:
                    print(f"❌ Connection failed")
                    return False
            finally:
                sock.close()
                
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    def _test_api_endpoints(self):
        """Test API endpoints"""
        session = requests.Session()
        session.timeout = 10
        
        endpoints_ok = 0
        total_endpoints = 0
        
        # Test /api/files (known to work)
        print("  🔍 Testing /api/files...", end=" ")
        total_endpoints += 1
        try:
            response = session.get(f"{self.config.web_url}/api/files")
            if response.status_code == 200:
                data = response.json()
                if 'files' in data:
                    files_count = len(data['files'])
                    print(f"✅ {files_count} files")
                    endpoints_ok += 1
                else:
                    print("❌ Invalid JSON structure")
            else:
                print(f"❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {e}")
            
        # Test /api/upload (check if exists)
        print("  🔍 Testing /api/upload...", end=" ")
        total_endpoints += 1
        try:
            response = session.post(f"{self.config.web_url}/api/upload")
            if response.status_code != 404:  # Endpoint exists
                print("✅ Endpoint exists")
                endpoints_ok += 1
            else:
                print("❌ Not found")
        except Exception as e:
            print(f"❌ {e}")
            
        # Test /api/send-command (check if exists)
        print("  🔍 Testing /api/send-command...", end=" ")
        total_endpoints += 1
        try:
            response = session.post(f"{self.config.web_url}/api/send-command")
            if response.status_code != 404:  # Endpoint exists
                print("✅ Endpoint exists")
                endpoints_ok += 1
            else:
                print("❌ Not found")
        except Exception as e:
            print(f"❌ {e}")
            
        return endpoints_ok >= 2  # At least 2/3 should work
        
    def _test_ui_content(self):
        """Test UI content"""
        try:
            session = requests.Session()
            response = session.get(self.config.web_url)
            content = response.text
            
            checks_ok = 0
            total_checks = 0
            
            # Check for key UI elements
            ui_elements = [
                ('AI Hacker Terminal', 'Page title'),
                ('terminal-frame', 'Terminal iframe'),
                ('file-browser', 'File browser'),
                ('drop-zone', 'Upload area'),
                ('<script>', 'JavaScript code'),
                ('loadFiles', 'loadFiles function'),
                (':7681', 'Terminal port config'),
            ]
            
            for element, description in ui_elements:
                print(f"  🔍 Checking {description}...", end=" ")
                total_checks += 1
                if element in content:
                    print("✅ Found")
                    checks_ok += 1
                else:
                    print("❌ Missing")
                    
            return checks_ok >= total_checks * 0.8  # At least 80% should be present
            
        except Exception as e:
            print(f"❌ Error checking UI: {e}")
            return False
            
    def _test_browser_basic(self):
        """Test basic browser functionality"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.implicitly_wait(5)
                
                print("  🔍 Loading page in browser...", end=" ")
                driver.get(self.config.web_url)
                
                # Wait for basic elements
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("✅ Loaded")
                
                # Check for JavaScript errors
                print("  🔍 Checking JavaScript errors...", end=" ")
                time.sleep(3)  # Let JS execute
                logs = driver.get_log('browser')
                errors = [log for log in logs if log['level'] == 'SEVERE']
                
                if len(errors) == 0:
                    print("✅ No errors")
                    return True
                else:
                    print(f"❌ {len(errors)} errors")
                    if self.args.debug:
                        for error in errors[:2]:  # Show first 2
                            print(f"      {error['message'][:80]}...")
                    return False
                    
            finally:
                if driver:
                    driver.quit()
                    
        except ImportError:
            print("  ⚠️ Selenium not available - skipping browser tests")
            return None
        except Exception as e:
            print(f"❌ Browser test error: {e}")
            return False
            
    def _print_quick_summary(self):
        """Print quick test summary"""
        print("\n" + "=" * 50)
        print("📊 QUICK VALIDATION RESULTS")
        print("=" * 50)
        
        status_icons = {True: "✅", False: "❌", None: "⚠️"}
        
        print(f"Connectivity:     {status_icons[self.results['connectivity']]} {'PASS' if self.results['connectivity'] else 'FAIL' if self.results['connectivity'] is False else 'SKIP'}")
        print(f"API Endpoints:    {status_icons[self.results['api']]} {'PASS' if self.results['api'] else 'FAIL' if self.results['api'] is False else 'SKIP'}")
        print(f"UI Content:       {status_icons[self.results['ui']]} {'PASS' if self.results['ui'] else 'FAIL' if self.results['ui'] is False else 'SKIP'}")
        print(f"Browser Functionality: {status_icons[self.results['browser']]} {'PASS' if self.results['browser'] else 'FAIL' if self.results['browser'] is False else 'SKIP'}")
        
    def run_full_tests(self):
        """Run comprehensive functional tests"""
        print("🔧 K8S-TMUX COMPREHENSIVE FUNCTIONAL TESTS")
        print("=" * 60)
        
        # Set environment variables for test configuration
        os.environ['K8S_TMUX_BASE_URL'] = self.config.base_url
        if self.args.no_browser:
            os.environ['HEADLESS'] = 'true'
            
        print(f"Target: {self.config.web_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Import and run functional tests
        from test_functional import run_functional_tests
        
        success = run_functional_tests()
        return success
        
    def run_debug_tests(self):
        """Run debugging-focused tests"""
        print("🔍 K8S-TMUX DEBUG TESTS")
        print("=" * 40)
        
        # Set environment for debugging
        os.environ['K8S_TMUX_BASE_URL'] = self.config.base_url
        
        from test_demo_functionality import run_demo_debug_tests
        
        success = run_demo_debug_tests()
        return success
        
    def generate_report(self):
        """Generate a test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_url': self.config.web_url,
            'test_type': 'quick' if self.args.quick else 'full',
            'results': self.results,
            'recommendations': []
        }
        
        # Generate recommendations
        if not self.results['connectivity']:
            report['recommendations'].append("Check if k8s-tmux service is running and accessible")
            report['recommendations'].append("Verify network connectivity to the target URL")
            
        if not self.results['api']:
            report['recommendations'].append("Check Python server logs for API endpoint errors")
            report['recommendations'].append("Verify NFS mounts are working properly")
            
        if not self.results['ui']:
            report['recommendations'].append("Check if HTML template is being served correctly")
            report['recommendations'].append("Verify JavaScript code is included in the response")
            
        if self.results['browser'] is False:
            report['recommendations'].append("JavaScript errors detected - check browser console")
            report['recommendations'].append("Run debugging tests for detailed JavaScript analysis")
            
        if not report['recommendations']:
            report['recommendations'].append("All basic tests passed - demo should be functional")
            
        # Save report
        report_file = Path(__file__).parent / f'demo_test_report_{int(time.time())}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Test report saved to: {report_file}")
        return report_file


def main():
    parser = argparse.ArgumentParser(
        description='Test runner for k8s-tmux demo validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_demo_tests.py                           # Quick validation
  python3 run_demo_tests.py --full                   # Comprehensive tests
  python3 run_demo_tests.py --debug                  # Debug-focused tests
  python3 run_demo_tests.py --quick --no-browser     # Quick tests without browser
  python3 run_demo_tests.py --url http://10.1.1.100  # Test different URL
        """
    )
    
    parser.add_argument('--url', 
                       help='Target URL (default: http://10.9.0.106)')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick validation tests only')
    parser.add_argument('--full', action='store_true',
                       help='Run comprehensive functional tests')
    parser.add_argument('--debug', action='store_true',
                       help='Run debugging-focused tests')
    parser.add_argument('--no-browser', action='store_true',
                       help='Skip browser-based tests')
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed test report')
                       
    args = parser.parse_args()
    
    # Default to quick if no specific test type specified
    if not any([args.quick, args.full, args.debug]):
        args.quick = True
        
    runner = DemoTestRunner(args)
    
    try:
        success = True
        
        if args.quick:
            success = runner.run_quick_validation()
        elif args.full:
            success = runner.run_full_tests() 
        elif args.debug:
            success = runner.run_debug_tests()
            
        if args.report:
            runner.generate_report()
            
        # Final summary
        print("\n" + "🎯 FINAL RESULT".center(50, "="))
        if success:
            print("✅ DEMO IS WORKING PROPERLY")
            print("All critical functionality validated successfully")
        else:
            print("❌ DEMO HAS ISSUES")
            print("Check the test output above for specific problems")
            print("Run with --debug for detailed analysis")
        print("=" * 50)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())