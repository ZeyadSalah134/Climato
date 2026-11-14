/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        earth: {
          950: '#06130d',
          900: '#0a1d14',
          850: '#0e261b',
          800: '#123123',
          700: '#1a4733',
          600: '#226045',
          500: '#10b981', // emerald
          400: '#34d399',
          300: '#6ee7b7',
          200: '#a7f3d0',
          100: '#d1fae5',
        },
        navy: {
          950: '#070b14',
          900: '#0c1322',
          850: '#111b30',
          800: '#182542',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
