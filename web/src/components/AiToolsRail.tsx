import { KeyRound, Laptop, Plus, ShieldCheck, Sparkles } from "lucide-react";
import type { ProviderAccount } from "../types";

interface AiToolsRailProps {
  accounts: ProviderAccount[];
}

const statusText: Record<ProviderAccount["status"], string> = {
  connected: "Connected",
  needs_setup: "Ready to add",
  unavailable: "Local only"
};

export function AiToolsRail({ accounts }: AiToolsRailProps) {
  return (
    <aside className="tools-rail" aria-label="AI tools">
      <div className="rail-header">
        <div>
          <p className="eyebrow">AI Tools</p>
          <h2>Connect once. Reuse everywhere.</h2>
        </div>
        <Sparkles aria-hidden="true" size={22} />
      </div>

      <div className="tool-list">
        {accounts.map((account) => (
          <div className="tool-row" key={account.id}>
            <span className="tool-icon" aria-hidden="true">
              {account.auth_mode === "local" ? <Laptop size={18} /> : <KeyRound size={18} />}
            </span>
            <span>
              <strong>{account.label}</strong>
              <small>{statusText[account.status]}</small>
            </span>
          </div>
        ))}
      </div>

      <button className="add-tool" type="button">
        <Plus aria-hidden="true" size={18} />
        Add AI tool
      </button>

      <div className="privacy-note">
        <ShieldCheck aria-hidden="true" size={18} />
        <span>API keys stay out of demo runs. Local runs keep credentials on this machine.</span>
      </div>
    </aside>
  );
}
