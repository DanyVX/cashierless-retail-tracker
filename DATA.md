# Data provenance and licensing

**M0 includes no datasets, model weights or participant recordings.**

| Candidate | Purpose | License / distribution status |
| --- | --- | --- |
| Private mock-shelf clips | Main demo, evaluation | Needs written participant consent held privately. Publication permission is separate; no footage committed. |
| Code-generated synthetic clips | Unit/smoke tests | Can commit source generator; not substantial binary files. |
| MOT17/MOT20 | Tracker evaluation | **Unverified** research/data and redistribution terms; verify with dataset publisher before use. |
| SKU-110K, RPC, Grocery Store | Shelf understanding | **Unverified** independent terms, do not download or redistribute yet. |

Pin and review package dependency licensing before shipping, including transitive binaries. [OpenCV's PyPI information](https://pypi.org/project/opencv-python/) explains OpenCV, FFmpeg, Qt and wheel-specific licenses; they are not interchangeable. Dataset licenses cannot be inferred from model licenses.
