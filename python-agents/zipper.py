"""Builds a downloadable ZIP archive of a completed run: generated project
source, documentation/justification reports, agent state (artifacts), and
checkpoints — everything needed to inspect or continue the work offline."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

from storage import store

EXCLUDE_DIR_NAMES = {"node_modules", ".git"}


def build_zip_bytes(run_id: str) -> bytes:
    run_dir = store.run_dir(run_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in run_dir.rglob("*"):
            if path.is_dir():
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            arcname = Path(run_id) / path.relative_to(run_dir)
            zf.write(path, arcname.as_posix())
    buf.seek(0)
    return buf.getvalue()
