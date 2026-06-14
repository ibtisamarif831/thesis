import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import build_opener


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "icon_data/iconsets/08_ghs_hazard_pictograms"
FILES = OUT / "files"
META = OUT / "metadata"
USER_AGENT = "thesis-icon-dataset/0.1 (local academic research dataset)"

FILENAMES = [
    "GHS-pictogram-explos.svg",
    "GHS-pictogram-flamme.svg",
    "GHS-pictogram-rondflam.svg",
    "GHS-pictogram-bottle.svg",
    "GHS-pictogram-acid.svg",
    "GHS-pictogram-skull.svg",
    "GHS-pictogram-exclam.svg",
    "GHS-pictogram-silhouette.svg",
    "GHS-pictogram-pollu.svg",
]


def main():
    FILES.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)

    opener = build_opener()
    opener.addheaders = [("User-Agent", USER_AGENT)]
    url = "https://commons.wikimedia.org/w/api.php?" + urlencode(
        {
            "action": "query",
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "titles": "|".join(f"File:{name}" for name in FILENAMES),
            "format": "json",
        }
    )
    with opener.open(url, timeout=30) as response:
        data = json.load(response)

    downloaded = []
    for page in data["query"]["pages"].values():
        title = page["title"]
        info = page["imageinfo"][0]
        name = title.removeprefix("File:")
        dest = FILES / name
        with opener.open(info["url"], timeout=60) as response:
            dest.write_bytes(response.read())
        downloaded.append({"title": title, "file": str(dest.relative_to(OUT)), **info})

    (META / "standard_ghs_pictograms.json").write_text(json.dumps(downloaded, indent=2))
    print(f"Downloaded {len(downloaded)} standard GHS pictograms to {FILES}")


if __name__ == "__main__":
    main()
