/** @type {import('tailwindcss').Config} */
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
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
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-invert-body': '#ededed',
            '--tw-prose-invert-headings': '#ffffff',
            '--tw-prose-invert-links': '#8b5cf6',
            '--tw-prose-invert-code': '#ededed',
            '--tw-prose-invert-pre-bg': '#111111',
            '--tw-prose-invert-hr': '#262626',
            '--tw-prose-invert-bullets': '#a1a1aa',
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
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
