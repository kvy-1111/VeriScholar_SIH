/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0F2A5F",
        sky: "#DDEBFF"
      }
    },
  },
  plugins: [],
};
