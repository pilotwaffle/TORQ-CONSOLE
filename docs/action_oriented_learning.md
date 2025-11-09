# Action-Oriented Learning for Prince Flowers

## Overview

The Action-Oriented Learning system enhances Prince Flowers to make better decisions about **when to act** versus **when to ask questions**. This was developed in response to user feedback where Prince offered "multiple options" when users wanted immediate action (like performing a web search).

## The Problem

**Before Enhancement:**
```
User: "Under ideation: search for top 2 viral TikTok videos"

Prince: ❌ "I can help! Would you like me to:
  1. Use WebSearch to find them
  2. Build a TypeScript tool for searching
  3. Create an n8n workflow..."

User: "No! I just wanted you to search!"
```

**After Enhancement:**
```
User: "Under ideation: search for top 2 viral TikTok videos"

Prince: ✅ *Immediately uses WebSearch*
"Here are the top 2 viral TikTok videos:
1. Zach King - Flying Broomstick (2.8B views)
2. Slow Motion Bird Bath (most viewed 2025)..."
```

## Key Concepts

### Action Decisions

The system categorizes agent responses into three types:

1. **IMMEDIATE_ACTION** - Act now, don't ask
   - Use for: Research, web search, information retrieval
   - Keywords: "search", "find", "look up", "show me", "under ideation"
   - Example: "search for top React libraries" → Immediately search

2. **ASK_CLARIFICATION** - Ask targeted questions first
   - Use for: Building tools, implementing features, complex tasks
   - Keywords: "build", "create", "develop", "implement"
   - Example: "build a monitoring dashboard" → Ask about requirements

3. **PROVIDE_OPTIONS** - Offer multiple approaches
   - Use for: Genuinely ambiguous requests
   - Should be rare
   - Example: "help with database choice" → Offer options with pros/cons

### Request Patterns

Common patterns recognized by the system:

| Pattern | Keywords | Action |
|---------|----------|--------|
| **Research** | search, find, look up, get, show, list | Immediate Action |
| **Ideation** | under ideation, brainstorm, explore | Immediate Action |
| **Building** | build, create, develop, implement | Ask Clarification |
| **Explanation** | explain, how does, what is | Immediate Action |
| **Debugging** | fix, debug, error, not working | Ask Clarification |

## Components

### 1. ActionOrientedLearning

Analyzes requests and learns from feedback.

```python
from torq_console.agents import get_action_learning

learning = get_action_learning()

# Analyze a request
analysis = learning.analyze_request("search for top AI tools")
# → {'recommended_action': 'immediate_action', 'confidence': 0.9, ...}

# Learn from feedback
learning.learn_from_feedback(
    user_request="find trending topics",
    agent_action=ActionDecision.PROVIDE_OPTIONS,  # What Prince did
    user_expected=ActionDecision.IMMEDIATE_ACTION,  # What user wanted
    feedback_score=0.2  # Low score = bad response
)
```

### 2. EnhancedPrinceFlowers

Prince Flowers with action-oriented behavior.

```python
from torq_console.agents import create_enhanced_prince_flowers

prince = create_enhanced_prince_flowers()

# Chat with action analysis
response = await prince.chat("search for viral videos")

# Record feedback
prince.record_user_feedback(
    expected_action=ActionDecision.IMMEDIATE_ACTION,
    feedback_score=0.9  # Good response
)

# Get learning stats
stats = prince.get_learning_stats()
```

### 3. Built-in Patterns

Pre-configured patterns for common scenarios:

- **research_immediate_action** (confidence: 0.9)
  - Keywords: search, find, look up, get, show, list, top, best, latest
  - Action: Immediate Action
  - Examples: "search for X", "find top Y", "show me latest Z"

- **build_ask_clarification** (confidence: 0.85)
  - Keywords: build, create, develop, implement, design
  - Action: Ask Clarification
  - Examples: "build a tool", "create an app", "implement a system"

- **ambiguous_provide_options** (confidence: 0.7)
  - Keywords: help with, advice on, suggestions for
  - Action: Provide Options
  - Examples: "help me choose", "advice on picking"

## Quick Start

### 1. Apply the TikTok Lesson

This permanently teaches Prince the lesson learned from the TikTok search feedback:

```python
from torq_console.agents import apply_tiktok_lesson

# Run once to teach the lesson
apply_tiktok_lesson()
```

What this does:
- Adds a high-confidence pattern for "under ideation" + "search"
- Teaches Prince to immediately search, not ask how to build
- Stores the lesson in persistent memory

### 2. Use Enhanced Prince Flowers

Replace regular Prince with the enhanced version:

```python
# Old way
from torq_console.agents import create_prince_flowers_agent
prince = create_prince_flowers_agent()

# New way (action-oriented)
from torq_console.agents import create_enhanced_prince_flowers
prince = create_enhanced_prince_flowers()
```

### 3. Provide Feedback

Help Prince learn from interactions:

```python
# After a response
prince.record_user_feedback(
    expected_action=ActionDecision.IMMEDIATE_ACTION,
    feedback_score=0.9,  # 0.0 (bad) to 1.0 (good)
    feedback_comment="Perfect! Just what I wanted"
)
```

## Usage Examples

### Example 1: Research Request

```python
import asyncio
from torq_console.agents import create_enhanced_prince_flowers

async def research_example():
    prince = create_enhanced_prince_flowers()

    # User wants immediate results
    response = await prince.chat(
        "search for top 5 Python web frameworks"
    )

    # Prince immediately searches (no questions)
    # Uses WebSearch tool and returns results

asyncio.run(research_example())
```

### Example 2: Build Request

```python
async def build_example():
    prince = create_enhanced_prince_flowers()

    # User wants to build something
    response = await prince.chat(
        "build a tool to monitor API performance"
    )

    # Prince asks clarifying questions:
    # - What metrics to track?
    # - Real-time or batch?
    # - Alert thresholds?
    # Then implements after clarification

asyncio.run(build_example())
```

### Example 3: Feedback Loop

```python
async def feedback_example():
    prince = create_enhanced_prince_flowers()

    # Interaction 1: Prince gets it wrong
    response1 = await prince.chat("find trending hashtags")

    if "Would you like me to" in response1:  # Prince asked instead of searching
        # Provide negative feedback
        prince.record_user_feedback(
            expected_action=ActionDecision.IMMEDIATE_ACTION,
            feedback_score=0.3,
            feedback_comment="Just search, don't ask!"
        )

    # Interaction 2: Prince improves
    response2 = await prince.chat("find viral memes")
    # Now Prince immediately searches!

    # Provide positive feedback
    prince.record_user_feedback(
        expected_action=ActionDecision.IMMEDIATE_ACTION,
        feedback_score=0.95,
        feedback_comment="Perfect! That's what I wanted"
    )

asyncio.run(feedback_example())
```

## Learning Statistics

Monitor Prince's learning progress:

```python
prince = create_enhanced_prince_flowers()
stats = prince.get_learning_stats()

print(stats)
# {
#   'action_learning': {
#     'total_patterns': 8,
#     'learned_patterns': 2,
#     'built_in_patterns': 3,
#     'average_confidence': 0.83
#   },
#   'memory': {
#     'total_interactions': 127,
#     'success_rate': 0.89,
#     'average_feedback': 0.76,
#     'learned_patterns': 5
#   },
#   'agent_performance': {
#     'total_interactions': 127,
#     'success_rate': 0.89,
#     'conversation_turns': 85
#   }
# }
```

## Integration with Existing Code

### Minimal Changes Required

If you're already using Prince Flowers:

```python
# Change ONE line:
# from torq_console.agents import create_prince_flowers_agent
from torq_console.agents import create_enhanced_prince_flowers

# Everything else stays the same
# prince = create_prince_flowers_agent()
prince = create_enhanced_prince_flowers()

# All existing methods work
response = await prince.chat("your message")
prince.update_preferences({"code_style": "google"})
state = prince.get_state()
```

### Adding Feedback (Optional)

For even better learning:

```python
# After any interaction where you have feedback
prince.record_user_feedback(
    expected_action=ActionDecision.IMMEDIATE_ACTION,  # or ASK_CLARIFICATION
    feedback_score=0.85  # Your assessment (0-1)
)
```

## How It Works

### 1. Request Analysis

When a user sends a message:

```python
# User message
"search for trending topics"

# System analyzes
→ Keywords matched: ['search', 'trending']
→ Pattern matched: 'research_immediate_action'
→ Confidence: 0.92
→ Recommended action: IMMEDIATE_ACTION
```

### 2. Action Execution

Based on analysis:

```python
if confidence > 0.7 and action == IMMEDIATE_ACTION:
    # Act immediately
    perform_web_search()
elif action == ASK_CLARIFICATION:
    # Ask 2-3 targeted questions
    ask_clarifying_questions()
else:
    # Provide options
    offer_multiple_approaches()
```

### 3. Learning from Feedback

When feedback is provided:

```python
if feedback_score < 0.5:  # Negative feedback
    # Extract keywords
    keywords = extract_keywords(user_request)

    # Create new pattern
    new_pattern = {
        'keywords': keywords,
        'action': user_expected_action,
        'confidence': 0.7,
        'learned_from_feedback': True
    }

    # Store in memory
    memory.learn_pattern('action_decision', new_pattern)
```

## Best Practices

### 1. When to Use Enhanced Prince

✅ **Use when:**
- Building chatbots or assistants
- Handling diverse user requests (research + build + explain)
- Want the agent to learn from interactions
- Need decisive, action-oriented behavior

❌ **Don't use when:**
- Only doing code generation (use CodeGenerationAgent)
- Only doing debugging (use DebuggingAgent)
- Single-purpose tasks

### 2. Providing Effective Feedback

**Good Feedback:**
```python
prince.record_user_feedback(
    expected_action=ActionDecision.IMMEDIATE_ACTION,
    feedback_score=0.9,
    feedback_comment="Exactly what I needed - quick research"
)
```

**Bad Feedback:**
```python
prince.record_user_feedback(
    expected_action=ActionDecision.IMMEDIATE_ACTION,
    feedback_score=0.5,  # Neutral - not helpful for learning
    feedback_comment=None  # No context
)
```

### 3. Monitoring Learning

Check stats regularly:

```python
stats = prince.get_learning_stats()

if stats['memory']['average_feedback'] < 0.5:
    print("Warning: Low satisfaction - review patterns")

if stats['action_learning']['learned_patterns'] > 10:
    print("Good: Agent is learning from feedback")
```

## Troubleshooting

### Prince Still Asking Instead of Acting

**Problem:** Prince asks "Would you like me to..." for research requests

**Solutions:**
1. Apply the TikTok lesson: `apply_tiktok_lesson()`
2. Provide negative feedback with expected action
3. Check if enhanced version is being used
4. Review action learning patterns

### Prince Acting When Should Ask

**Problem:** Prince builds/implements without clarification

**Solution:**
- Provide feedback with `ASK_CLARIFICATION` as expected action
- Use more specific keywords: "build", "create", "implement"

### Learning Not Persisting

**Problem:** Patterns not saved between sessions

**Solution:**
- Check memory storage path: `~/.torq/agent_memory/`
- Verify write permissions
- Check logs for save errors

## Advanced Usage

### Custom Action Patterns

Add your own patterns:

```python
from torq_console.agents import get_action_learning, ActionPattern, ActionDecision

learning = get_action_learning()

custom_pattern = ActionPattern(
    pattern_name="company_specific_research",
    request_keywords=["company data", "internal metrics", "dashboard view"],
    recommended_action=ActionDecision.IMMEDIATE_ACTION,
    confidence=0.85,
    examples=["show company metrics", "get internal data"],
    learned_from_feedback=False
)

learning.action_patterns.append(custom_pattern)
```

### Batch Feedback Application

Learn from historical data:

```python
historical_interactions = [
    ("search X", ActionDecision.PROVIDE_OPTIONS, ActionDecision.IMMEDIATE_ACTION, 0.2),
    ("find Y", ActionDecision.PROVIDE_OPTIONS, ActionDecision.IMMEDIATE_ACTION, 0.3),
    ("build Z", ActionDecision.IMMEDIATE_ACTION, ActionDecision.ASK_CLARIFICATION, 0.4),
]

for request, agent_action, expected, score in historical_interactions:
    learning.learn_from_feedback(request, agent_action, expected, score)
```

## API Reference

### ActionDecision Enum

```python
class ActionDecision(str, Enum):
    IMMEDIATE_ACTION = "immediate_action"
    ASK_CLARIFICATION = "ask_clarification"
    PROVIDE_OPTIONS = "provide_options"
```

### EnhancedPrinceFlowers Methods

```python
class EnhancedPrinceFlowers:
    async def chat(message: str, context: Dict = None) -> str
    def record_user_feedback(expected_action: ActionDecision, feedback_score: float, feedback_comment: str = None)
    def get_learning_stats() -> Dict[str, Any]
```

### ActionOrientedLearning Methods

```python
class ActionOrientedLearning:
    def analyze_request(user_request: str) -> Dict[str, Any]
    def learn_from_feedback(user_request: str, agent_action: ActionDecision, user_expected: ActionDecision, feedback_score: float)
    def get_learning_summary() -> Dict[str, Any]
```

## Resources

- **Implementation:** `torq_console/agents/action_learning.py`
- **Enhanced Prince:** `torq_console/agents/prince_flowers_enhanced.py`
- **Examples:** `examples/enhanced_prince_flowers_demo.py`
- **Memory System:** `torq_console/agents/marvin_memory.py`

## Support

For issues or questions:
- GitHub Issues: https://github.com/pilotwaffle/TORQ-CONSOLE/issues
- Documentation: See `CLAUDE.md` in repository

---

**Status:** Production Ready ✅
**Integration:** TORQ Console v0.80.0+ with Marvin 3.0
**Version:** 1.0
**Last Updated:** 2025-11-07
