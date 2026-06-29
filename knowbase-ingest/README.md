# knowbase-ingest

Automate the full ingest pipeline for a [Karpathy-style](https://x.com/karpathy/status/1876077186808557992) personal knowledge base:
copy a source file into `raw/`, extract its content, create a structured wiki page with internal links,
update `processed-sources.json` and `INDEX.md`, and verify integrity — all in one command.

## What It Does

1. **Validates** the knowledge base structure (`raw/`, `wiki/`, `INDEX.md`, `processed-sources.json`)
2. **Copies** the source file into `raw/` and checks for duplicates
3. **Extracts** content — PDF (visual), Markdown, text, PPTX, DOCX, HTML
4. **Discovers** related wiki pages via two-phase search (category scan + keyword grep)
5. **Creates** a wiki page (`create` mode) or integrates into an existing one (`merge` mode)
6. **Updates** `processed-sources.json` atomically (single read-modify-write)
7. **Updates** `INDEX.md` with the new entry
8. **Verifies** links, JSON validity, and index consistency
9. **Reports** a structured ingest summary

## Triggers

- "add this to my knowledge base"
- "ingest this file / document"
- "process this into wiki"
- "add to knowbase" / "add to kb"
- "create wiki page for this"
- "store in raw and create wiki"
- "karpathy wiki ingest"
- "process raw file"

## Platform

**Claude Code** (CLI). Also works with any agent that has file system access.

## Setup

### Option 1: Manual install (Claude Code)

```bash
# Clone or download this skill into your Qoder skills directory
cp -r knowbase-ingest-generic ~/.qoder/skills/knowbase-ingest-generic
```

Then activate it in Claude Code with `/knowbase-ingest-generic` or just describe what you want to do.

### Option 2: npx install

```bash
npx skills add <your-github-handle>/<your-repo> --skill knowbase-ingest-generic
```

### Prerequisites

Your knowledge base must follow the Karpathy three-folder structure:

```
your-kb/
├── raw/                          # source files (append-only)
├── wiki/
│   ├── INDEX.md                  # category index
│   ├── processed-sources.json    # processing state tracker
│   └── *.md                      # wiki pages
├── outputs/                      # AI-generated analyses and Q&A
└── CLAUDE.md                     # schema file (see references/schema-guide.md)
```

To initialize a fresh knowledge base:

```bash
mkdir -p my-kb/{raw,wiki,outputs}
echo '{}' > my-kb/wiki/processed-sources.json
# Create wiki/INDEX.md and CLAUDE.md — see references/schema-guide.md for templates
```

## Usage

```
Add raw/my-article.pdf to the knowledge base at ~/my-kb
```

```
Ingest raw/research-paper.pdf in merge mode — integrate into the existing RAG page
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `KNOWBASE_PATH` | *(ask if not clear from context)* | Root directory of the knowledge base |
| `SOURCE_FILE` | *(required)* | File to ingest; can be in `raw/` already or elsewhere |
| `MODE` | `create` | `create` = new wiki page; `merge` = integrate into existing |

## Reference Files

| File | Contents |
|------|----------|
| `references/wiki-page-template.md` | Standard wiki page format, field rules, worked example |
| `references/edge-cases.md` | 15 edge case scenarios with handling instructions |
| `references/schema-guide.md` | How to write and evolve your `CLAUDE.md` schema file |

## Key Design Principles

**raw/ is append-only** — source files are never modified, moved, or deleted. Processing state lives in `processed-sources.json`, not in file locations.

**Schema is the core asset** — `CLAUDE.md` / `AGENTS.md` is more important than any individual wiki page. Every time AI output quality drifts, fix the schema rather than editing wiki pages manually.

**Links are validated before writing** — every `[[slug]]` is verified against an existing `wiki/slug.md` file before being written. No broken links.

**Atomic JSON updates** — `processed-sources.json` is always updated in a single read-modify-write. Never two separate writes.
