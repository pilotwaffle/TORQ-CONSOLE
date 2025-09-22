# TORQ CONSOLE

[![GitHub stars](https://img.shields.io/github/stars/pilotwaffle/TORQ-CONSOLE?style=social)](https://github.com/pilotwaffle/TORQ-CONSOLE/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![Last Commit](https://img.shields.io/github/last-commit/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/commits/main)
[![Issues](https://img.shields.io/github/issues/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/pilotwaffle/TORQ-CONSOLE)](https://github.com/pilotwaffle/TORQ-CONSOLE/pulls)

> **Version:** 0.60.0 (MCP-Enhanced Polish Milestone)  
> **Author:** B Flowers  
> **Status:** Draft – for Aider-AI Maintainer Review  
> **License:** MIT  

TORQ CONSOLE is an enhanced evolution of [Aider](https://github.com/Aider-AI/aider), the open-source AI pair programmer (⭐37k+).  
It combines Aider's **CLI speed** with the **Model Context Protocol (MCP)** for agentic workflows, polished UX, and intuitive ideation.

---

## 🚀 Why TORQ CONSOLE?

- **Aider is fast** but trails Cursor in **intuitiveness, ideation, and polish**.  
- MCP, now an open JSON-RPC standard adopted by OpenAI, GitHub Copilot, Replit, and others, unlocks **privacy-first tool integration**.  
- Community demand is clear:  
  - [Aider issue #3314](https://github.com/Aider-AI/aider/issues/3314) on MCP support has **200+ upvotes**.  
  - Threads across Reddit/X show frustration with CLI silos.  

TORQ CONSOLE answers that call.  

---

## ✨ Key Features (Milestone v0.60.0)

### 🟢 P0 – MCP Core
- Native bidirectional MCP integration (GitHub, Postgres, Jenkins, etc.).
- `--mcp-connect` for endpoint discovery and secure auth.
- Privacy-first: BYO-API key, local cache, no telemetry.

### 🟡 P1 – Intuitiveness & Ideation
- Interactive shell with guided prompts (`--interactive`).
- Voice command support via Whisper + TTS (`--voice-shortcuts`).
- IDE terminal integration (auto-open in VS Code, synced edits).
- Web/DB-powered ideation through MCP (`--ideate`, `--plan`).
- Multi-file prototyping with MCP-driven repo mapping.
- Local model optimization (Ollama/CodeLlama support).

### 🔵 P2 – Polish
- Visual diffs with `git-delta`.
- Syntax highlighting via `bat`.
- Enhanced GUI (web TUI with panels for files, diffs, chat).
- Workflow automation scripts (CI/CD, PR templates).

---

## 🎯 Objectives & Success Metrics
- **Intuitiveness:** 80% of new users rate setup <10 min.  
- **Ideation:** 50% of prototyping tasks leverage MCP/web.  
- **Polish:** 60% adopt visuals/GUI features.  
- **Adoption:** Grow from 37k → 46k GitHub stars (25% increase).  
- **Quality:** 95% MCP call success rate.  

---

## 👩‍💻 User Personas
- **Alice (Power User):** Terminal loyalist. Wants MCP-chained edits + voice shortcuts.  
- **Bob (Beginner):** IDE-native. Needs guided setup + polished GUI.  
- **Charlie (Team Lead):** DevOps workflows. Wants secure MCP for CI/CD.  

---

## 🔧 Tech Stack
- **Core:** Python 3.10+  
- **Key Dependencies:** `prompt_toolkit`, `jsonrpcserver`, `fastapi`, `htmx`, `ollama-python`, `speech_recognition`, `pyttsx3`  
- **OS:** Linux, macOS, Windows  
- **LLMs Supported:** Claude 3.5, GPT-4o, CodeLlama  

---

## 🛠️ Roadmap
- **v0.60.0 (Q4 2025):** MCP core + polish features (this repo).  
- **v0.61:** Plugin system.  
- **v0.62:** VS Code extension.  

---

## 🤝 Community
- **GitHub:** [Issues/PRs](../../issues) welcomed for MCP servers & polish.  
- **Discord / r/Aider:** Beta feedback and ideation contests.  
- **X/Twitter:** Follow demos (voice + MCP workflows).  

---

## 📜 License
MIT License – Open source and community-driven.

---

## 📌 Status
This is an early-stage **OSS project**.  
Expect rapid iteration, community-driven contributions, and bounties for MCP server integrations.
