import sqlite3
import os
from scapy.all import ARP, Ether, srp

# Veritabanı dosyası
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


def aktif_cihazlari_bul(ip_blogu="10.109.246.0/24"):
    print(f"[*] Hedef ag taraniyor: {ip_blogu}")
    paket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_blogu)
    cevaplar, _ = srp(paket, timeout=2, verbose=False)

    cihaz_listesi = []
    for _, gelen_paket in cevaplar:
        cihaz_listesi.append({
            "ip_adresi": gelen_paket.psrc,
            "mac_adresi": gelen_paket.hwsrc
        })
    return cihaz_listesi


def veritabanina_kaydet(cihazlar):
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    for cihaz in cihazlar:
        imlec.execute('''
                      INSERT INTO cihazlar (ip_adresi, mac_adresi)
                      VALUES (?, ?) ON CONFLICT(mac_adresi) 
            DO
                      UPDATE SET ip_adresi=excluded.ip_adresi, son_gorulme= CURRENT_TIMESTAMP
                      ''', (cihaz['ip_adresi'], cihaz['mac_adresi']))

    baglanti.commit()
    baglanti.close()
    print(f"[+] {len(cihazlar)} cihaz başarıyla veritabanına işlendi/güncellendi.")


if __name__ == "__main__":
    ag_envanteri = aktif_cihazlari_bul()

    if ag_envanteri:
        veritabanina_kaydet(ag_envanteri)
    else:
        print("[-] Ağda cihaz bulunamadı.")