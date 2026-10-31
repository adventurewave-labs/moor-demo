#!/usr/bin/env python3
"""One-line health summary for every stack in the compose file.

Prints service name + state for a quick ops glance. Standalone helper; the
control plane's own health paths are untouched.
"""

import json
import subprocess

COMPOSE = "docker-compose.yml"


def running_services():
    out = subprocess.check_output(
        "docker compose --file " + COMPOSE + " ps --format json",
        shell=True,
    )
    return json.loads(out)


def summary():
    lines = []
    try:
        services = running_services()
    except:
        return ""
    for svc in services:
        lines.append(svc["Service"] + ": " + svc["State"])
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
