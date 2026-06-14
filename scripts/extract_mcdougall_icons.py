from collections import deque
from pathlib import Path
import warnings

from PIL import Image

warnings.simplefilter("ignore", DeprecationWarning)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "icon_data/iconsets/01_mcdougall_symbol_icon_set/appendix_pages_png"
OUTPUT_DIR = ROOT / "icon_data/iconsets/01_mcdougall_symbol_icon_set/extracted_icons_png"

LEFT_X = 205
RIGHT_X = 900
CROP_W = 330
ROW_YS = [495, 835, 1175, 1515, 1855]
CROP_H_BY_ROW = [225, 225, 225, 225, 255]


def component_boxes(mask, width, height):
    seen = bytearray(width * height)
    boxes = []

    for start in range(width * height):
        if seen[start] or not mask[start]:
            continue

        queue = deque([start])
        seen[start] = 1
        min_x = max_x = start % width
        min_y = max_y = start // width
        area = 0

        while queue:
            idx = queue.popleft()
            area += 1
            x = idx % width
            y = idx // width
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                nidx = ny * width + nx
                if not seen[nidx] and mask[nidx]:
                    seen[nidx] = 1
                    queue.append(nidx)

        boxes.append((min_x, min_y, max_x + 1, max_y + 1, area))

    return boxes


def extract_icon(page_image, x, y, width, height, row_index):
    crop = page_image.crop((x, y, x + width, y + height)).convert("L")
    pixels = list(crop.getdata())

    # Include black symbols and light gray printed symbol backgrounds, but ignore
    # very faint page noise.
    mask = bytearray(1 if value < 245 else 0 for value in pixels)
    boxes = component_boxes(mask, width, height)

    keep = []
    for x1, y1, x2, y2, area in boxes:
        box_w = x2 - x1
        box_h = y2 - y1
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        if area < 8:
            continue

        # Rating text fragments usually sit far to the right of the symbol zone.
        if cx > 255:
            continue

        # Item titles from the next row are near the bottom of the crop. The
        # last row can use the full crop because there is no following title.
        if row_index != 4 and cy > 175 and box_h < 60:
            continue

        # Keep symbol strokes and dense gray symbol backgrounds. Thin text
        # fragments that survive the position filters tend to be small.
        if area >= 20 or box_w >= 12 or box_h >= 12:
            keep.append((x1, y1, x2, y2))

    if not keep:
        return Image.new("RGB", (256, 256), "white")

    min_x = max(0, min(box[0] for box in keep) - 8)
    min_y = max(0, min(box[1] for box in keep) - 8)
    max_x = min(width, max(box[2] for box in keep) + 8)
    max_y = min(height, max(box[3] for box in keep) + 8)

    icon = page_image.crop((x + min_x, y + min_y, x + max_x, y + max_y)).convert("RGB")
    canvas = Image.new("RGB", (256, 256), "white")
    icon.thumbnail((232, 232), Image.Resampling.LANCZOS)
    canvas.paste(icon, ((256 - icon.width) // 2, (256 - icon.height) // 2))
    return canvas


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in OUTPUT_DIR.glob("mcdougall_*.png"):
        old_file.unlink()

    item = 1
    for page_number in range(9, 32):
        page = Image.open(SOURCE_DIR / f"mcdougall_appendix_page-{page_number:02d}.png").convert("RGB")
        for row_index, y in enumerate(ROW_YS):
            for x in (LEFT_X, RIGHT_X):
                icon = extract_icon(page, x, y, CROP_W, CROP_H_BY_ROW[row_index], row_index)
                icon.save(OUTPUT_DIR / f"mcdougall_{item:03d}.png")
                item += 1

    page = Image.open(SOURCE_DIR / "mcdougall_appendix_page-32.png").convert("RGB")
    for row_index in range(4):
        for x in (LEFT_X, RIGHT_X):
            icon = extract_icon(
                page,
                x,
                ROW_YS[row_index],
                CROP_W,
                CROP_H_BY_ROW[row_index],
                row_index,
            )
            icon.save(OUTPUT_DIR / f"mcdougall_{item:03d}.png")
            item += 1

    icon = extract_icon(page, LEFT_X, ROW_YS[4], CROP_W, CROP_H_BY_ROW[4], 4)
    icon.save(OUTPUT_DIR / f"mcdougall_{item:03d}.png")
    item += 1
    print(f"Extracted {item - 1} icons to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
