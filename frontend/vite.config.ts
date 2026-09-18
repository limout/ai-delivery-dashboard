import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/metrics": {
        target: "http://127.0.0.1:8000",
        bypass(req) {
          const accept = req.headers.accept ?? "";
          if (accept.includes("text/html")) {
            return "/index.html";
          }
          return undefined;
        },
      },
      "/sources": "http://127.0.0.1:8000",
      "/projects": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/static": "http://127.0.0.1:8000",
    },
  },
});
