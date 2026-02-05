from pathlib import Path
from datetime import datetime
import re

UPLOAD_ROOT = Path("data/uploads")

def safe_segment(s: str) -> str:
    # keep it filesystem safe
    s = s.strip()
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    return s[:80] if len(s) > 80 else s

def build_voucher_path(firm_id: int, client_code: str, fy: str, month: str, vtype: str, original_filename: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{safe_segment(original_filename)}"
    return UPLOAD_ROOT / f"firm_{firm_id}" / safe_segment(client_code) / safe_segment(fy) / safe_segment(month) / safe_segment(vtype) / fname
