from pathlib import Path
import sys

from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.webapp import app  # noqa: E402

app.mount("/static", StaticFiles(directory=str(ROOT / "web" / "static")), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
