"""Pembaca berkas basis data SQLite (hanya-baca)
menurut dokumentasi format berkas resmi SQLite.

Membaca byte mentah: header 100 byte, b-tree
tabel (daun 0x0D + interior 0x05), varint, format
record, dan halaman overflow — tanpa memakai
modul sqlite3 sama sekali. sqlite3 hanya wasit
di berkas uji.
"""

import struct


class GalatSQLite(Exception):
    pass


def _varint(data, pos):
    """Varint SQLite: s.d. 8 byte 7-bit big-endian;
    byte ke-9 (bila ada) memakai 8 bit penuh."""
    hasil = 0
    for i in range(9):
        if pos >= len(data):
            raise GalatSQLite("varint terpotong")
        b = data[pos]
        pos += 1
        if i == 8:
            hasil = (hasil << 8) | b
            return hasil, pos
        hasil = (hasil << 7) | (b & 0x7F)
        if not (b & 0x80):
            return hasil, pos
    raise AssertionError("tak tercapai")


# tipe serial -> panjang byte tetap (selain teks/
# blob yang dihitung dari tipenya)
_TETAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 6,
          6: 8, 7: 8, 8: 0, 9: 0}


def _nilai_serial(tipe, mentah):
    if tipe == 0:
        return None
    if tipe in (1, 2, 3, 4, 5, 6):
        return int.from_bytes(mentah, "big",
                              signed=True)
    if tipe == 7:
        return struct.unpack(">d", mentah)[0]
    if tipe == 8:
        return 0
    if tipe == 9:
        return 1
    if tipe >= 12:
        if tipe % 2 == 0:
            return bytes(mentah)
        return mentah.decode("utf-8")
    raise GalatSQLite("tipe serial cadangan: %d"
                      % tipe)


def _baca_record(muata):
    """Muatan sel -> daftar nilai kolom."""
    panjang_header, pos = _varint(muata, 0)
    akhir_header = pos - 0 + (panjang_header -
                              (pos - 0))
    # panjang_header dihitung dari awal muatan
    akhir_header = panjang_header
    tipe = []
    p = pos
    while p < akhir_header:
        t, p = _varint(muata, p)
        tipe.append(t)
    badan = akhir_header
    nilai = []
    for t in tipe:
        if t in _TETAP:
            n = _TETAP[t]
        elif t >= 12:
            n = (t - 12) // 2
        else:
            raise GalatSQLite(
                "tipe serial cadangan: %d" % t)
        nilai.append(_nilai_serial(
            t, muata[badan:badan + n]))
        badan += n
    return nilai


class BasisData:
    def __init__(self, data):
        if len(data) < 100 or \
                data[:16] != b"SQLite format 3\x00":
            raise GalatSQLite(
                "bukan berkas SQLite (header)")
        self.data = data
        (self.ukuran_halaman,) = struct.unpack_from(
            ">H", data, 16)
        if self.ukuran_halaman == 1:
            self.ukuran_halaman = 65536
        self.format_tulis = data[18]
        self.format_baca = data[19]
        (self.jumlah_halaman,) = struct.unpack_from(
            ">I", data, 28)
        (self.kode_teks,) = struct.unpack_from(
            ">I", data, 56)
        if self.kode_teks != 1:
            raise GalatSQLite(
                "hanya enkode UTF-8 didukung")

    def _halaman(self, nomor):
        """nomor 1-based -> bytes halaman."""
        awal = (nomor - 1) * self.ukuran_halaman
        potong = self.data[awal:awal +
                           self.ukuran_halaman]
        if len(potong) < self.ukuran_halaman and \
                nomor != self.jumlah_halaman:
            raise GalatSQLite("halaman terpotong")
        return potong

    def _muatan_sel(self, halaman, awal,
                    muatan_penuh):
        """Muatan sel mulai di offset awal pada
        halaman; ikuti rantai overflow bila perlu."""
        U = self.ukuran_halaman
        X = U - 35
        if muatan_penuh <= X:
            return halaman[awal:awal + muatan_penuh]
        M = ((U - 12) * 32 // 255) - 23
        K = M + (muatan_penuh - M) % (U - 4)
        lokal = K if K <= X else M
        gabung = bytearray(halaman[awal:awal + lokal])
        (berikut,) = struct.unpack_from(
            ">I", halaman, awal + lokal)
        while berikut != 0:
            hal = self._halaman(berikut)
            (berikut,) = struct.unpack_from(
                ">I", hal, 0)
            perlu = muatan_penuh - len(gabung)
            ambil = min(perlu, U - 4)
            gabung += hal[4:4 + ambil]
        return bytes(gabung)

    def _sel_tabel(self, nomor_halaman, hasil):
        """Kumpulkan (rowid, record) dari sub-b-tree
        tabel yang berakar di nomor_halaman."""
        halaman = self._halaman(nomor_halaman)
        geser = 100 if nomor_halaman == 1 else 0
        jenis = halaman[geser]
        # tata letak header b-tree: [jenis 1]
        # [freeblock 2][jumlah sel 2][awal konten 2]
        # [fragmen 1] (+ [anak kanan 4] utk interior)
        (jumlah_sel,) = struct.unpack_from(
            ">H", halaman, geser + 3)
        if jenis == 0x0D:  # daun tabel
            for i in range(jumlah_sel):
                (penunjuk,) = struct.unpack_from(
                    ">H", halaman, geser + 8 + 2 * i)
                panjang, p1 = _varint(halaman,
                                       penunjuk)
                rowid, p2 = _varint(halaman, p1)
                muatan = self._muatan_sel(
                    halaman, p2, panjang)
                hasil.append(
                    (rowid, _baca_record(muatan)))
        elif jenis == 0x05:  # interior tabel
            (anak_kanan,) = struct.unpack_from(
                ">I", halaman, geser + 8)
            for i in range(jumlah_sel):
                (penunjuk,) = struct.unpack_from(
                    ">H", halaman,
                    geser + 12 + 2 * i)
                (anak,) = struct.unpack_from(
                    ">I", halaman, penunjuk)
                self._sel_tabel(anak, hasil)
            self._sel_tabel(anak_kanan, hasil)
        else:
            raise GalatSQLite(
                "jenis halaman tak dikenal: %#x"
                % jenis)

    def _semua_baris(self, akar):
        hasil = []
        self._sel_tabel(akar, hasil)
        hasil.sort(key=lambda r: r[0])
        return hasil

    def daftar_tabel(self):
        """Nama tabel dari sqlite_master."""
        keluar = []
        for rowid, rec in self._semua_baris(1):
            # rec: type, name, tbl_name, rootpage, sql
            if rec[0] == "table":
                keluar.append(rec[1])
        return keluar

    def skema(self, nama):
        for rowid, rec in self._semua_baris(1):
            if rec[0] == "table" and rec[1] == nama:
                return {"akar": rec[3], "sql": rec[4]}
        raise GalatSQLite("tabel tak ada: " + nama)

    def _definisi_kolom(self, sql):
        return self._nama_kolom(sql, True)

    def _nama_kolom(self, sql, dengan_def=False):
        """Nama kolom dari SQL CREATE TABLE: ambil
        daftar di kurung pertama, pisah koma di
        tingkat atas, kata pertama tiap definisi;
        lewati batasan tabel (PRIMARY KEY dll.)."""
        awal = sql.index("(")
        dalam = 0
        akhir = awal
        for i in range(awal, len(sql)):
            if sql[i] == "(":
                dalam += 1
            elif sql[i] == ")":
                dalam -= 1
                if dalam == 0:
                    akhir = i
                    break
        isi = sql[awal + 1:akhir]
        bagian = []
        dalam = 0
        cur = ""
        for ch in isi:
            if ch == "(":
                dalam += 1
            elif ch == ")":
                dalam -= 1
            if ch == "," and dalam == 0:
                bagian.append(cur)
                cur = ""
            else:
                cur += ch
        if cur.strip():
            bagian.append(cur)
        kolom = []
        for b in bagian:
            kata = b.strip().split()
            if not kata:
                continue
            nama = kata[0].strip('"`[]')
            if nama.upper() in (
                    "PRIMARY", "FOREIGN", "UNIQUE",
                    "CHECK", "CONSTRAINT"):
                continue
            kolom.append((nama, b) if dengan_def
                         else nama)
        return kolom

    def baca_tabel(self, nama):
        """Semua baris tabel -> list of dict kolom
        (+ kunci '_rowid_')."""
        info = self.skema(nama)
        kolom = self._definisi_kolom(info["sql"])
        keluar = []
        for rowid, rec in self._semua_baris(
                info["akar"]):
            baris = {"_rowid_": rowid}
            for i, (nama_kol, definisi) in \
                    enumerate(kolom):
                v = rec[i] if i < len(rec) else None
                # Kolom INTEGER PRIMARY KEY adalah
                # alias rowid: record menyimpan NULL
                # di posisinya, nilai aslinya rowid.
                if v is None and "INTEGER" in \
                        definisi.upper() and \
                        "PRIMARY KEY" in \
                        definisi.upper():
                    v = rowid
                baris[nama_kol] = v
            keluar.append(baris)
        return keluar

    def cari_rowid(self, nama, rowid):
        for baris in self.baca_tabel(nama):
            if baris["_rowid_"] == rowid:
                return baris
        return None
