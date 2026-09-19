"""Subprocess entry point for explicit synthetic-authority runner tests only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tests.public_fixture_authority import run_fixture_runner

if __name__ == "__main__":
    raise SystemExit(run_fixture_runner(sys.argv[1:]))
