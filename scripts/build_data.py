"""Copy talk inputs out of the sibling projects so the deck renders on its own."""
import csv
import json
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
SECTOPAT = HERE.parent
EXPLORER = SECTOPAT / "philtransexplorer"
PIPELINE = SECTOPAT / "philtranscopy"

shutil.copy(EXPLORER / "data/derivatives/articles.json", HERE / "data/articles.json")
shutil.copy(EXPLORER / "assets/SecToPat-logo.png", HERE / "assets/SecToPat-logo.png")

# Only files carrying _meta are the canonical extraction run.
rows = []
for path in sorted((PIPELINE / "data/extractions").rglob("*.json")):
    record = json.loads(path.read_text())
    if "_meta" not in record:
        continue
    key = str(path.parent.relative_to(PIPELINE / "data/extractions"))
    for loc in record.get("locations", []):
        rows.append({"article": key, **{f: loc.get(f) for f in ("place", "geography", "detail")}})

with open(HERE / "data/extraction_places.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["article", "place", "geography", "detail"])
    writer.writeheader()
    writer.writerows(rows)

page = Image.open(PIPELINE / "experiments/1_13_226/page_1_0226.png").convert("RGB")
page.crop((440, 2825, 2440, 3132)).save(HERE / "assets/mackerel-cook.jpg", quality=88)
page.crop((440, 1620, 2440, 2120)).save(HERE / "assets/mackerel-title.jpg", quality=88)
page.resize((page.width // 2, page.height // 2)).save(HERE / "assets/mackerel-page.jpg", quality=85)
