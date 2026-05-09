import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        p0: "#dc2626",
        p1: "#ea580c",
        p2: "#2563eb",
        p3: "#16a34a",
      },
    },
  },
  plugins: [],
};
export default config;
