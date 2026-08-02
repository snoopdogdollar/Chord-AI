import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./features/**/*.{ts,tsx}", "./services/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        paper: "#f7f5ef",
        staff: "#d7cdc0",
        accent: "#2f7f73",
        warning: "#b86b1d"
      }
    }
  },
  plugins: []
};

export default config;
