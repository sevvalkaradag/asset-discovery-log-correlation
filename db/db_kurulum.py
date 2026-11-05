import sqlite3
import os

db_yolu = os.path.join(os.path.dirname(__file__), "veritabani.sqlite")

def veritabani_olustur():
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    imlec.execute('''
    CREATE TABLE IF NOT EXISTS cihazlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_adresi TEXT,
        mac_adresi TEXT UNIQUE,
        switch_adi TEXT DEFAULT '-',
        port TEXT DEFAULT '-',
        vlan TEXT DEFAULT '-',
        kaynak TEXT DEFAULT 'ARP',
        durum TEXT DEFAULT 'guvenli',
        isletim_sistemi TEXT DEFAULT 'Bilinmiyor',
        acik_portlar TEXT DEFAULT '-',
        ilk_gorulme TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        son_gorulme TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # tabloya yeni sütunları otomatik ekler
    ek_sutunlar = [
        ("switch_adi", "TEXT DEFAULT '-'"),
        ("port", "TEXT DEFAULT '-'"),
        ("vlan", "TEXT DEFAULT '-'"),
        ("kaynak", "TEXT DEFAULT 'ARP'"),
        ("durum", "TEXT DEFAULT 'guvenli'"),
        ("isletim_sistemi", "TEXT DEFAULT 'Bilinmiyor'"),
        ("acik_portlar", "TEXT DEFAULT '-'")
    ]
    for sutun_adi, veri_tipi in ek_sutunlar:
        try:
            imlec.execute(f"ALTER TABLE cihazlar ADD COLUMN {sutun_adi} {veri_tipi}")
        except sqlite3.OperationalError:
            pass

    imlec.execute('''
    CREATE TABLE IF NOT EXISTS loglar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kaynak_ip TEXT,
        mesaj TEXT,
        zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    baglanti.commit()
    baglanti.close()
    print(f"[*] Veritabanı ve tablolar başarıyla güncellendi: {db_yolu}")

if __name__ == "__main__":
    veritabani_olustur()