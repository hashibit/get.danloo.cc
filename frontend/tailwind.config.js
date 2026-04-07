/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./src/pages/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 8-bit CRT palette — semantic tokens
        pixel: {
          bg:           '#0D0D1A',
          surface:      '#111122',
          raised:       '#1A1A30',
          border:       '#2A2A44',
          'border-mid': '#3A3A55',
          green:        '#00FF41',
          'green-dark': '#007A1A',
          yellow:       '#FFD700',
          'yellow-dark':'#886600',
          cyan:         '#00FFFF',
          'cyan-dark':  '#006688',
          red:          '#FF3333',
          'red-dark':   '#880000',
          blue:         '#4488FF',
          orange:       '#FF8C00',
          purple:       '#9933FF',
          white:        '#E0E0E0',
          gray:         '#666677',
        },
        // Semantic shorthands
        success:  '#00FF41',
        warning:  '#FFD700',
        danger:   '#FF3333',

        // Remap Tailwind's gray to dark theme equivalents
        gray: {
          50:  '#1A1A2E',
          100: '#222233',
          200: '#2A2A44',
          300: '#3A3A55',
          400: '#555566',
          500: '#666677',
          600: '#888899',
          700: '#AAAAAA',
          800: '#CCCCCC',
          900: '#E0E0E0',
          950: '#F0F0F0',
        },
        // Remap blue → pixel cyan
        blue: {
          50:  '#001133',
          100: '#001A44',
          200: '#002266',
          500: '#4488FF',
          600: '#3377EE',
          700: '#2266DD',
        },
        // Remap red to dark-theme red
        red: {
          50:  '#1A0008',
          100: '#2A0010',
          500: '#FF3333',
          600: '#CC2222',
          700: '#AA1111',
        },
      },

      fontFamily: {
        // Primary: Noto Sans SC (CJK-safe, clean, bold for 8-bit feel)
        sans:  ['"Noto Sans SC"', 'sans-serif'],
        // Pixel: Press Start 2P for ASCII-only decorative elements
        pixel: ['"Press Start 2P"', 'monospace'],
        mono:  ['"Courier New"', 'Courier', 'monospace'],
      },

      fontSize: {
        'xs':   ['11px', { lineHeight: '1.5' }],
        'sm':   ['12px', { lineHeight: '1.6' }],
        'base': ['14px', { lineHeight: '1.75' }],
        'lg':   ['16px', { lineHeight: '1.6' }],
        'xl':   ['18px', { lineHeight: '1.5' }],
        '2xl':  ['22px', { lineHeight: '1.4' }],
        '3xl':  ['28px', { lineHeight: '1.3' }],
        '4xl':  ['36px', { lineHeight: '1.2' }],
        '5xl':  ['48px', { lineHeight: '1.1' }],
      },

      boxShadow: {
        // Pixel hard shadows — no blur
        'pixel':        '4px 4px 0px #000000',
        'pixel-green':  '4px 4px 0px #007A1A',
        'pixel-yellow': '4px 4px 0px #886600',
        'pixel-cyan':   '4px 4px 0px #006688',
        'pixel-red':    '4px 4px 0px #880000',
        'pixel-sm':     '2px 2px 0px #000000',
        'pixel-lg':     '6px 6px 0px #007A1A',
        'pixel-inset':  'inset 2px 2px 0px rgba(0,0,0,0.8)',
        // Map old names used in code
        'card':         '4px 4px 0px #000000',
        'card-lg':      '6px 6px 0px #007A1A',
        'dropdown':     '4px 4px 0px #000000',
        'floating':     '8px 8px 0px #000000',
        'inner-glow':   'inset 0 0 8px rgba(0,255,65,0.15)',
      },

      borderRadius: {
        // All zero — pixel perfect
        'none':   '0px',
        'sm':     '0px',
        DEFAULT:  '0px',
        'md':     '0px',
        'lg':     '0px',
        'xl':     '0px',
        '2xl':    '0px',
        '3xl':    '0px',
        'full':   '0px',
        'card':   '0px',
        'button': '0px',
        'input':  '0px',
        'modal':  '0px',
      },

      animation: {
        'blink':       'blink 1s step-end infinite',
        'blink-slow':  'blink 2s step-end infinite',
        'pixel-pulse': 'pixel-pulse 2s step-end infinite',
        'glitch':      'glitch 4s step-end infinite',
      },

      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':       { opacity: '0' },
        },
        'pixel-pulse': {
          '0%, 100%': { boxShadow: '4px 4px 0px #007A1A' },
          '50%':       { boxShadow: '4px 4px 0px #886600' },
        },
        glitch: {
          '0%, 88%, 100%': { transform: 'translate(0)' },
          '90%': { transform: 'translate(-2px, 1px)' },
          '92%': { transform: 'translate(2px, -1px)' },
          '94%': { transform: 'translate(-1px, 2px)' },
        },
      },
    },
  },
  plugins: [],
}
