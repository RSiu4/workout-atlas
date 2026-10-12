# Workout Atlas: roadmap

## Done: location history outside workouts (Google Timeline)

`Data… → Location history (.json)…` (or drop the file) imports the on-device Timeline export
(`location-history.json`: a list of `visit` / `activity` / `timelinePath` entries) as its own source.

- `activity` → a route coloured by mode: Walking, Cycling, Running, Car (incl. motorcycle), Transit
  (subway, bus, tram, train, ferry), Flight, Other. The export stores only start and end, so trips are
  straight lines.
- `visit` (hierarchy level 0 only) → a **Visit** point with its dwell time. Heat counts → "Time spent"
  turns these into a where-do-my-hours-go map.
- `timelinePath` → a thin **Other** trace.
- Visit, Flight and Other start switched off so the workout map stays readable.

## Not done yet

- **Other location formats.** Android's `Timeline.json` (`semanticSegments`) and the older Takeout
  `Records.json` (`locations` with `latitudeE7`) use different shapes. Add a converter next to
  `importGoogleTimeline` in `index.html` that emits the same records.
- **Road-following paths.** The export has no road geometry; snapping trips to a road network would need
  an online routing service, which conflicts with keeping everything local.
- **Privacy helpers.** Optionally blur or round home / work locations before saving to IndexedDB.
- **Apple Significant Locations / iOS location.** iOS has no supported bulk export. A third-party logger's
  GPX export already works through the GPX importer.

## Activity file formats

- **Done:** GPX, TCX (Garmin Connect, Strava and others; TCX also carries the sport and calories), Apple Health `export.zip`.
- **Not done:** FIT, the binary format of Garmin bulk exports and Strava's `.fit.gz`. A parser would live next to
  `processTcx` in `index.html` and emit the same track summary. Selections containing `.fit` files now say how many
  were skipped, instead of ignoring them silently.

## Google Drive

- **Done:** pick a folder, scan sub-folders, import newest zip / json and all GPX / TCX, replace on re-sync.
- **Not done:** automatic background sync (the page has to be open and you click Sync), remembering a Drive
  login across sessions (Google tokens last an hour), importing only changed activity files instead of all of them.
