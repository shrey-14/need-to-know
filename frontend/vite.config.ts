import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // /api/* is proxied and rewritten to FastAPI's actual routes (/login, /chat,
    // no prefix). This namespace is required, not cosmetic: the frontend's own
    // page routes are also named /login and /chat, so proxying those exact
    // paths directly would intercept browser navigation to the pages themselves.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
