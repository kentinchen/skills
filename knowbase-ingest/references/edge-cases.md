# Edge Cases

Handling guide for uncommon but important scenarios in the knowbase-ingest workflow.

---

## Scenario Index

| # | Scenario | Severity | Blocking? |
|---|----------|----------|-----------|
| 1 | File already in raw/ and fully processed | ⚠️ Warning | No — ask user |
| 2 | File in raw/ with intermediate status | ⚠️ Warning | No — ask user |
| 3 | No related wiki pages found | ℹ️ Info | No |
| 4 | Content highly overlaps an existing wiki page | ⚠️ Warning | No — suggest merge |
| 5 | Image-heavy or scan-only document | ℹ️ Info | No |
| 6 | Filename contains special characters | ⚙️ Auto | No |
| 7 | No matching category exists | ⚙️ Auto | No |
| 8 | processed-sources.json is malformed | 🔴 Error | Yes |
| 9 | INDEX.md is malformed | 🔴 Error | Yes |
| 10 | Source file is empty or unreadable | 🔴 Error | Yes |
| 11 | Same filename, different content already in raw/ | ⚠️ Warning | No — ask user |
| 12 | Very large document (200+ pages / 60+ slides) | ℹ️ Info | No |
| 13 | Mixed-language document | ⚙️ Auto | No |
| 14 | Password-protected or encrypted file | 🔴 Error | Yes |
| 15 | Generated slug conflicts with existing wiki page | ⚠️ Warning | No — auto-disambiguate |

---

## Detailed Handling

### 1. File already processed

**Detection**: `processed-sources.json` contains the filename with `status: "processed"`.

**Action**:
1. Warn: `⚠️ This file was already processed on {processedDate}. Linked wiki page: [[slug]]`
2. Ask the user to choose:
   - **Skip** — report the existing wiki page and stop.
   - **Reprocess** — overwrite the wiki page content (raw/ file stays untouched).
   - **Append** — run in merge mode to add new content to the existing wiki page.

### 2. File with intermediate status

**Detection**: `processed-sources.json` contains the filename with a non-final status (e.g., `analyzed`, `template_created`, `content_extracted`).

**Action**:
1. Report: `ℹ️ File is in intermediate state: {status}`
2. Ask whether to resume from that state or restart from scratch.
3. If restarting: delete any incomplete artifacts (draft wiki page) before re-running.

### 3. No related pages found

**Detection**: Both discovery phases return empty results.

**Action**: Create the wiki page normally. In the "Related Pages" section write:
```
No related pages identified yet. Run a maintenance pass later to discover connections.
```
This is a valid state. The knowledge graph fills in as the base grows.

### 4. High content overlap with existing page

**Detection**: Three or more keywords from the source match an existing wiki page, and the topics are substantially similar.

**Action**:
1. Warn: `⚠️ High overlap detected with [[existing-slug]]`
2. Show a brief overlap summary.
3. Suggest switching to merge mode.
4. If the user chooses `create` anyway, add a cross-reference link in both pages.

### 5. Image-heavy document

**Detection**: PDF or PPTX where images account for more than ~50% of content (scans, infographics, diagram-heavy slide decks).

**Action**:
1. Extract whatever text is available and create the wiki page.
2. Add a notice at the top of the wiki page:
   ```
   > ⚠️ **Extraction Note**: This document is image-heavy. Text extraction may be
   > incomplete. Key diagrams or charts should be added manually later.
   ```
3. Add to `processed-sources.json`: `"note": "image-heavy, text extraction incomplete"`

### 6. Special characters in filename

**Slug generation rules** (applied automatically):

| Input | Transformation | Example |
|-------|---------------|---------|
| Spaces | → `-` | `My Doc` → `my-doc` |
| `()` `（）` | remove | `RAG (intro)` → `RAG-intro` |
| `—` `–` `_` | → `-` | `AI—future` → `AI-future` |
| `/` `\` | → `-` | `cloud/edge` → `cloud-edge` |
| `.` (non-extension) | remove | `v2.0 plan` → `v20-plan` |
| CJK characters | **keep** | `AI策略` → `AI策略` |
| Emoji | remove | `🚀strategy` → `strategy` |
| Consecutive `-` | → single `-` | `A--B` → `A-B` |
| Leading/trailing `-` | remove | `-notes-` → `notes` |

### 7. No matching category

**Detection**: Source content does not fit any existing category in INDEX.md.

**Action**:
1. Determine a short, distinctive category name (2–6 words).
2. Choose a relevant emoji following the existing style.
3. Add `### {emoji} {Category Name}` to INDEX.md in an appropriate position.
4. Document the new category in your ingest report.

Common emoji by domain:

| Domain | Emoji |
|--------|-------|
| Security / Cybersecurity | 🛡️ |
| Data / Analytics | 📊 |
| Cloud / Infrastructure | ☁️ |
| Industry case studies | 🏢 |
| Products / Tools | 🔧 |
| Methodology / Process | 📋 |
| People / Organizations | 👥 |
| Trends / Future | 🔮 |
| Research / Academia | 🔬 |
| Finance / Business | 💼 |

### 8. processed-sources.json malformed

**Detection**: JSON parse error when reading the file.

**Action**:
1. Report: `🔴 processed-sources.json is invalid JSON — cannot parse`
2. Attempt automatic repair: check for missing commas, unmatched brackets, BOM header, comments (not valid in JSON).
3. If auto-repair succeeds: continue.
4. If not: stop and ask the user to fix the file manually before retrying.

### 9. INDEX.md malformed

**Detection**: Missing expected structure (top-level heading, category heading format inconsistent).

**Action**:
1. Report the specific structural issue.
2. Attempt to repair by applying the expected format pattern.
3. If repair succeeds: continue.
4. If not: stop and ask the user to inspect the file.

### 10. Source file empty or unreadable

**Detection**: File exists but contains no extractable text, or the extraction tool returns an error.

**Action**:
1. Report: `🔴 Cannot extract usable content from this file`
2. Check if the file is zero bytes or structurally corrupt.
3. Stop and report to the user. Do not create a wiki page stub.

### 11. Same filename, different content in raw/

**Detection**: `raw/` already contains a file with the same name, but file size or hash differs from the file being ingested.

**Action**:
1. Warn: `⚠️ A file with this name already exists in raw/ but appears to have different content`
2. Show sizes and modification timestamps for both.
3. Offer options:
   - **Rename new file** (recommended): add a date suffix — `filename_20250315.ext`
   - **Replace** — not recommended; violates raw/ immutability principle.

### 12. Large document (200+ pages / 60+ slides)

**Detection**: PDF exceeds ~200 pages or PPTX exceeds ~60 slides.

**Action**:
1. Note: `ℹ️ Large document detected — extracting in batches`
2. Extract in chunks (e.g., 50 pages at a time for PDFs), then merge into a single content object.
3. Be mindful of context window limits; summarize early sections if needed before processing later ones.
4. Do **not** attempt parallel extraction of the same file.

### 13. Mixed-language document

**Detection**: Document contains substantial content in two or more languages.

**Action**:
1. Use the dominant language for the wiki page language and slug generation.
2. Preserve technical terms, product names, and proper nouns in their original language.
3. Note the secondary language in the wiki page header if relevant.

### 14. Password-protected or encrypted file

**Detection**: Extraction tool returns an access error or password prompt.

**Action**:
1. Report: `🔴 File is password-protected — cannot extract content`
2. Ask the user to provide the password.
3. If provided: retry extraction with the password parameter.
4. If unavailable: skip the file and document it as `status: "blocked"` in processed-sources.json.

### 15. Slug conflicts with existing wiki page

**Detection**: After generating the slug, `wiki/{slug}.md` already exists with different content.

**Action**:
1. Warn: `⚠️ Slug conflict: wiki/{slug}.md already exists`
2. Append a disambiguating suffix, in order of preference:
   - Source-based: `{slug}-{short-source-name}`
   - Date-based: `{slug}-{YYYYMMDD}`
   - Numeric: `{slug}-2`, `{slug}-3`
3. In the new wiki page, note: `This page covers a different source from [[{original-slug}]].`
4. Consider adding a cross-reference in the original page.

---

## Severity Legend

| Symbol | Meaning | Blocks workflow? |
|--------|---------|-----------------|
| 🔴 Error | Must resolve before continuing | Yes |
| ⚠️ Warning | Requires user decision | No (after user confirms) |
| ⚙️ Auto | Handled automatically, no user input needed | No |
| ℹ️ Info | Informational only, no action needed | No |
