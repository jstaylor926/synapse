/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * Gate the cockpit to kernel-wired ("ready") views only.
   * "1" forces the gate ON, "0" forces it OFF. Unset → policy default
   * (see src/featureFlags.ts). Set it in apps/cockpit/.env.local.
   */
  readonly VITE_SYNAPSE_ONLY_READY?: "0" | "1";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
