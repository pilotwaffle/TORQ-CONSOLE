# How to Build an App in Torq-Console

**King Flowers Edition - Complete Guide**

## Overview

Torq-Console provides multiple ways to build applications with AI assistance, live coding, and integrated tools. This guide covers all methods.

---

## Method 1: Interactive Chat Interface (Recommended for Beginners)

### Access the Console
1. Open your browser to: http://localhost:8899
2. You'll see a 3-panel layout:
   - **Left Panel:** MCP Tools & Integration
   - **Center Panel:** Chat Interface
   - **Right Panel:** File Browser & Diffs

### Start Building

#### Step 1: Create a New Chat
```
Click the "New Chat" button (or press Ctrl+T)
```

#### Step 2: Describe Your App
In the chat, type what you want to build:

```
Example: "I want to build a todo app with React and TypeScript.
It should have:
- Add/remove tasks
- Mark tasks as complete
- Save to localStorage
- Modern UI with Tailwind CSS"
```

#### Step 3: Watch the Build Process
The console will:
- ✅ Create project structure
- ✅ Generate files
- ✅ Show real-time progress
- ✅ Display diffs in the right panel

#### Step 4: Review Changes
- Files appear in the right panel
- Click any file to see its contents
- Approve or modify changes
- See live diffs before applying

---

## Method 2: Command Palette Workflow (Power Users)

### Open Command Palette
Press `Ctrl+Shift+P` or click the command icon

### Key Commands for Building

```
🏗️ Project Setup Commands:
"Create New Project"
"Initialize Git Repository"
"Setup Package.json"
"Install Dependencies"

📝 File Commands:
"New File"
"Edit File"
"Delete File"
"Save All Files"

🔨 Build Commands:
"Run Build"
"Run Tests"
"Start Dev Server"
"Deploy Project"

🤖 AI Commands:
"Generate Code"
"Refactor Code"
"Add Documentation"
"Optimize Code"
```

### Example Workflow
1. Press `Ctrl+Shift+P`
2. Type "Create New Project"
3. Follow the prompts
4. Use "Generate Code" to create components
5. Use "Run Build" to compile

---

## Method 3: Using Prince Flowers Agent (Advanced)

### Via Chat Interface
In the chat, use the `@prince` prefix:

```
@prince create a REST API with Express and TypeScript

@prince add authentication using JWT

@prince write tests for the API endpoints

@prince optimize the database queries
```

### Via Command Line (if using CLI)
```bash
torq> prince help

torq> prince create a new React component for user profile

torq> prince refactor this code to use async/await

torq> prince status  # Check agent performance
```

---

## Method 4: Direct File Editing

### Using the Web Interface

#### 1. Browse Files (Left Panel)
- Navigate your project structure
- Click folders to expand
- Click files to edit

#### 2. Edit Files
- Select a file
- Use the inline editor (press `Ctrl+K`)
- Make changes
- Save with `Ctrl+S`

#### 3. See Changes Live
- Right panel shows diffs automatically
- Green = additions
- Red = deletions
- Compare before/after

---

## Method 5: Spec-Driven Development (Professional)

### Using GitHub Spec-Kit Workflow

#### 1. Create a Constitution
```
In chat: "/constitution create MyApp 'Build amazing software'
  --principles='Quality,Speed,Security'
  --constraints='Time,Budget'
  --criteria='Performance,Usability'"
```

#### 2. Create Specifications
```
/specify create 'User Authentication' 'Secure auth system'
  --requirements='Login,Logout,Password reset'
  --tech='python,jwt,database'
  --priority='high'
```

#### 3. Generate Implementation Plan
```
/plan generate spec_0001
```

#### 4. View Tasks
```
/tasks list spec_0001
```

#### 5. Start Implementation
```
/implement start spec_0001
```

#### 6. Track Progress
```
/torq-spec status
```

---

## Complete Example: Building a Simple Web App

### Step-by-Step Tutorial

#### 1. Start a New Project

**In Chat:**
```
Create a new web application called "TaskMaster" with:
- Frontend: React + TypeScript + Vite
- Styling: Tailwind CSS
- Features: CRUD operations for tasks
- Storage: LocalStorage
```

#### 2. Watch the Build Process

The console will:
```
[1/5] Creating project structure...
    ├── src/
    ├── public/
    ├── package.json
    └── tsconfig.json

[2/5] Installing dependencies...
    npm install react react-dom vite tailwindcss

[3/5] Generating components...
    ✓ src/App.tsx
    ✓ src/components/TaskList.tsx
    ✓ src/components/TaskForm.tsx

[4/5] Configuring build...
    ✓ vite.config.ts
    ✓ tailwind.config.js

[5/5] Project ready!
```

#### 3. Review Generated Files

**Right Panel shows:**
- File tree with all new files
- Click any file to see contents
- Diffs show what was created

#### 4. Run the Development Server

**In Chat:**
```
Start the development server
```

**Or use Command Palette:**
```
Ctrl+Shift+P → "Start Dev Server"
```

**Or use Built-in Terminal:**
```
cd TaskMaster
npm run dev
```

#### 5. Make Changes

**Request modifications:**
```
Add a dark mode toggle to the app
```

**Or edit directly:**
- Press `Ctrl+K` on any file
- Make your changes
- See live preview in right panel

#### 6. Test and Build

**In Chat:**
```
Run the tests and create a production build
```

**The console will:**
```
[Testing] Running test suite...
  ✓ 15 tests passed

[Building] Creating production build...
  ✓ Build complete: dist/

[Stats]
  Bundle size: 142KB
  Build time: 3.2s
```

---

## Active Outcome Display

### What You'll See During Build

#### 1. Real-Time Progress
```
┌─────────────────────────────────────┐
│ Building TaskMaster...              │
│ ━━━━━━━━━━━━━━━━━━━ 45%           │
│                                     │
│ Current: Installing dependencies    │
│ Next: Generating components         │
└─────────────────────────────────────┘
```

#### 2. File Changes
```
📄 src/App.tsx [NEW]
  + 120 lines added

📄 package.json [MODIFIED]
  + Added: react, react-dom, vite
  + Added: tailwindcss, autoprefixer
```

#### 3. Build Output
```
$ npm run build

> taskmaster@1.0.0 build
> vite build

vite v5.0.8 building for production...
✓ 34 modules transformed.
dist/index.html                0.46 kB
dist/assets/index-4f3e9b2c.css 3.24 kB
dist/assets/index-d2c4a019.js  142.45 kB

✓ built in 3.21s
```

#### 4. Test Results
```
Test Suites: 3 passed, 3 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        2.456s
```

---

## Advanced Features

### 1. Multi-File Editing
```
In chat: "Refactor all components to use TypeScript strict mode
and add proper error handling"
```

The console will:
- Identify all relevant files
- Show changes for each file
- Let you approve/reject each change
- Apply changes in correct order

### 2. MCP Tool Integration

**Use External Tools:**
```
"Use the DeepSeek API to analyze code quality"
"Search GitHub for similar implementations"
"Query the database for user data"
"Call the n8n workflow to deploy"
```

**The console automatically:**
- Detects when tools are needed
- Calls appropriate MCP servers
- Shows tool execution results
- Integrates responses into build

### 3. Context-Aware Building

**Use @-symbols for context:**
```
@files src/*.tsx - Include all TypeScript components
@code authentication - Find auth-related code
@docs README.md - Reference documentation
@git recent - Check recent changes
```

**Example:**
```
"Refactor @files src/components/*.tsx to use
the patterns from @docs ARCHITECTURE.md"
```

### 4. Collaborative Workflow

**Start a Session:**
```
Ctrl+Shift+P → "Start Collaboration Session"
```

**Share with Team:**
- Get session link
- Team members join
- See live changes together
- Real-time code review

---

## Tips for Effective Building

### 1. Be Specific
❌ Bad: "Build an app"
✅ Good: "Build a React todo app with TypeScript, Tailwind CSS, and localStorage persistence"

### 2. Iterate Gradually
```
Step 1: "Create basic project structure"
Step 2: "Add authentication"
Step 3: "Implement user dashboard"
Step 4: "Add real-time features"
```

### 3. Use Context
```
"Based on @files src/types.ts, create API client functions"
"Following the patterns in @code services/, add a new UserService"
```

### 4. Review Changes
- Always check the right panel diffs
- Understand what's being changed
- Approve changes incrementally
- Test frequently

### 5. Save Progress
```
Ctrl+Shift+P → "Save All Files"
Ctrl+Shift+P → "Git Commit"
```

---

## Keyboard Shortcuts Reference

```
Ctrl+Shift+P  - Open Command Palette
Ctrl+K        - Inline Editor
Ctrl+T        - New Chat Tab
Ctrl+W        - Close Chat Tab
Ctrl+B        - Toggle Sidebar
Ctrl+.        - Code Actions
Alt+Enter     - Quick Question
Ctrl+S        - Save File
Ctrl+F        - Find in File
F1            - Help
```

---

## Troubleshooting

### Build Not Starting
1. Check MCP servers are running
2. Refresh browser (Ctrl+F5)
3. Check console logs
4. Try "prince status" to check agent

### No Files Showing
1. Ensure you're in the right directory
2. Click "Refresh" in file browser
3. Check permissions on folders

### Changes Not Saving
1. Use Ctrl+S or "Save All Files"
2. Check file permissions
3. Verify git repository is initialized

### Can't See Build Output
1. Check right panel is visible (Ctrl+B)
2. Enable "Show Build Output" in settings
3. Check browser console for errors

---

## Example Projects You Can Build

### Quick Projects (5-15 minutes)
- ✅ Todo List App
- ✅ Calculator
- ✅ Weather Dashboard
- ✅ Note Taking App
- ✅ URL Shortener

### Medium Projects (30-60 minutes)
- ✅ Blog Platform
- ✅ E-commerce Store
- ✅ Chat Application
- ✅ Project Management Tool
- ✅ API Service with Auth

### Complex Projects (2+ hours)
- ✅ Social Media Platform
- ✅ Real-time Collaboration Tool
- ✅ Video Streaming Service
- ✅ Trading Dashboard
- ✅ Enterprise CRM System

---

## Next Steps

1. **Try the Tutorial**: Start with a simple todo app
2. **Explore Commands**: Press Ctrl+Shift+P and browse
3. **Use Prince Flowers**: Try "@prince help" for advanced features
4. **Read Specs**: Use /specify for professional workflows
5. **Join Chat**: Get help in the chat interface

---

## Getting Help

### In Console
```
- Type "help" in chat
- Press F1 for help menu
- Use "prince help" for agent assistance
- Check /torq-spec help for spec commands
```

### Quick Support
```
Issue: Something not working
Solution: Type "prince health" to diagnose
```

---

**Ready to build? Open http://localhost:8899 and start creating!** 🚀

Your first prompt could be:
```
"Create a modern React app with TypeScript and Tailwind CSS.
It should be a simple dashboard with cards showing stats."
```

The console will take care of the rest!
