"""Set documentation links without ever handling an access token."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", sys.argv[1]):
    raise SystemExit("Usage: python3 scripts/configure_dockerhub.py YOUR_DOCKERHUB_USERNAME")
username = sys.argv[1]
readme = Path(__file__).resolve().parents[1] / "README.md"
readme.write_text(readme.read_text().replace("DOCKERHUB_USERNAME/module10-calculator", f"{username}/module10-calculator"))
print(f"Docker Hub link: https://hub.docker.com/r/{username}/module10-calculator")
print("Also set the GitHub Actions repository variable DOCKERHUB_USERNAME to this username.")
