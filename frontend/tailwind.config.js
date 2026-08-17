/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        void: '#0B0E14',
        surface: '#131824',
        surface2: '#1A2130',
        emerald: {
          DEFAULT: '#2FD675',
          dim: 'rgba(47,214,117,0.15)',
        },
        glowstone: {
          DEFAULT: '#F5B942',
          dim: 'rgba(245,185,66,0.15)',
        },
        redstone: {
          DEFAULT: '#E5484D',
          dim: 'rgba(229,72,77,0.15)',
        },
        lapis: {
          DEFAULT: '#4C7FE0',
          dim: 'rgba(76,127,224,0.15)',
        },
        ink: {
          DEFAULT: '#E8EDF2',
          muted: '#8B96A8',
          dim: '#5B6577',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
}
