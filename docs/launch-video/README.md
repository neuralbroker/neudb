# neuDB launch video

15-second launch teaser (`neudb-launch-15s.mp4`), 1920×1080, xAI-style dark minimal.

## Watch

Open [`neudb-launch-15s.mp4`](neudb-launch-15s.mp4) after generating.

## Regenerate

```bash
pip install playwright
playwright install chromium
python docs/launch-video/render.py
```

Produces:
- `raw.webm` — intermediate capture (gitignored)
- `neudb-launch-15s.mp4` — final H.264 video

## Storyboard (15s)

| Time | Content |
|------|---------|
| 0–4s | Logo + neuDB wordmark |
| 4–8s | "Your AI forgets every chat." → "neuDB remembers." |
| 8–12s | JSON on disk · Semantic search · Zero deps |
| 12–15s | `pip install neudb` + GitHub URL |

## Edit

Change copy or timing in [`promo.html`](promo.html), then re-run `render.py`.