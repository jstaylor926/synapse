# zed-synapse

The Synapse Zed extension. Zed extensions are Rust crates compiled to WASM, so
this directory is **not** a Bun workspace (it has no `package.json`).

## Develop

Install it as a dev extension from Zed: `zed: install dev extension` and point it
at this directory. Zed builds the crate against `zed_extension_api` automatically.
