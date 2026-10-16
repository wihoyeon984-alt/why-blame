import os
import subprocess
import sys

environment = os.environ.copy()
environment["PYTHONUTF8"] = "1"
environment["PYTHONIOENCODING"] = "utf-8"
environment["PYTHONTRACEMALLOC"] = "25"

result = subprocess.run(
    [
        sys.executable,
        "-W",
        "default::ResourceWarning",
        "-m",
        "unittest",
        "discover",
        "-v",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=environment,
)

stdout = result.stdout.decode(
    "utf-8",
    errors="replace",
)
stderr = result.stderr.decode(
    "utf-8",
    errors="replace",
)

sys.stdout.write(stdout)
sys.stderr.write(stderr)

combined = stdout + "\n" + stderr

warning_lines = [
    line
    for line in combined.splitlines()
    if (
        "ResourceWarning" in line
        or "Implicitly cleaning up <HTTPError" in line
    )
]

print(
    "HTTP_RESOURCE_WARNING_LINES:",
    len(warning_lines),
)

if result.returncode != 0:
    raise SystemExit(result.returncode)

if warning_lines:
    print()
    print("Detected ResourceWarning output:")

    for line in warning_lines:
        print(line)

    raise SystemExit(1)

print("HTTP_RESOURCE_WARNING_CHECK_OK")
