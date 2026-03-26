# WeatherDependentCommits

A playful project to answer an important question: are your commits weather-dependent?

This repository now contains:

- `weather.py`: the original Python CLI script.
- `web/`: a Vue 3 web app (v1) that runs fully client-side and can be deployed to GitHub Pages.

## Web app (Vue)

The web app analyzes a public GitHub repository (default branch), fetches historical rain data from Open-Meteo, and shows:

- rainy vs. dry commit split
- adjustable rain threshold slider
- monthly trend view
- day-of-week insights
- funny verdict text

### Run locally

```bash
cd web
npm install
npm run dev
```

Then open the local URL shown by Vite.

### Build locally

```bash
cd web
npm run build
```

### GitHub Pages deployment

A GitHub Actions workflow is included at `.github/workflows/deploy-web.yml`.

- It builds `web/` and deploys `web/dist` to GitHub Pages.
- The Vite base path is set to `/WeatherDependentCommits/` in `web/vite.config.js`.
- Expected project page URL: `https://v-o-id.github.io/WeatherDependentCommits/`

To enable deployment in GitHub:

1. Open repository settings -> Pages.
2. Under Build and deployment, choose Source: GitHub Actions.
3. Push to `master` (or run the workflow manually).

## Original Python script

The original CLI still works for local analysis.

### Usage

Make sure Git and Python are installed.

- Analyze an existing local repository path:

```bash
python weather.py <absolute-path-to-your-repo> <latitude> <longitude>
```

- Clone a GitHub repo first, then analyze it:

```bash
python weather.py <https://github.com/owner/repo.git> <latitude> <longitude> --d
```

Example:

```bash
python weather.py https://github.com/V-o-id/WeatherDependentCommits.git 48.303056 14.290556 --d
```

Notes:

- Current web app and script target public repository data.
- Unauthenticated GitHub API requests are rate-limited.
