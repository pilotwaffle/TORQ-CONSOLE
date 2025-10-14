# Terminal Commands Tool - Usage Examples

## Quick Start

### Basic Import and Setup

```python
from torq_console.agents.tools import TerminalCommandsTool, create_terminal_commands_tool

# Create tool instance
tool = create_terminal_commands_tool()

# Check availability
if tool.is_available():
    print("✅ Terminal Commands Tool ready")
else:
    print("❌ Tool unavailable")
```

## Core Usage Patterns

### 1. Execute Simple Command

```python
# Execute a whitelisted command
result = tool.execute(
    action="execute_command",
    command="ls -la"
)

if result['success']:
    print("Output:", result['stdout'])
    print("Exit code:", result['exit_code'])
else:
    print("Error:", result['error'])
```

**Output**:
```
Output: total 48
drwxr-xr-x  12 user  staff   384 Oct 13 10:30 .
drwxr-xr-x   8 user  staff   256 Oct 13 09:15 ..
-rw-r--r--   1 user  staff  1024 Oct 13 10:25 README.md
...

Exit code: 0
```

### 2. Execute with Timeout

```python
# Execute with custom timeout
result = tool.execute(
    action="execute_command",
    command="find . -name '*.py'",
    timeout=10  # 10 seconds
)

if result['success']:
    print("Files found:", result['stdout'].count('\n'))
else:
    if 'timeout' in result['error'].lower():
        print("Command timed out")
    else:
        print("Error:", result['error'])
```

### 3. Execute with Working Directory

```python
# Execute in specific directory
result = tool.execute(
    action="execute_command",
    command="git status",
    working_dir="/path/to/your/repo"
)

if result['success']:
    print("Git status:", result['stdout'])
else:
    print("Error:", result['error'])
```

### 4. Validate Command Before Execution

```python
# Check if command is allowed
validation = tool.execute(
    action="validate_command",
    command="git push origin main"
)

if validation['valid']:
    print("✅ Command is allowed")
else:
    print("❌ Command not allowed:", validation['reason'])
```

**Output**:
```
❌ Command not allowed: Subcommand 'push' not allowed for 'git'. Allowed: ['status', 'log', 'diff', 'branch', 'show']
```

### 5. Get Whitelist Information

```python
# Get list of allowed commands
result = tool.execute(action="get_whitelist")

if result['success']:
    whitelist = result['result']['whitelisted_commands']
    blocked = result['result']['blocked_commands']

    print(f"Whitelisted commands: {len(whitelist)}")
    print(f"Blocked commands: {len(blocked)}")

    # Show some examples
    print("\nSample whitelisted commands:")
    for cmd, subcmds in list(whitelist.items())[:5]:
        if subcmds:
            print(f"  {cmd}: {subcmds}")
        else:
            print(f"  {cmd}: (all arguments allowed)")
```

**Output**:
```
Whitelisted commands: 20
Blocked commands: 25

Sample whitelisted commands:
  ls: (all arguments allowed)
  cat: (all arguments allowed)
  git: ['status', 'log', 'diff', 'branch', 'show']
  npm: ['list', 'view', 'info']
  pip: ['list', 'show', 'freeze']
```

## Prince Flowers Integration Examples

### 1. Using Terminal Commands in Prince Flowers

```python
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

# Initialize agent
prince = TORQPrinceFlowers()

# Execute terminal command via Prince Flowers
result = await prince._execute_terminal_command(
    command="ls -la",
    timeout=30
)

if result['success']:
    print(result['stdout'])
```

### 2. Query-Based Execution

```python
# User query triggers terminal command
query = "Show me the git status of the current repository"

# Prince Flowers processes query and executes command
response = await prince.process_query(query)
print(response)
```

### 3. Validating User Commands

```python
# User wants to run a command
user_command = "git push origin main"

# Validate first
validation = await prince._execute_terminal_command(
    action="validate_command",
    command=user_command
)

if validation['valid']:
    # Execute
    result = await prince._execute_terminal_command(
        command=user_command
    )
else:
    print(f"Command not allowed: {validation['reason']}")
```

## Common Use Cases

### Use Case 1: Check Git Repository Status

```python
def check_git_status(repo_path: str) -> Dict[str, Any]:
    """Check git repository status."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command="git status --short",
        working_dir=repo_path,
        timeout=10
    )

    if result['success']:
        return {
            'clean': len(result['stdout'].strip()) == 0,
            'changes': result['stdout'],
            'message': 'Repository is clean' if not result['stdout'].strip() else 'Uncommitted changes'
        }
    else:
        return {
            'error': result['error']
        }

# Usage
status = check_git_status("/path/to/repo")
print(status)
```

### Use Case 2: List Files in Directory

```python
def list_files(directory: str, pattern: str = "*.py") -> List[str]:
    """List files matching pattern."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command=f"find . -name '{pattern}'",
        working_dir=directory,
        timeout=30
    )

    if result['success']:
        files = result['stdout'].strip().split('\n')
        return [f for f in files if f]
    else:
        return []

# Usage
python_files = list_files("/path/to/project", "*.py")
print(f"Found {len(python_files)} Python files")
```

### Use Case 3: Check Package Dependencies

```python
def check_pip_packages() -> List[Dict[str, str]]:
    """Get list of installed pip packages."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command="pip list --format=json",
        timeout=30
    )

    if result['success']:
        import json
        packages = json.loads(result['stdout'])
        return packages
    else:
        return []

# Usage
packages = check_pip_packages()
for pkg in packages[:5]:
    print(f"{pkg['name']}: {pkg['version']}")
```

### Use Case 4: View File Content

```python
def view_file(filepath: str, lines: int = 10) -> str:
    """View first N lines of file."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command=f"head -n {lines} {filepath}",
        timeout=5
    )

    if result['success']:
        return result['stdout']
    else:
        return f"Error: {result['error']}"

# Usage
content = view_file("README.md", lines=20)
print(content)
```

### Use Case 5: Search in Files

```python
def search_in_files(pattern: str, directory: str) -> List[str]:
    """Search for pattern in files."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command=f"grep -r '{pattern}' .",
        working_dir=directory,
        timeout=30
    )

    if result['success']:
        matches = result['stdout'].strip().split('\n')
        return [m for m in matches if m]
    else:
        return []

# Usage
matches = search_in_files("TODO", "/path/to/project")
print(f"Found {len(matches)} TODOs")
for match in matches[:5]:
    print(f"  {match}")
```

## Error Handling Patterns

### Pattern 1: Graceful Degradation

```python
def safe_execute(command: str) -> Optional[str]:
    """Execute command with graceful error handling."""
    tool = create_terminal_commands_tool()

    try:
        result = tool.execute(
            action="execute_command",
            command=command,
            timeout=30
        )

        if result['success']:
            return result['stdout']
        else:
            print(f"Command failed: {result['error']}")
            return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Pattern 2: Retry with Timeout Adjustment

```python
def execute_with_retry(command: str, max_attempts: int = 3) -> Dict[str, Any]:
    """Execute command with retry logic."""
    tool = create_terminal_commands_tool()
    timeout = 10

    for attempt in range(max_attempts):
        result = tool.execute(
            action="execute_command",
            command=command,
            timeout=timeout
        )

        if result['success']:
            return result

        # If timeout, increase for next attempt
        if 'timeout' in result.get('error', '').lower():
            timeout *= 2
            print(f"Timeout, retrying with {timeout}s timeout...")
        else:
            # Non-timeout error, don't retry
            break

    return result
```

### Pattern 3: Validation Before Execution

```python
def safe_git_command(subcommand: str, args: str = "") -> Dict[str, Any]:
    """Execute git command with validation."""
    tool = create_terminal_commands_tool()

    command = f"git {subcommand} {args}".strip()

    # Validate first
    validation = tool.execute(
        action="validate_command",
        command=command
    )

    if not validation['valid']:
        return {
            'success': False,
            'error': f"Invalid command: {validation['reason']}"
        }

    # Execute
    return tool.execute(
        action="execute_command",
        command=command,
        timeout=30
    )

# Usage
result = safe_git_command("log", "--oneline -10")
if result['success']:
    print(result['stdout'])
```

## Advanced Patterns

### Pattern 1: Batch Command Execution

```python
def execute_batch(commands: List[str]) -> List[Dict[str, Any]]:
    """Execute multiple commands sequentially."""
    tool = create_terminal_commands_tool()
    results = []

    for command in commands:
        result = tool.execute(
            action="execute_command",
            command=command,
            timeout=30
        )
        results.append(result)

        # Stop on first failure
        if not result['success']:
            print(f"Batch execution stopped at: {command}")
            break

    return results

# Usage
commands = [
    "git status",
    "git log --oneline -5",
    "git diff --stat"
]
results = execute_batch(commands)
```

### Pattern 2: Command Output Parsing

```python
def parse_git_log(repo_path: str) -> List[Dict[str, str]]:
    """Parse git log output into structured data."""
    tool = create_terminal_commands_tool()

    result = tool.execute(
        action="execute_command",
        command="git log --pretty=format:'%h|%an|%s' -10",
        working_dir=repo_path,
        timeout=10
    )

    if not result['success']:
        return []

    commits = []
    for line in result['stdout'].strip().split('\n'):
        if '|' in line:
            hash, author, message = line.split('|', 2)
            commits.append({
                'hash': hash,
                'author': author,
                'message': message
            })

    return commits

# Usage
commits = parse_git_log("/path/to/repo")
for commit in commits:
    print(f"{commit['hash']}: {commit['message']}")
```

### Pattern 3: Conditional Execution

```python
def conditional_execute(condition_cmd: str, action_cmd: str) -> bool:
    """Execute action command only if condition succeeds."""
    tool = create_terminal_commands_tool()

    # Check condition
    condition = tool.execute(
        action="execute_command",
        command=condition_cmd,
        timeout=10
    )

    if not condition['success']:
        print("Condition failed, skipping action")
        return False

    # Execute action
    action = tool.execute(
        action="execute_command",
        command=action_cmd,
        timeout=30
    )

    return action['success']

# Usage: Only show git diff if there are changes
success = conditional_execute(
    condition_cmd="git diff --quiet",  # Returns 1 if differences
    action_cmd="git diff --stat"
)
```

## Security Best Practices

### 1. Always Validate User Input

```python
def execute_user_command(user_input: str) -> Dict[str, Any]:
    """Execute user-provided command safely."""
    tool = create_terminal_commands_tool()

    # ALWAYS validate first
    validation = tool.execute(
        action="validate_command",
        command=user_input
    )

    if not validation['valid']:
        return {
            'success': False,
            'error': f"Command not allowed: {validation['reason']}"
        }

    # Get user confirmation for execution
    print(f"About to execute: {user_input}")
    confirm = input("Proceed? (yes/no): ")

    if confirm.lower() != 'yes':
        return {
            'success': False,
            'error': 'User cancelled execution'
        }

    # Execute
    return tool.execute(
        action="execute_command",
        command=user_input,
        timeout=30
    )
```

### 2. Use Timeouts Appropriately

```python
# SHORT timeout for quick operations
result = tool.execute(
    action="execute_command",
    command="pwd",
    timeout=5  # 5 seconds sufficient
)

# LONGER timeout for complex operations
result = tool.execute(
    action="execute_command",
    command="find . -name '*.py'",
    timeout=60  # May need more time for large directories
)

# NEVER use unlimited timeout
# BAD: timeout=None or timeout=9999
```

### 3. Validate Working Directories

```python
def execute_in_directory(command: str, directory: str) -> Dict[str, Any]:
    """Execute command with directory validation."""
    import os
    from pathlib import Path

    tool = create_terminal_commands_tool()

    # Validate directory exists
    if not Path(directory).exists():
        return {
            'success': False,
            'error': f"Directory does not exist: {directory}"
        }

    # Validate it's actually a directory
    if not Path(directory).is_dir():
        return {
            'success': False,
            'error': f"Path is not a directory: {directory}"
        }

    # Execute
    return tool.execute(
        action="execute_command",
        command=command,
        working_dir=directory,
        timeout=30
    )
```

## Testing Examples

### Unit Test Example

```python
import unittest
from torq_console.agents.tools import create_terminal_commands_tool

class TestTerminalCommands(unittest.TestCase):

    def setUp(self):
        self.tool = create_terminal_commands_tool()

    def test_whitelisted_command(self):
        """Test whitelisted command executes."""
        result = self.tool.execute(
            action="execute_command",
            command="echo test"
        )
        self.assertTrue(result['success'])
        self.assertIn('test', result['stdout'])

    def test_blocked_command(self):
        """Test blocked command is rejected."""
        result = self.tool.execute(
            action="execute_command",
            command="rm test.txt"
        )
        self.assertFalse(result['success'])
        self.assertIn('blocked', result['error'].lower())

if __name__ == '__main__':
    unittest.main()
```

## Troubleshooting

### Issue: "Command not found"

**Cause**: Command not installed on system

**Solution**:
```python
# Check if command exists first
result = tool.execute(
    action="execute_command",
    command="which git"  # Unix
    # or "where git" on Windows
)

if result['success']:
    print("Git is installed")
else:
    print("Git not found")
```

### Issue: "Command timeout"

**Cause**: Operation takes longer than timeout

**Solution**:
```python
# Increase timeout
result = tool.execute(
    action="execute_command",
    command="find / -name '*.log'",
    timeout=120  # Increase from default 30s
)
```

### Issue: "Working directory does not exist"

**Cause**: Invalid working directory

**Solution**:
```python
import os

# Use absolute path
abs_path = os.path.abspath("/path/to/dir")

result = tool.execute(
    action="execute_command",
    command="ls",
    working_dir=abs_path
)
```

## Conclusion

The Terminal Commands Tool provides secure, controlled terminal access for AI agents with comprehensive security controls. Follow the patterns and best practices in this guide to use it safely and effectively.

**Key Takeaways**:
- Always validate commands before execution
- Use appropriate timeouts
- Handle errors gracefully
- Check whitelist for allowed commands
- Never bypass security controls

---

*For security information, see: TERMINAL_COMMANDS_SECURITY.md*
*For implementation details, see: terminal_commands_tool.py*
