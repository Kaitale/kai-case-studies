"""Execute every notebook from its own folder; fail on the first error."""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

failed = []
for nb_path in sorted(Path(".").glob("*/[0-9]*.ipynb")):
    print(f"running {nb_path} …", flush=True)
    nb = nbformat.read(nb_path, as_version=4)
    try:
        NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(nb_path.parent)}}).execute()
    except Exception as e:  # noqa: BLE001
        print(f"FAILED {nb_path}: {e}", flush=True)
        failed.append(str(nb_path))
sys.exit(1 if failed else 0)
