# EJDERBEY - Akademik NLP Görev Asistanı 🐉

EJDERBEY, dışa aktarılmış WhatsApp sohbet (ZIP veya TXT) dosyalarındaki mesajları analiz ederek, metin içerisindeki görevleri, istekleri ve emirleri Doğal Dil İşleme (NLP) teknikleriyle otomatik olarak tespit eden bir masaüstü uygulamasıdır.

* **Otomatik Görev Çıkarımı:** Sohbet içerisindeki günlük konuşmaları filtreleyerek sadece "yapılması gereken" işleri listeler.
* **Zaman Etiketleme:** Cümle içindeki zaman zarflarını (yarın, akşam, pazartesi vb.) otomatik tespit eder.
* **Dinamik Yönetim:** Bulunan görevleri kişi bazlı filtreleyebilir, düzenleyebilir veya silebilirsiniz.
* **Excel Çıktısı:** Elde edilen görev tablosunu CSV/Excel formatında kaydedebilme.

## 🧠 Kullanılan Doğal Dil İşleme (NLP) Teknikleri
Bu proje basit anahtar kelime eşleştirmesi yerine, Stanford'un **Stanza** kütüphanesini kullanarak derinlemesine morfolojik analiz yapar. Projenin %100'ü kural tabanlı NLP teknikleri üzerine inşa edilmiştir:

1.  **Lemmatization (Kök Bulma):** Kelimelerin çekim eklerinden arındırılarak kök hallerinin (örn: `gerek`, `lazım`, `şart`) tespit edilmesi.
2.  **POS Tagging (Part-of-Speech):** Cümledeki kelimelerin türlerinin (Fiil, İsim, Sıfat) belirlenmesi (`UPOS="VERB"`).
3.  **Morphological Analysis:** Fiillerin aldığı kiplerin incelenmesi. Projede şu kipler görev olarak işaretlenmektedir:
    * `Mood=Nec`: Gereklilik Kipi (-malı, -meli)
    * `Mood=Opt`: İstek/Öneri Kipi (-alım, -elim)
    * `Mood=Imp`: Emir Kipi (Sadece aksiyon bildiren eylemler için)
4.  **Tokenization & Stopword Filtering:** Cümlelerin anlamlı parçalara bölünmesi ve günlük sohbet kalıplarının (zaten, maalesef vb.) filtrelenmesi.

## 🛠️ Kurulum ve Kullanım

### Gereksinimler
Projeyi çalıştırmak için sisteminizde Python 3.7+ yüklü olmalıdır. Gerekli kütüphaneleri kurmak için:

```bash
pip install pandas stanza

Çalıştırma
python EJDERBEY.py

Uygulama açıldığında "ZIP Yükle" butonuna tıklayarak WhatsApp'tan dışa aktardığınız .zip dosyasını seçin. Stanza dil modelinin ilk yüklenmesi (yaklaşık 500MB) biraz zaman alabilir.


