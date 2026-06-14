import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "icon_data/iconsets/07_arasaac_pictograms"
META = OUT / "metadata"
PNG = OUT / "png_300"
API_URL = "https://api.arasaac.org/api/pictograms/all/en"
STATIC_URL = "https://static.arasaac.org/pictograms/{id}/{id}_300.png"


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    with urlopen(url, timeout=timeout) as response:
        return response.read()


def download_one(pictogram_id: int) -> tuple[int, bool, str]:
    path = PNG / f"{pictogram_id}.png"
    if path.exists() and path.stat().st_size > 0:
        return pictogram_id, True, "exists"
    try:
        data = fetch_bytes(STATIC_URL.format(id=pictogram_id))
        path.write_bytes(data)
        return pictogram_id, True, "downloaded"
    except (HTTPError, URLError, TimeoutError) as error:
        return pictogram_id, False, str(error)


def main() -> None:
    META.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)

    all_json = fetch_bytes(API_URL, timeout=120)
    (META / "arasaac_all_en.json").write_bytes(all_json)
    records = json.loads(all_json)
    ids = sorted({record["_id"] for record in records})
    (META / "arasaac_ids.txt").write_text("\n".join(map(str, ids)) + "\n")

    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(download_one, pictogram_id) for pictogram_id in ids]
        for future in as_completed(futures):
            pictogram_id, ok, message = future.result()
            completed += 1
            if not ok:
                failures.append({"id": pictogram_id, "error": message})
            if completed % 500 == 0:
                print(f"Downloaded/checked {completed}/{len(ids)}")

    (META / "download_failures.json").write_text(json.dumps(failures, indent=2))
    print(f"ARASAAC records: {len(records)}")
    print(f"Unique pictogram ids: {len(ids)}")
    print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
