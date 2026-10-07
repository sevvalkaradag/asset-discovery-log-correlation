Varlık Keşfi ve Log Korelasyon Platformu 🔍

Merhaba! Bu depo, bitirme projem kapsamında sıfırdan geliştirmekte olduğum bir ağdaki cihazları otomatik keşfeden ve sistem loglarını merkezi olarak toplayan arka uç (backend) altyapısını barındırıyor.

Temel amacım; bir şirket ağına bağlanan cihazların envanterini otomatik çıkaran, cihazlardan gelen logları tek bir merkezde toplayan ve bu iki veriyi birbiriyle konuşturarak (korelasyon) "Ağa yabancı bir cihaz bağlandı!" gibi güvenlik alarmları üreten bir platform kurmak.

🛠️ İçeride Neler Var? (Ana Modüller)

Projeyi modüler bir yapıda, 3 temel parçaya ayırdım:

1. Keşif Motoru (src/core/ag_kesif.py): Ağda sürekli ARP taramaları yapıyor. Kim var kim yok bulup, IP ve MAC adreslerini veritabanına işliyor.

2. Syslog Sunucusu (src/core/syslog_sunucu.py): UDP 514 portunda nöbet tutan modülümüz. Ağdaki cihazlardan fırlatılan tüm logları yakalayıp veritabanına kaydediyor.

3. Veritabanı Yönetimi (src/db/): Geçici RAM yerine her şeyi yerel SQLite veritabanında tutuyoruz. db_kurulum.py dosyasını bir kez çalıştırdığınızda ihtiyaç duyulan tüm tablolar (cihazlar, loglar, alarmlar) otomatik oluşuyor. db_kontrol.py ile de "içeride ne verimiz var" diye terminalden bakabiliyoruz.

🚀 Nasıl Kurulur?

Projeyi kendi bilgisayarınızda denemek isterseniz kurulum adımları:

Önce projeyi bilgisayarınıza indirin:

git clone https://github.com/sevvalkaradag/asset-discovery-log-correlation.git
cd asset-discovery-log-correlation


İzole bir Python ortamı (virtual environment) açın:

python3 -m venv .venv
source .venv/bin/activate


Gerekli kütüphaneleri yükleyin:

pip install -r requirements.txt


💻 Nasıl Çalıştırılır?

Sistemin tam verimle çalışması için modülleri farklı terminal pencerelerinde sırayla ayağa kaldırmamız gerekiyor:

Adım 1: Veritabanını hazırlayalım
Sadece ilk seferde tabloları oluşturmak için çalıştırın:

python src/db/db_kurulum.py


Adım 2: Log merkezini dinlemeye alalım
Bir terminalde sürekli açık kalacak şekilde çalıştırın:

python src/core/syslog_sunucu.py


(İpucu: Sistemi test etmek için src/core/test_log_uretici.py dosyasını çalıştırıp sahte log fırlatabilirsiniz).

Adım 3: Ağda keşfi  
Yeni bir terminal açıp keşif motorunu başlatın (Ağa paket yollayacağımız için sudo yetkisi isteyebilir):

sudo python src/core/ag_kesif.py


🔮 Sırada Ne Var? (Yol Haritası)

Şu an projenin arka uç iskeleti büyük ölçüde hazır. Danışman hocamın da değerli yönlendirmesiyle, bir sonraki aşamada sistemi gerçek bir ağda yormak yerine Containerlab kullanarak izole bir sanal ağ (simülasyon) ortamı kuracağım.

Bu sanal ortamda; 1 switch, 3-4 sahte çalışan bilgisayarı (Linux uç makineler) ve 1 merkezi sunucu kurgulayıp, yazdığım korelasyon algoritmasının yabancı makine girişlerini nasıl yakaladığını güvenli bir şekilde test edeceğim.