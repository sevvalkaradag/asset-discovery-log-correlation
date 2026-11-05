from flask import Flask, render_template, redirect, url_for
import sqlite3
import os
import json
import subprocess

app = Flask(__name__)
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


@app.route('/')
def index():
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    # cihaz envanteri tablosu
    imlec.execute('''
        SELECT mac_adresi, ip_adresi, switch_adi, port, vlan, kaynak, durum, son_gorulme, isletim_sistemi, acik_portlar
        FROM cihazlar
        ORDER BY CASE WHEN durum IN ('yabanci', 'izole') THEN 0 ELSE 1 END, vlan ASC, ip_adresi ASC
    ''')
    cihaz_kayitlari = imlec.fetchall()

    # log kayıtları tablosu
    imlec.execute('''
        SELECT COALESCE(cihazlar.mac_adresi, 'Bilinmiyor'), loglar.kaynak_ip, loglar.mesaj, loglar.zaman, 
               COALESCE(cihazlar.durum, 'guvenli')
        FROM loglar
        LEFT JOIN cihazlar ON loglar.kaynak_ip = cihazlar.ip_adresi
        ORDER BY loglar.id DESC LIMIT 50
    ''')
    korelasyon_kayitlari = imlec.fetchall()

    # istatistikler
    istatistik = {
        "toplam": len(cihaz_kayitlari),
        "arp": sum(1 for c in cihaz_kayitlari if c[5] and "ARP" in c[5]),
        "fdb": sum(1 for c in cihaz_kayitlari if c[5] and "FDB" in c[5]),
        "syslog": sum(1 for c in cihaz_kayitlari if c[5] and "SYSLOG" in c[5]),
        "yabanci": sum(1 for c in cihaz_kayitlari if c[6] in ('yabanci', 'izole'))
    }

    # grafik verileri
    imlec.execute('SELECT COALESCE(isletim_sistemi, "Bilinmiyor"), COUNT(*) FROM cihazlar GROUP BY isletim_sistemi')
    os_data = {str(k): v for k, v in imlec.fetchall()}

    imlec.execute('SELECT COALESCE(vlan, "-"), COUNT(*) FROM cihazlar GROUP BY vlan')
    vlan_data = {str(k): v for k, v in imlec.fetchall()}

    baglanti.close()

    return render_template('index.html',
                           loglar=korelasyon_kayitlari,
                           cihazlar=cihaz_kayitlari,
                           istatistik=istatistik,
                           os_labels=json.dumps(list(os_data.keys())),
                           os_values=json.dumps(list(os_data.values())),
                           vlan_labels=json.dumps(list(vlan_data.keys())),
                           vlan_values=json.dumps(list(vlan_data.values())))


@app.route('/port_kapat/<switch_adi>/<port_adi>')
def port_kapat(switch_adi, port_adi):
    if switch_adi != '-' and port_adi != '-':
        try:
            # switch'e müdahale komutu
            komut = ["sudo", "docker", "exec", f"clab-bitirme-lab-{switch_adi}", "ip", "link", "set", port_adi, "down"]
            subprocess.run(komut, check=True)

            # durumu veritabanında günceller
            baglanti = sqlite3.connect(db_yolu)
            imlec = baglanti.cursor()
            imlec.execute("UPDATE cihazlar SET durum = 'izole' WHERE switch_adi = ? AND port = ?",
                          (switch_adi, port_adi))
            baglanti.commit()
            baglanti.close()
            print(f"[*] GÜVENLİK MÜDAHALESİ: {switch_adi} üzerindeki {port_adi} portu başarıyla kapatıldı!")
        except Exception as e:
            print(f"[!] Port kapatılırken hata oluştu: {e}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)