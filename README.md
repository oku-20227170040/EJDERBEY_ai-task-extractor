# ai-task-extractor
# Söz Uçar, Yapay Zeka Tutar: NLP Tabanlı Görev Çıkarıcı (AI Task Extractor)

## Proje Hakkında
Bu proje, günlük mesajlaşma metinleri içerisinde kaybolan görev, söz ve planlamaları Doğal Dil İşleme (NLP) teknikleri kullanarak tespit etmeyi amaçlayan bir sistemdir. Geleneksel kural tabanlı yaklaşımlar ve kelime vektörleştirme modelleri (Word2Vec) harmanlanarak, yapısal olmayan gündelik Türkçe sohbet metinlerinden anlamlı görevler çıkarılır ve kullanıcı için otomatik olarak bir takvim etkinliğine (`.ics`) dönüştürülür.

## Temel Özellikler
* **Türkçe Metin Ön İşleme:** Metinlerdeki anlam taşımayan bağlaç ve edatların (Stopwords) temizlenmesi.
* **Kök Bulma (Stemming):** Gelen Türkçe kelimelerin eklerinin atılarak köklerinin tespit edilmesi (TurkishStemmer entegrasyonu).
* **Niyet (Intent) Sınıflandırması:** Cümlenin sıradan bir sohbet mi yoksa bir görev/söz mü içerdiğinin analiz edilmesi.
* **Zaman Çıkarımı:** Tespit edilen görevlerin ne zaman yapılacağına dair zaman etiketlerinin (örn: yarın, akşam) yakalanması.
