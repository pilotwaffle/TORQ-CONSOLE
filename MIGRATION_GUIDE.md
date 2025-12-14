# TORQ CONSOLE File Restructuring Migration Guide

## 🎯 Overview

This guide helps developers migrate from the old monolithic file structure to the new modular structure. The restructuring improves maintainability, performance, and developer experience while maintaining full backward compatibility.

## 📋 What Changed

### Before (Monolithic Structure)
```
torq_console/agents/
├── torq_prince_flowers.py          # 4,540 lines - Everything in one file
```

### After (Modular Structure)
```
torq_console/agents/
├── torq_prince_flowers.py          # Backward compatibility shim
└── torq_prince_flowers/            # New modular package
    ├── __init__.py                 # Main entry point
    ├── interface.py                # TORQ Console integration
    ├── core/                       # Core agent functionality
    ├── capabilities/               # Agent capabilities
    ├── tools/                      # Agent tools
    ├── integrations/               # External integrations
    └── utils/                      # Utility functions
```

## 🔄 Migration Steps

### Step 1: Update Your Imports (Recommended)

#### Old Import (Deprecated)
```python
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowersInterface
```

#### New Import (Recommended)
```python
# Import from the package (cleaner, no deprecation warning)
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowersInterface
```

#### Import Specific Components
```python
# Import specific components for finer control
from torq_console.agents.torq_prince_flowers.core import TORQPrinceFlowers
from torq_console.agents.torq_prince_flowers.core.state import ReasoningMode
from torq_console.agents.torq_prince_flowers.capabilities import ReasoningEngine
```

### Step 2: Update Your Code (Optional Enhancements)

#### Create Agent Instance (No Change Required)
```python
# This code continues to work exactly as before
agent = TORQPrinceFlowers(llm_provider=my_provider, config=my_config)
result = await agent.process_query("Hello, Prince Flowers!")
```

#### Enhanced Usage (New Opportunities)
```python
# Access specific components directly
from torq_console.agents.torq_prince_flowers.capabilities import ReasoningEngine

reasoning_engine = ReasoningEngine(my_provider)
analysis = await reasoning_engine.analyze_query("search for AI trends")
```

### Step 3: Update Testing (Optional)

#### Test Individual Components
```python
# Test specific components in isolation
from torq_console.agents.torq_prince_flowers.capabilities.learning import LearningEngine

def test_learning_engine():
    engine = LearningEngine()
    # Test learning functionality
```

## ⚠️ Deprecation Warnings

You'll see deprecation warnings when using old import patterns:

```
DeprecationWarning: Direct import from torq_console.agents.torq_prince_flowers.py is deprecated.
Import from torq_console.agents.torq_prince_flowers package instead.
```

**Action**: Update your imports to avoid these warnings.

## 🚀 Benefits of Migration

### 1. Better Performance
- **Faster Imports**: Only load needed components
- **Reduced Memory**: Smaller modules use less memory
- **Lazy Loading**: Components loaded only when used

### 2. Improved Development Experience
- **Better IDE Support**: Smaller files for better navigation
- **Easier Debugging**: Isolated components simplify troubleshooting
- **Enhanced Testing**: Test components individually

### 3. Cleaner Code
- **Separation of Concerns**: Each module has one responsibility
- **Reduced Complexity**: Smaller, focused modules
- **Better Documentation**: Clear module boundaries

## 🛠️ Advanced Usage Examples

### Custom Agent Configuration
```python
from torq_console.agents.torq_prince_flowers.capabilities import ReasoningEngine, LearningEngine
from torq_console.agents.torq_prince_flowers.tools import WebSearchTool

# Create custom configuration
reasoning = ReasoningEngine(custom_provider)
learning = LearningEngine()
search_tool = WebSearchTool()

# Use components independently
result = await reasoning.analyze_query("complex query", context)
await learning.record_experience(trajectory, analysis, success=True)
search_results = await search_tool.search("AI developments")
```

### Extending with Custom Tools
```python
from torq_console.agents.torq_prince_flowers.core import TORQPrinceFlowers

class CustomAgent(TORQPrinceFlowers):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add custom tools or capabilities
        self.custom_tool = MyCustomTool()

    async def custom_method(self, query):
        # Custom implementation
        return await self.custom_tool.execute(query)
```

### Component-Level Testing
```python
import pytest
from torq_console.agents.torq_prince_flowers.capabilities.reasoning import ReasoningEngine

@pytest.mark.asyncio
async def test_reasoning_engine():
    engine = ReasoningEngine()
    analysis = await engine.analyze_query("test query")
    assert analysis["intent"] == "general"
```

## 🔧 Troubleshooting

### Import Errors

#### Issue: "ModuleNotFoundError: No module named 'torq_prince_flowers'"
**Solution**: Ensure you're importing from the package, not the old file:
```python
# Wrong
from torq_console.agents import torq_prince_flowers

# Correct
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
```

#### Issue: "ImportError: cannot import name 'SomeClass'"
**Solution**: Check the new module structure:
```python
# Check what's available
from torq_console.agents.torq_prince_flowers import *
dir()  # See available symbols

# Or import specific module
from torq_console.agents.torq_prince_flowers.core.state import SomeClass
```

### Performance Issues

#### Issue: Slower imports after migration
**Solution**: This should improve, but if you see issues:
```python
# Import only what you need
from torq_console.agents.torq_prince_flowers.core import TORQPrinceFlowers
# Instead of importing everything
```

### Compatibility Issues

#### Issue: Old code still using the monolithic file
**Solution**: The compatibility shim should handle this, but update imports:
```python
# Old (still works, but deprecated)
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

# New (recommended)
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
```

## 📅 Migration Timeline

### Phase 1: Immediate (Now)
- ✅ torq_prince_flowers.py restructured
- ⚠️ Compatibility warnings in place
- 📚 Migration guide available

### Phase 2: Next 30 Days
- 🔄 Encourage migration to new imports
- 📝 Update documentation
- 🧪 Enhanced testing capabilities

### Phase 3: Next 90 Days
- 🚀 Full optimization benefits realized
- 📈 Performance improvements measured
- 🛠️ Additional tooling available

### Phase 4: Future (6+ months)
- 🗑️ Consider removing compatibility shims
- 📦 Package optimizations
- 🔧 Advanced features

## 🎯 Best Practices

### 1. Import Strategy
```python
# ✅ Good: Import specific components
from torq_console.agents.torq_prince_flowers.core import TORQPrinceFlowers

# ✅ Good: Import from package
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

# ⚠️ Acceptable: Old style (works but deprecated)
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

# ❌ Avoid: Star imports (can cause namespace pollution)
from torq_console.agents.torq_prince_flowers import *
```

### 2. Component Usage
```python
# ✅ Good: Use high-level interface
agent = TORQPrinceFlowers()
result = await agent.process_query("query")

# ✅ Good: Use specific components when needed
reasoning = ReasoningEngine()
analysis = await reasoning.analyze_query("query")

# ❌ Avoid: Direct internal component manipulation
agent.reasoning_engine.internal_method()  # Avoid this
```

### 3. Testing Strategy
```python
# ✅ Good: Test high-level functionality
async def test_agent_processing():
    agent = TORQPrinceFlowers()
    result = await agent.process_query("test")
    assert result.success

# ✅ Good: Test specific components
async def test_reasoning_analysis():
    engine = ReasoningEngine()
    analysis = await engine.analyze_query("test")
    assert "intent" in analysis
```

## 📞 Getting Help

### Documentation
- **Restructuring Plan**: `RESTRUCTURING_PLAN.md`
- **Progress Report**: `RESTRUCTURING_PROGRESS.md`
- **Module Documentation**: In each `__init__.py` file

### Support
- Check the troubleshooting section above
- Review the module documentation
- Look at the example usage patterns

### Contributing
- Follow the established patterns for new modules
- Maintain backward compatibility
- Add appropriate tests and documentation

---

## 🎉 Summary

The restructuring of TORQ CONSOLE files provides significant benefits while maintaining full backward compatibility. The migration is straightforward and optional, but recommended for the best development experience.

**Key Takeaways:**
1. **Update imports** to avoid deprecation warnings
2. **Explore new capabilities** now available through modular structure
3. **Test components** individually for better quality assurance
4. **Follow best practices** for optimal performance

The migration ensures your code continues to work while gaining access to improved performance, maintainability, and development experience.