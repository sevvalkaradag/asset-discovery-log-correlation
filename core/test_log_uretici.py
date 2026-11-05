import socket
import subprocess
import time
from datetime import datetime


def konteynerden_syslog_gonder(konteyner_adi, mesaj, hedef_ip="172.20.20.1", port=514):
    """Containerlab içindeki switch veya PC konteynerinden ana makinedeki Syslog sunucusuna gerçek UDP 514 logu atar."""
    py_komut = (
        f"import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); "
        f"s.sendto({ repr(mesaj.encode('utf-8')) }, ('{hedef_ip}', {port})); s.close()"
    )
    # FRR switch'lerde python3, Alpine PC'lerde nc/sh kullan기 veya doğrudan logger
    sonuc = subprocess.run(
        ["docker", "exec", f"clab-bitirme-lab-{konteyner_adi}", "sh", "-c", f"echo -n '{mesaj}' | nc -u -w1 {hedef_ip} {port}"],
        capture_output=True
    )
    if sonuc.returncode == 0:
        print(f"[+] [{konteyner_adi}] -> Syslog gönderildi: {mesaj}")
    else:
        # Konteyner içinde nc parametresi farklıysa host üzerinden simüle eder
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(mesaj.encode('utf-8'), ("127.0.0.1", port))
        s.close()
        print(f"[+] [Lokal Fallback - {konteyner_adi}] -> {mesaj}")


def senaryolari_calistir():
    zaman = datetime.now().strftime("%b %d %H:%M:%S")
    print("[*] Switch ve Uç Cihaz Syslog Senaryoları Başlatılıyor...\n")

    # Switch1'den gerçek FDB/Port logu (PC1)
    log1 = f"<30>{zaman} switch1 zebra[102]: INTERFACE_UP: dev eth2 vlan 10 mac aa:c1:ab:ec:be:30 ip 10.10.10.11"
    konteynerden_syslog_gonder("switch1", log1)
    time.sleep(0.5)

    # Switch2'den gerçek VLAN 20 FDB logu (PC6)
    log2 = f"<30>{zaman} switch2 br0: FDB_LEARN: dev eth4 vlan 20 mac aa:c1:ab:7a:15:c6 ip 10.10.20.16"
    konteynerden_syslog_gonder("switch2", log2)
    time.sleep(0.5)

    # Switch2'nin portuna Kayıtsız/Yabancı bir cihaz takılması
    log3 = f"<28>{zaman} switch2 security[404]: PORT_SECURITY_WARN: dev eth3 vlan 20 mac de:ad:be:ef:99:99 ip 10.10.20.99"
    konteynerden_syslog_gonder("switch2", log3)
    print("\n[!] Tüm test logları başarıyla gönderildi. Web panelini kontrol edebilirsiniz!")


if __name__ == "__main__":
    senaryolari_calistir()