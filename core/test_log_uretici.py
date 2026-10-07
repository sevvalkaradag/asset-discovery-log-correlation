import socket


def test_logu_firlat():
    hedef_ip = "127.0.0.1"
    hedef_port = 514

    # log mesajı
    mesaj = "BİTİRME PROJESİ TEST: Bu log test aracı tarafından otomatik üretilmiştir."

    # UDP soketi + mesajı byte a çevir
    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.sendto(mesaj.encode('utf-8'), (hedef_ip, hedef_port))
    soket.close()

    print(f"[+] Test logu başarıyla {hedef_ip}:{hedef_port} hedefine gönderildi!")


if __name__ == "__main__":
    test_logu_firlat()