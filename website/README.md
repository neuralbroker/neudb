# neuDB website

xAI-inspired product landing page for neuDB.

## Run locally

```bash
cd website
python3 -m http.server 8080
```

Open http://127.0.0.1:8080

## Structure

```
website/
├── index.html      # Landing page
├── assets/         # Logos (synced from docs/brand/)
├── css/style.css   # Styles
└── js/
    ├── main.js     # Chat, tabs, product nav
    └── background.js
```

## Deploy (GitHub Pages)

1. Push the repo to GitHub
2. Settings → Pages → Deploy from branch
3. Set folder to `/website` (or copy `website/` to `gh-pages` branch root)

## Update logos

Brand files live in `docs/brand/`. After changes:

```bash
cp docs/brand/* website/assets/
```