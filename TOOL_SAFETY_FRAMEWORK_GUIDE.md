# TORQ Console Tool Safety Framework

## Overview

The TORQ Console Tool Safety Framework is a comprehensive, enterprise-grade security system that provides **sandbox enforcement**, **confirmation workflows**, and **policy-driven access control** for all tool operations. This framework implements the **deny-by-default** security principle with comprehensive protection against common threats.

## 🔐 Core Security Features

### 1. Policy Engine (Deny-by-Default)
- **Default Deny**: Tools without explicit policies are automatically blocked
- **Path Validation**: Whitelist/blacklist-based file system access control
- **Operation Control**: Granular permission management for read/write/execute operations
- **Risk Assessment**: Automatic risk level determination for all operations

### 2. Sandbox Management
- **Process Isolation**: Tools execute in isolated environments
- **Resource Limits**: CPU, memory, and disk usage constraints
- **File System Sandboxing**: Restricted access to specified directories only
- **Network Isolation**: Optional network access controls

### 3. Confirmation Workflows
- **Risk-Based Confirmation**: High-risk operations require explicit user approval
- **Multiple Methods**: CLI prompts, web dialogs, email, SMS, external approvals
- **Timeout Management**: Configurable confirmation timeouts
- **Audit Trail**: Complete confirmation history tracking

### 4. Rate Limiting
- **Sliding Window Algorithm**: Precise rate limiting with token buckets
- **Multi-Level Controls**: Global, tool-specific, and user-specific limits
- **Burst Protection**: Handles traffic spikes while preventing abuse
- **Dynamic Adjustments**: Runtime limit modifications

### 5. Security Monitoring
- **Threat Detection**: Pattern-based identification of malicious inputs
- **Prompt Injection Protection**: Detection of LLM prompt manipulation attempts
- **Input Validation**: Comprehensive validation of all parameters
- **Session Risk Scoring**: Dynamic risk assessment based on behavior patterns

### 6. Comprehensive Audit Logging
- **Complete Event Tracking**: All tool operations logged with full context
- **Security Violations**: Detailed logging of security incidents
- **Performance Metrics**: Execution time and resource usage tracking
- **Structured Logs**: JSON-formatted logs for easy analysis

## 📁 File Structure

```
torq_console/
├── safety/                          # Core safety framework
│   ├── __init__.py                 # Safety system exports
│   ├── models.py                   # Pydantic data models
│   ├── policy_engine.py            # Policy evaluation engine
│   ├── sandbox.py                  # Sandbox management
│   ├── confirmation.py             # Confirmation workflows
│   ├── audit_logger.py             # Comprehensive logging
│   ├── rate_limiter.py             # Rate limiting system
│   ├── security.py                 # Security threat detection
│   └── safety_manager.py           # Main integration manager
├── agents/tools/policies/          # Tool policy files
│   ├── file_operations_tool.yaml   # File operations policy
│   ├── browser_automation_tool.yaml # Browser automation policy
│   ├── code_generation_tool.yaml   # Code generation policy
│   ├── mcp_client_tool.yaml        # MCP client policy
│   └── image_generation_tool.yaml  # Image generation policy
└── test_tool_safety_system.py      # Comprehensive test suite
```

## 🚀 Quick Start

### 1. Basic Usage

```python
from torq_console.safety import SafetyManager
from torq_console.safety.models import ToolRequest, OperationType

# Initialize safety manager
safety_manager = SafetyManager(
    policies_dir="./policies",
    audit_log_dir="./audit_logs"
)

# Create tool request
request = ToolRequest(
    tool_name="file_operations_tool",
    operation=OperationType.READ,
    parameters={"file": "./data.txt"}
)

# Evaluate and execute with safety
result = safety_manager.evaluate_and_execute_tool(
    request,
    user_id="user123",
    session_id="session456"
)

if result["success"]:
    print("Tool executed successfully:", result["result"])
elif result["requires_confirmation"]:
    print("User confirmation required:", result["confirmation_id"])
elif result["denied"]:
    print("Request denied:", result["denied_reason"])
```

### 2. Handling Confirmations

```python
# Request confirmation for high-risk operation
result = safety_manager.evaluate_and_execute_tool(high_risk_request)

if result["requires_confirmation"]:
    confirmation_id = result["confirmation_id"]

    # Simulate user confirmation
    confirmed = safety_manager.confirm_operation(
        confirmation_id=confirmation_id,
        confirmed=True,
        user_id="user123"
    )

    if confirmed:
        print("User confirmed operation")
        # Execute the operation again
        result = safety_manager.evaluate_and_execute_tool(
            request, bypass_confirmation=True
        )
```

### 3. Custom Policy Creation

Create a YAML policy file for your tool:

```yaml
# policies/my_tool.yaml
tool_name: "my_tool"
risk_level: "medium"

# Path restrictions
allowed_paths:
  - "./workspace/"
  - "/tmp/"
forbidden_paths:
  - "/etc/"
  - "/root/"

# Operation permissions
allowed_operations:
  - "read"
  - "write"
forbidden_operations:
  - "execute"
  - "system"

# Safety settings
requires_confirmation: true
confirmation_timeout: 300

# Rate limiting
rate_limit:
  requests: 100
  window: 3600  # per hour

# Security settings
require_user_context: true
log_level: "warning"
```

## 🛡️ Security Policies

### Risk Levels

- **LOW**: Minimal impact, basic operations only
- **MEDIUM**: Potential for data exposure, requires user context
- **HIGH**: Significant impact potential, requires confirmation
- **CRITICAL**: Could cause serious damage, strict restrictions

### Operation Types

- **READ**: Read files or data
- **WRITE**: Write or modify files
- **EXECUTE**: Execute commands or programs
- **DELETE**: Delete files or resources
- **NETWORK**: Network access
- **SYSTEM**: System-level operations
- **FILE_SYSTEM**: File system operations
- **API_CALL**: External API calls

### Policy Enforcement Rules

1. **Default Deny**: Tools without policies are automatically blocked
2. **Path Validation**: All file paths checked against allowed/forbidden lists
3. **Operation Control**: Each operation type requires explicit permission
4. **Risk-Based Confirmation**: High-risk operations require user approval
5. **Rate Limiting**: Prevents abuse and resource exhaustion
6. **Input Validation**: All parameters scanned for threats

## 📊 Monitoring and Analytics

### Safety Status Dashboard

```python
# Get comprehensive safety status
status = safety_manager.get_safety_status()

print("Safety Statistics:")
print(f"Total Requests: {status['statistics']['total_requests']}")
print(f"Allowed: {status['statistics']['allowed_requests']}")
print(f"Denied: {status['statistics']['denied_requests']}")
print(f"Security Violations: {status['statistics']['security_violations']}")

print("\nPolicy Engine:")
print(f"Loaded Policies: {status['policy_engine']['total_policies']}")
print(f"Policy Files: {status['policy_engine']['loaded_policies']}")
```

### Audit Log Analysis

```python
# Search audit logs
logs = safety_manager.audit_logger.search_logs(
    tool_name="file_operations_tool",
    start_time=datetime.utcnow() - timedelta(hours=24),
    limit=100
)

for log in logs:
    print(f"{log['timestamp']}: {log['data']['tool_name']} - {log['data']['decision']}")
```

### Security Violation Reporting

```python
# Get security report
security_report = safety_manager.security_manager.get_security_report()

print(f"Active Sessions: {security_report['active_sessions']}")
print(f"High Risk Sessions: {security_report['high_risk_sessions']}")
print(f"Security Events: {security_report['security_events_count']}")
```

## 🔧 Advanced Configuration

### Sandbox Configuration

```python
from torq_console.safety.models import SandboxConfig

sandbox_config = SandboxConfig(
    working_directory="/safe/workspace",
    temp_directory="/safe/tmp",
    network_isolated=True,
    filesystem_isolated=True,
    max_memory_mb=512,
    max_cpu_time_seconds=300,
    allowed_environment_vars=["PATH", "HOME"],
    forbidden_environment_vars=["PASSWORD", "API_KEY"]
)

safety_manager = SafetyManager(sandbox_config=sandbox_config)
```

### Rate Limiting Rules

```python
from torq_console.safety.rate_limiter import RateLimitRule

# Add global rate limit
safety_manager.rate_limiter.add_global_rule(
    RateLimitRule(requests=1000, window_seconds=3600)  # 1000 requests per hour
)

# Add tool-specific limit
safety_manager.rate_limiter.add_tool_rule(
    "high_risk_tool",
    RateLimitRule(requests=10, window_seconds=3600, priority=1)
)

# Add user-specific limit
safety_manager.rate_limiter.add_user_rule(
    "user123",
    RateLimitRule(requests=500, window_seconds=3600)
)
```

### Security Context

```python
from torq_console.safety.models import SecurityContext

context = SecurityContext(
    user_id="user123",
    session_id="session456",
    ip_address="192.168.1.100",
    authentication_level="mfa",  # none, basic, oauth, mfa
    permissions={"read_files", "write_workspace"},
    risk_score=0.2
)

result = safety_manager.evaluate_and_execute_tool(request, context=context)
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd TORQ-CONSOLE
python test_tool_safety_system.py
```

The test suite validates:
- ✅ Policy enforcement (default deny)
- ✅ Path validation and sandboxing
- ✅ Confirmation workflows
- ✅ Rate limiting
- ✅ Security threat detection
- ✅ Audit logging
- ✅ Error handling
- ✅ Configuration updates

## 📈 Performance Considerations

### Optimization Tips

1. **Policy Caching**: Policies are cached in memory for fast evaluation
2. **Sliding Window Efficiency**: Rate limiting uses optimized data structures
3. **Async Logging**: Audit logging is non-blocking
4. **Connection Pooling**: Reuse database connections where applicable
5. **Resource Limits**: Configure appropriate limits for your environment

### Resource Usage

- **Memory**: ~50MB base + ~1MB per active sandbox
- **CPU**: Minimal overhead for policy evaluation
- **Disk**: Audit logs rotate automatically (100MB default)
- **Network**: Only when tools require network access

## 🔒 Security Best Practices

### 1. Policy Design
- **Principle of Least Privilege**: Grant minimum necessary permissions
- **Layered Security**: Multiple security controls for defense in depth
- **Regular Reviews**: Periodically review and update policies

### 2. User Authentication
- **Strong Authentication**: Require MFA for sensitive operations
- **Session Management**: Implement secure session handling
- **Context Awareness**: Use security context for risk assessment

### 3. Monitoring and Alerting
- **Real-time Monitoring**: Monitor for security violations
- **Alert Thresholds**: Set appropriate alert thresholds
- **Regular Audits**: Conduct regular security audits

### 4. Incident Response
- **Violation Response**: Have procedures for security violations
- **Backup and Recovery**: Regular backups of configuration and logs
- **Documentation**: Maintain security documentation

## 🆘 Troubleshooting

### Common Issues

1. **Policy Not Found**
   - Check policy file location and naming
   - Verify YAML syntax
   - Restart safety manager after policy changes

2. **Confirmation Timeout**
   - Increase confirmation timeout in policy
   - Check user notification system
   - Verify confirmation handler configuration

3. **Rate Limit Exceeded**
   - Review rate limit settings
   - Check for potential abuse
   - Consider increasing limits for legitimate use

4. **Sandbox Creation Failed**
   - Check system permissions
   - Verify disk space availability
   - Review sandbox configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('torq_console.safety').setLevel(logging.DEBUG)
```

## 📚 API Reference

### SafetyManager

Main interface for the safety framework.

```python
class SafetyManager:
    def __init__(self, policies_dir=None, audit_log_dir=None, sandbox_config=None):
        """Initialize safety manager with optional configurations"""

    def evaluate_and_execute_tool(self, request, user_id=None, session_id=None, context=None, bypass_confirmation=False):
        """Evaluate tool request against safety policies and execute if allowed"""

    def confirm_operation(self, confirmation_id, confirmed, user_id=None):
        """Process user confirmation for high-risk operations"""

    def get_safety_status(self):
        """Get comprehensive safety system status and statistics"""

    def reload_policies(self):
        """Reload all safety policies from disk"""

    def update_configuration(self, config_updates):
        """Update safety system configuration"""

    def cleanup(self):
        """Cleanup resources and temporary data"""
```

### ToolRequest

Represents a request to use a tool.

```python
class ToolRequest(BaseModel):
    tool_name: str
    operation: OperationType
    parameters: Dict[str, Any]
    target_path: Optional[str]
    user_context: Optional[Dict[str, Any]]
    session_id: Optional[str]
    timestamp: datetime
    request_id: str
```

### PolicyDecision

Result of policy evaluation.

```python
class PolicyDecision(BaseModel):
    decision: Decision  # ALLOW, DENY, REQUIRE_CONFIRMATION, RATE_LIMITED
    risk_level: RiskLevel
    reason: str
    policy_name: str
    confirmation_required: bool
    confirmation_message: Optional[str]
    rate_limit_info: Optional[Dict[str, Any]]
    allowed_operations: List[OperationType]
    denied_operations: List[OperationType]
```

## 🎯 Integration Examples

### 1. Integrating with Existing Tools

```python
class MyTool:
    def __init__(self, safety_manager):
        self.safety_manager = safety_manager

    def process_file(self, file_path, user_id):
        request = ToolRequest(
            tool_name="my_tool",
            operation=OperationType.READ,
            parameters={"file": file_path}
        )

        result = self.safety_manager.evaluate_and_execute_tool(
            request, user_id=user_id
        )

        if result["success"]:
            return self._actual_file_processing(file_path)
        else:
            raise SecurityError(f"Operation denied: {result['denied_reason']}")
```

### 2. Web API Integration

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
safety_manager = SafetyManager()

@app.route('/api/tool/execute', methods=['POST'])
def execute_tool():
    data = request.json

    tool_request = ToolRequest(
        tool_name=data['tool_name'],
        operation=OperationType(data['operation']),
        parameters=data['parameters'],
        target_path=data.get('target_path')
    )

    result = safety_manager.evaluate_and_execute_tool(
        tool_request,
        user_id=request.headers.get('X-User-ID'),
        session_id=request.headers.get('X-Session-ID')
    )

    return jsonify(result)
```

### 3. CLI Integration

```python
import click
from torq_console.safety import SafetyManager

@click.command()
@click.option('--tool', required=True, help='Tool name')
@click.option('--operation', required=True, help='Operation type')
@click.option('--file', help='Target file path')
@click.option('--force', is_flag=True, help='Bypass confirmations')
def run_tool(tool, operation, file, force):
    safety_manager = SafetyManager()

    request = ToolRequest(
        tool_name=tool,
        operation=OperationType(operation),
        parameters={"file": file} if file else {}
    )

    result = safety_manager.evaluate_and_execute_tool(
        request, bypass_confirmation=force
    )

    if result["success"]:
        click.echo("✅ Tool executed successfully")
    elif result["requires_confirmation"]:
        click.echo(f"⚠️  Confirmation required: {result['confirmation_message']}")
        if click.confirm('Proceed with this operation?'):
            safety_manager.confirm_operation(result["confirmation_id"], True)
            # Execute again with bypass
            result = safety_manager.evaluate_and_execute_tool(request, bypass_confirmation=True)
            click.echo("✅ Tool executed after confirmation")
    else:
        click.echo(f"❌ Operation denied: {result['denied_reason']}")
```

## 📄 License

This tool safety framework is part of TORQ Console and follows the same licensing terms.

## 🤝 Contributing

When contributing to the safety framework:

1. **Security First**: Always consider security implications
2. **Test Thoroughly**: Add comprehensive tests for new features
3. **Document Changes**: Update documentation for all changes
4. **Review Required**: All security changes require code review

---

**🔒 TORQ Console Tool Safety Framework** - Enterprise-grade security for AI tool operations