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
        chai: {
          50: '#fff9f2',
          100: '#fef1e3',
          200: '#fbdcc3',
          300: '#f7be96',
          400: '#f19460',
          500: '#ea6d35',
          600: '#db4f22',
          700: '#b6391a',
          800: '#912e1c',
          900: '#75281a',
          950: '#3f110a',
        },
        masala: {
          850: '#191b22',
          900: '#12141a',
          950: '#0a0b0e',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Cabinet Grotesk', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
