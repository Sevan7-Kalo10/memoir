# Integrating Memoir

Memoir is a library. One `pip install`, ~15 lines of glue code, and your AI has continuous memory.

---

## Claude Code — Manual Import (no coding)

If you don't want to write code: paste your memories into the conversation
whenever relevant.

```bash
# Step 1: build search index (first time only)
memoir index --store ./my-memories

# Step 2: load memories for your topic
memoir load --trigger "you are my AI companion" --store ./my-memories --render
```

The `--render` flag outputs the full text of matched memories. **Copy the
output and paste it at the start of your Claude Code session.** Claude will
read it as shared context.

Before each session, re-run the command with a relevant trigger phrase.
This is manual — but it takes under 5 seconds.

To search for a specific memory mid-conversation:

```bash
memoir search "functional programming" --store ./my-memories
```

---

## Claude Code — Auto Import (hooks)

Claude Code supports [hooks](https://docs.claude.codes/hooks) —
scripts that run automatically at session start, every user message, and
session end. This gives you fully automatic memory injection.

### Step 1: Create the loader script

**`load_context.py`**
```python
import json
from pathlib import Path
from memoir.config import MemoirConfig
from memoir.core.loader import build_load_plan, render_context
from memoir.core.weight import mark_triggered

STORE_DIR = Path("./my-memories")
CONTEXT_FILE = Path(".claude/memory_context.md")

config = MemoirConfig.from_yaml(STORE_DIR / "memoirs.yaml")

# Read last user prompt from the hook environment
last_prompt = ""
try:
    # Claude Code exposes conversation state via env vars
    env_file = Path(".claude/session_env.json")
    if env_file.exists():
        env_data = json.loads(env_file.read_text())
        last_prompt = env_data.get("last_user_message", "")
except Exception:
    pass

plan = build_load_plan(
    config.store_path, config,
    conversation_text=last_prompt,
)

# Mark triggered (weight boost accumulates over time)
for f in plan.files:
    try:
        mark_triggered(config.store_path / f)
    except Exception:
        pass

context = render_context(plan, config.store_path)
CONTEXT_FILE.write_text(context, encoding="utf-8")
print(f"[Memoir] Loaded {len(plan.files)} memories (~{plan.total_tokens_estimate} tokens)")
```

### Step 2: Configure hooks

Add to your **`.claude/settings.json`**:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python ./load_context.py"
      }]
    }]
  }
}
```

### Step 3: Use it

Start a Claude Code session. The hook fires automatically — you'll see
`[Memoir] Loaded 12 memories (~3500 tokens)` in the startup output.
Your AI now has persistent memory across every session.

To also track what triggers during conversation, add a second hook:

```json
"UserPromptSubmit": [{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "python ./load_context.py"
  }]
}]
```

This re-runs the loader on every user message, so memory selection adapts
to the current topic in real time.

---

## OpenAI / DeepSeek / Any Chat API

```python
from openai import OpenAI
from memoir.core.loader import build_load_plan, render_context
from memoir.config import MemoirConfig

config = MemoirConfig.from_yaml("./my-memories/memoirs.yaml")

def chat(user_message: str):
    plan = build_load_plan(
        config.store_path, config,
        conversation_text=user_message,
    )
    memory_context = render_context(plan, config.store_path)

    client = OpenAI(base_url="https://api.deepseek.com")
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"You have these memories:\n\n{memory_context}"},
            {"role": "user", "content": user_message},
        ],
    )
```

The build_load_plan runs the four-layer loading engine. render_context
concatenates matched files. That's it — the AI now reads your memories
as system context before every reply.

---

## Common Patterns

### Append a new memory from conversation

```python
from memoir.core.frontmatter import write
from datetime import datetime, timezone

fm = {
    "name": "sevan-prefers-shochu",
    "weight": 4,
    "tags": ["Sevan", "酒", "偏好"],
    "domain": "core",
    "description": "Sevan likes imo shochu, not fruity high-proof",
    "created": datetime.now(timezone.utc).isoformat(),
}
write("./my-memories/core/sevan-shochu.md", fm, "Sevan prefers imo shochu over fruit-forward styles.")
```

### Search before replying

```python
from memoir.core.indexer import MemoirIndex

index = MemoirIndex(config.store_path)
index.auto()  # Rebuild only if needed
results = index.search("prefers shochu", weight_min=2, limit=5)
for r in results:
    print(r["relpath"], r["snippet"])
```

---

## The Minimal Loop

A complete 15-line integration that does everything:

```python
from memoir.config import MemoirConfig
from memoir.core.loader import build_load_plan, render_context
from memoir.core.weight import mark_triggered

config = MemoirConfig.from_yaml("./my-memories/memoirs.yaml")

def context_for(user_input: str) -> str:
    plan = build_load_plan(
        config.store_path, config,
        conversation_text=user_input,
    )
    for f in plan.files:
        mark_triggered(config.store_path / f)
    return render_context(plan, config.store_path)
```

Call `context_for("your message")` → paste result into system prompt. Done.
