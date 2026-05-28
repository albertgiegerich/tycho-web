import os
from pathlib import Path

os.environ.setdefault("ENV_FILE", str(Path(__file__).parent / ".env"))
