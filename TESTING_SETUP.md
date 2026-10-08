# ?? Setup Instructions for Testing Framework

## Prerequisites

You need to have the following installed on your system:

- **Python 3.9+** (for backend tests with pytest)
- **Node.js 16+** (for frontend tests with Jest and npm)

## Installation Steps

### Step 1: Install Python Dependencies

Open a terminal/command prompt and run:

```bash
pip install pytest pytest-cov pytest-mock
```

Or if pip is not in PATH, use:

```bash
python -m pip install pytest pytest-cov pytest-mock
```

**Verify installation:**
```bash
pytest --version
```

### Step 2: Install JavaScript Dependencies

```bash
npm install
```

This will install all dependencies from `package.json`, including:
- Jest
- Babel
- Testing libraries

**Verify installation:**
```bash
npx jest --version
```

### Step 3: Verify Setup

Test that everything is configured correctly:

#### Python tests:
```bash
pytest --collect-only tests/
```

Expected output: Should list all pytest test files (currently none yet)

#### JavaScript tests:
```bash
npm run test:js
```

Expected output: Should run Jest with 0 tests (since we haven't written them yet)

## Running Tests

After setup, use these commands:

### Run all tests:
```bash
npm run test
```

### Run Python tests only:
```bash
npm run test:python
```

### Run JavaScript tests only:
```bash
npm run test:js
```

### Run tests with coverage:
```bash
npm run test:python:cov
npm run test:js:cov
```

### Run tests in watch mode (auto-rerun on file changes):
```bash
npm run test:watch
```

## Troubleshooting

### "pytest: command not found"
- Make sure Python is installed: `python --version`
- Install pytest: `python -m pip install pytest`
- Check that Python is in your PATH

### "npm: command not found"  
- Make sure Node.js is installed: `node --version`
- Add Node.js to your PATH or install from nodejs.org

### "jest: command not found"
- Make sure npm dependencies are installed: `npm install`
- Use `npx jest` instead of just `jest`

## Coverage Reports

After running tests with coverage:
- **Python**: Open `htmlcov/index.html` in your browser
- **JavaScript**: Coverage report will be printed to console

## CI/CD Setup

Once tests are working locally, GitHub Actions will automatically run them on push/PR.
See `.github/workflows/tests.yml` for CI configuration.
