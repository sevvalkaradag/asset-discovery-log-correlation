import os
import sqlite3
import subprocess
import json
import socket
from scapy.layers.l2 import Ether, ARP
from scapy.layers.inet import IP, ICMP
from scapy.sendrecv import srp, sr1

db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


def clab_arayuzunu_bul(hedef_ag="172.20.20."):
    sonuc = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True)
    if sonuc.returncode == 0:
        for iface in json.loads(sonuc.stdout):
            for addr in iface.get("addr_info", []):
                if addr.get("local", "").startswith(hedef_ag):
                    return iface.get("ifname")
    return None


def os_ve_port_taramasi(ip_adresi):
    """Hedef IP'nin açık portlarını ve TTL değerinden işletim sistemini tespit eder."""
    if not ip_adresi or ip_adresi == "Bilinmiyor":
        return "Bilinmiyor", "-"

    # TCP port taraması için
    hedef_portlar = [22, 80, 443, 514]
    acik_portlar = []
    for p in hedef_portlar:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)  # Çok hızlı zaman aşımı
            if s.connect_ex((ip_adresi, p)) == 0:
                acik_portlar.append(str(p))
            s.close()
        except:
            pass
    portlar_str = ",".join(acik_portlar) if acik_portlar else "-"

    # ICMP TTL ile OS tespiti
    os_tahmin = "Bilinmiyor"
    try:
        paket = IP(dst=ip_adresi) / ICMP()
        cevap = sr1(paket, timeout=0.5, verbose=False)
        if cevap and IP in cevap:
            ttl = cevap[IP].ttl
            if ttl <= 64:
                os_tahmin = "Linux/Unix (Alpine)"
            elif ttl <= 128:
                os_tahmin = "Windows"
            else:
                os_tahmin = "Ağ Cihazı/Router"
    except:
        pass

    return os_tahmin, portlar_str


def aktif_cihazlari_bul(ip_blogu="172.20.20.0/24"):
    arayuz = clab_arayuzunu_bul()
    print(f"[*] Hedef ag taraniyor: {ip_blogu} (Arayuz: {arayuz})")

    paket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_blogu)
    if arayuz:
        sonuc = srp(paket, timeout=3, verbose=False, iface=arayuz)
    else:
        sonuc = srp(paket, timeout=3, verbose=False)

    cihaz_listesi = []
    if sonuc is not None and len(sonuc) == 2:
        for _, gelen_paket in sonuc[0]:
            ip_adres = gelen_paket.psrc
            os_bilgisi, port_bilgisi = os_ve_port_taramasi(ip_adres)
            cihaz_listesi.append({
                "ip_adresi": ip_adres,
                "mac_adresi": gelen_paket.hwsrc.lower(),
                "switch": "mgmt-br",
                "port": "-",
                "vlan": "Mgmt",
                "kaynak": "ARP",
                "os": os_bilgisi,
                "acik_portlar": port_bilgisi
            })
    return cihaz_listesi


def switch_mac_tablosu_cek():
    kontrol = subprocess.run(
        ["docker", "exec", "clab-bitirme-lab-switch1", "ip", "link", "show", "br0"],
        capture_output=True, text=True
    )
    if kontrol.returncode != 0:
        return []

    hedefler = {
        "log-server": ["10.10.10.1", "10.10.10.14"],
        "pc1": ["10.10.10.1", "10.10.20.16"],
        "pc2": ["10.10.10.1", "10.10.10.14"],
        "pc3": ["10.10.20.1", "10.10.20.15"],
        "pc4": ["10.10.10.1", "10.10.10.11"],
        "pc5": ["10.10.20.1", "10.10.20.13"],
        "pc6": ["10.10.20.1", "10.10.10.11"]
    }

    for cihaz, ipler in hedefler.items():
        komut_str = " ; ".join([f"ping -c 1 -W 1 {ip} >/dev/null 2>&1" for ip in ipler])
        subprocess.run(["docker", "exec", f"clab-bitirme-lab-{cihaz}", "sh", "-c", komut_str],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ip_mac_eslesmesi = {}
    arp_sonuc = subprocess.run(["docker", "exec", "clab-bitirme-lab-switch1", "ip", "neigh", "show"],
                               capture_output=True, text=True)
    if arp_sonuc.returncode == 0:
        for satir in arp_sonuc.stdout.splitlines():
            if "lladdr" in satir and ("vlan10" in satir or "vlan20" in satir):
                parcalar = satir.split()
                ip_mac_eslesmesi[parcalar[parcalar.index("lladdr") + 1].lower()] = parcalar[0]

    uc_portlar = {"switch1": ["eth1", "eth2", "eth3", "eth4"], "switch2": ["eth2", "eth3", "eth4"]}
    switch_cihazlari = []
    gorulen_macler = set()

    for sw, port_listesi in uc_portlar.items():
        sonuc = subprocess.run(["docker", "exec", f"clab-bitirme-lab-{sw}", "bridge", "fdb", "show"],
                               capture_output=True, text=True)
        if sonuc.returncode == 0:
            for satir in sonuc.stdout.splitlines():
                if "vlan" in satir and "permanent" not in satir and "self" not in satir:
                    parcalar = satir.split()
                    mac = parcalar[0].lower()
                    port = parcalar[parcalar.index("dev") + 1]
                    vlan = parcalar[parcalar.index("vlan") + 1]

                    if port in port_listesi and (sw, port, mac) not in gorulen_macler:
                        gorulen_macler.add((sw, port, mac))
                        bulunan_ip = ip_mac_eslesmesi.get(mac, "Bilinmiyor")
                        kaynak_tipi = "FDB+ARP" if bulunan_ip != "Bilinmiyor" else "FDB"

                        os_bilgisi, port_bilgisi = os_ve_port_taramasi(bulunan_ip) if bulunan_ip != "Bilinmiyor" else (
                            "Bilinmiyor", "-")

                        switch_cihazlari.append({
                            "switch": sw, "port": port, "mac_adresi": mac, "vlan": vlan,
                            "ip_adresi": bulunan_ip, "kaynak": kaynak_tipi,
                            "os": os_bilgisi, "acik_portlar": port_bilgisi
                        })
    return switch_cihazlari


def veritabanina_kaydet(cihazlar):
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    for c in cihazlar:
        imlec.execute('''
            INSERT INTO cihazlar (ip_adresi, mac_adresi, switch_adi, port, vlan, kaynak, durum, isletim_sistemi, acik_portlar)
            VALUES (?, ?, ?, ?, ?, ?, 'guvenli', ?, ?) ON CONFLICT(mac_adresi) 
            DO UPDATE SET 
                ip_adresi=excluded.ip_adresi, switch_adi=excluded.switch_adi, port=excluded.port,
                vlan=excluded.vlan, kaynak=excluded.kaynak, isletim_sistemi=excluded.isletim_sistemi,
                acik_portlar=excluded.acik_portlar, son_gorulme=CURRENT_TIMESTAMP
        ''', (c['ip_adresi'], c['mac_adresi'], c.get('switch', '-'), c.get('port', '-'), str(c.get('vlan', '-')),
              c.get('kaynak', 'ARP'), c.get('os', 'Bilinmiyor'), c.get('acik_portlar', '-')))

    baglanti.commit()
    baglanti.close()
    print(f"[+] {len(cihazlar)} cihaz veritabanına işlendi.")


if __name__ == "__main__":
    ag_envanteri = aktif_cihazlari_bul("172.20.20.0/24")
    if ag_envanteri:
        veritabanina_kaydet(ag_envanteri)
        for c in ag_envanteri:
            print(f"    [ARP] IP: {c['ip_adresi']} | OS: {c['os']} | Portlar: {c['acik_portlar']}")

    switch_macleri = switch_mac_tablosu_cek()
    print(f"\n[+] Switch MAC Tablosundan {len(switch_macleri)} kayıt:")
    for m in switch_macleri:
        print(f"    [FDB] IP: {m['ip_adresi']} | OS: {m['os']} | Portlar: {m['acik_portlar']}")
    if switch_macleri:
        veritabanina_kaydet(switch_macleri)