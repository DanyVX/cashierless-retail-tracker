# Contributing

One milestone per `m<N>-<slug>` branch and pull request. Conventional commits only; merge after lint, typecheck, tests, coverage, CI, audit and security checks pass. Do not commit raw recordings, participant consent, personal images, model weights, secrets or large binaries.

Install `uv sync --extra dev`, run `ruff check .`, `ruff format --check .`, `mypy src/crt`, `pytest --cov=crt --cov-fail-under=70`. Document every major choice in the decision log and every untested edge case in LIMITATIONS.
