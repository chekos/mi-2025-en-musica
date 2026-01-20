# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Interactive dashboard visualizing Spotify listening history for 2025. Static site hosted on GitHub Pages at https://chekos.github.io/mi-2025-en-musica/

## Commands

**Regenerate dashboard data:**
```bash
uv run scripts/generate_data.py
```

**Local development:**
```bash
# Any static file server works
python -m http.server 8000
# or
npx serve .
```

## Architecture

```
data/
  streaming_history_2025.json  # Raw Spotify Extended Streaming History (input)
  spotify-2025.json           # Processed dashboard data (output)

scripts/
  generate_data.py            # Transforms raw data → dashboard JSON
                              # Converts UTC timestamps to Pacific Time
                              # Calculates all metrics, heatmaps, trends

js/charts.js                  # All visualization functions using Observable Plot + D3
css/style.css                 # Monospace design system with CSS variables
index.html                    # Main dashboard (metrics, top artists/tracks, trends)
heatmaps.html                 # Faceted small-multiple heatmaps
```

## Data Flow

1. Raw Spotify data (`streaming_history_2025.json`) contains UTC timestamps
2. `generate_data.py` processes everything into Pacific Time and outputs `spotify-2025.json`
3. HTML pages load JSON and render with Observable Plot

## Key Technical Details

- **Timezone**: All timestamps converted from UTC to `America/Los_Angeles` (Pacific Time)
- **Visualizations**: Observable Plot 0.6 with D3.js 7
- **Skip definition**: Song marked as "skipped" OR reason_end is "fwdbtn"/"backbtn"
- **Skip rate filter**: Only shows songs with 10+ plays for statistical reliability
- **Design**: Grayscale palette, monospace typography, Tufte-inspired minimalism
