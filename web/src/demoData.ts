import type {
  CatalogResponse,
  DebateRunSummary,
  PanelConfig,
  RunEvent,
  RunLane
} from "./types";

export const fallbackCatalog: CatalogResponse = {
  accounts: [
    {
      id: "demo-openai",
      provider: "openai",
      label: "ChatGPT / Codex",
      auth_mode: "demo",
      status: "connected",
      secret_storage: "not_stored"
    },
    {
      id: "demo-anthropic",
      provider: "anthropic",
      label: "Claude",
      auth_mode: "demo",
      status: "needs_setup",
      secret_storage: "not_stored"
    },
    {
      id: "demo-google",
      provider: "google",
      label: "Gemini",
      auth_mode: "demo",
      status: "needs_setup",
      secret_storage: "not_stored"
    },
    {
      id: "demo-local",
      provider: "local",
      label: "Local model",
      auth_mode: "local",
      status: "unavailable",
      secret_storage: "not_stored"
    }
  ],
  models: [
    {
      id: "gpt-5-thinking",
      account_id: "demo-openai",
      provider: "openai",
      label: "GPT-5 Thinking",
      cost_hint: "Balanced",
      reasoning_efforts: ["low", "medium", "high", "xhigh"]
    },
    {
      id: "gpt-5-fast",
      account_id: "demo-openai",
      provider: "openai",
      label: "GPT-5 Fast",
      cost_hint: "Lower",
      reasoning_efforts: ["none", "low", "medium"]
    },
    {
      id: "claude-demo",
      account_id: "demo-anthropic",
      provider: "anthropic",
      label: "Claude demo seat",
      cost_hint: "Setup needed",
      reasoning_efforts: ["medium"]
    },
    {
      id: "gemini-demo",
      account_id: "demo-google",
      provider: "google",
      label: "Gemini demo seat",
      cost_hint: "Setup needed",
      reasoning_efforts: ["medium"]
    }
  ],
  default_panel: {
    diversity_label: "Focused",
    seats: [
      {
        role: "builder",
        label: "Builder",
        required: true,
        enabled: true,
        account_id: "demo-openai",
        model_id: "gpt-5-thinking",
        reasoning_effort: "medium",
        fresh_instance: true
      },
      {
        role: "critic_a",
        label: "Critic A",
        required: true,
        enabled: true,
        account_id: "demo-openai",
        model_id: "gpt-5-thinking",
        reasoning_effort: "high",
        fresh_instance: true
      },
      {
        role: "critic_b",
        label: "Critic B",
        required: false,
        enabled: false,
        account_id: "demo-openai",
        model_id: "gpt-5-fast",
        reasoning_effort: "medium",
        fresh_instance: true
      },
      {
        role: "judge",
        label: "Judge",
        required: true,
        enabled: true,
        account_id: "demo-openai",
        model_id: "gpt-5-thinking",
        reasoning_effort: "medium",
        fresh_instance: true
      }
    ]
  }
};

export function buildFallbackRun(
  question: string,
  lane: RunLane,
  panel: PanelConfig
): DebateRunSummary {
  return {
    id: `demo-${Date.now()}`,
    lane,
    question,
    status: "completed",
    active_phase: "final",
    panel,
    final_report: [
      "## Final Position",
      "",
      `**Question:** ${question}`,
      "",
      "**Recommendation:** Conditional approval. Continue, but write down launch criteria, rollback ownership, and cost controls before users depend on it.",
      "",
      "**Top risks:** Success criteria are broad, support ownership is vague, and budget exposure needs a cap.",
      "",
      "**Next action:** Convert the decision into a one-page launch brief and run another debate after the missing details are filled in."
    ].join("\n")
  };
}

export function buildFallbackEvents(runId: string): RunEvent[] {
  return [
    {
      run_id: runId,
      phase: "build",
      status: "running",
      title: "Builder framed the decision",
      detail: "The idea became a concrete plan with assumptions and success criteria.",
      progress: 18
    },
    {
      run_id: runId,
      phase: "critique",
      status: "running",
      title: "Critic A found weak spots",
      detail: "The panel flagged launch timing, support load, cost, and rollback clarity.",
      progress: 42
    },
    {
      run_id: runId,
      phase: "debate",
      status: "running",
      title: "Panel compared tradeoffs",
      detail: "The debate separated blockers from risks that can be monitored.",
      progress: 68
    },
    {
      run_id: runId,
      phase: "judge",
      status: "running",
      title: "Judge weighed the evidence",
      detail: "Evidence quality won over confidence.",
      progress: 88
    },
    {
      run_id: runId,
      phase: "final",
      status: "completed",
      title: "Final report ready",
      detail: "Recommendation, risks, and next steps are ready.",
      progress: 100
    }
  ];
}
