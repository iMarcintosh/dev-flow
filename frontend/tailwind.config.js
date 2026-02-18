/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        foreground: '#ededed',
        card: '#111111',
        'card-hover': '#1a1a1a',
        border: '#262626',
        primary: {
          DEFAULT: '#8b5cf6',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#3b82f6',
          foreground: '#ffffff',
        },
        muted: {
          DEFAULT: '#262626',
          foreground: '#a1a1aa',
        },
        accent: {
          DEFAULT: '#1a1a1a',
          foreground: '#ededed',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.scrollbar-thin::-webkit-scrollbar': {
          width: '6px',
          height: '6px',
        },
        '.scrollbar-thin::-webkit-scrollbar-track': {
          backgroundColor: 'transparent',
        },
        '.scrollbar-thin::-webkit-scrollbar-thumb': {
          backgroundColor: '#374151',
          borderRadius: '3px',
        },
        '.scrollbar-thin::-webkit-scrollbar-thumb:hover': {
          backgroundColor: '#4b5563',
        },
      })
    }
  ],
}
