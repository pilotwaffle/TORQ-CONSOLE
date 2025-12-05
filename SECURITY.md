# TORQ Console - Security Documentation

**Last Updated:** December 5, 2025  
**Version:** 0.80.0+  
**Maintainer:** B Flowers

---

## Security Overview

TORQ Console takes security seriously. This document outlines our security practices, known considerations, and guidelines for secure deployment.

## Table of Contents

1. [Security Principles](#security-principles)
2. [Recent Security Improvements](#recent-security-improvements)
3. [Network Security](#network-security)
4. [Data Security](#data-security)
5. [Cryptographic Practices](#cryptographic-practices)
6. [Input Validation](#input-validation)
7. [Deployment Security](#deployment-security)
8. [Reporting Security Issues](#reporting-security-issues)

---

## Security Principles

### Defense in Depth
We implement multiple layers of security controls to protect against various threat vectors.

### Least Privilege
Default configurations follow the principle of least privilege, requiring explicit actions to enable broader access.

### Secure by Default
Security features are enabled by default, with clear warnings when security-reducing options are used.

### Transparency
We document all security decisions and provide clear guidance on secure usage.

---

## Recent Security Improvements

### December 2025 Updates

#### 1. Fixed Critical Code Vulnerabilities
- **Fixed undefined name errors** that could cause runtime crashes (4 instances)
- **Fixed syntax warnings** for invalid escape sequences (2 instances)
- **Status:** ✅ Complete

#### 2. Improved Cryptographic Hash Usage
- **Issue:** MD5 hash used for non-security purposes without explicit flag
- **Fix:** Added `usedforsecurity=False` parameter to all MD5 usage
- **Locations Fixed:**
  - `torq_console/agents/advanced_memory_system.py`
  - `torq_console/core/context_manager.py` (3 instances)
- **Status:** ✅ Complete

**Code Example:**
```python
# Before (flagged by security scanners)
return hashlib.md5(content.encode()).hexdigest()

# After (explicit non-security usage)
return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
```

#### 3. Enhanced Network Binding Security
- **Issue:** Server defaulted to binding on all network interfaces (0.0.0.0)
- **Fix:** Changed default to localhost (127.0.0.1) with explicit flag for external access
- **Location:** `torq_console/api/server.py`
- **Status:** ✅ Complete

**Migration Guide:**
```python
# Old behavior (automatically exposed on all interfaces)
run_server()  # Bound to 0.0.0.0:8899

# New behavior (secure by default)
run_server()  # Bound to 127.0.0.1:8899 (localhost only)

# To expose on all interfaces (explicit opt-in)
run_server(bind_all=True)  # Bound to 0.0.0.0:8899 with security warning
```

#### 4. SQL Injection Prevention
- **Issue:** SQL template generator didn't emphasize parameterized queries
- **Fix:** Enhanced template with security examples and input sanitization
- **Location:** `torq_console/agents/tools/code_generation_tool.py`
- **Status:** ✅ Complete

**Template Improvements:**
- Added parameterized query examples
- Included security warnings against string concatenation
- Sanitized user input in template generation
- Provided examples for multiple database libraries

#### 5. Pickle Deserialization Security
- **Issue:** Pickle files loaded without integrity verification
- **Fix:** Added file permission checks and error handling
- **Location:** `torq_console/indexer/vector_store.py`
- **Status:** ✅ Complete

**Security Measures:**
- Verify file permissions before loading
- Refuse to load world-writable files on Unix systems
- Set secure permissions (0o600) when saving pickle files
- Comprehensive error handling for corrupted files

---

## Network Security

### Default Configuration

**Localhost Only (Secure Default):**
```python
# Server binds to 127.0.0.1 by default
run_server()  # Only accessible from the same machine
```

**Explicit External Access:**
```python
# Use --bind-all flag for external access
run_server(bind_all=True)  # ⚠️ Security warning displayed
```

### Deployment Recommendations

#### Development Environment
✅ **Use localhost binding** (default)
```bash
python -m torq_console.cli --web
# Server at http://127.0.0.1:8899
```

#### Production Environment
⚠️ **Use reverse proxy** (recommended)
```nginx
# nginx configuration
server {
    listen 80;
    server_name torq.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8899;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Benefits:
- SSL/TLS termination
- Rate limiting
- Access control
- DDoS protection

#### Docker Deployment
```yaml
# docker-compose.yml
services:
  torq-console:
    image: torq-console:latest
    ports:
      - "127.0.0.1:8899:8899"  # Only expose on localhost
    environment:
      - BIND_ALL=false
```

### Firewall Configuration

**Allow only necessary ports:**
```bash
# UFW (Ubuntu)
sudo ufw allow from 192.168.1.0/24 to any port 8899

# iptables
iptables -A INPUT -p tcp --dport 8899 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8899 -j DROP
```

---

## Data Security

### File Storage Security

#### Vector Store (Pickle Files)

**Security Measures:**
1. **File Permission Checks:**
   - Verify files are not world-writable before loading
   - Refuse to load suspicious files
   
2. **Secure File Creation:**
   - Set restrictive permissions (0o600 on Unix)
   - Owner read/write only

3. **Error Handling:**
   - Graceful handling of corrupted files
   - No exposure of internal paths in errors

**Example Usage:**
```python
# Secure vector store initialization
vector_store = VectorStore(persist_dir="/secure/path/to/data")
vector_store.save()  # Files saved with 0o600 permissions

# Loading with security checks
vector_store.load("/secure/path/to/data")  # Validates file permissions
```

#### Sensitive Data

**API Keys:**
- Store in environment variables or `.env` file
- Never commit to version control
- Use `.gitignore` to exclude `.env`

```bash
# .env file (never commit)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**User Data:**
- Minimize data collection
- Clear chat history option
- No telemetry by default

---

## Cryptographic Practices

### Hash Functions

#### For Security (Authentication, Tokens)
✅ **Use SHA-256 or better:**
```python
import hashlib

# Generate secure token
token = hashlib.sha256(secret_data.encode()).hexdigest()

# Password hashing (use proper libraries)
from passlib.hash import bcrypt
hashed = bcrypt.hash(password)
```

#### For Non-Security (Caching, Checksums)
✅ **MD5 with explicit flag:**
```python
import hashlib

# Cache key generation
cache_key = hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()
```

❌ **Never use MD5 for:**
- Password hashing
- Digital signatures
- Security tokens
- Authentication

### Encryption

**For sensitive data at rest:**
```python
from cryptography.fernet import Fernet

# Generate key (store securely)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt
encrypted = cipher.encrypt(sensitive_data.encode())

# Decrypt
decrypted = cipher.decrypt(encrypted).decode()
```

---

## Input Validation

### SQL Queries

✅ **Always use parameterized queries:**
```python
# Python with psycopg2
cursor.execute(
    "SELECT * FROM users WHERE username = %s",
    (username,)  # Parameterized
)

# Python with SQLite
cursor.execute(
    "SELECT * FROM users WHERE username = ?",
    (username,)  # Parameterized
)
```

❌ **Never use string concatenation:**
```python
# VULNERABLE - SQL Injection risk!
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)
```

### Command Injection

✅ **Use subprocess safely:**
```python
import subprocess

# Safe - arguments as list
subprocess.run(['ls', '-la', user_directory], check=True)

# Safe - with shell=False (default)
subprocess.run([command, arg1, arg2])
```

❌ **Avoid shell=True with user input:**
```python
# VULNERABLE - Command injection risk!
subprocess.run(f"ls {user_input}", shell=True)
```

### Path Traversal

✅ **Validate paths:**
```python
from pathlib import Path

def safe_file_access(user_path: str, base_dir: Path) -> Path:
    """Safely resolve user-provided paths."""
    requested = (base_dir / user_path).resolve()
    
    # Ensure path is within base directory
    if not requested.is_relative_to(base_dir):
        raise ValueError("Path traversal attempt detected")
    
    return requested
```

---

## Deployment Security

### Environment Variables

**Required for production:**
```bash
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Security settings
BIND_ALL=false  # Explicit localhost binding
LOG_LEVEL=info  # Don't expose debug info in production
```

### Monitoring and Logging

**What to log:**
- Authentication attempts
- API access patterns
- Error rates
- Security warnings

**What NOT to log:**
- API keys
- User passwords
- Personal information
- Full request payloads

```python
# Good logging
logger.info(f"User {user_id} accessed resource {resource_id}")

# Bad logging - exposes sensitive data
logger.info(f"API call with key {api_key} to {endpoint}")
```

### Regular Updates

**Security Update Schedule:**
1. **Monitor dependencies:** Use `pip-audit` or `safety`
   ```bash
   pip install pip-audit
   pip-audit
   ```

2. **Update regularly:**
   ```bash
   pip install --upgrade torq-console
   ```

3. **Review security advisories:**
   - GitHub Security Advisories
   - CVE databases
   - Python security mailing lists

---

## Security Checklist

### Before Production Deployment

- [ ] Change default server binding to localhost
- [ ] Use reverse proxy with SSL/TLS
- [ ] Configure firewall rules
- [ ] Set secure file permissions
- [ ] Remove debug/development code
- [ ] Review all API keys and secrets
- [ ] Enable security logging
- [ ] Set up monitoring and alerts
- [ ] Review and test backup procedures
- [ ] Document security configuration
- [ ] Train team on security practices

### Regular Security Review

- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Audit file permissions quarterly
- [ ] Penetration testing annually
- [ ] Security awareness training

---

## Reporting Security Issues

### Responsible Disclosure

We take security seriously. If you discover a security vulnerability:

**DO:**
1. Email security details to the maintainers privately
2. Provide clear reproduction steps
3. Allow time for fix before public disclosure (90 days)
4. Work with us to verify the fix

**DON'T:**
1. Publicly disclose before fix is available
2. Exploit the vulnerability
3. Access data you don't own
4. Perform destructive testing

### What to Include

```
Subject: [SECURITY] Brief description

Description: Detailed description of the vulnerability

Impact: What can an attacker do?

Reproduction:
1. Step 1
2. Step 2
3. Observe result

Environment:
- TORQ Console version: X.Y.Z
- Python version: X.Y.Z
- Operating System: OS version

Suggested Fix: (optional)
Your recommendation for addressing the issue
```

### Response Timeline

- **24 hours:** Initial acknowledgment
- **7 days:** Assessment and severity classification
- **30 days:** Fix developed and tested
- **90 days:** Fix released and disclosure (if critical)

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Acknowledged in release notes (if desired)
- Listed in SECURITY.md
- Given credit in CVE if applicable

---

## Additional Resources

### Security Tools

- **Bandit:** Python security linter
  ```bash
  pip install bandit
  bandit -r torq_console/
  ```

- **pip-audit:** Check for known vulnerabilities
  ```bash
  pip install pip-audit
  pip-audit
  ```

- **Safety:** Check dependencies for security issues
  ```bash
  pip install safety
  safety check
  ```

### Documentation

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### Contact

- **Security Issues:** Open a private security advisory on GitHub
- **General Questions:** See CONTRIBUTING.md
- **Discussion:** GitHub Discussions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.80.0+ | 2025-12-05 | Security improvements: MD5 flags, network binding, SQL injection prevention, pickle security |
| 0.70.0 | 2025-XX-XX | Initial security documentation |

---

**Security is a continuous process. This document will be updated as new security measures are implemented and best practices evolve.**

*Last reviewed: December 5, 2025*
