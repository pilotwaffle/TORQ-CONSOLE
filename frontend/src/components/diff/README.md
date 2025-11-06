# TORQ Console Diff Components

Production-ready inline diff viewer components for TORQ Console with Monaco editor integration.

## Components

### 1. DiffViewer
Main diff viewer component using Monaco editor with TORQ color scheme.

**Features:**
- Side-by-side and unified diff views
- Line-by-line highlighting with TORQ colors (green for additions, red for deletions)
- Navigation between changes with keyboard shortcuts
- Toggle between view modes
- Minimap support for large diffs
- Custom styling matching TORQ design system

**Usage:**
```tsx
import { DiffViewer } from '@/components/diff';

<DiffViewer
  original="const x = 1;"
  modified="const x = 2;"
  language="typescript"
  viewMode="split"
  height="500px"
/>
```

**Props:**
- `original: string` - Original code content
- `modified: string` - Modified code content
- `language?: string` - Language for syntax highlighting (default: 'plaintext')
- `viewMode?: 'split' | 'unified'` - Diff view mode (default: 'split')
- `showMinimap?: boolean` - Show Monaco minimap (default: false)
- `readOnly?: boolean` - Make editor read-only (default: true)
- `height?: string` - Editor height (default: '400px')
- `onViewModeChange?: (mode) => void` - Callback when view mode changes

### 2. DiffStats
Displays diff statistics with visual indicators.

**Features:**
- Addition/deletion counts with TORQ green/red colors
- Visual ratio bar showing change distribution
- File name display with icon
- Multiple file support
- Net change calculation
- Large diff warnings

**Usage:**
```tsx
import { DiffStats } from '@/components/diff';

<DiffStats
  additions={42}
  deletions={15}
  fileName="src/App.tsx"
  showBar={true}
/>
```

**Props:**
- `additions: number` - Number of added lines
- `deletions: number` - Number of deleted lines
- `fileName?: string` - File name to display
- `fileCount?: number` - Number of files changed (default: 1)
- `showBar?: boolean` - Show visual ratio bar (default: true)
- `showFileIcon?: boolean` - Show file icon (default: true)

**Variants:**
- `CompactDiffStats` - Inline compact version (+42 -15)
- `DiffStatsList` - Multi-file stats with totals

### 3. DiffMessage
Collapsible diff viewer for chat messages.

**Features:**
- Shows stats by default, expands to full diff on click
- Uses DiffViewer component for expanded view
- Compact preview of first few lines when collapsed
- File name and language support
- Large diff handling with appropriate height
- Smooth expand/collapse animations

**Usage:**
```tsx
import { DiffMessage } from '@/components/diff';

<DiffMessage
  diff={{
    additions: 42,
    deletions: 15,
    hunks: [...]
  }}
  fileName="src/App.tsx"
  language="typescript"
/>
```

**Props:**
- `diff: DiffBlock` - Diff data structure from types.ts
- `fileName?: string` - File name to display
- `language?: string` - Language for syntax highlighting
- `defaultExpanded?: boolean` - Start expanded (default: false)

**Variants:**
- `InlineDiffMessage` - Compact inline version without expansion

## Type Definitions

All diff-related types are defined in `src/lib/types.ts`:

```typescript
interface DiffBlock {
  additions: number;
  deletions: number;
  hunks: DiffHunk[];
}

interface DiffHunk {
  oldStart: number;
  oldLines: number;
  newStart: number;
  newLines: number;
  lines: DiffLine[];
}

interface DiffLine {
  type: 'add' | 'remove' | 'context';
  content: string;
  lineNumber?: number;
}
```

## TORQ Color Scheme

The components use TORQ's color scheme defined in `tailwind.config.js`:

- **Additions**: `#10b981` (torq-green)
- **Deletions**: `#ef4444` (torq-red)
- **Modified**: `#f59e0b` (torq-orange)
- **Background overlays**: 15% opacity for line highlights, 30% for character highlights

## Integration with Chat Messages

The `DiffMessage` component is designed to work seamlessly with TORQ's chat system:

```tsx
// In ChatMessage.tsx
{message.type === 'diff' && message.metadata?.diff && (
  <DiffMessage
    diff={message.metadata.diff}
    fileName={message.metadata.filePath}
    language={message.metadata.language}
  />
)}
```

## Monaco Editor Configuration

The DiffViewer uses the following Monaco editor options:
- Font: JetBrains Mono, Fira Code, Source Code Pro
- Font Size: 14px
- Line Height: 20px
- Theme: vs-dark with TORQ custom colors
- Whitespace rendering: On selection
- Automatic layout resizing
- Overview ruler enabled

## Keyboard Shortcuts

When focused on the diff viewer:
- `F7` - Next change
- `Shift+F7` - Previous change
- `Alt+F5` - Toggle between split/unified view (custom)

## Performance Considerations

- Debounced rendering for large diffs
- Minimap automatically enabled for diffs > 500 lines
- Virtual scrolling via Monaco editor
- Lazy loading of Monaco editor bundle
- Memoized diff calculation

## Examples

See `DiffExample.tsx` for comprehensive usage examples including:
- Basic diff viewing
- Multiple file statistics
- Collapsible chat messages
- Inline compact diffs
- All component variants

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Monaco editor requires modern ES6+ support

## Dependencies

- `@monaco-editor/react` ^4.6.0
- `monaco-editor` ^0.45.0
- `lucide-react` ^0.294.0 (icons)
- `class-variance-authority` ^0.7.1 (styling)

## Testing

Key test scenarios:
1. Side-by-side vs unified view rendering
2. Navigation between multiple changes
3. Large diff handling (1000+ lines)
4. Collapsible expand/collapse state
5. Keyboard navigation
6. Color contrast accessibility
7. Mobile responsive behavior

## Accessibility

- ARIA labels on navigation buttons
- Keyboard navigation support
- Color contrast ratio compliance (WCAG AA)
- Screen reader friendly announcements
- Focus management for keyboard users

## Future Enhancements

Potential improvements:
- Inline editing with merge conflict resolution
- Comment threads on specific lines
- Export to patch file
- Copy diff to clipboard
- Syntax highlighting themes
- Word-level diff highlighting
- Fold unchanged regions

---

**File Locations:**
- `src/components/diff/DiffViewer.tsx` - Main viewer (9KB)
- `src/components/diff/DiffStats.tsx` - Statistics (7KB)
- `src/components/chat/DiffMessage.tsx` - Chat integration (9KB)
- `src/components/diff/index.ts` - Barrel exports
- `src/lib/types.ts` - Type definitions (existing)

**Total:** ~4 new files, ~25KB of production code
