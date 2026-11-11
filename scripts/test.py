"""Run suites in separate processes: ML and speech both use package `app`."""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
failed = False
for service in ("web", "ml", "speech"):
    print(f"Testing {service}", flush=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=root / "services" / service)
    failed = failed or result.returncode != 0
raise SystemExit(1 if failed else 0)
