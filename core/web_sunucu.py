from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)
# Veritabanı dosyasının yolu
db_yolu = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "veritabani.sqlite")


@app.route('/')
def index():
    baglanti = sqlite3.connect(db_yolu)
    imlec = baglanti.cursor()

    # Loglar sorgusuna cihazlar.durum eklendi
    imlec.execute('''
                  SELECT cihazlar.mac_adresi, cihazlar.ip_adresi, loglar.mesaj, loglar.zaman, cihazlar.durum
                  FROM loglar
                           JOIN cihazlar ON loglar.kaynak_ip = cihazlar.ip_adresi
                  ORDER BY loglar.zaman DESC
                  ''')
    korelasyon_kayitlari = imlec.fetchall()

    # Cihazlar sorgusuna durum eklendi
    imlec.execute('SELECT mac_adresi, ip_adresi, son_gorulme, durum FROM cihazlar ORDER BY son_gorulme DESC')
    cihaz_kayitlari = imlec.fetchall()

    baglanti.close()

    return render_template('index.html', loglar=korelasyon_kayitlari, cihazlar=cihaz_kayitlari)

    # HTML sayfasına bu verileri gönderir
    return render_template('index.html', loglar=korelasyon_kayitlari, cihazlar=cihaz_kayitlari)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)