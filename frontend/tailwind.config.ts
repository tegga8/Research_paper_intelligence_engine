import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#07111f',
        panel: 'rgba(15, 23, 42, 0.72)',
        accent: '#7c3aed'
      },
      boxShadow: {
        glow: '0 0 60px rgba(124, 58, 237, 0.28)'
      }
    }
  },
  plugins: []
};

export default config;
