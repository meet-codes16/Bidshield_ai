from pathlib import Path
from app.core.config import settings

def ensure_dirs():
    for p in [settings.UPLOAD_DIR, settings.EXTRACTED_DIR]:
        Path(p).mkdir(parents=True, exist_ok=True)
    Path(settings.AUDIT_DB).parent.mkdir(parents=True, exist_ok=True)
