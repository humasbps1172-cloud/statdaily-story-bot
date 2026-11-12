#!/usr/bin/env python3
"""Tayangkan carousel Instagram dari folder queue_carousel/ (satu subfolder = satu carousel).

Isi tiap subfolder:
  - 2 sampai 10 file JPG/JPEG (urutan tayang = urutan nomor di nama file, mis. "Slide 2" sebelum "Slide 10")
  - caption.txt  (teks caption; wajib, maksimal 2.200 karakter)
Subfolder diproses berurutan menurut nama (awalan YYYYMMDD = yang tertua dulu).

Alur resmi (carousel):
  1. POST /{id}/media  (image_url + is_carousel_item=true) untuk tiap slide -> id anak
  2. POST /{id}/media  (media_type=CAROUSEL, children, caption)             -> id wadah
  3. GET  /{wadah}?fields=status_code sampai FINISHED
  4. POST /{id}/media_publish (creation_id)                                 -> tayang
Folder yang berhasil tayang dihapus dari queue_carousel/.

Variabel lingkungan: sama seperti publish_story.py, ditambah
  MAX_PER_RUN  jumlah carousel per jalan, default 1
  DRY_RUN      "1" = hanya tampilkan rencana
"""
import re
import shutil
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

import publish_story as ps  # pakai ulang call, wait_public, wait_container, mask

CAROUSEL_DIR = Path(ps.os.environ.get("CAROUSEL_DIR", "queue_carousel"))
CAPTION_FILE = "caption.txt"
MAX_SLIDES = 10
MIN_SLIDES = 2
MAX_CAPTION = 2200
MAX_HASHTAGS = 30


def natural_key(p: Path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def read_carousel(folder: Path):
    """Kembalikan (slides, caption) atau lempar ValueError kalau folder belum layak tayang."""
    slides = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ps.EXTS), key=natural_key)
    if not (MIN_SLIDES <= len(slides) <= MAX_SLIDES):
        raise ValueError(f"jumlah slide {len(slides)} (harus {MIN_SLIDES}-{MAX_SLIDES})")
    cap_path = folder / CAPTION_FILE
    if not cap_path.is_file():
        raise ValueError(f"{CAPTION_FILE} tidak ada")
    caption = cap_path.read_text(encoding="utf-8").strip()
    if not caption:
        raise ValueError(f"{CAPTION_FILE} kosong")
    if len(caption) > MAX_CAPTION:
        raise ValueError(f"caption {len(caption)} karakter (maksimal {MAX_CAPTION})")
    if len(re.findall(r"(?<!\w)#\w+", caption)) > MAX_HASHTAGS:
        raise ValueError(f"hashtag lebih dari {MAX_HASHTAGS}")
    return slides, caption


def public_url(path: Path) -> str:
    rel = "/".join(urllib.parse.quote(part) for part in path.as_posix().split("/"))
    return f"{ps.PUBLIC_BASE_URL}/{rel}"


def publish_carousel(folder: Path, slides, caption):
    print(f"Menayangkan carousel: {folder.name} ({len(slides)} slide)")
    children = []
    for i, s in enumerate(slides, 1):
        url = public_url(s)
        print(f"  slide {i}: {s.name}\n    URL: {url}")
        ps.wait_public(url)
        item = ps.call("POST", f"{ps.IG_ID}/media", body={"image_url": url, "is_carousel_item": True})
        ps.wait_container(item["id"])
        children.append(item["id"])
    parent = ps.call(
        "POST",
        f"{ps.IG_ID}/media",
        body={"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption},
    )
    pid = parent["id"]
    print(f"  wadah carousel: {pid}")
    ps.wait_container(pid)
    result = ps.call("POST", f"{ps.IG_ID}/media_publish", body={"creation_id": pid})
    print(f"  TAYANG, id media: {result.get('id')}")


def main():
    CAROUSEL_DIR.mkdir(exist_ok=True)
    folders = sorted(p for p in CAROUSEL_DIR.iterdir() if p.is_dir())
    ready = []
    for f in folders:
        try:
            slides, caption = read_carousel(f)
            ready.append((f, slides, caption))
        except ValueError as e:
            print(f"PERINGATAN: {f.name} dilewati: {e}")
    if not ready:
        print("Tidak ada carousel yang siap tayang.")
        return 0
    batch = ready[: ps.MAX_PER_RUN]
    print(f"Antrian siap tayang: {len(ready)} carousel; diproses sekarang: {len(batch)}")

    if ps.DRY_RUN:
        for f, slides, caption in batch:
            print(f"[DRY RUN] akan menayangkan: {f.name} ({len(slides)} slide, caption {len(caption)} karakter)")
            print("  Caption:\n" + "\n".join("    " + ln for ln in caption.splitlines()))
        return 0
    if not ps.TOKEN:
        print("IG_ACCESS_TOKEN belum diatur.", file=sys.stderr)
        return 2
    if not ps.IG_ID:
        print("IG_USER_ID belum diatur.", file=sys.stderr)
        return 2

    failed = 0
    for f, slides, caption in batch:
        try:
            publish_carousel(f, slides, caption)
            stamp = datetime.now(ps.WIB).strftime("%Y-%m-%d %H:%M WIB")
            shutil.rmtree(f)
            print(f"[{stamp}] sudah tayang dan dihapus dari repo: {f.name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"GAGAL untuk {f.name}: {ps.mask(str(e))}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
