"""Irisan 3 — sapuan diferensial acak terkontrol:
beberapa basis data, ukuran halaman beragam,
semua tipe kolom + NULL + unicode + blob; semua
baris semua tabel identik dengan sqlite3."""
import random

import sqliteku
from uji_bersama import buat, tanya

if __name__ == "__main__":
    cek = 0
    acak = random.Random(30)
    for halaman in (512, 1024, 4096, 8192):
        baris_sql = []
        harap = []
        for i in range(1, 121):
            a = acak.choice([None, 0, 1, -1,
                             acak.randrange(-2 ** 62,
                                            2 ** 62)])
            b = acak.choice([None, 0.0, -1.5,
                             acak.uniform(-1e6, 1e6)])
            c = acak.choice([None, "", "teks",
                             "üñïçødé 水",
                             "panjang " * 40])
            d = acak.choice([None, b"",
                             bytes(acak.randrange(256)
                                   for _ in range(
                                       acak.randrange(
                                           0, 40)))])
            harap.append((i, a, b, c, d))

            def lit(v):
                if v is None:
                    return "NULL"
                if isinstance(v, float):
                    return repr(v)
                if isinstance(v, int):
                    return str(v)
                if isinstance(v, bytes):
                    return "x'%s'" % v.hex()
                return "'%s'" % v.replace(
                    "'", "''")

            baris_sql.append(
                "INSERT INTO t VALUES (%d, %s, %s,"
                " %s, %s);" % (i, lit(a), lit(b),
                               lit(c), lit(d)))
        data = buat("acak%d.db" % halaman, """
            CREATE TABLE t(id INTEGER PRIMARY KEY,
                a INTEGER, b REAL, c TEXT, d BLOB);
            %s
        """ % "\n".join(baris_sql), halaman=halaman)
        db = sqliteku.BasisData(data)
        got = [(r["id"], r["a"], r["b"], r["c"],
                r["d"]) for r in db.baca_tabel("t")]
        wasit = tanya(data, "SELECT id, a, b, c, d "
                            "FROM t ORDER BY rowid")
        assert got == [tuple(w) for w in wasit], \
            halaman
        assert got == harap, halaman
        cek += 1
    # header rusak -> ditolak
    try:
        sqliteku.BasisData(b"bukan basis data" * 20)
        raise AssertionError("header liar diterima")
    except sqliteku.GalatSQLite:
        cek += 1
    print("irisan 3: %d pemeriksaan LULUS" % cek)
