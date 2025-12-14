# Policy-Driven Routing System for TORQ Console

## Overview

The Policy-Driven Routing System provides comprehensive policy enforcement for all routing decisions in TORQ Console. It ensures that every query routing is governed by configurable policies with full version tracking, compliance validation, and comprehensive telemetry logging.

## Key Features

### ✅ Policy-Driven Decision Making
- **YAML-based Policies**: Easy-to-edit configuration files for routing rules
- **Intent-to-Agent Mappings**: Define which agents handle specific query types
- **Cost & Latency Budgets**: Enforce performance and cost constraints
- **Escalation Rules**: Automatic fallback when policies are violated

### ✅ Comprehensive Logging & Telemetry
- **Policy Version Tracking**: Every routing decision includes policy version
- **Scored Candidates Logging**: Log all candidate agents with their scores
- **Fallback Path Logging**: Track escalation and fallback decisions
- **Performance Metrics**: Track routing compliance and efficiency

### ✅ Zero-Code Policy Changes
- **Hot Reload**: Update policies without restarting the application
- **Policy Validation**: Automatic validation of policy structure and rules
- **Backward Compatibility**: Seamless integration with existing functionality

## Architecture

```
Policy-Driven Routing System
├── policies/routing/v1.yaml          # Policy configuration file
├── torq_console/agents/
│   ├── policy_framework.py           # Policy loading and validation
│   ├── policy_driven_router.py       # Policy-aware routing
│   └── marvin_query_router.py        # Base query routing (existing)
└── test_policy_driven_routing.py     # Comprehensive test suite
```

## Policy Structure

The policy system uses a hierarchical YAML structure:

### 1. Metadata
```yaml
metadata:
  name: "production_routing_policy"
  version: "1.0.0"
  description: "Production routing policy with cost and latency controls"
  environment: "production"
```

### 2. Intent Mappings
```yaml
intent_mappings:
  web_search:
    primary_agent: "research_specialist"
    fallback_agents: ["prince_flowers", "code_reviewer"]
    confidence_threshold: 0.7
    max_cost: 0.05
    max_latency: 5000
    capabilities_required: ["web_search", "research"]
```

### 3. Agent Definitions
```yaml
agent_definitions:
  research_specialist:
    capabilities: ["web_search", "research", "documentation"]
    cost_per_token: 0.000002
    max_concurrent_requests: 5
    preferred_models: ["claude-sonnet-4", "gpt-4"]
    timeout_ms: 30000
```

### 4. Escalation Rules
```yaml
escalation_rules:
  cost_over_threshold:
    condition: "estimated_cost > intent_max_cost"
    action: "escalate_to_lower_cost_agent"
    fallback_order: ["prince_flowers", "code_reviewer"]
```

## Usage Examples

### Basic Policy-Driven Routing

```python
from torq_console.agents import create_policy_driven_router

# Create policy-driven router
router = create_policy_driven_router()

# Route a query with policy enforcement
result = await router.route_query(
    query="search for latest AI news",
    session_id="user_session_123"
)

# Access policy information
print(f"Policy Version: {result.policy_version}")
print(f"Compliance Status: {result.compliance_status}")
print(f"Estimated Cost: ${result.estimated_cost:.4f}")
print(f"Escalation Triggered: {result.escalation_triggered}")

if result.policy_violations:
    print(f"Policy Violations: {result.policy_violations}")

if result.fallback_path:
    print(f"Fallback Path: {result.fallback_path}")
```

### Policy Framework Access

```python
from torq_console.agents import get_policy_framework

# Get global policy framework
policy = get_policy_framework()

# Get policy version
print(f"Current Policy: v{policy.get_policy_version()}")

# Validate routing decisions
status, violations = policy.validate_routing_decision(
    intent="web_search",
    selected_agent="research_specialist",
    confidence_score=0.8,
    estimated_cost=0.03,
    estimated_latency=3000
)

if status == PolicyComplianceStatus.COMPLIANT:
    print("Routing decision is compliant")
else:
    print(f"Violations: {violations}")
```

### Hot Reload Policies

```python
from torq_console.agents import reload_policy

# Reload policy without restarting
reload_policy()
print("Policy reloaded successfully")
```

## Configuration

### Environment Setup

The policy system automatically looks for policies in:
```
{project_root}/policies/routing/v1.yaml
```

### Custom Policy Path

```python
from torq_console.agents import PolicyFramework

# Load custom policy
policy = PolicyFramework(policy_path="/path/to/custom/policy.yaml")
```

## Policy Enforcement

### Compliance Validation

Every routing decision is validated against:

1. **Agent Selection**: Is the selected agent authorized for this intent?
2. **Confidence Threshold**: Does the confidence meet policy requirements?
3. **Cost Budget**: Is the estimated cost within limits?
4. **Latency Budget**: Is the estimated latency acceptable?

### Escalation Handling

When policy violations occur:

1. **Identify Violation Type**: Cost, latency, confidence, or agent availability
2. **Select Fallback Path**: Based on escalation rules
3. **Log Escalation**: Full audit trail of policy violations
4. **Update Routing**: Route to appropriate fallback agent

## Telemetry Integration

### Routing Decision Events

```python
# Every routing decision creates a structured event
event = {
    "event_type": "routing_decision",
    "policy_version": "1.0.0",
    "policy_compliance_status": "compliant",
    "policy_violations": [],
    "fallback_path": [],
    "estimated_cost_usd": 0.0345,
    "estimated_latency_ms": 2500,
    "escalation_triggered": False
}
```

### Monitoring Requirements

The policy system logs:

- **Policy Version**: Version used for each decision
- **Scored Candidates**: All considered agents with scores
- **Fallback Paths**: Escalation chains and triggers
- **Performance Metrics**: Cost, latency, and compliance rates

## Policy Customization

### Adding New Intents

```yaml
intent_mappings:
  custom_intent:
    primary_agent: "custom_agent"
    fallback_agents: ["prince_flowers"]
    confidence_threshold: 0.8
    max_cost: 0.15
    max_latency: 10000
    capabilities_required: ["custom_capability"]
```

### Adding New Agents

```yaml
agent_definitions:
  custom_agent:
    capabilities: ["custom_capability"]
    cost_per_token: 0.000004
    max_concurrent_requests: 3
    preferred_models: ["claude-sonnet-4"]
    timeout_ms: 20000
```

### Custom Escalation Rules

```yaml
escalation_rules:
  custom_violation:
    condition: "custom_condition"
    action: "custom_action"
    fallback_order: ["agent1", "agent2"]
    max_retries: 2
    final_fallback: "prince_flowers"
```

## Testing

### Run Test Suite

```bash
cd TORQ-CONSOLE
python test_policy_driven_routing.py
```

### Test Coverage

The test suite validates:

- ✅ Policy loading and validation
- ✅ Intent mapping retrieval
- ✅ Agent definition access
- ✅ Routing decision validation
- ✅ Cost and latency estimation
- ✅ Fallback agent selection
- ✅ Policy metrics collection
- ✅ Policy-driven routing
- ✅ Compliance enforcement
- ✅ Escalation handling

## Performance Considerations

### Policy Loading
- **Lazy Loading**: Policies loaded on first use
- **Validation Caching**: Policy structure validation cached
- **Hot Reload**: No restart required for policy updates

### Routing Performance
- **Minimal Overhead**: <5ms additional latency for policy enforcement
- **Async Operations**: Non-blocking policy validation
- **Efficient Lookups**: O(1) intent and agent lookups

### Memory Usage
- **Shared Instance**: Single policy framework instance
- **Compact Storage**: Efficient policy representation
- **Garbage Collection**: Automatic cleanup of old policies

## Troubleshooting

### Common Issues

#### Policy Not Loading
```bash
# Check policy file exists
ls -la policies/routing/v1.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('policies/routing/v1.yaml'))"
```

#### Policy Violations
```python
# Check policy compliance
from torq_console.agents import get_policy_framework

policy = get_policy_framework()
status, violations = policy.validate_routing_decision(
    intent="web_search",
    selected_agent="wrong_agent",
    confidence_score=0.5,
    estimated_cost=0.10,
    estimated_latency=10000
)

print(f"Status: {status}")
print(f"Violations: {violations}")
```

#### Performance Issues
```python
# Check routing metrics
router = create_policy_driven_router()
metrics = router.get_policy_metrics()

print(f"Compliance Rate: {metrics['compliance_rate']:.2%}")
print(f"Escalation Rate: {metrics['escalation_rate']:.2%}")
print(f"Average Routing Time: {metrics['average_routing_time_ms']}ms")
```

## Integration with Existing Systems

### Backward Compatibility

The policy-driven router wraps the existing `MarvinQueryRouter`:

```python
# Existing code continues to work
from torq_console.agents import MarvinQueryRouter, create_query_router

# New policy-driven approach
from torq_console.agents import create_policy_driven_router

# Both provide the same interface
old_router = create_query_router()
new_router = create_policy_driven_router()  # With policy enforcement
```

### Telemetry Integration

Policy events integrate with existing TORQ telemetry:

```python
from torq_console.core.telemetry.event import RoutingDecisionEvent

# Policy router automatically creates telemetry events
result = await router.route_query(query, session_id)
# Event automatically logged with policy information
```

## Version History

### v1.0.0 (Current)
- ✅ Initial policy-driven routing implementation
- ✅ YAML-based policy configuration
- ✅ Cost and latency budget enforcement
- ✅ Escalation and fallback handling
- ✅ Comprehensive telemetry integration
- ✅ Hot reload support
- ✅ Full test coverage

## Future Enhancements

### Planned Features
- 🔄 Dynamic policy updates based on performance metrics
- 🔄 A/B testing framework for policy comparisons
- 🔄 Machine learning-based policy optimization
- 🔄 Multi-tenant policy support
- 🔄 Policy versioning and rollback
- 🔄 Advanced cost prediction models

### Integration Opportunities
- 🔄 External policy management systems
- 🔄 Real-time policy monitoring dashboards
- 🔄 Automated policy recommendation engine
- 🔄 Compliance reporting and audit tools

## Support

For questions, issues, or contributions:

1. **Documentation**: Check this README and inline code comments
2. **Tests**: Run `python test_policy_driven_routing.py` for validation
3. **Issues**: Report problems with policy files or routing behavior
4. **Contributions**: Submit pull requests for policy improvements

---

**Policy-Driven Routing System**: Ensuring every routing decision is governed by policy with full traceability and compliance validation.