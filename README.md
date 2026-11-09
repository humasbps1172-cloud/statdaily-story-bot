# Bot story Instagram @stat.daily (Instagram API, GitHub Actions)

Menayangkan story dari folder `queue/` ke Instagram lewat Instagram API with Instagram Login.
GitHub Actions yang menjalankan skripnya sesuai jadwal. Tidak butuh Metricool dan tidak kena batas 20 post per bulan.

## Cara kerja
1. Desainer mengekspor story sebagai **JPEG 1080x1920 (9:16)**, lalu Anda unggah ke folder `queue/`.
2. Pada jadwal (default 5 kali sehari: 07.00, 10.00, 13.00, 17.00, 20.00 WIB):
   - `publish_story.py` mengambil file tertua di `queue/`, membuat wadah media (media_type=STORIES), menunggu FINISHED, lalu menerbitkannya.
   - File yang tayang dipindah ke `posted/`.
3. Tiap Senin `refresh_token.py` memperpanjang token supaya tidak kedaluwarsa (60 hari sejak perpanjangan).

Satu jalan = satu story, jadi 5 jalan per hari = 5 story per hari. Kalau antrean kurang dari 5, yang tayang hanya yang ada. Ubah jam di `post-story.yml` (cron memakai UTC; WIB = UTC+7). Saat menjalankan manual, isi kolom "count" untuk menayangkan beberapa sekaligus.

## Pemasangan (sekali saja)

### 1. Akun Instagram
- Akun harus **Business**. Dokumentasi Meta menyebut story lewat API dibatasi untuk akun bisnis, jadi akun Creator mungkin tidak bisa.

### 2. Aplikasi Meta dan token
1. Buka developers.facebook.com, buat aplikasi (tipe Business), tambahkan produk Instagram.
2. Buka **API setup with Instagram login**.
3. Di "Generate access tokens": **Add account**, login dengan akun Instagram, setujui izin
   `instagram_business_basic` dan `instagram_business_content_publish`.
4. Klik **Generate token** dan salin segera (hanya tampil sekali). Token berlaku 60 hari.
5. Catat juga ID akun Instagram (tampil di halaman yang sama).

Jangan pernah menempel token di chat atau di file repositori.

### 3. Repositori GitHub
1. Buat repositori **publik** baru (misalnya `statdaily-story-bot`) dan unggah seluruh isi folder ini.
   - Harus publik karena Instagram mengunduh gambar dari URL `raw.githubusercontent.com`.
   - Konsekuensinya: gambar di `queue/` bisa dilihat siapa saja sebelum tayang. Unggah gambar menjelang jam tayang.
2. Settings, Secrets and variables, Actions, **New repository secret**:
   - `IG_ACCESS_TOKEN` = token dari langkah 2
   - `IG_USER_ID` = ID akun Instagram (opsional; kalau kosong dipakai "me")
3. Settings, Actions, General, Workflow permissions: pilih **Read and write permissions**.

### 4. Uji
1. Unggah satu gambar JPEG ke `queue/`.
2. Tab **Actions**, pilih "Tayangkan story Instagram", **Run workflow**. Biarkan centang `dry_run`: skrip hanya menampilkan rencana.
3. Jalankan lagi dengan `dry_run` **dihilangkan** untuk tayang sungguhan.
4. Jalankan juga "Perpanjang token Instagram" sekali untuk memastikan token valid.

## Perawatan
- Token tidak boleh dibiarkan 60 hari tanpa perpanjangan (tidak ada masa tenggang). Kalau workflow perpanjangan gagal atau memberi peringatan token baru, buat token baru di Meta for Developers dan ganti secret.
- GitHub bisa menonaktifkan workflow terjadwal di repositori publik yang tidak ada aktivitas selama 60 hari. Penayangan dan pemindahan file ke `posted/` menghasilkan commit, jadi biasanya aman.
- Jadwal cron GitHub bisa terlambat beberapa menit.
- Ubah jadwal di `.github/workflows/post-story.yml` (zona waktu cron adalah UTC; WIB = UTC+7).

## Batasan API
- Tidak ada stiker interaktif (polling, tautan, pertanyaan) lewat API.
- Ada batas penayangan harian lewat API; jauh di atas kebutuhan ini.
- Story tidak punya keterangan (caption).
- Hanya file JPG/JPEG yang ditayangkan; file lain di `queue/` dilewati dengan peringatan. Skrip tidak mengecek ukuran, jadi pastikan ekspor 1080x1920.
- Skrip ini belum diuji ke server Instagram asli; hanya diuji dengan server tiruan.
