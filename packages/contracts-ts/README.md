# @synapse/contracts-ts

TypeScript mirror of the kernel's Pydantic contracts (`kernel/contracts/models.py`).
Import shared types from here so every surface stays in lockstep with the backend:

```ts
import type { SearchHit, Job } from "@synapse/contracts-ts";
```

## Keeping in sync

These are hand-mirrored today. When `kernel/contracts/models.py` changes, update
`src/index.ts` to match. To automate later, generate JSON Schema from the Pydantic
models (`Model.model_json_schema()`) and run a schema→TS codegen step into this file.
