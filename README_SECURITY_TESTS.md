# Security Vulnerability Tests - CorrigeProvas

This directory contains comprehensive security tests for the CorrigeProvas application, designed to identify and validate potential security vulnerabilities.

## Overview

The security test suite covers 10 major vulnerability categories:

1. **Token Balance Race Conditions** - Tests for concurrent token reservation vulnerabilities
2. **File Upload Validation** - Tests for malicious file upload bypasses
3. **Storage Path Traversal** - Tests for path traversal vulnerabilities in file storage
4. **Idempotency Key Validation** - Tests for weak idempotency key handling
5. **Information Disclosure** - Tests for sensitive information leakage in errors
6. **Rate Limiting** - Tests for missing or insufficient rate limiting
7. **Worker Input Validation** - Tests for insufficient input validation in worker processes
8. **Session Management** - Tests for session handling and JWT security issues
9. **Security Headers** - Tests for missing security headers
10. **Sensitive Logging** - Tests for sensitive information disclosure in logs

## Setup

### Prerequisites

1. Python 3.10 or higher
2. Access to the CorrigeProvas Supabase instance
3. Required environment variables

### Installation

1. Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

2. Set up environment variables:
```bash
# Required for most tests
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Alternative frontend environment variables
export VITE_SUPABASE_URL="https://your-project.supabase.co"
export VITE_SUPABASE_ANON_KEY="your-anon-key"
```

## Running Tests

### Run All Tests

Execute the comprehensive test runner:
```bash
python tests/run_security_tests.py
```

This will:
- Run all security tests
- Generate a detailed report
- Highlight critical vulnerabilities
- Provide remediation recommendations

### Run Individual Test Categories

Run specific test files:
```bash
# Test token race conditions
python -m pytest tests/test_token_race_condition.py -v

# Test file upload validation
python -m pytest tests/test_file_upload_validation.py -v

# Test storage path traversal
python -m pytest tests/test_storage_path_traversal.py -v

# Test all with detailed output
python -m pytest tests/ -v --tb=short
```

### Run Tests with Coverage

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### 1. Token Balance Race Conditions (`test_token_race_condition.py`)

**Purpose**: Validates the token reservation system against race conditions.

**Tests**:
- Concurrent token reservations
- Balance calculation accuracy
- Insufficient balance protection

**Critical Findings**: If multiple concurrent requests can reserve more tokens than available.

### 2. File Upload Validation (`test_file_upload_validation.py`)

**Purpose**: Tests file upload security and validation.

**Tests**:
- Malicious files with valid headers
- Executable files with image MIME types
- Polyglot files (valid image + script)
- File size limit enforcement

**Critical Findings**: If malicious files are accepted based only on MIME type.

### 3. Storage Path Traversal (`test_storage_path_traversal.py`)

**Purpose**: Tests for path traversal vulnerabilities in file storage.

**Tests**:
- Path traversal in upload paths
- Path traversal in result paths
- Filename sanitization
- User ID validation

**Critical Findings**: If path traversal sequences allow access to unauthorized files.

### 4. Idempotency Key Validation (`test_idempotency_key_validation.py`)

**Purpose**: Tests idempotency key handling and collision detection.

**Tests**:
- Key length validation
- Special character handling
- Collision detection
- Format validation

**Critical Findings**: If weak idempotency keys allow duplicate operations or collisions.

### 5. Information Disclosure (`test_information_disclosure.py`)

**Purpose**: Tests for sensitive information leakage in responses.

**Tests**:
- Error message analysis
- Stack trace disclosure
- Database schema disclosure
- Internal ID exposure

**Critical Findings**: If error messages reveal internal system details.

### 6. Rate Limiting (`test_rate_limiting.py`)

**Purpose**: Tests for proper rate limiting implementation.

**Tests**:
- Endpoint rate limiting
- Concurrent request handling
- Burst vs sustained load
- Per-user vs global limits

**Critical Findings**: If endpoints lack rate limiting and can be abused.

### 7. Worker Input Validation (`test_worker_input_validation.py`)

**Purpose**: Tests worker process input validation.

**Tests**:
- Storage path validation
- Job ID validation
- Template data validation
- Configuration validation

**Critical Findings**: If worker processes accept malicious input without validation.

### 8. Session Management (`test_session_management.py`)

**Purpose**: Tests session handling and JWT security.

**Tests**:
- JWT token validation
- Expired token handling
- Session fixation protection
- Token information disclosure

**Critical Findings**: If invalid or expired tokens are accepted.

### 9. Security Headers (`test_security_headers.py`)

**Purpose**: Tests for proper security header implementation.

**Tests**:
- Content Security Policy
- X-Frame-Options
- HSTS headers
- CORS configuration

**Critical Findings**: If critical security headers are missing.

### 10. Sensitive Logging (`test_sensitive_logging.py`)

**Purpose**: Tests for sensitive information in logs.

**Tests**:
- User ID logging
- Password/token logging
- Database connection logging
- Error message sensitivity

**Critical Findings**: If sensitive data is logged inappropriately.

## Understanding Test Results

### Test Outcomes

- **PASS**: Test completed without finding vulnerabilities
- **FAIL**: Test found potential vulnerabilities or security issues
- **SKIP**: Test was skipped due to missing dependencies or configuration

### Vulnerability Severity

- **CRITICAL**: Immediate security risk requiring urgent attention
- **HIGH**: Significant security risk requiring prompt attention
- **MEDIUM**: Moderate security risk requiring attention
- **LOW**: Minor security improvement opportunity

### Result Interpretation

- **VULNERABILITY CONFIRMED**: A definitive security vulnerability was found
- **WARNING**: A potential security issue or bad practice was identified
- **INFO**: General information about security configuration

## Common Issues and Solutions

### Environment Variables Not Set

**Issue**: Tests are skipped due to missing environment variables.

**Solution**: Ensure all required environment variables are set:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

### Network Timeouts

**Issue**: Tests fail due to network timeouts.

**Solution**: 
- Check network connectivity
- Verify Supabase URL is correct
- Increase timeout values in test configuration

### Authentication Failures

**Issue**: Tests fail with 401 Unauthorized errors.

**Solution**:
- Verify API keys are correct and active
- Check if RLS policies are properly configured
- Ensure service role key has necessary permissions

### Import Errors

**Issue**: Worker-related tests fail with import errors.

**Solution**:
- Ensure the worker module is in the Python path
- Install worker dependencies
- Run tests from the correct directory

## Security Best Practices

Based on the test findings, implement these security measures:

### 1. Input Validation
- Validate all user inputs on both client and server side
- Sanitize file paths and names
- Implement proper UUID validation

### 2. Authentication & Authorization
- Implement proper JWT validation
- Use secure session management
- Implement proper token expiration

### 3. Rate Limiting
- Implement rate limiting on all public endpoints
- Use per-user rate limiting where appropriate
- Monitor for abuse patterns

### 4. Security Headers
- Implement comprehensive security headers
- Configure proper CORS policies
- Use HTTPS everywhere

### 5. Error Handling
- Sanitize error messages
- Avoid exposing internal system details
- Implement proper logging practices

### 6. File Handling
- Validate file content, not just MIME types
- Implement proper file size limits
- Sanitize file paths and names

## Continuous Security Testing

### Integration with CI/CD

Add security tests to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Security Tests
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run security tests
        run: python tests/run_security_tests.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
```

### Regular Security Assessments

- Run security tests weekly
- Review and update tests as the application evolves
- Monitor for new vulnerability patterns
- Keep test dependencies updated

## Contributing

When adding new security tests:

1. Follow the existing test structure
2. Include comprehensive documentation
3. Test both positive and negative cases
4. Provide clear vulnerability descriptions
5. Include remediation recommendations

## Support

For questions about the security tests:

1. Review the test documentation
2. Check the vulnerability analysis report
3. Consult the main application documentation
4. Contact the security team for critical findings

---

**Remember**: These tests are designed to identify potential vulnerabilities. A passing test doesn't guarantee security - regular security reviews and updates are essential.