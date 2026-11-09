#!/usr/bin/env python3
"""Tayangkan story Instagram dari folder queue/ lewat Instagram API with Instagram Login.

Alur per gambar (dua langkah resmi):
  1. POST /{id}/media          (image_url + media_type=STORIES)  -> id wadah
  2. GET  /{wadah}?fields=status_code  sampai FINISHED
  3. POST /{id}/media_publish  (creation_id)                     -> tayang
Gambar yang berhasil tayang dihapus dari queue/ (riwayat tayang ada di log run).

Variabel lingkungan:
  IG_ACCESS_TOKEN  (wajib kecuali DRY_RUN=1)  token Instagram jangka panjang
  IG_USER_ID       (wajib)  id akun Instagram (angka)
  MAX_PER_RUN      jumlah story per jalan, default 1
  DRY_RUN          "1" = hanya tampilkan rencana, tidak memanggil API
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_BASE = os.environ.get("IG_API_BASE", "https://graph.facebook.com").rstrip("/")
API_VERSION = os.environ.get("IG_API_VERSION", "v26.0")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_ID = os.environ.get("IG_USER_ID", "").strip()
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN") or "1")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
QUEUE_DIR = Path(os.environ.get("QUEUE_DIR", "queue"))
EXTS = {".jpg", ".jpeg"}

_repo = os.environ.get("GITHUB_REPOSITORY", "")
_ref = os.environ.get("GITHUB_REF_NAME", "main")
PUBLIC_BASE_URL = (
    os.environ.get("PUBLIC_BASE_URL")
    or f"https://raw.githubusercontent.com/{_repo}/{_ref}"
).rstrip("/")

WIB = timezone(timedelta(hours=7))


def mask(text: str) -> str:
    return text.replace(TOKEN, "***") if TOKEN else text


def call(method, path, body=None, params=None):
    url = f"{API_BASE}/{API_VERSION}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = mask(e.read().decode(errors="replace"))
        raise RuntimeError(f"HTTP {e.code} dari {path}: {detail[:500]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Gagal terhubung ke {path}: {mask(str(e.reason))}") from None


def wait_public(url, tries=18, delay=10):
    """Instagram mengunduh gambar sendiri, jadi URL harus sudah bisa dibuka publik."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                resp.read(1)
                return
        except Exception:
            print(f"  menunggu URL publik aktif ({i + 1}/{tries})...")
            time.sleep(delay)
    raise RuntimeError(f"URL publik tidak bisa dibuka: {url}")


def wait_container(container_id, tries=40, delay=3):
    for _ in range(tries):
        status = call("GET", container_id, params={"fields": "status_code"}).get("status_code")
        print(f"  status wadah: {status}")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Wadah gagal diproses (status {status})")
        time.sleep(delay)
    raise RuntimeError("Wadah belum selesai diproses (waktu habis)")


def publish_story(path: Path):
    url = f"{PUBLIC_BASE_URL}/{QUEUE_DIR.as_posix()}/{urllib.parse.quote(path.name)}"
    print(f"Menayangkan {path.name}\n  URL gambar: {url}")
    wait_public(url)
    container = call("POST", f"{IG_ID}/media", body={"image_url": url, "media_type": "STORIES"})
    cid = container["id"]
    print(f"  wadah dibuat: {cid}")
    wait_container(cid)
    result = call("POST", f"{IG_ID}/media_publish", body={"creation_id": cid})
    print(f"  TAYANG, id media: {result.get('id')}")


def main():
    files = sorted(p for p in QUEUE_DIR.glob("*") if p.suffix.lower() in EXTS)
    for other in sorted(QUEUE_DIR.glob("*")):
        if other.is_file() and other.suffix.lower() not in EXTS and other.name != ".gitkeep":
            print(f"PERINGATAN: {other.name} dilewati; hanya file JPG/JPEG yang ditayangkan.")
    if not files:
        print("Antrian kosong, tidak ada story untuk ditayangkan.")
        return 0
    batch = files[:MAX_PER_RUN]
    print(f"Antrian: {len(files)} file; diproses sekarang: {len(batch)}")

    if DRY_RUN:
        for p in batch:
            print(f"[DRY RUN] akan menayangkan: {p.name}")
        return 0
    if not TOKEN:
        print("IG_ACCESS_TOKEN belum diatur.", file=sys.stderr)
        return 2
    if not IG_ID:
        print("IG_USER_ID belum diatur.", file=sys.stderr)
        return 2

    failed = 0
    for p in batch:
        try:
            publish_story(p)
            stamp = datetime.now(WIB).strftime("%Y-%m-%d %H:%M WIB")
            p.unlink()
            print(f"[{stamp}] sudah tayang dan dihapus dari repo: {p.name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"GAGAL untuk {p.name}: {mask(str(e))}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
