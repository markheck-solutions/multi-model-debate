# Multi-Model Debate

**Get your ideas stress-tested by AI before you build them.**

You know that feeling when you're about to start a project and you *wish* you could get a few smart people to poke holes in your plan first? This tool does exactly that, except the "smart people" are different AI models debating each other about your idea.

![Demo](demo.gif)

## What It Does

You describe what you want to build. Two AI models then:

1. **Critique your plan** independently (finding different problems)
2. **Debate each other** about which issues matter most
3. **A judge picks a winner** based on argument quality
4. **The winning critic's points get consolidated**
5. **Your original AI defends your plan** against the winner
6. **You get a final report** with clear recommendations

The whole process takes about 10-20 minutes, *depending on complexity*, and runs automatically.

## Why Use This?

| Without This Tool | With This Tool |
|-------------------|----------------|
| You ask one AI for feedback | Three AIs argue about your plan |
| AI tends to agree with you | AIs are prompted to find problems |
| Criticism may be shallow | Multi-round debate deepens analysis |
| You might miss blind spots | Different AI "personalities" catch different issues |
| No structure to the feedback | Organized report with priorities |

**Best for:**
- Architecture decisions
- Feature designs
- Migration plans
- Any plan where being wrong is expensive

---

## Prerequisites

You need **at least 2 AI CLIs** installed before using this tool

This tool works out of the box using the following three:

| AI | Command | How to Get It |
|----|---------|---------------|
| Claude Code | `claude` | [Install Claude Code](https://github.com/anthropics/claude-code) |
| Codex | `codex` | [Install OpenAI Codex CLI](https://github.com/openai/codex) |
| Gemini CLI | `gemini` | [Install Google Gemini CLI](https://github.com/google-gemini/gemini-cli) |

---

## Quick Setup: Let Claude Do It For You

Already using Claude Code? Just paste this into your conversation:

```
I want to install the Multi-Model Debate tool. Please:

1. Check if pipx is installed. If not, install it
2. Run: pipx install multi-model-debate
3. Verify it works: multi-model-debate --help
4. APPEND these instructions to my ~/.claude/CLAUDE.md file (create the file if it doesn't exist, but DO NOT overwrite any existing content):

## Multi-Model Debate Tool

When I say "run the debate tool", "start the debate", "do a peer review", or "review this":
1. Save my plan to a markdown file in the current directory
2. Run: multi-model-debate start <filename.md>
3. Wait for it to complete (about 10-20 minutes)
4. Show me the Final Position from the runs folder

When I say "resume the debate" or "continue the review":
1. Run: multi-model-debate resume

When I say "check debate status":
1. Run: multi-model-debate status

Confirm everything is set up
```

That's it! Claude will handle the rest. Once done, you can say "run the debate tool" anytime during your Claude Code session.

---

## Manual Setup

*Skip this if you used the Quick Setup above.*

### Step 1: Install the Tool

Open your terminal (Terminal app on Mac, or Command Prompt/PowerShell on Windows) and run this command:

```bash
pipx install multi-model-debate
```

This downloads and installs the tool from [PyPI](https://pypi.org/project/multi-model-debate/).

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

### Step 2: Teach your model the Commands (Example using Claude Code)

If you want to use this tool from inside Claude Code by saying things like "run the debate tool", you need to add instructions to a special file called **CLAUDE.md**.

**Where to put it:**
- `~/.claude/CLAUDE.md` applies to ALL your projects (recommended)
- Or `CLAUDE.md` in a specific project folder; applies only to that project

**What to add:**

Open (or create) the file and **add this at the bottom** (don't replace existing content):

```markdown
## Multi-Model Debate Tool

When I say "run the debate tool", "start the debate", "do a peer review", or "review this":
1. Save my plan to a markdown file in the current directory
2. Run: multi-model-debate start <filename.md>
3. Wait for it to complete (about 10-20 minutes)
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

### Option A: From Inside your AI CLI
*The recommended option. Your AI will defend your plan with context* 

Once you've completed setup, just talk naturally:

**Start a review:**
1. Describe your plan to AI like you normally would
2. Say **"run the debate tool"**
3. Wait about 10-20 minutes
4. Your AI CLI will show you the results

**Other commands you can say:**

| Say This | What Happens |
|----------|--------------|
| "run the debate tool" | Starts a new review of your plan |
| "resume the debate" | Continues if it got interrupted |
| "check debate status" | Shows progress |
| "show me the final position" | Displays the results again |

### Option B: Standalone

You can also run the tool directly from the terminal:

**From a file:**
```bash
multi-model-debate start [my-plan].md
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
        └── p6_final_position.md  ← THE FINAL SUMMARY (start here!)
```

### The Summary File

The file you care about most is:

```
runs/<latest-folder>/p6_final_position.md
```

This is the **Final Position**: a structured summary of everything that happened in the debate, with clear recommendations for you.

**Quick way to find it:**
- From AI CLI: Say "show me the final position"
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
- Make sure you have at least 2 AI CLIs installed (e.g., claude, codex, or gemini)
- Test them: `claude --version`, `codex --version`, `gemini --version`

**The debate seems stuck**
- Say "check debate status" (in AI CLI) or run `multi-model-debate status` (in terminal)
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

The tool works out of the box with Claude, Codex, and Gemini. To customize which AI models are used, create a configuration file.

### Creating the Config File

1. Open your project folder (where you run the debate tool)
2. Create a new file called `multi_model_debate.toml`
3. Copy this starter template:

```toml
[roles]
strategist = "claude"
critics = ["gemini", "codex"]
judge = "claude"

[debate]
critic_rounds = 4            # How many rounds the critics debate each other
strategist_rounds = 4        # How many rounds your AI defends the plan

[notification]
enabled = true               # Desktop notification when done
command = "notify-send"      # Linux (use "osascript" wrapper for Mac)
```

### What Each Role Does

| Role | What It Does | Recommendation |
|------|--------------|----------------|
| **strategist** | Defends your plan | Use your primary AI |
| **critics** | Find problems with your plan | Use 2+ different AIs for diverse perspectives |
| **judge** | Picks which critic argued better | Same as strategist (different instance) |

> **Note:** The `critics` list must have at least 2 different AI models. This ensures diverse perspectives in the debate.

### Critic Perspectives (Lenses)

Each critic approaches your plan with a different "lens" *a set of concerns they focus on*

**How it works:**

```toml
[roles]
critics = ["gemini", "ollama"]
# critic_1_lens↑      ↑critic_2_lens
```

| Position | Lens File | Default Focus |
|----------|-----------|---------------|
| First in list | `critic_1_lens.md.j2` | Architecture, logic, scalability, edge cases |
| Second in list | `critic_2_lens.md.j2` | Security, deployment, maintenance, dependencies |

**Choosing which AI gets which lens:**

Think about each AI's strengths. Put the AI that's better at:
- **Deep technical analysis** → first position (critic_1_lens)
- **Practical/real-world concerns** → second position (critic_2_lens)

**Tip:** If you're unsure, Ask AI:
> "Which model is better at [specific strength]?"

### Customizing Lenses

The default lenses work well for software projects. For specialized domains, you can customize what each critic focuses on.

**Lens files are located at:**
```
src/multi_model_debate/prompts/
├── critic_1_lens.md.j2    # First critic's perspective
└── critic_2_lens.md.j2    # Second critic's perspective
```

**Examples by domain:**

| Domain | critic_1_lens could focus on | critic_2_lens could focus on |
|--------|------------------------------|------------------------------|
| Academia | Methodology rigor, statistical validity | Citation gaps, reproducibility, ethics |
| Agriculture | Soil/climate assumptions, yield models | Regulatory compliance, supply chain |
| Healthcare | Clinical accuracy, safety protocols | HIPAA compliance, patient outcomes |

**Tip:** Ask AI to help customize:
> "Help me modify the debate tool's critic lenses for [your domain]"

---

## Using Other AI Models

The tool includes defaults for Claude, Codex, and Gemini. Want to use a different AI? Follow these steps.

### Step 1: Make Sure Your AI Has a Command-Line Tool

The debate tool works by running commands in your terminal. Your AI needs a CLI (command-line interface) tool.

**Examples of AI CLIs:**
- **Ollama**: `ollama run llama3 "your prompt"`
- **[llm](https://llm.datasette.io/)**: `llm "your prompt"`

**Test it first:** Open your terminal and try running your AI with a simple prompt. If it responds, you're good!

### Step 2: Find (or Create) Your Config File

Look for `multi_model_debate.toml` in your project folder.

**Don't have one?** Create it:
1. Open your project folder
2. Create a new text file
3. Name it exactly: `multi_model_debate.toml`

### Step 3: Add Your AI's Settings

Open `multi_model_debate.toml` and add a section for your AI. Copy this template and fill in the blanks:

```toml
[cli.YOUR_AI_NAME]
command = "your-cli-command"
input_mode = "positional"
```

**Example for Ollama:**

```toml
[cli.ollama]
command = "ollama"
subcommand = "run"
input_mode = "positional"
flags = ["llama3"]
```

**What each setting means:**

| Setting | What to Put | Example |
|---------|-------------|---------|
| `command` | The command you type in terminal | `"ollama"` |
| `subcommand` | Extra word after command (if needed) | `"run"` |
| `input_mode` | How the prompt is sent | `"positional"` (usually this) |
| `flags` | Extra options (like model name) | `["llama3"]` |
| `timeout` | Max seconds to wait (optional) | `600` |

**Complete example with Ollama as a critic:**

```toml
[roles]
strategist = "claude"
critics = ["ollama", "gemini"]
judge = "claude"

[cli.ollama]
command = "ollama"
subcommand = "run"
input_mode = "positional"
flags = ["llama3"]
timeout = 600
```

### Step 4: Test It

Run a debate and check that your AI responds. If you see errors, double-check:
- Is the CLI installed? (Try running it in terminal)
- Is the spelling exactly right in the config?
- Did you save the file?

### Need Help?

Just ask AI:

> "Help me configure the debate tool to use [your AI name]"

AI can help you figure out the right settings for its CLI.

---

## How This Was Built

I'm not a developer. This tool was built entirely with Claude Code Opus 4.5. I provided the vision and continuously questioned EVERYTHING. The code itself? All AI-generated.

If you're a developer reviewing this, I can't explain the architectural decisions or maintain this at a technical level. I only aggressively push AI for *well-architected* and *best-in-class* decisions and then have separate AI models critique it.

If you're a non-developer curious how AI can enable you, I hope this helps.

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
