# M6 reproducible evaluation

`python eval/run_synthetic.py --out results/synthetic_eval.json` generates synthetic frames **in memory**, labels scripted picks, runs the integrated perception/cart stack and writes actual metrics plus environment/Git hash. Scenarios: single shopper, hover, multi-item, pick-return (currently one pick only, RETURN requires a separate recording), two people, staff restock (no action script), occlusion, low light, fast shopper. Failures are kept, not hidden. This toy test is not evidence of real-world accuracy, demographic fairness, HOTA or retailer-readiness.

`eval/metrics.py` implements matched SKU/qty/time PICK/RETURN event counts, exact-cart and mean quantity errors, and simple MOTA counts; HOTA and IDF1 require TrackEval and properly licensed MOT subset plus labeled consented video. Thresholds should be determined on validation only. Reporting includes small counts; never invent confidence intervals or accuracy.
