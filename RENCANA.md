# RENCANA — Build 30: Pembaca Berkas SQLite

Sumber: **dokumentasi format berkas resmi
SQLite** (sqlite.org/fileformat2.html) sebagai
panduan, dan **sqlite3 pustaka standar** sebagai
wasit diferensial: basis data dibuat sungguhan
oleh SQLite, dibaca dua jalan — SQL lewat
sqlite3, dan byte mentah lewat build ini —
hasilnya harus sama.

Beda tegas dengan build 9 (DBDB): itu basis data
mainan yang *ditulis* sendiri. Ini membaca
format produksi yang ditulis program lain —
latihan interoperabilitas format biner nyata,
hanya-baca.

## Lingkup

MASUK:
- Header 100 byte: ukuran halaman, format
  tulis/baca, halaman pertama (skema) dari
  offset 100.
- Varint SQLite (big-endian 7-bit, byte ke-9
  penuh 8 bit), format record (header varint +
  tipe serial: NULL, int 8/16/24/32/48/64,
  float64, 0/1, BLOB, TEXT).
- B-tree tabel: halaman daun (0x0D) + interior
  (0x05) ditelusuri rekursif; sel halaman
  meluap (overflow) untuk muatan besar.
- API: daftar tabel dari sqlite_master, baca
  semua baris tabel -> daftar dict kolom, cari
  baris by rowid.
- Validasi: string ajaib header, versi format.

DILUAR (tercatat):
- B-tree indeks (pencarian via indeks) — API
  rowid menelusuri b-tree tabel; WAL/journal
  (basis data wasit dibuat mode delete),
  penulisan apa pun, halaman freelist dibaca
  sebagai kosong.

## Irisan

- [x] Irisan 1 — Header + varint + record:
  basis data mungil buatan sqlite3 terbaca
  byte-eksak dari header & skema.
- [x] Irisan 2 — B-tree tabel + overflow:
  tabel multi-halaman, baris besar meluap,
  semua tipe kolom; diferensial sqlite3.
- [x] Irisan 3 — Sapuan diferensial: beberapa
  basis data acak terkontrol benih (ukuran
  halaman 512..8192, ratusan baris, NULL/teks
  unicode/blob/angka tepi) — semua tabel,
  semua baris identik sqlite3.

## Pagar selesai

- [x] `uji_irisan1.py` … `uji_irisan3.py` hijau.
- [x] `CATATAN.md` satu halaman per irisan.
- [ ] Repo GitHub publik
  `build-your-own-sqlite-python` terbit dan
  terverifikasi (SHA blob lokal == remote, halaman
  publik terbaca).
