# TORQ Console - Local + Production Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TORQ Console                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  LOCAL DEVELOPMENT                                               │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │ Vite Dev Server  │──────▶│ Railway Backend  │                │
│  │  localhost:5173  │ API  │ web-production...│                │
│  └──────────────────┘      └──────────────────┘                │
│         │                                                        │
│         └──► Hot Module Replacement + Proxy                     │
│                                                                   │
│  PRODUCTION (Vercel)                                             │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │   Vercel Edge    │──────▶│ Vercel API Proxy│──────▶ Railway  │
│  │ torq-console.app │ API  │ (serverless)     │      Backend    │
│  └──────────────────┘      └──────────────────┘                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Files

### 1. vite.config.ts (Local Development)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@features': path.resolve(__dirname, './src/features'),
      '@workflows': path.resolve(__dirname, './src/features/workflows'),
      '@components': path.resolve(__dirname, './src/components'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/api': {
        target: 'https://web-production-74ed0.up.railway.app',
        changeOrigin: true,
        secure: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

**Key Points:**
- **Port 5173** - Vite's default port (matches your spec)
- **API Proxy** - Routes `/api/*` to Railway backend in development
- **Path Aliases** - Clean imports across the codebase
- **Source Maps** - Enabled for debugging

### 2. tsconfig.json (TypeScript Configuration)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@features/*": ["src/features/*"],
      "@workflows/*": ["src/features/workflows/*"],
      "@components/*": ["src/components/*"],
      "@lib/*": ["src/lib/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Key Points:**
- **Path Mapping** - Matches vite.config.ts aliases
- **Bundler Resolution** - Works with Vite's module resolution
- **Strict Mode** - Type safety enabled

### 3. vercel.json (Production Deployment)

```json
{
  "buildCommand": "npx vite build",
  "outputDirectory": "dist",
  "devCommand": "npx vite",
  "installCommand": "npm install",
  "framework": null,
  "functions": {
    "api/proxy.ts": {
      "runtime": "nodejs20.x"
    }
  },
  "rewrites": [
    {
      "source": "/api/:path*",
      "function": "api/proxy.ts"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Key Points:**
- **Build Command** - `vite build` creates `dist/` folder
- **API Rewrite** - Routes `/api/*` to Vercel serverless function
- **SPA Fallback** - All other routes serve `/index.html`
- **Serverless Proxy** - Hides Railway secrets, handles CORS

### 4. package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

## Path Aliases Reference

| Alias | Resolves To | Example Usage |
|-------|-------------|---------------|
| `@/*` | `src/*` | `import { Button } from '@/components/ui'` |
| `@features/*` | `src/features/*` | `import { WorkflowsPage } from '@features/workflows/pages'` |
| `@workflows/*` | `src/features/workflows/*` | `import { useWorkflows } from '@workflows/hooks'` |
| `@components/*` | `src/components/*` | `import { Layout } from '@components/layout'` |
| `@lib/*` | `src/lib/*` | `import { cn } from '@lib/utils'` |
| `@hooks/*` | `src/hooks/*` | `import { useAuth } from '@hooks/useAuth'` |
| `@utils/*` | `src/utils/*` | `import { format } from '@utils/date'` |

## API Calls - Relative Paths Only

**✅ CORRECT - Works in both local and production:**
```typescript
// Always use relative paths
fetch('/api/tasks/graphs')
fetch('/api/tasks/executions')
fetch('/api/chat')
```

**❌ WRONG - Breaks in production:**
```typescript
// Never use full URLs
fetch('https://web-production-74ed0.up.railway.app/api/tasks/graphs')
fetch('http://localhost:8899/api/tasks/graphs')
```

## Development Workflow

### Local Development

```bash
# 1. Install dependencies
npm install

# 2. Start dev server (opens browser at localhost:5173)
npm run dev

# 3. Make changes - HMR updates automatically
# 4. Check browser console for errors
```

**What happens:**
1. Vite serves the frontend at `http://localhost:5173`
2. API calls to `/api/*` are proxied to Railway backend
3. Changes trigger hot module replacement
4. Browser refreshes automatically

### Production Build

```bash
# Build for production
npm run build

# Preview production build locally
npm run preview
```

**What happens:**
1. TypeScript compiles (`tsc`)
2. Vite bundles and optimizes to `dist/`
3. Static assets are hashed for caching
4. Source maps generated for debugging

### Deploy to Vercel

```bash
# Option 1: Vercel CLI
vercel --prod

# Option 2: Git push (if connected)
git push origin main
```

**What happens:**
1. Vercel runs `npm run build`
2. Output in `dist/` is deployed to edge network
3. `/api/*` requests go to Vercel serverless proxy
4. Proxy forwards to Railway backend (secrets hidden)

## Workflow Builder Routes

All routes are accessible in both local and production:

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | ChatPage | Main chat interface |
| `/workflows` | WorkflowsPage | Workflow list with actions |
| `/workflows/new` | NewWorkflowPage | Create from template |
| `/workflows/:graphId` | WorkflowDetailsPage | Workflow visualization |
| `/executions` | ExecutionsPage | Execution list with status |
| `/executions/:executionId` | ExecutionDetailsPage | Execution monitoring |

## Environment Variables

### Development (.env.local)
```bash
# Optional: Override Railway backend for local testing
# VITE_API_URL=http://localhost:8899
```

### Production (Vercel Dashboard)
Set these in Vercel Project Settings → Environment Variables:
```bash
RAILWAY_API_URL=https://web-production-74ed0.up.railway.app
RAILWAY_API_KEY=your-secret-key
```

## Troubleshooting

### Dev Server Issues

**Port 5173 already in use:**
```bash
# Kill process on port 5173 (Windows)
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

**Module resolution errors:**
```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Restart TypeScript Server in VS Code
Ctrl+Shift+P → "TypeScript: Restart TS Server"
```

**API proxy not working:**
```bash
# Test backend directly
curl https://web-production-74ed0.up.railway.app/health

# Test via proxy
curl http://localhost:5173/api/tasks/graphs
```

### Build Issues

**TypeScript errors:**
```bash
# Check TypeScript errors
npx tsc --noEmit
```

**Build output issues:**
```bash
# Clean build
rm -rf dist
npm run build
```

### Production Issues

**Deployment fails:**
- Check Vercel deployment logs
- Verify `buildCommand` in vercel.json
- Ensure all dependencies are in package.json

**API calls failing in production:**
- Check Vercel function logs
- Verify environment variables set
- Test API proxy function directly

## URLs Summary

| Environment | Frontend URL | API Proxy |
|-------------|--------------|-----------|
| Local | `http://localhost:5173` | Vite → Railway |
| Production | `https://torq-console.vercel.app` | Vercel Function → Railway |

## Next Steps

1. **Start local development:**
   ```bash
   npm run dev
   # Opens at http://localhost:5173
   ```

2. **Test workflow routes:**
   - http://localhost:5173/workflows
   - http://localhost:5173/workflows/new
   - http://localhost:5173/executions

3. **Verify API connectivity:**
   ```bash
   curl http://localhost:5173/api/tasks/graphs
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

5. **Deploy to Vercel:**
   ```bash
   vercel --prod
   ```

---

**Status:** ✅ Configuration complete for both local development and production deployment.
