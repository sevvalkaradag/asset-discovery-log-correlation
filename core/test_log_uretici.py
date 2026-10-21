import socket
from datetime import datetime


def test_log_gonder(hedef_ip="127.0.0.1", port=514):
    zaman = datetime.now().strftime("%H:%M:%S")
    mesaj = f"OTO-TEST [{zaman}]: Host makineden lokal test basarili!".encode('utf-8')

    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.sendto(mesaj, (hedef_ip, port))
    soket.close()

    print(f"[+] Test logu gönderildi -> {hedef_ip}:{port}")


if __name__ == "__main__":
    test_log_gonder()