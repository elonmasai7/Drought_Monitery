/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9f0',
          100: '#dcf2dc',
          200: '#bae5ba',
          300: '#89d389',
          400: '#5abc5a',
          500: '#37a837',
          600: '#2d8a2d',
          700: '#276f27',
          800: '#245824',
          900: '#1f4a1f',
        },
        secondary: {
          50: '#f0f8f4',
          100: '#dbeee5',
          200: '#b9ddce',
          300: '#8cc5b0',
          500: '#4a7c59',
          600: '#3e6b4a',
          700: '#34573d',
          800: '#2c4633',
          900: '#263a2b',
        }
      }
    },
  },
  plugins: [],
}