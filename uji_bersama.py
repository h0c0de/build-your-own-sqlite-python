"""Pembuat basis data wasit utk build 30: sqlite3
membangun berkas sungguhan di cakram, build ini
membacanya dari byte mentah; sqlite3 juga wasit
pembanding hasil bacanya."""
import os
import sqlite3
import tempfile

DIR = tempfile.mkdtemp(prefix="uji-sqlite-")


def buat(nama, skrip, halaman=None):
    path = os.path.join(DIR, nama)
    if os.path.exists(path):
        os.remove(path)
    kon = sqlite3.connect(path)
    if halaman:
        kon.execute("PRAGMA page_size=%d" % halaman)
    kon.execute("PRAGMA journal_mode=DELETE")
    kon.executescript(skrip)
    kon.commit()
    kon.close()
    with open(path, "rb") as f:
        return f.read()


def tanya(path_data, sql):
    """Jalankan SQL wasit atas salinan data."""
    path = os.path.join(DIR, "wasit.db")
    with open(path, "wb") as f:
        f.write(path_data)
    kon = sqlite3.connect(path)
    hasil = kon.execute(sql).fetchall()
    kon.close()
    return hasil
