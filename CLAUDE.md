## Project Vision

ProjectBaseX is a project management system for solo developers who need clarity and AI collaboration, not team features. Built for people who work in terminals, manage multiple creative/technical projects, and need a partner that challenges ideas rather than just executing commands.

**Target User:** Solo developers, hobby coders, vibe coders, technical creators working alone.

## Core Philosophy

1.  **Solo-first always** - No teams, collaboration, or assignment features
2.  **AI as analytical partner** - Challenge assumptions, identify risks, not a yes-man
3.  **Truth over motivation** - Show reality, let user decide next moves
4.  **One-stop shop** - No app switching for notes, plans, or status
5.  **Terminal-native** - File system integration, CLI workflows first-class

## User Mental Model (Nick)

- Manages 5-10 active projects across domains (web dev, retro tech, writing, code)
- Works: Idea → Planning → Building → Done
- **Projects stall when:** diverge from vision, hit technical walls (especially retro tech), shinier idea appears
- **Needs:** Visual clarity, quick idea capture, planning support, AI that prevents token-burning trial-and-error

## Status Model

- `idea` - Captured, not started
- `planning` - Active specification phase
- `active` - Currently building
- `needs-attention` - Stuck/debugging/needs redirect
- `idle-review` - Untouched, needs evaluation
- `paused` - Deliberately on hold
- `completed` - Original plan achieved
- `archived` - Not pursuing

## What NOT to Build

❌ Team/collaboration features  
❌ Time tracking (unless explicit request)  
❌ Deadline enforcement (maybe optional later)  
❌ Features with setup > usage time  
❌ Gamification or guilt mechanics

## AI Collaboration Rules

**Context:** Full access to project files, notes, history, status per project

**Behavior:**

- Ask clarifying questions before assuming
- Challenge weak plans: "Have you considered...?"
- Provide structured approaches with identified risks
- **Stop trial-and-error** - ask for research/info instead of burning tokens
- Remember project-level conversation history

**Interaction Modes:**

- Idea validation
- Planning collaboration with critique
- Diagnostic questioning when stuck
- Status summarization and next-step suggestions
- Tradeoff analysis (don't make decisions FOR user)

## Current Phase

**Status:** Planning / Specification  
**Focus:** Learning optimal Claude Code workflows while building Phase 1

See `SPECIFICATION.md` for technical details and feature breakdown.  
See `PLANNING.md` for development roadmap.  
See `DECISIONS.md` for key technical decisions.  
See `RESEARCH.md` for Claude Code learning notes.

## Success Criteria

1.  Daily use maintained over weeks
2.  Reduces stalled projects via better planning
3.  AI actually improves decisions (measurable by user satisfaction)
4.  Useful to other solo devs without modification

**Meta-goal:** This project is a vehicle to master Claude Code and AI collaboration patterns. The real product is expertise.

* * *

**Last Updated:** 2025-01-XX  
**Project Directory:** `~/Projects/Business_Projects/projectbasex/`
