# Privacy design and threat model

**Allowed inputs:** only consented private mock-shelf recordings. Per-session ephemeral track IDs have no facial recognition, biometric matching or cross-session linkage.

- Consent: evidence kept privately, outside repo. Participant filming permission and publication permission are different.
- Data minimization: default is no raw frame storage and zero retention. Do not log raw video, embeddings, faces, voice, IDs or secrets.
- Publication: blocked in M0/M1; must require proven blur-on-output and measured blur miss-rate later. A blur checkbox alone is insufficient.
- Persistence: any future sensitive storage requires authenticated access, encryption at rest, finite TTL, deletion/erase, and documented threat tests.
- Threats: camera compromise, secret leakage, stolen storage, calibration tampering, replay of event streams and model failures. Mitigations require further milestones.
- Real-store deployment would require signage, permission/consent analysis, retention/privacy policies and jurisdiction-specific legal review. This prototype has none of those assurances.

The local `consent_confirmed` guard represents externally verified evidence, not a substitute for collecting proof. No anti-theft evasion or shopper identification is intended.
