"""Generate non-secret payloads; never invoke an agent, change config, or restart a service."""
import argparse
import json
import os
from pathlib import Path
import sys

FAILURE_SCRIPT = '''"""Synthetic oversized output; exit 7 is intentional. No side effects."""
import sys

for i in range(220):
    print("CANARY_%04d " % i + "synthetic diagnostic alpha beta gamma delta " * 3)
sys.exit(7)
'''


def generate(output):
    output.mkdir(mode=0o700, exist_ok=False)
    payloads = {
        "small.txt": "".join(f"CANARY_SMALL_{i:03d}\n" for i in range(1, 13)),
        "351-lines.txt": "".join(f"CANARY_LINE_{i:03d}\n" for i in range(1, 352)),
        "oversized_failure.py": FAILURE_SCRIPT,
    }
    for name, content in payloads.items():
        path = output / name
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    return list(payloads)


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "invalid arguments; use --help for usage\n")


def main():
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory; parent must exist")
    args = parser.parse_args()
    try:
        names = generate(args.output.expanduser())
    except OSError:
        print("cannot create fixtures: choose a new writable directory with an existing parent", file=sys.stderr)
        return 2
    print(json.dumps({"directory": str(args.output), "synthetic": True, "files": names}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
