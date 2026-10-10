# Privacy design and threat model

**Scope:** consenting, single-camera mock-shelf experiments only. No real consumer identification, payment or anti-theft service.

- Capture requires external private consent evidence; publishing a clip requires **separate express permission**.
- Track IDs are ephemeral within sessions and never used for re-identification. IDs and event logs cannot resolve a natural person.
- Raw frame storage is disabled by default and retention is zero. The in-memory pipeline does not persist source media or embeddings. The synthetic-only demo is permitted to save generated clip frames, because they depict no participants.
- M7 implements a best-effort OpenCV Haar frontal-face detector and Gaussian blur, **not verified complete anonymization**. Profiles, tiny faces, occlusion, lighting, and false negatives can evade it. No real-media export is allowed in CLI. Blur miss-rate is **TBD (no consented labeled validation footage)**; do not claim 100% coverage.
- Encryption at rest is not needed for the default nonpersisted source frames. Any future real-media storage must add encryption, short TTL, delete/erase, access controls and audit, before enabling capture storage.
- Risks: leaked camera stream credentials, camera tampering/calibration drift, corrupt video, data poisoning, false shelf attribution, event API replay or backpressure, accidental publishing of faces. Current mitigations: no credentials logged, capture opt-in, conservative attribution, gap resets, strictly synthetic published demo.
- Production usage needs signage, applicable legal review, consent/notification analysis, tested retention/erasure and access-control policies. None of this prototype constitutes a production compliance assurance.

**Explicit limitations:** No quantified face-blur miss rate, no realistic human benchmark, and no evidence of lawful processing for a real store. Published examples must be demonstrably synthetic until those blockers are resolved.
