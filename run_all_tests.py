#!/usr/bin/env python3
"""
Comprehensive test runner for the GenAI for Travel project.

This script provides a single command to run all tests in the project,
including unit tests, integration tests, and performance tests.

Usage:
    python run_all_tests.py [options]

Options:
    --unit          Run only unit tests
    --integration   Run only integration tests
    --performance   Run only performance tests
    --coverage      Run tests with coverage reporting
    --verbose       Run tests with verbose output
    --parallel      Run tests in parallel
    --help          Show this help message

Examples:
    python run_all_tests.py                    # Run all tests
    python run_all_tests.py --unit            # Run only unit tests
    python run_all_tests.py --coverage        # Run with coverage
    python run_all_tests.py --verbose --parallel  # Run with verbose output in parallel
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.absolute()


def get_test_directory():
    """Get the test directory."""
    return get_project_root() / "tests"


def get_requirements_file():
    """Get the requirements file path."""
    return get_project_root() / "requirements.txt"


def get_requirements_test_file():
    """Get the test requirements file path."""
    return get_project_root() / "requirements-test.txt"


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pytest
        import coverage
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    
    # Install main requirements
    if get_requirements_file().exists():
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(get_requirements_file())
        ], check=True)
    
    # Install test requirements
    if get_requirements_test_file().exists():
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(get_requirements_test_file())
        ], check=True)
    
    # Install pytest and coverage if not already installed
    subprocess.run([
        sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "pytest-xdist"
    ], check=True)


def run_unit_tests(verbose=False, parallel=False, coverage=False):
    """Run unit tests."""
    print("Running unit tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test directory
    cmd.append(str(get_test_directory()))
    
    # Add unit test marker
    cmd.extend(["-m", "unit"])
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def run_integration_tests(verbose=False, parallel=False, coverage=False):
    """Run integration tests."""
    print("Running integration tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test directory
    cmd.append(str(get_test_directory()))
    
    # Add integration test marker
    cmd.extend(["-m", "integration"])
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def run_performance_tests(verbose=False, parallel=False, coverage=False):
    """Run performance tests."""
    print("Running performance tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test directory
    cmd.append(str(get_test_directory()))
    
    # Add performance test marker
    cmd.extend(["-m", "performance"])
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def run_all_tests(verbose=False, parallel=False, coverage=False):
    """Run all tests."""
    print("Running all tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test directory
    cmd.append(str(get_test_directory()))
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def run_specific_test_file(test_file, verbose=False, coverage=False):
    """Run a specific test file."""
    print(f"Running test file: {test_file}")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test file
    cmd.append(str(get_test_directory() / test_file))
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def run_specific_test_function(test_file, test_function, verbose=False, coverage=False):
    """Run a specific test function."""
    print(f"Running test function: {test_file}::{test_function}")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test file and function
    cmd.append(f"{get_test_directory() / test_file}::{test_function}")
    
    # Add verbose output
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    return subprocess.run(cmd, cwd=get_project_root())


def list_available_tests():
    """List all available tests."""
    print("Available tests:")
    
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    cmd.append(str(get_test_directory()))
    
    result = subprocess.run(cmd, cwd=get_project_root(), capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("Error collecting tests:")
        print(result.stderr)


def generate_test_report():
    """Generate a comprehensive test report."""
    print("Generating test report...")
    
    # Run tests with coverage
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    cmd.extend([
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--junitxml=test-results.xml",
        "--html=test-report.html",
        "--self-contained-html"
    ])
    
    result = subprocess.run(cmd, cwd=get_project_root())
    
    if result.returncode == 0:
        print("Test report generated successfully!")
        print("HTML report: test-report.html")
        print("Coverage report: htmlcov/index.html")
        print("JUnit XML: test-results.xml")
        print("Coverage XML: coverage.xml")
    else:
        print("Error generating test report")
    
    return result


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for the GenAI for Travel project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run only performance tests"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Run a specific test file"
    )
    
    parser.add_argument(
        "--function",
        type=str,
        help="Run a specific test function (requires --file)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tests"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a comprehensive test report"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install required dependencies"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if required dependencies are installed"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if args.check_deps:
        if check_dependencies():
            print("All required dependencies are installed.")
        else:
            print("Some required dependencies are missing.")
            print("Run with --install-deps to install them.")
        return 0
    
    # Install dependencies
    if args.install_deps:
        try:
            install_dependencies()
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return 1
        return 0
    
    # Check if dependencies are available
    if not check_dependencies():
        print("Required dependencies are missing.")
        print("Run with --install-deps to install them.")
        return 1
    
    # List available tests
    if args.list:
        list_available_tests()
        return 0
    
    # Generate test report
    if args.report:
        return generate_test_report()
    
    # Run specific test function
    if args.function and args.file:
        start_time = time.time()
        result = run_specific_test_function(
            args.file, args.function, args.verbose, args.coverage
        )
        end_time = time.time()
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        return result.returncode
    
    # Run specific test file
    if args.file:
        start_time = time.time()
        result = run_specific_test_file(args.file, args.verbose, args.coverage)
        end_time = time.time()
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        return result.returncode
    
    # Run tests based on type
    start_time = time.time()
    
    if args.unit:
        result = run_unit_tests(args.verbose, args.parallel, args.coverage)
    elif args.integration:
        result = run_integration_tests(args.verbose, args.parallel, args.coverage)
    elif args.performance:
        result = run_performance_tests(args.verbose, args.parallel, args.coverage)
    else:
        result = run_all_tests(args.verbose, args.parallel, args.coverage)
    
    end_time = time.time()
    print(f"Tests completed in {end_time - start_time:.2f} seconds")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
