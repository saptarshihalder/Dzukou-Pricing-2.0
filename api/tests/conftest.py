import sys
from pathlib import Path

# Ensure the project root is on sys.path so `import api` works when running tests via `api/tests/*`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
