/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        s: {
          bg: "#f4f5f7",
          panel: "#ffffff",
          "panel-alt": "#fafbfc",
          surface: "#ebedf0",
          border: "#d1d5db",
          "border-light": "#e5e7eb",
          accent: "#2c5282",
          "accent-light": "#ebf0f7",
          danger: "#9b2c2c",
          "danger-light": "#fef2f2",
          warn: "#92400e",
          "warn-light": "#fffbeb",
          safe: "#276749",
          "safe-light": "#f0fdf4",
          purple: "#553c9a",
          cyan: "#1a6e7e",
          muted: "#6b7280",
          text: "#1e293b",
          "text-secondary": "#4b5563",
          "text-tertiary": "#9ca3af",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
