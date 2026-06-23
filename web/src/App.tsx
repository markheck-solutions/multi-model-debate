import { Play, RotateCcw, Share2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fetchCatalog, getFallbackEvents, startRun } from "./api";
import { AiToolsRail } from "./components/AiToolsRail";
import { LivePreview } from "./components/LivePreview";
import { PanelSeatCard } from "./components/PanelSeatCard";
import { PhaseTimeline } from "./components/PhaseTimeline";
import { fallbackCatalog } from "./demoData";
import type {
  CatalogResponse,
  DebateRunSummary,
  PanelConfig,
  PanelSeat,
  RunEvent,
  RunLane
} from "./types";
import "./styles.css";

const sampleQuestion = "Should we launch this feature next month?";

export default function App() {
  const [catalog, setCatalog] = useState<CatalogResponse>(fallbackCatalog);
  const [panel, setPanel] = useState<PanelConfig>(fallbackCatalog.default_panel);
  const [question, setQuestion] = useState(sampleQuestion);
  const [lane, setLane] = useState<RunLane>("demo");
  const [run, setRun] = useState<DebateRunSummary | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    fetchCatalog().then((nextCatalog) => {
      setCatalog(nextCatalog);
      setPanel(nextCatalog.default_panel);
    });
  }, []);

  const latestEvent = events.at(-1) ?? null;
  const enabledSeats = panel.seats.filter((seat) => seat.enabled);
  const connectedCount = catalog.accounts.filter((account) => account.status === "connected").length;

  const canStart = useMemo(() => question.trim().length >= 3 && !isRunning, [isRunning, question]);

  function updateSeat(nextSeat: PanelSeat): void {
    setPanel((currentPanel) => ({
      ...currentPanel,
      seats: currentPanel.seats.map((seat) => (seat.role === nextSeat.role ? nextSeat : seat))
    }));
  }

  async function handleStart(): Promise<void> {
    if (!canStart) {
      return;
    }

    setIsRunning(true);
    setEvents([]);

    const nextRun = await startRun({
      question,
      lane,
      panel,
      sync_report: false
    });

    setRun(nextRun);
    const nextEvents = getFallbackEvents(nextRun.id);

    for (const event of nextEvents) {
      await new Promise((resolve) => window.setTimeout(resolve, 120));
      setEvents((currentEvents) => [...currentEvents, event]);
    }

    setIsRunning(false);
  }

  function resetDemo(): void {
    setQuestion(sampleQuestion);
    setLane("demo");
    setPanel(catalog.default_panel);
    setRun(null);
    setEvents([]);
  }

  return (
    <main className="app-shell">
      <AiToolsRail accounts={catalog.accounts} />

      <section className="workbench" aria-label="Debate setup">
        <header className="topbar">
          <div>
            <p className="eyebrow">Decision cockpit</p>
            <h1>Multi-Model Debate</h1>
          </div>
          <div className="top-actions">
            <button className="ghost-button" type="button" onClick={resetDemo}>
              <RotateCcw aria-hidden="true" size={17} />
              Reset
            </button>
            <button className="ghost-button" type="button">
              <Share2 aria-hidden="true" size={17} />
              Share
            </button>
          </div>
        </header>

        <label className="question-box">
          <span>What are you trying to decide?</span>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
          />
        </label>

        <div className="lane-toggle" role="group" aria-label="Run lane">
          <button
            className={lane === "demo" ? "selected" : ""}
            type="button"
            onClick={() => setLane("demo")}
          >
            Hosted demo
          </button>
          <button
            className={lane === "local" ? "selected" : ""}
            type="button"
            onClick={() => setLane("local")}
          >
            Local real run
          </button>
        </div>

        <section className="panel-grid" aria-label="Panel seats">
          {panel.seats.map((seat) => (
            <PanelSeatCard
              key={seat.role}
              accounts={catalog.accounts}
              models={catalog.models}
              seat={seat}
              onChange={updateSeat}
            />
          ))}
        </section>

        <div className="status-strip">
          <strong>Panel Diversity: {panel.diversity_label}</strong>
          <span>
            {connectedCount} account connected, {enabledSeats.length} fresh instances
          </span>
        </div>

        <PhaseTimeline latestEvent={latestEvent} />

        <div className="launch-row">
          <p>{lane === "demo" ? "No keys needed. Safe portfolio demo." : "Uses local runner only."}</p>
          <button className="start-button" type="button" disabled={!canStart} onClick={handleStart}>
            <Play aria-hidden="true" size={20} />
            {isRunning ? "Debating..." : "Start Debate"}
          </button>
        </div>
      </section>

      <LivePreview question={question} panel={panel} latestEvent={latestEvent} run={run} />
    </main>
  );
}
