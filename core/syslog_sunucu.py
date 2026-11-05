import socket
import sqlite3
import os
import re

# veritabanı dosyası
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")

# Log içinden MAC, IP, Port ve VLAN yakalamak için Regex desenleri
MAC_REGEX = re.compile(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})')
IP_REGEX = re.compile(r'\b(10\.10\.\d+\.\d+|172\.20\.20\.\d+)\b')
PORT_REGEX = re.compile(r'\b(eth[0-9]+)\b')
VLAN_REGEX = re.compile(r'vlan\s*([0-9]+)', re.IGNORECASE)


def logu_veritabanina_yaz(kaynak_ip, mesaj):
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    # Log mesajının içinde MAC, iç IP, Port veya VLAN var mı kontrol eder
    mac_eslesme = MAC_REGEX.search(mesaj)
    ip_eslesme = IP_REGEX.search(mesaj)
    port_eslesme = PORT_REGEX.search(mesaj)
    vlan_eslesme = VLAN_REGEX.search(mesaj)

    yakalanan_mac = mac_eslesme.group(1).lower() if mac_eslesme else None
    yakalanan_ip = ip_eslesme.group(1) if ip_eslesme else kaynak_ip
    yakalanan_port = port_eslesme.group(1) if port_eslesme else "-"
    yakalanan_vlan = vlan_eslesme.group(1) if vlan_eslesme else "-"

    # Switch IP'lerini isimlendirir
    switch_haritasi = {
        "172.20.20.10": "switch1",
        "172.20.20.2": "switch2",
        "10.10.10.1": "switch1",
        "10.10.10.2": "switch2"
    }
    switch_adi = switch_haritasi.get(kaynak_ip, "-")

    # Cihazın MAC veya IP si envanterde var mı kontrol eder
    if yakalanan_mac:
        imlec.execute(
            "SELECT id, durum, kaynak FROM cihazlar WHERE mac_adresi = ? OR ip_adresi = ?",
            (yakalanan_mac, yakalanan_ip)
        )
    else:
        imlec.execute("SELECT id, durum, kaynak FROM cihazlar WHERE ip_adresi = ?", (yakalanan_ip,))

    cihaz = imlec.fetchone()

    if cihaz is None:
        # Cihaz envanterde yoksa Güvenlik Uyarısı / Yabancı Cihaz etiketi
        kayit_mac = yakalanan_mac if yakalanan_mac else f"KAYITSIZ-{yakalanan_ip}"
        imlec.execute('''
            INSERT INTO cihazlar (ip_adresi, mac_adresi, switch_adi, port, vlan, kaynak, durum)
            VALUES (?, ?, ?, ?, ?, 'SYSLOG', 'yabanci')
            ON CONFLICT(mac_adresi) DO UPDATE SET son_gorulme=CURRENT_TIMESTAMP
        ''', (yakalanan_ip, kayit_mac, switch_adi, yakalanan_port, yakalanan_vlan))
        print(f"\n[🚨 ALARM] GÜVENLİK UYARISI: Log üzerinden kayıtsız aktivite tespit edildi! (IP: {yakalanan_ip}, MAC: {kayit_mac})")
    else:
        # Cihaz envanterde varsa son görülme zamanını ve kaynak bilgisini günceller
        cihaz_id, mevcut_durum, mevcut_kaynak = cihaz
        yeni_kaynak = mevcut_kaynak if "SYSLOG" in (mevcut_kaynak or "") else f"{mevcut_kaynak}+SYSLOG"
        imlec.execute('''
            UPDATE cihazlar 
            SET son_gorulme = CURRENT_TIMESTAMP, kaynak = ?
            WHERE id = ?
        ''', (yeni_kaynak, cihaz_id))

    # Gelen logu loglar tablosuna ekler
    imlec.execute('''
        INSERT INTO loglar (kaynak_ip, mesaj)
        VALUES (?, ?)
    ''', (kaynak_ip, mesaj))

    baglanti.commit()
    baglanti.close()


def syslog_dinle(host="0.0.0.0", port=514):
    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.bind((host, port))
    print(f"[*] Merkezi Log ve Korelasyon Sunucusu Aktif.")
    print(f"[*] Syslog dinleniyor: {host}:{port} (Durdurmak için Ctrl+C)\n")

    try:
        while True:
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