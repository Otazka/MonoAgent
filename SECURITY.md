# Security Policy

## Supported Versions

We are committed to providing security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

- **Non-root Docker container**: Runs as dedicated `monoagent` user
- **Automated security scanning**: Trivy vulnerability scanning in CI/CD
- **CodeQL analysis**: Static code analysis for security vulnerabilities
- **Dependency scanning**: Regular updates and vulnerability checks
- **Token redaction**: Sensitive tokens are redacted in logs

## Reporting a Vulnerability

If you discover a security vulnerability in MonoAgent, please report it to us:

1. **DO NOT** create a public GitHub issue
2. **DO** email us at: [security@yourdomain.com] (replace with your actual security contact)
3. **Include** detailed information about the vulnerability
4. **Provide** steps to reproduce the issue

### What to expect:

- **Response time**: We aim to respond within 48 hours
- **Updates**: You'll receive regular updates on the status
- **Credit**: Security researchers will be credited in our security advisories
- **Disclosure**: We follow responsible disclosure practices

## Security Best Practices

When using MonoAgent:

1. **Use latest version**: Always use the most recent stable release
2. **Secure tokens**: Store GitHub/GitLab tokens securely
3. **Review permissions**: Use minimal required permissions for tokens
4. **Monitor logs**: Check logs for any suspicious activity
5. **Update dependencies**: Keep your Python environment updated
