/**
 * Feature gating for the cockpit.
 *
 * Most views are still presentational mock-ups; only `ready: true` views in
 * `views/index.ts` are wired to the kernel. To keep local testing honest we
 * filter the nav + router so non-ready views aren't reachable when the gate is
 * on (see App.tsx). This module owns *one* thing: deciding when the gate is on.
 *
 * The env flag `VITE_SYNAPSE_ONLY_READY` (apps/cockpit/.env.local) can force it:
 *   "1" → gate ON   "0" → gate OFF (show all)   unset → policy default below.
 */

/** Raw flag from the Vite build env: "1", "0", or undefined when unset. */
const FLAG = import.meta.env.VITE_SYNAPSE_ONLY_READY;

/** True under `vite` / `tauri dev`; false in a production build. */
const IS_DEV = import.meta.env.DEV;

/**
 * Whether to restrict the cockpit to kernel-wired ("ready") views only.
 *
 * Policy (yours to adjust — this is the heart of the flag):
 *   1. An explicit flag value always wins: "1" → gated, "0" → show all.
 *      (Env vars are strings, hence the string compares.)
 *   2. When the flag is unset, default to gating in dev and showing everything
 *      in a production build — so local testing surfaces only working features
 *      while a packaged build can still show the full (designed) nav.
 *
 * Want a different default? e.g. always gate until more views land:
 *   `return FLAG !== "0";`
 */
export function gateToReadyOnly(): boolean {
  if (FLAG === "1") return true;
  if (FLAG === "0") return false;
  return IS_DEV;
}
