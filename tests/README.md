# 🧪 Stardust.ai Chatbot Test Suite

Comprehensive test suite for the Stardust.ai Chatbot application, covering all features and components.

## 📋 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_runner.py              # Test runner script
├── README.md                   # This file
├── unit/                       # Unit tests
│   ├── test_theme.py          # Theme management tests
│   ├── test_mobile.py         # Mobile optimization tests
│   ├── test_analytics.py      # Analytics system tests
│   ├── test_rag.py            # RAG system tests
│   └── test_performance.py    # Performance optimization tests
├── integration/                # Integration tests
│   └── test_app_integration.py # Application integration tests
└── e2e/                        # End-to-end tests
    └── test_end_to_end.py     # Complete workflow tests
```

## 🚀 Quick Start

### Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-html pytest-xdist pytest-timeout
pip install pytest-asyncio pytest-mock
```

### Running Tests

#### Run All Tests
```bash
python tests/test_runner.py
```

#### Run Specific Test Types
```bash
# Unit tests only
python tests/test_runner.py --type unit

# Integration tests only
python tests/test_runner.py --type integration

# End-to-end tests only
python tests/test_runner.py --type e2e
```

#### Run with Coverage
```bash
python tests/test_runner.py --coverage
```

#### Run Specific Test Files
```bash
python tests/test_runner.py --files tests/unit/test_theme.py
```

#### Run All Checks (Tests + Linting + Type Checking)
```bash
python tests/test_runner.py --all-checks
```

## 📊 Test Categories

### Unit Tests
Test individual components in isolation:

- **Theme Management** (`test_theme.py`)
  - Theme initialization and configuration
  - Theme switching and persistence
  - Custom theme creation and import/export
  - CSS generation and application

- **Mobile Optimization** (`test_mobile.py`)
  - Mobile device detection
  - Responsive design components
  - Touch-friendly interface elements
  - Mobile configuration management

- **Analytics System** (`test_analytics.py`)
  - Database initialization and management
  - User action tracking
  - Performance metric collection
  - Error logging and monitoring

- **RAG System** (`test_rag.py`)
  - Document processing and chunking
  - Vector search and retrieval
  - Database operations
  - Error handling

- **Performance Optimization** (`test_performance.py`)
  - Caching mechanisms
  - Performance monitoring
  - Async processing
  - Memory management

### Integration Tests
Test component interactions:

- **Application Integration** (`test_app_integration.py`)
  - Theme and mobile system integration
  - Analytics and RAG system integration
  - Performance and analytics integration
  - Cross-component data flow

### End-to-End Tests
Test complete user workflows:

- **User Onboarding** - Complete user setup process
- **Document Upload and Query** - Full RAG workflow
- **Theme Customization** - Theme management workflow
- **Mobile Optimization** - Mobile experience workflow
- **Analytics Monitoring** - Analytics data collection
- **Performance Optimization** - Performance monitoring workflow
- **Error Recovery** - Error handling and recovery
- **Multi-User Workflow** - Concurrent user simulation
- **Data Persistence** - Data persistence across sessions

## 🎯 Test Markers

Tests are organized using pytest markers:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Slow running tests
@pytest.mark.performance  # Performance tests
@pytest.mark.mobile       # Mobile-specific tests
@pytest.mark.theme        # Theme-related tests
@pytest.mark.analytics    # Analytics tests
@pytest.mark.rag          # RAG system tests
@pytest.mark.cache        # Cache system tests
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

- **Test Discovery**: Automatically finds test files
- **Output Options**: Verbose output with colored results
- **Markers**: Organized test categorization
- **Timeout**: 300-second timeout for tests
- **Logging**: Detailed logging configuration

### Test Fixtures (`conftest.py`)

Common fixtures available to all tests:

- `temp_dir`: Temporary directory for test files
- `mock_streamlit_session`: Mock Streamlit session state
- `mock_openai_client`: Mock OpenAI client
- `sample_document`: Sample document for testing
- `sample_chat_history`: Sample chat history
- `mock_analytics_data`: Mock analytics data

## 📈 Coverage Reports

Generate comprehensive coverage reports:

```bash
# HTML coverage report
python tests/test_runner.py --coverage

# Comprehensive report with HTML, XML, and JUnit
python tests/test_runner.py --report
```

Reports are generated in the `reports/` directory:
- `test_report.html` - HTML test report
- `coverage_html/index.html` - Coverage report
- `coverage.xml` - Coverage data in XML format
- `junit.xml` - JUnit format for CI/CD

## 🚨 Continuous Integration

### GitHub Actions Integration

The test suite is integrated with GitHub Actions for automated testing:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html
    - name: Run tests
      run: python tests/test_runner.py --all-checks
```

### Pre-commit Hooks

Set up pre-commit hooks to run tests before commits:

```bash
pip install pre-commit
pre-commit install
```

## 🐛 Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with verbose output and no capture
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/unit/test_theme.py::TestThemeManagement::test_set_theme -v -s
```

### Test Logging

Enable detailed logging:

```bash
python -m pytest tests/ --log-cli-level=DEBUG
```

### Interactive Debugging

Use `pdb` for interactive debugging:

```bash
python -m pytest tests/ --pdb
```

## 📝 Writing New Tests

### Test File Structure

```python
"""
Test module description
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.module_name import function_name

class TestClassName:
    """Test class description"""
    
    def test_function_name(self):
        """Test function description"""
        # Arrange
        input_data = "test"
        
        # Act
        result = function_name(input_data)
        
        # Assert
        assert result == "expected"
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_parametrized(self, input, expected):
        """Test with multiple inputs"""
        result = function_name(input)
        assert result == expected
```

### Best Practices

1. **Test Naming**: Use descriptive test names
2. **Arrange-Act-Assert**: Structure tests clearly
3. **One Assertion**: One assertion per test when possible
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include boundary and error conditions
6. **Use Fixtures**: Reuse common test setup
7. **Parametrize**: Use parametrize for multiple inputs
8. **Clean Up**: Clean up resources in teardown

## 🔍 Test Data Management

### Mock Data

Use fixtures for consistent test data:

```python
@pytest.fixture
def sample_data():
    return {
        "key": "value",
        "list": [1, 2, 3]
    }
```

### Temporary Files

Use temporary directories for file operations:

```python
def test_file_operation(temp_dir):
    file_path = os.path.join(temp_dir, "test.txt")
    # Test file operations
```

### Database Testing

Use in-memory databases for testing:

```python
def test_database_operation(temp_dir):
    db_path = os.path.join(temp_dir, "test.db")
    # Test database operations
```

## 📊 Performance Testing

### Benchmark Tests

```python
@pytest.mark.performance
def test_performance_benchmark():
    start_time = time.time()
    # Perform operation
    end_time = time.time()
    
    duration = end_time - start_time
    assert duration < 1.0  # Should complete within 1 second
```

### Load Testing

```python
@pytest.mark.slow
def test_load_handling():
    # Test with large datasets
    large_data = ["item"] * 10000
    result = process_data(large_data)
    assert len(result) == 10000
```

## 🎉 Test Results

### Success Criteria

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All end-to-end tests pass
- ✅ Code coverage > 80%
- ✅ No linting errors
- ✅ No type checking errors

### Test Metrics

- **Total Tests**: 50+ tests
- **Coverage**: >80% code coverage
- **Execution Time**: <5 minutes for full suite
- **Categories**: Unit, Integration, E2E
- **Components**: Theme, Mobile, Analytics, RAG, Performance

## 📞 Support

For test-related questions:

- **GitHub Issues**: [Create an issue](https://github.com/your-username/chatbot/issues)
- **Documentation**: [Read the docs](https://docs.stardust.ai)
- **Community**: [Join Discord](https://discord.gg/stardust-ai)

---

**Happy Testing! 🧪✨**
