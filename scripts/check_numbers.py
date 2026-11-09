"""Recompute every number stated on a slide and check the deck still says it."""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DECK = (HERE / "2026-11-13_DEPTH-philtransexplorer.qmd").read_text()
ARTICLES = json.loads((HERE / "data/articles.json").read_text())
with open(HERE / "data/extraction_places.csv", newline="") as f:
    PLACES = list(csv.DictReader(f))
OCR_ROOT = HERE.parent / "philtranscopy/data/ocr"
NOTES_RE = re.compile(r"::: \{\.notes\}\n(.*?)\n:::", re.S)


def median(values):
    values = sorted(values)
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2


def decade(start):
    return [a for a in ARTICLES if a["year"] // 10 * 10 == start]


def pct(items, test):
    return round(100 * sum(map(test, items)) / len(items))


is_letter = lambda a: a["topic"] == "Letter"
no_author = lambda a: not a["authors"]
pages = lambda start: median([a["n_pages"] for a in decade(start) if a["n_pages"] is not None])
experiments = [a for a in ARTICLES if a["topic"] == "Experiment"]
filled = [p["place"].lower() for p in PLACES if p["place"]]
names = {n for a in ARTICLES for n in a["authors"]}
longest = max(ARTICLES, key=lambda a: a["n_pages"] or 0)
maskelyne = [a["year"] for a in ARTICLES if any("Maskelyne" in n for n in a["authors"])]

# (computed value, expected value, the text the deck must contain)
CHECKS = [
    (len(ARTICLES), 8545, "8,545"),
    (1886 - 1665 + 1, 222, "222"),
    (len(experiments), 455, "455"),
    (round(100 * len(experiments) / len(ARTICLES)), 5, "about 5%"),
    (sum(a["n_pages"] is not None for a in ARTICLES), 8081, "8,081"),
    (pages(1660), 3, "from 3 pages"),
    (pages(1870), 20, "twenty pages"),
    (pages(1880), 32, "thirty-two"),
    (longest["n_pages"], 1005, "1,005-page"),
    (len(filled), 965, "965"),
    (sum("private" in p for p in filled), 144, "144"),
    (sum("public" in p for p in filled), 0, '<span class="n">0</span>'),
    (filled.count("private study or laboratory"), 26, "26 exact matches"),
    (sum("kitchen" in p for p in filled), 4, '"kitchen" appears 4 times'),
    (min(maskelyne), 1759, "1759"),
    (max(maskelyne), 1879, "1879"),
    (max(a["year"] for a in ARTICLES if is_letter(a)), 1860, "from 1860"),
]

failures = []
for value, expected, text in CHECKS:
    if value != expected:
        failures.append(f"{text!r}: data gives {value}")
    if text not in DECK:
        failures.append(f"{text!r}: not found in deck")

# Claims made in prose, about the shape of the charts.
PROSE = {
    "letters about one in six in the 1660s": pct(decade(1660), is_letter) == 16,
    "letters half of the 1750s": pct(decade(1750), is_letter) == 50,
    "letters under 1% in the 1850s": 100 * sum(map(is_letter, decade(1850))) / len(decade(1850)) < 1,
    "no author over half in the 1660s": pct(decade(1660), no_author) > 50,
    "no author 2% in the 1870s": pct(decade(1870), no_author) == 2,
    "the longest item is by Newton, 1672": longest["year"] == 1672 and any("Newton" in n for n in longest["authors"]),
    "four spellings of Hooke": {"Hooke, Robert", "Hook, ", "Hooke, ", "Hooke's, Dr."} <= names,
    "labels Article and Articles both exist": {"Article", "Articles"} <= {a["topic"] for a in ARTICLES},
    "private study or laboratory is the top place": max(set(filled), key=filled.count) == "private study or laboratory",
    "Royal Society example": any(p["place"] == "private study or meeting room (Royal Society)" for p in PLACES),
    "Royal Institution example": any(p["place"] == "private study or laboratory (Royal Institution)" for p in PLACES),
    "Gresham example": any(p["place"] == "private laboratory or workshop (attached to Gresham College)" for p in PLACES),
    "sparrow example": any(p["detail"] == "where the sparrow was placed" for p in PLACES),
    "cat example": any(p["detail"] == "floor area where the cat was placed" for p in PLACES),
}
if OCR_ROOT.exists():
    PROSE["8,506 page transcripts"] = sum(1 for _ in OCR_ROOT.rglob("page*.txt")) == 8506
failures += [f"prose claim fails: {name}" for name, ok in PROSE.items() if not ok]

for path in (HERE / "data/annotations").glob("*"):
    print(f"annotation file present, error rate not yet wired in: {path.name}")

notes = " ".join(NOTES_RE.findall(DECK))
words = len(re.sub(r"\[[^\]]*\]", " ", notes).split())
timings = re.findall(r"(?m)^\[(\d+):(\d\d)\]", "\n".join(NOTES_RE.findall(DECK)))
seconds = sum(int(m) * 60 + int(s) for m, s in timings)
print(f"speaker notes: {words} words across {len(timings)} slides; planned time {seconds // 60}:{seconds % 60:02d}")
if not 2300 <= words <= 2700:
    failures.append(f"speaker notes are {words} words, outside 2,300-2,700")

print(f"PENDING slides: {len(re.findall('pending-tag', DECK))}")
if failures:
    raise SystemExit("FAILED\n" + "\n".join(failures))
print("all numbers on slides reconcile")
