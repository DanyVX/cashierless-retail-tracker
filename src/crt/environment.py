"""Privacy-minimized hardware and toolchain snapshot for reproducibility."""

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _command_output(*args: str) -> str | None:
    if shutil.which(args[0]) is None:
        return None
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=4, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _ram_bytes() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return None
    return int(page_size * pages)


def _network_probe() -> bool:
    request = urllib.request.Request("https://github.com", method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return 200 <= response.status < 500
    except (OSError, urllib.error.URLError):
        return False


def environment_snapshot(*, check_network: bool = False) -> dict[str, Any]:
    """Metadata for benchmarks, deliberately excluding usernames, hostname and secrets."""
    disk = shutil.disk_usage(Path.cwd().anchor or ".")
    cuda = _command_output("nvcc", "--version")
    gpu = _command_output(
        "nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"
    )
    sha = _command_output("git", "rev-parse", "HEAD")
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "shell": os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")),
        "python": platform.python_version(),
        "python_executable_kind": Path(sys.executable).name,
        "ram_bytes": _ram_bytes(),
        "disk_free_bytes": disk.free,
        "gpu": gpu if gpu else None,
        "cuda_toolkit": cuda.splitlines()[-1] if cuda else None,
        "uv_available": shutil.which("uv") is not None,
        "pip_available": _version("pip") is not None,
        "docker_available": shutil.which("docker") is not None,
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
        "git_identity_configured": bool(
            _command_output("git", "config", "user.name")
            and _command_output("git", "config", "user.email")
        ),
        "git_commit": sha if sha else None,
        "libraries": {
            package: _version(package)
            for package in ("pydantic", "pydantic-settings", "opencv-python-headless", "numpy")
        },
        **({"internet_reachable": _network_probe()} if check_network else {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate non-identifying environment report")
    parser.add_argument("--output", type=Path, help="Optional JSON output file")
    parser.add_argument("--check-network", action="store_true", help="Opt-in reachability probe")
    args = parser.parse_args()
    payload = json.dumps(environment_snapshot(check_network=args.check_network), indent=2)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
