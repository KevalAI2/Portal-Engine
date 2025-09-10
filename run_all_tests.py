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
    --stats         Run tests and show pass percentage per test file
    --help          Show this help message

Examples:
    python run_all_tests.py                    # Run all tests
    python run_all_tests.py --unit            # Run only unit tests
    python run_all_tests.py --coverage        # Run with coverage
    python run_all_tests.py --stats           # Run with per-file pass percentages
"""

import os
import sys
import subprocess
import argparse
import time
import json
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
        import pytest  # noqa
        import coverage  # noqa
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
        sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "pytest-xdist", "pytest-json-report"
    ], check=True)


def run_unit_tests(verbose=False, parallel=False, coverage=False):
    """Run unit tests."""
    print("Running unit tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    cmd.extend(["-m", "unit"])
    
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
    return subprocess.run(cmd, cwd=get_project_root())


def run_integration_tests(verbose=False, parallel=False, coverage=False):
    """Run integration tests."""
    print("Running integration tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    cmd.extend(["-m", "integration"])
    
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
    return subprocess.run(cmd, cwd=get_project_root())


def run_performance_tests(verbose=False, parallel=False, coverage=False):
    """Run performance tests."""
    print("Running performance tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    cmd.extend(["-m", "performance"])
    
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
    return subprocess.run(cmd, cwd=get_project_root())


def run_all_tests(verbose=False, parallel=False, coverage=False):
    """Run all tests."""
    print("Running all tests...")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    
    if verbose:
        cmd.append("-v")
    if parallel:
        cmd.extend(["-n", "auto"])
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
    return subprocess.run(cmd, cwd=get_project_root())


def run_specific_test_file(test_file, verbose=False, coverage=False):
    """Run a specific test file."""
    print(f"Running test file: {test_file}")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory() / test_file))
    
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
    return subprocess.run(cmd, cwd=get_project_root())


def run_specific_test_function(test_file, test_function, verbose=False, coverage=False):
    """Run a specific test function."""
    print(f"Running test function: {test_file}::{test_function}")
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(f"{get_test_directory() / test_file}::{test_function}")
    
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend([
            "--cov=app", "--cov-report=html", "--cov-report=term-missing", "--cov-report=xml"
        ])
    
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])
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
    cmd = [sys.executable, "-m", "pytest"]
    cmd.append(str(get_test_directory()))
    cmd.extend([
        "--cov=app", "--cov-report=html", "--cov-report=term-missing",
        "--cov-report=xml", "--junitxml=test-results.xml",
        "--html=test-report.html", "--self-contained-html"
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


def run_tests_with_stats():
    """Run tests and calculate pass percentage per test file."""
    print("Running tests with statistics...")

    report_file = "test-results.json"
    cmd = [
        sys.executable, "-m", "pytest",
        str(get_test_directory()),
        "--json-report",
        f"--json-report-file={report_file}",
        "--disable-warnings", "--tb=short"
    ]
    result = subprocess.run(cmd, cwd=get_project_root())

    report_path = get_project_root() / report_file
    if report_path.exists():
        with open(report_path, "r") as f:
            data = json.load(f)

        file_stats = {}
        for test in data.get("tests", []):
            file_name = Path(test["nodeid"].split("::")[0]).name
            outcome = test["outcome"]
            if file_name not in file_stats:
                file_stats[file_name] = {"passed": 0, "failed": 0, "skipped": 0}
            if outcome == "passed":
                file_stats[file_name]["passed"] += 1
            elif outcome == "failed":
                file_stats[file_name]["failed"] += 1
            elif outcome == "skipped":
                file_stats[file_name]["skipped"] += 1

        print("\n📊 Test Pass Percentages Per File:")
        for file_name, stats in file_stats.items():
            total = sum(stats.values())
            passed = stats["passed"]
            percent = (passed / total) * 100 if total > 0 else 0
            print(f"{file_name:<30} {passed}/{total} passed ({percent:.2f}%)")

    return result


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for the GenAI for Travel project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage reporting")
    parser.add_argument("--verbose", action="store_true", help="Run tests with verbose output")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--file", type=str, help="Run a specific test file")
    parser.add_argument("--function", type=str, help="Run a specific test function (requires --file)")
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--report", action="store_true", help="Generate a comprehensive test report")
    parser.add_argument("--install-deps", action="store_true", help="Install required dependencies")
    parser.add_argument("--check-deps", action="store_true", help="Check if required dependencies are installed")
    parser.add_argument("--stats", action="store_true", help="Run tests and show pass percentage per file")

    args = parser.parse_args()

    if args.check_deps:
        if check_dependencies():
            print("All required dependencies are installed.")
        else:
            print("Some required dependencies are missing.")
            print("Run with --install-deps to install them.")
        return 0

    if args.install_deps:
        try:
            install_dependencies()
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return 1
        return 0

    if not check_dependencies():
        print("Required dependencies are missing.")
        print("Run with --install-deps to install them.")
        return 1

    if args.list:
        list_available_tests()
        return 0

    if args.report:
        return generate_test_report()

    if args.stats:
        return run_tests_with_stats()

    if args.function and args.file:
        start_time = time.time()
        result = run_specific_test_function(args.file, args.function, args.verbose, args.coverage)
        end_time = time.time()
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        return result.returncode

    if args.file:
        start_time = time.time()
        result = run_specific_test_file(args.file, args.verbose, args.coverage)
        end_time = time.time()
        print(f"Test completed in {end_time - start_time:.2f} seconds")
        return result.returncode

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
