import { useMemo, useState } from "react";
import {
  AppShell,
  TitleBar,
  SearchField,
  NavRail,
  NavItem,
  Badge,
  NAV_ICONS,
  type AccentId,
} from "@synapse/ui-kit";
import { DegradationLadder } from "./components/DegradationLadder";
import { gateToReadyOnly } from "./featureFlags";
import { VIEWS, type ViewId } from "./views";
import "./App.css";

function App() {
  // Nav rail mirrors NAV_ICONS, but when the gate is on we drop any view that
  // isn't kernel-wired so only working features are reachable in local testing.
  const navItems = useMemo(() => {
    const gated = gateToReadyOnly();
    return NAV_ICONS.filter((item) => !gated || VIEWS[item.name as ViewId].ready);
  }, []);

  // Default to the first *available* view so we never land on a hidden one.
  const [view, setView] = useState<ViewId>((navItems[0]?.name as ViewId) ?? "ask");
  // Accent is wired to state now so the picker (a later milestone) is a one-liner.
  const [accent] = useState<AccentId>("toxic-blue");

  const ActiveView = VIEWS[view].component;

  return (
    <AppShell
      accent={accent}
      titleBar={
        <TitleBar
          center={<SearchField />}
          status={
            <>
              <Badge tone="accent" pulse>
                1 JOB · Docling 62%
              </Badge>
              <Badge tone="success">GENERATIVE</Badge>
              <Badge tone="purple">GATEKEEPER</Badge>
            </>
          }
        />
      }
      sidebar={
        <NavRail footer={<DegradationLadder />}>
          {navItems.map((item) => (
            <NavItem
              key={item.name}
              icon={item.name}
              label={item.label}
              tag={item.tag}
              active={view === (item.name as ViewId)}
              onClick={() => setView(item.name as ViewId)}
            />
          ))}
        </NavRail>
      }
    >
      <ActiveView />
    </AppShell>
  );
}

export default App;
