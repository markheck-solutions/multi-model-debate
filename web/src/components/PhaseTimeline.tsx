import { FileCheck2, Gavel, Hammer, MessageSquareWarning, Swords } from "lucide-react";
import type { RunEvent, RunPhase } from "../types";

const phases: Array<{ id: RunPhase; label: string; icon: typeof Hammer }> = [
  { id: "build", label: "Build", icon: Hammer },
  { id: "critique", label: "Critique", icon: MessageSquareWarning },
  { id: "debate", label: "Debate", icon: Swords },
  { id: "judge", label: "Judge", icon: Gavel },
  { id: "final", label: "Final", icon: FileCheck2 }
];

interface PhaseTimelineProps {
  latestEvent: RunEvent | null;
}

export function PhaseTimeline({ latestEvent }: PhaseTimelineProps) {
  const activeIndex = latestEvent
    ? phases.findIndex((phase) => phase.id === latestEvent.phase)
    : -1;

  return (
    <section className="timeline" aria-label="Debate progress">
      {phases.map((phase, index) => {
        const Icon = phase.icon;
        const state = index <= activeIndex ? "phase-active" : "";

        return (
          <div className={`phase ${state}`} key={phase.id}>
            <span aria-hidden="true">
              <Icon size={18} />
            </span>
            <strong>{phase.label}</strong>
          </div>
        );
      })}
    </section>
  );
}
