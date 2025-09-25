/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./torq_console/ui/templates/**/*.html"],
  theme: {
    extend: {
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'voice-pulse': 'voice-pulse 1.5s ease-in-out infinite',
      },
      keyframes: {
        'voice-pulse': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.7' },
          '50%': { transform: 'scale(1.1)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}