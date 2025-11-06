# TORQ Console Frontend

Modern, agent-centric UI inspired by Cursor 2.0, built with React, TypeScript, and Vite.

## Features

- **Agent-Centric Interface**: UI focused on agent interactions rather than traditional file trees
- **Real-time Chat**: Interactive chat interface with multiple agents
- **Modern Design System**: Custom design tokens matching Cursor 2.0 aesthetics
- **Type-Safe**: Full TypeScript support with strict type checking
- **State Management**: Zustand for efficient, minimal state management
- **Responsive Layout**: Adaptive layout with sidebar and main workspace

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first styling
- **Zustand** - State management
- **class-variance-authority** - Type-safe component variants
- **Socket.IO Client** - Real-time communication (planned)

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Badge.tsx
│   │   ├── layout/       # Layout components
│   │   │   ├── TopNav.tsx
│   │   │   └── AgentSidebar.tsx
│   │   └── chat/         # Chat-related components
│   │       ├── ChatWindow.tsx
│   │       ├── ChatMessage.tsx
│   │       └── ChatInput.tsx
│   ├── stores/           # Zustand stores
│   │   └── agentStore.ts
│   ├── lib/              # Utilities and types
│   │   └── types.ts
│   ├── App.tsx           # Main application
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Visit http://localhost:3000

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Design System

### Colors

- **Background**: Primary (#1e1e1e), Secondary (#252526), Tertiary (#2d2d30)
- **Text**: Primary (#ffffff), Secondary (#cccccc), Muted (#808080)
- **Agent States**: Active (#0078d4), Thinking (#f59e0b), Success (#10b981), Error (#ef4444)
- **Accents**: Primary (#0078d4), Hover (#0086f0)
- **Borders**: Default (#3e3e42), Focus (#0078d4)

### Typography

- **Fonts**: Inter (sans-serif), JetBrains Mono (monospace)
- **Sizes**: H1 (32px), H2 (24px), H3 (20px), Body (14px), Small (12px), Code (14px)

### Component Variants

#### Button
- `default` - Primary action button
- `secondary` - Secondary action with border
- `ghost` - Transparent hover state
- `danger` - Destructive action

#### Badge
- `default` - Accent colored
- `secondary` - Muted background
- `success` - Green for success states
- `warning` - Yellow for in-progress
- `error` - Red for error states
- `active` - Blue for active agents

## State Management

The app uses Zustand for centralized state management:

```typescript
import { useAgentStore } from '@/stores/agentStore';

// Access state and actions
const { agents, activeAgentId, setActiveAgent } = useAgentStore();
```

### Store Structure

- `agents` - List of available agents
- `activeAgentId` - Currently selected agent
- `sessions` - Chat sessions
- `activeSessionId` - Current chat session
- `workspace` - Workspace configuration
- `isConnected` - WebSocket connection status

## Backend Integration

The frontend connects to the TORQ Console backend at `http://localhost:8899`:

- **HTTP API**: `/api/*` - REST endpoints
- **WebSocket**: `/socket.io` - Real-time communication

### Vite Proxy Configuration

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8899',
    changeOrigin: true,
  },
  '/socket.io': {
    target: 'http://localhost:8899',
    changeOrigin: true,
    ws: true,
  },
}
```

## Next Steps

- [ ] Implement WebSocket connection for real-time updates
- [ ] Add Monaco Editor for code viewing/editing
- [ ] Build inline diff viewer component
- [ ] Add multi-agent coordination panel
- [ ] Implement command palette (Ctrl+K)
- [ ] Add keyboard shortcuts
- [ ] Create settings panel
- [ ] Add dark/light theme toggle
- [ ] Implement file tree viewer
- [ ] Add session persistence

## Contributing

This is part of the TORQ Console project. See the main README for contribution guidelines.

## License

Part of TORQ Console - see main project for license details.
