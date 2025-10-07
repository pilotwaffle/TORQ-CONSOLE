# How to Fix: Console Doing Research Instead of Building

## What Happened

Your console is in **Ideation Mode** which causes it to:
- ❌ Research about building apps
- ❌ Search the web for information
- ❌ Gather ideas and examples
- ✅ Instead of actually building

## Quick Fixes

### Fix 1: Disable Ideation Mode

1. Look at the top-left of the console
2. See "💡 Ideation Mode" indicator?
3. Click it to toggle OFF
4. Resubmit your build request

### Fix 2: Use Direct Build Language

Instead of:
```
# AI Prompt Library Application
## Project Overview
Build a sophisticated prompt management system...
```

Use:
```
BUILD: Create an AI Prompt Library with Next.js, Supabase,
and Claude API. Include markdown editor, authentication,
and prompt optimization features.
```

### Fix 3: Start with Project Command

```
Create a new Next.js 14 TypeScript project called "prompt-library"
```

Then add features step by step.

---

## Why This Happens

### Ideation Mode Triggers
- Long formatted specifications (markdown headings)
- Research-style questions
- "Overview" or "Planning" keywords
- Multiple sections with details

### Build Mode Triggers
- Direct "Create", "Build", "Make" commands
- Specific tech stack mentioned first
- Simple, clear instructions
- Action verbs at start

---

## Correct Build Commands

### ✅ Good Build Commands

```
Create a Next.js app with Supabase and authentication
```

```
Build a markdown editor with live preview using React
```

```
Make a todo app with TypeScript and Tailwind CSS
```

### ❌ Commands That Trigger Research

```
# Project Overview
I want to understand how to build...
```

```
Research the best practices for...
```

```
What are the options for building...
```

---

## For Your AI Prompt Library

### Step 1: Create Base Project
```
Create a new Next.js 14 project with:
- TypeScript
- Tailwind CSS
- App Router
- Shadcn UI components

Name it "ai-prompt-library"
```

### Step 2: Add Database
```
Add Supabase integration with:
- Users table
- Prompts table (id, user_id, title, content, tags, is_favorite)
- Authentication setup
```

### Step 3: Add Editor
```
Create a markdown editor component with:
- React Markdown for rendering
- Syntax highlighting
- Live preview split screen
- Toolbar for formatting
```

### Step 4: Add Claude Integration
```
Add Claude API integration:
- Optimize button
- API route for Claude calls
- Loading states
- Display suggestions
```

### Step 5: Add UI
```
Implement TORQ brand styling:
- Space Cadet (#2b2d42) backgrounds
- Red Pantone (#ef233c) accents
- Card-based layouts
- Smooth transitions
```

---

## Checking Current Mode

### Look for These Indicators

**Ideation Mode Active:**
```
💡 Ideation Mode
🌐 Web Research ✓
```

**Build Mode Active:**
```
🔨 Building...
📦 Installing packages...
📝 Creating files...
```

### Console Status

Check top-right:
- Model selector
- MCP status
- Mode indicators

---

## Pro Tips

### 1. Start Simple
Don't paste full specs immediately. Build incrementally.

### 2. Use Clear Commands
Begin with "Create", "Build", "Make", "Generate"

### 3. One Feature at a Time
Break complex projects into steps

### 4. Check Mode Before Submitting
Verify ideation mode is OFF for building

### 5. Use Spec-Kit for Complex Projects
```
/specify create "ProjectName" "Description"
/plan generate spec_0001
/implement start spec_0001
```

---

## Emergency Reset

If console is stuck in research mode:

1. **Refresh Browser** (Ctrl+F5)
2. **Click New Chat** (Ctrl+T)
3. **Toggle Ideation Mode OFF**
4. **Start with simple command:**
   ```
   Create a basic Next.js project
   ```

---

## Testing the Fix

After applying any fix, test with:

```
Create a simple counter app with React
```

If you see:
```
🔨 Creating project structure...
```

✅ **You're in build mode!**

If you see:
```
🌐 Searching for information about...
```

❌ **Still in research mode - try another fix**

---

## For Your Specific Project

Here's the correct way to build your AI Prompt Library:

```bash
# Open console at http://localhost:8899
# Make sure Ideation Mode is OFF
# Then paste this command:

Build an AI Prompt Library application:

Tech Stack:
- Next.js 14 with App Router
- TypeScript
- Supabase (database + auth)
- Tailwind CSS + Shadcn UI
- Claude Sonnet 4.5 API

Core Features:
1. User authentication (email + Google OAuth)
2. Markdown editor with live preview
3. Prompt library with grid/list views
4. Tags and favorites system
5. Claude API integration for prompt optimization
6. TORQ brand colors (Space Cadet, Red Pantone)

Start with project setup and basic structure.
```

This should trigger **build mode** and start creating your app!
