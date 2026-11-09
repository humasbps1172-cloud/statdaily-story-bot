#!/usr/bin/env python3
"""Perpanjang token Instagram jangka panjang agar tidak kedaluwarsa (berlaku 60 hari sejak perpanjangan).

Token harus sudah berumur lebih dari 24 jam dan belum kedaluwarsa. Dijalankan mingguan.
Token tidak pernah dicetak. Jika Instagram mengembalikan token yang berbeda, skrip memberi
peringatan supaya secret diganti manual.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")


def main():
    if not TOKEN:
        print("IG_ACCESS_TOKEN belum diatur.", file=sys.stderr)
        return 2
    query = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": TOKEN})
    url = f"{API_BASE}/refresh_access_token?{query}"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace").replace(TOKEN, "***")
        print(f"Gagal memperpanjang token: HTTP {e.code} {detail[:400]}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Gagal terhubung: {str(e.reason).replace(TOKEN, '***')}", file=sys.stderr)
        return 1

    days = int(data.get("expires_in", 0)) // 86400
    print(f"Token berhasil diperpanjang; berlaku sekitar {days} hari lagi.")
    if data.get("access_token") and data["access_token"] != TOKEN:
        print("::warning::Instagram mengembalikan token BARU. Ganti secret IG_ACCESS_TOKEN "
              "dengan token dari Meta for Developers (Generate token).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
