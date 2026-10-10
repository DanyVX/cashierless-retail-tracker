# Design and decision log

## Mission
Build a CPU-first, single-camera, mock-shelf *research prototype* that tracks ephemeral shopper sessions, recognizes shelf changes, attributes pick/return events conservatively, and computes virtual carts. 5–10 known SKUs only. It must be auditable with event, tracking and cart metrics. Ambiguity is explicitly **unattributed**, not a sale.

## Scope boundaries
No payments, public surveillance, face identification, persistent identity, multi-camera tracking, production claims or loss-prevention features.

## Planned modules
- M0: validated settings, privacy gates, environment discovery, capture protocol.
- M1: timestamped streaming video I/O, drop/gap detection and CPU tiny mode.
- M2: person detector + lifecycle tracker, MOT subsets and labeled clips.
- M3: shelf polygons and wrist-to-track attribution.
- M4: before/after shelf-state inference, unknown SKU handling.
- M5: confidence-aware event and cart state machine.
- M6: tracking/event/cart error scripts, oracle ablations and CPU benchmarks.
- M7: measured face redaction, retention/erase and privacy threat tests.
- M8: overlays, published blurred demo, limitations and release.

## Decision log
| Date | Alternatives | Choice | Why |
| --- | --- | --- | --- |
| 2026-10-10 | Real checkout vs controlled demo | Small mock shelf | Repeatable, honest evaluation |
| 2026-10-10 | Persistent IDs vs session IDs | Ephemeral track IDs | Reduce biometric/privacy risks |
| 2026-10-10 | GPU-first vs CPU-first | CPU-first with opt-in accelerated path | No GPU detected in builder |
| 2026-10-10 | Ultralytics default vs review each license | Provisional ONNX Runtime (MIT runtime), detector/weights TBD | Avoid unreviewed AGPL/research-only dependencies |
| 2026-10-10 | Permissive media export vs fail closed | Ban publishing and raw storage in M0 | Face blur and consent verification not yet implemented |
| 2026-10-10 | Notebook-only vs installable Python modules | src-layout, strict tests and CI | Reproducibility and maintainability |

| 2026-10-10 | Hardcode constant FPS vs use source PTS when present | PTS with marked FPS fallback and explicit gap packets | Expose temporal uncertainty instead of inventing pick/return events across missing frames |

## Open M0 blockers
Actual camera model, resolution/FPS, mounting angle, lighting, shelf geometry, SKU list and participants' consent cannot be inferred. The [recording protocol](RECORDING.md) records required fields as TBD. A high-front/top-down camera is a *recommendation*, not a confirmed setup.

## Uncertainty policy
No fabricated event across a frame gap, no confident attribution when wrist ownership is ambiguous, no guessed unseen SKU, no silent cart mutation below confidence thresholds. Every future result will include counts, failure breakdown, hardware and code revision.


## M2 implementation specifics
The `ColorMarkerDetector` segments deliberately encoded blue rectangles in synthetic scenes; it is not a human detector and cannot be sold as real CV accuracy. OpenCV HOG is the uncalibrated CPU pedestrian baseline, with OpenCV-bundled weights and no third-party download. A constant-velocity 2D Kalman filter with two-stage Hungarian center-distance association and tentative/confirmed/lost/removed track lifecycle approximates **some** ByteTrack ideas; it does not replicate ByteTrack or handle reidentification. Frames after a timeline gap must reset tracks. When a confirmed shopper leaves and returns after removal, a new ID is created. No model benchmark has yet been run.

| 2026-10-10 | Ultralytics AGPL dependency vs OpenCV HOG vs licensed external ONNX model | Built-in OpenCV HOG + clearly synthetic-only blue-marker backend | No unlicensed external weight download; CPU-first with measurable honest limitations |
