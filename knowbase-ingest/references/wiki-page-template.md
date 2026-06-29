# Wiki Page Template

## Standard Template

```markdown
# Page Title

> **Source**: raw/original-filename.ext
> **Author**: Author or organization (if known)
> **Created**: YYYY-MM-DD
> **Category**: {emoji} Category Name

---

## Core Insight

1–2 paragraphs summarizing the document's most important ideas, findings, or arguments.

---

## {Section Based on Source Structure}

Key content extracted from the source, preserving important data, frameworks, code, or quotes.
Inline `[[related-page]]` links where relevant — only link to pages that actually exist.

### Sub-section (if needed)

Further detail...

---

## {Additional Sections as Needed}

...

---

## Related Pages

- [[existing-page-1]] — one-line explanation of the connection
- [[existing-page-2]] — one-line explanation of the connection
- [[existing-page-3]] — one-line explanation of the connection
```

---

## Field Rules

### Header Block

| Field | Required | Format |
|-------|----------|--------|
| Title | Yes | `# Title` — concise, descriptive |
| Source | Yes | `> **Source**: raw/filename.ext` — exact filename in raw/ |
| Author | Optional | `> **Author**: Name` — omit if unknown |
| Created | Yes | `> **Created**: YYYY-MM-DD` |
| Category | Yes | `> **Category**: {emoji} Name` — must match a category in INDEX.md |

### Internal Links

- Format: `[[page-slug]]` — corresponds to `wiki/page-slug.md` (no `.md` extension)
- **Always validate** the target `.md` file exists before writing the link
- Works with any filename convention: `[[rag-systems]]`, `[[my-notes-on-agents]]`
- Can appear inline in body text or collected in the "Related Pages" section

### Related Pages Section

- Place at the end of the page, separated by `---`
- Each entry: `- [[slug]] — one-sentence explanation of why these pages are related`
- Target: 3–8 links. Zero links is acceptable when starting out.

### Content Organization

- Use `##` for main sections
- Use `###` for sub-sections
- Tables use standard Markdown syntax
- Code blocks use fenced syntax with language tag
- Lists: `-` for unordered, `1.` for ordered

---

## Worked Example

```markdown
# The Case for Flat Knowledge Structures

> **Source**: raw/why-flat-wins-over-hierarchy.pdf
> **Author**: Jane Smith
> **Created**: 2025-03-15
> **Category**: 📖 Knowledge Management

---

## Core Insight

Hierarchical folder structures fail as knowledge bases grow because categories
become ambiguous and documents span multiple categories. A flat structure with
internal links scales better because the link graph self-organizes around actual
usage patterns rather than an imposed taxonomy.

---

## Why Hierarchy Fails at Scale

The author analyzed 12 companies that migrated from nested folder structures to
flat wikis. Key findings:

| Metric | Hierarchical | Flat + Links |
|--------|-------------|-------------|
| Retrieval time (avg) | 4.2 min | 1.1 min |
| Orphaned documents | 31% | 4% |
| Cross-topic discovery | Low | High |

The core problem: every categorization decision made at creation time becomes a
liability as the knowledge base evolves. See [[link-rot-and-knowledge-decay]] for
related analysis on how stale links compound this problem.

---

## The Three-Folder Structure

The recommended structure for AI-assisted knowledge bases:

```
kb/
├── raw/    — source files, never modified
├── wiki/   — structured wiki pages, AI-maintained
└── outputs/ — answers, analyses, discoveries
```

This separates concerns: raw/ preserves fidelity, wiki/ provides structure,
outputs/ captures the value derived. Discussed further in [[knowledge-base-setup]].

---

## Related Pages

- [[knowledge-base-setup]] — how to initialize the three-folder structure
- [[link-rot-and-knowledge-decay]] — why links degrade and how to prevent it
- [[ai-wiki-maintenance]] — automating consistency checks across flat wikis
```

---

## Image-Heavy Documents

If the source document is image-dense (scanned PDFs, slide decks with minimal text), add a notice at the top:

```markdown
> ⚠️ **Extraction Note**: This document is image-heavy. Text extraction may be
> incomplete. Key diagrams or charts should be manually added later.
```

Also add a `note` field in `processed-sources.json`:
```json
"note": "image-heavy document, text extraction incomplete"
```
