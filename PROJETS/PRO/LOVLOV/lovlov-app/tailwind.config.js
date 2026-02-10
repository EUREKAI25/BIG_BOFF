/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // LovLov Red Theme - from logo colors
        love: {
          primary: '#b61600',  // Background red
          dark: '#700b06',     // Dark red
          light: '#d46f66',    // Light coral
        },
        cream: {
          DEFAULT: '#F5E6D3',
          50: '#FFFEF7',
          100: '#FFF8E7',
          200: '#F5E6D3',
          300: '#E8D4BC',
        },
      },
      fontFamily: {
        romantic: ['Pacifico', 'cursive'],
        display: ['Bebas Neue', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'love-gradient': 'linear-gradient(135deg, #b61600 0%, #700b06 100%)',
        'love-radial': 'radial-gradient(ellipse at center, #b61600 0%, #700b06 70%)',
      },
      animation: {
        'pulse-heart': 'pulse-heart 1.5s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-heart': {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.1)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
};
