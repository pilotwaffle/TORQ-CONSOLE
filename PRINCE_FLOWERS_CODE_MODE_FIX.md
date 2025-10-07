# Prince Flowers Code Generation Mode Fix

**Date:** 2025-10-06
**Issue:** Prince Flowers doing research instead of code generation
**Solution:** Configure agent for code-focused tasks based on Claude Agent SDK principles

---

## 🎯 The Problem

Based on Claude Agent SDK article research, the issue is clear:

**Current Behavior:**
- Prince Flowers entering "gather context" mode (research/composition)
- Using 3 composition steps to analyze
- Returning research results instead of code

**Expected Behavior:**
- Prince Flowers should "take action" mode (code generation)
- Generate actual application code
- Create file structures and implementations

---

## 📚 Claude Agent SDK Insights

### Key Principle from Anthropic
> "Design agents around a core feedback loop: **gather context → take action → verify work → repeat**"

### Agent Modes

**Gather Context Mode:**
- Agentic file system search
- Semantic search
- Research and analysis
- ❌ This is what Prince is currently doing

**Take Action Mode:**
- Custom tool creation
- Code generation
- Bash/scripting
- ✅ This is what Prince should be doing

---

## 🔧 The Fix Strategy

### Option 1: System Prompt Override (Immediate)

When routing to Prince Flowers for BUILD tasks, add a strong system prompt:

```python
system_prompt = """You are Prince Flowers, an expert code generation agent.

CRITICAL INSTRUCTIONS:
- Your PRIMARY task is CODE GENERATION, not research
- When given a project specification, GENERATE ACTUAL CODE
- Do NOT do web research or composition analysis
- Do NOT return information ABOUT building - BUILD IT
- Output: Working code files, project structure, implementation

WORKFLOW:
1. Analyze the specification
2. Generate complete, working code
3. Provide file structure
4. Include all necessary files

You are in CODE GENERATION MODE. Build the application NOW.
"""
```

### Option 2: Mode Parameter (Better)

Add explicit mode detection in Prince Flowers integration:

```python
def route_to_prince_flowers(query, mode='code'):
    if mode == 'code' or mode == 'build':
        # Use code generation system prompt
        return prince_flowers.generate_code(query)
    elif mode == 'research':
        # Use research mode
        return prince_flowers.research(query)
```

### Option 3: Skip Prince Flowers for Code (Fastest)

Route BUILD requests directly to Claude Sonnet 4.5 code_generation method:

```python
if mode == 'build':
    # Skip Prince Flowers agentic system
    # Go directly to Claude code generation
    return claude_provider.code_generation(query)
```

---

## 💡 Recommended Solution

Use **Option 3** (direct Claude code generation) for immediate results, then enhance Prince Flowers later.

### Why This Works

1. **Claude Sonnet 4.5 is NOW working** - We just fixed the provider
2. **Direct code generation** - No agentic overhead
3. **Fast and reliable** - Proven code generation quality
4. **Prince for research** - Keep Prince for actual research tasks

### Implementation

Update `_handle_basic_query_fixed()` to call Claude directly:

```python
async def _handle_basic_query_fixed(self, query: str, context_matches: Optional[List] = None) -> str:
    """Handle BUILD MODE - direct code generation."""

    # Try Claude provider directly for code generation
    if hasattr(self.console, 'llm_manager') and self.console.llm_manager:
        # Get Claude provider
        claude = self.console.llm_manager.get_provider('claude')

        if claude and claude.is_configured():
            try:
                # Use Claude's code_generation method directly
                response = await claude.code_generation(
                    task_description=query,
                    language='typescript',  # or detect from query
                    context='Build a complete, production-ready application',
                    temperature=0.3,
                    max_tokens=8000
                )
                return response
            except Exception as e:
                self.logger.error(f"Claude code generation failed: {e}")

    # Fallback to other methods...
```

---

## 🎯 Expected Results After Fix

### Before Fix:
```
User: Prince Build an AI Prompt Library
Prince: "Based on comprehensive analysis using 3 composition steps..."
Result: Research about building, not actual code
```

### After Fix:
```
User: Prince Build an AI Prompt Library
Claude: [Generates actual code]
Result: Complete Next.js app with:
  - app/page.tsx
  - components/PromptEditor.tsx
  - lib/supabase.ts
  - All working code ready to run
```

---

## 🔄 Future Enhancement

Once this works, we can create a proper **Code Generation Agent** that:

1. **Analyzes specification** (quick planning)
2. **Generates code** (main task)
3. **Verifies output** (checks for errors)
4. **Iterates if needed** (fixes issues)

This follows the Claude Agent SDK pattern properly.

---

## 📝 Next Steps

1. ✅ Claude Sonnet 4.5 provider working
2. ⏳ Update `_handle_basic_query_fixed()` to use Claude directly
3. ⏳ Test with AI Prompt Library spec
4. ⏳ Verify actual code generation
5. ⏳ Create dedicated code generation agent (future)

---

## 🎯 The Key Insight

**Prince Flowers is designed for RESEARCH** (multi-step agentic reasoning)
**We need it to do CODE GENERATION** (direct action)

**Solution:** Use Claude Sonnet 4.5 directly for code, keep Prince for research.

This aligns with Claude Agent SDK's principle of **choosing the right tool for the right task**.

---

**Status:** Ready to implement direct Claude code generation
**Expected Time:** 5 minutes to update and test
**Expected Result:** Actual working code generation! 🚀
