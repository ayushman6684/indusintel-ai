import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0B0F11",
          900: "#0F1417",
          800: "#161D21",
          700: "#1E262B",
          600: "#2A343A",
          border: "#26313700",
        },
        line: "#232D33",
        ink: {
          DEFAULT: "#E7EBEC",
          muted: "#93A1A6",
          faint: "#5D6B70",
        },
        amber: {
          DEFAULT: "#F2A93B",
          soft: "#F2A93B1A",
        },
        steel: {
          DEFAULT: "#4C90AC",
          soft: "#4C90AC1A",
        },
        status: {
          pass: "#4FAE7E",
          passBg: "#4FAE7E1A",
          warn: "#F2A93B",
          warnBg: "#F2A93B1A",
          fail: "#E2604F",
          failBg: "#E2604F1A",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        sm: "3px",
        DEFAULT: "6px",
        lg: "10px",
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(#1B2327 1px, transparent 1px), linear-gradient(90deg, #1B2327 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
export default config;
