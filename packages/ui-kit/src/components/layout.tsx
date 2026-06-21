/**
 * Neo-Gonzo Noir — layout & chrome.
 *
 * The window frame the whole cockpit lives in: AppShell (the bezel + grain),
 * TitleBar (traffic lights, brand, search, status), and the NavRail with its
 * NavItems. Composition is left to the surface — see apps/cockpit.
 */
import type { HTMLAttributes, ReactNode } from "react";
import { Icon, type IconName } from "../icons";
import type { AccentId } from "../theme/accents";
import { GrainOverlay } from "./effects";

function cx(...parts: (string | false | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

/* ---------------------------------- AppShell ---------------------------------- */

export interface AppShellProps {
  /** Spans the top of the window (typically <TitleBar />). */
  titleBar?: ReactNode;
  /** The left navigation column (typically <NavRail />). */
  sidebar?: ReactNode;
  /** The active view. */
  children?: ReactNode;
  /** Re-tint the whole surface. */
  accent?: AccentId;
  /** Fill the viewport with no outer bezel (desktop-maximized look). */
  fluid?: boolean;
  /** Render the film-grain overlay. */
  grain?: boolean;
}

export function AppShell({
  titleBar,
  sidebar,
  children,
  accent,
  fluid = false,
  grain = true,
}: AppShellProps) {
  return (
    <div className={cx("syn-shell", fluid && "syn-shell--fluid")} data-accent={accent}>
      <div className="syn-shell__window">
        {grain && <GrainOverlay />}
        {titleBar}
        <div className="syn-shell__body">
          {sidebar}
          <main className="syn-shell__main">{children}</main>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------- SearchField -------------------------------- */

export function SearchField({
  placeholder = "Ask or search the vault…",
  hint = "⌘K · kb_search",
}: {
  placeholder?: string;
  hint?: ReactNode;
}) {
  return (
    <div className="syn-search">
      <Icon name="search" size={14} strokeWidth={1.6} />
      <span className="syn-search__placeholder">{placeholder}</span>
      <span style={{ flex: 1 }} />
      <span className="syn-search__kbd">{hint}</span>
    </div>
  );
}

/* ---------------------------------- TitleBar ---------------------------------- */

export interface TitleBarProps {
  brand?: string;
  /** The dimmed mono subtitle after the brand. */
  subtitle?: ReactNode;
  /** Centered slot — usually <SearchField />. */
  center?: ReactNode;
  /** Right-aligned status chips. */
  status?: ReactNode;
}

export function TitleBar({
  brand = "SYNAPSE",
  subtitle = "kernel · synapse-engine · MCP@localhost",
  center,
  status,
}: TitleBarProps) {
  return (
    <div className="syn-titlebar">
      <div className="syn-titlebar__lights">
        <span className="syn-titlebar__light" style={{ background: "var(--syn-light-red)" }} />
        <span className="syn-titlebar__light" style={{ background: "var(--syn-light-yellow)" }} />
        <span className="syn-titlebar__light" style={{ background: "var(--syn-light-green)" }} />
      </div>
      <div className="syn-titlebar__brand">
        <span className="syn-titlebar__brand-dot" />
        <span className="syn-titlebar__brand-name">{brand}</span>
        {subtitle && <span className="syn-titlebar__brand-sub">{subtitle}</span>}
      </div>
      <div className="syn-titlebar__center">{center}</div>
      <div className="syn-titlebar__status">{status}</div>
    </div>
  );
}

/* ----------------------------------- NavRail ---------------------------------- */

export interface NavRailProps extends HTMLAttributes<HTMLDivElement> {
  heading?: string;
  /** Pinned to the bottom of the rail (e.g. the degradation ladder). */
  footer?: ReactNode;
}

export function NavRail({ heading = "WORKSPACE", footer, children, className, ...props }: NavRailProps) {
  return (
    <nav className={cx("syn-rail", className)} {...props}>
      <div className="syn-rail__heading">{heading}</div>
      {children}
      <div className="syn-rail__spacer" />
      {footer && <div className="syn-rail__footer">{footer}</div>}
    </nav>
  );
}

/* ----------------------------------- NavItem ---------------------------------- */

export interface NavItemProps {
  icon: IconName;
  label: ReactNode;
  /** The dimmed mono tool tag on the right (e.g. "reason_*"). */
  tag?: ReactNode;
  active?: boolean;
  onClick?: () => void;
}

export function NavItem({ icon, label, tag, active = false, onClick }: NavItemProps) {
  return (
    <button className="syn-navitem" aria-current={active ? "page" : undefined} onClick={onClick}>
      {active && <span className="syn-navitem__active" />}
      <span className="syn-navitem__icon">
        <Icon name={icon} size={18} />
      </span>
      <span className="syn-navitem__label">{label}</span>
      {tag && <span className="syn-navitem__tag">{tag}</span>}
    </button>
  );
}
