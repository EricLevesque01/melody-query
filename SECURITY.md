# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please report security vulnerabilities via GitHub's private vulnerability reporting feature or by emailing the maintainers directly. Do NOT open a public issue for security vulnerabilities.

## Security Model

TechWatch v1 is designed as a **local CLI tool** with the following security boundaries:

- **API keys** are stored via environment variables or OS keychain, never in committed files
- **All HTTP fetches** go through a domain allowlist (see `src/techwatch/adapters/base.py`)
- **No authenticated scraping** — the tool does not log into retailer accounts
- **No auto-purchase** — the tool is research-only in v1
- **Email delivery** uses standard SMTP with TLS

## Adapter Compliance

Source adapters must:
- Respect `robots.txt` and legal guidance
- Implement rate limiting per source
- Never follow arbitrary URLs without domain allowlist checks
