import sqlite3
import os
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

# Veritabanı dosyası
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


def aktif_cihazlari_bul(ip_blogu="172.20.20.0/24"):
    print(f"[*] Hedef ag taraniyor: {ip_blogu}")

    paket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_blogu)

    # Paketleri Containerlab sanal kartından (br-ede5b6949460) göndermek için
    sonuc = srp(paket, timeout=3, verbose=False, iface="br-ede5b6949460")

    cihaz_listesi = []

    # Güvenlik kontrolü: Scapy'den dönen veri boş gelirse
    if sonuc is not None and len(sonuc) == 2:
        cevaplar = sonuc[0]  # Yanıt veren cihazların listesi
        if cevaplar is not None:
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
    # Containerlab IP bloğu -> ana fonksiyon bloğu
    ag_envanteri = aktif_cihazlari_bul("172.20.20.0/24")

    if ag_envanteri:
        veritabanina_kaydet(ag_envanteri)
    else:
        print("[-] Ağda cihaz bulunamadı veya bağlantı kurulamadı.")