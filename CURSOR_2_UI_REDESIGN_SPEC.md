# TORQ Console UI Redesign: Cursor 2.0 Style

## Vision

Transform TORQ Console from a traditional CLI/web interface into a **modern, agent-centric development environment** inspired by Cursor 2.0's revolutionary design.

## Cursor 2.0 Key Principles

### 1. **Agent-Centric Design**
- Interface centers around **agents rather than files**
- Focus on **outcomes, not implementation**
- Agents are first-class citizens in the UI

### 2. **Flexible Navigation**
- Easy switching between agent view and classic IDE view
- "Easily open files when needed or switch back to classic IDE"
- Contextual navigation based on task

### 3. **Multi-Agent Coordination**
- Run multiple agents simultaneously without interference
- Compare outputs and select best results
- Visual representation of parallel work

### 4. **Code Review Excellence**
- "Much easier to quickly review changes an agent has made"
- Dive deeper into code when needed
- Streamlined diff viewing

### 5. **Native Testing Integration**
- Built-in browser tool for autonomous testing
- Agents can test their own work
- Iterate until correct

### 6. **Polished, Modern Aesthetics**
- Clean, minimal interface
- Smooth animations and transitions
- Professional typography and spacing

---

## TORQ Console UI Redesign Architecture

### Core Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  TORQ Console                                    [⚙️] [👤] [🔔]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────┐  ┌─────────────────────────────────────────────┐│
│  │           │  │                                             ││
│  │  Agents   │  │         Agent Workspace                     ││
│  │  Panel    │  │                                             ││
│  │           │  │  ┌────────────────────────────────────────┐││
│  │  • Prince │  │  │                                        │││
│  │    Flowers│  │  │  Conversation / Task View              │││
│  │           │  │  │                                        │││
│  │  • Code   │  │  │  [Agent chat, inline edits, diffs]    │││
│  │    Review │  │  │                                        │││
│  │           │  │  │                                        │││
│  │  • Search │  │  └────────────────────────────────────────┘││
│  │    Master │  │                                             ││
│  │           │  │  ┌────────────────────────────────────────┐││
│  │  • File   │  │  │                                        │││
│  │    Ops    │  │  │  Code Preview / Diff Viewer            │││
│  │           │  │  │                                        │││
│  │  [+ New]  │  │  │  [Live file preview, syntax highlight] │││
│  │           │  │  │                                        │││
│  └───────────┘  │  └────────────────────────────────────────┘││
│                  │                                             ││
│                  └─────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. **Top Navigation Bar**
```tsx
<TopNav>
  <Logo>TORQ Console</Logo>
  <SearchBar placeholder="Search or ask..." />
  <QuickActions>
    <NotificationBell />
    <Settings />
    <UserProfile />
  </QuickActions>
</TopNav>
```

#### 2. **Agent Sidebar** (Left Panel)
```tsx
<AgentSidebar>
  <AgentList>
    <AgentCard
      name="Prince Flowers"
      status="active"
      avatar="🤖"
      capabilities={["chat", "code", "research"]}
    />
    <AgentCard
      name="Code Reviewer"
      status="idle"
      avatar="👀"
      capabilities={["review", "refactor"]}
    />
    <AgentCard
      name="Search Master"
      status="idle"
      avatar="🔍"
      capabilities={["search", "research"]}
    />
  </AgentList>
  <NewAgentButton />
</AgentSidebar>
```

#### 3. **Agent Workspace** (Center)
```tsx
<AgentWorkspace>
  <ConversationView>
    <MessageList>
      <UserMessage>Create authentication system</UserMessage>
      <AgentMessage>
        <AgentThinking>Analyzing requirements...</AgentThinking>
        <AgentPlan>
          1. Create user model
          2. Implement JWT tokens
          3. Add password hashing
        </AgentPlan>
        <AgentActions>
          <FileCreated path="auth.py" />
          <FileModified path="models.py" />
        </AgentActions>
      </AgentMessage>
    </MessageList>
    <InputBar>
      <CommandPalette />
      <AttachFiles />
      <VoiceInput />
    </InputBar>
  </ConversationView>

  <DiffViewer>
    <SplitDiff
      before={originalCode}
      after={modifiedCode}
      language="python"
    />
    <ActionBar>
      <AcceptChanges />
      <RejectChanges />
      <ModifyRequest />
    </ActionBar>
  </DiffViewer>
</AgentWorkspace>
```

#### 4. **Code Preview Panel** (Right, Collapsible)
```tsx
<CodePreviewPanel>
  <TabBar>
    <Tab file="auth.py" modified={true} />
    <Tab file="models.py" modified={false} />
  </TabBar>
  <CodeEditor
    language="python"
    showLineNumbers={true}
    showMinimap={true}
    readOnly={true}
  />
  <QuickActions>
    <OpenInIDE />
    <CopyCode />
    <RunTests />
  </QuickActions>
</CodePreviewPanel>
```

---

## Design System

### Color Palette (Dark Theme)

```scss
$colors: (
  // Base
  bg-primary: #1e1e1e,
  bg-secondary: #252526,
  bg-tertiary: #2d2d30,

  // Agent colors
  agent-active: #0078d4,
  agent-thinking: #f59e0b,
  agent-success: #10b981,
  agent-error: #ef4444,

  // Text
  text-primary: #ffffff,
  text-secondary: #cccccc,
  text-muted: #808080,

  // Accent
  accent-primary: #0078d4,
  accent-hover: #0086f0,

  // Borders
  border: #3e3e42,
  border-focus: #0078d4,

  // Diff colors
  diff-added: rgba(16, 185, 129, 0.15),
  diff-removed: rgba(239, 68, 68, 0.15),
  diff-modified: rgba(245, 158, 11, 0.15)
);
```

### Typography

```scss
$fonts: (
  primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif,
  mono: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', monospace
);

$type-scale: (
  h1: 2rem,      // 32px - Page titles
  h2: 1.5rem,    // 24px - Section titles
  h3: 1.25rem,   // 20px - Subsection titles
  body: 0.875rem,// 14px - Body text
  small: 0.75rem,// 12px - Captions
  code: 0.875rem // 14px - Code
);
```

### Spacing System

```scss
$spacing: (
  xs: 0.25rem,   // 4px
  sm: 0.5rem,    // 8px
  md: 1rem,      // 16px
  lg: 1.5rem,    // 24px
  xl: 2rem,      // 32px
  2xl: 3rem      // 48px
);
```

### Border Radius

```scss
$radius: (
  sm: 0.25rem,   // 4px - Buttons, inputs
  md: 0.5rem,    // 8px - Cards
  lg: 0.75rem,   // 12px - Panels
  full: 9999px   // Circular
);
```

---

## Key Features Implementation

### 1. **Agent-Centric Chat Interface**

```tsx
// components/AgentChat.tsx
import React, { useState } from 'react';
import { MessageList, InputBar, AgentStatus } from './chat';

export const AgentChat: React.FC = () => {
  const [messages, setMessages] = useState([]);
  const [activeAgent, setActiveAgent] = useState('prince_flowers');

  return (
    <div className="agent-chat">
      <AgentStatus
        name={activeAgent}
        status="ready"
        capabilities={["code", "chat", "research"]}
      />

      <MessageList messages={messages}>
        {messages.map(msg => (
          <Message
            key={msg.id}
            content={msg.content}
            type={msg.type}
            timestamp={msg.timestamp}
            actions={msg.actions}
          />
        ))}
      </MessageList>

      <InputBar
        onSend={handleSend}
        placeholder="Ask Prince Flowers anything..."
        suggestions={getContextualSuggestions()}
      />
    </div>
  );
};
```

### 2. **Inline Diff Viewer**

```tsx
// components/DiffViewer.tsx
import React from 'react';
import { Diff } from 'react-diff-viewer';

export const InlineDiffViewer: React.FC<DiffProps> = ({
  oldCode,
  newCode,
  language,
  onAccept,
  onReject
}) => {
  return (
    <div className="diff-viewer">
      <DiffHeader>
        <FileName>{file.path}</FileName>
        <DiffStats added={stats.added} removed={stats.removed} />
      </DiffHeader>

      <Diff
        oldValue={oldCode}
        newValue={newCode}
        splitView={false}
        useDarkTheme={true}
        showDiffOnly={false}
        compareMethod="diffWords"
      />

      <ActionBar>
        <Button variant="primary" onClick={onAccept}>
          Accept Changes
        </Button>
        <Button variant="secondary" onClick={onReject}>
          Reject
        </Button>
        <Button variant="ghost" onClick={onModify}>
          Request Modification
        </Button>
      </ActionBar>
    </div>
  );
};
```

### 3. **Multi-Agent Coordination**

```tsx
// components/MultiAgentView.tsx
import React from 'react';

export const MultiAgentView: React.FC = () => {
  const [agents, setAgents] = useState([
    { id: 1, name: "Prince Flowers", task: "Backend API" },
    { id: 2, name: "Code Reviewer", task: "Code quality check" },
    { id: 3, name: "Test Generator", task: "Unit tests" }
  ]);

  return (
    <div className="multi-agent-grid">
      {agents.map(agent => (
        <AgentWorkspaceCard key={agent.id}>
          <AgentHeader
            name={agent.name}
            status={agent.status}
            progress={agent.progress}
          />

          <WorkspacePreview>
            <CodeSnippet code={agent.currentCode} />
            <ProgressIndicator steps={agent.steps} />
          </WorkspacePreview>

          <CompareActions>
            <Button onClick={() => selectAgent(agent.id)}>
              Use This Result
            </Button>
            <Button onClick={() => compareWith(agent.id)}>
              Compare
            </Button>
          </CompareActions>
        </AgentWorkspaceCard>
      ))}
    </div>
  );
};
```

### 4. **Command Palette** (Cmd+K / Ctrl+K)

```tsx
// components/CommandPalette.tsx
import React, { useState } from 'react';

export const CommandPalette: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const commands = [
    { id: 'agent.new', label: 'Create New Agent', icon: '🤖' },
    { id: 'file.open', label: 'Open File', icon: '📁' },
    { id: 'search.code', label: 'Search in Code', icon: '🔍' },
    { id: 'git.commit', label: 'Commit Changes', icon: '💾' },
    { id: 'diff.view', label: 'View Diff', icon: '🔄' },
  ];

  return (
    <CommandPaletteModal open={isOpen} onClose={onClose}>
      <SearchInput
        value={query}
        onChange={setQuery}
        placeholder="Search commands or ask a question..."
        autoFocus
      />

      <CommandList>
        {fuzzySearch(commands, query).map(cmd => (
          <CommandItem
            key={cmd.id}
            icon={cmd.icon}
            label={cmd.label}
            shortcut={cmd.shortcut}
            onClick={() => executeCommand(cmd.id)}
          />
        ))}
      </CommandList>

      <Footer>
        <Hint>↑↓ navigate • Enter select • Esc close</Hint>
      </Footer>
    </CommandPaletteModal>
  );
};
```

### 5. **Code Review Workflow**

```tsx
// components/CodeReview.tsx
import React from 'react';

export const CodeReviewPanel: React.FC = () => {
  const [changes, setChanges] = useState([]);
  const [currentFile, setCurrentFile] = useState(0);

  return (
    <ReviewContainer>
      <ReviewHeader>
        <ReviewTitle>Code Review</ReviewTitle>
        <ReviewProgress>
          {currentFile + 1} / {changes.length} files
        </ReviewProgress>
      </ReviewHeader>

      <FileNavigator>
        {changes.map((file, idx) => (
          <FileTab
            key={idx}
            active={idx === currentFile}
            onClick={() => setCurrentFile(idx)}
          >
            <FileIcon type={file.type} />
            <FileName>{file.name}</FileName>
            <ChangeIndicator
              added={file.stats.added}
              removed={file.stats.removed}
            />
          </FileTab>
        ))}
      </FileNavigator>

      <DiffViewer file={changes[currentFile]} />

      <ReviewActions>
        <Button onClick={previousFile}>Previous</Button>
        <Button onClick={nextFile}>Next</Button>
        <Spacer />
        <Button variant="danger" onClick={rejectAll}>
          Reject All
        </Button>
        <Button variant="success" onClick={acceptAll}>
          Accept All
        </Button>
      </ReviewActions>
    </ReviewContainer>
  );
};
```

---

## Technology Stack

### Frontend

- **Framework**: React 18 with TypeScript
- **Styling**: TailwindCSS + CSS Modules
- **State Management**: Zustand (lightweight, modern)
- **Component Library**: Radix UI (unstyled, accessible)
- **Code Editor**: Monaco Editor (VSCode's editor)
- **Diff Viewer**: react-diff-viewer-continued
- **Icons**: Lucide React
- **Animations**: Framer Motion

### Backend

- **Server**: FastAPI (Python) - Already integrated
- **WebSocket**: Socket.IO - Already integrated
- **MCP Integration**: Existing infrastructure

### Build Tools

- **Bundler**: Vite (fast, modern)
- **Package Manager**: pnpm (fast, efficient)
- **Linter**: ESLint + Prettier

---

## File Structure

```
TORQ-CONSOLE/
├── frontend/                      # New React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── agents/
│   │   │   │   ├── AgentChat.tsx
│   │   │   │   ├── AgentSidebar.tsx
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   └── MultiAgentView.tsx
│   │   │   ├── code/
│   │   │   │   ├── DiffViewer.tsx
│   │   │   │   ├── CodeEditor.tsx
│   │   │   │   └── CodePreview.tsx
│   │   │   ├── chat/
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── InputBar.tsx
│   │   │   │   └── Message.tsx
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── CommandPalette.tsx
│   │   │   └── layout/
│   │   │       ├── TopNav.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Workspace.tsx
│   │   ├── hooks/
│   │   │   ├── useAgent.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useCodeDiff.ts
│   │   ├── stores/
│   │   │   ├── agentStore.ts
│   │   │   ├── uiStore.ts
│   │   │   └── codeStore.ts
│   │   ├── styles/
│   │   │   ├── globals.css
│   │   │   ├── themes.css
│   │   │   └── animations.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── torq_console/                 # Existing Python backend
│   └── ui/
│       └── api/                  # New API endpoints for React frontend
│           ├── agents.py
│           ├── code.py
│           └── websocket.py
│
└── docs/
    └── UI_REDESIGN_GUIDE.md
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up React + TypeScript + Vite
- [ ] Create design system (colors, typography, spacing)
- [ ] Build core UI components (Button, Card, Modal)
- [ ] Implement layout structure (TopNav, Sidebar, Workspace)

### Phase 2: Agent Interface (Week 3-4)
- [ ] Agent sidebar with agent cards
- [ ] Agent chat interface
- [ ] Message components (user, agent, system)
- [ ] Input bar with command palette integration

### Phase 3: Code Features (Week 5-6)
- [ ] Inline diff viewer
- [ ] Code preview panel
- [ ] Monaco editor integration
- [ ] Syntax highlighting for multiple languages

### Phase 4: Advanced Features (Week 7-8)
- [ ] Multi-agent coordination view
- [ ] Code review workflow
- [ ] File navigator
- [ ] Quick actions and shortcuts

### Phase 5: Polish & Testing (Week 9-10)
- [ ] Animations and transitions
- [ ] Dark/light theme toggle
- [ ] Accessibility improvements
- [ ] Performance optimization
- [ ] E2E testing

---

## Keyboard Shortcuts (Cursor-style)

```typescript
const shortcuts = {
  // Command Palette
  'Cmd+K': 'Open command palette',
  'Cmd+P': 'Quick file open',

  // Agent Actions
  'Cmd+Shift+A': 'New agent',
  'Cmd+Shift+C': 'Chat with agent',
  'Cmd+Shift+R': 'Review changes',

  // Navigation
  'Cmd+1..9': 'Switch to agent N',
  'Cmd+B': 'Toggle sidebar',
  'Cmd+J': 'Toggle terminal',

  // Code Actions
  'Cmd+D': 'View diff',
  'Cmd+Shift+D': 'Accept all changes',
  'Cmd+Shift+X': 'Reject all changes',

  // Search
  'Cmd+F': 'Search in file',
  'Cmd+Shift+F': 'Search in project',
};
```

---

## API Endpoints (New)

```python
# torq_console/ui/api/agents.py

from fastapi import APIRouter, WebSocket
from typing import List

router = APIRouter(prefix="/api/agents")

@router.get("/")
async def list_agents() -> List[Agent]:
    """List all available agents."""
    return agent_registry.list()

@router.post("/{agent_id}/chat")
async def send_message(agent_id: str, message: str):
    """Send message to agent."""
    return await agent_registry.get(agent_id).process(message)

@router.websocket("/{agent_id}/stream")
async def agent_stream(websocket: WebSocket, agent_id: str):
    """Stream agent responses via WebSocket."""
    await websocket.accept()
    # Stream implementation
```

---

## Next Steps

1. **Review this spec** - Ensure alignment with vision
2. **Set up React frontend** - Initialize Vite + React + TypeScript
3. **Create design system** - Implement colors, typography, components
4. **Build core layout** - TopNav, Sidebar, Workspace structure
5. **Implement agent chat** - Message list, input bar, WebSocket
6. **Add diff viewer** - Code comparison and review tools
7. **Polish and test** - Animations, accessibility, performance

---

**Status**: 📋 Specification Ready
**Next**: Begin Phase 1 implementation
**Timeline**: 10 weeks to full Cursor 2.0-style UI
**Priority**: High - Transform user experience
