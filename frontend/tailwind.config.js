/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Mined from the PharmaDesk UI/UX handoff so the build matches it.
        accent: { DEFAULT: '#2f6df0', dark: '#1f4fc0', soft: '#e8f0fe' },
        ink: '#101828',
        muted: '#5b6781',
        faint: '#8a94a6',
        line: '#e3e8f1',
        canvas: '#eef2f8',
        sidebar: { DEFAULT: '#141b2d', hover: '#1f2940', muted: '#7e8db0' },
        ok: '#067647',
        warn: '#b54708',
        danger: '#b42318',
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
