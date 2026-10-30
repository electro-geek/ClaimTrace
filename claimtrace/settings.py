import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_dotenv(path=ROOT / ".env"):
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_dotenv()
DATA_DIR = Path(os.getenv("CLAIMTRACE_DATA_DIR", str(ROOT / "data")))
DB_PATH = Path(os.getenv("CLAIMTRACE_DB_PATH", str(DATA_DIR / "claimtrace.db")))
if not DATA_DIR.is_absolute(): DATA_DIR = ROOT / DATA_DIR
if not DB_PATH.is_absolute(): DB_PATH = ROOT / DB_PATH
GROUND_TRUTH_PATH = Path(os.getenv("CLAIMTRACE_GROUND_TRUTH", str(DATA_DIR / "ground_truth.csv")))
if not GROUND_TRUTH_PATH.is_absolute(): GROUND_TRUTH_PATH = ROOT / GROUND_TRUTH_PATH
API_URL = os.getenv("VITE_API_URL", "http://localhost:8000/api")
CORS_ORIGINS = [x.strip() for x in os.getenv("CLAIMTRACE_CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
DEFAULT_SEED = int(os.getenv("CLAIMTRACE_SEED", "20261022"))
DEFAULT_SCALE = os.getenv("CLAIMTRACE_SCALE", "full")
