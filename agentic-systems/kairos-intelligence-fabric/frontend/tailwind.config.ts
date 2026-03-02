import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0a1a',
        surface: '#12122a',
        glass: 'rgba(255,255,255,0.05)',
        primary: '#6366f1',
        secondary: '#06b6d4',
        accent: '#f59e0b',
        success: '#22c55e',
        warning: '#f97316',
        danger: '#ef4444',
        knowledge: '#fbbf24',
        node: {
          equipment: '#3b82f6',
          orders: '#f59e0b',
          products: '#22c55e',
          quality: '#ef4444',
          people: '#a855f7',
          suppliers: '#06b6d4',
          production: '#f97316',
          insights: '#fbbf24',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        panel: '12px',
        button: '8px',
      },
      backdropBlur: {
        glass: '20px',
      },
    },
  },
  plugins: [],
} satisfies Config
