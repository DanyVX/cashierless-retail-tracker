# M8 demonstration and event buffer

`python tools/run_demo.py --out results/demo` synthesizes one encoded mock shopper and colored shelf item, runs frame-by-frame tracking, interaction, shelf comparison and cart logic, then writes `results/demo/events.json` and an optional `synthetic.gif`. The demo is not consented human footage; a synthetic GIF can be shared without facial privacy risk. `ffmpeg` is needed only for GIF export; `--no-gif` generates JSON without ffmpeg.

`src/crt/viz/overlay.py` draws ephemeral track IDs, zone polygons, wrist markers, virtual cart contents and event status on an input copy. `src/crt/api/events.py` provides a bounded no-video event buffer with explicit dropped-event counter; HTTP endpoint wiring is not included yet. Any real-source publication is blocked until validated blur and consent checks, even though best-effort Haar redaction exists.

Known failure modes: colored solid rectangles are not consumer products; pose markers are not actual hand joints; event timing depends on clear frames and known frame PTS. The pipeline is a **mock-shelf demonstration**, not an automatic billing product.
