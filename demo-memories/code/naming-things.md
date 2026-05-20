---
name: naming-things
weight: 3
tags: [code, naming, readability]
domain: code
description: Names are the first line of documentation
---

# Naming Things

## The Principle
A name should tell you what something IS, not what it DOES.
`users_by_age` not `process_data`. `send_invoice` not `do_stuff`.

## Rules of Thumb
- **Length proportional to scope**: one-letter variables are fine in
  a 3-line loop. In a 300-line function, use full words.
- **No abbreviations without a glossary**: `cfg` means nothing.
  `config` means something.
- **Consistency over cleverness**: if you call it `fetch` in one place,
  don't call it `retrieve` in another.

## Why
Reading code is the bottleneck, not writing it. Every name is a
decision about what the next reader will understand. Bad names
are a tax collected in confusion.

## Log
- **2026-05-20** — Initial entry.
