# Reproducible results

**Real detection, tracking, shelf-event, cart and face-blur metrics are TBD.** There is no licensed MOT subset and no set of three consented participant clips; therefore HOTA, IDF1, real-event F1, real-cart match, reliability and fairness claims are forbidden.

What *is implemented*:
- `python eval/run_synthetic.py`: nine tiny scripted generated-scene cases, with measured event matching and final cart quantities and scenario-specific raw counts. The labels are drawn from the scene script, not human annotations.
- `python bench/bench_video.py`: actual synthetic MJPG CPU decoder wall time and frames/sec.
- `crt.environment.environment_snapshot()`: Python, OS, RAM, hardware/GPU, package versions and Git revision in each generated JSON output.

Results are saved to ignored `results/*.json`; only script-observed results may appear in tables, with their synthetic scope prominent. No measurements have been copied into this document. **Uncertainty is extreme**, because generated scenes reflect the assumptions of the algorithm itself. Oracle tracking-vs-events ablations await real ground truth.
