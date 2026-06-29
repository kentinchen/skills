---
name: knowbase-ingest
description: >
  Ingest a source document into a Karpathy-style personal knowledge base:
  copy to raw/, extract content, create a wiki page with internal links,
  update processed-sources.json and INDEX.md, verify integrity.
  Triggers: "add this to my knowledge base", "ingest this file",
  "process this document into wiki", "add to knowbase", "create wiki page for",
  "knowledge base ingest", "store in raw and create wiki", "karpathy wiki ingest",
  "process raw file", "add source to kb"
---

# Knowbase Ingest

Automate the full ingest pipeline for a Karpathy-style knowledge base:
`raw/` → extract → `wiki/` → update metadata → verify.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `KNOWBASE_PATH` | *(ask user if not obvious from context)* | Root directory of the knowledge base |
| `SOURCE_FILE` | *(required — path to the file to ingest)* | File to ingest; may already be in `raw/` or elsewhere |
| `MODE` | `create` | `create` = new wiki page; `merge` = integrate into an existing wiki page |

---

## Step 1: Detect Environment

Verify the knowledge base project structure is intact:

```bash
KBPATH="<KNOWBASE_PATH>"
test -d "$KBPATH/raw"                          && echo "raw/ OK"   || echo "MISSING: raw/"
test -d "$KBPATH/wiki"                         && echo "wiki/ OK"  || echo "MISSING: wiki/"
test -f "$KBPATH/wiki/INDEX.md"                && echo "INDEX OK"  || echo "MISSING: wiki/INDEX.md"
test -f "$KBPATH/wiki/processed-sources.json"  && echo "JSON OK"   || echo "MISSING: wiki/processed-sources.json"
```

**Gate**: All 4 checks must pass. If any fail, stop and tell the user exactly what is missing. Do not proceed.

If `KNOWBASE_PATH` was not provided and cannot be inferred, ask the user for it before running the checks.

---

## Step 2: Copy / Confirm File in raw/

1. If the source file is already inside `raw/`, skip copying and note the filename.
2. Otherwise, copy the source file to `raw/`, preserving the original filename exactly.
3. **Duplicate check** — read `wiki/processed-sources.json` and look up the filename:
   - Status `processed`: warn the user, ask whether to skip or reprocess.
   - Intermediate status (`analyzed`, `template_created`, `content_extracted`): ask whether to resume from that state or restart.
   - Not present: continue normally.
4. Record the exact `raw/` filename; use it in all subsequent steps.

**Rule**: raw/ is append-only. Never rename, move, or modify files already in raw/.

---

## Step 3: Extract Source Content

Route by file extension:

| Extension | Method |
|-----------|--------|
| `.md`, `.txt` | Read directly with the Read tool |
| `.pdf` | Use the `pdf` skill (visual extraction); extract **one file at a time** — do NOT batch multiple PDFs in parallel (causes stream truncation) |
| `.pptx` | Use the `pptx` skill (markitdown or python-pptx) |
| `.docx` | pandoc or python-docx |
| `.html` | WebFetch or pandoc |

**Gate**: Content must be successfully loaded into context before proceeding. If extraction yields no usable text, report the error and stop.

---

## Step 4: Discover Related Wiki Pages (Two-Phase)

**Phase 1 — INDEX.md category scan**:
1. Read `wiki/INDEX.md`.
2. Based on the source content, identify the 1–3 most relevant categories.
3. List all pages under those categories as candidates.

**Phase 2 — Keyword grep**:
1. Extract 3–5 keywords from the source content (prefer: domain-specific nouns, technology names, organization names).
2. For each keyword, search `wiki/*.md` files for matches.
3. Merge results, deduplicate, rank by number of keyword hits.

**Compile final link list**: Combine Phase 1 and Phase 2 results; target 3–8 internal links.

**Link validation rule**: Before writing any `[[slug]]`, confirm that `wiki/slug.md` actually exists. Never write a link that points to a non-existent file.

If no related pages are found: create a zero-link wiki page — this is a valid state that maintenance scripts will resolve later.

---

## Step 5: Determine Category and Create Wiki Page

1. Read the existing category headings from `INDEX.md`.
2. Select the best-matching category. If none fits, create a new one (short name + descriptive emoji, following the existing style).
3. Generate a wiki filename slug:
   - Preserve CJK (Chinese/Japanese/Korean) characters
   - Replace spaces with hyphens
   - Remove other special characters (keep hyphens and CJK)
   - Check for slug conflicts; add a disambiguating suffix if needed
4. Create the wiki page following the template in `references/wiki-page-template.md`.

**MODE branch**:
- **create**: write `wiki/{slug}.md` as a new file.
- **merge**: read the target wiki page, integrate new content into the appropriate sections without duplicating existing content.

---

## Step 6: Update processed-sources.json

Use a single **read-modify-write** operation (e.g., python3 `json.load` → update → `json.dump`). Never write the JSON in two separate steps.

**create mode** entry:
```json
"filename.ext": {
  "processedDate": "YYYY-MM-DD",
  "linkedWikiPages": ["wiki/slug.md"],
  "status": "processed"
}
```

**merge mode** entry:
```json
"filename.ext": {
  "processedDate": "YYYY-MM-DD",
  "linkedWikiPages": ["wiki/existing-slug.md"],
  "status": "analyzed_and_integrated",
  "note": "Brief description of what was merged"
}
```

Also update the top-level `lastUpdated` field.

---

## Step 7: Update INDEX.md

1. Read the current `INDEX.md`.
2. Under the selected category, append: `- [[slug]] — brief description` (≤50 characters, descriptive — not "summary" or "category tag").
3. Increment the total file count by 1.
4. Update the last-modified date.
5. If Step 5 created a new category, add `### {emoji} {Category Name}` in the appropriate position.

---

## Step 8: Verify

1. **Link check**: For every `[[link]]` in the new wiki page, confirm `wiki/{link}.md` exists. Fix broken links immediately (remove or replace).
2. **JSON validation**: Confirm `processed-sources.json` is valid JSON.
3. **INDEX consistency**: Confirm the new entry appears under the correct category.

If any check fails, fix it before reporting success.

---

## Step 9: Report

Output a structured summary:

```
## Ingest Complete

| Item | Value |
|------|-------|
| Source file | raw/filename.ext |
| Wiki page | wiki/slug.md |
| Category | {emoji} Category Name |
| Internal links | N ([[link1]], [[link2]], ...) |
| Status | processed |
| Broken links | 0 |

### Actions Taken
1. Copied source file to raw/
2. Extracted content ({method})
3. Created wiki page ({N} sections)
4. Updated processed-sources.json
5. Updated INDEX.md
6. Verification passed
```

---

## Core Constraints

- **raw/ is append-only**: Source files in raw/ are never moved, renamed, or modified. This is the foundation of the entire system's traceability.
- **Validate links before writing**: Every `[[slug]]` must correspond to an existing `wiki/slug.md`. No link is written speculatively.
- **Single write for JSON**: processed-sources.json updates are always one atomic read-modify-write. Never issue two separate write operations.
- **Category reuse first**: Always prefer an existing category. Creating a new category is a last resort.
- **Schema is the core asset**: The knowledge base's `CLAUDE.md` / `AGENTS.md` file is more important than any individual wiki page. See `references/schema-guide.md` for how to write and maintain it.

## Reference Files

- `references/wiki-page-template.md` — Standard wiki page format, field rules, and a worked example
- `references/edge-cases.md` — Handling for duplicate files, broken extraction, slug conflicts, large files, and 10+ other scenarios
- `references/schema-guide.md` — How to write and evolve the `CLAUDE.md` / `AGENTS.md` schema file for a new knowledge base
