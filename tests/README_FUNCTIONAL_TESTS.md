# K8s-Tmux Functional Test Suite

This directory contains comprehensive functional tests for the k8s-tmux demo application, designed to validate that all features work correctly and identify issues preventing full functionality.

## Test Files Overview

### 1. `test_functional.py` - Main Functional Test Suite
**Purpose:** Test all major features to ensure they work correctly
- Web UI loads completely
- File browser displays files and allows navigation
- Terminal iframe loads and connects to ttyd
- Command scheduling works
- File upload functionality works
- MQTT test connection works

**Key Test Classes:**
- `TestConnectivity` - Basic connectivity and service health
- `TestWebUI` - Web UI rendering and content
- `TestAPIEndpoints` - API endpoint functionality
- `TestFileOperations` - File upload/download operations
- `TestCommandScheduling` - Command scheduling functionality
- `TestMQTTNotifications` - MQTT notification system
- `TestBrowserCompatibility` - JavaScript functionality with Selenium
- `TestPerformanceAndReliability` - Performance testing
- `TestErrorHandling` - Error conditions and edge cases

### 2. `test_demo_functionality.py` - Demo-Specific Debug Tests
**Purpose:** Identify why the demo isn't working (focus on JavaScript issues)
- JavaScript console error detection
- API endpoint connectivity validation
- Terminal iframe connection testing
- File browser loading analysis

**Key Test Classes:**
- `DemoConnectivityTest` - Basic demo server connectivity
- `DemoAPIFunctionalityTest` - Detailed API testing (known working endpoints)
- `DemoJavaScriptDebugTest` - JavaScript error detection and debugging
- `DemoNetworkDebugTest` - Network configuration issues (CORS, CSP, etc.)

### 3. `run_demo_tests.py` - Simple Test Runner
**Purpose:** User-friendly test runner for demo validation
- Quick validation mode for fast checks
- Comprehensive testing mode
- Debug mode with detailed output
- Automatic report generation

## Quick Start

### Prerequisites
```bash
# Install required Python packages
pip3 install requests selenium

# For browser tests (optional but recommended)
# Install Chrome and ChromeDriver
# On macOS: brew install chromedriver
# On Ubuntu: apt-get install chromium-chromedriver
```

### Running Tests

#### Quick Demo Validation (Recommended First Step)
```bash
cd /Users/erquill/Documents/GitHub/k8s-tmux/tests
python3 run_demo_tests.py
```

This runs basic connectivity, API, and UI tests to quickly identify if the demo is working.

#### Comprehensive Functional Tests
```bash
python3 run_demo_tests.py --full
```

Runs the complete functional test suite with all features.

#### Debug Mode (For JavaScript Issues)
```bash
python3 run_demo_tests.py --debug
```

Focuses on JavaScript debugging and detailed error analysis - perfect for your current issue.

#### Skip Browser Tests (Faster)
```bash
python3 run_demo_tests.py --no-browser
```

Skip Selenium browser tests if you don't have ChromeDriver installed.

#### Test Different URL
```bash
python3 run_demo_tests.py --url http://your-server-ip
```

### Individual Test Files

#### Run Main Functional Tests
```bash
python3 test_functional.py
```

#### Run Demo Debug Tests
```bash
python3 test_demo_functionality.py
```

## Expected Results

### If Demo is Working Correctly
- All connectivity tests pass
- API endpoints return expected JSON
- File browser loads with content
- No JavaScript console errors
- Terminal iframe configured correctly

### If Demo Has Issues (Current Situation)
The tests will help identify:
- **JavaScript Errors:** Console errors preventing file browser from loading
- **API Issues:** Problems with /api/files endpoint
- **Network Problems:** CORS, CSP, or other network configuration issues
- **UI Problems:** Missing JavaScript functions or broken HTML structure

## Test Output Examples

### Successful Test Output
```
🚀 K8S-TMUX DEMO QUICK VALIDATION
==================================================
1️⃣ Testing Basic Connectivity...
  🔍 Testing web service... ✅ OK
  🔍 Testing terminal port... ✅ Accessible

2️⃣ Testing API Endpoints...
  🔍 Testing /api/files... ✅ 2 files

✅ DEMO IS WORKING PROPERLY
```

### Failed Test Output (JavaScript Issue)
```
4️⃣ Testing Browser Functionality...
  🔍 Loading page in browser... ✅ Loaded  
  🔍 Checking JavaScript errors... ❌ 3 errors
      Cannot read property 'files' of undefined...
      loadFiles is not defined...

❌ DEMO HAS ISSUES
Run with --debug for detailed analysis
```

## Debugging Your Current Issue

Based on your description (backend working, file browser API returns correct JSON, but JavaScript frontend not working), run:

```bash
python3 run_demo_tests.py --debug
```

This will:
1. ✅ Confirm backend/API is working (expected to pass)
2. 🔍 Detect JavaScript console errors (likely to find issues)
3. 🔍 Test if JavaScript functions exist (loadFiles, etc.)
4. 🔍 Analyze file browser loading process step-by-step
5. 🔍 Test fetch API calls from JavaScript

## Common Issues and Solutions

### JavaScript Function Not Defined
If tests show `loadFiles is not defined`:
- JavaScript code may not be loading
- Syntax errors preventing script execution
- Functions defined after they're called

### File Browser Stuck on "Loading..."
If file browser shows "Loading..." indefinitely:
- JavaScript fetch() calls failing
- API endpoint returning wrong content-type
- CORS issues blocking cross-origin requests

### Console Errors
If browser tests detect console errors:
- Check for syntax errors in embedded JavaScript
- Verify all required functions are defined
- Look for failed network requests

## Test Reports

Use `--report` flag to generate detailed JSON reports:
```bash
python3 run_demo_tests.py --debug --report
```

Reports are saved as `demo_test_report_<timestamp>.json` and include:
- Detailed test results
- Specific error messages
- Recommendations for fixing issues

## Environment Variables

- `K8S_TMUX_BASE_URL` - Override default test URL
- `HEADLESS` - Run browser tests in headless mode (default: true)

## File Structure

```
tests/
├── test_functional.py           # Main functional tests
├── test_demo_functionality.py   # Demo-specific debugging
├── run_demo_tests.py            # User-friendly test runner
├── test_files/                  # Test files for upload testing
├── README_FUNCTIONAL_TESTS.md   # This file
└── demo_test_report_*.json      # Generated test reports
```

## Next Steps

1. **Start with quick validation:**
   ```bash
   python3 run_demo_tests.py
   ```

2. **If issues found, run debug mode:**
   ```bash
   python3 run_demo_tests.py --debug
   ```

3. **Check the specific JavaScript errors reported**

4. **Fix identified issues and re-test**

The tests are designed to pinpoint exactly why your demo isn't working and provide actionable information for fixing the issues.