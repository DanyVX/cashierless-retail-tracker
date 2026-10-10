PYTHON ?= python
.PHONY: setup lint format typecheck test test-fast bench run docker-build clean
setup:
	$(PYTHON) -m pip install -e '.[dev]'
lint:
	ruff check .
	ruff format --check .
format:
	ruff format .
typecheck:
	mypy src/crt
test:
	pytest --cov=crt --cov-report=term-missing --cov-fail-under=70 -m 'not slow and not gpu'
test-fast:
	pytest -q -m 'not slow and not gpu'
bench:
	$(PYTHON) bench/bench_video.py --frames 30
	$(PYTHON) -m eval.run_synthetic
run:
	$(PYTHON) tools/run_demo.py --out results/demo
docker-build:
	@echo 'No Dockerfile exists; Docker deployment is not implemented.'
clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov')]"
