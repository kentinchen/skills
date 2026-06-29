# Schema Guide: Writing CLAUDE.md / AGENTS.md

The schema file (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex/other agents)
is the most important artifact in a Karpathy-style knowledge base. It is more
valuable than any individual wiki page, because it is the persistent instruction set
that governs how the AI maintains the entire system.

> "If you think about it this way, the knowledge base is less a product of the LLM
> and more a product of Karpathy's instruction-writing — the LLM just executes at scale."

---

## Why the Schema Is the Core Asset

Without a schema file:
- The AI infers structure inconsistently across sessions.
- Wiki page quality degrades over time as style drifts.
- Link networks become fragmented.
- Maintenance is manual.

With a well-written schema file:
- Every new session starts with full context on how the knowledge base works.
- Quality is enforced by rules, not by memory.
- The AI can perform maintenance autonomously (link repair, deduplication, consistency checks).
- The human's only job is sourcing good material and asking the right questions.

**The schema evolves.** Every time you notice the AI producing output that doesn't match
your expectations, the fix is to improve the schema — not to edit the wiki page manually.

---

## Minimum Required Sections

### 1. Purpose Statement

One paragraph explaining what this knowledge base is for and who it serves.

```markdown
## Purpose

This knowledge base captures research, articles, and notes on [your topic].
It is maintained by an AI agent. The human provides source materials;
the AI extracts, links, and maintains the wiki.
```

### 2. Folder Structure

Describe each folder's role explicitly.

```markdown
## Folder Structure

- `raw/` — original source files, never modified or deleted
- `wiki/` — AI-maintained wiki pages (one .md file per topic)
- `outputs/` — AI-generated analyses, Q&A, and discovery reports
- `CLAUDE.md` — this file; the schema that governs AI behavior
```

### 3. Core Rules

The rules the AI must follow without exception.

```markdown
## Rules

1. Never modify files in raw/. It is append-only.
2. Always validate [[links]] before writing — confirm wiki/slug.md exists.
3. Update processed-sources.json with a single read-modify-write operation.
4. Prefer existing categories over creating new ones.
5. Wiki pages use flat structure + internal links. No sub-folders in wiki/.
```

### 4. Wiki Page Format

Either inline the template or reference the template file.

```markdown
## Wiki Page Format

See references/wiki-page-template.md for the standard format.

Every wiki page must have: title, source, created date, category, and a
"Related Pages" section at the bottom.
```

### 5. Category System

List your categories so the AI can always pick the right one.

```markdown
## Categories

Use these categories in wiki pages and INDEX.md. Create a new category only
if none of these fit.

| Emoji | Name | What goes here |
|-------|------|----------------|
| 📖 | Knowledge Management | How-to articles on building and maintaining knowledge systems |
| 🤖 | AI Agents | Agent frameworks, skills, autonomous systems |
| 🔍 | Search & Retrieval | RAG, vector search, retrieval evaluation |
| 🏗️ | Engineering Practice | Software architecture, tooling, best practices |
```

### 6. Processing State Definitions

Document the valid status values so the AI uses them correctly.

```markdown
## Processing States (processed-sources.json)

- `processed` — wiki page created, fully complete
- `analyzed_and_integrated` — content merged into an existing wiki page
- `template_created` — only a skeleton page exists; content not yet filled in
- `blocked` — file could not be processed (encrypted, empty, corrupt)
```

---

## Optional But Recommended Sections

### Slug Naming Convention

```markdown
## Slug Naming

Wiki filenames (slugs) should:
- Be lowercase with hyphens as word separators
- Preserve CJK characters as-is
- Omit file extensions
- Be concise but descriptive (3–7 words)

Examples: `rag-evaluation-methods`, `agent-self-evolution`, `知识库管理方法论`
```

### Maintenance Instructions

```markdown
## Maintenance Tasks

When asked to run maintenance, perform these checks:

1. **Broken links** — scan all wiki/*.md for [[slugs]] with no corresponding file
2. **Orphaned pages** — wiki pages with no incoming links (consider linking or deleting)
3. **Stale INDEX** — entries in INDEX.md that don't match actual wiki files
4. **Duplicate detection** — identify wiki pages with >80% content overlap
5. **JSON integrity** — validate processed-sources.json is well-formed
```

### Q&A and Analysis Instructions

```markdown
## Answering Questions

When asked a question about the knowledge base:

1. Search wiki/*.md for relevant pages using keywords.
2. Synthesize an answer drawing from multiple pages.
3. Save the answer to outputs/qa/{YYYY-MM-DD}-{topic}.md
4. Include: question, answer, sources (wiki pages used), confidence level.
```

---

## Schema Evolution: How to Improve Over Time

The schema is never "done." Treat it as a living document.

### When to update the schema

| Trigger | Schema fix |
|---------|-----------|
| AI creates wiki pages with inconsistent format | Add or tighten the format rules |
| AI uses wrong categories | Clarify category definitions or add examples |
| AI writes broken links | Reinforce the link validation rule |
| AI creates redundant pages | Add a deduplication check instruction |
| Maintenance misses something | Add that check to the maintenance section |
| New file type needs handling | Add extraction instructions for that type |

### Update process

1. Notice a quality gap in AI output.
2. Identify the missing or ambiguous rule.
3. Add or refine the rule in CLAUDE.md / AGENTS.md.
4. On the next session, verify the AI follows the new rule.
5. Iterate.

**Do not** manually fix wiki pages to compensate for a bad schema. Fix the schema and let the AI re-apply the rules.

---

## Starter Template

Copy this as your initial `CLAUDE.md`:

```markdown
# Knowledge Base Schema

## Purpose

This is a personal research knowledge base on [your topic]. Source materials
are in raw/. The wiki/ directory contains structured pages I maintain for you.
You maintain the wiki; I source the materials and ask questions.

## Folder Structure

- `raw/` — original files; never modify
- `wiki/` — one .md page per topic; you maintain these
- `outputs/` — your analyses and Q&A answers
- `CLAUDE.md` — this file

## Rules

1. Never modify or delete files in raw/.
2. Before writing any [[link]], confirm wiki/slug.md exists.
3. Update wiki/processed-sources.json using a single read-modify-write.
4. Keep wiki/ flat — no sub-folders.
5. Prefer existing categories over creating new ones.

## Wiki Page Format

Every page: title, source, created date, category, sections, related pages.
See the template in references/wiki-page-template.md.

## Categories

| Emoji | Name | Scope |
|-------|------|-------|
| *(add your categories here)* | | |

## Processing States

- `processed` — complete
- `analyzed_and_integrated` — merged into existing page
- `template_created` — skeleton only
- `blocked` — could not process
```

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| No schema file at all | Inconsistent output across sessions | Create CLAUDE.md before first ingest |
| Schema too vague | AI invents rules | Be specific: name formats, required fields, exact status values |
| Editing wiki pages manually to fix AI mistakes | Schema drift accelerates | Fix the schema rule instead |
| Never updating the schema | Quality degrades over time | Review after every 10–20 ingests |
| Mixing AI-library and personal notes | Provenance confusion | Keep them in separate vaults |
