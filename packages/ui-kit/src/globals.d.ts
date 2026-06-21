/** Ambient declarations so `tsc --noEmit` accepts side-effect CSS imports.
 *  Vite handles the actual bundling at build time. */
declare module "*.css";
