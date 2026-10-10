# Reproducible results

**No accuracy or speed measurements exist yet.** All HOTA/MOTA/IDF1, event F1, cart exact-match, FPS and latency values are **TBD (not yet measured)**.

Future scripts in `bench/` and `eval/` must save each run to `results/*.json` with UTC timestamp, Git SHA, operating system, hardware, RAM, GPU/CUDA status, Python and library versions, data split, scenario, seed, command and configuration. Render README tables from these result files, never hand-type plausible metrics. Include scriptable negative cases and per-scenario small-sample counts. A CPU smoke benchmark belongs in CI; heavy benchmark runs are opt-in.
