# Security Policy

## Supported Versions

The following table shows which versions of this project are currently supported with security updates:

| Version | Supported          |
|----------|--------------------|
| main (latest) | ✅ Supported |
| older releases | ❌ Not supported |

---

## Reporting a Vulnerability

We take security issues seriously and appreciate your help in improving the safety of this project.

If you discover a vulnerability, please **do not create a public GitHub issue**.  
Instead, report it responsibly by following these steps:

1. **Notify the maintainers** at: [ReqTrace Support Form](https://forms.gle/mQXHCCQgG7FzMEGc9) 
2. Include as much detail as possible to help reproduce and validate the issue:
   - A detailed description of the vulnerability
   - Steps to reproduce
   - Any relevant code snippets or log output
3. You can expect a response within **5 business days**.
4. Once confirmed, we’ll work on a fix and coordinate a public disclosure if appropriate.

---

## Security Best Practices

To ensure your local setup remains secure:
- Never commit or share `.env` files or credentials publicly.
- Use environment variables or secret managers for sensitive data (API keys, database passwords).
- Regularly update dependencies using:
  ```bash
  pip install --upgrade -r requirements.txt
  npm update
