# quackles-lineage-v0

Source-reported study behind the post `web/app/quackles-lineage-v0`. Nothing here was re-rendered or re-reviewed.

| file | what | origin |
|---|---|---|
| `data/history-v1.json`, `data/timeline.json`, `data/atlas.json` | the lineage archive: 665 versions, milestones, sprite atlas index | kvnloo/quackles `fff480b` static export (local branch, not pushed); dataset sha256 `7caa3704…` |
| `data/lineage-assets-README.md` | how the thumbnails were derived | kvnloo/quackles-assets `7c2e7da` (local branch) |
| `data/crop-metrics.json` | per-crop render settings and sharpness scores | fidelity-zoom run-01 `crop-metrics.csv`, local path column removed |
| `data/fidelity-zoom.json` | dimensions, pyramid tile counts, texel densities, coupons, render cost | transcribed from fidelity-zoom `REPORT.md` (2026-10-15) |
| `data/overnight-trials.json` | 34 rows / 39 review decisions from one overnight run | transcribed from `OVERNIGHT-2026-10-16.md` |
| `data/review-picks.json` | the five agent picks with reviewer notes | `review-5-scenes/CURRENT.json` (2026-10-16), scene and capture paths dropped |
| `data/timeline-ui.json` | lineage page checks | overnight log and the 2026-10-27 showcase note |

Images live in `web/public/media/quackles-lineage-v0/` and are hashed in `manifest.yaml`: the atlas pages and medium plates
from the lineage assets, the public process images from kvnloo/quackles `cb1196d`, and WebP conversions (quality 78, native
size) of the run-01 crops and heatmaps.

`python3 scripts/build_quackles_data.py` derives `web/data/quackles-lineage-v0.json` and fails if the frozen files disagree.
