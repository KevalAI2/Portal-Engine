#!/usr/bin/env python3
"""
Comprehensive test runner for the FastAPI project
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-asyncio',
        'httpx',
        'fastapi',
        'redis'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {missing_packages}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("All dependencies are installed.")
    return True


def run_unit_tests():
    """Run unit tests."""
    return run_command(
        "python -m pytest tests/ -m unit --cov=app --cov-report=term-missing --cov-report=html",
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        "python -m pytest tests/ -m integration --cov=app --cov-report=term-missing",
        "Integration Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml",
        "All Tests"
    )


def run_specific_test(test_path):
    return run_command(
        f"python -m pytest {test_path} -v --tb=long --show-capture=all --durations=10 --cov=app --cov-report=term-missing",
        f"Specific Test: {test_path}"
    )



def run_tests_with_coverage():
    """Run tests with detailed coverage report."""
    return run_command(
        "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=80",
        "Tests with Coverage Report"
    )


def run_performance_tests():
    """Run performance tests."""
    return run_command(
        "python -m pytest tests/ -m slow -v",
        "Performance Tests"
    )


def generate_test_report():
    """Generate comprehensive test report."""
    print("\nGenerating test report...")
    
    # Run tests with coverage
    success = run_tests_with_coverage()
    
    if success:
        print("\nTest report generated successfully!")
        print("Coverage report available at: htmlcov/index.html")
        print("XML coverage report available at: coverage.xml")
        print("Test log available at: tests.log")
    else:
        print("Test report generation failed!")
    
    return success


def clean_test_artifacts():
    """Clean test artifacts."""
    print("Cleaning test artifacts...")
    
    artifacts = [
        "htmlcov",
        "coverage.xml",
        "tests.log",
        ".coverage",
        ".pytest_cache",
        "__pycache__",
        "**/__pycache__"
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                run_command(f"rm -rf {artifact}", f"Removing directory: {artifact}")
            else:
                run_command(f"rm -f {artifact}", f"Removing file: {artifact}")
    
    print("Test artifacts cleaned.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="FastAPI Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--specific", type=str, help="Run specific test file or function")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("FastAPI Test Runner")
    print("==================")
    
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        return
    
    if args.clean:
        clean_test_artifacts()
        return
    
    if not check_dependencies():
        print("Please install missing dependencies first.")
        sys.exit(1)
    
    success = True
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.all:
        success = run_all_tests()
    elif args.coverage:
        success = run_tests_with_coverage()
    elif args.performance:
        success = run_performance_tests()
    elif args.specific:
        success = run_specific_test(args.specific)
    elif args.report:
        success = generate_test_report()
    else:
        # Default: run all tests with coverage
        success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
