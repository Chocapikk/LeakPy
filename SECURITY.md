# Security Policy

## Supported Versions

We actively support the following versions of LeakPy with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in LeakPy, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email security details to: **balgogan@protonmail.com**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Best Practices

When using LeakPy:

- **API Key Security**: Never commit your LeakIX API key to version control
- **Key Storage**: LeakPy stores your API key securely using your system's keychain
- **Permissions**: Ensure the config directory has restrictive permissions (600)
- **Updates**: Keep LeakPy updated to the latest version

## Disclosure Policy

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide an initial assessment within 7 days
- We will keep you informed of our progress
- Once fixed, we will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Considerations

- LeakPy handles sensitive API keys - always use the secure storage mechanisms provided
- The cache stores API responses locally - be aware of what data is cached
- Use `--clear-cache` if you need to remove cached data

