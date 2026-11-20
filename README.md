# Build Your Own — Pembaca Berkas SQLite

Pembaca **format berkas SQLite** dalam Python
murni — hanya-baca, byte mentah, tanpa memakai
modul `sqlite3` sama sekali di kode utamanya.
`sqlite3` hanya menjadi wasit: ia membangun
basis data sungguhan di cakram, build ini
membacanya dari byte, dan semua baris dari semua
tabel harus kembali **identik** lewat kedua
jalan itu.

Beda tegas dengan build 9 (DBDB): itu basis
data mainan yang *ditulis* sendiri. Ini membaca
format produksi yang ditulis program lain —
interoperabilitas format biner nyata.

## Isi

| Berkas | Isi |
| --- | --- |
| `sqliteku.py` | Header 100 byte, varint, record, b-tree tabel (daun + interior), rantai overflow, API tabel/rowid |
| `uji_bersama.py` | Pembuat basis data wasit via sqlite3 |
| `uji_irisan1.py` … `uji_irisan3.py` | Uji per irisan |

## Memakai

```python
from sqliteku import BasisData

db = BasisData(open("data.db", "rb").read())
print(db.daftar_tabel())
for baris in db.baca_tabel("orang"):
    print(baris["_rowid_"], baris["nama"])
print(db.cari_rowid("orang", 42))
```

## Tiga hal yang menentukan

1. **Varint SQLite bukan varint biasa**: s.d.
   8 byte menyumbang 7 bit, tetapi byte ke-9 —
   bila rowid cukup besar — memakai 8 bit penuh.
   Varint gaya protobuf akan salah membaca
   rowid di atas 2⁵⁶.

2. **Sel yang terlalu besar tidak putus, ia
   meluap**: b-tree menyimpan hanya sebagian
   muatan yang dihitung rumus (ambang X = U−35,
   lokal K/M), sisanya dirantai ke halaman
   overflow 4-byte-penunjuk. Baris teks 20 KB
   pada halaman 512 byte adalah uji yang
   membuktikan rantainya.

3. **Kolom `INTEGER PRIMARY KEY` tidak ada di
   record**: ia alias rowid, dan record menyimpan
   NULL di posisinya. Pembaca yang tidak tahu ini
   akan melaporkan id semua baris sebagai None.

## Di luar lingkup

B-tree indeks (pencarian berjalan lewat b-tree
tabel), mode WAL, dan penulisan apa pun.
Enkode teks selain UTF-8 ditolak tegas.

## Lisensi

Kode: MIT. Dokumentasi format berkas SQLite
adalah domain publik.
