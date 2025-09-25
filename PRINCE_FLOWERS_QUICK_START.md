# Prince Flowers Enhanced Agent - Quick Start Guide

## 🚀 Getting Started

The Prince Flowers Enhanced Agent is now integrated into TORQ Console with advanced agentic RL capabilities. Here's how to use it:

## 💻 Launch TORQ Console

```bash
cd E:\TORQ-CONSOLE
python -m torq_console
```

Or if you have it installed:
```bash
torq
```

## 🤖 Basic Commands

### Help and Status
```bash
# Get help
torq> prince help
torq> help

# Check agent status
torq> prince status

# Health check
torq> prince health

# Show capabilities
torq> prince capabilities
```

### Search and Research
```bash
# Web search
torq> prince search latest AI developments
torq> prince search machine learning trends 2024

# Research queries
torq> prince what is agentic reinforcement learning
torq> prince explain quantum computing advances
```

### Analysis Commands
```bash
# Deep analysis
torq> prince analyze current state of AI
torq> prince compare different ML approaches

# Technical queries
torq> prince how does transformer architecture work
torq> prince latest breakthroughs in computer vision
```

## 🎯 Command Formats

### Standard Format
```bash
prince <your query or command>
```

### Alternative Format (with @)
```bash
@prince <your query or command>
```

### Examples
```bash
torq> prince search latest AI news
torq> @prince what is the future of AI
torq> prince status
torq> prince help
```

## 📊 Understanding Responses

The agent provides rich, formatted responses with:

- **Main Response** - Comprehensive answer to your query
- **Performance Metrics** - Confidence, execution time, tools used
- **Learning Info** - Reasoning mode, strategy used
- **Sources** - When web search is performed

Example output:
```
🤖 Prince Flowers Enhanced
┌────────────────────────────────────────────────────────────┐
│ Based on my comprehensive research across 3 high-quality   │
│ sources, here's what I found about latest AI developments: │
│                                                            │
│ **Recent Breakthroughs:**                                  │
│ - Advanced reasoning capabilities in large language models │
│ - Improved multi-modal AI systems                         │
│ - Enhanced AI safety and alignment research                │
│                                                            │
│ *[Analysis performed using 3 tools via research_workflow  │
│ strategy, confidence: 87%]*                               │
└────────────────────────────────────────────────────────────┘
```

## 🧠 Agent Capabilities

### Reasoning Modes
The agent automatically selects the best approach:

1. **Direct** - Quick, straightforward responses
2. **Research** - Web search + analysis for current information
3. **Analysis** - Deep analysis with multiple sources
4. **Composition** - Complex multi-step reasoning
5. **Meta-Planning** - Strategy optimization and planning

### Available Tools
- **Web Search** - Multi-source information gathering
- **Content Analysis** - Deep content understanding
- **Response Synthesis** - Coherent response generation
- **Memory Search** - Context-aware information retrieval
- **Error Recovery** - Self-correction capabilities
- **Meta-Planning** - Strategy selection optimization

## 📈 Performance Monitoring

### Check Agent Performance
```bash
torq> prince status
```

Shows:
- Total queries processed
- Success rate
- Average response time
- Tool usage statistics
- Learning progression
- Best performing strategies

### Health Monitoring
```bash
torq> prince health
```

Shows:
- Overall system health
- Individual component status
- Tool availability
- Memory system status
- Performance indicators

## 🔧 Advanced Usage

### Context-Aware Queries
The agent maintains conversation context:

```bash
torq> prince search artificial intelligence trends
# Agent remembers this context

torq> prince how does this relate to business applications
# Agent uses previous context about AI trends
```

### Performance Optimization
The agent learns from interactions:

- **Strategy Selection** - Improves over time
- **Tool Usage** - Optimizes based on success rates
- **Response Quality** - Adapts to user preferences
- **Error Recovery** - Gets better at handling failures

## 💡 Tips for Best Results

### Effective Queries
```bash
# Good: Specific and clear
torq> prince search latest developments in computer vision 2024

# Good: Context-rich
torq> prince analyze the impact of transformer models on NLP

# Good: Current information request
torq> prince what are the recent breakthroughs in AI safety
```

### Using Different Command Types
```bash
# For current information
torq> prince search [topic]

# For analysis
torq> prince analyze [topic]

# For explanations
torq> prince explain [concept]

# For comparisons
torq> prince compare [A] vs [B]
```

## 🛠️ Troubleshooting

### Common Issues

**Agent not responding:**
```bash
torq> prince health
# Check if all systems are operational
```

**Slow responses:**
```bash
torq> prince status
# Check performance metrics and tool usage
```

**Command not recognized:**
- Make sure to use `prince` prefix
- Try `prince help` for command list
- Check for typos in command

### Getting Help
```bash
# General TORQ Console help
torq> help

# Prince Flowers specific help
torq> prince help

# Show capabilities
torq> prince capabilities
```

## 🎯 Example Session

```bash
$ torq
TORQ CONSOLE Interactive Shell
Type 'help' for commands, 'exit' to quit
🤖 Prince Flowers Enhanced Agent integrated - try 'prince help'

torq> prince search latest AI developments
🤖 Prince Flowers Enhanced
┌────────────────────────────────────────────────────────────┐
│ Based on my research using 3 sources, here are the latest │
│ AI developments:                                           │
│                                                            │
│ **Recent Breakthroughs:**                                  │
│ - Large language models with improved reasoning...         │
│ [detailed response]                                        │
└────────────────────────────────────────────────────────────┘

torq> prince status
📊 Prince Flowers Enhanced Status

Agent Information:
- Version: 2.1.0
- Status: active
- Uptime: 0.2 hours

Performance Metrics:
- Total Queries: 1
- Success Rate: 100.0%
- Avg Response Time: 1.45s

torq> prince analyze machine learning trends
[Agent provides comprehensive analysis...]

torq> exit
```

## 🎉 Ready to Go!

The Prince Flowers Enhanced Agent is now ready for use with:
- ✅ Advanced agentic RL capabilities
- ✅ Web search and research
- ✅ Continuous learning and optimization
- ✅ Comprehensive analysis capabilities
- ✅ Real-time performance monitoring

Start with `prince help` and explore the enhanced capabilities!

---

**🤖 Prince Flowers Enhanced v2.1.0 - Your Advanced AI Assistant**