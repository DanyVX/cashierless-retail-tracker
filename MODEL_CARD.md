# Model card: M2 person detection baselines

Two baselines, with **no real camera accuracy numbers yet**:

- `ColorMarkerDetector`: deterministic connected components over explicitly blue-coded mock people. Not a trained model, **synthetic only**, cannot be used for general people identification.
- `OpenCVHOGDetector`: classic pretrained HOG/SVM pedestrian detector bundled with OpenCV. OpenCV source license Apache-2.0; wheel's packaging/FFmpeg/third-party notices require separate review; see DATA.md. HOG score transformed by sigmoid is **not calibrated probability**. It is likely brittle under crowded shelf views, high camera angles, occlusion, small people, reflections, and lighting changes; fairness/demographic performance is **unmeasured**.

No face recognition or reidentification. No model assets are bundled in Git and neither backend is fit for real automated billing. Proposed future licensed ONNX person detector remains an optional extension, not a shipped capability.
