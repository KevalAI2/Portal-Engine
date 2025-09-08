#!/usr/bin/env python3
"""
Demonstration script for the FastAPI test suite
"""
import subprocess
import sys
import os
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def run_demo():
    """Run the test suite demonstration."""
    print_header("FastAPI Test Suite Demonstration")
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   The 'tests' directory should be present.")
        sys.exit(1)
    
    print("✅ Found tests directory")
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 9):
        print("⚠️  Warning: Python 3.9+ is recommended for optimal performance")
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ Error: pytest is not installed")
        print("   Install it with: pip install pytest pytest-cov")
        sys.exit(1)
    
    # Check if other dependencies are available
    dependencies = [
        ("pytest-cov", "pytest_cov"),
        ("httpx", "httpx"),
        ("fastapi", "fastapi"),
        ("redis", "redis")
    ]
    
    missing_deps = []
    for dep_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {dep_name} is available")
        except ImportError:
            print(f"❌ {dep_name} is missing")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("   Install them with: pip install " + " ".join(missing_deps))
        print("   Or install all test dependencies: pip install -r requirements-test.txt")
    
    print_header("Test Suite Overview")
    
    # Count test files
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"📁 Test files found: {len(test_files)}")
    for test_file in test_files:
        print(f"   - {test_file.name}")
    
    # Count test functions
    total_tests = 0
    for test_file in test_files:
        try:
            with open(test_file, 'r') as f:
                content = f.read()
                test_count = content.count('def test_')
                total_tests += test_count
                print(f"   - {test_file.name}: {test_count} tests")
        except Exception as e:
            print(f"   - {test_file.name}: Error reading file ({e})")
    
    print(f"\n📊 Total test functions: {total_tests}")
    
    print_header("Running Sample Tests")
    
    # Run a simple test to verify everything works
    try:
        print("Running basic test verification...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_main_app.py::TestMainApplication::test_app_creation",
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Basic test passed!")
            print("Output:")
            print(result.stdout)
        else:
            print("❌ Basic test failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (this might indicate an issue)")
    except Exception as e:
        print(f"❌ Error running test: {e}")
    
    print_header("Available Test Commands")
    
    commands = [
        ("Run all tests", "pytest"),
        ("Run with coverage", "pytest --cov=app --cov-report=html"),
        ("Run unit tests only", "pytest -m unit"),
        ("Run integration tests", "pytest -m integration"),
        ("Run specific test file", "pytest tests/test_main_app.py"),
        ("Run with verbose output", "pytest -v"),
        ("Run tests in parallel", "pytest -n auto"),
        ("Generate test report", "python run_tests.py --report"),
        ("Check dependencies", "python run_tests.py --check-deps"),
        ("Clean test artifacts", "python run_tests.py --clean")
    ]
    
    for description, command in commands:
        print(f"📝 {description}:")
        print(f"   {command}")
    
    print_header("Test Coverage Goals")
    
    coverage_info = [
        ("Minimum Coverage", "80%"),
        ("Target Coverage", "90%"),
        ("Critical Paths", "100%"),
        ("Error Handling", "100%"),
        ("API Endpoints", "100%"),
        ("Business Logic", "100%")
    ]
    
    for component, target in coverage_info:
        print(f"🎯 {component}: {target}")
    
    print_header("Test Categories")
    
    categories = [
        ("Unit Tests", "Individual component testing", "@pytest.mark.unit"),
        ("Integration Tests", "Component interaction testing", "@pytest.mark.integration"),
        ("Performance Tests", "Load and performance testing", "@pytest.mark.slow"),
        ("External Tests", "External service testing", "@pytest.mark.external")
    ]
    
    for name, description, marker in categories:
        print(f"📋 {name}:")
        print(f"   Description: {description}")
        print(f"   Marker: {marker}")
    
    print_header("Next Steps")
    
    next_steps = [
        "Install missing dependencies if any",
        "Run the full test suite: pytest",
        "Check coverage: pytest --cov=app --cov-report=html",
        "View coverage report: open htmlcov/index.html",
        "Run specific tests: pytest tests/test_main_app.py",
        "Use the test runner: python run_tests.py",
        "Set up CI/CD with GitHub Actions",
        "Add more tests as the application grows"
    ]
    
    for i, step in enumerate(next_steps, 1):
        print(f"{i}. {step}")
    
    print_header("Test Suite Ready!")
    
    print("🎉 The FastAPI test suite is ready to use!")
    print("📚 For detailed documentation, see: tests/README.md")
    print("📊 For test summary, see: TEST_SUITE_SUMMARY.md")
    print("🚀 Happy testing!")


if __name__ == "__main__":
    run_demo()
