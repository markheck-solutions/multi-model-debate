# Multi-Model Debate

**Get your ideas stress-tested by AI before you build them.**

You know that feeling when you're about to start a project and you *wish* you could get a few smart people to poke holes in your plan first? This tool does exactly that — except the "smart people" are different AI models debating each other about your idea.

![Demo](demo.gif)

## What It Does

You describe what you want to build. Three AI models then:

1. **Critique your plan** independently (finding different problems)
2. **Debate each other** about which issues matter most
3. **A judge picks a winner** based on argument quality
4. **The winning critic's points get consolidated**
5. **Your original AI defends your plan** against the best criticisms
6. **You get a final report** with clear recommendations

The whole process takes about 10-15 minutes and runs automatically.

## Why Use This?

| Without This Tool | With This Tool |
|-------------------|----------------|
| You ask one AI for feedback | Three AIs argue about your plan |
| AI tends to agree with you | AIs are prompted to find problems |
| Criticism may be shallow | Multi-round debate deepens analysis |
| You might miss blind spots | Different AI "personalities" catch different issues |
| No structure to the feedback | Organized report with priorities |

**Best for:**
- Architecture decisions ("Should we use microservices or a monolith?")
- Feature designs ("Here's how I want to implement search...")
- Migration plans ("We're moving from X to Y...")
- Any plan where being wrong is expensive

---

## Prerequisites

You need **at least 2 AI CLIs** installed before using this tool:

| AI | Command | How to Get It |
|----|---------|---------------|
| Claude | `claude` | ✅ You already have this if you're using Claude Code |
| Codex | `codex` | [Install OpenAI Codex CLI](https://github.com/openai/codex) |
| Gemini | `gemini` | [Install Google Gemini CLI](https://github.com/google-gemini/gemini-cli) |

**You need Claude + at least one other.** Test with: `claude --version`, `codex --version`, `gemini --version`

---

## Quick Setup: Let Claude Do It For You

If you're already using Claude Code, just paste this into your conversation:

```
I want to install the Multi-Model Debate tool. Please:

1. Check if pipx is installed, if not install it
2. Run: pipx install git+https://github.com/markheck-solutions/multi-model-debate.git
3. Verify it works: multi-model-debate --help
4. APPEND these instructions to my ~/.claude/CLAUDE.md file (create the file if it doesn't exist, but DO NOT overwrite any existing content):

## Multi-Model Debate Tool

When I say "run the debate tool", "start the debate", "do a peer review", or "review this":
1. Save my plan to a markdown file in the current directory
2. Run: multi-model-debate start <filename.md>
3. Wait for it to complete (about 10-15 minutes)
4. Show me the Final Position from the runs folder

When I say "resume the debate" or "continue the review":
1. Run: multi-model-debate resume

When I say "check debate status":
1. Run: multi-model-debate status

5. Confirm everything is set up
```

That's it! Claude will handle the rest. Once done, you can say "run the debate tool" anytime.

---

## Manual Setup

*Skip this if you used the Quick Setup above.*

### Step 1: Install the Tool

Open your terminal (Terminal app on Mac, or Command Prompt/PowerShell on Windows) and run this command:

```bash
pipx install git+https://github.com/markheck-solutions/multi-model-debate.git
```

This downloads and installs the tool on your computer.

> **Don't have pipx?** Install it first:
> - **Mac:** `brew install pipx && pipx ensurepath`
> - **Linux:** `sudo apt install pipx && pipx ensurepath`
> - **Windows:** `scoop install pipx` or `pip install --user pipx`
>
> Then restart your terminal and run the install command above.

To verify it worked, run:
```bash
multi-model-debate --help
```

You should see a list of commands.

### Step 2: Teach Claude Code the Commands

If you want to use this tool from inside Claude Code by saying things like "run the debate tool", you need to add instructions to a special file called **CLAUDE.md**.

**Where to put it:**
- `~/.claude/CLAUDE.md` — applies to ALL your projects (recommended)
- Or `CLAUDE.md` in a specific project folder — applies only to that project

**What to add:**

Open (or create) the file and **add this at the bottom** (don't replace existing content):

```markdown
## Multi-Model Debate Tool

When I say "run the debate tool", "start the debate", "do a peer review", or "review this":
1. Save my plan to a markdown file in the current directory
2. Run: multi-model-debate start <filename.md>
3. Wait for it to complete (about 10-15 minutes)
4. Show me the Final Position from the runs folder

When I say "resume the debate" or "continue the review":
1. Run: multi-model-debate resume

When I say "check debate status":
1. Run: multi-model-debate status
```

> **Where is ~/.claude/?**
> - **Mac/Linux:** It's a hidden folder in your home directory. In terminal: `open ~/.claude` (Mac) or `xdg-open ~/.claude` (Linux)
> - **Windows:** `C:\Users\YourName\.claude\`

---

## How to Use It

### Option A: From Inside Claude Code (Recommended)

Once you've completed setup, just talk naturally:

**Start a review:**
1. Describe your plan to Claude like you normally would
2. Say **"run the debate tool"**
3. Wait about 10-15 minutes
4. Claude will show you the results

**Other commands you can say:**

| Say This | What Happens |
|----------|--------------|
| "run the debate tool" | Starts a new review of your plan |
| "resume the debate" | Continues if it got interrupted |
| "check debate status" | Shows progress |
| "show me the final position" | Displays the results again |

### Option B: Standalone (From Terminal)

You can also run the tool directly without Claude Code:

**From a file:**
```bash
multi-model-debate start my-plan.md
```

**By typing your plan directly:**
```bash
multi-model-debate start --stdin
```
Then type or paste your plan, and press `Ctrl+D` (Mac/Linux) or `Ctrl+Z` then Enter (Windows) when done.

**Other commands:**
```bash
multi-model-debate status    # Check progress
multi-model-debate resume    # Continue interrupted debate
```

---

## Where to Find the Results

### Debate Files Location

All debates are saved in a **`runs/`** folder in your current directory:

```
your-project/
└── runs/
    └── 20260123_143052/          ← One folder per debate (date_time)
        ├── 00_game_plan.md       ← Your original plan
        ├── p1_gemini_baseline.json
        ├── p1_codex_baseline.json
        ├── p2_r1_gemini.json     ← Debate rounds
        ├── p2_r2_codex.json
        ├── ...
        ├── p3_winner_decision.md
        ├── p4_peer_review.md
        ├── p5_r1_strategist.md   ← Defense rounds
        ├── ...
        └── p6_final_position.md  ← ⭐ THE SUMMARY (start here!)
```

### The Summary File

The file you care about most is:

```
runs/<latest-folder>/p6_final_position.md
```

This is the **Final Position** — a structured summary of everything that happened in the debate, with clear recommendations for you.

**Quick way to find it:**
- From Claude Code: Say "show me the final position"
- From terminal: `ls -t runs/` shows newest folder first, then open `p6_final_position.md`

---

## What You Get Back

The **Final Position** (`p6_final_position.md`) contains:

| Section | What It Tells You |
|---------|-------------------|
| **Executive Summary** | Quick verdict: APPROVED, CONDITIONAL, or BLOCKED |
| **Issues by Category** | Technical facts vs. tradeoffs vs. constraints |
| **What Was Resolved** | Points defended or conceded during debate |
| **What Needs Your Decision** | Things only a human can decide |
| **Recommended Actions** | Prioritized fixes (BLOCKER → HIGH → MEDIUM) |
| **My Recommendation** | The AI's honest opinion on tradeoffs |

### Example Output

```markdown
## EXECUTIVE SUMMARY
CONDITIONAL APPROVAL — the core architecture is sound, but four
clarifications are required before implementation.

## WHAT NEEDS YOUR DECISION
| # | Decision | Options |
|---|----------|---------|
| 1 | Burst allowance | A) Strict (10), B) Moderate (25), C) Permissive (50) |
| 2 | Consistency model | A) Exact global (slower), B) Approximate (faster) |

## RECOMMENDED ACTIONS
| Priority | Action | Why |
|----------|--------|-----|
| BLOCKER | Define burst capacity | Without this, 100 requests can hit in 1ms |
| HIGH | Specify consistency strategy | Avoids surprise latency |

## MY RECOMMENDATION
Define the burst capacity first. Everything else is refinement.
```

---

## Troubleshooting

**"Command not found: multi-model-debate"**
- Run `pipx ensurepath` and restart your terminal
- Make sure the install command completed without errors

**"Command not found: pipx"**
- Install pipx first (see Step 1)

**"No models available" or the tool can't find AI CLIs**
- Make sure you have at least 2 AI CLIs installed (claude, codex, or gemini)
- Test them: `claude --version`, `codex --version`, `gemini --version`

**The debate seems stuck**
- Say "check debate status" (in Claude Code) or run `multi-model-debate status`
- Say "resume the debate" or run `multi-model-debate resume`

**Claude doesn't understand "run the debate tool"**
- Make sure the CLAUDE.md instructions were added (Quick Setup does this automatically)
- Check the file is in the right place (`~/.claude/CLAUDE.md`)
- Try restarting Claude Code

**I can't find the results**
- Look in the `runs/` folder in your current directory
- The summary is `runs/<folder>/p6_final_position.md`
- Run `ls runs/` to see all your debates

---

## Configuration (Optional)

The tool works out of the box, but you can customize it by creating a file called `multi_model_debate.toml` in your project folder:

```toml
[debate]
critic_rounds = 4            # How many rounds the critics debate each other
strategist_rounds = 4        # How many rounds your AI defends the plan

[models]
available = ["claude", "gemini", "codex"]   # Which AIs to use

[notification]
enabled = true               # Desktop notification when done
command = "notify-send"      # Linux (use "osascript" wrapper for Mac)
```

---

## How This Was Built

I'm not a developer. This tool was built entirely with Claude Code. I provided the vision and continuously questioned EVERYTHING. The code itself? All AI-generated.

If you're a developer reviewing this, I can't explain the architectural decisions or maintain this at a technical level. I only aggressively push AI for well-architected and best-in-class decisions and then have separate AI models critique it.

If you're a non-developer curious how AI can enable you, here you go.

---

# Technical Reference

*Everything below is for developers.*

## How the Debate Works

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Baseline Critiques                                     │
│   Critic A ──────► independent critique                         │
│   Critic B ──────► independent critique                         │
├─────────────────────────────────────────────────────────────────┤
│ Phase 2: Adversarial Debate (4 rounds)                          │
│   Critic A ◄────► Critic B                                      │
│   (They argue about which issues matter most)                   │
├─────────────────────────────────────────────────────────────────┤
│ Phase 3: Winner Determination                                   │
│   Judge picks which critic made better arguments                │
├─────────────────────────────────────────────────────────────────┤
│ Phase 4: Peer Review                                            │
│   Winner consolidates all critiques                             │
├─────────────────────────────────────────────────────────────────┤
│ Phase 5: Strategist Defense (4 rounds)                          │
│   Your original AI defends your plan                            │
├─────────────────────────────────────────────────────────────────┤
│ Phase 6: Final Position                                         │
│   Summary report with recommendations                           │
└─────────────────────────────────────────────────────────────────┘
```

## CLI Reference

```bash
multi-model-debate start [OPTIONS] [FILE]
  --stdin, -           Read proposal from stdin
  --skip-protocol      Skip pre-debate date injection
  --config, -c PATH    Custom config file
  --runs-dir, -r PATH  Custom output directory
  --verbose, -v        Show detailed logs

multi-model-debate resume [OPTIONS]
  --run PATH           Resume specific run (default: latest)

multi-model-debate status
```

## Development

```bash
git clone https://github.com/markheck-solutions/multi-model-debate.git
cd multi-model-debate
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v
ruff check src/ tests/
mypy src/
```

## License

MIT
