# Bot story Instagram @stat.daily

Menayangkan story dari folder `queue/` ke Instagram lewat Instagram API (API setup with Unified login, host graph.facebook.com).

## Cara kerja
1. Desainer mengekspor JPEG 1080x1920 ke `queue/` (urutan nama file = urutan tayang).
2. GitHub Actions berjalan 5x sehari (07:00, 10:00, 13:00, 17:00, 20:00 WIB) dan menayangkan 1 file tiap kali jalan. Bisa juga dijalankan manual lewat Actions → "Tayangkan story" → Run workflow (isi `count` dan matikan `dry_run`).
3. File yang sudah tayang dipindah ke `posted/` dengan awalan tanggal-jam.

Catatan: repo publik, jadi gambar di `queue/` bisa dilihat siapa saja sebelum tayang. Instagram butuh URL publik untuk mengambil gambar.

## Setup (sekali saja)
1. Meta for Developers: app dengan kasus penggunaan Instagram, terhubung ke portofolio bisnis, konfigurasi "Instagram API (Login Terpadu)" (token pengguna sistem, tidak kedaluwarsa), izin `instagram_basic` dan `instagram_content_publish`.
2. Akun Instagram ditambahkan sebagai Penguji Instagram dan undangannya diterima, lalu buat token di langkah "Buat token akses".
3. Di GitHub: Settings → Secrets and variables → Actions:
   - `IG_ACCESS_TOKEN` = token (jangan dibagikan)
   - `IG_USER_ID` = ID akun Instagram (angka)
4. Settings → Actions → General → Workflow permissions: **Read and write permissions**.
5. Uji: Actions → Tayangkan story → Run workflow dengan `dry_run` aktif, lalu satu kali dengan `dry_run` mati.

## Batasan
- Hanya JPG/JPEG yang ditayangkan; file lain dilewati dengan peringatan.
- Batas API Instagram: 100 postingan via API per 24 jam.
- GitHub bisa menonaktifkan workflow terjadwal di repo publik yang tidak aktif 60 hari; commit pemindahan ke `posted/` biasanya menjaganya tetap aktif.
