#!/usr/bin/env python3
"""
Test Runner for Invoice Management System
Comprehensive test runner with multiple execution modes
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✅ {description or cmd} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or cmd} failed with exit code {e.returncode}")
        return False

def run_unit_tests():
    """Run unit tests only"""
    cmd = "python -m pytest tests/test_models.py tests/test_utils.py -v --tb=short"
    return run_command(cmd, "Unit Tests (Models & Utils)")

def run_route_tests():
    """Run route tests only"""
    cmd = "python -m pytest tests/test_*_routes.py -v --tb=short"
    return run_command(cmd, "Route Tests (API Endpoints)")

def run_integration_tests():
    """Run integration tests only"""
    cmd = "python -m pytest tests/test_integration.py -v --tb=short"
    return run_command(cmd, "Integration Tests")

def run_all_tests():
    """Run all tests with coverage"""
    cmd = "python -m pytest tests/ -v --cov=models --cov=routes --cov=utils --cov=app --cov-report=html --cov-report=term-missing"
    return run_command(cmd, "All Tests with Coverage")

def run_fast_tests():
    """Run fast tests only (excluding slow ones)"""
    cmd = 'python -m pytest tests/ -v -m "not slow" --tb=short'
    return run_command(cmd, "Fast Tests Only")

def run_slow_tests():
    """Run slow tests only"""
    cmd = 'python -m pytest tests/ -v -m "slow" --tb=short'
    return run_command(cmd, "Slow Tests Only")

def run_specific_test(test_path):
    """Run a specific test file or test function"""
    cmd = f"python -m pytest {test_path} -v --tb=short"
    return run_command(cmd, f"Specific Test: {test_path}")

def run_tests_with_markers(markers):
    """Run tests with specific markers"""
    marker_expr = " and ".join(markers)
    cmd = f'python -m pytest tests/ -v -m "{marker_expr}" --tb=short'
    return run_command(cmd, f"Tests with markers: {marker_expr}")

def run_code_quality_checks():
    """Run code quality checks"""
    checks = [
        ("flake8 models routes utils app.py", "Flake8 Linting"),
        ("black --check models routes utils app.py", "Black Formatting Check"),
        ("isort --check-only models routes utils app.py", "Import Sorting Check"),
        ("mypy models routes utils", "Type Checking"),
        ("bandit -r models routes utils app.py", "Security Check"),
        ("safety check", "Dependency Security Check")
    ]
    
    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False
    
    return all_passed

def run_performance_tests():
    """Run performance benchmarks"""
    cmd = "python -m pytest tests/ -v --benchmark-only --tb=short"
    return run_command(cmd, "Performance Benchmarks")

def generate_test_report():
    """Generate comprehensive test report"""
    cmd = "python -m pytest tests/ --html=reports/test_report.html --self-contained-html --cov=models --cov=routes --cov=utils --cov=app --cov-report=html:reports/coverage"
    return run_command(cmd, "Test Report Generation")

def run_parallel_tests():
    """Run tests in parallel"""
    cmd = "python -m pytest tests/ -n auto -v --tb=short"
    return run_command(cmd, "Parallel Test Execution")

def run_continuous_integration():
    """Run full CI pipeline"""
    print("\n🚀 Starting Continuous Integration Pipeline")
    print("=" * 60)
    
    steps = [
        (run_code_quality_checks, "Code Quality Checks"),
        (run_unit_tests, "Unit Tests"),
        (run_route_tests, "Route Tests"),
        (run_integration_tests, "Integration Tests"),
        (generate_test_report, "Test Report Generation")
    ]
    
    failed_steps = []
    
    for step_func, step_name in steps:
        print(f"\n📋 Step: {step_name}")
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ Failed: {step_name}")
        else:
            print(f"✅ Passed: {step_name}")
    
    if failed_steps:
        print(f"\n❌ CI Pipeline Failed. Failed steps: {', '.join(failed_steps)}")
        return False
    else:
        print(f"\n✅ CI Pipeline Passed Successfully!")
        return True

def setup_test_environment():
    """Set up test environment"""
    print("Setting up test environment...")
    
    # Create necessary directories
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("generated_files", exist_ok=True)
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    os.environ['TESTING'] = 'True'
    
    print("✅ Test environment set up successfully")

def clean_test_artifacts():
    """Clean up test artifacts"""
    print("Cleaning up test artifacts...")
    
    cleanup_paths = [
        ".pytest_cache",
        "htmlcov",
        "reports/coverage",
        ".coverage",
        "*.log"
    ]
    
    for path in cleanup_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    print("✅ Test artifacts cleaned up")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Invoice Management System Test Runner")
    parser.add_argument("--mode", choices=[
        "unit", "routes", "integration", "all", "fast", "slow", "quality", 
        "performance", "report", "parallel", "ci", "clean"
    ], default="all", help="Test execution mode")
    parser.add_argument("--test", help="Run specific test file or function")
    parser.add_argument("--markers", nargs="+", help="Run tests with specific markers")
    parser.add_argument("--setup", action="store_true", help="Set up test environment")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_test_environment()
        return
    
    if args.clean:
        clean_test_artifacts()
        return
    
    # Set up environment
    setup_test_environment()
    
    # Run specific test
    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    
    # Run tests with markers
    if args.markers:
        success = run_tests_with_markers(args.markers)
        sys.exit(0 if success else 1)
    
    # Run based on mode
    mode_functions = {
        "unit": run_unit_tests,
        "routes": run_route_tests,
        "integration": run_integration_tests,
        "all": run_all_tests,
        "fast": run_fast_tests,
        "slow": run_slow_tests,
        "quality": run_code_quality_checks,
        "performance": run_performance_tests,
        "report": generate_test_report,
        "parallel": run_parallel_tests,
        "ci": run_continuous_integration,
        "clean": clean_test_artifacts
    }
    
    if args.mode in mode_functions:
        success = mode_functions[args.mode]()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()