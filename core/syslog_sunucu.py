import socket
import sqlite3
import os

# Veritabanı dosyası
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


def logu_veritabanina_yaz(ip_adresi, mesaj):
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    # 1. Gelen logun IP adresi envanterde var mı kontrol
    imlec.execute("SELECT durum FROM cihazlar WHERE ip_adresi = ?", (ip_adresi,))
    cihaz = imlec.fetchone()

    if cihaz is None:
        # 2. Cihaz envanterde YOK! Güvenlik ihlali tespit edildi
        # Cihazı 'yabanci' durumuyla ve MAC adresi bilinmiyor olarak kaydet
        imlec.execute('''
                      INSERT INTO cihazlar (mac_adresi, ip_adresi, durum)
                      VALUES (?, ?, ?)
                      ''', ('BILINMIYOR (KAYITSIZ)', ip_adresi, 'yabanci'))
        print(f"\n[🚨 ALARM] GÜVENLİK UYARISI: Kayıtsız cihaz tespit edildi! (IP: {ip_adresi})")

    # 3. Gelen logu tabloya ekle
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