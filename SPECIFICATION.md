## Technical Overview

### System Requirements

- **Platform:** Linux (Debian 12 primary target)
- **Deployment:** Local-first (installable app or local web app)
- **Integration:** File system access to `~/Projects/` directory structure
- **AI:** Claude API (primary), Ollama (secondary/experimental)

### Technology Stack (To Be Determined)

**Options under consideration:**

- **Web App (Local):** Python/Flask or Node/Express with local SQLite
- **Desktop App:** Electron or Tauri
- **Terminal UI:** Python Rich/Textual or Rust/Ratatui
- **Hybrid:** Web UI with CLI companion

**Decision criteria:**

- Easy AI integration
- File system access
- Terminal workflow compatibility
- Nick's comfort level vs. learning goals

## Data Model

### Project Entity

Collapse

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

›

Project {

id: uuid

name: string

status: enum \[idea, planning, active, needs-attention, idle-review, paused, completed, archived\]

category: enum \[business, code, website, other\]

created_date: timestamp

last_modified: timestamp

completion_date: timestamp (nullable)

original_plan: text (what defines "done")

directory_path: string (link to ~/Projects/)

// Relations

notes: Note\[\]

ideas: Idea\[\]

ai_conversations: Conversation\[\]

timeline_events: TimelineEvent\[\]

}

### Note Entity

Collapse

Save Copy

9

1

2

3

4

5

6

7

›

Note {

id: uuid

project_id: uuid

content: text (markdown supported)

created_date: timestamp

tags: string\[\]

}

### Idea Entity

Collapse

Save Copy

9

1

2

3

4

5

6

7

8

9

›

Idea {

id: uuid

title: string

description: text

sparked_by: string (context - what caused this idea)

related_project: uuid (nullable)

captured_date: timestamp

status: enum \[new, exploring, implemented, rejected\]

}

### Conversation Entity

Collapse

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

›

Conversation {

id: uuid

project_id: uuid

messages: Message\[\]

conversation_type: enum \[planning, stuck, review, decision, general\]

started: timestamp

last_message: timestamp

}

Message {

role: enum \[user, assistant\]

content: text

timestamp: timestamp

context_snapshot: json (project state at time of message)

}

### TimelineEvent Entity

Collapse

Save Copy

9

1

2

3

4

5

6

7

8

›

TimelineEvent {

id: uuid

project_id: uuid

event_type: enum \[created, status_change, note_added, ai_session, milestone\]

description: text

timestamp: timestamp

metadata: json

}

## Feature Breakdown

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Basic project tracking with visual dashboard

**Core Features:**

- [ ] Project CRUD operations
    
- [ ] Status management with 8 defined states
    
- [ ] Dashboard view showing:
    
    - [ ] Active projects (status: active, needs-attention)
    - [ ] Idle projects requiring review
    - [ ] Recent activity
    - [ ] Quick stats (total projects by status)
- [ ] Integration with `~/Projects/` directory structure
    
    - [ ] Auto-scan and suggest projects
    - [ ] Link existing projects to directories
- [ ] Simple note-taking per project (Joplin replacement)
    
- [ ] Quick idea capture form with "sparked by" context
    

**Learning Focus:**

- CLAUDE.md best practices
- Task decomposition with Claude Code
- Session management
- Git integration patterns

### Phase 2: AI Integration (Weeks 3-4)

**Goal:** Embedded AI collaboration per project

**Core Features:**

- [ ] Project-specific AI conversation interface
    
- [ ] Conversation history and context retention
    
- [ ] AI interaction modes:
    
    - [ ] **Idea validation mode:** Flesh out new concepts
    - [ ] **Planning mode:** Collaborative spec writing
    - [ ] **Stuck mode:** Diagnostic questioning
    - [ ] **Review mode:** Project status summary
    - [ ] **Decision mode:** Tradeoff analysis
- [ ] Context-aware AI prompts (auto-include project notes, status, files)
    
- [ ] Token usage tracking and warnings
    
- [ ] "Stop and ask" pattern for preventing trial-and-error waste
    

**Learning Focus:**

- Multi-file orchestration
- Prompt engineering patterns from Reddit
- RAG fundamentals (project context injection)
- Comparison: Claude API vs Ollama local

### Phase 3: Intelligence & Workflow (Weeks 5+)

**Goal:** Smart assistance and visual project journey

**Core Features:**

- [ ] Visual project timeline (idea → planning → building → done)
    
- [ ] "What should I work on?" recommendation engine
    
    - [ ] Consider: project momentum, status, last activity, blocking issues
    - [ ] Prioritize: projects close to completion, unstuck projects
    - [ ] Surface: idle projects needing review
- [ ] Pattern recognition:
    
    - [ ] Why do projects stall? (common themes)
    - [ ] Which projects succeed? (characteristics)
    - [ ] Time between status changes
- [ ] Weekly/Monthly views:
    
    - [ ] Projects that moved forward
    - [ ] Projects that didn't move (with reasons if captured)
    - [ ] Status change history
- [ ] Quick project health check
    
    - [ ] "Is this still aligned with original plan?"
    - [ ] "What's blocking progress?"
    - [ ] "Should this be paused or archived?"

**Optional/Future:**

- [ ] Deadline support (opt-in per project)
    
- [ ] Export/import project data
    
- [ ] Integration with git repos (commit history as timeline events)
    
- [ ] AI-generated progress summaries
    
- [ ] Voice note capture for ideas
    

## User Interface Mockup (Conceptual)

### Dashboard View

Collapse

Run

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

›

╔═══════════════════════════════════════════════════════════════╗

║ ProjectBaseX \[+ New Idea\] ║

╠═══════════════════════════════════════════════════════════════╣

║ ║

║ NEEDS ATTENTION (2) ║

║ ┌─────────────────────────────────────────────────────────┐ ║

║ │ 🔴 BBS Museum - debugging telnet connections │ ║

║ │ Last activity: 3 days ago │ ║

║ │ │ ║

║ │ 🟡 Neverwhere Game - paused, direction unclear │ ║

║ │ Last activity: 2 weeks ago │ ║

║ └─────────────────────────────────────────────────────────┘ ║

║ ║

║ ACTIVE (3) ║

║ ┌─────────────────────────────────────────────────────────┐ ║

║ │ 🟢 ProjectBaseX - 20% complete, in planning │ ║

║ │ 🟢 Dashboard Cosmetic Updates - 90% complete │ ║

║ │ 🟢 Local Server - mostly done, will expand │ ║

║ └─────────────────────────────────────────────────────────┘ ║

║ ║

║ IDLE - REVIEW (5) \[View All: 36\] ║

║ ║

║ RECENT IDEAS (3) \[View All: 12\] ║

║ ║

╚═══════════════════════════════════════════════════════════════╝

### Project Detail View

Collapse

Run

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

›

╔═══════════════════════════════════════════════════════════════╗

║ ← Back to Dashboard BBS Museum \[⚙ Settings\] ║

╠═══════════════════════════════════════════════════════════════╣

║ Status: needs-attention │ Category: code ║

║ Created: 2024-09-15 │ Modified: 3 days ago ║

║ Path: ~/Projects/Code_Projects/bbs-museum/ ║

╠═══════════════════════════════════════════════════════════════╣

║ \[Overview\] \[Notes\] \[AI Chat\] \[Timeline\] ║

╠═══════════════════════════════════════════════════════════════╣

║ ║

║ ORIGINAL PLAN ║

║ Create a working museum of 12 DOS BBS systems from the ║

║ 1980s/90s, fully functional with modern telnet access. ║

║ ║

║ CURRENT STATUS ║

║ Stuck on telnet connection integration. Claude Code has ║

║ been trying various approaches but burning tokens without ║

║ clear progress. Need to research specific retro protocols. ║

║ ║

║ NOTES (5) \[+ Add Note\] ║

║ - WWIV system configured and working ║

║ - Renegade having character encoding issues ║

║ - Found old documentation on BBSDocumentary.com ║

║ ║

║ \[Ask AI for help\] \[Mark as Paused\] \[Change Status\] ║

║ ║

╚═══════════════════════════════════════════════════════════════╝

## AI Integration Architecture

### Context Building

For each AI interaction, build context package:

Collapse

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

›

{

"project": {

"name": "BBS Museum",

"status": "needs-attention",

"original_plan": "...",

"current_notes": \[...\],

"recent_activity": \[...\]

},

"conversation_history": \[...last 10 messages\],

"file_context": {

"directory": "~/Projects/Code_Projects/bbs-museum/",

"key_files": \[...\],

"recent_changes": \[...\]

},

"user_request": "I'm stuck on telnet integration",

"interaction_mode": "stuck"

}

### AI Behavior Prompts (System Messages)

**Base System Prompt:**

Collapse

Run

Save Copy

99

1

2

3

4

5

6

7

8

9

10

11

12

13

14

›

You are an AI collaborator embedded in ProjectBaseX, a project management

tool for solo developers. Your role is to be an analytical partner, not

a yes-man assistant.

Core behaviors:

\- Ask clarifying questions before making assumptions

\- Challenge plans that seem incomplete or risky

\- Provide structured approaches with identified tradeoffs

\- STOP trial-and-error: if you don't have enough information, ask for it

\- Remember this is one person working alone - be concise and actionable

Current project context: \[injected\]

Conversation history: \[injected\]

User's request: \[injected\]

**Mode-Specific Additions:**

*Planning Mode:*

Collapse

Run

Save Copy

9

1

2

3

4

5

6

›

The user is in planning phase. Help them develop a detailed specification

before writing code. Ask about:

\- What defines "done" for this project?

\- What are the technical risks?

\- What could cause this to stall?

\- Is the scope realistic for a solo developer?

*Stuck Mode:*

Collapse

Run

Save Copy

9

1

2

3

4

5

6

›

The user is stuck on a technical problem. DO NOT immediately suggest

solutions. Instead:

1\. Ask diagnostic questions to understand the actual problem

2\. Identify if this is a knowledge gap, tool limitation, or approach issue

3\. If it's niche/retro tech, acknowledge limited training data

4\. Suggest research steps rather than trial-and-error coding

*Review Mode:*

Collapse

Run

Save Copy

9

1

2

3

4

5

›

Summarize the current state of this project. Include:

\- Progress since last review

\- Alignment with original plan

\- Potential blockers ahead

\- Honest assessment: should this continue, pause, or archive?

## Security & Privacy

- **All data local** - no cloud sync unless explicitly added later
- **API keys** - stored in config file, not in database
- **Conversation history** - user owns all data, can export/delete
- **File system access** - read-only by default, explicit write permissions

## Testing Strategy

**Phase 1:**

- Manual testing of CRUD operations
- Test directory scanning with Nick's actual ~/Projects/ structure
- Verify dashboard accurately reflects project states

**Phase 2:**

- Test AI context building with real project data
- Verify token usage tracking
- Test conversation history retention across sessions

**Phase 3:**

- Test recommendation engine with various project portfolios
- Validate timeline accuracy
- User testing with Nick's actual workflow

## Success Metrics

**Adoption:**

- Daily use for 2+ weeks without abandoning
- Replaces Joplin for project notes
- Becomes first place Nick checks in the morning

**Effectiveness:**

- Measurable reduction in "needs-attention" status duration
- Fewer projects in "idle-review" status
- User reports better decision-making with AI collaboration

**Learning:**

- Nick can explain Claude Code best practices
- Blog posts written documenting the process
- Portfolio-ready project demonstrating AI integration

* * *

**Last Updated:** 2025-01-XX
