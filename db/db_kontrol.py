import sqlite3
import os

db_yolu = os.path.join(os.path.dirname(__file__), "veritabani.sqlite")

def verileri_goster():
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    print("=== ENVANTERDEKİ CİHAZLAR ===")
    imlec.execute("SELECT * FROM cihazlar")
    cihazlar = imlec.fetchall()

    if not cihazlar:
        print("[-] Henüz kayıtlı cihaz yok.")
    else:
        for cihaz in cihazlar:
            # Cihaz Tablosu: id, ip_adresi, mac_adresi, ilk_gorulme, son_gorulme
            print(f"ID: {cihaz[0]} | IP: {cihaz[1]} | MAC: {cihaz[2]} | İlk: {cihaz[3]} | Son: {cihaz[4]}")

    print("\n=== SİSTEMDEKİ LOGLAR ===")
    imlec.execute("SELECT * FROM loglar")
    loglar = imlec.fetchall()

    if not loglar:
        print("[-] Henüz kayıtlı log yok.")
    else:
        for log in loglar:
            # Log Tablosu: id, kaynak_ip, mesaj, zaman
            print(f"ID: {log[0]} | Kaynak IP: {log[1]} | Zaman: {log[3]} | Mesaj: {log[2]}")

    baglanti.close()


if __name__ == "__main__":
    verileri_goster()