# Architecture

## 1. System Overview

`
Frontend (Vue 3 + Vite)
  /api/* proxy -> Backend (FastAPI + Uvicorn)
    routes.py -> converter.py -> assembler.py -> ai_service.py -> DeepSeek API
`

## 2. Conversion Pipeline

### Two Modes

| Mode | Description |
|------|-------------|
| One-shot | Pre-scan -> all chapters -> assemble |
| Step-by-step | Pre-scan -> character review -> per-chapter -> assemble |

### Phase 0: Pre-Scan

One lightweight AI call to extract global context.

- Sends FULL chapter texts (no truncation)
- AI returns: character list (name, aliases, role, personality, first_chapter) + per-chapter summaries
- Code assigns stable IDs: char_001, char_002...
- Character appearance inferred from personality keywords

### Phase 1: Per-Chapter Conversion

- Each chapter calls DeepSeek independently
- Context injection: existing character table (with IDs) + previous summaries
- Temperature: 0.1 (minimized hallucination)
- Anti-hallucination: system prompt requires strict source adherence
- Post-processing: remap AI-invented character_ids to pre-scan stable IDs

### Phase 2: Assembler

- Merges characters by name (pre-scan IDs take priority)
- Parses scenes from chapter YAML
- Global scene renumbering
- Post-assembly ID remapping
- Runs 4 continuity checks
- Deduplicates IDs
- Sorts characters by role priority

## 3. Character ID Management

| Stage | Operation |
|-------|-----------|
| Pre-scan | Assign char_001..char_N |
| Context injection | get_character_context_yaml() includes id field |
| Post-chapter | Remap dialogue character_ids by name match |
| update_characters | Preserve existing IDs, fill new ones |
| Assembler merge | Pre-scan IDs take priority over chapter YAML IDs |
| Assembler dedup | Same ID across different names -> renumber |
| Frontend merge | doMerge() remaps all scene references |

## 4. Dynamic Continuity Warnings

4 checks: orphan_character, location_consistency, scene_gaps, character_description_changed.

- Refresh button re-runs all checks on current state
- Click warning to navigate to source scene
- One-click fixes: missing_transition (add cut), orphan_character (add to table), inconsistent_location (normalize)

## 5. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Health check |
| POST | /api/chapters/parse | Local chapter split |
| POST | /api/convert | One-shot conversion (JSON) |
| POST | /api/convert/yaml | One-shot conversion (YAML) |
| POST | /api/convert/pre-scan | Pre-scan: extract characters + summaries |
| POST | /api/convert/chapter | Per-chapter conversion with context + ID remapping |
| POST | /api/convert/assemble | Assemble chapter YAMLs into screenplay |
| POST | /api/convert/recheck | Re-run continuity checks |
| POST | /api/prompts/generate | AI video prompt generation |
| GET | /api/schema | Screenplay YAML schema |
| CRUD | /api/workspaces/* | Workspace management |

## 6. Frontend Views

| View | Purpose |
|------|---------|
| HomePage | Product intro + feature cards |
| ConvertPage | Core conversion controller (both modes) |
| WorkspacesPage | Workspace list + export/import |
| PromptsPage | AI video prompt workshop |

## 7. Key Components

| Component | Purpose |
|-----------|---------|
| NovelInput | Text input + file upload |
| ConversionProgress | Full-mode progress bar |
| ScreenplayResult | Full result display with inline editing |
| EditableField | Click-to-edit inline field (reads DOM value) |

## 8. Data Flow (Step-by-Step Mode)

`
1. User pastes text -> parseChapters() -> chapters[]
2. preScan(novel) -> preScanChars[] (with IDs) + preScanSummaries{}
3. Character review -> user edits/adds/deletes/merges -> confirmCharacters()
4. convertChapter(chapter, existingChars, summaries) -> {scenes, newChars}
5. Post-processing: remap AI character_ids -> pre-scan IDs
6. Repeat step 4-5 for each chapter
7. assembleStep(novel) -> full Screenplay
8. Post-assembly: remap scene character_ids -> character table IDs
`

## 9. Workspace Persistence

- JSON files stored in /workspaces/
- Fields: raw_text, chapters, screenplay, step_results, status
- step_results enables progress persistence across sessions
- Export/import via JSON download/upload

## 10. Hallucination Prevention

- System prompt: strict source adherence, anti-hallucination checklist
- Example YAML uses placeholders not real names
- Temperature: 0.1 for conversion
- Post-processing: character ID remapping
- String sanitization: handle list/mixed-type values from AI

## 11. Project Structure

`
7Cow/
  docs/
    architecture.md
    screenplay-schema.md
  backend/app/
    main.py
    config.py
    models/ (novel.py, screenplay.py, workspace.py)
    services/ (parser.py, ai_service.py, converter.py, assembler.py, workspace_store.py)
    prompts/ (pre_scan.py, system.py, video_prompt.py)
    api/routes.py
  frontend/src/
    views/ (Home, Convert, Workspaces, Prompts)
    components/ (NovelInput, ConversionProgress, ScreenplayResult, EditableField)
    composables/useWorkspace.js
    router/index.js
  workspaces/
`
