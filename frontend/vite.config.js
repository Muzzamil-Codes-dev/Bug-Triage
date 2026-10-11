import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development (`npm run dev`) API calls are proxied to the FastAPI
// server. In production FastAPI serves the built files from dist/ itself.
const API_URL = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/bug-triage": API_URL,
      "/bug-review": API_URL,
    },
  },
});
