/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FAF9F6",
        card: "#FFFFFF",
        sidebar: {
          DEFAULT: "#231F1D",
          hover: "#2F2A28",
          active: "#3A3431",
          border: "#332D2A",
          text: "#E5E1DD",
          muted: "#A09891"
        },
        border: {
          DEFAULT: "#EAE6E2",
          subtle: "#F2EFEA",
          dark: "#D5CEC7"
        },
        bronze: {
          light: "#E3D4C1",
          DEFAULT: "#C5A880",
          hover: "#B6976C",
          dark: "#8C6E46"
        },
        brand: {
          dark: "#1A1817",
          charcoal: "#231F1D",
          sand: "#FAF9F6",
          gray: "#68625D"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'card': '0 2px 6px -1px rgba(0, 0, 0, 0.05), 0 1px 4px -1px rgba(0, 0, 0, 0.03)',
        'elevated': '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03)'
      }
    },
  },
  plugins: [],
}

