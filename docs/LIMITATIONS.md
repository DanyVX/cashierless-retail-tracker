# Limitations, risks and uncovered scenarios

M0 was infrastructure only. M1 now has a basic video reader, but there is **no detector, tracker, hand detection, shelf inference, cart, API, face blur or cashierless real-time demo**. No participant or dataset recording exists, no experimental results are measured, no model licensing finalized. M0 recording decisions remain unconfirmed.

The sandbox has no GPU or Docker, and lacks direct GitHub DNS; not a claim about the target deployment device. `uv.lock` and fresh-clone quickstart verification remain pending because dependency resolution cannot reach registries.

Future single-camera limitations include shelf/people occlusion, ID switches, crossing shoppers, camera shake, low FPS, confusable SKUs, deceptive shelf rearrangement and small consented dataset bias. These must each be assessed or explicitly marked uncovered as milestones progress. Media exports are forbidden pending validated face blur.

M1 adds a basic consent-gated video reader, but no model/tracking/cart. Synthetic timing and RTSP reconnection are mock-tested, not verified with an actual camera. See [VIDEO.md](VIDEO.md) for backend-specific constraints.
