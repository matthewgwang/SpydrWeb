/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sentinel: {
          bg: "#0a0e1a",
          panel: "#111827",
          border: "#1f2937",
          accent: "#3b82f6",
          danger: "#ef4444",
          warn: "#f59e0b",
          safe: "#22c55e",
        },
      },
    },
  },
  plugins: [],
};
