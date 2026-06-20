//! Synapse Zed extension.
//!
//! Bridges the Zed editor to the Synapse kernel so the code assistant has
//! context from the ingested knowledge base. Zed extensions compile to WASM
//! against `zed_extension_api`; this is the minimal registration skeleton.

use zed_extension_api as zed;

struct SynapseExtension;

impl zed::Extension for SynapseExtension {
    fn new() -> Self {
        SynapseExtension
    }
}

zed::register_extension!(SynapseExtension);
