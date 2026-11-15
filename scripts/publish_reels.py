#!/usr/bin/env python3
"""Tayangkan Reels Instagram dari folder queue_reels/ (satu subfolder = satu Reels).

Isi tiap subfolder:
  - 1 file video .mp4 atau .mov (9:16, H.264 + AAC, sampai 90 detik, maksimal 300 MB)
  - caption.txt  (teks caption; wajib, maksimal 2.200 karakter dan 30 hashtag)
  - cover.jpg    (opsional; kalau ada dipakai sebagai cover, kalau tidak Instagram mengambil frame video)
Subfolder diproses berurutan menurut nama (awalan YYYYMMDD = yang tertua dulu).

Alur resmi (Reels):
  1. POST /{id}/media  (media_type=REELS, video_url, caption, share_to_feed, cover_url) -> id wadah
  2. GET  /{wadah}?fields=status_code sampai FINISHED (video butuh waktu proses lebih lama dari gambar)
  3. POST /{id}/media_publish (creation_id)                                            -> tayang
Folder yang berhasil tayang dihapus dari queue_reels/.

Variabel lingkungan: sama seperti publish_story.py, ditambah
  REELS_DIR      folder antrean, default queue_reels
  SHARE_TO_FEED  "0" = hanya tampil di tab Reels, default "1" (juga tampil di feed)
  MAX_PER_RUN    jumlah Reels per jalan, default 1
  DRY_RUN        "1" = hanya tampilkan rencana
"""
import re
import shutil
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

import publish_story as ps  # pakai ulang call, wait_public, wait_container, mask

REELS_DIR = Path(ps.os.environ.get("REELS_DIR", "queue_reels"))
SHARE_TO_FEED = ps.os.environ.get("SHARE_TO_FEED", "1") != "0"
CAPTION_FILE = "caption.txt"
VIDEO_EXTS = {".mp4", ".mov"}
COVER_NAMES = {"cover.jpg", "cover.jpeg"}
MAX_CAPTION = 2200
MAX_HASHTAGS = 30
MAX_VIDEO_BYTES = 300 * 1024 * 1024


def read_reel(folder: Path):
    """Kembalikan (video, cover_or_None, caption) atau lempar ValueError kalau belum layak tayang."""
    videos = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS)
    if len(videos) != 1:
        raise ValueError(f"harus ada tepat 1 video .mp4/.mov (ditemukan {len(videos)})")
    video = videos[0]
    if video.stat().st_size > MAX_VIDEO_BYTES:
        raise ValueError(f"video {video.stat().st_size / 1048576:.0f} MB (maksimal 300 MB)")
    cover = next((p for p in folder.iterdir() if p.is_file() and p.name.lower() in COVER_NAMES), None)
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
    return video, cover, caption


def public_url(path: Path) -> str:
    rel = "/".join(urllib.parse.quote(part) for part in path.as_posix().split("/"))
    return f"{ps.PUBLIC_BASE_URL}/{rel}"


def publish_reel(folder: Path, video: Path, cover, caption):
    print(f"Menayangkan Reels: {folder.name}")
    vurl = public_url(video)
    print(f"  video: {video.name}\n    URL: {vurl}")
    ps.wait_public(vurl)
    body = {
        "media_type": "REELS",
        "video_url": vurl,
        "caption": caption,
        "share_to_feed": SHARE_TO_FEED,
    }
    if cover is not None:
        curl = public_url(cover)
        print(f"  cover: {cover.name}\n    URL: {curl}")
        ps.wait_public(curl)
        body["cover_url"] = curl
    container = ps.call("POST", f"{ps.IG_ID}/media", body=body)
    cid = container["id"]
    print(f"  wadah Reels: {cid}")
    # Video diproses lebih lama: tunggu sampai ~15 menit.
    ps.wait_container(cid, tries=150, delay=6)
    result = ps.call("POST", f"{ps.IG_ID}/media_publish", body={"creation_id": cid})
    print(f"  TAYANG, id media: {result.get('id')}")


def main():
    REELS_DIR.mkdir(exist_ok=True)
    folders = sorted(p for p in REELS_DIR.iterdir() if p.is_dir())
    ready = []
    for f in folders:
        try:
            video, cover, caption = read_reel(f)
            ready.append((f, video, cover, caption))
        except ValueError as e:
            print(f"PERINGATAN: {f.name} dilewati: {e}")
    if not ready:
        print("Tidak ada Reels yang siap tayang.")
        return 0
    batch = ready[: ps.MAX_PER_RUN]
    print(f"Antrian siap tayang: {len(ready)} Reels; diproses sekarang: {len(batch)}")

    if ps.DRY_RUN:
        for f, video, cover, caption in batch:
            size = video.stat().st_size / 1048576
            print(f"[DRY RUN] akan menayangkan: {f.name} (video {size:.1f} MB, cover {'ada' if cover else 'otomatis'}, caption {len(caption)} karakter)")
            print("  Caption:\n" + "\n".join("    " + ln for ln in caption.splitlines()))
        return 0
    if not ps.TOKEN:
        print("IG_ACCESS_TOKEN belum diatur.", file=sys.stderr)
        return 2
    if not ps.IG_ID:
        print("IG_USER_ID belum diatur.", file=sys.stderr)
        return 2

    failed = 0
    for f, video, cover, caption in batch:
        try:
            publish_reel(f, video, cover, caption)
            stamp = datetime.now(ps.WIB).strftime("%Y-%m-%d %H:%M WIB")
            shutil.rmtree(f)
            print(f"[{stamp}] sudah tayang dan dihapus dari repo: {f.name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"GAGAL untuk {f.name}: {ps.mask(str(e))}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
