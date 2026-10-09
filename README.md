# Workout Atlas

A single-file, offline-first dashboard for exploring your own location data on a map:
Apple Health workout routes, GPX files, and Google Timeline location history. Everything is
parsed in your browser; nothing is uploaded.

- **Routes and heatmaps**, with per-source layers (each data source has its own style, palette and counting method, drawn on top of each other)
- **Filters**: date (or brush the monthly chart), activity, place, time of day / week / month, distance, duration, speed, climb
- **Play**: animate routes building up over time
- **Compare**: two people or two time periods, overlay or difference heatmap, stats table
- **Blank map** option, and switchable place labels
- **Load your own data** in the page: Apple Health `export.zip`, a folder of `.gpx` files, or a Google Timeline `location-history.json`

## Use it

Open `workout_atlas_empty.html` in a browser (Chrome, Edge, Firefox or Safari), click **Data…** and add your files.
Sources can be remembered in the browser (IndexedDB) so you only import once. The page needs an internet
connection for the map library and tiles (Leaflet, Esri and OpenStreetMap), and for the zip reader (fflate) the first time you open a `.zip`.

### Optional: bake your data into the page

`build.py` reads an Apple Health export and writes a copy of the page with your routes embedded, so it opens ready to use:

```bash
python build.py path/to/export.zip            # writes workout_dashboard.html
python build.py --empty                       # writes workout_atlas_empty.html (no data, safe to share)
```

`workout_dashboard.html` contains your routes (and therefore where you live), so it is git-ignored. Don't publish it.

## Files

| File | |
|---|---|
| `template.html` | the whole app (HTML, CSS, JS) |
| `build.py` | bakes an Apple Health export into the template, or writes the empty viewer |
| `workout_atlas_empty.html` | built viewer with no data |
| `ROADMAP.md` | what's done and what's next |

## Privacy

Your data never leaves the browser. Do not commit exports (`*.zip`), location files (`*.json`),
GPX files, or built pages that contain data; `.gitignore` excludes them.
