# ?? Testing Framework Documentation

## Overview

This project implements a comprehensive testing framework for the Proformas-Empresas multi-platform application. The testing infrastructure covers both backend (Python) and frontend (JavaScript) components.

## Testing Architecture

### Backend Testing (Python with pytest)
- **Location**: `tests/unit/` and `tests/integration/`
- **Framework**: pytest with pytest-cov (coverage)
- **Test Categories**:
  - Unit tests for individual modules
  - Integration tests for API endpoints
  - Configuration validation tests

### Frontend Testing (JavaScript with Jest)
- **Location**: `tests/javascript/unit/`
- **Framework**: Jest with jsdom
- **Test Categories**:
  - Configuration loading tests
  - Form validation tests
  - Calculation tests
  - API integration tests
  - Local storage tests
  - UI interaction tests

## Project Structure

```
tests/
??? unit/                          # Backend unit tests
?   ??? test_company_config.py    # CompanyConfig class tests
?   ??? test_document_engine.py   # PDF/DOCX generation tests
?   ??? __init__.py
??? integration/                   # Backend integration tests
?   ??? test_server.py            # HTTP server API tests
?   ??? __init__.py
??? fixtures/                      # Test fixtures and test data
?   ??? company_configs/          # Sample company configurations
?   ??? payloads/                 # Sample proforma payloads
??? javascript/
?   ??? unit/                     # Frontend unit tests
?   ?   ??? app.test.js           # Main app.js tests
?   ?   ??? __tests__/            # Alternative test directory
?   ??? fixtures/                 # JavaScript test fixtures
?   ??? __mocks__/                # Jest mocks
?   ?   ??? styleMock.js          # CSS import mock
?   ??? jest.setup.js             # Jest initialization
??? conftest.py                   # pytest fixtures and configuration
??? __init__.py

# Configuration files
pytest.ini                         # pytest configuration
jest.config.js                     # Jest configuration
.babelrc                          # Babel configuration
TESTING_SETUP.md                  # Setup instructions
TESTS_ROADMAP.md                  # This file
```

## Test Coverage Summary

### Backend Tests

#### `test_company_config.py` (45+ tests)
Tests for the `CompanyConfig` dataclass:
- ? Loading valid configurations
- ? Error handling (file not found, invalid JSON)
- ? Serialization (to_dict, JSON conversion)
- ? Field validation (types, required fields)
- ? Multi-company configuration support

#### `test_document_engine.py` (90+ tests)
Tests for document generation engine:
- ? `normalize_money()` function (precision, type conversion)
- ? `compute_tax_breakdown()` function (sin_igv, con_igv modes)
- ? `ProformaData.from_payload()` classmethod
- ? PDF generation with `build_pdf()`
- ? DOCX generation with `build_docx()`
- ? Company configuration integration
- ? Payment field access (critical bug fixes verified)
- ? Edge cases (negative amounts, special characters)

#### `test_server.py` (60+ tests - framework laid out)
Tests for HTTP API server:
- Configuration loading endpoints (`/api/config`)
- Company list endpoint (`/api/companies`)
- PDF export endpoint (`POST /api/export/pdf`)
- DOCX export endpoint (`POST /api/export/docx`)
- Error handling (400, 404, validation errors)
- Concurrent request handling
- Performance testing

### Frontend Tests

#### `app.test.js` (137+ tests - frameworks laid out)
Tests for JavaScript frontend (`src/app.js`):
- **Configuration Loading** (6 tests): Loading company configs from API
- **Normalization Functions** (10 tests): Normalizing form data
- **Formatting Functions** (10 tests): Money formatting, date display
- **Money Calculations** (7 tests): Parsing and converting currency
- **Tax Calculations** (8 tests): IGV calculations for both modes
- **PDF/DOCX Import Parsing** (13 tests): Extracting data from imported files
- **Form Validation** (10 tests): Customer name, dates, items validation
- **Form Submission** (10 tests): API calls and payload creation
- **Local Storage** (10 tests): History management
- **Advance Tracking** (9 tests): Advance payment calculations
- **Payment Tracking** (5 tests): Payment method information
- **Document Generation** (10 tests): PDF and DOCX generation
- **File Downloads** (6 tests): Download triggering
- **UI Interactions** (10 tests): Form element interactions
- **Error Messages** (6 tests): Error display and handling
- **Edge Cases** (10 tests): Boundary conditions and special inputs

## Running Tests

### Prerequisites

Install dependencies first:

```bash
# Python dependencies
pip install pytest pytest-cov pytest-mock

# JavaScript dependencies
npm install
```

### Run All Tests

```bash
npm run test:all
```

### Run Python Tests Only

```bash
# Run all tests
npm run test:python

# Run with coverage report
npm run test:python:cov

# Run specific test file
pytest tests/unit/test_company_config.py -v

# Run specific test
pytest tests/unit/test_company_config.py::TestCompanyConfigLoadValidConfig::test_load_valid_config_jc_services -v
```

### Run JavaScript Tests Only

```bash
# Run all tests
npm run test:js

# Run with coverage
npm run test:js:cov

# Run in watch mode (auto-rerun on file changes)
npm run test:watch

# Run specific test file
npx jest tests/javascript/unit/app.test.js
```

### View Coverage Reports

#### Python Coverage
```bash
pytest --cov=proforma_app --cov-report=html tests/
# Then open: htmlcov/index.html
```

#### JavaScript Coverage
```bash
npm run test:js:cov
# Coverage report printed to console, also in coverage/ directory
```

## Fixtures and Test Data

### Python Fixtures (conftest.py)
- `temp_dir`: Temporary directory for test files
- `sample_payload`: Sample proforma data (JSON)
- `sample_company_config`: Sample company configuration (dict)
- `mock_config_dir`: Mock company configurations directory

### JavaScript Fixtures
- Mocked localStorage with jest.fn()
- Mocked fetch API for API calls
- Mocked Blob and file download functions

## Test Implementation Status

### ? Completed
- [x] Test directory structure created
- [x] pytest configuration (pytest.ini)
- [x] Jest configuration (jest.config.js)
- [x] Babel configuration (.babelrc)
- [x] pytest fixtures (tests/conftest.py)
- [x] Jest setup file (jest.setup.js)
- [x] CSS mock for Jest (styleMock.js)
- [x] Test implementation for company_config.py
- [x] Test implementation for document_engine.py
- [x] Test framework for server.py (integration tests)
- [x] Test framework for app.js (frontend tests)
- [x] npm scripts for running tests

### ? To Be Completed
- [ ] Run Python tests and fix any issues
- [ ] Run JavaScript tests and fix any issues
- [ ] Generate coverage reports
- [ ] Achieve 80%+ code coverage target
- [ ] Setup GitHub Actions CI/CD
- [ ] Create pre-commit hooks for linting

### ?? Future Enhancements
- [ ] E2E tests with Playwright or Cypress
- [ ] Performance benchmarking
- [ ] Load testing for concurrent requests
- [ ] Visual regression testing
- [ ] Accessibility testing (a11y)

## Implementation Guidelines

### Writing Backend Tests

```python
import pytest
from proforma_app.company_config import CompanyConfig

class TestCompanyConfigExample:
    """Test suite for specific functionality."""
    
    def test_valid_scenario(self, sample_company_config):
        """Test a valid use case."""
        config = CompanyConfig(**sample_company_config)
        assert config.company_id is not None
    
    def test_error_scenario(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            CompanyConfig.from_json_file("nonexistent.json")
```

### Writing Frontend Tests

```javascript
describe('Feature Name', () => {
  beforeEach(() => {
    // Setup before each test
    fetch.mockClear();
    localStorage.clear();
  });

  test('should do something specific', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = myFunction(input);
    
    // Assert
    expect(result).toEqual('expected');
  });
});
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Fixtures**: Use pytest fixtures for reusable test data
3. **Mocking**: Mock external dependencies (API, localStorage)
4. **Isolation**: Each test should be independent and not rely on others
5. **Coverage**: Aim for high coverage (80%+) but focus on critical paths
6. **Assertions**: Use specific assertions, not generic truthy checks
7. **Organization**: Group related tests into classes or describe blocks

## Continuous Integration

Tests are automatically run by GitHub Actions on every push and PR.

See `.github/workflows/tests.yml` for CI configuration.

### CI Pipeline
1. Checkout code
2. Setup Python environment
3. Install Python dependencies
4. Run Python tests with coverage
5. Setup Node.js environment
6. Install JavaScript dependencies
7. Run JavaScript tests with coverage
8. Generate coverage reports
9. Upload coverage to service (if configured)

## Troubleshooting

### Common Issues

**Python tests not found:**
```bash
pytest --collect-only tests/
```
Should list all discovered tests.

**Jest not recognizing test files:**
```bash
npx jest --listTests
```
Should list all test files Jest finds.

**Coverage below expected:**
- Check which modules/lines are not covered
- Add tests for uncovered code paths
- Review test isolation (tests should not affect each other)

**Tests failing intermittently:**
- Check for timing issues in async tests
- Ensure proper cleanup in afterEach/afterAll
- Mock time-dependent functions with jest.useFakeTimers()

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Testing Best Practices](https://testingjavascript.com/)

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Implement the feature
3. Ensure all tests pass
4. Check coverage hasn't decreased
5. Commit with clear test descriptions

## Maintenance

- Review and update tests when refactoring code
- Keep test data realistic and representative
- Remove obsolete tests
- Update test documentation as needed
