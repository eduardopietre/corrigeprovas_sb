#!/usr/bin/env python3
"""
Security vulnerability test runner for CorrigeProvas.

This script runs all security tests and generates a comprehensive report.
"""

import os
import subprocess
import sys
from datetime import datetime


def run_tests():
    """Run all security tests and generate report."""
    print("=" * 80)
    print("CorrigeProvas Security Vulnerability Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if required environment variables are set
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var) and not os.getenv(f"VITE_{var}"):
            missing_vars.append(var)
    
    if missing_vars:
        print("WARNING: Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var} (or VITE_{var})")
        print("Some tests may be skipped.")
        print()
    
    # Test files to run
    test_files = [
        "test_token_race_condition.py",
        "test_file_upload_validation.py", 
        "test_storage_path_traversal.py",
        "test_idempotency_key_validation.py",
        "test_information_disclosure.py",
        "test_rate_limiting.py",
        "test_worker_input_validation.py",
        "test_session_management.py",
        "test_security_headers.py",
        "test_sensitive_logging.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"Running {test_file}...")
        print("-" * 60)
        
        try:
            # Run pytest with verbose output
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            results[test_file] = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print(f"✓ {test_file} completed successfully")
            else:
                print(f"✗ {test_file} completed with issues")
            
        except Exception as e:
            print(f"✗ Error running {test_file}: {e}")
            results[test_file] = {
                "returncode": -1,
                "error": str(e)
            }
        
        print()
    
    # Generate summary report
    print("=" * 80)
    print("SECURITY TEST SUMMARY REPORT")
    print("=" * 80)
    
    total_tests = len(test_files)
    successful_tests = sum(1 for r in results.values() if r.get("returncode") == 0)
    failed_tests = total_tests - successful_tests
    
    print(f"Total test files: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed/Skipped: {failed_tests}")
    print()
    
    # Detailed results
    for test_file, result in results.items():
        status = "✓ PASS" if result.get("returncode") == 0 else "✗ FAIL"
        print(f"{status} {test_file}")
        
        if result.get("returncode") != 0:
            if "error" in result:
                print(f"    Error: {result['error']}")
            elif result.get("stderr"):
                print(f"    Error: {result['stderr'][:100]}...")
    
    print()
    print("=" * 80)
    print("VULNERABILITY ANALYSIS")
    print("=" * 80)
    
    # Analyze output for vulnerability confirmations
    vulnerabilities_found = []
    warnings_found = []
    
    for test_file, result in results.items():
        output = result.get("stdout", "")
        
        # Look for vulnerability confirmations
        if "VULNERABILITY CONFIRMED" in output:
            lines = output.split('\n')
            for line in lines:
                if "VULNERABILITY CONFIRMED" in line:
                    vulnerabilities_found.append(f"{test_file}: {line.strip()}")
        
        # Look for warnings
        if "WARNING:" in output:
            lines = output.split('\n')
            for line in lines:
                if "WARNING:" in line:
                    warnings_found.append(f"{test_file}: {line.strip()}")
    
    if vulnerabilities_found:
        print("CRITICAL VULNERABILITIES FOUND:")
        for vuln in vulnerabilities_found:
            print(f"  🚨 {vuln}")
        print()
    
    if warnings_found:
        print("SECURITY WARNINGS:")
        for warning in warnings_found[:10]:  # Limit to first 10 warnings
            print(f"  ⚠️  {warning}")
        if len(warnings_found) > 10:
            print(f"  ... and {len(warnings_found) - 10} more warnings")
        print()
    
    if not vulnerabilities_found and not warnings_found:
        print("✓ No critical vulnerabilities or warnings detected in test output.")
        print("  Note: This doesn't guarantee the system is secure - manual review is still needed.")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if vulnerabilities_found:
        print("IMMEDIATE ACTION REQUIRED:")
        print("1. Review all CRITICAL vulnerabilities listed above")
        print("2. Implement fixes for confirmed vulnerabilities")
        print("3. Re-run tests to verify fixes")
        print()
    
    if warnings_found:
        print("SECURITY IMPROVEMENTS:")
        print("1. Review all security warnings")
        print("2. Implement recommended security headers")
        print("3. Improve input validation and sanitization")
        print("4. Review logging practices for sensitive data")
        print()
    
    print("GENERAL RECOMMENDATIONS:")
    print("1. Conduct regular security assessments")
    print("2. Implement security monitoring and alerting")
    print("3. Keep all dependencies up to date")
    print("4. Follow security best practices for deployment")
    print()
    
    print(f"Report completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return exit code based on results
    if vulnerabilities_found:
        return 2  # Critical vulnerabilities found
    elif failed_tests > successful_tests:
        return 1  # More tests failed than passed
    else:
        return 0  # All good


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)