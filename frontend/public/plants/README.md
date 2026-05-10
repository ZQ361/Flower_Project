# Plant Images

Static plant images live in `images/` and are served by Vite from `/plants/images/...`.

Use the downloader from the `frontend` directory:

```powershell
npm.cmd run images:download -- --limit=5
```

Useful options:

- `--limit=5`: process only the first 5 catalog entries.
- `--start-class=73`: start from a specific Flowers-102 class id.
- `--force`: replace existing local images.
- `--dry-run`: search and write metadata without downloading files.
- `--delay=1200`: wait between plants, in milliseconds.

The script reads `backend/app/data/flowers_102_zh.json`, searches Wikimedia Commons by English flower name, saves images into `images/`, and writes:

- `credits.json`: matched/downloaded image metadata and attribution.
- `review-needed.json`: flowers that need manual image review or replacement.
