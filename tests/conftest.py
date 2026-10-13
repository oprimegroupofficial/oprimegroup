import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: statistical validation with many synthetic replicates")
