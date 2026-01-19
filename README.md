# multi-model-debate

Let AI models argue so you don't have to.

## What It Does

Three AI models debate your proposal. Critics challenge it. A judge picks the stronger argument. The original model defends against the best critiques. You get a stress-tested assessment, not "yes this is great."

## Quick Start

```bash
# Install
pip install -e .

# Run a debate
multi-model-debate start your_proposal.md

# Resume if interrupted
multi-model-debate resume

# Check status
multi-model-debate status
```

## Requirements

- Python 3.11+
- CLI access to at least 3 AI models (claude, gemini, codex by default)
- Each model needs to be callable from your terminal

## How It Works

1. **Baseline**: Each critic independently reviews the proposal
2. **Debate**: Critics argue with each other (4 rounds)
3. **Judge**: Determines which critic made stronger arguments
4. **Peer Review**: Winner consolidates all critiques
5. **Defense**: Original model defends against critiques (4 rounds)
6. **Final Position**: Summary with recommendations

The output is a Final Position document listing every critique and how it was addressed.

## Configuration

Copy `multi_model_debate.toml` to your project and customize:

```toml
[debate]
critic_rounds = 4
strategist_rounds = 4

[models]
available = ["claude", "gemini", "codex"]
```

## How This Was Built

I'm not a developer. This tool was built entirely with Claude Code. I provided the vision and continuously questioned EVERYTHING. The code itself? All AI-generated.

If you're a developer reviewing this, I can't explain the architectural decisions or maintain this at a technical level. I only aggressively push AI for well-architected and best-in-class decisions and then have separate AI models critique it.

If you're a non-developer curious how AI can enable you, here you go.

## Limitations

- Requires 3+ model families to run (critics must differ from strategist)
- Judge uses the same model family as the strategist, which may introduce subtle bias in close calls
- No GUI, terminal only
- Debates take 10-30 minutes depending on model response times

## License

MIT
