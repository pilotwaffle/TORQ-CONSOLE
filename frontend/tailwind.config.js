/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // TORQ Brand Colors
        'torq-green': '#10b981',
        'torq-blue': '#0078d4',
        'torq-red': '#ef4444',
        'torq-orange': '#f59e0b',
        'torq-dark': '#1e1e1e',
        'torq-accent': '#0086f0',

        // Base colors (dark theme)
        'bg-primary': '#1e1e1e',
        'bg-secondary': '#252526',
        'bg-tertiary': '#2d2d30',

        // Agent colors (mapped to TORQ colors)
        'agent-active': '#0078d4',     // torq-blue
        'agent-thinking': '#f59e0b',   // torq-orange
        'agent-success': '#10b981',    // torq-green
        'agent-error': '#ef4444',      // torq-red

        // Text
        'text-primary': '#ffffff',
        'text-secondary': '#cccccc',
        'text-muted': '#808080',

        // Accent (mapped to TORQ colors)
        'accent-primary': '#0078d4',   // torq-blue
        'accent-hover': '#0086f0',     // torq-accent

        // Borders
        border: '#3e3e42',
        'border-focus': '#0078d4',     // torq-blue

        // Diff colors
        'diff-added': 'rgba(16, 185, 129, 0.15)',     // torq-green with opacity
        'diff-removed': 'rgba(239, 68, 68, 0.15)',    // torq-red with opacity
        'diff-modified': 'rgba(245, 158, 11, 0.15)',  // torq-orange with opacity
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Source Code Pro', 'monospace'],
      },
      fontSize: {
        'h1': '2rem',      // 32px
        'h2': '1.5rem',    // 24px
        'h3': '1.25rem',   // 20px
        'body': '0.875rem',// 14px
        'small': '0.75rem',// 12px
        'code': '0.875rem',// 14px
      },
      borderRadius: {
        'sm': '0.25rem',   // 4px
        'md': '0.5rem',    // 8px
        'lg': '0.75rem',   // 12px
      },
      animation: {
        'slide-in': 'slideIn 0.2s ease-out',
        'fade-in': 'fadeIn 0.15s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [],
}
