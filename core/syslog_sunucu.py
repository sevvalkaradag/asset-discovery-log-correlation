import socket
import sqlite3
import os

# Veritabanı dosyası
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


def logu_veritabanina_yaz(ip_adresi, mesaj):
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()
    # gelen logu tabloya ekler
    imlec.execute('''
                  INSERT INTO loglar (kaynak_ip, mesaj)
                  VALUES (?, ?)
                  ''', (ip_adresi, mesaj))
    baglanti.commit()
    baglanti.close()


def syslog_dinle(host="0.0.0.0", port=514):
    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.bind((host, port))
    print(f"[*] Merkezi Log Sunucusu Aktif.")
    print(f"[*] Syslog dinleniyor: {host}:{port} (Durdurmak için Ctrl+C)\n")

    try:
        while True:
            # log paketi gelene kadar bekler
            veri, adres = soket.recvfrom(2048)
            mesaj = veri.decode('utf-8', errors='ignore').strip()
            kaynak_ip = adres[0]

            print(f"[+] {kaynak_ip} Cihazından Log Yakalandı: {mesaj}")
            logu_veritabanina_yaz(kaynak_ip, mesaj)

    except KeyboardInterrupt:
        print("\n[!] Sunucu durduruldu.")
        soket.close()


if __name__ == "__main__":
    syslog_dinle()