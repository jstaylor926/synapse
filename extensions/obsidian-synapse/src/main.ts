/**
 * Synapse Obsidian plugin.
 *
 * The vault is the source of truth, so this plugin runs *inside* Obsidian and
 * talks to the kernel's REST edge to surface the planner and due spaced-repetition
 * cards without leaving the editor. It deliberately never writes to the vault
 * directly while the kernel is running — those writes go through the kernel's
 * Vault Gatekeeper to avoid clobbering.
 */

import { Notice, Plugin } from "obsidian";
import type { ReviewCard } from "@synapse/contracts-ts";

const KERNEL_API = "http://127.0.0.1:8765";

export default class SynapsePlugin extends Plugin {
  override async onload(): Promise<void> {
    this.addCommand({
      id: "synapse-review-due",
      name: "Synapse: Review due cards",
      callback: async () => {
        try {
          const res = await fetch(`${KERNEL_API}/study/due`);
          const cards = (await res.json()) as ReviewCard[];
          new Notice(`Synapse: ${cards.length} card(s) due for review.`);
        } catch {
          new Notice("Synapse: kernel not reachable. Is `bun run dev` running?");
        }
      },
    });
  }
}
