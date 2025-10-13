# Security Testing Guidelines

## API Key Security in Tests

**CRITICAL**: Never expose real API keys in tests or test output.

### ✅ Secure Practices:

1. **Use Mock API Keys**: Only use fake/mock keys like `"sk-test123"` for testing
2. **Environment Isolation**: Always use `patch.dict(os.environ, {...}, clear=True)` to isolate test environment
3. **Prevent .env Loading**: Use `Config(env_file="/tmp/nonexistent.env")` to prevent loading real credentials
4. **Mock Config Properties**: Use `patch.object(Config, 'openai_api_key', ...)` to ensure empty keys in tests
5. **Verify Empty Keys**: Always assert that `config.openai_api_key == ""` in security-focused tests

### ❌ Dangerous Practices:

1. **Never** use real API keys in test code
2. **Never** allow tests to load from actual `.env` files containing real credentials
3. **Never** let test output expose real API keys in assertion errors
4. **Never** commit real API keys to version control

### Example Secure Test:

```python
def test_missing_api_key():
    with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
        with patch.object(Config, 'openai_api_key', new_callable=lambda: property(lambda self: "")):
            config = Config(env_file="/tmp/nonexistent.env")
            assert config.openai_api_key == ""  # Security verification
            # ... rest of test
```

### Security Review Checklist:

- [ ] No real API keys in test code
- [ ] Environment properly isolated with `clear=True`
- [ ] Config prevented from loading real `.env` files
- [ ] API key assertions verify empty strings, not real keys
- [ ] Test output doesn't expose sensitive information

## Reporting Security Issues

If you discover any security issues in tests or code:

1. **Do not** commit the fix immediately if it exposes the issue
2. Remove any exposed credentials from git history if needed
3. Review all test output for potential credential exposure
4. Update this document with new security practices as needed
