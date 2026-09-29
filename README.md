# about-me

Source of [ffhammer.github.io/about-me](https://ffhammer.github.io/about-me/).

- `content/*.md` – page text (syntax: `content/README.md`)
- `templates/page.html` + `build.py` – turn the Markdown into `site/**/index.html` (no dependencies)
- `site/assets/` – CSS, JS, images, videos
- `./dev.sh start` – local preview on :8000 that rebuilds and reloads on save

Pushing to `main` builds and deploys the site with GitHub Actions (`.github/workflows/pages.yml`).
