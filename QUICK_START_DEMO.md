# Quick Start Demo - Build Your First App

**Time: 5 minutes | Difficulty: Beginner**

## What We'll Build

A simple **Counter App** with React to demonstrate the Torq-Console workflow.

---

## Step 1: Open the Console

```
Browser: http://localhost:8899
```

You should see three panels:
- **Left:** Tools & MCP Integration
- **Center:** Chat interface
- **Right:** File browser & changes

---

## Step 2: Start Building

### In the Chat Box, Type:

```
Create a simple counter app with React and Vite.

Features:
- Display a number starting at 0
- Increment button (+1)
- Decrement button (-1)
- Reset button
- Modern styling with gradient background
```

Press **Enter**

---

## Step 3: Watch the Magic ✨

You'll see the console:

### Phase 1: Project Setup
```
🔨 Creating project structure...
   ├── counter-app/
   │   ├── src/
   │   │   ├── App.tsx
   │   │   ├── main.tsx
   │   │   └── index.css
   │   ├── public/
   │   ├── package.json
   │   ├── vite.config.ts
   │   └── tsconfig.json
   ✓ Complete
```

### Phase 2: Installing Dependencies
```
📦 Installing packages...
   → react@18.3.1
   → react-dom@18.3.1
   → vite@5.0.8
   → typescript@5.3.3
   ✓ Complete (15s)
```

### Phase 3: Generating Code
```
📝 Writing files...
   ✓ src/App.tsx (45 lines)
   ✓ src/main.tsx (8 lines)
   ✓ src/index.css (30 lines)
   ✓ vite.config.ts (7 lines)
   ✓ package.json (25 lines)
```

---

## Step 4: Review the Files

### Right Panel Shows:

```
📄 src/App.tsx [NEW FILE]
───────────────────────────────
+ import { useState } from 'react'
+ import './App.css'
+
+ function App() {
+   const [count, setCount] = useState(0)
+
+   return (
+     <div className="app">
+       <h1>Counter App</h1>
+       <div className="counter">{count}</div>
+       <div className="buttons">
+         <button onClick={() => setCount(c => c + 1)}>
+           +1
+         </button>
+         <button onClick={() => setCount(c => c - 1)}>
+           -1
+         </button>
+         <button onClick={() => setCount(0)}>
+           Reset
+         </button>
+       </div>
+     </div>
+   )
+ }
+
+ export default App
```

---

## Step 5: Run the App

### Option A: In Chat
```
Start the development server for the counter app
```

### Option B: Command Palette
1. Press `Ctrl+Shift+P`
2. Type "Start Dev Server"
3. Select the counter-app directory

### Option C: Manual
```bash
cd E:/Torq-Console/counter-app
npm run dev
```

---

## Step 6: See Your App!

```
VITE v5.0.8  ready in 432 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

Open http://localhost:5173/ in your browser!

---

## Step 7: Make Changes

### Ask for Modifications:

```
Add a feature to multiply the counter by 2
```

### Watch the Update:

```
📝 Updating src/App.tsx...

@@ -12,6 +12,9 @@
   <button onClick={() => setCount(c => c - 1)}>
     -1
   </button>
+  <button onClick={() => setCount(c => c * 2)}>
+    ×2
+  </button>
   <button onClick={() => setCount(0)}>
     Reset
   </button>

✓ File updated
```

The app **automatically reloads** with the new button!

---

## What You Just Learned

✅ **Create projects** through natural language
✅ **See real-time progress** of builds
✅ **Review all changes** before applying
✅ **Modify code** with simple requests
✅ **Run development servers** from console
✅ **Live reload** on changes

---

## Try These Next

### Styling Changes
```
Make the counter display bigger and use a gradient color
```

### Add Features
```
Add a step size input so users can increment by custom amounts
```

### Animation
```
Add a bounce animation when the counter changes
```

### Save Progress
```
Save all files and commit to git with message "Initial counter app"
```

---

## Advanced Example: Full-Stack App

Once comfortable, try this:

```
Create a full-stack todo app with:

Backend:
- Express.js API
- PostgreSQL database
- JWT authentication
- RESTful endpoints

Frontend:
- React with TypeScript
- Tailwind CSS
- Axios for API calls
- Login/Register pages

Features:
- User authentication
- CRUD operations for todos
- Due dates and priorities
- Search and filter
```

The console will:
1. Create backend and frontend directories
2. Set up database schema
3. Generate API routes
4. Create React components
5. Configure authentication
6. Show you every step with live diffs

---

## Pro Tips

### 1. Use Specific Language
❌ "Make an app"
✅ "Create a React todo app with TypeScript, Material-UI, and localStorage"

### 2. Iterate in Steps
```
Step 1: "Create the basic structure"
Step 2: "Add user authentication"
Step 3: "Implement the main features"
```

### 3. Use Context
```
"Based on @files src/types.ts, create matching API endpoints"
```

### 4. Ask for Explanations
```
"Explain how the authentication flow works in this app"
```

### 5. Get Code Quality Feedback
```
"Review the code and suggest improvements for performance and security"
```

---

## Keyboard Shortcuts

```
Ctrl+Shift+P  →  Command Palette
Ctrl+K        →  Inline Edit
Ctrl+T        →  New Chat
Ctrl+S        →  Save
Ctrl+B        →  Toggle Sidebar
Alt+Enter     →  Quick Question
```

---

## Need Help?

### In Console
- Type: `help`
- Type: `prince help`
- Press: `F1`

### Check Status
```
prince status
prince health
```

### Common Issues

**Server won't start?**
```
Check MCP servers: prince health
Restart console: Refresh browser (Ctrl+F5)
```

**Changes not showing?**
```
Click refresh in file browser
Check right panel for pending changes
```

**Build failed?**
```
Check error messages in right panel
Ask: "What went wrong with the build?"
Type: "Fix the build errors"
```

---

## You're Ready! 🚀

Open http://localhost:8899 and try:

```
Create a weather dashboard app with React that:
- Shows current weather
- 5-day forecast
- Location search
- Beautiful card layout
- Weather icons
```

Watch as Torq-Console builds it step by step with full visibility into every change!

---

**Happy Building!** 🎉
