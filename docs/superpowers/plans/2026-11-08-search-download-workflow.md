# Search/download workflow implementation plan

> Execution: inline, continuing the user's explicit instruction to implement priorities 1–4. No commits or remote publishing requested.

**Goal:** Measure useful audio coverage, explain empty searches, compare matching metadata across origins, and persist download preferences.
**Architecture:** Reuse Store/Settings, SearchEngine events and per-origin DownloadManager manifests. Bend emits interface markup and text; JavaScript bridges DOM/HTTP.
**Tech Stack:** Existing Python/FastAPI/SQLite, Bend 2, vanilla JavaScript.
**Spec:** ../specs/2026-11-08-search-download-workflow-design.md

## Constraints and review focus
- Preserve LAWS.bend requirements; only confirmed audio counts; only audio/images enter selection.
- No new dependency, preview, transcoding, external telemetry, automatic transfer or cross-origin ZIP.
- Validate timeout vs unavailable media, cached checks, unknown artists, original/remix distinctions, unavailable preferred format, stale asynchronous responses and partial batch failures.

## Tasks
- [x] Add failing tests in tests/test_workflow.py for distinct diagnostic counters, stable grouping metadata, settings/profile persistence, bounded local measurements and download completion accounting. Run focused tests.
- [x] Extend models.py, engine.py, downloads.py and storage.py with those fields/counters, keeping source failures isolated. Add /api/coverage read/clear in app.py. Run focused and affected existing tests.
- [x] Add ui/home/workflow.bend markup/text exports and build markers for preferences/coverage. Update source diagnostics and grouped results in app.js; preference fields in preferences.js; reviewed selection/original batch action in downloads.js; bounded sample runner in coverage.js.
- [x] Extend browser checks for empty-source details, grouped origin formats, preferred format fallback, persistence, original/ZIP exact selection and coverage/cancellation. Build Bend exports; run PROOF.bend through existing build script.
- [x] Run full Python tests and browser checks; perform live coverage sample without media transfer; build dist/workflow/EveryTune.exe and verify native interface/download. Record evidence and limits in docs.
