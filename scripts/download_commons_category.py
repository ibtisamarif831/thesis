import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import build_opener


API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "thesis-icon-dataset/0.1 (local academic research dataset)"


def make_opener():
    opener = build_opener()
    opener.addheaders = [("User-Agent", USER_AGENT)]
    return opener


def api_get(opener, **params):
    params.setdefault("format", "json")
    url = API + "?" + urlencode(params)
    with opener.open(url, timeout=60) as response:
        return json.load(response)


def category_members(opener, category, namespace=None):
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": "500",
    }
    if namespace is not None:
        params["cmnamespace"] = str(namespace)

    while True:
        data = api_get(opener, **params)
        yield from data["query"]["categorymembers"]
        if "continue" not in data:
            break
        params.update(data["continue"])


def collect_files(opener, root_category, recursive):
    seen_categories = set()
    seen_files = {}

    def visit(category):
        if category in seen_categories:
            return
        seen_categories.add(category)

        for member in category_members(opener, category):
            title = member["title"]
            ns = member["ns"]
            if ns == 6:
                seen_files[title] = member
            elif recursive and ns == 14:
                visit(title)

    visit(root_category)
    return sorted(seen_files)


def image_info(opener, titles):
    results = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i : i + 50]
        data = api_get(
            opener,
            action="query",
            prop="imageinfo",
            iiprop="url|mime|size|extmetadata",
            titles="|".join(chunk),
        )
        for page in data["query"]["pages"].values():
            if "imageinfo" in page:
                results[page["title"]] = page["imageinfo"][0]
        time.sleep(0.1)
    return results


def safe_name(title):
    return title.removeprefix("File:").replace("/", "_")


def download_url(opener, url, dest):
    last_error = "download failed"
    for attempt in range(6):
        try:
            with opener.open(url, timeout=120) as response:
                dest.write_bytes(response.read())
            return None
        except HTTPError as error:
            last_error = f"HTTP {error.code}: {error.reason}"
            if error.code in {429, 500, 502, 503, 504}:
                time.sleep(2 ** attempt)
                continue
            return last_error
        except (URLError, TimeoutError) as error:
            time.sleep(2 ** attempt)
            last_error = str(error)
    return last_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--mime", action="append", default=[])
    args = parser.parse_args()

    out = Path(args.out)
    files_dir = out / "files"
    meta_dir = out / "metadata"
    files_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    opener = make_opener()
    titles = collect_files(opener, args.category, args.recursive)
    info = image_info(opener, titles)

    allowed_mimes = set(args.mime)
    downloaded = []
    skipped = []
    for title in titles:
        item = info.get(title)
        if not item:
            skipped.append({"title": title, "reason": "missing imageinfo"})
            continue
        if allowed_mimes and item.get("mime") not in allowed_mimes:
            skipped.append({"title": title, "reason": f"mime {item.get('mime')}"})
            continue

        name = safe_name(title)
        dest = files_dir / name
        if not dest.exists() or dest.stat().st_size == 0:
            error = download_url(opener, item["url"], dest)
            if error:
                skipped.append({"title": title, "reason": error})
                continue
            time.sleep(0.2)
        downloaded.append({"title": title, "file": str(dest.relative_to(out)), **item})

    (meta_dir / "category.json").write_text(
        json.dumps(
            {
                "category": args.category,
                "recursive": args.recursive,
                "downloaded": downloaded,
                "skipped": skipped,
            },
            indent=2,
        )
    )
    print(f"Category: {args.category}")
    print(f"Files found: {len(titles)}")
    print(f"Downloaded/kept: {len(downloaded)}")
    print(f"Skipped: {len(skipped)}")


if __name__ == "__main__":
    main()
