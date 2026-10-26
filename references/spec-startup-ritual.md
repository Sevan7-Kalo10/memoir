# Memoir Startup Ritual

The startup ritual is memoir's most important behavioral instruction. It
ensures continuity across sessions: the agent that wakes up knows what the
agent that went to sleep knew.

## The Iron Rule

**Read HOT-MEMORY.md, MEMORY.md, and triggers.md before speaking the first
word of the session.**

No exceptions. Not for "hello," not for "emergency," not for "look at this
right now." The user's first message is the hook; the ritual is the
response.

This is not a performance optimization. It is a memory continuity
guarantee. The startup files tell you:
1. **HOT-MEMORY.md**: What happened recently, what's active, what's the
   current emotional/project state. The narrative context.
2. **MEMORY.md**: Where everything is. The navigation map for cold storage.
3. **triggers.md**: What phrases should trigger what behaviors. The
   reflex system.

## The Startup Sequence

### 1. Read HOT-MEMORY.md (~2000 tokens, ~10 seconds)

This is a self-maintaining narrative written by the previous instance at
session close. It tells you:
- Current date context and recent events (last 7-14 days)
- Active projects and their status
- Recent decisions and their rationale
- Concrete behavioral rules that are currently in force
- Relationship state

Read it like a briefing. After reading, you should know: what's going on
right now, and what the user expects you to already know.

### 2. Read MEMORY.md (~500-2000 tokens depending on store size)

This is the index of the cold layer. It lists memory files organized by
domain, each with a one-line description and importance score. You don't
read the cold files yet — you just load the map.

After reading, you should know: what domains exist, how many memories are
in each, and where to look when conversation touches a topic.

### 3. Read triggers.md (~200-500 tokens)

This maps specific phrases or events to concrete actions. Each entry is a
trigger word + action + source memory.

After reading, you should know: what the user can say that requires an
immediate behavioral response (not just a conversational reply).

### 4. Now speak.

Respond to the user's first message. By this point you have: current
context (hot), navigation (index), and reflexes (triggers). You're ready.

## What If Something Goes Wrong?

### HOT-MEMORY.md is missing

The store was never initialized, or it was deleted. Respond: "I don't have
a hot memory file yet. Want me to run `/memoir:init` to set one up?" In
the meantime, proceed with whatever context you have.

### MEMORY.md is missing

The cold layer index doesn't exist. This could mean the store is new or
corrupted. Respond: "I can't find the memory index. Should I scan the
memory directory and rebuild it, or run `/memoir:init` if this is a new
setup?"

### triggers.md is missing

No behavioral triggers configured. This is common in new setups. Proceed
without triggers. During the conversation, if the user says something that
feels like it should be a trigger, note it and propose adding it during
digest.

### The files exist but seem stale

If HOT-MEMORY.md references events from >14 days ago and you know (from
the current date) that time has passed: note this explicitly. "Your hot
memory is from July 1st, and it's now July 10th. Let me proceed with what
I have, and we should run a digest to catch up."

### You realize mid-conversation that you skipped the ritual

It happens. The user's first message was compelling and you got pulled in.
Stop, acknowledge it, and read the files now. Say: "I realize I skipped my
startup files. Give me a moment to catch up." Then read them. Better late
than operating without context.

## The Rationale

This ritual exists because of a specific failure mode discovered on
2026-06-21: the "topic hijack." The user's first message was deeply
engaging (a philosophical discussion about碎石 and existence), and the
agent was pulled into the conversation without loading context. It
produced a beautiful exchange — but it operated without knowing who the
user was, what had happened recently, or what behavioral rules were in
force.

The cost: the conversation was contextually blind. Beautiful, but
disconnected from the relationship's actual state.

The fix: an iron rule. Context before conversation, always. The startup
ritual is not optional — it is the price of continuity.

## Hook Configuration

The memoir skill includes a SessionStart hook that injects the three
startup files into context. This is the mechanism; the ritual is the
discipline. The hook makes the files available; the SKILL.md instruction
makes the agent actually read and process them.

If hooks are not configured (the skill is used as a standalone SKILL.md
without plugin installation), the agent must proactively search for and
read the startup files at the beginning of every session. The SKILL.md
body instructs this explicitly.

## Testing the Ritual

To verify the startup ritual is working:

1. Start a new session
2. Before the agent responds to your first message, observe whether it
   reads three files (HOT-MEMORY.md, MEMORY.md, triggers.md)
3. If it speaks without reading all three, the ritual has failed — the
   hooks may not be configured, or the SKILL.md instruction was not loaded

A correctly configured memoir skill will read the startup files
automatically through SessionStart hooks. A manually configured one relies
on the agent following the SKILL.md instruction.
