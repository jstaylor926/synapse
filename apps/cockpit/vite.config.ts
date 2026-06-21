import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react()],

  // CodeMirror breaks if more than one instance of @codemirror/state loads
  // (instanceof checks fail → "Unrecognized extension value"). `@codemirror/state`
  // and `@codemirror/view` are pinned (root package.json `overrides`) and listed as
  // direct cockpit deps so bun hoists a single copy here; `dedupe` makes Vite
  // resolve every importer to that one module.
  resolve: {
    dedupe: ["@codemirror/state", "@codemirror/view"],
  },

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
}));
