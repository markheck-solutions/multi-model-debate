import { BrainCircuit, ChevronDown, ToggleLeft, ToggleRight } from "lucide-react";
import type { ModelOption, PanelSeat, ProviderAccount, ReasoningEffort } from "../types";

interface PanelSeatCardProps {
  seat: PanelSeat;
  accounts: ProviderAccount[];
  models: ModelOption[];
  onChange: (seat: PanelSeat) => void;
}

export function PanelSeatCard({ seat, accounts, models, onChange }: PanelSeatCardProps) {
  const selectedModel = models.find((model) => model.id === seat.model_id) ?? models[0];
  const availableModels = models.filter((model) => model.account_id === seat.account_id);
  const reasoningOptions = selectedModel?.reasoning_efforts ?? ["medium"];

  function updateSeat(patch: Partial<PanelSeat>): void {
    onChange({ ...seat, ...patch });
  }

  function updateModel(modelId: string): void {
    const nextModel = models.find((model) => model.id === modelId);
    updateSeat({
      model_id: modelId,
      account_id: nextModel?.account_id ?? seat.account_id,
      reasoning_effort: nextModel?.reasoning_efforts[0] ?? seat.reasoning_effort
    });
  }

  return (
    <section className={`seat-card ${seat.enabled ? "" : "seat-muted"}`}>
      <header className="seat-header">
        <span className="seat-icon" aria-hidden="true">
          <BrainCircuit size={20} />
        </span>
        <span>
          <h3>{seat.label}</h3>
          <small>{seat.required ? "Required" : "Optional"}</small>
        </span>
        {!seat.required && (
          <button
            aria-label={seat.enabled ? "Disable Critic B" : "Enable Critic B"}
            className="icon-button"
            type="button"
            onClick={() => updateSeat({ enabled: !seat.enabled })}
          >
            {seat.enabled ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
          </button>
        )}
      </header>

      <label className="field-label">
        Provider
        <span className="select-wrap">
          <select
            disabled={!seat.enabled}
            value={seat.account_id}
            onChange={(event) => {
              const accountModels = models.filter(
                (model) => model.account_id === event.target.value
              );
              const nextModel = accountModels[0] ?? selectedModel;
              updateSeat({
                account_id: event.target.value,
                model_id: nextModel.id,
                reasoning_effort: nextModel.reasoning_efforts[0]
              });
            }}
          >
            {[...new Set(models.map((model) => model.account_id))].map((accountId) => {
              const account = accounts.find((item) => item.id === accountId);

              return (
                <option key={accountId} value={accountId}>
                  {account?.label ?? accountId}
                </option>
              );
            })}
          </select>
          <ChevronDown aria-hidden="true" size={16} />
        </span>
      </label>

      <label className="field-label">
        Model
        <span className="select-wrap">
          <select
            disabled={!seat.enabled}
            value={seat.model_id}
            onChange={(event) => updateModel(event.target.value)}
          >
            {availableModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
          <ChevronDown aria-hidden="true" size={16} />
        </span>
      </label>

      <label className="field-label">
        Reasoning
        <span className="select-wrap">
          <select
            disabled={!seat.enabled}
            value={seat.reasoning_effort}
            onChange={(event) =>
              updateSeat({ reasoning_effort: event.target.value as ReasoningEffort })
            }
          >
            {reasoningOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <ChevronDown aria-hidden="true" size={16} />
        </span>
      </label>

      <p className="fresh-instance">Fresh instance</p>
    </section>
  );
}
