import { useState } from "react";
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
import { VIEWS, type ViewId } from "./views";
import "./App.css";

function App() {
  const [view, setView] = useState<ViewId>("planner");
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
          {NAV_ICONS.map((item) => (
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
