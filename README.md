# BOLANG
BOla elang

## Menjalankan antarmuka PHP + Flask (Windows)

Ini menambahkan halaman `index.php` sederhana yang berfungsi sebagai landing page ("Selamat datang") dan dapat menampilkan stream video yang disediakan oleh Flask app (`app.py`).

Langkah cepat:

1. Pastikan dependency Python terpasang (lihat file Python di repo). Jalankan Flask secara manual jika ingin kontrol penuh:

	- Buka PowerShell di folder proyek `d:\python\BOLANG`
	- Jalankan: `python app.py`

	Flask akan berjalan di http://127.0.0.1:5000 dan endpoint video berada di `/video`.

2. Jalankan server PHP sederhana untuk membuka `index.php` (atau letakkan file di webserver yang Anda gunakan):

	- Dari folder proyek: `php -S 127.0.0.1:8000`
	- Buka browser ke: http://127.0.0.1:8000/index.php

3. Atau gunakan tombol "Mulai Flask" di halaman untuk mencoba memulai `app.py` dari PHP (Windows). Tombol ini menjalankan perintah background dan membutuhkan PHP yang diizinkan memanggil proses shell.

Catatan keamanan dan izin:
 - Menjalankan perintah sistem dari PHP berisiko. Pastikan Anda hanya menjalankan ini pada lingkungan pengembangan lokal.

