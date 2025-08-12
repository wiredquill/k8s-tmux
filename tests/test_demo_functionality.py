#!/usr/bin/env python3
"""
Demo-Specific Functionality Tests for k8s-tmux

This test suite focuses specifically on identifying why the demo might not be working:
- JavaScript console error detection
- API endpoint connectivity tests  
- Terminal iframe connection tests
- File browser loading tests
- Debug information collection

Based on the issue description:
- Application is deployed and accessible at http://10.9.0.106
- Backend Python server is working (HTML loads, API responds)
- File browser API returns correct JSON
- Issue appears to be JavaScript frontend not working properly

Run with: python3 test_demo_functionality.py
"""

import unittest
import requests
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import socket
from urllib.parse import urlparse, urljoin


class DemoTestConfig:
    """Configuration specific to demo testing"""
    
    def __init__(self):
        self.base_url = "http://10.9.0.106"  # Known demo URL
        self.terminal_port = 7681
        self.web_port = 80
        self.timeout = 15
        
    @property
    def web_url(self):
        return self.base_url
        
    @property
    def terminal_url(self):
        return f"{self.base_url.replace('http://', '')}:{self.terminal_port}"


class DemoConnectivityTest(unittest.TestCase):
    """Test basic demo connectivity"""
    
    def setUp(self):
        self.config = DemoTestConfig()
        self.session = requests.Session()
        self.session.timeout = 10
        
    def test_demo_server_accessible(self):
        """Test that demo server is accessible"""
        print(f"\n🔍 Testing connectivity to {self.config.web_url}")
        
        try:
            response = self.session.get(self.config.web_url)
            print(f"✅ Server responds with status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('content-type')}")
            print(f"✅ Content-Length: {len(response.content)} bytes")
            
            self.assertEqual(response.status_code, 200)
            self.assertGreater(len(response.content), 1000)  # Should have substantial content
            
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ Cannot connect to demo server: {e}")
            
    def test_terminal_port_connectivity(self):
        """Test terminal port connectivity"""
        print(f"\n🔍 Testing terminal port {self.config.terminal_port}")
        
        host = self.config.base_url.replace('http://', '')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((host, self.config.terminal_port))
            if result == 0:
                print(f"✅ Terminal port {self.config.terminal_port} is accessible")
            else:
                print(f"❌ Terminal port {self.config.terminal_port} not accessible (code: {result})")
                self.fail(f"Terminal port not accessible")
        finally:
            sock.close()
            
    def test_known_api_endpoints(self):
        """Test the known working API endpoints"""
        print(f"\n🔍 Testing API endpoints")
        
        endpoints_to_test = [
            ('/api/files', 'File browser API'),
            ('/api/upload', 'File upload API'),
            ('/api/send-command', 'Command sending API'),
            ('/api/test-ntfy', 'NTFY test API'),
        ]
        
        for endpoint, description in endpoints_to_test:
            url = urljoin(self.config.web_url, endpoint)
            try:
                # Use HEAD request first to check if endpoint exists
                response = self.session.head(url, timeout=5)
                if response.status_code == 405:  # Method not allowed - endpoint exists
                    print(f"✅ {description} endpoint exists")
                elif response.status_code == 404:
                    print(f"❌ {description} endpoint missing")
                else:
                    print(f"✅ {description} responds with: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {description} error: {e}")


class DemoAPIFunctionalityTest(unittest.TestCase):
    """Test specific API functionality that should be working"""
    
    def setUp(self):
        self.config = DemoTestConfig()
        self.session = requests.Session()
        self.session.timeout = 10
        
    def test_files_api_detailed(self):
        """Detailed test of /api/files endpoint (known to be working)"""
        print(f"\n🔍 Testing /api/files endpoint in detail")
        
        url = f"{self.config.web_url}/api/files"
        try:
            response = self.session.get(url)
            print(f"✅ Files API status: {response.status_code}")
            print(f"✅ Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON parsing successful")
                    print(f"✅ Response structure: {list(data.keys())}")
                    
                    if 'files' in data:
                        files = data['files']
                        print(f"✅ Files array length: {len(files)}")
                        
                        if files:
                            print(f"✅ Sample file entry: {files[0]}")
                            
                            # Validate known directories exist
                            file_names = [f.get('name', '') for f in files]
                            print(f"✅ File names found: {file_names}")
                            
                            expected = ['k8s-tmux', 'WiredQuill'] 
                            found = [name for name in expected if name in file_names]
                            print(f"✅ Expected directories found: {found}")
                            
                        self.assertIsInstance(files, list)
                    else:
                        print(f"❌ No 'files' key in response: {data}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"Raw response: {response.text[:500]}...")
                    self.fail("Files API returned invalid JSON")
            else:
                print(f"❌ Files API returned status {response.status_code}")
                print(f"Response text: {response.text[:300]}")
                
        except Exception as e:
            self.fail(f"Files API test failed: {e}")
            
    def test_files_api_with_path(self):
        """Test /api/files with path parameter"""
        print(f"\n🔍 Testing /api/files with path parameter")
        
        # First get root files
        response = self.session.get(f"{self.config.web_url}/api/files")
        if response.status_code == 200:
            data = response.json()
            dirs = [f for f in data.get('files', []) if f.get('type') == 'dir']
            
            if dirs:
                test_dir = dirs[0]['name']
                print(f"✅ Testing path navigation to: {test_dir}")
                
                # Test path parameter
                path_url = f"{self.config.web_url}/api/files?path={test_dir}"
                path_response = self.session.get(path_url)
                
                print(f"✅ Path API status: {path_response.status_code}")
                if path_response.status_code == 200:
                    path_data = path_response.json()
                    print(f"✅ Path response structure: {list(path_data.keys())}")
                else:
                    print(f"❌ Path API failed: {path_response.text[:200]}")
            else:
                print("⚠️ No directories found to test path navigation")
                
    def test_command_api_basic(self):
        """Test basic command API functionality"""
        print(f"\n🔍 Testing /api/send-command endpoint")
        
        test_command = {
            'command': 'echo "Demo test command"'
        }
        
        try:
            response = self.session.post(
                f"{self.config.web_url}/api/send-command",
                json=test_command,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"✅ Command API status: {response.status_code}")
            print(f"✅ Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Command response: {data}")
                    self.assertIn('success', data)
                except json.JSONDecodeError:
                    print(f"❌ Command API returned non-JSON: {response.text}")
            else:
                print(f"❌ Command API error: {response.text[:300]}")
                
        except Exception as e:
            print(f"❌ Command API test failed: {e}")


class DemoJavaScriptDebugTest(unittest.TestCase):
    """Test JavaScript functionality and debug issues"""
    
    def setUp(self):
        self.config = DemoTestConfig()
        self.driver = None
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')  # Capture all logs
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
        except Exception as e:
            print(f"⚠️ WebDriver not available: {e}")
            
    def tearDown(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
                
    def test_page_loads_completely(self):
        """Test that the page loads completely"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Testing complete page load")
        
        self.driver.get(self.config.web_url)
        
        # Wait and check basic page structure
        try:
            # Wait for basic elements
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ Page body loaded")
            
            # Check for main container
            container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cyber-container"))
            )
            print("✅ Main container found")
            
            # Check page title
            title = self.driver.title
            print(f"✅ Page title: {title}")
            self.assertIn('AI Hacker Terminal', title)
            
        except TimeoutException:
            print("❌ Page failed to load basic elements")
            self.fail("Page did not load completely")
            
    def test_javascript_console_errors(self):
        """Check for JavaScript console errors"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Checking JavaScript console for errors")
        
        self.driver.get(self.config.web_url)
        time.sleep(5)  # Allow JavaScript to execute
        
        try:
            # Get browser logs
            logs = self.driver.get_log('browser')
            
            print(f"✅ Total console entries: {len(logs)}")
            
            # Categorize logs
            errors = [log for log in logs if log['level'] == 'SEVERE']
            warnings = [log for log in logs if log['level'] == 'WARNING']
            info = [log for log in logs if log['level'] == 'INFO']
            
            print(f"✅ Errors: {len(errors)}, Warnings: {len(warnings)}, Info: {len(info)}")
            
            # Print all errors
            if errors:
                print("\n❌ JAVASCRIPT ERRORS DETECTED:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error['message']}")
                    print(f"     Level: {error['level']}, Source: {error.get('source', 'unknown')}")
                    
                # Check for specific error patterns that would break functionality
                critical_patterns = [
                    'cannot read property',
                    'is not defined',
                    'failed to fetch',
                    'network error',
                    'syntax error',
                    'unexpected token'
                ]
                
                critical_errors = []
                for error in errors:
                    message = error['message'].lower()
                    for pattern in critical_patterns:
                        if pattern in message:
                            critical_errors.append(f"CRITICAL: {error['message']}")
                            break
                            
                if critical_errors:
                    print(f"\n🚨 CRITICAL ERRORS THAT BREAK FUNCTIONALITY:")
                    for error in critical_errors:
                        print(f"  • {error}")
                        
            else:
                print("✅ No JavaScript errors detected")
                
            # Print warnings for context
            if warnings:
                print(f"\n⚠️ JavaScript warnings ({len(warnings)}):")
                for warning in warnings[:3]:  # Show first 3
                    print(f"  • {warning['message']}")
                if len(warnings) > 3:
                    print(f"  • ... and {len(warnings) - 3} more warnings")
                    
        except Exception as e:
            print(f"❌ Could not retrieve console logs: {e}")
            
    def test_javascript_functions_exist(self):
        """Test that expected JavaScript functions exist"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Testing JavaScript function availability")
        
        self.driver.get(self.config.web_url)
        time.sleep(3)  # Allow JavaScript to load
        
        # List of expected JavaScript functions
        expected_functions = [
            'loadFiles',
            'refreshFiles', 
            'handleFileClick',
            'downloadFile',
            'cycleTheme',
            'changeTitle',
            'toggleRemote',
            'scheduleMessage',
            'testRemote',
            'toggleFullscreen',
            'uploadFiles'
        ]
        
        function_results = {}
        for func_name in expected_functions:
            try:
                result = self.driver.execute_script(f"return typeof {func_name};")
                function_results[func_name] = result
                
                if result == 'function':
                    print(f"✅ Function {func_name}: Available")
                else:
                    print(f"❌ Function {func_name}: {result}")
                    
            except Exception as e:
                print(f"❌ Function {func_name}: Error - {e}")
                function_results[func_name] = f"Error: {e}"
                
        # Check if critical functions are missing
        missing_critical = [name for name, result in function_results.items() 
                          if result != 'function' and name in ['loadFiles', 'refreshFiles']]
                          
        if missing_critical:
            self.fail(f"Critical JavaScript functions missing: {missing_critical}")
            
    def test_file_browser_loading_process(self):
        """Test the file browser loading process in detail"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Testing file browser loading process")
        
        self.driver.get(self.config.web_url)
        
        try:
            # Find file browser element
            file_browser = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "fileBrowser"))
            )
            print("✅ File browser element found")
            
            # Check initial state
            initial_content = file_browser.text
            print(f"✅ Initial file browser content: '{initial_content.strip()}'")
            
            # Wait for content to load (should change from "Loading...")
            max_wait = 15
            for i in range(max_wait):
                current_content = file_browser.text.strip()
                print(f"✅ File browser content (t+{i}s): '{current_content}'")
                
                if current_content and current_content != "Loading...":
                    print(f"✅ File browser loaded successfully after {i}s")
                    break
                    
                time.sleep(1)
            else:
                print(f"❌ File browser still showing '{current_content}' after {max_wait}s")
                self.fail("File browser failed to load content")
                
            # Test the loadFiles function directly
            print(f"\n🔍 Testing loadFiles() function directly")
            try:
                # Call loadFiles function
                self.driver.execute_script("loadFiles();")
                print("✅ loadFiles() executed without error")
                
                # Wait a moment for it to process
                time.sleep(2)
                
                # Check if content changed
                new_content = file_browser.text.strip()
                print(f"✅ File browser content after loadFiles(): '{new_content}'")
                
            except Exception as e:
                print(f"❌ Error calling loadFiles(): {e}")
                
        except TimeoutException:
            print("❌ File browser element not found")
            self.fail("File browser element not found")
            
    def test_terminal_iframe_setup(self):
        """Test terminal iframe setup and configuration"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Testing terminal iframe setup")
        
        self.driver.get(self.config.web_url)
        
        try:
            # Find terminal iframe
            terminal_frame = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "terminalFrame"))
            )
            print("✅ Terminal iframe found")
            
            # Check iframe attributes
            src = terminal_frame.get_attribute("src")
            print(f"✅ Terminal iframe src: {src}")
            
            if src:
                expected_port = str(self.config.terminal_port)
                if expected_port in src:
                    print(f"✅ Terminal iframe correctly configured for port {expected_port}")
                else:
                    print(f"❌ Terminal iframe not using expected port {expected_port}")
            else:
                print(f"❌ Terminal iframe has no src attribute")
                self.fail("Terminal iframe not configured")
                
            # Test if iframe src is set by JavaScript
            print(f"\n🔍 Testing JavaScript iframe configuration")
            script_result = self.driver.execute_script("""
                var iframe = document.getElementById('terminalFrame');
                return {
                    src: iframe.src,
                    hostname: window.location.hostname,
                    expected: 'http://' + window.location.hostname + ':7681'
                };
            """)
            
            print(f"✅ JavaScript iframe config: {script_result}")
            
        except TimeoutException:
            print("❌ Terminal iframe not found")
            self.fail("Terminal iframe not found")
            
    def test_api_call_from_javascript(self):
        """Test API calls made from JavaScript"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        print(f"\n🔍 Testing JavaScript API calls")
        
        self.driver.get(self.config.web_url)
        time.sleep(3)  # Let page load
        
        # Test fetch API availability
        try:
            fetch_available = self.driver.execute_script("return typeof fetch;")
            print(f"✅ Fetch API availability: {fetch_available}")
            
            if fetch_available == 'function':
                # Test actual API call from JavaScript
                print(f"\n🔍 Testing fetch('/api/files') from JavaScript")
                
                api_test_script = """
                return fetch('/api/files')
                    .then(response => response.json())
                    .then(data => {
                        return {
                            success: true,
                            filesCount: data.files ? data.files.length : 0,
                            hasFiles: !!data.files,
                            keys: Object.keys(data)
                        };
                    })
                    .catch(error => {
                        return {
                            success: false,
                            error: error.toString()
                        };
                    });
                """
                
                # Execute async JavaScript
                result = self.driver.execute_async_script("""
                    var callback = arguments[arguments.length - 1];
                    """ + api_test_script.replace('return ', 'callback(') + """;
                """)
                
                print(f"✅ JavaScript API call result: {result}")
                
                if result.get('success'):
                    print(f"✅ JavaScript successfully called /api/files")
                    print(f"✅ Files count: {result.get('filesCount')}")
                else:
                    print(f"❌ JavaScript API call failed: {result.get('error')}")
                    
            else:
                print(f"❌ Fetch API not available in browser")
                
        except Exception as e:
            print(f"❌ Error testing JavaScript API calls: {e}")


class DemoNetworkDebugTest(unittest.TestCase):
    """Test network-related issues that might affect the demo"""
    
    def setUp(self):
        self.config = DemoTestConfig()
        self.session = requests.Session()
        
    def test_cors_headers(self):
        """Test for CORS issues"""
        print(f"\n🔍 Testing CORS headers")
        
        # Test main page
        response = self.session.get(self.config.web_url)
        headers = response.headers
        
        cors_headers = {
            'Access-Control-Allow-Origin': headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': headers.get('Access-Control-Allow-Headers'),
        }
        
        print(f"✅ CORS headers: {cors_headers}")
        
        # Test API endpoint
        api_response = self.session.get(f"{self.config.web_url}/api/files")
        api_cors = {
            'Access-Control-Allow-Origin': api_response.headers.get('Access-Control-Allow-Origin'),
        }
        
        print(f"✅ API CORS headers: {api_cors}")
        
    def test_content_security_policy(self):
        """Test for Content Security Policy issues"""
        print(f"\n🔍 Testing Content Security Policy")
        
        response = self.session.get(self.config.web_url)
        csp = response.headers.get('Content-Security-Policy')
        
        if csp:
            print(f"✅ CSP header found: {csp}")
            
            # Check if CSP might block iframe
            if 'frame-src' in csp and 'none' in csp:
                print(f"❌ CSP might block iframe loading")
        else:
            print(f"✅ No CSP header (should not block functionality)")
            
    def test_response_encoding(self):
        """Test response encoding issues"""
        print(f"\n🔍 Testing response encoding")
        
        response = self.session.get(self.config.web_url)
        
        encoding = response.encoding
        content_type = response.headers.get('content-type', '')
        
        print(f"✅ Response encoding: {encoding}")
        print(f"✅ Content-Type header: {content_type}")
        
        # Check if content is properly UTF-8
        try:
            content = response.text
            print(f"✅ Content decoded successfully ({len(content)} characters)")
        except UnicodeDecodeError as e:
            print(f"❌ Unicode decode error: {e}")


def run_demo_debug_tests():
    """Run all demo debugging tests"""
    print("🔧 K8S-TMUX DEMO DEBUGGING TEST SUITE")
    print("=" * 60)
    print(f"Target: {DemoTestConfig().web_url}")
    print("Focus: JavaScript issues and API connectivity")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in order of importance
    test_classes = [
        DemoConnectivityTest,        # Basic connectivity first
        DemoAPIFunctionalityTest,    # API functionality (known working)
        DemoJavaScriptDebugTest,     # JavaScript issues (suspected problem)
        DemoNetworkDebugTest,        # Network configuration issues
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run with maximum verbosity for debugging
    runner = unittest.TextTestRunner(verbosity=2, buffer=False, stream=None)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 DEMO DEBUGGING SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"Tests run: {total_tests}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, error in result.failures:
            test_name = f"{test.__class__.__name__}.{test._testMethodName}"
            print(f"  • {test_name}")
            
    if result.errors:
        print(f"\n🚫 ERRORS ({len(result.errors)}):")
        for test, error in result.errors:
            test_name = f"{test.__class__.__name__}.{test._testMethodName}"
            print(f"  • {test_name}")
            
    # Recommendations
    print(f"\n💡 DEBUGGING RECOMMENDATIONS:")
    if failures + errors == 0:
        print("  ✅ All basic tests passed - demo should be working")
    else:
        print("  🔍 Check the detailed test output above for specific issues")
        print("  🔍 Focus on JavaScript console errors if UI not working")
        print("  🔍 Verify API endpoints if data not loading")
        print("  🔍 Check network connectivity if requests failing")
    
    return failures + errors == 0


if __name__ == '__main__':
    success = run_demo_debug_tests()
    exit(0 if success else 1)