"""Check every vendored data file against the SHA-256 listed in DATA.md."""
import hashlib
import re
import sys
from pathlib import Path

table = dict(re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", Path("DATA.md").read_text(encoding="utf-8")))
bad = 0
for f in sorted(p for p in Path(".").glob("*/data/**/*") if p.is_file()):
    want = table.get(f.name)
    got = hashlib.sha256(f.read_bytes()).hexdigest()
    status = "ok" if want == got else ("NOT LISTED" if want is None else "CHANGED")
    bad += status != "ok"
    print(f"{status:10} {f}")
sys.exit(1 if bad else 0)
