"""Run each service's tests in its own locked uv environment."""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
failed = False
service_env = os.environ.copy()
service_env.pop("VIRTUAL_ENV", None)
for service in ("web", "ml", "speech"):
    print(f"Testing {service}", flush=True)
    result = subprocess.run(
        ["uv", "run", "--locked", "--group", "dev", "python", "-m", "pytest", "tests", "-q"],
        cwd=root / "services" / service,
        env=service_env,
    )
    failed = failed or result.returncode != 0
raise SystemExit(1 if failed else 0)
