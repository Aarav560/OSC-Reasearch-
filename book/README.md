# The Orbital Strike Codex

Five volumes, about 1,000 A4 pages, generated entirely from this repository's data:

| volume | contents | pages |
|---|---|---|
| I · The Science | 14 chapters on the mechanics, measured on Paper 26.3, plus test protocols | 42 |
| II · The Cannons | every downloaded cannon: render, materials list, side pictures, a plan of every layer | 632 |
| III · Zephyr | my own cannons: core, calibration, controllers, debugging, live fire, drill, ring nuke, stills | 56 |
| IV · The Video Atlas | one page per harvested video (260) | 269 |
| V · Data & Index | per-TNT data, flight logs, nuke runs, materials index, glossary, full video list | 25 |

The PDFs are not committed: they contain renders of other creators' schematics and frames and
excerpts from their videos, and they are large. Rebuild them:

    # renders (needs the schematics from tools/fetch_schematics.py, the 26.3 client assets and
    # blocks.json, and render/ served on :8766 from the view root)
    python3 render_schematics.py <schem dir> <assets> <blocks.json> <art dir> <view root>
    python3 blueprints.py <art dir> <assets>
    python3 build.py <art dir> <out dir> 1,2,3,4,5
    NODE_PATH=$(npm root -g) node print.js <out dir> 1,2,3,4,5

Text lives in `content_science.py`, `content_cannons.py`, `content_zephyr.py`, `content_atlas.py` and
`content_data.py`; charts and diagrams are drawn by `svgfig.py` from `paper-tests/` data; `paginate.js`
pours flowing text onto pages in the browser before printing. Vol. III's stills come from the
`showcase/` video renders.
