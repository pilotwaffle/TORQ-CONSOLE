# Capabilities Configuration

This file (`capabilities.yaml`) defines the testable capabilities of the TORQ Console system, organized by user personas.

## Structure

### Version
- Current version: `1`
- Tracks the schema version of the capabilities configuration

### Personas

#### basic_user
- **Description**: Local usage with built-in commands and no external API keys required
- **Access Level**: Core CLI functionality without external dependencies

#### power_user
- **Description**: Access to the full CLI surface and evaluation workflows
- **Access Level**: Advanced features including evaluation, benchmarking, and MCP connections

### Capabilities

Each capability includes:
- **id**: Unique identifier
- **personas**: List of personas that have access to this capability
- **description**: Human-readable description of what the capability provides
- **dependencies**: Required capabilities or dependencies (if any)
- **verify**: Test specification for validating the capability
  - **command**: Shell command to run for verification
  - **expect**: Expected outcome (`success` or `blocked`)
  - **success_contains**: (For success) List of strings that should appear in output
  - **blocked_reason**: (For blocked) Reason why the command should be blocked
  - **artifacts**: Paths where test artifacts should be stored
- **negative_cases**: (Optional) List of behaviors that should NOT occur

## Current Capabilities

### CLI Help Commands (Success Expected)
1. **cli_help**: Primary TORQ Console CLI help menu
2. **eval_help**: Evaluation runner options documentation
3. **bench_help**: Benchmarking and SLO configuration
4. **mcp_help**: MCP server connection documentation
5. **config_init_help**: Configuration initialization guidance
6. **serve_help**: Web UI server startup documentation

### Validation Commands (Blocked Expected)
7. **eval_requires_set**: Ensures `--set` parameter is required for eval command
8. **mcp_requires_endpoint**: Ensures `--endpoint` parameter is required for mcp command

### Security/Sandbox Tests (Blocked Expected)
9. **sandbox_blocks_proc_mem**: Verifies read access to `/proc/1/mem` is denied
10. **sandbox_blocks_write_outside_workspace**: Verifies write access to `/proc/1/mem` is denied

## Usage

### Validating Capabilities

Run the validation script to test all capabilities:

```bash
python validate_capabilities.py
```

This will:
1. Load the capabilities.yaml file
2. Execute each capability's verification command
3. Check if the outcome matches expectations
4. Generate a detailed report in `capability_validation_results.json`

### Adding New Capabilities

To add a new capability:

1. Choose appropriate persona(s) for access
2. Define a unique `id`
3. Write a clear `description`
4. Create a `verify` specification with:
   - A testable `command`
   - Expected outcome (`success` or `blocked`)
   - Validation criteria (success_contains or blocked_reason)
5. Define artifact storage paths using `{git_sha}` placeholder

Example:

```yaml
- id: new_feature_help
  personas: [basic_user, power_user]
  description: "Document the new feature usage."
  dependencies: []
  verify:
    command: "python -m torq_console.cli new-feature --help"
    expect: success
    success_contains:
      - "New feature documentation"
      - "Usage:"
    artifacts:
      log: "reports/capabilities/{git_sha}/new_feature_help.log"
```

## Artifact Storage

Test artifacts (logs) are stored in:
```
reports/capabilities/{git_sha}/
```

Where `{git_sha}` is replaced with the current Git commit SHA at runtime, enabling:
- Historical tracking of capability validation across commits
- Regression analysis
- CI/CD integration

## Integration with CI/CD

This capabilities configuration can be integrated into CI/CD pipelines to:
- Validate that expected features work correctly
- Ensure security boundaries are maintained
- Prevent regressions in core functionality
- Document system capabilities for users

## Notes

- Commands that expect `blocked` should return non-zero exit codes
- Commands that expect `success` should return zero exit codes
- Sandbox tests verify OS-level security boundaries
- All capabilities should be testable without external API keys for basic_user persona
