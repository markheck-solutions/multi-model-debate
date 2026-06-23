import { ClipboardList, FileText, PanelTop, RadioTower } from "lucide-react";
import type { DebateRunSummary, PanelConfig, RunEvent } from "../types";

interface LivePreviewProps {
  question: string;
  panel: PanelConfig;
  latestEvent: RunEvent | null;
  run: DebateRunSummary | null;
}

export function LivePreview({ question, panel, latestEvent, run }: LivePreviewProps) {
  const enabledSeats = panel.seats.filter((seat) => seat.enabled);

  return (
    <aside className="preview" aria-label="Live preview">
      <div className="preview-title">
        <RadioTower aria-hidden="true" size={20} />
        <h2>Live Preview</h2>
      </div>

      <section className="preview-section">
        <h3>
          <ClipboardList aria-hidden="true" size={16} />
          Question
        </h3>
        <p>{question || "Should we launch this feature next month?"}</p>
      </section>

      <section className="preview-section">
        <h3>
          <PanelTop aria-hidden="true" size={16} />
          Panel
        </h3>
        <p>
          {enabledSeats.length} fresh instances. Diversity: {panel.diversity_label}.
        </p>
      </section>

      <section className="preview-section">
        <h3>
          <FileText aria-hidden="true" size={16} />
          Expected Output
        </h3>
        <p>Decision, blockers, risks, owner questions, and next actions.</p>
      </section>

      {latestEvent && (
        <section className="event-strip">
          <strong>{latestEvent.title}</strong>
          <p>{latestEvent.detail}</p>
          <div className="progress-meter" aria-label={`${latestEvent.progress}% complete`}>
            <span style={{ width: `${latestEvent.progress}%` }} />
          </div>
        </section>
      )}

      {run?.final_report && (
        <section className="report-preview">
          <h3>Final report</h3>
          <p>{run.final_report.replaceAll("#", "").slice(0, 260)}...</p>
        </section>
      )}
    </aside>
  );
}
