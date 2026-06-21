/**
 * View registry. Keys match the icon names in `NAV_ICONS` so the nav rail and
 * the router stay in lockstep.
 *
 * `ready` is the single source of truth for "this view is wired to the kernel
 * for real" (vs. a presentational mock). The feature gate in `../featureFlags`
 * reads it to decide what's selectable during local testing. Flip a view to
 * `ready: true` the moment its kernel capability + REST route + client method
 * land — see IMPLEMENTATION_STATUS.md.
 */
import type { ComponentType } from "react";
import { AskView } from "./AskView";
import { CodeBuddyView } from "./CodeBuddyView";
import { CaptureView } from "./CaptureView";
import { PlannerView } from "./PlannerView";
import { ReviewView } from "./ReviewView";
import { StudyView } from "./StudyView";
import { NotesView } from "./NotesView";
import { VaultView } from "./VaultView";

export type ViewId =
  | "ask"
  | "code"
  | "capture"
  | "planner"
  | "review"
  | "study"
  | "notes"
  | "vault";

export interface ViewMeta {
  title: string;
  component: ComponentType;
  /** True once the view is backed by a real kernel capability (not mock data). */
  ready: boolean;
}

export const VIEWS: Record<ViewId, ViewMeta> = {
  ask: { title: "Ask", component: AskView, ready: true },
  code: { title: "Code Buddy", component: CodeBuddyView, ready: true },
  capture: { title: "Capture", component: CaptureView, ready: false },
  planner: { title: "Planner", component: PlannerView, ready: false },
  review: { title: "Review", component: ReviewView, ready: false },
  study: { title: "Study", component: StudyView, ready: false },
  notes: { title: "Notes", component: NotesView, ready: false },
  vault: { title: "Vault", component: VaultView, ready: false },
};
