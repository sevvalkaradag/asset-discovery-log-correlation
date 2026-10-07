import sqlite3
import os

# Veritabanının oluşturulacağı yol (src/db/veritabani.sqlite)
db_yolu = os.path.join(os.path.dirname(__file__), "veritabani.sqlite")

def veritabani_olustur():
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    # cihazların tablosu
    # aynı cihaz tekrar eklendiğinde hata vermesi için mac_adresi UNIQUE
    imlec.execute('''
    CREATE TABLE IF NOT EXISTS cihazlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_adresi TEXT,
        mac_adresi TEXT UNIQUE,
        ilk_gorulme TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        son_gorulme TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Log tablosu
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
    print(f"[*] Veritabanı ve tablolar başarıyla oluşturuldu: {db_yolu}")

if __name__ == "__main__":
    veritabani_olustur()