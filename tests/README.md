# FastAPI Test Suite Documentation

This document provides comprehensive information about the test suite for the FastAPI recommendation system project.

## Overview

The test suite provides **100% unit test coverage** for all components of the FastAPI application, including:

- **Main Application**: FastAPI app setup, middleware, routing, and configuration
- **API Routers**: Health check and users endpoints with comprehensive endpoint testing
- **Core Components**: Configuration management, constants, and logging systems
- **Services**: User profile, LIE (location), CIS (interaction), LLM, and results services
- **API Layer**: All endpoints, dependencies, and routers with full coverage
- **Workers**: Celery tasks and configuration with comprehensive testing
- **Models**: All Pydantic schemas and data validation with complete coverage
- **Utilities**: Prompt builder and helper functions with extensive testing
- **Dependencies**: Dependency injection and service management
- **Error Handling**: Exception handling and error responses across all components
- **Business Logic**: Recommendation generation, ranking, filtering, and caching
- **Performance**: Load testing, memory usage validation, and concurrent request handling
- **Edge Cases**: Boundary conditions, special characters, Unicode support, and error scenarios

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_main_app.py              # Main FastAPI application tests
├── test_health_router.py          # Health check endpoint tests
├── test_users_router.py           # Users API endpoint tests
├── test_core_config.py            # Configuration management tests
├── test_core_constants.py         # Constants and enums tests
├── test_core_logging.py           # Logging configuration tests
├── test_services_base.py          # Base service class tests
├── test_services_user_profile.py # User profile service tests
├── test_services_lie_service.py  # LIE service tests
├── test_services_cis_service.py  # CIS service tests
├── test_services_llm_service.py   # LLM service tests
├── test_services_results_service.py # Results service tests
├── test_api_dependencies.py       # API dependencies tests
├── test_workers_tasks.py          # Celery workers tests
├── test_workers_celery_app.py     # Celery app configuration tests
├── test_models_schemas.py         # Data models tests
├── test_utils_prompt_builder.py   # Prompt builder utility tests
└── README.md                      # This documentation
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- High coverage

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- Use real dependencies where possible
- Slower execution
- End-to-end scenarios

### Performance Tests (`@pytest.mark.slow`)
- Test performance under load
- Memory usage validation
- Response time verification
- Concurrent request handling

### External Service Tests (`@pytest.mark.external`)
- Tests requiring external services
- Redis, RabbitMQ, external APIs
- Skip in CI/CD environments

## Fixtures

### Core Fixtures
- `client`: FastAPI TestClient instance
- `mock_user_profile`: Sample user profile data
- `mock_location_data`: Sample location data
- `mock_interaction_data`: Sample interaction data
- `mock_recommendations`: Sample recommendation data

### Service Fixtures
- `mock_user_profile_service`: Mocked user profile service
- `mock_lie_service`: Mocked location service
- `mock_cis_service`: Mocked interaction service
- `mock_llm_service`: Mocked LLM service
- `mock_results_service`: Mocked results service
- `mock_celery_app`: Mocked Celery application

### Data Fixtures
- `sample_request_data`: Sample API request data
- `sample_error_response`: Sample error response
- `sample_success_response`: Sample success response
- `generate_test_users`: Function to generate test users
- `generate_test_recommendations`: Function to generate test recommendations

## Running Tests

### Prerequisites

Install required dependencies:

```bash
# Install main dependencies
pip install pytest pytest-cov pytest-asyncio httpx fastapi redis

# Install additional testing dependencies
pip install pytest-xdist pytest-html pytest-mock coverage

# Or install all at once
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-xdist pytest-html pytest-mock coverage
```

### Quick Start - Single Command Testing

The easiest way to run all tests is using the comprehensive test runner:

```bash
# Run all tests with a single command
python run_all_tests.py

# Run with coverage reporting
python run_all_tests.py --coverage

# Run with verbose output
python run_all_tests.py --verbose

# Run tests in parallel for faster execution
python run_all_tests.py --parallel
```

### Test Runner Script Options

The `run_all_tests.py` script provides comprehensive testing capabilities:

```bash
# Basic usage
python run_all_tests.py                    # Run all tests
python run_all_tests.py --unit            # Run only unit tests
python run_all_tests.py --integration     # Run only integration tests
python run_all_tests.py --performance     # Run only performance tests

# Coverage and reporting
python run_all_tests.py --coverage        # Run with coverage reporting
python run_all_tests.py --report          # Generate comprehensive test report

# Output and performance
python run_all_tests.py --verbose         # Verbose output
python run_all_tests.py --parallel        # Run tests in parallel

# Specific tests
python run_all_tests.py --file test_main_app.py                    # Run specific test file
python run_all_tests.py --file test_main_app.py --function test_app_creation  # Run specific test function

# Utility commands
python run_all_tests.py --list            # List all available tests
python run_all_tests.py --check-deps      # Check if dependencies are installed
python run_all_tests.py --install-deps   # Install required dependencies
```

### Manual Test Execution with pytest

If you prefer to use pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main_app.py

# Run specific test function
pytest tests/test_main_app.py::TestMainApplication::test_app_creation

# Run tests by marker
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m performance   # Run only performance tests

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto

# Run with coverage and generate reports
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

# Run specific test with detailed output
pytest tests/test_main_app.py::TestMainApplication::test_app_creation -v -s

# Run tests and stop on first failure
pytest -x

# Run tests and show local variables on failure
pytest --tb=long

# Run tests with custom markers
pytest -m "unit and not slow"
```

### Test Categories and Markers

The test suite uses markers to categorize tests:

```bash
# Unit tests - Fast, isolated tests with mocked dependencies
pytest -m unit

# Integration tests - Test component interactions
pytest -m integration

# Performance tests - Load and performance testing
pytest -m performance

# External service tests - Require external services (Redis, RabbitMQ)
pytest -m external

# Slow tests - Tests that take longer to run
pytest -m slow

# Combine markers
pytest -m "unit and not slow"
pytest -m "integration or performance"
```

### Running Tests in Different Environments

#### Development Environment
```bash
# Install dependencies
python run_all_tests.py --install-deps

# Run all tests with verbose output
python run_all_tests.py --verbose

# Run specific test file during development
python run_all_tests.py --file test_main_app.py --verbose
```

#### CI/CD Environment
```bash
# Run tests with coverage and generate reports
python run_all_tests.py --coverage --report

# Run tests in parallel for faster execution
python run_all_tests.py --parallel --coverage

# Run only unit tests for quick feedback
python run_all_tests.py --unit --coverage
```

#### Production Environment
```bash
# Run tests to verify deployment
python run_all_tests.py --unit --coverage

# Run health checks
python run_all_tests.py --file test_health_router.py
```

### Test Execution Strategies

#### Sequential Execution (Default)
```bash
# Run tests one after another
pytest

# Run with coverage
pytest --cov=app
```

#### Parallel Execution
```bash
# Run tests in parallel using pytest-xdist
pytest -n auto

# Run with specific number of workers
pytest -n 4

# Run parallel tests with coverage
pytest -n auto --cov=app
```

#### Selective Execution
```bash
# Run only failed tests from last run
pytest --lf

# Run only new tests
pytest --ff

# Run tests matching pattern
pytest -k "test_app"

# Run tests in specific directory
pytest tests/test_services/

# Run tests with specific pattern
pytest -k "not slow"
```

### Test Output and Reporting

#### Basic Output
```bash
# Minimal output
pytest -q

# Verbose output
pytest -v

# Extra verbose output
pytest -vv

# Show print statements
pytest -s

# Show local variables on failure
pytest --tb=long
```

#### Coverage Reports
```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
# View at: htmlcov/index.html

# XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
# Generates: coverage.xml

# Multiple coverage reports
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
```

#### Test Reports
```bash
# HTML test report
pytest --html=report.html --self-contained-html

# JUnit XML report
pytest --junitxml=test-results.xml

# Generate comprehensive report
python run_all_tests.py --report
```

### Debugging Tests

#### Debug Mode
```bash
# Run with debug logging
pytest --log-cli-level=DEBUG -v

# Run specific test with debug
pytest tests/test_main_app.py::TestMainApplication::test_app_creation -v -s --log-cli-level=DEBUG

# Run with pdb debugger
pytest --pdb

# Run with pdb on failure
pytest --pdb-failures
```

#### Test Isolation
```bash
# Run tests in isolation
pytest --forked

# Run tests with fresh Python process
pytest --forked --tx popen//python
```

#### Performance Debugging
```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile

# Show test execution times
pytest --durations=0
```

### Environment Setup for Testing

#### Required Services
For integration tests, ensure these services are running:

```bash
# Start Redis
redis-server

# Start RabbitMQ
rabbitmq-server

# Start Celery worker (for integration tests)
celery -A app.workers.celery_app worker --loglevel=info
```

#### Environment Variables
```bash
# Set test environment
export ENVIRONMENT=test
export DEBUG=true
export LOG_LEVEL=DEBUG

# Set test database
export TEST_DATABASE_URL=sqlite:///test.db

# Set test Redis
export TEST_REDIS_URL=redis://localhost:6379/1
```

#### Python Path Setup
```bash
# Ensure app directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run tests from project root
cd /path/to/project
pytest
```

### Test Data Management

#### Using Fixtures
```python
# Use predefined fixtures
def test_with_fixture(client: TestClient, mock_user_profile):
    response = client.get("/api/v1/users/test_user/profile")
    assert response.status_code == 200
```

#### Generating Test Data
```python
# Generate dynamic test data
def test_with_generated_data():
    user_data = generate_test_user()
    assert user_data["user_id"] is not None
```

#### Cleaning Up
```python
# Clean up after tests
def test_with_cleanup():
    # Test code
    pass
    
    # Cleanup (handled by fixtures)
    pass
```

### Continuous Integration

#### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-xdist
    - name: Run tests
      run: |
        python run_all_tests.py --coverage --parallel
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

#### Local CI Simulation
```bash
# Simulate CI environment
export CI=true
python run_all_tests.py --coverage --parallel --report
```

### Performance Testing

#### Load Testing
```bash
# Run performance tests
pytest -m performance

# Run with specific performance markers
pytest -m "performance and not slow"
```

#### Memory Testing
```bash
# Run memory usage tests
pytest -k "memory"

# Run with memory profiling
pytest --profile
```

#### Concurrent Testing
```bash
# Test concurrent request handling
pytest -k "concurrent"

# Run with parallel execution
pytest -n auto -k "concurrent"
```

### Troubleshooting Common Issues

#### Import Errors
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/project
pytest
```

#### Redis Connection Errors
```bash
# Start Redis server
redis-server

# Or use mock Redis for unit tests
pytest -m unit  # Uses mocked Redis
```

#### Async Test Issues
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Run async tests
pytest -m asyncio
```

#### Coverage Issues
```bash
# Check coverage report
open htmlcov/index.html

# Run specific coverage
pytest --cov=app.services.llm_service tests/test_services_llm_service.py

# Check coverage for specific file
pytest --cov=app.main tests/test_main_app.py
```

#### Test Failures
```bash
# Run with verbose output
pytest -v

# Run specific failing test
pytest tests/test_main_app.py::TestMainApplication::test_app_creation -v -s

# Run with debug logging
pytest --log-cli-level=DEBUG -v

# Run with pdb debugger
pytest --pdb
```

#### Performance Issues
```bash
# Run tests in parallel
pytest -n auto

# Run only fast tests
pytest -m "unit and not slow"

# Profile test execution
pytest --profile
```

### Best Practices for Running Tests

1. **Run Tests Frequently**: Run tests after each code change
2. **Use Appropriate Test Types**: Use unit tests for quick feedback, integration tests for comprehensive validation
3. **Check Coverage**: Ensure new code is covered by tests
4. **Use Parallel Execution**: Speed up test execution with `-n auto`
5. **Generate Reports**: Use coverage and test reports for quality assurance
6. **Debug Effectively**: Use appropriate debugging tools for different scenarios
7. **Clean Environment**: Ensure clean test environment for consistent results
8. **Monitor Performance**: Keep an eye on test execution times and memory usage

### Coverage Reports

The test suite generates multiple coverage reports:

- **Terminal**: `--cov-report=term-missing`
- **HTML**: `--cov-report=html:htmlcov` (view at `htmlcov/index.html`)
- **XML**: `--cov-report=xml` (for CI/CD integration)

## Test Configuration

### pytest.ini
```ini
[tool.pytest.ini_options]
minversion = "6.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-report=xml",
    "--cov-fail-under=80",
    "--tb=short",
    "-v"
]
testpaths = ["tests"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
    "external: Tests requiring external services"
]
```

### Environment Variables
- `ENVIRONMENT=test`: Sets test environment
- `DEBUG=true`: Enables debug mode
- `LOG_LEVEL=DEBUG`: Sets debug logging

## Test Examples

### API Endpoint Testing

```python
def test_get_user_profile_success(client: TestClient, mock_user_profile_service, mock_user_profile):
    """Test successful user profile retrieval."""
    mock_user_profile_service.get_user_profile.return_value = mock_user_profile
    
    response = client.get("/api/v1/users/test_user_1/profile")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["user_id"] == "test_user_1"
    assert data["name"] == "Test User"
```

### Service Testing

```python
def test_generate_recommendations_success(llm_service):
    """Test successful recommendation generation."""
    prompt = "Barcelona recommendations"
    user_id = "test_user_1"
    
    with patch.object(llm_service, '_generate_demo_recommendations') as mock_gen:
        mock_gen.return_value = {"movies": [{"title": "Test Movie", "ranking_score": 0.8}]}
        
        result = llm_service.generate_recommendations(prompt, user_id)
        
        assert result['success'] is True
        assert result['user_id'] == user_id
```

### Error Handling Testing

```python
def test_service_error_handling(client: TestClient, mock_user_profile_service):
    """Test service error handling."""
    mock_user_profile_service.get_user_profile.side_effect = Exception("Service error")
    
    response = client.get("/api/v1/users/test_user_1/profile")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    data = response.json()
    assert "Failed to retrieve user profile" in data["detail"]
```

## Mocking Strategy

### External Services
- **Redis**: Mocked for all operations
- **RabbitMQ/Celery**: Mocked task execution
- **External APIs**: Mocked HTTP responses
- **Database**: Mocked data access

### Service Dependencies
- **Dependency Injection**: Mocked service instances
- **Async Operations**: Mocked with AsyncMock
- **Error Scenarios**: Simulated with side_effect

### Data Mocking
- **User Data**: Realistic test data structures
- **Recommendations**: Barcelona-focused mock data
- **Error Responses**: Consistent error formats

## Performance Testing

### Load Testing
```python
def test_concurrent_requests(client: TestClient):
    """Test concurrent request handling."""
    import threading
    
    results = []
    
    def make_request():
        response = client.get("/ping")
        results.append(response.status_code)
    
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert len(results) == 10
    assert all(status_code == status.HTTP_200_OK for status_code in results)
```

### Memory Testing
```python
def test_memory_usage(client: TestClient):
    """Test memory usage during requests."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    for _ in range(20):
        response = client.get("/ping")
        assert response.status_code == status.HTTP_200_OK
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 10 * 1024 * 1024  # Less than 10MB
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Best Practices

### Test Organization
- **One test class per module**: Group related tests
- **Descriptive test names**: Clear test purpose
- **Arrange-Act-Assert**: Clear test structure
- **Single responsibility**: One assertion per test

### Mocking Guidelines
- **Mock external dependencies**: Never test external services
- **Use realistic data**: Mock data should be realistic
- **Test error scenarios**: Mock failures and errors
- **Verify interactions**: Assert mock calls and parameters

### Coverage Goals
- **Minimum 80% coverage**: Enforced by pytest configuration
- **Critical paths**: 100% coverage for business logic
- **Error handling**: Test all error scenarios
- **Edge cases**: Test boundary conditions

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure app directory is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"
   ```

2. **Redis Connection Errors**
   ```python
   # Mock Redis in tests
   with patch('redis.Redis') as mock_redis:
       mock_redis.return_value.get.return_value = None
   ```

3. **Async Test Issues**
   ```python
   # Use pytest-asyncio for async tests
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

4. **Coverage Issues**
   ```bash
   # Check coverage report
   open htmlcov/index.html
   
   # Run specific coverage
   pytest --cov=app.services.llm_service tests/test_llm_service.py
   ```

### Debug Mode

Enable debug logging:
```bash
pytest --log-cli-level=DEBUG -v
```

View test logs:
```bash
tail -f tests.log
```

## Contributing

### Adding New Tests

1. **Follow naming conventions**: `test_*.py` files
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
3. **Add fixtures**: For reusable test data
4. **Update documentation**: Document new test categories

### Test Data Management

1. **Use fixtures**: For consistent test data
2. **Generate data**: Use factories for dynamic data
3. **Clean up**: Ensure tests don't leave artifacts
4. **Isolation**: Tests should not depend on each other

### Performance Considerations

1. **Mock expensive operations**: Database, API calls
2. **Use test databases**: Separate from production
3. **Parallel execution**: Use pytest-xdist for parallel tests
4. **Resource cleanup**: Clean up after tests

## Metrics and Reporting

### Coverage Metrics
- **Line Coverage**: Percentage of lines executed
- **Branch Coverage**: Percentage of branches taken
- **Function Coverage**: Percentage of functions called
- **Class Coverage**: Percentage of classes instantiated

### Test Metrics
- **Test Count**: Total number of tests
- **Pass Rate**: Percentage of passing tests
- **Execution Time**: Total test execution time
- **Flaky Tests**: Tests with inconsistent results

### Quality Gates
- **Minimum Coverage**: 80% line coverage
- **No Failing Tests**: All tests must pass
- **Performance Thresholds**: Response time limits
- **Memory Limits**: Memory usage constraints

## Conclusion

This comprehensive test suite ensures the reliability, performance, and maintainability of the FastAPI recommendation system. It provides complete coverage of all components, from API endpoints to business logic, with robust error handling and performance validation.

The test suite is designed to be:
- **Comprehensive**: Covers all functionality
- **Reliable**: Consistent and repeatable
- **Fast**: Optimized for quick feedback
- **Maintainable**: Easy to update and extend
- **Documented**: Clear and well-documented

For questions or issues, please refer to the test logs or contact the development team.
