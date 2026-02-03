import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        ink: "#0e1116",
        mist: "#e7eefc",
        flare: "#ff784f",
        splash: "#5b7cfa",
        moss: "#2fd68a",
        dusk: "#0f172a",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(91,124,250,0.3), 0 10px 40px rgba(15,23,42,0.25)",
      },
      backgroundImage: {
        hero: "radial-gradient(1200px 600px at 10% -10%, rgba(91,124,250,0.35), transparent 55%), radial-gradient(800px 500px at 90% 10%, rgba(255,120,79,0.25), transparent 60%), linear-gradient(180deg, #0b1020 0%, #0e1116 60%, #0b0f1a 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
