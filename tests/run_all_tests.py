#!/usr/bin/env python3
"""
Test runner for k8s-tmux security and functionality tests.
Runs all test suites and generates comprehensive reports.
"""

import unittest
import sys
import os
import time
import json
from io import StringIO
from datetime import datetime

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all test modules
try:
    from test_file_handler import *
    from test_security_penetration import *
    from test_mqtt_security import *
except ImportError as e:
    print(f"Warning: Could not import test module: {e}")


class SecurityTestResult(unittest.TestResult):
    """Custom test result class to track security-specific results"""
    
    def __init__(self):
        super().__init__()
        self.security_failures = []
        self.critical_issues = []
        self.test_results = {}
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        
        # Categorize security failures
        if any(keyword in test_name.lower() for keyword in 
               ['injection', 'traversal', 'authentication', 'authorization']):
            self.critical_issues.append({
                'test': test_name,
                'error': str(err[1]),
                'category': 'Critical Security'
            })
            
        self.security_failures.append(test_name)
        
    def addError(self, test, err):
        super().addError(test, err)
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_results[test_name] = 'ERROR'
        
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_results[test_name] = 'PASS'


def run_security_tests():
    """Run all security-focused test suites"""
    
    print("🔒 K8S-TMUX SECURITY TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Test categories and their classes
    test_categories = {
        "Core Functionality Tests": [
            "TestFileHandlerFunctionality",
            "TestEdgeCases",
        ],
        "Security Vulnerability Tests": [
            "TestFileHandlerSecurity", 
            "TestPathTraversalAttacks",
            "TestCommandInjectionAttacks",
            "TestFileSystemSecurityBypass",
            "TestResourceExhaustionAttacks",
            "TestPrivilegeEscalation",
            "TestDataExfiltrationVectors",
            "TestAuthenticationBypass",
        ],
        "MQTT Security Tests": [
            "TestMQTTProtocolSecurity",
            "TestMQTTNetworkSecurity", 
            "TestMQTTMessageSecurity",
            "TestMQTTAuthorizationSecurity",
            "TestMQTTDenialOfServiceAttacks",
        ],
        "Integration Tests": [
            "TestIntegration",
        ]
    }
    
    results_by_category = {}
    
    # Run tests by category
    for category, test_class_names in test_categories.items():
        print(f"📋 {category}")
        print("-" * len(category))
        
        category_suite = unittest.TestSuite()
        
        for test_class_name in test_class_names:
            try:
                # Get test class if it exists
                test_class = globals().get(test_class_name)
                if test_class:
                    tests = loader.loadTestsFromTestCase(test_class)
                    category_suite.addTests(tests)
                else:
                    print(f"⚠️  Test class not found: {test_class_name}")
            except Exception as e:
                print(f"❌ Error loading {test_class_name}: {e}")
        
        # Run category tests
        if category_suite.countTestCases() > 0:
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(category_suite)
            
            # Store results
            results_by_category[category] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
            }
            
            # Print category summary
            print(f"  Tests Run: {result.testsRun}")
            print(f"  Failures: {len(result.failures)}")
            print(f"  Errors: {len(result.errors)}")
            print(f"  Success Rate: {results_by_category[category]['success_rate']:.1f}%")
            
            # Show critical failures
            if result.failures:
                print("  ❌ FAILURES:")
                for test, error in result.failures[:3]:  # Show first 3
                    test_name = f"{test.__class__.__name__}.{test._testMethodName}"
                    print(f"    • {test_name}")
                if len(result.failures) > 3:
                    print(f"    • ... and {len(result.failures) - 3} more")
                    
            if result.errors:
                print("  🚫 ERRORS:")
                for test, error in result.errors[:3]:  # Show first 3
                    test_name = f"{test.__class__.__name__}.{test._testMethodName}"
                    print(f"    • {test_name}")
                if len(result.errors) > 3:
                    print(f"    • ... and {len(result.errors) - 3} more")
        else:
            print("  ⚠️  No tests found in this category")
            results_by_category[category] = {
                'tests_run': 0, 'failures': 0, 'errors': 0, 'success_rate': 0
            }
            
        print()
    
    # Generate overall summary
    total_tests = sum(cat['tests_run'] for cat in results_by_category.values())
    total_failures = sum(cat['failures'] for cat in results_by_category.values())
    total_errors = sum(cat['errors'] for cat in results_by_category.values())
    overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    
    print("📊 OVERALL TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {total_tests}")
    print(f"Total Failures: {total_failures}")
    print(f"Total Errors: {total_errors}")
    print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    print()
    
    # Security assessment
    security_categories = [
        "Security Vulnerability Tests",
        "MQTT Security Tests"
    ]
    
    security_tests = sum(results_by_category.get(cat, {}).get('tests_run', 0) 
                        for cat in security_categories)
    security_failures = sum(results_by_category.get(cat, {}).get('failures', 0) 
                           for cat in security_categories)
    security_errors = sum(results_by_category.get(cat, {}).get('errors', 0) 
                         for cat in security_categories)
    
    print("🔒 SECURITY ASSESSMENT")
    print("=" * 30)
    
    if security_tests > 0:
        security_issues = security_failures + security_errors
        security_score = ((security_tests - security_issues) / security_tests * 100)
        
        print(f"Security Tests: {security_tests}")
        print(f"Security Issues: {security_issues}")
        print(f"Security Score: {security_score:.1f}%")
        print()
        
        if security_score < 70:
            print("🚨 CRITICAL SECURITY ALERT")
            print("Multiple security vulnerabilities detected!")
            print("Immediate remediation required before deployment.")
        elif security_score < 85:
            print("⚠️  MODERATE SECURITY CONCERNS")
            print("Several security issues require attention.")
        else:
            print("✅ GOOD SECURITY POSTURE")
            print("Most security tests passed.")
    else:
        print("⚠️  No security tests were executed.")
    
    print()
    print("🎯 RECOMMENDATIONS")
    print("=" * 20)
    
    # Generate recommendations based on test categories
    recommendations = []
    
    if results_by_category.get("Security Vulnerability Tests", {}).get('failures', 0) > 0:
        recommendations.extend([
            "• Implement input validation for all user inputs",
            "• Add path traversal protection for file operations", 
            "• Sanitize commands before execution",
            "• Add authentication and authorization mechanisms"
        ])
        
    if results_by_category.get("MQTT Security Tests", {}).get('failures', 0) > 0:
        recommendations.extend([
            "• Enable MQTT encryption (use port 8883)",
            "• Implement MQTT authentication",
            "• Configure MQTT access control lists (ACLs)",
            "• Add message validation and rate limiting"
        ])
        
    if not recommendations:
        recommendations = [
            "• Continue monitoring security best practices",
            "• Regular security testing and code reviews",
            "• Keep dependencies updated"
        ]
    
    for rec in recommendations:
        print(rec)
    
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return exit code based on critical security failures
    critical_failures = results_by_category.get("Security Vulnerability Tests", {}).get('failures', 0)
    if critical_failures > 5:  # More than 5 critical security failures
        return 1
    return 0


def generate_test_report():
    """Generate a detailed test report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_environment': {
            'python_version': sys.version,
            'platform': sys.platform,
        },
        'summary': {},
        'recommendations': []
    }
    
    # Save report to file
    report_file = os.path.join(os.path.dirname(__file__), 'security_test_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report_file}")


if __name__ == '__main__':
    print("Starting comprehensive security test suite...")
    
    try:
        exit_code = run_security_tests()
        generate_test_report()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)