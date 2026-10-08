# Test Suite

This directory contains tests and verification scripts for the Proformas-Empresas application.

## Structure

```
tests/
??? unit/              # Unit tests and verification scripts
?   ??? verify_advances.py
?   ??? verify_tax_mode.py
?   ??? verify_pdf_import.mjs
?   ??? verify_pdf_import_igv.mjs
??? integration/       # Integration tests (WIP)
```

## Running Tests

### Verification Scripts

These are legacy test scripts that verify specific behaviors:

**Python Tests:**
```bash
python tests/unit/verify_advances.py
python tests/unit/verify_tax_mode.py
```

**JavaScript Tests:**
```bash
node tests/unit/verify_pdf_import.mjs
node tests/unit/verify_pdf_import_igv.mjs
```

## Test Data

Each verification script contains hardcoded test payloads and expected outputs for:
- Advance payments processing
- Tax mode calculations (con IGV vs sin IGV)
- PDF import validation

## Integration Tests (Future)

The `integration/` directory will contain:
- Company configuration loading tests
- Multi-company generation tests
- Full workflow end-to-end tests
- Asset validation tests

## Contributing

When adding new tests:
1. Use `pytest` framework for Python tests
2. Create descriptive test names
3. Document expected inputs and outputs
4. Test both happy path and error cases

## CI/CD

Tests should eventually be integrated into CI/CD pipeline to run automatically on commits.
