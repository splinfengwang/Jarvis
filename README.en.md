<p align="center">
  <h1 align="center">Jarvis</h1>
  <p align="center"><strong>An opinionated runtime for long-term agentic work.</strong></p>
  <p align="center">Turn LLM conversations into a recoverable, verifiable, reusable work knowledge system.</p>
  <p align="center">
    <a href="README.md">中文</a> · <a href="README.en.md">English</a>
  </p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-%E2%89%A53.10-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</p>

<p align="center">
  <img src="assets/jarvis-hero-persona-light.png" alt="Anthropomorphic Jarvis work-memory assistant illustration" width="100%">
</p>

---

## Positioning

Jarvis is an Agent Runtime for long-term work.

It is not another chatbot, not a prompt bundle, and not a RAG wrapper around a document folder. Its goal is lower in the stack: give an LLM an executable work discipline, so it knows what to read, what to record, what it may write, what must be confirmed, and which conclusions are allowed to enter long-term knowledge.

If a normal LLM session is one-off intellectual outsourcing, Jarvis upgrades it into a persistent work memory system:

```text
Conversation -> Topic -> Evidence -> Knowledge -> Reuse
```

Every discussion is placed into the same chain: context can be recovered, conclusions can be traced, knowledge can be reused, and writes can be audited.

---

## Product Thesis

The bottleneck of LLM work is shifting from "can it answer?" to "can it collaborate reliably over time?"

Jarvis is built on a simple judgment: a personal work knowledge base should not depend on manual cleanup after every conversation, and it should not allow an agent to rewrite knowledge without governance. A better shape is:

> The agent captures knowledge under constraints, the human keeps decision authority, and the filesystem preserves the auditable state.

Jarvis is therefore not designed for invisible automation. It is designed for a more reliable collaboration structure:

- For the agent: routing, retrieval, write, and extraction discipline
- For the human: decision authority only when future judgment is affected
- For the knowledge base: every knowledge item has source, status, location, and reuse semantics
- For future sessions: "continue from last time" becomes an executable action, not a memory hallucination

---

## Design Principles

### 1. Conversation is the interface, not the memory

Normal LLM collaboration often stops at "we talked about it." Jarvis does not try to save chat logs as the final artifact. It extracts what will matter later into more stable assets:

- Terms and concepts, so future discussions do not restart from definitions
- Relationships and rules, so workflows and systems remain understandable
- Judgments and decisions, so tradeoffs and abandoned paths are preserved
- Open questions, so unknowns are not reused as facts
- File-processing outputs, such as structured summaries of PDFs, slides, OCR, web pages, and Confluence documents

The knowledge base is not an archive created after work. It is a judgment system that grows during work.

### 2. Memory without governance is liability

The core of Jarvis is not "make the agent do more." It is "make the agent respect boundaries before it acts":

- Facts, evidence, inferences, preferences, and open questions must be distinguished
- Project knowledge must be looked up through `知识库/wiki索引.md` before broad search
- OpenViking or memory search results are recall hints, not facts
- Content writes and high-risk writes require confirmation
- Closing a Topic does not automatically ingest knowledge; ingestion requires an Evidence Pack and confirmation checklist

This discipline is enforced through Core rules, Skills, Hooks, and scripts, not just agent self-control.

### 3. Topic is the atomic unit of long-term work

Jarvis models every durable work stream as a Topic. A Topic is not just a folder. It carries:

- Scope
- Last action
- Next action
- Confirmed facts
- Current inferences
- Pending decisions
- Open questions
- Linked sessions
- Key outputs
- Extraction state

So when the user says "continue from last time," the agent should not answer from memory. It should restore the Topic: read the dashboard, read the snapshot, read the index, and report what was done, what comes next, and what was blocked.

### 4. Knowledge should stay inspectable

Jarvis defaults to Markdown and the filesystem instead of pushing everything into an opaque vector store.

That is a deliberate tradeoff:

- Upside: humans can read it, Git can diff it, mistakes can be rolled back, links can be traced
- Cost: indexes, naming, status, and confirmation flows must be maintained

Jarvis accepts that cost because long-term work knowledge needs explainability and governance more than one-off semantic similarity.

---

## How It Differs

| Question | Typical chat / RAG / agent framework | Jarvis tradeoff |
|---|---|---|
| What remains after a session? | Chat history or vector chunks | Topic snapshots, evidence packs, confirmed knowledge items |
| How does the agent know what to read? | Similarity search or free exploration | Router + Context Pack + wiki-index discipline |
| Can memory results be used as facts? | Often blended into answers | Only as leads; source confirmation is required |
| How are writes controlled? | Allow or deny tool calls | Record / content / high-risk write classification |
| How does knowledge enter the long-term base? | Auto-summary or manual cleanup | Evidence Pack -> grouped confirmation -> indexed ingestion |
| How does multi-session work resume? | Model memory or user recap | Dashboard + Topic Capsule + linked sessions |
| What happens when something is wrong? | Hard to trace | Markdown + Git + backlinks + source fields |

Jarvis is not about making the agent "chat better." It turns the agent from a temporary assistant into a governed long-term collaborator.

---

## Product Model

Jarvis is composed of eight object types.

| Object | Purpose | Typical location |
|---|---|---|
| Core | Agent rules: routing, retrieval, write decisions, fact discipline, safety boundaries | `jarvis/core/` |
| Skill | Triggerable workflows: create/resume/close Topic, extract/ingest knowledge, Roundtable review | `jarvis/skills/` |
| Hook | Inject Core, guard writes, and checkpoint state in the Claude Code lifecycle | `adapters/claude/hooks/` |
| Topic | State container for a durable work stream | `platform-ops/topics/<Topic>/` |
| Knowledge | Confirmed or pending knowledge assets, layered as L1-L4/F | `知识库/`, `业务/` |
| Catalog | Project content-directory registry, including read/write policy | `jarvis.yaml` |
| Persona | Reusable review roles for Roundtable reviews | `jarvis/personas/`, `jarvis.yaml` |
| Backend | Memory retrieval backend: default file search, optional OpenViking semantic search | `jarvis/backends/` |

### Execution Layers

Jarvis does not turn everything into a fully automated background service. It separates deterministic operations from judgment-heavy operations:

| Layer | Responsibility | Examples |
|---|---|---|
| Hook automation | Session startup, pre-write guard, pre-compact checkpoint | Inject Core, block high-risk writes |
| CLI / Script deterministic execution | Verifiable file structures and state sync | Create Topic, update dashboard, generate Evidence Pack |
| Skill orchestration | Agent reads, judges, explains, and proposes through a workflow | Extraction, ingestion, Roundtable, catalog registration |
| Human confirmation | Content judgment, knowledge confirmation, high-risk authorization | Ingest or not, merge terms or not, adopt a proposal or not |

The split is intentional: scripts handle deterministic work; the agent and the human handle judgment. This avoids fast automation that silently corrupts long-term knowledge.

---

## Core Capabilities

### 1. Runtime baseline injection at session start

After installation, Jarvis uses Claude Code hooks to inject Core rules at session start.

Startup chain:

```text
Claude Code SessionStart
  -> jarvis-core-inject.sh
  -> read JARVIS_CORE.md
  -> read project jarvis.yaml
  -> inject plugin modules
  -> inject semantic path mapping
  -> inject knowledge snapshot
  -> agent receives the work baseline for this session
```

Two additional hooks support the runtime:

- `jarvis-write-guard.sh`: protects file writes and high-risk Bash commands
- `jarvis-compact-save.sh`: asks the agent to save runtime state before context compaction

### 2. Natural-language routing into workflows

Users do not need to remember commands. They can trigger workflows with natural language:

| User says | Jarvis should route to |
|---|---|
| "What's current?" / "What are we working on?" | `jarvis-status` |
| "Continue X" / "resume last time" | `jarvis-topic-resume` |
| "Open a Topic" | `jarvis-topic-create` |
| "Pause this" / "save this state" | `jarvis-topic-freeze` |
| "Close this Topic" | `jarvis-topic-close` |
| "Extract this Topic" | `jarvis-knowledge-extract` |
| "Confirm group A" / "ingest these items" | `jarvis-knowledge-ingest` |
| "Record this follow-up" | `jarvis-followup-sync` |
| "By the way..." | `jarvis-fragment-triage` |
| "Search Confluence" | `jarvis-confluence-read` |
| "Turn this OCR result into a document" | `jarvis-file-process` |
| "Review from multiple angles" | `jarvis-roundtable` |
| "Create a review persona" | `jarvis-persona-create` |
| "Create a directory for X going forward" | `jarvis-catalog-register` |

The router first identifies intent and side effects, then decides what to read, whether to write, and whether confirmation is required.

### 3. Topic lifecycle management

Topic is the primary work unit in Jarvis.

Standard structure:

```text
platform-ops/topics/YYYYMMDD_short-topic-title/
├── 索引.md
├── _上下文快照.md
├── _准入检查单.md
├── 讨论记录.md
├── 参考资料/
├── 过程稿/
└── 定稿/
```

Status model:

| Status | Meaning |
|---|---|
| `doing` / `[🟢 Doing]` | Currently active |
| `paused` / `[🟡 Paused]` | Paused, recoverable |
| `blocked` / `[🔴 Blocked]` | Blocked by external dependency |
| `pending_extraction` / `[📋 待萃取]` | Work completed, waiting for knowledge extraction |
| `done` / `[⚪ Done]` | Extracted and archived |

Closing a Topic does not automatically ingest knowledge. It moves the Topic to "pending extraction." Work completion and knowledge confirmation are separate events.

Topic state changes sync across:

- Topic body: `索引.md`, `_上下文快照.md`, `讨论记录.md`
- Global entry points: `platform-ops/仪表盘.md`, `platform-ops/log.md`
- External protection: Git checkpoints when needed

### 4. Context Pack: read only what matters

Jarvis discourages scanning the whole project every time.

Different tasks require different reading depth:

| Scenario | Primary context |
|---|---|
| Status query | Dashboard, active Topic snapshots |
| Topic resume | Dashboard, target Topic snapshot, Topic index |
| New work stream | wiki index, dashboard, relevant business docs |
| Knowledge extraction | Topic core files, linked session JSONL, source files |
| Deep trace | Knowledge body, Topic records, Confluence source, JSONL |

The principle: context should be explainable, sufficient, and source-traceable, not merely large.

### 5. Evidence Pack before ingestion

Knowledge extraction is not "summarize the chat."

`jarvis-knowledge-extract` turns a Topic and its sources into an Evidence Pack and a confirmation checklist:

- A. Fast-confirmable
- B. Needs decision
- C. Needs verification or arbitration
- D. Recommended not to ingest
- E. File-processing outputs
- G. Complete Topic documents

Every candidate item must have source, confidence, intended usage, and an ingestion recommendation. Claims without sources do not enter the checklist.

Only after confirmation does `jarvis-knowledge-ingest` write into the knowledge base and sync `wiki索引.md`, `术语索引.md`, and the operation log.

### 6. L1-L4/F knowledge layers

Jarvis splits knowledge into five layers:

| Layer | Content | Recommended carrier |
|---|---|---|
| L1 | Terms and concept definitions | `知识库/术语/` |
| L2 | Relationships, rules, workflows | `业务/<domain>/` |
| L3 | Judgments, decisions, tradeoff rationale | `业务/<domain>/` or Topic final docs |
| L4 | Open questions and unresolved issues | Topic / analysis docs |
| F | File-processing outputs, such as structured OCR/PDF/PPT summaries | `业务/<domain>/` |

The layering is not cosmetic. It controls reuse risk: definitions can be reused frequently, judgments must carry context, and open questions must not become facts.

### 7. Multi-persona Roundtable review

Jarvis ships with five built-in personas:

- `pm-analyst`: requirement completeness and priority
- `design-reviewer`: interaction flow and user experience
- `edge-case-hunter`: boundary conditions and extreme cases
- `technical-auditor`: technical feasibility and architectural fit
- `medical-safety`: medical safety and parameter provenance

`jarvis-roundtable` extracts context from the current Topic, spawns independent sub-agents with different personas, and lets the main agent synthesize consensus, disagreement, and priority recommendations.

Users can also create project-level personas through `jarvis-persona-create`.

### 8. Catalog and plugin extension

Catalogs answer "which content directories exist, and which ones may Jarvis write to?"

```yaml
catalogs:
  ProductSpecs:
    writable: true
    description: "Confirmed product and design documents"
  ExternalSources:
    writable: false
    description: "Read-only reference material"
```

Plugins answer "what domain-specific safety boundaries should be injected?"

The built-in medical plugin can inject:

- Domain safety rules
- Multi-perspective validation
- Delivery checklist
- Medical knowledge taxonomy

Enable it in a project:

```yaml
plugins:
  - medical-safety
```

### Install platform adapters

Jarvis can prepare adapters for Claude Code, Reasonix, and Codex:

```bash
# Claude Code global hooks and skills
jarvis install --target claude

# Reasonix native config
jarvis install --target reasonix

# Codex skills
jarvis install --target codex

# Install all global adapters
jarvis install --target all
```

`jarvis install` without `--target` auto-detects from the current project (`reasonix.toml` / `.reasonix/` -> Reasonix, `.codex/` -> Codex, otherwise Claude). The same target can be selected during npm postinstall:

```bash
JARVIS_TARGET=all npm install -g jarvis-agent
```

The installer is safe to rerun during upgrades:

- Claude Code: relinks stale Jarvis skill/hook symlinks and replaces old Jarvis hook commands.
- Reasonix: writes native `config.toml` / prompt wiring and removes legacy Jarvis hooks from `~/.reasonix/settings.json`.
- Codex: refreshes global skill links; project bootstrap still comes from `AGENTS.md`.

For an existing project:

```bash
jarvis upgrade ~/my-project
jarvis install --target all
jarvis init --sync ~/my-project
```

Core rule upgrades are a two-step process: upgrade the framework and global adapters first, then run `jarvis init --sync <project>` for each existing project. Running only `upgrade` / `install` does not refresh an already embedded `AGENTS.md` / `REASONIX.md` runtime block.

`--sync` updates `jarvis.yaml` version, `jarvis_home`, and missing `platform`, refreshes `AGENTS.md` / `REASONIX.md` / `reasonix.toml`, and removes old project-level Jarvis hooks from `.claude/settings.json`. If npm / pipx has already upgraded the framework, start from `jarvis install --target all`.

---

## Daily Usage

### Initialize a project

```bash
npm install -g jarvis-agent

# Default Claude Code project
jarvis init ~/my-project

# For one project shared across Claude Code, Reasonix, and Codex:
jarvis install --target all
jarvis init ~/shared-project --platform all

# Start Claude Code in the initialized project
cd ~/my-project
claude
```

With `--platform all`, Jarvis creates:

- `CLAUDE.md` for Claude Code
- `AGENTS.md` for Codex / Reasonix
- `REASONIX.md` as the Reasonix runtime prompt
- `reasonix.toml` as the project-level Reasonix bridge
- `jarvis.yaml` as the shared cross-platform config

If global Claude Code hooks already exist, `jarvis init` skips the project-level `.claude/` adapter to avoid duplicate hook execution. If global hooks are absent, the project receives a local `.claude/` adapter.

Typical project structure:

```text
my-project/
├── jarvis.yaml
├── CLAUDE.md
├── 知识库/
│   ├── wiki索引.md
│   └── 术语/
│       └── 术语索引.md
├── 业务/
├── platform-ops/
│   ├── 仪表盘.md
│   ├── log.md
│   └── topics/
└── .claude/
    ├── skills/
    ├── hooks/
    └── settings.json      # only when global Claude hooks are absent
```

### Start a new work stream

Tell the agent:

```text
Open a Topic: service request management.
Scope: map the full workflow from request registration to dispatch.
```

Jarvis should:

1. Check whether a Topic is justified
2. Produce a dry-run creation plan
3. Create the Topic core files and standard subdirectories
4. Update the dashboard
5. Record the current session source

### Work through drafts and outputs

Drafts go under:

```text
platform-ops/topics/<Topic>/过程稿/
```

Confirmed final outputs go under:

```text
platform-ops/topics/<Topic>/定稿/
```

Naming conventions:

```text
YYYYMMDD-topic-document-type.md
YYYYMMDD-topic-document-type-v0.1.md
```

### Pause and resume

Pause:

```text
Save this for now. Next step is to cover exception flows.
```

Resume:

```text
Continue the service request management Topic.
```

Jarvis should report:

1. Where the work stopped
2. What should happen next
3. What was blocked or pending decision

### Close and extract

Close a Topic:

```text
Close this Topic and move it to pending extraction.
```

Extract knowledge:

```text
Extract this Topic.
```

Confirm ingestion:

```text
Confirm group A, keep group C pending verification, store G1 independently.
```

Jarvis boundary: close does not extract automatically; extraction does not ingest automatically; ingestion requires explicit confirmation scope.

### Query existing knowledge

Ask directly:

```text
How did we define service request previously?
```

Jarvis should read `知识库/wiki索引.md` or `知识库/术语/术语索引.md` first, then read the matched source files. If it degrades to search, it must state the index gap and record that gap in the wiki index.

---

## CLI

| Command | Purpose |
|---|---|
| `jarvis init <path>` | Initialize a project skeleton |
| `jarvis init --sync <path>` | Sync an existing project version and clean duplicated project-level hooks |
| `jarvis doctor <path>` | Check installation, skills, hooks, indexes, dashboard, and backend |
| `jarvis status <path>` | Show Jarvis project configuration status |
| `jarvis upgrade [path]` | Upgrade the framework based on git tags |
| `jarvis uninstall <path>` | Remove Jarvis from a project while keeping user data by default |
| `jarvis bootstrap` | Globally register only the `/jarvis-init` skill |
| `jarvis version` | Print the current version |

Offline install:

```bash
npm pack jarvis-agent
npm install -g ./jarvis-agent-x.y.z.tgz
jarvis init ~/my-project
```

Install from source:

```bash
git clone https://github.com/splinfengwang/Jarvis.git
cd Jarvis
pip install -e .
jarvis init ~/my-project
```

Verify installation:

```bash
jarvis doctor ~/my-project
```

---

## Built-in Skills

Jarvis currently ships with 19 built-in skills.

| Group | Skills |
|---|---|
| Project setup | `jarvis-init` |
| Topic lifecycle | `jarvis-topic-create`, `jarvis-topic-resume`, `jarvis-topic-freeze`, `jarvis-topic-close`, `jarvis-topic-organize` |
| Status and governance | `jarvis-status`, `jarvis-fragment-triage`, `jarvis-followup-sync` |
| Knowledge loop | `jarvis-knowledge-extract`, `jarvis-knowledge-ingest`, `jarvis-knowledge-feedback` |
| Files and sources | `jarvis-file-process`, `jarvis-confluence-read` |
| Analysis assets | `jarvis-analysis-thread` |
| Extension mechanisms | `jarvis-catalog-register`, `jarvis-persona-create`, `jarvis-roundtable` |
| Help | `jarvis-help` |

---

## Engineering Structure

```text
jarvis/
├── core/             # Core behavior rules and bootstrap
├── skills/           # 19 Jarvis skills
├── hooks/            # SessionStart / PreToolUse / PreCompact hooks
├── scripts/          # 17 executable maintenance scripts
├── references/       # Specs for Topic, knowledge, evidence, writes, plugins
├── templates/        # Project initialization templates
├── personas/         # Built-in review personas
├── plugins/          # Domain plugins
├── backends/         # file / openviking memory backends
└── research-cards/   # Notes on external systems and design influences
```

Key files:

| File | Purpose |
|---|---|
| `jarvis/core/JARVIS_CORE.md` | Compact runtime rules injected into sessions |
| `jarvis/core/JARVIS_CORE_FULL.md` | Full behavior spec and design details |
| `jarvis/core/JARVIS_BOOTSTRAP.md` | Manual bootstrap entry when Core was not auto-injected |
| `jarvis/references/topic-lifecycle.md` | Topic lifecycle and file naming rules |
| `jarvis/references/knowledge-model.md` | L1-L4/F knowledge model |
| `jarvis/references/evidence-pack-spec.md` | Evidence Pack format |
| `jarvis/references/write-permission.md` | Write-decision rules |

---

## Configuration

Project configuration lives in `jarvis.yaml`.

Minimal configuration:

```yaml
jarvis_version: "1.10.0"
jarvis_home: "/path/to/jarvis"

paths:
  knowledge_base: 知识库
  wiki_index: 知识库/wiki索引.md
  terms_dir: 知识库/术语
  terms_index: 知识库/术语/术语索引.md
  business_dir: 业务
  ops_dir: platform-ops
  dashboard: platform-ops/仪表盘.md
  log: platform-ops/log.md
  topics: platform-ops/topics

plugins: []
backend: file
```

Optional extensions:

```yaml
backend: openviking

catalogs:
  ProductSpecs:
    writable: true
    description: "Confirmed product and design documents"

personas:
  compliance-auditor:
    title: "Compliance Auditor"
    role: "Review proposals from a compliance and audit perspective"
```

---

## Boundaries and Tradeoffs

Jarvis deliberately keeps some "slow" steps:

- Use indexes instead of jumping directly to full-text search
- Use confirmation checklists instead of automatic ingestion
- Classify writes instead of allowing every file mutation
- Synchronize Topic state instead of relying only on chat context

These steps add short-term friction, but they buy recoverability, traceability, and governance for long-term work.

Current boundaries:

- Jarvis is not a model-calling framework and does not orchestrate providers
- Jarvis does not replace Git, Obsidian, Confluence, or OpenViking
- OpenViking is an optional recall layer, not a source of truth
- Roundtable depends on the current agent environment supporting sub-agents / task tools
- Confluence reading depends on local cookie configuration
- Domain plugins inject rules; they do not make domain decisions for the user

Jarvis also constrains answers: when project knowledge is involved, the agent should state confirmed sources, pending sources, inference basis, and proposal assumptions. A conclusion without provenance must not pretend to be a fact.

---

## Fit

Jarvis is especially suitable for:

- Long-running product discussions
- Continuous business knowledge-base maintenance
- Frequent cross-session context recovery
- Work that needs decision chains and tradeoff rationale preserved
- Multi-perspective agent-assisted reviews
- Domains such as healthcare, enterprise software, and B2B work where terms, boundaries, and evidence matter

It is not ideal for:

- One-off Q&A
- Casual conversation that should not be preserved
- Content generation where traceability does not matter
- Teams unwilling to maintain directories, indexes, and confirmation flows

---

## License

MIT
