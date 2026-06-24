import { defineConfig } from "vite";

// The G2 app loads from http://<lan-ip>:5174 and must reach the glasses-bridge
// (:4317), which paginates a kernel ExtractResult into reveal-able study
// screens. Rather than make the WebView talk to a second origin (CORS + the
// app.json `network` permission), we proxy the bridge under /bridge so the
// app's requests are same-origin. The glasses fetch `/bridge/spec_view/study`.
//
// Port 5174 (not 5173) so this can run alongside apps/glasses-hub.
export default defineConfig({
  server: {
    host: true, // bind 0.0.0.0 so the glasses can reach the dev server over LAN
    port: 5174,
    proxy: {
      "/bridge": {
        target: process.env.GLASSES_BRIDGE_URL ?? "http://localhost:4317",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/bridge/, ""),
      },
    },
  },
});
