# Gets past the initial errors due to missing functions. When no new logs are
# found, it will continually check every five seconds until it either finds a
# new log or hits 100 iterations and stops. This lets you catch missing
# functions on the main menu and level start as well.

# 1. Launch the game
# 2. Check the logs for missing functions
# 3. Add those function addresses to the config
# 4. Codegen + build
# 5. Repeat

import re
import subprocess
import sys
from pathlib import Path
import time

TOML = Path("condemned2_glue_functions.toml")
LOGS_DIR = Path("out/build/win-amd64-relwithdebinfo/logs")

FATAL_PATTERN = re.compile(
    r"Call to invalid or unregistered function at guest address (0x[0-9A-Fa-f]+)"
)


def run(cmd):
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def find_latest_log():
    logs = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not logs:
        return None

    return logs[0]


def extract_addresses(log_path):
    addresses = []
    with open(log_path) as f:
        for line in f:
            m = FATAL_PATTERN.search(line)
            if m:
                addresses.append(m.group(1).lower())

    return addresses


def add_to_manifest(addresses):
    text = TOML.read_text()
    text_lower = text.lower()

    to_add = [a for a in addresses if a not in text_lower]

    if not to_add:
        return []

    if "[functions]" not in text:
        text = text.rstrip() + "\n\n[functions]\n"

    for addr in to_add:
        text = text.rstrip() + f"\n{addr} = {{}}\n"

    TOML.write_text(text)
    return to_add


def check_log():
    log = find_latest_log()

    if not log:
        return False

    print(f"Reading: {log.name}")
    addresses = extract_addresses(log)

    if not addresses:
        return False

    added = add_to_manifest(addresses)

    if added:
        print(f"Found and added {len(added)} address(es): {', '.join(added)}")

    return bool(added)


check_log()

while True:
    run(["powershell", "-File", "script_codegen.ps1"])
    run(["powershell", "-File", "script_build.ps1"])
    run(["powershell", "-File", "script_run.ps1"])

    i = 0

    while True:
        i += 1

        if not check_log():
            print("No missing addresses found; sleeping...")
            time.sleep(5)
        else:
            break

    if i > 99:
        print("Exiting after 100 iterations without any new addresses found.")
        sys.exit(0)
