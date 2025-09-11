#!/usr/bin/env python3
"""
Test runner for Stardust.ai Chatbot
Comprehensive test suite execution with reporting
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_tests(test_type="all", verbose=False, coverage=False, parallel=False):
    """Run tests with specified options"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test type filter
    if test_type == "unit":
        cmd.extend(["tests/unit/"])
    elif test_type == "integration":
        cmd.extend(["tests/integration/"])
    elif test_type == "e2e":
        cmd.extend(["tests/e2e/"])
    else:
        cmd.extend(["tests/"])
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=tools", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add markers for specific test types
    if test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "mobile":
        cmd.extend(["-m", "mobile"])
    elif test_type == "theme":
        cmd.extend(["-m", "theme"])
    elif test_type == "analytics":
        cmd.extend(["-m", "analytics"])
    elif test_type == "rag":
        cmd.extend(["-m", "rag"])
    elif test_type == "cache":
        cmd.extend(["-m", "cache"])
    
    # Add timeout and other options
    cmd.extend([
        "--timeout=300",
        "--tb=short",
        "--strict-markers"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    start_time = time.time()
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    end_time = time.time()
    
    duration = end_time - start_time
    print("=" * 60)
    print(f"Test execution completed in {duration:.2f} seconds")
    
    return result.returncode

def run_specific_tests(test_files):
    """Run specific test files"""
    cmd = ["python", "-m", "pytest"] + test_files + [
        "-v", "--tb=short", "--strict-markers"
    ]
    
    print(f"Running specific tests: {' '.join(test_files)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode

def run_linting():
    """Run code linting"""
    print("Running code linting...")
    print("=" * 60)
    
    # Run flake8 if available
    try:
        result = subprocess.run(["flake8", "tools/", "tests/"], 
                              cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print("✅ Linting passed!")
        else:
            print("❌ Linting failed!")
        return result.returncode
    except FileNotFoundError:
        print("⚠️ flake8 not found, skipping linting")
        return 0

def run_type_checking():
    """Run type checking with mypy"""
    print("Running type checking...")
    print("=" * 60)
    
    try:
        result = subprocess.run(["mypy", "tools/"], 
                              cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print("✅ Type checking passed!")
        else:
            print("❌ Type checking failed!")
        return result.returncode
    except FileNotFoundError:
        print("⚠️ mypy not found, skipping type checking")
        return 0

def generate_test_report():
    """Generate comprehensive test report"""
    print("Generating test report...")
    print("=" * 60)
    
    cmd = [
        "python", "-m", "pytest", "tests/",
        "--html=reports/test_report.html",
        "--self-contained-html",
        "--cov=tools",
        "--cov-report=html:reports/coverage_html",
        "--cov-report=xml:reports/coverage.xml",
        "--junitxml=reports/junit.xml"
    ]
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        print("✅ Test report generated successfully!")
        print("📊 HTML Report: reports/test_report.html")
        print("📈 Coverage Report: reports/coverage_html/index.html")
        print("📋 JUnit XML: reports/junit.xml")
    else:
        print("❌ Test report generation failed!")
    
    return result.returncode

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Stardust.ai Chatbot Test Runner")
    
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "e2e", "performance", "mobile", "theme", "analytics", "rag", "cache"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific test files to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run code linting"
    )
    
    parser.add_argument(
        "--type-check",
        action="store_true",
        help="Run type checking"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    parser.add_argument(
        "--all-checks",
        action="store_true",
        help="Run all checks (tests, linting, type checking, report)"
    )
    
    args = parser.parse_args()
    
    print("🌟 Stardust.ai Chatbot Test Runner")
    print("=" * 60)
    
    exit_code = 0
    
    if args.all_checks:
        # Run all checks
        print("Running all checks...")
        
        # Linting
        if run_linting() != 0:
            exit_code = 1
        
        # Type checking
        if run_type_checking() != 0:
            exit_code = 1
        
        # Tests
        if run_tests(args.type, args.verbose, args.coverage, args.parallel) != 0:
            exit_code = 1
        
        # Report
        if generate_test_report() != 0:
            exit_code = 1
            
    elif args.files:
        # Run specific files
        exit_code = run_specific_tests(args.files)
        
    elif args.report:
        # Generate report
        exit_code = generate_test_report()
        
    elif args.lint:
        # Run linting only
        exit_code = run_linting()
        
    elif args.type_check:
        # Run type checking only
        exit_code = run_type_checking()
        
    else:
        # Run tests
        exit_code = run_tests(args.type, args.verbose, args.coverage, args.parallel)
    
    print("=" * 60)
    if exit_code == 0:
        print("🎉 All checks passed!")
    else:
        print("❌ Some checks failed!")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
