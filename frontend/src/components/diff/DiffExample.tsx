/**
 * DiffExample Component
 *
 * Example/demo component showing all diff viewer capabilities.
 * Use this as a reference for integrating diff components in your application.
 */

import React, { useState } from 'react';
import { DiffViewer, DiffStats, DiffStatsList } from './index';
import { DiffMessage, InlineDiffMessage } from '../chat/DiffMessage';
import type { DiffBlock } from '@/lib/types';
import { Button } from '@/components/ui/Button.tsx';

export const DiffExample: React.FC = () => {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  // Example diff data
  const exampleOriginal = `import React from 'react';

function Calculator() {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <h1>Calculator</h1>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}

export default Calculator;`;

  const exampleModified = `import React, { useState } from 'react';

interface CalculatorProps {
  initialValue?: number;
}

function Calculator({ initialValue = 0 }: CalculatorProps) {
  const [count, setCount] = useState(initialValue);

  const handleIncrement = () => {
    setCount(prev => prev + 1);
  };

  const handleDecrement = () => {
    setCount(prev => prev - 1);
  };

  return (
    <div className="calculator">
      <h1>Enhanced Calculator</h1>
      <p>Current Count: {count}</p>
      <div className="button-group">
        <button onClick={handleIncrement}>
          Increment
        </button>
        <button onClick={handleDecrement}>
          Decrement
        </button>
      </div>
    </div>
  );
}

export default Calculator;`;

  // Example DiffBlock data structure
  const exampleDiffBlock: DiffBlock = {
    additions: 18,
    deletions: 6,
    hunks: [
      {
        oldStart: 1,
        oldLines: 15,
        newStart: 1,
        newLines: 27,
        lines: [
          { type: 'remove', content: "import React from 'react';" },
          { type: 'add', content: "import React, { useState } from 'react';" },
          { type: 'add', content: '' },
          { type: 'add', content: 'interface CalculatorProps {' },
          { type: 'add', content: '  initialValue?: number;' },
          { type: 'add', content: '}' },
          { type: 'context', content: '' },
          { type: 'remove', content: 'function Calculator() {' },
          { type: 'add', content: 'function Calculator({ initialValue = 0 }: CalculatorProps) {' },
          { type: 'remove', content: '  const [count, setCount] = React.useState(0);' },
          { type: 'add', content: '  const [count, setCount] = useState(initialValue);' },
          { type: 'add', content: '  ' },
          { type: 'add', content: '  const handleIncrement = () => {' },
          { type: 'add', content: '    setCount(prev => prev + 1);' },
          { type: 'add', content: '  };' },
          { type: 'add', content: '  ' },
          { type: 'add', content: '  const handleDecrement = () => {' },
          { type: 'add', content: '    setCount(prev => prev - 1);' },
          { type: 'add', content: '  };' },
        ],
      },
    ],
  };

  return (
    <div className="p-8 space-y-8 bg-bg-primary min-h-screen">
      <div>
        <h1 className="text-h1 font-bold mb-2">TORQ Diff Components</h1>
        <p className="text-body text-text-secondary">
          Production-ready diff viewing components with Monaco editor integration
        </p>
      </div>

      {/* Example 1: Full DiffViewer */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">1. DiffViewer Component</h2>
        <p className="text-body text-text-secondary">
          Full-featured Monaco diff editor with side-by-side and unified views
        </p>
        <DiffViewer
          original={exampleOriginal}
          modified={exampleModified}
          language="typescript"
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          height="500px"
        />
      </section>

      {/* Example 2: DiffStats */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">2. DiffStats Component</h2>
        <p className="text-body text-text-secondary">
          Visual statistics showing additions and deletions
        </p>
        <div className="bg-bg-secondary p-4 rounded-lg border border-border">
          <DiffStats
            additions={18}
            deletions={6}
            fileName="src/components/Calculator.tsx"
            showBar={true}
          />
        </div>
      </section>

      {/* Example 3: DiffStatsList */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">3. DiffStatsList Component</h2>
        <p className="text-body text-text-secondary">
          Statistics for multiple files with totals
        </p>
        <div className="bg-bg-secondary p-4 rounded-lg border border-border">
          <DiffStatsList
            files={[
              { fileName: 'src/components/Calculator.tsx', additions: 18, deletions: 6 },
              { fileName: 'src/components/Counter.tsx', additions: 5, deletions: 2 },
              { fileName: 'src/lib/utils.ts', additions: 12, deletions: 8 },
            ]}
          />
        </div>
      </section>

      {/* Example 4: DiffMessage (collapsible) */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">4. DiffMessage Component</h2>
        <p className="text-body text-text-secondary">
          Collapsible diff viewer for chat messages
        </p>
        <DiffMessage
          diff={exampleDiffBlock}
          fileName="src/components/Calculator.tsx"
          language="typescript"
        />
      </section>

      {/* Example 5: InlineDiffMessage */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">5. InlineDiffMessage Component</h2>
        <p className="text-body text-text-secondary">
          Compact inline diff for message flows
        </p>
        <InlineDiffMessage
          diff={exampleDiffBlock}
          fileName="src/components/Calculator.tsx"
        />
      </section>

      {/* Usage Examples */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">Usage Examples</h2>
        <div className="bg-bg-secondary p-6 rounded-lg border border-border font-mono text-code space-y-4">
          <div>
            <h3 className="text-body font-semibold mb-2 text-torq-blue">Basic DiffViewer:</h3>
            <pre className="text-text-secondary overflow-x-auto">
              {`<DiffViewer
  original="const x = 1;"
  modified="const x = 2;"
  language="typescript"
  viewMode="split"
/>`}
            </pre>
          </div>

          <div>
            <h3 className="text-body font-semibold mb-2 text-torq-blue">With Message:</h3>
            <pre className="text-text-secondary overflow-x-auto">
              {`<DiffMessage
  diff={{
    additions: 42,
    deletions: 15,
    hunks: [...]
  }}
  fileName="app.tsx"
  language="typescript"
/>`}
            </pre>
          </div>

          <div>
            <h3 className="text-body font-semibold mb-2 text-torq-blue">Import:</h3>
            <pre className="text-text-secondary overflow-x-auto">
              {`import {
  DiffViewer,
  DiffStats,
  DiffMessage
} from '@/components/diff';`}
            </pre>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="space-y-4">
        <h2 className="text-h2 font-semibold">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            'Side-by-side and unified diff views',
            'Monaco editor integration',
            'TORQ color scheme (green/red)',
            'Line-by-line highlighting',
            'Navigation between changes',
            'Collapsible for chat messages',
            'Statistics with visual bars',
            'Multiple file support',
            'TypeScript type safety',
            'Responsive design',
            'Keyboard shortcuts',
            'Accessibility compliant',
          ].map((feature, index) => (
            <div key={index} className="flex items-start gap-2 text-body">
              <span className="text-torq-green">✓</span>
              <span className="text-text-secondary">{feature}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default DiffExample;
