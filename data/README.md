# data/

Put your own exports here. **Everything in this folder except this file is git-ignored.**

| What | Where it comes from | How to use it |
|---|---|---|
| `export.zip` | Apple Health → profile picture → Export All Health Data | `python build.py` bakes it into `dist/workout_atlas_personal.html`, or load it in the app with **Data…** |
| `*.gpx` / a folder of GPX files | Strava, Garmin, Komoot, or the `workout-routes` folder of an Apple export | load with **Data…** |
| `location-history*.json` | Google Maps app → Timeline → export | load with **Data…** |

Files here are only a convenient place to keep them. The app does not read this folder by itself;
you pick files in the page (nothing is uploaded) or run `build.py`.
