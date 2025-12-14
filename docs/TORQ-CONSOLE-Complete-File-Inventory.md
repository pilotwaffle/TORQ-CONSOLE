# TORQ CONSOLE - Complete File Inventory & Analysis

**Generated:** 2025-12-12
**Total Files Analyzed:** 700+

---

## Executive Summary

| Category | Count | Total Lines |
|----------|-------|-------------|
| Python Files (torq_console/) | 150+ | 82,971 |
| Test Files | 107 | ~45,000 |
| Documentation Files (.md) | 168 | ~500,000+ chars |
| Frontend Files (TSX/TS) | 30+ | 5,231 |
| JavaScript Files | 9 | 2,592 |
| Configuration Files | 15+ | ~1,000 |

---

## 1. TORQ_CONSOLE PACKAGE (82,971 lines)

### 1.1 agents/ (~25,000 lines)

**Core Prince Flowers Agents:**
| File | Lines | Description |
|------|-------|-------------|
| `torq_prince_flowers.py` | 4,535 | Main production agent with full capabilities |
| `enhanced_prince_flowers_v2.py` | 1,119 | Advanced RL learning variant |
| `torq_search_master.py` | 1,071 | Search orchestration |
| `prince_flowers_agent.py` | 750 | Base RL agent |
| `prince_flowers_enhanced.py` | 519 | Enhanced integration |
| `prince_flowers_enhanced_integration.py` | 700 | Integration layer |
| `marvin_prince_flowers.py` | 400 | Marvin-powered variant |
| `glm_prince_flowers.py` | 200 | GLM-4 integration |

**Agent Tools (agents/tools/):**
| File | Lines | Description |
|------|-------|-------------|
| `multi_tool_composition_tool.py` | 1,143 | Tool chaining/orchestration |
| `mcp_client_tool.py` | 1,141 | Model Context Protocol |
| `browser_automation_tool.py` | 815 | Playwright web automation |
| `code_generation_tool.py` | 773 | Multi-language code gen |
| `n8n_workflow_tool.py` | 757 | n8n automation |
| `file_operations_tool.py` | 580 | File read/write/edit |
| `terminal_commands_tool.py` | 545 | Shell execution |
| `twitter_posting_tool.py` | 350 | Twitter/X automation |
| `linkedin_posting_tool.py` | 330 | LinkedIn automation |
| `landing_page_generator.py` | 400 | Website scaffolding |
| `image_generation_tool.py` | 280 | AI image generation |

**Marvin Integration:**
| File | Lines | Description |
|------|-------|-------------|
| `marvin_commands.py` | 686 | CLI commands |
| `marvin_orchestrator.py` | 500 | Multi-agent coordination |
| `marvin_query_router.py` | 570 | Intelligent routing |
| `marvin_workflow_agents.py` | 460 | Specialized agents |
| `marvin_memory.py` | 360 | Persistent memory |

**RL & Learning Systems:**
| File | Lines | Description |
|------|-------|-------------|
| `enhanced_rl_system.py` | 580 | Advanced RL with memory |
| `rl_learning_system.py` | 410 | Base RL system |
| `meta_learning_engine.py` | 470 | Cross-task meta-learning |
| `action_learning.py` | 400 | Action pattern learning |
| `feedback_learning.py` | 365 | User feedback integration |
| `preference_learning.py` | 340 | User preference modeling |
| `self_evaluation_system.py` | 565 | Agent self-assessment |

**Advanced Systems:**
| File | Lines | Description |
|------|-------|-------------|
| `handoff_optimizer.py` | 685 | Agent handoff optimization |
| `handoff_context.py` | 295 | Context management |
| `hierarchical_task_planner.py` | 510 | Task planning |
| `multi_agent_debate.py` | 460 | Debate activation |
| `improved_debate_activation.py` | 295 | Enhanced debate |
| `intent_detector.py` | 550 | User intent classification |
| `adaptive_quality_manager.py` | 385 | Quality management |
| `advanced_memory_system.py` | 455 | Semantic memory |
| `conversation_session.py` | 345 | Session management |
| `coordination_benchmark.py` | 540 | Performance benchmarks |

**RL Modules (agents/rl_modules/):**
| File | Lines | Description |
|------|-------|-------------|
| `modular_agent.py` | 300+ | Modular architecture |
| `async_training.py` | 200+ | Async training pipeline |
| `dynamic_actions.py` | 150+ | Dynamic action space |

---

### 1.2 api/ (1,354 lines)

| File | Lines | Description |
|------|-------|-------------|
| `socketio_handler.py` | 558 | Real-time WebSocket |
| `routes.py` | 530 | API endpoints |
| `server.py` | 255 | FastAPI server |
| `__init__.py` | 11 | Package init |

---

### 1.3 core/ (4,460 lines)

| File | Lines | Description |
|------|-------|-------------|
| `chat_manager.py` | 1,600 | Multi-tab chat system |
| `context_manager.py` | 1,050 | @-symbol parsing, Tree-sitter |
| `console.py` | 965 | Terminal interface |
| `config.py` | 691 | Configuration management |
| `executor_pool.py` | 106 | Execution pool |
| `logger.py` | 41 | Logging utilities |

---

### 1.4 indexer/ (1,387 lines)

| File | Lines | Description |
|------|-------|-------------|
| `semantic_search.py` | 425 | Semantic search engine |
| `embeddings.py` | 363 | Embedding generation |
| `vector_store.py` | 351 | Vector database |
| `code_scanner.py` | 226 | Code indexing |

---

### 1.5 integrations/ (2,508 lines)

| File | Lines | Description |
|------|-------|-------------|
| `huggingface_models.py` | 821 | HuggingFace integration |
| `n8n_workflows.py` | 685 | n8n workflow API |
| `video_generation.py` | 346 | Video generation |
| `perplexity_search.py` | 240 | Perplexity API |
| `github_push.py` | 225 | GitHub integration |
| `image_generation.py` | 187 | Image generation |

---

### 1.6 llm/ (~6,000 lines)

**Core:**
| File | Lines | Description |
|------|-------|-------------|
| `websearch.py` | 1,314 | Multi-provider web search |
| `manager.py` | 662 | LLM routing & management |
| `content_safety.py` | 493 | Content moderation |

**Providers:**
| File | Lines | Description |
|------|-------|-------------|
| `llama_cpp_provider.py` | 445 | llama.cpp integration |
| `ollama.py` | 343 | Ollama integration |
| `deepseek.py` | 307 | DeepSeek integration |
| `claude.py` | 275 | Anthropic Claude |
| `glm.py` | 165 | GLM-4 integration |

**Utilities:**
| File | Lines | Description |
|------|-------|-------------|
| `confidence.py` | 444 | Confidence scoring |
| `extractor.py` | 423 | Data extraction |
| `synthesizer.py` | 381 | Response synthesis |
| `registry.py` | 323 | Provider registry |

---

### 1.7 marvin_integration/ (1,089 lines)

| File | Lines | Description |
|------|-------|-------------|
| `models.py` | 371 | Pydantic models |
| `agents.py` | 356 | Base Marvin agents |
| `core.py` | 300 | Core integration |
| `__init__.py` | 62 | Package exports |

---

### 1.8 mcp/ (2,051 lines)

| File | Lines | Description |
|------|-------|-------------|
| `claude_code_bridge.py` | 523 | Claude Code compatibility |
| `client.py` | 486 | Core MCP client |
| `enhanced_client.py` | 476 | Extended capabilities |
| `mcp_commands.py` | 211 | CLI commands |
| `mcp_manager.py` | 208 | Server management |
| `enhanced_integration.py` | 142 | Enhanced features |

---

### 1.9 memory/ (431 lines)

| File | Lines | Description |
|------|-------|-------------|
| `letta_integration.py` | 412 | Letta memory system |
| `__init__.py` | 19 | Package init |

---

### 1.10 orchestration/ (~1,100 lines)

| File | Lines | Description |
|------|-------|-------------|
| `base_agents.py` | 293 | Base agent classes |
| `research_flow.py` | 211 | Research workflows |
| `base_tasks.py` | 191 | Task definitions |
| `analysis_flow.py` | 180 | Analysis workflows |
| `integration.py` | 122 | Integration utilities |

---

### 1.11 reasoning/ (2,413 lines)

| File | Lines | Description |
|------|-------|-------------|
| `templates.py` | 758 | CoT templates |
| `enhancers.py` | 655 | Reasoning enhancements |
| `validator.py` | 561 | Output validation |
| `core.py` | 408 | Base reasoning engine |

---

### 1.12 spec_kit/ (5,744 lines)

| File | Lines | Description |
|------|-------|-------------|
| `spec_commands.py` | 993 | CLI commands |
| `spec_engine.py` | 839 | Core specification management |
| `ecosystem_intelligence.py` | 819 | GitHub/GitLab integration |
| `realtime_editor.py` | 556 | Live editing assistance |
| `adaptive_intelligence.py` | 502 | Real-time suggestions |
| `collaboration_server.py` | 483 | WebSocket collaboration |
| `marvin_quality_engine.py` | 465 | Multi-dimensional scoring |
| `rl_spec_analyzer.py` | 387 | RL-powered analysis |
| `marvin_spec_analyzer.py` | 368 | AI-powered analysis |
| `marvin_integration.py` | 332 | Integration bridge |

---

### 1.13 swarm/ (4,974 lines)

**Orchestration:**
| File | Lines | Description |
|------|-------|-------------|
| `orchestrator_advanced.py` | 658 | Advanced coordination |
| `orchestrator.py` | 296 | Basic orchestration |
| `memory_system.py` | 527 | Shared memory |
| `message_system.py` | 446 | Inter-agent messaging |
| `communication_tools.py` | 409 | Communication protocols |
| `communication_parser.py` | 220 | Message parsing |

**Swarm Agents (swarm/agents/):**
| File | Lines | Description |
|------|-------|-------------|
| `code_agent.py` | 745 | Code generation |
| `documentation_agent.py` | 713 | Documentation generation |
| `testing_agent.py` | 674 | Test generation |
| `performance_agent.py` | 657 | Performance optimization |
| `search_agent.py` | 244 | Web search |
| `synthesis_agent.py` | 169 | Result synthesis |
| `response_agent.py` | 196 | Response formatting |
| `analysis_agent.py` | 132 | Data analysis |

---

### 1.14 ui/ (7,339 lines)

| File | Lines | Description |
|------|-------|-------------|
| `web.py` | 2,365 | Main FastAPI web app |
| `command_palette.py` | 1,789 | VSCode-like commands |
| `inline_editor.py` | 1,229 | Ghost text suggestions |
| `web_ai_fix.py` | 543 | AI fix utilities |
| `learning_system.py` | 513 | UI-level learning |
| `intent_detector.py` | 456 | Intent classification |
| `app.py` | 281 | App entry point |
| `shell.py` | 112 | Shell interface |
| `main.py` | 47 | Main entry |

---

### 1.15 utils/ (6,200+ lines)

| File | Lines | Description |
|------|-------|-------------|
| `app_builder.py` | 1,183 | Full-stack app builder |
| `advanced_web_search.py` | 652 | Advanced search |
| `planning_tools.py` | 606 | Planning utilities |
| `ai_integration.py` | 595 | AI integration helpers |
| `notebook_tools.py` | 562 | Jupyter tools |
| `visual_diff.py` | 495 | Visual diff utilities |
| `web_tools.py` | 447 | Web utilities |
| `search_tools.py` | 397 | Search utilities |
| `edit_tools.py` | 366 | Edit utilities |
| `profiling.py` | 318 | Performance profiling |

---

## 2. TEST FILES (107 files, ~45,000 lines)

### Largest Test Files:
| File | Lines | Description |
|------|-------|-------------|
| `test_integration_final.py` | 849 | End-to-end tests |
| `test_cot_comprehensive.py` | 785 | Chain-of-thought tests |
| `test_enhanced_rl_system.py` | 715 | RL system tests |
| `tests/test_phase5_export_ux.py` | 659 | Phase 5 export tests |
| `test_enhanced_prince_v2_agentic.py` | 641 | Agentic behavior tests |
| `tests/test_phase4_content_synthesis.py` | 588 | Content synthesis tests |
| `test_phase3_validation.py` | 547 | Phase 3 validation |
| `test_phase1_controlflow_standalone.py` | 543 | Control flow tests |
| `test_phase2_adaptive_intelligence.py` | 503 | Adaptive intelligence tests |
| `test_phase3_ecosystem_intelligence.py` | 493 | Ecosystem tests |

### Test Categories:
- **Phase Tests:** test_phase1_*, test_phase2_*, test_phase3_*, test_phase4_*, test_phase5_*
- **Integration Tests:** test_integration*.py, test_*_integration.py
- **Agent Tests:** test_prince_*.py, test_enhanced_prince_*.py
- **Feature Tests:** test_rl_*.py, test_handoff_*.py, test_search_*.py

---

## 3. DOCUMENTATION FILES (168 files)

### Core Documentation:
| File | Size | Description |
|------|------|-------------|
| `README.md` | 31KB | Main project README |
| `CLAUDE.md` | 38KB | Claude Code integration |
| `SECURITY.md` | 12KB | Security guidelines |
| `CONTRIBUTING.md` | 14KB | Contribution guide |
| `CHANGELOG.md` | 9KB | Version history |

### Feature Documentation:
- `N8N_*.md` (6 files) - n8n integration docs
- `PRINCE_*.md` (18 files) - Prince Flowers agent docs
- `PHASE_*.md` (10 files) - Development phase docs
- `TERMINAL_COMMANDS_*.md` (4 files) - Terminal command docs
- `RAILWAY_*.md` (6 files) - Railway deployment docs

### Reports:
- `*_REPORT.md` (15 files) - Various reports
- `*_SUMMARY.md` (20 files) - Summary documents
- `*_TEST_RESULTS.md` (8 files) - Test results

---

## 4. FRONTEND (React/Vite - 5,231 lines)

### Components:
| File | Lines | Description |
|------|-------|-------------|
| `CommandPalette.tsx` | 432 | Command palette UI |
| `WorkflowGraph.tsx` | 387 | Workflow visualization |
| `DiffMessage.tsx` | 301 | Diff display |
| `DiffViewer.tsx` | 288 | Diff viewer |
| `CoordinationPanel.tsx` | 271 | Agent coordination |
| `DiffExample.tsx` | 262 | Diff examples |
| `CodeViewer.tsx` | 231 | Code display |
| `DiffStats.tsx` | 231 | Diff statistics |
| `AgentCard.tsx` | 189 | Agent card UI |
| `MonacoEditor.tsx` | 170 | Code editor |
| `CodeBlock.tsx` | 163 | Code blocks |
| `ChatMessage.tsx` | 125 | Chat messages |

### Services:
| File | Lines | Description |
|------|-------|-------------|
| `agentService.ts` | 306 | Agent API service |
| `api.ts` | 257 | API client |
| `websocket.ts` | 188 | WebSocket client |

### Stores:
| File | Lines | Description |
|------|-------|-------------|
| `coordinationStore.ts` | 281 | Coordination state |
| `agentStore.ts` | 224 | Agent state |

### Hooks:
| File | Lines | Description |
|------|-------|-------------|
| `useKeyboardShortcuts.ts` | 115 | Keyboard shortcuts |

---

## 5. MAXIM INTEGRATION (20+ files, ~25,000 lines)

| File | Lines | Description |
|------|-------|-------------|
| `phase2_professional_task_optimization.py` | 2,096 | Task optimization |
| `phase1_quality_consistency_framework.py` | 1,663 | Quality framework |
| `advanced_agent_growth_tests.py` | 1,581 | Growth tests |
| `phase2_evolutionary_learning.py` | 1,527 | Evolutionary learning |
| `phase3_system_integration_testing.py` | 1,424 | System testing |
| `observe_system.py` | 1,172 | Observation system |
| `phase1_learning_velocity_enhancement.py` | 1,085 | Learning velocity |
| `phase4_production_deployment_monitoring.py` | 1,071 | Deployment monitoring |
| `agent_growth_monitoring_dashboard.py` | 1,061 | Growth dashboard |
| `human_in_the_loop_evaluation.py` | 1,041 | HITL evaluation |
| `prompt_optimization_workflow.py` | 1,001 | Prompt optimization |
| `enhanced_prince_adaptive_learning_test.py` | 988 | Adaptive learning |
| `hard_comprehensive_test.py` | 982 | Comprehensive tests |
| `maxim_style_evaluation_test.py` | 923 | Style evaluation |
| `zep_enhanced_prince_flowers.py` | 800+ | Zep memory integration |

---

## 6. ROOT-LEVEL PYTHON FILES (~15,000 lines)

| File | Lines | Description |
|------|-------|-------------|
| `torq_integration.py` | 1,137 | Main integration |
| `torq_integration_working.py` | 923 | Working integration |
| `torq_integration_fixed.py` | 623 | Fixed integration |
| `viral_x_posts_app.py` | 568 | Viral posts app |
| `api_integration_validator.py` | 518 | API validation |
| `xai_grok_integration.py` | 415 | X.AI Grok integration |
| `web_api_fix.py` | 416 | Web API fixes |
| `maxim_integration.py` | 395 | Maxim integration |
| `claude_websearch_real.py` | 392 | Claude web search |

---

## 7. JAVASCRIPT FILES (2,592 lines)

| File | Lines | Description |
|------|-------|-------------|
| `comprehensive_test_suite.js` | 596 | Comprehensive tests |
| `final_prince_test.js` | 404 | Prince agent tests |
| `web_api_test.js` | 341 | Web API tests |
| `api_quality_test.js` | 333 | API quality tests |
| `api_discovery.js` | 330 | API discovery |
| `server_analysis.js` | 267 | Server analysis |
| `configure_api_keys.js` | 207 | API key config |
| `brave_api_fix_test.js` | 96 | Brave API tests |

---

## 8. CONFIGURATION FILES

### Deployment:
| File | Description |
|------|-------------|
| `railway.toml` | Railway configuration |
| `railway.json` | Railway settings |
| `render.yaml` | Render deployment |
| `vercel.json` | Vercel deployment |
| `Procfile` | Process file |
| `.nixpacks.toml` | Nixpacks config |

### Package Management:
| File | Description |
|------|-------------|
| `pyproject.toml` | Python project config |
| `requirements.txt` | Python dependencies |
| `requirements-letta.txt` | Letta dependencies |
| `package.json` | Node.js config |
| `package-lock.json` | Node.js lock file |

### Environment:
| File | Description |
|------|-------------|
| `.env.example` | Environment template |
| `.gitignore` | Git ignore patterns |
| `.dockerignore` | Docker ignore patterns |
| `.railwayignore` | Railway ignore |

### Build:
| File | Description |
|------|-------------|
| `tailwind.config.js` | Tailwind CSS config |
| `vite.config.ts` | Vite bundler config |
| `tsconfig.json` | TypeScript config |
| `postcss.config.js` | PostCSS config |

---

## 9. EXAMPLES (4 files)

| File | Lines | Description |
|------|-------|-------------|
| `torq_prince_flowers_demo.py` | 600+ | Prince Flowers demo |
| `n8n_architect_examples.py` | 360 | n8n examples |
| `marvin_integration_examples.py` | 340 | Marvin examples |
| `enhanced_prince_flowers_demo.py` | 260 | Enhanced demo |
| `QUICKSTART.md` | 250 | Quick start guide |

---

## 10. SCRIPTS

| File | Lines | Description |
|------|-------|-------------|
| `apply_action_learning_lesson.py` | 120 | Action learning script |
| `install.sh` | 28 | Installation script |
| Various `.bat` files | - | Windows launchers |
| Various `.ps1` files | - | PowerShell scripts |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Python Lines** | ~130,000+ |
| **Total TypeScript Lines** | ~5,200 |
| **Total JavaScript Lines** | ~2,600 |
| **Total Documentation** | ~500KB+ |
| **Unique Python Classes** | 200+ |
| **Unique Functions** | 2,000+ |
| **API Endpoints** | 50+ |
| **Agent Types** | 20+ |
| **Tool Types** | 12 |
| **LLM Providers** | 6 |
| **Test Files** | 107 |
| **Documentation Files** | 168 |

---

## Key File Categories

### Most Critical Files:
1. `torq_console/agents/torq_prince_flowers.py` - Main production agent
2. `torq_console/ui/web.py` - Web interface
3. `torq_console/core/chat_manager.py` - Chat system
4. `torq_console/llm/manager.py` - LLM orchestration
5. `torq_console/spec_kit/spec_engine.py` - Specification engine

### Most Complex Subsystems:
1. **Agents** - 25,000+ lines across 45+ files
2. **UI** - 7,300+ lines with command palette and inline editor
3. **Spec-Kit** - 5,700+ lines for specification management
4. **Swarm** - 5,000+ lines for multi-agent coordination
5. **Utils** - 6,200+ lines of shared utilities

---

*Generated by Claude Code Analysis*
