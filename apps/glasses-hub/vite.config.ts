import { defineConfig } from "vite";

// The G2 app loads from http://<lan-ip>:5173 and must reach the HUD relay
// (:4318). Rather than make the WebView talk to a second origin (CORS + the
// app.json `network` permission), we proxy the relay under /relay so the app's
// requests are same-origin. The glasses poll `/relay/tail?since=N`.
export default defineConfig({
  server: {
    host: true, // bind 0.0.0.0 so the glasses can reach the dev server over LAN
    proxy: {
      "/relay": {
        target: process.env.HUD_RELAY_URL ?? "http://localhost:4318",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/relay/, ""),
      },
    },
  },
});
