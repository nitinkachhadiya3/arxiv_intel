# Social Agent Runbook

This document explains the full technical flow: how content is ingested, rendered, published, scheduled, and safely operated.

## 1) System Overview

The pipeline has these major stages:

1. **Topic + content generation** (existing pipeline + post JSON files in `output/posts/`).
2. **Story planning** via strategist (`src/content/story_brief.py`) to choose single/carousel, hooks, and slide plan.
3. **Image rendering** via Gemini backgrounds + Pillow compositor (`src/media/gemini_carousel_images.py`, `src/media/editorial_compositor.py`).
4. **Publishing** to Instagram via `src/publish/instagram_publisher`.

Entrypoint for all operations: `main.py`.

## 2) Branch / Release Policy

- Day-to-day work: **`dev`** branch.
- Promote to production: merge/sync to **`main`** only with explicit approval.
- Current team preference in this repo: continue feature work on `dev`.

## 3) Required Runtime Inputs

### 3.1 Environment (`.env`)

Typical required values:

- `GEMINI_API_KEY` for image + strategist generation.
- Instagram/Meta credentials used by publisher (app/user/page tokens as configured in your bytecode publisher module).
- Optional control flags described below.

### 3.2 Config (`config/settings.yaml`)

Contains RSS feeds, trusted domains, scoring weights, and scheduler cadence:

- `scheduler.ingestion_interval_minutes`
- `scheduler.full_pipeline_runs_per_day`
- `scheduler.full_pipeline_at`

## 4) Commands You Will Use

Run from repo root: `/Users/nitinkaachhadiya/social_agent`

### 4.1 Render only (no publish)

```bash
python main.py --render-post
```

- Uses latest file in `output/posts/`.

Render a specific post JSON:

```bash
python main.py --render-post output/posts/<file>.json
```

### 4.2 Publish to Instagram

Publish latest post JSON:

```bash
python main.py --post-instagram
```

Publish a specific post JSON (recommended for controlled ops):

```bash
python main.py --post-instagram --post-json output/posts/<file>.json
```

### 4.3 Scheduler mode

```bash
python main.py --run-scheduler
```

- Starts long-running scheduler loop via `JobScheduler.run_forever()`.
- Use process supervisor (systemd/launchd/pm2/docker restart policy) in production.

## 5) Safety Controls and Fallback Behavior

## 5.1 Strict publish gate (important)

By default, publishing requires Gemini key and blocks silent low-quality fallback:

- `REQUIRE_GEMINI_FOR_PUBLISH=1` (default)
  - publish fails fast if `GEMINI_API_KEY` is missing
  - blocks Pillow-only fallback publish when Gemini render fails

Override only intentionally:

```bash
REQUIRE_GEMINI_FOR_PUBLISH=0 python main.py --post-instagram --post-json output/posts/<file>.json
```

## 5.2 Story strategist fallback

- `STORY_STRATEGIST_ENABLED=1` (default): uses Gemini strategist.
- If strategist unavailable or disabled, fallback planner still builds slide plan.

Disable strategist explicitly:

```bash
STORY_STRATEGIST_ENABLED=0 python main.py --render-post
```

## 5.3 Modular category/brand (minimal change switch)

You can shift vertical without code changes:

- `CONTENT_CATEGORY` (default: `technology`)
- `BRAND_NAME` (default: `ArXiv Intel`)

Example:

```bash
CONTENT_CATEGORY=finance BRAND_NAME="Signal Ledger" python main.py --render-post
```

This changes strategist + image prompt framing while preserving pipeline logic.

## 6) Current Visual Stack (Instagram)

- Cinematic overlay mode (`IMAGE_RENDER_MODE=cinematic_overlay`) is the active quality path.
- Divider + centered logo mark integrated in text region.
- Frosted/blurred lower text dock (not hard cut).
- Slide counters removed.
- Bullet formatting normalized for detail slides.
- Branding asset configured in `src/media/templates/branding.json` (`logo_path`).

## 7) End-to-End Operational Flow

For each post:

1. Load post JSON (`output/posts/*.json`).
2. Build/ensure story brief (`ensure_story_brief`).
3. Generate Gemini backgrounds per slide.
4. Composite text/branding via Pillow.
5. Save JPEGs and metadata under `output/images/...`.
6. Upload images (Cloudinary path used by publisher).
7. Publish Instagram carousel.
8. Return `instagram_media_id` in CLI output.

## 8) Real-World Test Pattern (Recommended)

### 8.1 Pre-publish validation

1. Render only first:
   ```bash
   python main.py --render-post output/posts/<file>.json
   ```
2. Visually inspect generated slides in `output/images/render_<slug>/`.
3. Publish only when approved:
   ```bash
   python main.py --post-instagram --post-json output/posts/<file>.json
   ```

### 8.2 Multi-post staged test

- Publish 2 different posts with controlled gap (e.g., 15 min).
- Verify topic non-repeat by selecting two different JSON files.
- Capture `instagram_media_id` for each post in ops notes.

## 9) Troubleshooting

### Error: `GEMINI_API_KEY missing for publish`

- Add/fix `GEMINI_API_KEY` in `.env`.
- Or set `REQUIRE_GEMINI_FOR_PUBLISH=0` only if fallback publishing is intentionally allowed.

### Error: `Image generation produced no slides`

- Gemini request may have failed and strict mode blocked fallback.
- Check model availability/network, then retry.

### Output quality looks “stage-1 / plain”

- Ensure strict publish gate is active (`REQUIRE_GEMINI_FOR_PUBLISH=1`).
- Confirm logs show `story_brief_ok` and `gemini_carousel_done` before publish.

### Duplicate / repeated topic concern

- Use explicit `--post-json` with different files.
- For scheduler-based selection, rely on repeat-guard settings in `config/settings.yaml`.

## 10) Logs and Artifacts

- Runtime logs print JSON lines with stage markers:
  - `story_brief_ok`
  - `gemini_carousel_start`
  - `gemini_carousel_done`
  - `instagram_carousel_published`
- Per-render artifacts:
  - `output/images/<run>/slide_XX.jpg`
  - `output/images/<run>/_meta/slide_XX_prompt.txt`
  - `output/images/<run>/_meta/story_brief.json`

## 11) Production Hardening Checklist

Before unattended deployment:

- [ ] `.env` validated (`GEMINI_API_KEY`, Instagram creds).
- [ ] `REQUIRE_GEMINI_FOR_PUBLISH=1` confirmed.
- [ ] Scheduler cadence configured in `config/settings.yaml`.
- [ ] Process supervisor configured with auto-restart.
- [ ] Log retention + alerting defined.
- [ ] Dry run + one controlled live post completed.

## 12) Quick Command Cheat Sheet

```bash
# render latest
python main.py --render-post

# render specific
python main.py --render-post output/posts/<file>.json

# publish latest
python main.py --post-instagram

# publish specific
python main.py --post-instagram --post-json output/posts/<file>.json

# run scheduler loop
python main.py --run-scheduler
```

---

If you want, next step can be a second doc: `docs/DEPLOYMENT.md` with platform-specific setup (systemd, Docker, launchd, cron wrappers) and exact production commands.
