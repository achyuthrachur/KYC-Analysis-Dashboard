import argparse
import json
import re
from pathlib import Path


def extract_data(source: Path, target: Path) -> None:
    html = source.read_text(encoding="utf-8")
    match = re.search(
        r'<script[^>]*id=["\\\']dashboard-data["\\\'][^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not locate the dashboard-data script block in the HTML.")
    payload = match.group(1).strip()
    data = json.loads(payload)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {target} with {len(data.get('records', []))} records.")


def main():
    parser = argparse.ArgumentParser(description="Extract dashboard JSON from the provided HTML file.")
    parser.add_argument("source", type=Path, help="Path to the HTML file containing the dashboard-data script tag.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "dashboard_data.json",
        help="Where to write the extracted JSON (default: data/dashboard_data.json).",
    )
    args = parser.parse_args()
    extract_data(args.source, args.output)


if __name__ == "__main__":
    main()
