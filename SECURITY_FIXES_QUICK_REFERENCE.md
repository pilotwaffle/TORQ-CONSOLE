# Security Fixes Quick Reference

**Generated:** 2025-10-06
**Status:** URGENT - IMMEDIATE ACTION REQUIRED

---

## CRITICAL VULNERABILITIES - FIX IMMEDIATELY (24-48 hours)

### 1. XSS in Tool Dropdown - CRITICAL
**File:** `torq_console/ui/templates/dashboard.html`
**Lines:** 720-760

**Quick Fix:**
```html
<!-- Add DOMPurify library -->
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>

<script>
// Sanitize all MCP tool data
function sanitizeMCPContent(content) {
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: [],
        ALLOWED_ATTR: [],
        KEEP_CONTENT: true
    });
}

// In Alpine.js init()
this.mcpTools = data.tools.map(tool => ({
    ...tool,
    name: sanitizeMCPContent(tool.name),
    icon: sanitizeMCPContent(tool.icon),
    description: sanitizeMCPContent(tool.description)
}));
</script>
```

### 2. No Parameter Validation - CRITICAL
**File:** `torq_console/mcp/client.py`
**Lines:** 213-235

**Quick Fix:**
```python
# Add this before line 226
from jsonschema import validate, ValidationError

async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None,
                   endpoint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if arguments is None:
        arguments = {}

    # GET TOOL SCHEMA
    tools = await self.list_tools(endpoint)
    tool_schema = next((t for t in tools if t['name'] == tool_name), None)

    if tool_schema:
        input_schema = tool_schema.get('inputSchema', {})
        try:
            # VALIDATE PARAMETERS
            validate(instance=arguments, schema=input_schema)
        except ValidationError as e:
            self.logger.error(f"Parameter validation failed: {e}")
            return {"error": "VALIDATION_ERROR", "message": str(e)}

    # Continue with existing code
    response = await self._send_request(...)
```

### 3. Command Injection - CRITICAL
**File:** `torq_console/mcp/client.py`
**Lines:** 56-72

**Quick Fix:**
```python
# Add at top of file
ALLOWED_MCP_MODULES = {
    "torq_console.mcp.servers.filesystem",
    "torq_console.mcp.servers.database",
    "torq_console.mcp.servers.git"
}

async def _connect_stdio(self, endpoint: str) -> bool:
    command_path = endpoint[8:]

    # VALIDATE MODULE
    if command_path not in ALLOWED_MCP_MODULES:
        self.logger.error(f"Unauthorized module: {command_path}")
        return False

    # Check for path traversal
    if ".." in command_path:
        return False

    # Rest of existing code...
```

---

## HIGH PRIORITY FIXES (1 week)

### 4. No Authentication on API Endpoints
**File:** `torq_console/ui/web.py`
**Lines:** 242-250

**Quick Fix:**
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()
API_KEY = os.getenv("TORQ_API_KEY", "change-me-in-production")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Add to endpoints
@self.app.get("/api/mcp/tools")
async def list_mcp_tools(authorized: bool = Depends(verify_api_key)):
    return await self._list_mcp_tools()

@self.app.post("/api/mcp/call")
async def call_mcp_tool(request: MCPToolRequest, authorized: bool = Depends(verify_api_key)):
    return await self._call_mcp_tool(request)
```

### 5. No CSRF Protection
**File:** `torq_console/ui/web.py`

**Quick Fix:**
```python
from fastapi import Cookie, Header
import secrets

def validate_csrf(
    cookie_token: Optional[str] = Cookie(None, alias="csrf_token"),
    header_token: Optional[str] = Header(None, alias="X-CSRF-Token")
):
    if not cookie_token or cookie_token != header_token:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    return True

# Add CSRF token endpoint
@self.app.get("/api/csrf-token")
async def get_csrf_token(response: Response):
    token = secrets.token_urlsafe(32)
    response.set_cookie(key="csrf_token", value=token, httponly=True, samesite="strict")
    return {"csrf_token": token}

# Add to POST endpoints
@self.app.post("/api/mcp/call")
async def call_mcp_tool(request: MCPToolRequest, csrf: bool = Depends(validate_csrf)):
    return await self._call_mcp_tool(request)
```

### 6. Backend XSS Prevention
**File:** `torq_console/ui/web.py`
**Lines:** 1210+

**Quick Fix:**
```python
import html
import re

def sanitize_tool_field(value: str) -> str:
    """Sanitize tool metadata."""
    if not isinstance(value, str):
        return str(value)

    # HTML escape
    value = html.escape(value, quote=True)

    # Remove dangerous patterns
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)

    # Limit length
    return value[:500]

# In _list_mcp_tools()
for tool in server_tools:
    sanitized_tool = {
        "name": sanitize_tool_field(tool.get("name", "")),
        "description": sanitize_tool_field(tool.get("description", "")),
        "icon": sanitize_tool_field(tool.get("icon", ""))[:10]
    }
    tools.append(sanitized_tool)
```

### 7. Add Security Headers
**File:** `torq_console/ui/web.py`

**Quick Fix:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

# Add to app
self.app.add_middleware(SecurityHeadersMiddleware)
```

---

## TESTING COMMANDS

### Run Security Scans
```bash
# Install tools
pip install bandit safety

# Scan for Python vulnerabilities
bandit -r torq_console/ -ll

# Check dependencies
safety check

# Run unit tests
pytest torq_console/tests/security/
```

### Manual XSS Testing
```javascript
// Test payloads in tool name field
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
javascript:alert('XSS')
```

### Test Authentication
```bash
# Should fail without API key
curl http://localhost:8000/api/mcp/tools

# Should succeed with API key
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/mcp/tools
```

---

## DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] All CRITICAL fixes applied and tested
- [ ] DOMPurify library added to frontend
- [ ] Parameter validation implemented
- [ ] Command injection fixed with whitelist
- [ ] Authentication enabled on all endpoints
- [ ] CSRF protection added
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Audit logging enabled
- [ ] Security scan results reviewed
- [ ] Penetration testing completed
- [ ] Environment variables set (API keys, secrets)
- [ ] Security documentation updated
- [ ] Team trained on security best practices

---

## ENVIRONMENT VARIABLES TO SET

```bash
# .env file
TORQ_API_KEY=<generate-strong-random-key>
SESSION_SECRET_KEY=<generate-strong-random-key>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
ENABLE_DEBUG=false
```

---

## EMERGENCY CONTACTS

**Security Team:** security@torqconsole.com
**On-Call Engineer:** +1-XXX-XXX-XXXX
**Incident Response:** Follow IR-001 playbook

---

## NEXT STEPS

1. Review full audit report: `MCP_DROPDOWN_SECURITY_AUDIT.md`
2. Assign tasks to development team
3. Track progress in security ticketing system
4. Schedule security review meeting
5. Plan penetration testing after fixes deployed
6. Update security training materials

---

**Document Owner:** Security Team
**Last Updated:** 2025-10-06
**Next Review:** After all CRITICAL fixes deployed
