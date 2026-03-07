# Vite Configuration Guide - TORQ Console Frontend

## Overview

This guide explains the production-ready Vite configuration for TORQ Console, including path aliases, API proxy setup, and Railway backend integration.

## Configuration Files

### 1. vite.config.ts

The main Vite configuration file with comprehensive path aliases and Railway backend proxy.

```typescript
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiUrl = env.VITE_API_URL || 'https://web-production-74ed0.up.railway.app'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@workflows': path.resolve(__dirname, './src/features/workflows'),
        // ... see full config
      },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },
  }
})
```

### 2. tsconfig.json

TypeScript configuration matching Vite's path aliases.

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@workflows/*": ["./src/features/workflows/*"],
      "@features/*": ["./src/features/*"],
      // ... see full config
    }
  }
}
```

## Path Aliases

| Alias | Resolves To | Usage Example |
|-------|-------------|---------------|
| `@/*` | `./src/*` | `import { Button } from '@/components/ui'` |
| `@workflows/*` | `./src/features/workflows/*` | `import { useWorkflows } from '@workflows/hooks'` |
| `@features/*` | `./src/features/*` | `import { ChatFeature } from '@features/chat'` |
| `@components/*` | `./src/components/*` | `import { Layout } from '@components/layout'` |
| `@lib/*` | `./src/lib/*` | `import { cn } from '@lib/utils'` |
| `@hooks/*` | `./src/hooks/*` | `import { useAuth } from '@hooks/useAuth'` |
| `@utils/*` | `./src/utils/*` | `import { format } from '@utils/date'` |
| `@stores/*` | `./src/stores/*` | `import { useStore } from '@stores/app'` |
| `@pages/*` | `./src/pages/*` | `import { HomePage } from '@pages/Home'` |
| `@api/*` | `./src/api/*` | `import { client } from '@api/client'` |
| `@types/*` | `./src/types/*` | `import { User } from '@types/models'` |
| `@config/*` | `./src/config/*` | `import { config } from '@config/app'` |
| `@assets/*` | `./src/assets/*` | `import logo from '@assets/logo.svg'` |

## API Proxy Configuration

### Development Mode

When running `npm run dev`, API requests are proxied to the backend:

```
Frontend (localhost:3000) → Vite Dev Server → Backend (Railway)
```

### Environment Variables

Create a `.env.local` file for local development:

```bash
# Railway Production Backend (default)
VITE_API_URL=https://web-production-74ed0.up.railway.app

# Or use local backend
# VITE_API_URL=http://localhost:8899
```

### Production Build

For production deployment, the API URL is embedded at build time:

```typescript
// In vite.config.ts
define: {
  __API_URL__: JSON.stringify(apiUrl),
}
```

Usage in code:

```typescript
const apiUrl = import.meta.env.__API_URL__ || import.meta.env.VITE_API_URL
```

## Railway Backend Integration

### Current Production Backend

```
https://web-production-74ed0.up.railway.app
```

### API Endpoints

All API requests are prefixed with `/api` and proxied to Railway:

```
GET    /api/tasks/graphs         → https://railway.../api/tasks/graphs
POST   /api/tasks/graphs         → https://railway.../api/tasks/graphs
GET    /api/tasks/executions     → https://railway.../api/tasks/executions
GET    /health                   → https://railway.../health
```

## Development Workflow

### 1. Start Development Server

```bash
npm run dev
```

The dev server starts on `http://localhost:3000` with API proxying enabled.

### 2. Verify API Connection

```bash
# Test API health
curl http://localhost:3000/health

# Test workflows endpoint
curl http://localhost:3000/api/tasks/graphs
```

### 3. Build for Production

```bash
# Build with production API URL
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

### Module Resolution Errors

If you see "Cannot find module" errors:

1. **Restart TypeScript Server** in VS Code: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"
2. **Clear Vite cache**: `rm -rf node_modules/.vite`
3. **Reinstall dependencies**: `rm -rf node_modules && npm install`

### API Proxy Not Working

If API requests fail in development:

1. **Check backend is running**: `curl https://web-production-74ed0.up.railway.app/health`
2. **Verify VITE_API_URL**: `echo $VITE_API_URL`
3. **Check vite.config.ts proxy configuration**
4. **Check browser console for CORS errors**

### Path Aliases Not Resolving

If imports using `@/...` don't work:

1. **Verify both tsconfig.json and vite.config.ts** have matching aliases
2. **Restart dev server** after changing config
3. **Check for typos** in import paths

## Next Steps

1. **Run the API verification script**: `bash verify-workflow-api.sh`
2. **Start the frontend**: `npm run dev`
3. **Navigate to**: `http://localhost:3000/workflows`
4. **Follow the QA Test Plan**: See `WORKFLOW_BUILDER_QA_TEST_PLAN.md`

## Configuration Checklist

- [x] Path aliases configured in both tsconfig.json and vite.config.ts
- [x] API proxy configured for Railway backend
- [x] Environment variable support (VITE_API_URL)
- [x] Production build optimization (code splitting, chunking)
- [x] WebSocket proxy support for Socket.IO
- [x] Development server configured for port 3000
- [x] Source maps enabled for debugging

---

**Status**: Configuration complete and ready for development/testing.
