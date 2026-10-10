# Data provenance and licensing

**M0 includes no datasets, model weights or participant recordings.**

| Candidate | Purpose | License / distribution status |
| --- | --- | --- |
| Private mock-shelf clips | Main demo, evaluation | Needs written participant consent held privately. Publication permission is separate; no footage committed. |
| Code-generated synthetic clips | Unit/smoke tests | Can commit source generator; not substantial binary files. |
| MOT17/MOT20 | Tracker evaluation | **Unverified** research/data and redistribution terms; verify with dataset publisher before use. |
| SKU-110K, RPC, Grocery Store | Shelf understanding | **Unverified** independent terms, do not download or redistribute yet. |

Pin and review package dependency licensing before shipping, including transitive binaries. [OpenCV's PyPI information](https://pypi.org/project/opencv-python/) explains OpenCV, FFmpeg, Qt and wheel-specific licenses; they are not interchangeable. Dataset licenses cannot be inferred from model licenses.

## M1 direct runtime dependency review (2026-10-10)

| Package | License documentation | Caveat |
| --- | --- | --- |
| Pydantic | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) | Transitive wheels retain their own terms |
| pydantic-settings | [MIT](https://github.com/pydantic/pydantic-settings/blob/main/LICENSE) | Security audit required for exact pinned release |
| NumPy | [Project license declarations](https://github.com/numpy/numpy/blob/main/pyproject.toml): predominantly BSD-3-Clause, with MIT/0BSD/CC0 notices | Preserve accompanying notices on distribution |
| OpenCV Python headless | [Wheel and underlying code terms](https://pypi.org/project/opencv-python/): packaging MIT, OpenCV Apache-2.0, bundled FFmpeg LGPL-2.1 | Review exact wheel's 3rd-party notices prior to redistribution |

These links substantiate *project-level licensing documentation*, not a complete binary redistribution legal review. The runtime dependency audit is enforced by CI; exact dataset/model weight rights remain unverified because neither is selected.
