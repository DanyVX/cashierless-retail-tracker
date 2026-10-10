# Limitations and uncovered conditions

This is a **mock-shelf simulation prototype**, not a cashierless deployment. Original media must be consented; all public demo media is fully synthetic.

- No real camera, real participant annotations, staff recordings, measured faces or ground-truth video evaluations were available. HOTA/IDF1/real MOTA and real event/cart error rates are **not measured**.
- OpenCV HOG pedestrian detection is weak on overhead shelf footage and unmeasured here. Synthetic blue rectangles are not evidence of person detection.
- Magenta wrist markers and calibrated solid-color SKUs are synthetic stand-ins, not human pose estimation or general grocery product recognition; product appearance, unseen variants and near-duplicate brands remain unsupported.
- Kalman and Hungarian two-stage association is a simplified tracker, not official ByteTrack; crossing people and occlusion can cause ID switches. Session IDs are ephemeral.
- No automatic exit-line session closure, secure cart transfer after ID switches, multi-camera identity, real payments or identity verification. The explicit cart `end_session` call requires orchestration by a caller.
- Shelf lighting, camera rotation, hand occlusion, gloves, staff mode, calibration drift, time-lapse, reflective wrappers and camera shaking have not been robustly tested in real settings.
- The face-redaction baseline is **best effort**. No measured miss rate, so public real-person media export is blocked. Real persistent storage is unavailable; no encryption/erase pipeline for persisted biometric data is claimed.
- Event stream buffer is in-memory, bounded and records drops, but is not an authenticated HTTP API. Real queue backpressure/replay protection is not implemented.
- Synthetic script includes named scenarios with generated data, not real repeated experiments or statistically significant confidence intervals. Official TrackEval and oracle ablations remain incomplete.
- No external model/dataset licenses beyond documented project-level information have been reviewed for redistributable field use. Avoid unverified downloads.

All failures are evidence of work left, not a reason to invent success metrics.
