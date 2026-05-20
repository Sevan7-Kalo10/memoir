---
name: functional-style
weight: 4
tags: [code, fp, patterns]
domain: code
description: Why pure functions and immutable data win
---

# Functional Style

## The Principle
A function's output should depend only on its inputs.
No hidden state, no side effects, no surprises.

## Why
- **Testable**: pure function → input/output → one assertion
- **Composable**: small functions chain into large behavior
- **Debuggable**: the bug is in the function, not in the hidden state
- **Parallelizable**: no shared mutable state → no race conditions

## When to Break the Rule
- I/O is inherently side-effectful. Isolate it at the edges.
- Sometimes mutable state is simpler. Use it, but contain it.

## Log
- **2026-05-20** — Initial entry. This preference emerged from debugging
  too many state-related bugs in imperative codebases.
