# CATATAN — Build 30: Pembaca Berkas SQLite

Satu halaman per irisan: konsep inti + temuan.
Panduan: dokumentasi format berkas resmi
SQLite. Wasit: sqlite3 pustaka standar.

## Irisan 1 — Header + varint + record (15)

**Konsep.** Berkas dimulai header 100 byte
(string ajaib, ukuran halaman di offset 16,
jumlah halaman, kode teks), dan halaman 1
membawa header itu *plus* b-tree skema —
pembaca yang lupa geseran 100 byte di halaman
pertama akan membaca sampah sebagai sel.
Record adalah dua separuh: header berisi
panjangnya sendiri + daftar tipe serial,
badan berisi nilainya berurutan.

**Temuan.** Tipe serial mengenkode nilai di
dalam tipenya sendiri: 8 dan 9 berarti integer
0 dan 1 *tanpa byte badan sama sekali*, dan
panjang teks/blob dihitung dari tipenya
((N−12)/2 atau (N−13)/2), bukan disimpan
terpisah. Format ini hemat justru karena
kepala dan badan saling mengunci.

## Irisan 2 — B-tree + overflow (604)

**Konsep.** Halaman interior tabel (0x05) tidak
menyimpan record — hanya kunci pembatas + nomor
halaman anak, plus satu penunjuk anak paling
kanan di headernya. Daun (0x0D) menyimpan sel:
panjang muatan (varint), rowid (varint), lalu
muatan — yang mungkin hanya *sebagian* ada di
halaman itu, sisanya di rantai overflow.

**Temuan.** Rumus overflow adalah bagian paling
presisi di seluruh format: ambang X = U−35
memutuskan lokal-vs-luap, dan panjang lokal
K = M + ((P−M) mod (U−4)) dengan M = ((U−12)·32
/255)−23 dirancang agar halaman terakhir
overflow tidak menyisakan remah tak berguna.
Salah satu angka saja dan teks 20 KB di
halaman 512 byte kembali sebagai potongan
diam-diam — makanya irisan ini membandingkan
*setiap* baris ke wasit, bukan sampelnya.

## Irisan 3 — Sapuan diferensial (5)

**Konsep.** Empat basis data acak terkontrol
benih pada ukuran halaman 512/1024/4096/8192,
120 baris masing-masing dengan campuran NULL,
integer 62-bit, float, teks unicode, teks
panjang pemicu overflow kecil, dan blob acak.
Hasil baca dibandingkan tiga arah: build ini,
sqlite3, dan nilai yang dimasukkan.

**Temuan.** Sapuan lulus utuh di keempat ukuran
halaman pada jalan pertama — yang justru
menjadi catatan metodologis seri ini: tiga
build sebelumnya (27, 28, 29) masing-masing
menemukan bug nyata lewat wasitnya, build ini
tidak, dan itu *bukan* bukti formatnya mudah.
Buktinya adalah cakupan ujinya: interior
multi-tingkat (600 baris @512 byte), overflow
rantai panjang, varint 9-byte (rowid 9 miliar),
dan alias rowid semuanya dipaksa muncul oleh
setidaknya satu uji bernama sebelum sapuan
acak berjalan.
