# Workout Atlas

A single-file, offline-first dashboard for exploring your own location data on a map:
Apple Health workout routes, GPX files, and Google Timeline location history. Everything is
parsed in your browser; nothing is uploaded.

![Workout Atlas: two sources as separate layers, each with its own palette, plus the monthly timeline](docs/img/overview.png)

<sub>Screenshots use **synthetic demo data**: two made-up people whose trips are routed along real Vienna streets (street data © OpenStreetMap contributors, base map © Esri), not anyone's real routes. Regenerate with `python tools/make_demo.py`.</sub>

- **Routes and heatmaps**, with per-source layers (each data source has its own style, palette and counting method, drawn on top of each other). Palettes include Strava-style Hot, Blue, Purple, Gray and Blue-red, there's a heatmap glow, a dark label-free "Strava dark" map, and an **Apply Strava look** button that sets all of it at once
- **Filters**: date (or brush the monthly chart), activity, place, time of day / week / month, distance, duration, speed, climb
- **Play**: animate routes building up over time
- **Compare**: two people or two time periods, overlay or difference heatmap, stats table
- **Blank map** option, and switchable place labels
- **3D print export** (STL): your heatmap as a printable relief, or routes as raised lines on a plaque, with size, crop and per-trail exclusion
- **Load your own data** in the page: Apple Health `export.zip`, a folder of `.gpx` / `.tcx` files (Garmin Connect, Strava and others), or a Google Timeline `location-history.json`

### Compare two people or two periods

![Compare tab: group A vs group B on one map, with a stats table and side-by-side monthly bars](docs/img/compare.png)

## Use it

Open `index.html` in a browser (Chrome, Edge, Firefox or Safari), click **Data…** and add your files.
Sources can be remembered in the browser (IndexedDB) so you only import once.

The page needs an internet connection for the map library and tiles (Leaflet, Esri, OpenStreetMap),
and for the zip reader (fflate) the first time you open a `.zip`.

Because it is one static file, it also works on GitHub Pages or any static host: the host only serves
the page, your files are read locally in your browser.

## 3D printing

Click **3D print…** on the map toolbar. The export uses the current map view and filters, so pan, zoom and filter first.

- **Heat relief**: height follows how often you went somewhere (logarithmic by default, so a one-off ride is still visible next to your busiest road).
- **Raised routes**: every route is a raised line of fixed width on a flat plaque.
- **Size**: set the longest side up to your bed size (default 250 mm); crop the view with the four trim sliders.
- **Leave out trails**: untick routes in the list, or use **Leave out of 3D print** on a selected route.
- **Map base** (optional): streets as fine raised lines, water recessed, buildings as an extra. Click **Load map data** to fetch OpenStreetMap data for the visible area from the public Overpass API (only the map area is sent, not your routes; the view must be under 16 km across).
- **Detail**: 0.7 / 0.5 / 0.35 mm cells (about 150k to 600k triangles for a 200 mm model).

The file is a watertight STL (flat base, solid walls). Keep ridges at least 1 mm wide for a 0.4 mm nozzle. Everything is generated in your browser.

## Repository layout

```
index.html        the whole app (HTML, CSS, JS)
build.py          optional: bake an Apple Health export into a personal copy
tools/make_demo.py  generates synthetic demo data (used for the screenshots)
data/             your exports (git-ignored; see data/README.md)
dist/             build output (git-ignored)
docs/             ROADMAP.md and the README screenshots
```

### Optional: a personal copy that opens with your data already loaded

```bash
python build.py                      # reads data/export.zip, writes dist/workout_atlas_personal.html
python build.py path/to/export.zip   # or point at an export elsewhere
```

`dist/workout_atlas_personal.html` contains your routes (and therefore where you live). It is git-ignored; don't publish it.

## Privacy

Your data never leaves the browser. `data/` and `dist/` are git-ignored, as are `*.zip`, `*.gpx` and `*.json`,
so exports and built pages with data cannot be committed by accident. Check `git status` before pushing.
