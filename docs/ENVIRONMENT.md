# Environment discovery (2026-10-10)

These observations describe the **ChatGPT build sandbox, not the user's recording computer**.

| Requirement | Observed |
| --- | --- |
| OS / shell | Debian 13 Linux / bash |
| Python | 3.13.5 |
| uv / pip | uv 0.10.0 / pip 25.1.1 |
| GPU / CUDA | No NVIDIA GPU/toolkit detected |
| RAM | 5.8 GiB total |
| Available disk | Approximately 30 GiB at discovery |
| Internet | Direct github.com DNS failed, no direct package-resolution access |
| Docker | Unavailable |
| ffmpeg | Available |
| Git author identity | Unconfigured locally; authenticated GitHub connector used for commits |

This is **not a benchmark**. Run `crt-env --output environment.json` on your own machine; the output intentionally omits usernames, hostname and secret environment values. Because package registries were unreachable, `uv.lock` could not be generated. Direct dependencies in `pyproject.toml` are version-pinned, but transitive reproducibility and fresh-clone setup are not yet verified.

## CPU-first / GPU training path

Default tests and synthetic smoke runs must finish on CPU in minutes. Opt-in expensive benchmarks may run on Colab, Kaggle or Lambda after reviewing each dataset/model license. Record the environment, exact Git SHA, dataset version and command. Bring back only non-identifying JSON benchmark results. Never upload participant footage to third-party notebooks without separately informed consent and security/legal review.
