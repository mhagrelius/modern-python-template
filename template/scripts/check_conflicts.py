"""Reject unresolved merge markers in files supplied by prek."""

import re
import sys
from pathlib import Path

MARKER = re.compile(rb"^(?:<{7}(?: |$)|={7}$|>{7}(?: |$)|\|{7}(?: |$))", re.MULTILINE)


def main() -> int:
    failed = False
    for filename in sys.argv[1:]:
        path = Path(filename)
        if path.is_file() and MARKER.search(path.read_bytes()):
            print(f"Unresolved merge conflict: {filename}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
