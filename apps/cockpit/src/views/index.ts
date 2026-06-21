/**
 * View registry. Keys match the icon names in `NAV_ICONS` so the nav rail and
 * the router stay in lockstep. Each view is a presentational placeholder.
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

export const VIEWS: Record<ViewId, { title: string; component: ComponentType }> = {
  ask: { title: "Ask", component: AskView },
  code: { title: "Code Buddy", component: CodeBuddyView },
  capture: { title: "Capture", component: CaptureView },
  planner: { title: "Planner", component: PlannerView },
  review: { title: "Review", component: ReviewView },
  study: { title: "Study", component: StudyView },
  notes: { title: "Notes", component: NotesView },
  vault: { title: "Vault", component: VaultView },
};
