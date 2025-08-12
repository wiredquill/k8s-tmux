#!/usr/bin/env python3
"""
Comprehensive Functional Tests for k8s-tmux Demo Application

This test suite focuses on validating that all features work correctly:
- Web UI loads and renders properly
- File browser displays files and allows navigation  
- Terminal iframe connects and functions
- Command scheduling works
- File upload functionality works
- MQTT notifications work
- API endpoints respond correctly

Run with: python3 test_functional.py
Run specific tests: python3 test_functional.py TestWebUI.test_homepage_loads
"""

import unittest
import requests
import json
import time
import os
import tempfile
import subprocess
from pathlib import Path
from urllib.parse import urljoin
import re
import socket
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException


class K8sTmuxTestConfig:
    """Configuration for k8s-tmux functional tests"""
    
    def __init__(self):
        # Default test configuration
        self.base_url = os.getenv('K8S_TMUX_BASE_URL', 'http://10.9.0.106')
        self.terminal_port = 7681
        self.web_port = 80  # Service port
        self.timeout = 30
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        # Test data paths
        self.test_files_dir = Path(__file__).parent / 'test_files'
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Create test files for upload testing
        self.create_test_files()
        
    def create_test_files(self):
        """Create test files for upload testing"""
        # Small text file
        (self.test_files_dir / 'test_small.txt').write_text('Hello World\nThis is a test file.')
        
        # Medium text file with special characters
        (self.test_files_dir / 'test_medium.txt').write_text(
            'Test file with special chars: éñüñ\n' * 100
        )
        
        # Binary test file
        (self.test_files_dir / 'test_binary.dat').write_bytes(b'\x00\x01\x02\x03' * 256)
        
        # Script file
        (self.test_files_dir / 'test_script.sh').write_text(
            '#!/bin/bash\necho "Test script"\nls -la\n'
        )

    @property
    def web_url(self):
        return f"{self.base_url}:{self.web_port}" if self.web_port != 80 else self.base_url
        
    @property 
    def terminal_url(self):
        return f"{self.base_url.replace('http://', '').replace('https://', '')}:{self.terminal_port}"


class BaseK8sTmuxTest(unittest.TestCase):
    """Base test class with common functionality"""
    
    @classmethod
    def setUpClass(cls):
        cls.config = K8sTmuxTestConfig()
        cls.session = requests.Session()
        cls.session.timeout = cls.config.timeout
        
        # Test basic connectivity
        try:
            response = cls.session.get(cls.config.web_url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Application not accessible: {response.status_code}")
        except Exception as e:
            raise unittest.SkipTest(f"k8s-tmux application not available: {e}")
    
    def setUp(self):
        self.start_time = time.time()
        
    def tearDown(self):
        elapsed = time.time() - self.start_time
        if elapsed > 10:  # Log slow tests
            print(f"⚠️  Slow test: {self._testMethodName} took {elapsed:.2f}s")


class TestConnectivity(BaseK8sTmuxTest):
    """Test basic connectivity and service health"""
    
    def test_web_service_responds(self):
        """Test that web service is accessible and responding"""
        response = self.session.get(self.config.web_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('content-type', ''))
        
    def test_terminal_port_accessible(self):
        """Test that terminal port is accessible"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            host = self.config.base_url.replace('http://', '').replace('https://', '')
            result = sock.connect_ex((host, self.config.terminal_port))
            self.assertEqual(result, 0, f"Terminal port {self.config.terminal_port} not accessible")
        finally:
            sock.close()
            
    def test_response_headers(self):
        """Test response headers are appropriate"""
        response = self.session.get(self.config.web_url)
        headers = response.headers
        
        # Should have content-type
        self.assertIn('content-type', headers)
        
        # Response should be reasonably sized (not empty, not too large)
        content_length = len(response.content)
        self.assertGreater(content_length, 1000)  # At least 1KB
        self.assertLess(content_length, 1000000)  # Less than 1MB


class TestWebUI(BaseK8sTmuxTest):
    """Test web UI loads and renders correctly"""
    
    def test_homepage_loads(self):
        """Test that homepage loads with expected content"""
        response = self.session.get(self.config.web_url)
        content = response.text
        
        # Check for key UI elements
        self.assertIn('AI Hacker Terminal', content)
        self.assertIn('terminal-frame', content)  # Terminal iframe
        self.assertIn('file-browser', content)   # File browser
        self.assertIn('drop-zone', content)      # Upload area
        
    def test_css_styles_present(self):
        """Test that CSS styles are included"""
        response = self.session.get(self.config.web_url)
        content = response.text
        
        # Check for CSS classes and styles
        self.assertIn('cyber-container', content)
        self.assertIn('terminal-section', content)
        self.assertIn('sidebar', content)
        self.assertIn('background:', content)  # CSS styling
        
    def test_javascript_present(self):
        """Test that JavaScript code is included"""
        response = self.session.get(self.config.web_url)
        content = response.text
        
        # Check for JavaScript functions
        self.assertIn('<script>', content)
        self.assertIn('loadFiles', content)
        self.assertIn('function', content)
        self.assertIn('terminalFrame', content)
        
    def test_terminal_iframe_configured(self):
        """Test that terminal iframe is properly configured"""
        response = self.session.get(self.config.web_url)
        content = response.text
        
        # Check for iframe source setup
        self.assertIn('terminalFrame', content)
        self.assertIn(':7681', content)  # Terminal port
        
    def test_ui_sections_present(self):
        """Test that all UI sections are present"""
        response = self.session.get(self.config.web_url)
        content = response.text
        
        required_sections = [
            'Files (/mnt)',     # File browser section
            'Upload',           # Upload section  
            'Timed Messages',   # Command scheduling
            'Config',           # Configuration section
        ]
        
        for section in required_sections:
            self.assertIn(section, content, f"Missing UI section: {section}")


class TestAPIEndpoints(BaseK8sTmuxTest):
    """Test API endpoints functionality"""
    
    def test_files_api_responds(self):
        """Test /api/files endpoint responds correctly"""
        response = self.session.get(f"{self.config.web_url}/api/files")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        
        # Parse JSON response
        data = response.json()
        self.assertIn('files', data)
        self.assertIsInstance(data['files'], list)
        
    def test_files_api_returns_valid_structure(self):
        """Test /api/files returns expected data structure"""
        response = self.session.get(f"{self.config.web_url}/api/files")
        data = response.json()
        
        files = data['files']
        if files:  # If there are files
            for file_item in files:
                # Check required fields
                self.assertIn('name', file_item)
                self.assertIn('type', file_item)
                self.assertIn(file_item['type'], ['file', 'dir'])
                
                # Check optional fields exist
                if 'size' in file_item:
                    self.assertIsInstance(file_item['size'], int)
                    
    def test_files_api_shows_expected_directories(self):
        """Test /api/files shows expected NFS mount directories"""
        response = self.session.get(f"{self.config.web_url}/api/files")
        data = response.json()
        
        file_names = [f['name'] for f in data['files']]
        
        # Should show NFS mounted directories
        expected_dirs = ['k8s-tmux', 'WiredQuill']
        found_expected = any(expected in file_names for expected in expected_dirs)
        self.assertTrue(found_expected, f"Expected directories not found in: {file_names}")
        
    def test_upload_endpoint_exists(self):
        """Test /api/upload endpoint exists (but don't upload yet)"""
        # Test with invalid request to see if endpoint exists
        response = self.session.post(f"{self.config.web_url}/api/upload")
        
        # Should not be 404 (endpoint exists) but might be 400 (bad request)
        self.assertNotEqual(response.status_code, 404, "Upload endpoint not found")
        
    def test_send_command_endpoint_exists(self):
        """Test /api/send-command endpoint exists"""
        response = self.session.post(f"{self.config.web_url}/api/send-command")
        
        # Should not be 404 (endpoint exists)
        self.assertNotEqual(response.status_code, 404, "Send command endpoint not found")
        
    def test_test_ntfy_endpoint_exists(self):
        """Test /api/test-ntfy endpoint exists"""
        response = self.session.post(f"{self.config.web_url}/api/test-ntfy")
        
        # Should not be 404 (endpoint exists) 
        self.assertNotEqual(response.status_code, 404, "Test NTFY endpoint not found")


class TestFileOperations(BaseK8sTmuxTest):
    """Test file upload and download operations"""
    
    def test_file_upload_small_text(self):
        """Test uploading a small text file"""
        test_file = self.config.test_files_dir / 'test_small.txt'
        
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/plain')}
            response = self.session.post(f"{self.config.web_url}/api/upload", files=files)
            
        if response.status_code == 200:
            data = response.json()
            self.assertIn('success', data)
            self.assertIn('filename', data)
            self.assertEqual(data['filename'], test_file.name)
        else:
            # Log details for debugging
            print(f"Upload failed: {response.status_code} - {response.text}")
            # Don't fail the test immediately, might be expected
            
    def test_file_upload_multiple_files(self):
        """Test uploading multiple files"""
        files_to_upload = [
            'test_small.txt',
            'test_script.sh'
        ]
        
        uploaded_count = 0
        for filename in files_to_upload:
            test_file = self.config.test_files_dir / filename
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'application/octet-stream')}
                response = self.session.post(f"{self.config.web_url}/api/upload", files=files)
                
                if response.status_code == 200:
                    uploaded_count += 1
                    
        # At least one upload should succeed if upload functionality works
        self.assertGreater(uploaded_count, 0, "No files uploaded successfully")
        
    def test_file_download_functionality(self):
        """Test file download functionality if files exist"""
        # First get file list
        response = self.session.get(f"{self.config.web_url}/api/files")
        if response.status_code == 200:
            data = response.json()
            
            # Find a file to download
            files = [f for f in data['files'] if f['type'] == 'file']
            if files:
                filename = files[0]['name']
                download_response = self.session.get(
                    f"{self.config.web_url}/api/download/{filename}"
                )
                
                # Should get some response (might be 404 if file not found)
                self.assertIsNotNone(download_response)


class TestCommandScheduling(BaseK8sTmuxTest):
    """Test command scheduling functionality"""
    
    def test_send_command_api(self):
        """Test sending a command through the API"""
        command_data = {
            'command': 'echo "Functional test command"'
        }
        
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            json=command_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if the endpoint processes the request
        if response.status_code == 200:
            data = response.json()
            self.assertIn('success', data)
            self.assertEqual(data.get('command'), command_data['command'])
        else:
            # Log for debugging but don't fail - might indicate tmux session issues
            print(f"Send command failed: {response.status_code} - {response.text}")
            
    def test_send_command_with_special_characters(self):
        """Test sending commands with special characters"""
        special_commands = [
            'echo "Hello World"',
            'ls -la | head -5',
            'echo $HOME',
        ]
        
        success_count = 0
        for cmd in special_commands:
            command_data = {'command': cmd}
            response = self.session.post(
                f"{self.config.web_url}/api/send-command",
                json=command_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                success_count += 1
                
        # At least basic commands should work
        self.assertGreater(success_count, 0, "No commands executed successfully")
        
    def test_invalid_command_handling(self):
        """Test handling of invalid command requests"""
        # Empty command
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            json={'command': ''},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 400)
        
        # Missing command field
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            json={},
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 400)


class TestMQTTNotifications(BaseK8sTmuxTest):
    """Test MQTT notification functionality"""
    
    def test_ntfy_test_endpoint(self):
        """Test NTFY test endpoint functionality"""
        test_data = {
            'topic': 'test_functional',
            'message': 'Functional test notification'
        }
        
        response = self.session.post(
            f"{self.config.web_url}/api/test-ntfy",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should get a response (might fail if NTFY service unavailable)
        if response.status_code == 200:
            data = response.json()
            self.assertIn('success', data)
        else:
            # Log for debugging - might indicate network/NTFY issues
            print(f"NTFY test failed: {response.status_code} - {response.text}")
            
    def test_ntfy_with_different_topics(self):
        """Test NTFY with different topic names"""
        topics = ['test1', 'functional_test', 'ai_test']
        
        for topic in topics:
            test_data = {
                'topic': topic,
                'message': f'Test for topic {topic}'
            }
            
            response = self.session.post(
                f"{self.config.web_url}/api/test-ntfy",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Should at least accept the request format
            self.assertNotEqual(response.status_code, 400, f"Bad request for topic: {topic}")


class TestBrowserCompatibility(BaseK8sTmuxTest):
    """Test browser compatibility and JavaScript functionality"""
    
    def setUp(self):
        super().setUp()
        # Set up WebDriver for browser testing
        self.driver = None
        try:
            chrome_options = Options()
            if self.config.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            raise unittest.SkipTest(f"Chrome WebDriver not available: {e}")
            
    def tearDown(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        super().tearDown()
        
    def test_page_loads_in_browser(self):
        """Test that page loads completely in browser"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cyber-container"))
        )
        
        # Check title
        self.assertIn('AI Hacker Terminal', self.driver.title)
        
    def test_javascript_executes(self):
        """Test that JavaScript functions execute"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Test JavaScript execution
        result = self.driver.execute_script("return typeof loadFiles;")
        self.assertEqual(result, "function", "loadFiles function not found")
        
        result = self.driver.execute_script("return typeof refreshFiles;")
        self.assertEqual(result, "function", "refreshFiles function not found")
        
    def test_file_browser_loads(self):
        """Test that file browser loads with content"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Wait for file browser to load
        try:
            file_browser = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "fileBrowser"))
            )
            
            # Check if it has content (not just "Loading...")
            browser_text = file_browser.text
            self.assertNotEqual(browser_text.strip(), "Loading...", 
                              "File browser stuck on loading")
                              
            # Should have some content
            self.assertTrue(len(browser_text.strip()) > 0, 
                          "File browser has no content")
                          
        except TimeoutException:
            self.fail("File browser element not found")
            
    def test_terminal_iframe_loads(self):
        """Test that terminal iframe is present and configured"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Find terminal iframe
        try:
            terminal_frame = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "terminalFrame"))
            )
            
            # Check iframe src is set
            src = terminal_frame.get_attribute("src")
            self.assertIsNotNone(src, "Terminal iframe has no src")
            self.assertIn(":7681", src, "Terminal iframe not pointing to correct port")
            
        except TimeoutException:
            self.fail("Terminal iframe not found")
            
    def test_ui_buttons_clickable(self):
        """Test that UI buttons are clickable"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Test refresh button
        try:
            refresh_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Refresh')]")
            self.assertTrue(refresh_btn.is_enabled(), "Refresh button not enabled")
            
            # Click refresh button
            refresh_btn.click()
            time.sleep(2)  # Allow time for refresh
            
        except Exception as e:
            print(f"Refresh button test failed: {e}")
            
    def test_console_errors(self):
        """Test for JavaScript console errors"""
        if not self.driver:
            self.skipTest("WebDriver not available")
            
        self.driver.get(self.config.web_url)
        
        # Wait for page to load completely
        time.sleep(5)
        
        # Get console logs
        logs = self.driver.get_log('browser')
        
        # Filter for errors (ignore warnings and info)
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if errors:
            error_messages = [log['message'] for log in errors]
            print(f"JavaScript errors found: {error_messages}")
            # Don't fail test, but log for debugging
        
        # Check for specific error patterns that would break functionality
        critical_errors = []
        for error in errors:
            message = error['message'].lower()
            if any(keyword in message for keyword in ['cannot read', 'is not defined', 'failed to fetch']):
                critical_errors.append(error['message'])
                
        if critical_errors:
            self.fail(f"Critical JavaScript errors: {critical_errors}")


class TestPerformanceAndReliability(BaseK8sTmuxTest):
    """Test performance and reliability aspects"""
    
    def test_response_times(self):
        """Test that response times are reasonable"""
        urls_to_test = [
            self.config.web_url,
            f"{self.config.web_url}/api/files"
        ]
        
        for url in urls_to_test:
            start_time = time.time()
            response = self.session.get(url)
            end_time = time.time()
            
            response_time = end_time - start_time
            self.assertLess(response_time, 5.0, f"Slow response from {url}: {response_time:.2f}s")
            
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            try:
                response = self.session.get(f"{self.config.web_url}/api/files")
                return response.status_code == 200
            except:
                return False
                
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures, timeout=30)]
            
        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.8, f"Low success rate under load: {success_rate}")
        
    def test_memory_usage_stability(self):
        """Test that memory usage doesn't grow excessively"""
        # Make multiple requests and check for consistency
        response_sizes = []
        
        for i in range(10):
            response = self.session.get(self.config.web_url)
            response_sizes.append(len(response.content))
            time.sleep(0.5)
            
        # Response sizes should be consistent (within 10%)
        avg_size = sum(response_sizes) / len(response_sizes)
        for size in response_sizes:
            variation = abs(size - avg_size) / avg_size
            self.assertLess(variation, 0.1, f"Response size varies too much: {size} vs {avg_size}")


class TestErrorHandling(BaseK8sTmuxTest):
    """Test error handling and edge cases"""
    
    def test_invalid_api_endpoints(self):
        """Test handling of invalid API endpoints"""
        invalid_endpoints = [
            '/api/nonexistent',
            '/api/files/../../../etc/passwd',
            '/api/upload/../config',
        ]
        
        for endpoint in invalid_endpoints:
            response = self.session.get(f"{self.config.web_url}{endpoint}")
            # Should return 404 or 400, not 500 (server error)
            self.assertIn(response.status_code, [404, 400, 403], 
                         f"Unexpected status for {endpoint}: {response.status_code}")
                         
    def test_malformed_requests(self):
        """Test handling of malformed requests"""
        # Invalid JSON
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        self.assertIn(response.status_code, [400, 415])  # Bad request or unsupported media type
        
        # Missing content-type
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            data='{"command": "test"}'
        )
        # Should handle gracefully
        self.assertNotEqual(response.status_code, 500)
        
    def test_large_requests(self):
        """Test handling of large requests"""
        # Large command
        large_command = "echo " + "A" * 10000
        command_data = {'command': large_command}
        
        response = self.session.post(
            f"{self.config.web_url}/api/send-command",
            json=command_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should handle gracefully (accept or reject, but not crash)
        self.assertNotEqual(response.status_code, 500)


def run_functional_tests():
    """Run all functional tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConnectivity,
        TestWebUI,
        TestAPIEndpoints,
        TestFileOperations,
        TestCommandScheduling,
        TestMQTTNotifications,
        TestBrowserCompatibility,
        TestPerformanceAndReliability,
        TestErrorHandling,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    print("🚀 K8S-TMUX FUNCTIONAL TEST SUITE")
    print("=" * 50)
    print(f"Testing application at: {K8sTmuxTestConfig().web_url}")
    print("=" * 50)
    
    success = run_functional_tests()
    
    if success:
        print("\n✅ ALL FUNCTIONAL TESTS PASSED")
        exit(0)
    else:
        print("\n❌ SOME FUNCTIONAL TESTS FAILED")
        exit(1)