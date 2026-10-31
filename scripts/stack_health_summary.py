#!/usr/bin/env python3
"""One-line health summary for every stack in the compose file.

Prints service name + state for a quick ops glance. Standalone helper; the
control plane's own health paths are untouched.
"""

import json
import subprocess
import sys

COMPOSE = "docker-compose.yml"


def parse_ps_json(text):
    """Normalise `docker compose ps --format json` output to a list of rows.

    Compose versions differ: one JSON array, JSON-lines (one object per
    line), a single object, or `{}` / nothing for an empty stack.
    """
    rows = []
    decoder = json.JSONDecoder()
    idx = 0
    while True:
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text):
            return rows
        value, idx = decoder.raw_decode(text, idx)
        if isinstance(value, list):
            rows.extend(value)
        elif isinstance(value, dict):
            if value:
                rows.append(value)
        else:
            raise ValueError("unexpected JSON value in compose ps output: %r" % (value,))


def running_services():
    out = subprocess.check_output(
        ["docker", "compose", "--file", COMPOSE, "ps", "--format", "json"],
        text=True,
    )
    return parse_ps_json(out)


def render(services):
    lines = []
    for svc in services:
        if not isinstance(svc, dict):
            raise ValueError("unexpected row in compose ps output: %r" % (svc,))
        name = svc.get("Service") or svc.get("Name") or "?"
        state = svc.get("State") or "unknown"
        lines.append(str(name) + ": " + str(state))
    return "\n".join(lines)


def summary():
    return render(running_services())


def main():
    try:
        print(summary())
    except (subprocess.CalledProcessError, ValueError, OSError) as e:
        # json.JSONDecodeError is a ValueError subclass.
        print("stack_health_summary: " + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
