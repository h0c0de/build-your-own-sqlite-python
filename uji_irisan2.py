"""Irisan 2 — b-tree multi-halaman + overflow:
ratusan baris memaksa halaman interior; satu
baris teks 20 KB memaksa rantai overflow;
rowid besar menguji varint panjang."""
import sqliteku
from uji_bersama import buat, tanya

if __name__ == "__main__":
    cek = 0
    sisip = "\n".join(
        "INSERT INTO log VALUES (%d, 'entri-%d');"
        % (i, i) for i in range(1, 601))
    besar = "x" * 20000
    data = buat("besar.db", """
        CREATE TABLE log(id INTEGER PRIMARY KEY,
                         isi TEXT);
        %s
        INSERT INTO log VALUES (9000000000, '%s');
    """ % (sisip, besar), halaman=512)
    db = sqliteku.BasisData(data)
    assert db.ukuran_halaman == 512
    baris = db.baca_tabel("log")
    assert len(baris) == 601
    cek += 2
    wasit = tanya(data, "SELECT id, isi FROM log "
                        "ORDER BY rowid")
    for b, w in zip(baris, wasit):
        assert (b["id"], b["isi"]) == w, b["id"]
        cek += 1
    temu = db.cari_rowid("log", 9000000000)
    assert temu["isi"] == besar
    cek += 1
    print("irisan 2: %d pemeriksaan LULUS" % cek)
