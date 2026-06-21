# @synapse/ui-kit — Neo-Gonzo Noir

The Synapse design system: a dark "noir terminal" cockpit aesthetic, shipped as
React components and CSS design tokens. Consumed by the Tauri cockpit and any
other React surface.

> **Status:** initial implementation. Components are **presentational
> placeholders** — they render the design language with stand-in copy/data.
> Wiring to the MCP boundary lands in a later milestone.

## Usage

```tsx
import { AppShell, TitleBar, NavRail, NavItem, Button } from "@synapse/ui-kit";
```

Importing anything from the barrel also loads the stylesheets
(`tokens.css` → `base.css` → `components.css`), so there is nothing else to
wire up.

## The language

- **Surfaces** — deep navy-black (`--syn-bg-abyss` … `--syn-surface`).
- **Accent** — themeable. Default *Toxic Blue* `#2bc0ff`; set
  `data-accent="harsh-green | saturated-crimson | velvet-purple"` on the
  `AppShell` (or `<html>`) to re-tint everything. See `theme/accents.ts`.
- **Type** — `Archivo` (UI), `JetBrains Mono` (labels/code/tags),
  `Special Elite` (brand + stamps + newsprint headings).
- **Flourishes** — film grain (`GrainOverlay`), accent bloom (`GlowAccent`),
  hard offset shadows under primary buttons, rotated rubber-stamps (`Stamp`),
  and warm newsprint surfaces (`NewsprintCard`).

All visuals are driven by CSS custom properties in
[`src/styles/tokens.css`](src/styles/tokens.css) — edit there to re-skin.

## What's in the box

| Group | Components |
| --- | --- |
| Layout / chrome | `AppShell`, `TitleBar`, `SearchField`, `NavRail`, `NavItem` |
| Primitives | `Button`, `Badge`, `Tag`, `Card`, `Kbd`, `Stamp`, `ProgressBar`, `SegmentedControl`, `Stepper`, `Eyebrow`, `PageHeader`, `Divider`, `StatTile` |
| Content blocks | `ChatBubble`, `CitationCard`, `CodeBlock`, `Flashcard`, `RatingButtons`, `NewsprintCard`, `SaveToKbButton` |
| Effects | `GrainOverlay`, `GlowAccent` |
| Icons | `Icon` (+ `NAV_ICONS`) |

The cockpit composes these into one view per kernel capability — see
[`apps/cockpit/src/views`](../../apps/cockpit/src/views).

## Source of the design

The system was reverse-engineered from the design file at
`Neo-Gonzo Noir design system/Synapse Cockpit.dc.html` (and the `screens/`
mock-ups). When extending the system, match those references.

## Notes / TODO

- Fonts are loaded from Google Fonts via `@import` in `base.css`. Before going
  fully offline (the platform is local-first), self-host the three families.
