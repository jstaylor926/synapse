/**
 * @synapse/ui-kit — Neo-Gonzo Noir design system
 * ----------------------------------------------------------------------------
 * Shared React components and design-system primitives consumed by the cockpit
 * and other React surfaces. Importing anything from this barrel also loads the
 * design tokens + base styles, so a surface just needs:
 *
 *   import { AppShell, TitleBar, Button } from "@synapse/ui-kit";
 *
 * Everything here is presentational — wiring to the MCP boundary comes later.
 */

// Styles (tokens → base → components). Order matters: tokens define the
// variables the others consume.
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/components.css";

// Theme
export { ACCENTS, DEFAULT_ACCENT } from "./theme/accents";
export type { Accent, AccentId } from "./theme/accents";

// Icons
export { Icon, NAV_ICONS } from "./icons";
export type { IconName } from "./icons";

// Primitives
export {
  Button,
  Badge,
  Tag,
  Card,
  Kbd,
  Stamp,
  ProgressBar,
  SegmentedControl,
  Stepper,
  Eyebrow,
  PageHeader,
  Divider,
  StatTile,
} from "./components/primitives";
export type {
  ButtonProps,
  BadgeProps,
  TagProps,
  CardProps,
  StampProps,
  ProgressBarProps,
  SegmentedControlProps,
  StepperProps,
  PageHeaderProps,
  StatTileProps,
} from "./components/primitives";

// Effects
export { GrainOverlay, GlowAccent } from "./components/effects";

// Layout & chrome
export { AppShell, TitleBar, SearchField, NavRail, NavItem } from "./components/layout";
export type {
  AppShellProps,
  TitleBarProps,
  NavRailProps,
  NavItemProps,
} from "./components/layout";

// Content blocks
export {
  ChatBubble,
  CitationCard,
  CodeBlock,
  Flashcard,
  RatingButtons,
  NewsprintCard,
  SaveToKbButton,
} from "./components/content";
export type {
  ChatBubbleProps,
  CitationCardProps,
  CodeBlockProps,
  FlashcardProps,
  RatingButtonsProps,
  FsrsRating,
  NewsprintCardProps,
} from "./components/content";
