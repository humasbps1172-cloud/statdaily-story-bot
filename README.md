# Bot Instagram @stat.daily (story + carousel)

Menayangkan story dari folder `queue/` ke Instagram lewat Instagram API (API setup with Unified login, host graph.facebook.com).

## Cara kerja
1. Desainer mengekspor JPEG 1080x1920 ke `queue/` (urutan nama file = urutan tayang).
2. GitHub Actions berjalan 5x sehari (09:37, 10:37, 12:07, 17:37, 18:37 WIB) dan menayangkan 1 file tiap kali jalan. Bisa juga dijalankan manual lewat Actions → "Tayangkan story" → Run workflow (isi `count` dan matikan `dry_run`).
3. File yang sudah tayang dihapus dari `queue/` (riwayat ada di log run Actions). Catatan: file tetap ada di riwayat commit Git yang publik.

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
- GitHub bisa menonaktifkan workflow terjadwal di repo publik yang tidak aktif 60 hari; commit penghapusan file biasanya menjaganya tetap aktif.

## Carousel
Folder `queue_carousel/` berisi satu subfolder per carousel, mis. `queue_carousel/20261112 - Nama Bahasan/`:
- 2 sampai 10 file JPG/JPEG, urut menurut nomor di nama file (`... - Slide 1.jpg` ... `... - Slide 10.jpg`)
- `caption.txt` (wajib, maksimal 2.200 karakter dan 30 hashtag, tanpa baris sumber/kredit foto)

Workflow "Tayangkan carousel" berjalan dua kali sehari (target tayang sekitar 10.00 dan 18.00 WIB; cron 09:15 dan 17:15 WIB karena GitHub biasanya telat) dan tiap jalan menayangkan 1 subfolder tertua (urutan nama, awalan YYYYMMDD). Subfolder yang belum lengkap (tanpa `caption.txt` atau jumlah slide di luar 2-10) dilewati dengan peringatan. Yang sudah tayang dihapus dari `queue_carousel/`.
Uji: Actions → Tayangkan carousel → Run workflow dengan `dry_run` aktif (menampilkan rencana dan caption), lalu matikan `dry_run` untuk tayang sungguhan.
Memakai secrets yang sama dengan bot story (`IG_ACCESS_TOKEN`, `IG_USER_ID`).
