"""Irisan 1 — header, varint, record: basis data
mungil terbaca persis; skema cocok sqlite_master
wasit; varint diuji pada nilai tepi formatnya."""
import sqliteku
from sqliteku import _varint
from uji_bersama import buat, tanya

if __name__ == "__main__":
    cek = 0
    # varint: 1 byte, 2 byte, dan bentuk 9 byte
    for nilai, kemas in (
            (0, b"\x00"), (127, b"\x7f"),
            (128, b"\x81\x00"),
            (300, b"\x82\x2c"),
            (2 ** 56 - 1, None),
            (2 ** 64 - 1, b"\xff" * 9)):
        if kemas is not None:
            v, pos = _varint(kemas, 0)
            assert v == nilai and pos == len(kemas)
            cek += 1
    # enkode balik 2**56-1 lewat varint sqlite
    # sesungguhnya diuji lewat rowid besar di
    # irisan 2; di sini cukup header + skema:
    data = buat("kecil.db", """
        CREATE TABLE orang(
            id INTEGER PRIMARY KEY,
            nama TEXT, umur INTEGER, skor REAL,
            foto BLOB, catatan TEXT);
        INSERT INTO orang VALUES
            (1, 'Vero', 30, 9.5, x'00ff', NULL),
            (2, 'Ayu', NULL, -0.25, x'', 'halo');
    """)
    db = sqliteku.BasisData(data)
    assert db.ukuran_halaman == 4096
    assert db.daftar_tabel() == ["orang"]
    cek += 2
    baris = db.baca_tabel("orang")
    assert baris[0]["nama"] == "Vero"
    assert baris[0]["id"] == 1  # alias rowid
    assert baris[0]["foto"] == b"\x00\xff"
    assert baris[0]["catatan"] is None
    assert baris[1]["umur"] is None
    assert baris[1]["skor"] == -0.25
    cek += 6
    wasit = tanya(data, "SELECT id, nama, umur, "
                        "skor, foto, catatan FROM "
                        "orang ORDER BY rowid")
    for b, w in zip(baris, wasit):
        assert (b["id"], b["nama"], b["umur"],
                b["skor"], b["foto"],
                b["catatan"]) == w
        cek += 1
    print("irisan 1: %d pemeriksaan LULUS" % cek)
