# MarCO Forklift AMR — PROJE.md

> **Belgenin amacı:** Bu dosya, MarCO forklift AMR projesinde bundan sonra geliştirilecek navigasyon, saha haritalama, rota tanımlama, görev yürütme ve hassas yanaşma sisteminin **tek ve bağlayıcı teknik referansı** olarak kullanılacaktır.
>
> Bu belge özellikle projeyi devam ettirecek geliştirici veya yapay zekâ aracının mevcut kararları yeniden yorumlamadan, aynı mimari üzerinden ilerleyebilmesi için hazırlanmıştır.
>
> **Ana prensip:** Yarışma alanı önceden bilinmeyecektir. Yarışma alanı görüldüğünde kaynak kod değiştirilmemelidir. Sadece harita ve rota ağı saha üzerinde tanımlanmalıdır.

---

# 1. Projenin Temel Hedefi

Robot, TEKNOFEST 2026 Sanayide Robotik Uygulamalar Yarışması için geliştirilen otonom forklift AMR'dir.

Robotun temel görevi:

1. Yarışma alanını 2D LiDAR ile haritalamak.
2. Haritalama sonrasında yarışmadaki izin verilen rotaları tanımlamak.
3. Yük alma noktalarını (`A1`, `A2`, `A3`) tanımlamak.
4. Yük bırakma noktalarını (`B1`, `B2`, `B3`) tanımlamak.
5. Bekleme/başlangıç noktasını tanımlamak.
6. Kavşak/düğüm noktalarını tanımlamak.
7. Kontrollü kapı / `q5` bölgesini tanımlamak.
8. PLC'den gelen rastgele `Ax -> Bx` görevini almak.
9. Yalnızca önceden tanımlanmış rota ağı üzerinden uygun rotayı hesaplamak.
10. Bu rotayı mümkün olduğunca hassas takip etmek.
11. Alma/bırakma noktasının yaklaşık 1.5 m önünde Nav2 rota takibini bırakıp kamera + QR + renkli çizgi ile hassas yanaşmaya geçmek.
12. Dinamik engelde kaçınmak yerine güvenli şekilde durmak ve engel kalkınca devam etmek.
13. q5 kapı noktasında PLC ile haberleşip geçiş izni beklemek.

---

# 2. Şartnameden Gelen Bağlayıcı Gereksinimler

Kaynak: **TEKNOFEST 2026 Sanayide Robotik Uygulamalar Yarışması Şartnamesi**, sürüm V1.2.

Bu maddeler sistem tasarımını doğrudan belirlemektedir.

## 2.1 Haritalama

Robot üzerindeki 2D lazer alan tarayıcı kullanılarak haritalama yapılabilmelidir.

Seçilen çözüm:

- ROS2
- SLAM Toolbox
- 2D LiDAR
- `map` koordinat sistemi

Haritalama sonunda en az:

```text
map.yaml
map.pgm
```

dosyaları oluşturulmalıdır.

---

## 2.2 Rota Tanımlama

Şartname, forklift arayüzü üzerinden rota tanımlaması yapılabilmesini istemektedir.

Ayrıca yarışma senaryosunda haritalama sonrasında:

- rotalar,
- alma/bırakma noktaları,
- QR noktaları,
- düğüm noktaları,
- kontrollü kapı bölgesi

robot manuel gezdirilerek veya kullanıcı arayüzü üzerinden tanımlanabilir.

**Karar:** Biz iki yöntemi birleştiriyoruz.

- Robot manuel sürülecek.
- Konumlar Flutter arayüzündeki butonlarla kaydedilecek.
- Kaydedilen noktalar ve bağlantılar Nav2 Route Server uyumlu GeoJSON rota ağına dönüştürülecek.

Kullanıcının harita üzerinde piksel seçmesi zorunlu olmayacaktır.

---

## 2.3 Hazırlık Süresi

Haritalama + rota + diğer noktaların tanımlanması için yarışmadan bir veya iki gün önce **60 dakika** verilmektedir.

Bu nedenle saha hazırlama sistemi:

- hızlı,
- deterministik,
- kod yazmadan kullanılabilir,
- terminal bağımlılığı minimum,
- hata kontrolü otomatik

olmalıdır.

---

## 2.4 Rota Sapması

Robot tanımlı rota üzerinde ilerlerken rotadan **en fazla 10 cm** sapabilir.

Bu 10 cm bir kontrol hedefi değildir; maksimum yarışma sınırıdır.

İç tasarım hedefimiz daha sıkı olmalıdır.

Başlangıç için önerilen dahili takip bölgeleri:

```text
0 - 4 cm     : normal
4 - 6 cm     : dikkat / hız azaltılabilir
6 - 8 cm     : yüksek hata / belirgin hız azalt
8 - 10 cm    : kritik bölge
> 10 cm      : şartname sınırı aşılmıştır
```

Bu değerler yarışma şartnamesi değil, geliştirme/tuning için dahili mühendislik hedefidir.

---

## 2.5 Hassas Konumlanma

Bekleme, alma ve bırakma alanlarında:

```text
Konum toleransı : ±7.5 cm
Yön toleransı   : ±5 derece
```

sağlanmalıdır.

Normal Nav2 transit navigasyonu ile istasyona kadar gitmek yerine:

```text
Nav2 rota takibi
       ↓
A/B yaklaşma noktası
       ↓
QR + kamera + renkli çizgi
       ↓
son ~1.5 m
       ↓
hassas pickup/dropoff
```

mimarisi kullanılacaktır.

---

## 2.6 QR + Renkli Çizgi

Alma ve bırakma noktalarının yaklaşık **1.5 metre öncesinde** QR kod bulunacaktır.

Bu QR kod:

- hangi istasyona gelindiğini doğrular,
- hassas yanaşma aşamasına geçiş için kullanılabilir.

QR'dan sonra yere yerleştirilmiş renkli çizgi kamera ile takip edilir.

Bu nedenle sistem **hibrit navigasyon** olacaktır:

```text
LiDAR + localization + Nav2
            +
kamera + QR + line tracking
```

---

## 2.7 Engel Davranışı

Şartnameye göre robot:

- engeli algılamalı,
- güvenli mesafede durmalı,
- engele çarpmamalı,
- engelin etrafından dolaşmamalı,
- engel kaldırılınca görevine devam etmelidir.

Bu nedenle rota sırasında otomatik yeniden planlama ile engelden kaçış **istenmemektedir**.

---

## 2.8 Kontrollü Kapı

`q5` kapı bölgesinde robot:

1. duracak,
2. PLC'ye kapı noktasına ulaştığını bildirecek,
3. izin bekleyecek,
4. izin geldikten sonra devam edecektir.

Bu davranış, rota kapıdan hangi yönde geçerse geçsin uygulanmalıdır.

---

# 3. En Önemli Mimari Karar

## Kullanılacak yapı

```text
                    SAHA HAZIRLAMA

2D LiDAR
   │
   ▼
SLAM Toolbox
   │
   ▼
map.yaml + map.pgm
   │
   ▼
Robot başlangıca getirilir
   │
   ▼
AMCL / localization modu
   │
   ▼
Flutter Rota Tanımlama
   │
   ▼
route_editor ROS2 node
   │
   ▼
field_route.geojson


                    YARIŞMA / OTONOM MOD

PLC veya Flutter görevi
         │
         ▼
Mission Manager
         │
         ▼
Nav2 Route Server
         │
    kayıtlı graph
         │
         ▼
ComputeRoute
         │
         ▼
nav_msgs/Path
         │
         ▼
FollowPath
         │
         ▼
Regulated Pure Pursuit (RPP)
         │
         ▼
cmd_vel
         │
         ▼
STM32 + encoder PID
         │
         ▼
Robot
```

---

# 4. Nav2 Route Tool Konusunda Kesin Karar

Nav2'nin resmi **Route Tool** aracı bir RViz panelidir.

Biz yarışmada RViz üzerinden rota tanımlamayacağız.

Bu nedenle:

> Flutter içine Nav2 Route Tool gömülmeyecektir.

Bunun yerine Flutter tarafında Route Tool'un yaptığı temel işlemler uygulanacaktır:

- node oluşturma,
- edge oluşturma,
- node/edge silme,
- graph doğrulama,
- graph kaydetme.

Çıktı ise Route Tool ile aynı amaca hizmet eden:

```text
GeoJSON route graph
```

olacaktır.

Runtime'da asıl kullanılan Nav2 bileşeni:

```text
nav2_route / Route Server
```

olacaktır.

Özet:

```text
Nav2 Route Tool      = referans editör / debug aracı
Flutter              = bizim yarışma editörümüz
GeoJSON              = ortak veri formatı
Nav2 Route Server    = gerçek runtime rota hesaplayıcı
```

---

# 5. Neden Serbest Nav2 Planlaması Kullanılmıyor?

Robotun yalnızca yarışma alanında tanımlanmış kesikli rotalar üzerinde ilerlemesi gerekir.

Bu nedenle:

```text
NavigateToPose(A2)
```

deyip NavFn/Smac'e serbest alanda yol çizdirmek ana görev navigasyon yöntemi olmayacaktır.

Çünkü bu durumda planner teorik olarak boş alandan kestirme yapabilir.

İstenen:

```text
START
  │
  D1
  │
  D2 ───── D3
           │
           A2
```

ise robot:

```text
START -> D1 -> D2 -> D3 -> A2
```

gitmelidir.

Şunu yapmamalıdır:

```text
START ----------------> A2
```

Bu nedenle **Route Server graph navigasyonu** temel alınacaktır.

---

# 6. Localization: Robot Nerede Olduğunu Nasıl Bilecek?

Nav2'nin kendisi localization sistemi değildir.

Robotun global konumu şu zincirle elde edilir:

```text
Encoderlar
    │
    ▼
Odometri
    │
    ▼
EKF / robot_localization
    │
    ▼
odom -> base_footprint
```

ve:

```text
LiDAR + kayıtlı map
        │
        ▼
       AMCL
        │
        ▼
map -> odom
```

TF ağacı:

```text
map
 └── odom
      └── base_footprint
```

şeklinde olmalıdır.

Sonuç olarak her an:

```text
x
y
yaw
```

değerleri `map` koordinat sisteminde alınabilir.

Rota tanımlama sırasında Flutter'da bir noktaya basıldığında kullanılacak temel bilgi:

```text
TF: map -> base_footprint
```

olacaktır.

---

# 7. Haritalama Modundan Rota Tanımlama Moduna Geçiş

Önerilen yarışma workflow'u:

## Aşama 1 — Haritalama

1. SLAM Toolbox başlat.
2. Robotu manuel sür.
3. Tüm gerekli alanı LiDAR ile tara.
4. Haritalama tamamlanınca robotu **SLAM hâlâ aktifken başlangıç alanına geri getir**.
5. Robot başlangıçta ve sabitken:
   - mevcut `map -> base_footprint` pozunu sakla,
   - haritayı kaydet.
6. SLAM modundan localization moduna geç.
7. Map Server + AMCL başlat.
8. Gerekirse az önce saklanan son SLAM pozu AMCL initial pose olarak kullan.
9. Localization doğrulaması yap.

Bu yaklaşım sayesinde kullanıcıdan RViz üzerinde `2D Pose Estimate` seçmesi istenmemelidir.

---

# 8. Rota Öğretme Mantığı

## 8.1 Ham Sürüş İzi Kaydedilmeyecek

Aracın düz komutta bile sağa/sola kaçabildiği biliniyor.

Örneğin gerçek istenen rota:

```text
D1 ●────────────────────────● A1
```

manuel sürüş:

```text
D1 ●~~~╲___╱~~~╲___╱~~~~~~~● A1
```

olabilir.

**Ham sürüş izi GeoJSON edge geometrisi olarak kullanılmayacaktır.**

Aksi halde araç sonraki çalışmada öğretim sırasında yapılan hataları tekrar takip etmeye çalışır.

---

# 9. Seçilen Rota Öğretme Yöntemi: Anchor / Kontrol Noktaları

Rota geometrisi, operatörün belirlediği düzgün kontrol noktalarından oluşturulacaktır.

## Düz yol

```text
D1 ●────────────────────● A1
```

için:

1. D1 kaydedilir.
2. A1'e gidilir.
3. A1 kaydedilir.
4. Sistem D1 ile A1 arasında düz edge oluşturur.

## Düz olmayan yol

Gerçek rota:

```text
D1 ●─────────────┐
                 │
                 │
                 └──────────● A1
```

ise:

```text
D1
 ↓
ARA NOKTA
 ↓
A1
```

kaydedilir.

Graph geometrisi:

```text
D1 ●────────────● P1
                │
                │
                ● A1
```

olur.

Daha karmaşık geometri:

```text
D1 -> P1 -> P2 -> P3 -> A1
```

şeklinde temsil edilebilir.

**Sistem hiçbir zaman yolların düz veya 90 derece olduğunu varsaymamalıdır.**

Düz yol yalnızca özel ve kolay bir durumdur.

Bu karar sistemin farklı yarışma alanlarında çalışabilmesini sağlar.

---

# 10. Rota Segmenti Kavramı

En önemli pratik detaylardan biridir.

Sadece:

```text
önceki kaydedilen nokta -> yeni kaydedilen nokta
```

şeklinde sınırsız otomatik edge oluşturmak tehlikelidir.

Örneğin:

```text
      A1
      │
D1 ───┼──── D2
```

Operatör:

1. D1'den A1'e gider.
2. A1 kaydeder.
3. tekrar D1'e döner.
4. D2'ye gider.
5. D2 kaydeder.

Yazılım körlemesine son iki kayıt arasında edge oluşturursa:

```text
A1 -> D2
```

diye yanlış bir edge oluşabilir.

Bu nedenle rota tanımlama **segment session** mantığıyla yapılacaktır.

---

# 11. Rota Segmenti Kullanıcı Akışı

Flutter ekranında:

```text
[ ROTA PARÇASI BAŞLAT ]

Başlangıç düğümü:
[D1 ▼]

[ ARA NOKTA EKLE ]

Hedef:
[A1 KAYDET]

[ ROTA PARÇASINI BİTİR ]
```

mantığı bulunmalıdır.

Örnek:

### D1 -> A1 oluşturma

1. Robot fiziksel olarak D1'de.
2. Kullanıcı `Rota Parçası Başlat`.
3. Başlangıç = D1.
4. Robot manuel A1'e sürülür.
5. Yol düz değilse gerekli yerlerde `Ara Nokta`.
6. A1 QR/approach bölgesinde `A1 Kaydet`.
7. Segment tamamlanır.
8. GeoJSON'a D1 <-> A1 bağlantısı yazılır.

### D1 -> D2 oluşturma

1. Robot manuel olarak tekrar D1'e getirilir.
2. Yeni segment başlatılır.
3. Başlangıç olarak **mevcut D1** seçilir.
4. D2'ye gidilir.
5. D2 kaydedilir.
6. D1 <-> D2 edge oluşturulur.

Böylece yanlış `A1 -> D2` bağlantısı oluşmaz.

---

# 12. Flutter Rota Tanımlama Ekranı

Minimum ekran aşağıdaki fonksiyonları içermelidir.

```text
ROTA TANIMLAMA

Localization: HAZIR / HATALI
Robot durmuş: EVET / HAYIR
Aktif harita: field_01

NOKTALAR

[ BAŞLANGIÇ / BEKLEME KAYDET ]

[ DÜĞÜM KAYDET ]

[ A1 KAYDET ]
[ A2 KAYDET ]
[ A3 KAYDET ]

[ B1 KAYDET ]
[ B2 KAYDET ]
[ B3 KAYDET ]

[ q5 / KAPI KAYDET ]

ROTA

[ ROTA PARÇASI BAŞLAT ]
[ ARA NOKTA EKLE ]
[ ROTA PARÇASINI BİTİR ]
[ ROTA PARÇASINI İPTAL ET ]

GRAPH

[ DOĞRULA ]
[ KAYDET ]
[ AKTİFLEŞTİR ]
```

Ek olarak:

```text
Mevcut node listesi
Mevcut edge listesi
Sil
Geri al
```

özellikleri bulunmalıdır.

---

# 13. Nokta Kaydetme Sırasında Yapılacak İşlem

Örneğin kullanıcı:

```text
[D1 KAYDET]
```

butonuna bastı.

Flutter yalnızca backend'e:

```text
type = junction
name = D1
```

gibi semantik bilgi göndermelidir.

Flutter'ın:

- TF hesaplaması,
- GeoJSON yazması,
- ID yönetmesi,
- graph algoritması çalıştırması

istenmemektedir.

Bu işler ROS tarafında yapılmalıdır.

---

# 14. `route_editor` ROS2 Node

Yeni backend bileşeninin önerilen adı:

```text
route_editor_node
```

Yer:

```text
src/marco_navigation/scripts/
```

veya proje yapısına uygun şekilde ayrı bir ROS2 package.

İlk aşamada mevcut `marco_navigation` altında tutulması yeterlidir.

Görevleri:

1. `map -> base_footprint` TF okuyabilmek.
2. Robotun localization sağlığını kontrol etmek.
3. Robot hareketliyken kritik node kaydını reddetmek.
4. Pose ölçümünü kısa süreli örneklemek.
5. Node oluşturmak.
6. Ara nokta oluşturmak.
7. Edge oluşturmak.
8. Çift yönlü edge üretmek.
9. GeoJSON graph belleğini yönetmek.
10. Graph doğrulamak.
11. Dosyaya güvenli/atomik yazmak.
12. Aktif graph yolunu Route Server'a vermek.
13. Flutter'a mevcut graph durumunu yayınlamak.

---

# 15. Node Kaydında Pose Nasıl Alınmalı?

Tek bir anlık AMCL ölçümü doğrudan kaydedilmemelidir.

Robot durmuşken kısa bir pencere kullanılabilir.

Örnek:

```text
0.5 - 1.0 saniye boyunca
map -> base_footprint
```

ölçümleri alınır.

Sonra:

- x için median/ortalama,
- y için median/ortalama,
- yaw için circular mean

hesaplanabilir.

Node ancak localization sağlıklıysa kaydedilir.

Örnek hata durumları:

```text
AMCL pose yok
map->odom TF yok
odom->base_footprint TF yok
LiDAR verisi eski
robot hareket ediyor
covariance çok yüksek
```

Böyle durumda Flutter'a:

```text
NOKTA KAYDEDİLEMEDİ:
Localization güvenilir değil.
```

dönülmelidir.

---

# 16. Semantik Node Tipleri

Backend en az aşağıdaki node tiplerini desteklemelidir:

```text
START_WAIT
JUNCTION
PICKUP_APPROACH
DROPOFF_APPROACH
GATE
INTERMEDIATE
```

Opsiyonel:

```text
CHARGE
QR
```

---

# 17. A1 / B1 Gerçekte Neyi Temsil Edecek?

Önemli karar:

Nav2'nin ulaşacağı A/B graph node'u gerçek palet noktasının kendisi değil, yaklaşık 1.5 m önceki QR + renkli çizgi başlangıcıdır.

Örnek:

```text
normal route
────────────────────● A1_APPROACH
                    QR
                     │
                     │ ~1.5 m
                     │ kamera + çizgi
                     ▼
                    A1 gerçek palet
```

Flutter kullanıcıya:

```text
A1
```

gösterebilir.

Backend'de ise daha açık isim kullanılmalıdır:

```text
alma_1_approach
birak_1_approach
```

PLC görevi:

```text
A1
```

geldiğinde Mission Manager bunu:

```text
alma_1_approach
```

node'una eşlemelidir.

---

# 18. Node Veri Modeli

Önerilen dahili model:

```json
{
  "id": 10,
  "name": "alma_1_approach",
  "type": "PICKUP_APPROACH",
  "x": 4.32,
  "y": 1.87,
  "yaw": 1.57,
  "station_id": "A1"
}
```

Nav2 Route Server'ın zorunlu graph verisiyle uyumlu olması için GeoJSON Point oluşturulacaktır.

Örnek:

```json
{
  "type": "Feature",
  "properties": {
    "id": 10,
    "frame": "map",
    "name": "alma_1_approach",
    "node_type": "pickup_approach",
    "station_id": "A1",
    "yaw": 1.57
  },
  "geometry": {
    "type": "Point",
    "coordinates": [4.32, 1.87]
  }
}
```

Nav2'nin bilmediği ek metadata alanlarının kullanımında parser uyumluluğu test edilmelidir.

---

# 19. Edge Veri Modeli

Edge:

```text
D1 -> A1
```

için:

```json
{
  "type": "Feature",
  "properties": {
    "id": 100,
    "startid": 4,
    "endid": 10,
    "metadata": {
      "abs_speed_limit": 0.30
    }
  },
  "geometry": {
    "type": "MultiLineString",
    "coordinates": [[
      [2.14, 1.05],
      [3.00, 1.05],
      [4.32, 1.87]
    ]]
  }
}
```

Buradaki koordinatlar:

```text
start node
ara noktalar
end node
```

şeklindedir.

---

# 20. Edge Yönü

Nav2 graph yönlüdür.

Eğer fiziksel yol çift yönlü kullanılabilecekse iki edge oluşturulmalıdır:

```text
D1 -> A1
A1 -> D1
```

Mevcut repodaki `phase10_route.geojson` da bu yöntemi kullanmaktadır.

Flutter tarafında her segment için:

```text
Çift yönlü: [✓]
```

varsayılan olabilir.

Ancak veri modeli tek yönlü rota desteğini de korumalıdır.

---

# 21. GeoJSON Dosyası

Final saha graph'ı örnek olarak:

```text
field_route.geojson
```

adıyla saklanacaktır.

**Runtime graph dosyası package `share` klasörüne yazılmamalıdır.**

Önerilen writable saha klasörü:

```text
~/marco_data/fields/<field_name>/
```

Örnek:

```text
~/marco_data/fields/competition/
├── map.yaml
├── map.pgm
├── route.geojson
└── field_meta.json
```

`field_meta.json` örneği:

```json
{
  "name": "competition",
  "created_at": "...",
  "map_file": "map.yaml",
  "route_file": "route.geojson",
  "version": 1
}
```

Kaydetme işlemi:

```text
route.geojson.tmp
       ↓
validation
       ↓
atomic rename
       ↓
route.geojson
```

şeklinde yapılmalıdır.

Son başarılı dosyanın backup'ı tutulabilir.

---

# 22. Graph Aktivasyonu

Flutter'da:

```text
[AKTİFLEŞTİR]
```

butonuna basıldığında:

1. graph yeniden doğrulanır,
2. dosya kaydedilir,
3. aktif graph path'i navigation sistemine aktarılır,
4. Route Server graph'ı bu dosyadan yükler.

**Hot reload API'si varmış gibi varsayılmamalıdır.**

Kullanılan Nav2 / `nav2_route` sürümüne göre gerekirse:

- Route Server lifecycle reconfigure,
- restart,
- launch yeniden başlatma

backend tarafından güvenli şekilde yapılmalıdır.

Bu işlem Flutter kullanıcısına tek buton olarak görünmelidir.

---

# 23. Nav2 Route Server

Mevcut repo:

```text
src/marco_navigation/config/route_server.yaml
```

dosyasına sahiptir.

Mevcut olumlu ayarlar:

```text
route_frame: map
base_frame: base_footprint
path_density: 0.05
GeoJsonGraphFileLoader
DistanceScorer
TimeScorer
DynamicEdgesScorer
```

`path_density: 0.05` yaklaşık 5 cm path örnekleme yoğunluğu sağlar ve korunabilir.

---

# 24. Route Server'da Değiştirilecek Kritik Ayar

Mevcut:

```yaml
smooth_corners: true
smoothing_radius: 0.40
```

İlk yarışma sürümünde:

```yaml
smooth_corners: false
```

kullanılması önerilmektedir.

Sebep:

Rota toleransı yalnızca 10 cm'dir.

Route Server'ın otomatik köşe yumuşatması tanımlanan merkez çizgisini değiştirebilir.

Bizim yaklaşımımızda:

> Operatör hangi geometrik rotayı öğretmişse robotun referans path'i o geometri olmalıdır.

Gerçekten kavisli yol varsa bu kavis:

```text
P1
P2
P3
...
```

ara noktalarıyla bilinçli şekilde tanımlanmalıdır.

Yarışma öncesinde ölçümle doğrulanmadan otomatik 40 cm corner smoothing kullanılmamalıdır.

---

# 25. Route Server Rota Optimizasyonu

PLC örneğin:

```text
Pickup = A2
Dropoff = B3
```

gönderdiğinde robot bütün alanı serbest planlamaz.

Route Server graph üzerinde uygun yolu bulur.

Örnek graph:

```text
             A1
             │
START ─ D1 ─ D2 ─ D3 ─ q5
             │          │
             A2         │
                        D4 ─ B3
```

A2 -> B3:

```text
A2 -> D2 -> D3 -> q5 -> D4 -> B3
```

şeklinde hesaplanabilir.

DistanceScorer ve/veya TimeScorer kullanılarak tanımlı graph içindeki uygun rota seçilir.

---

# 26. Mission Manager ile Entegrasyon

Mevcut:

```text
src/marco_mission/marco_mission/mission_manager.py
```

zaten:

```text
ComputeRoute
    ↓
route_result.path
    ↓
FollowPath
```

akışını kullanmaktadır.

Bu korunacaktır.

Ana değişiklikler:

1. Hard-coded test graph yerine aktif saha graph'ı kullanılmalı.
2. Task isimleri yeni graph semantiğine bağlanmalı.
3. Nav2 sadece `*_approach` node'una kadar gitmeli.
4. Son 1.5 m docking/line tracking'e devredilmeli.
5. Gate davranışı sadece belirli mission aşamasına hard-code edilmemeli.
6. Rota q5'ten geçtiği her durumda gate kontrolü yapılmalı.
7. Return-home rotasında da q5 geçiliyorsa izin mantığı çalışmalı.
8. Loaded/unloaded hareket durumu controller/hız politikasına aktarılmalı.

---

# 27. Navigation Controller Kararı

Gerçek robot config'inde şu an:

```text
DWBLocalPlanner
```

kullanılmaktadır.

Sim config'inde ise:

```text
RegulatedPurePursuitController
```

bulunmaktadır.

**Son karar:** Gerçek robotta da rota takibi için RPP kullanılacaktır.

Gerekçe:

- sistemimizin ana problemi path tracking,
- robot izinli sanal çizgiden ayrılmamalı,
- serbest lokal trajectory optimizasyonu temel ihtiyaç değil,
- endüstriyel/differential drive robot için RPP uygun,
- hız/kavis regülasyonu bulunmaktadır.

---

# 28. RPP Geçişi

Değiştirilecek ana dosya:

```text
src/marco_navigation/config/nav2_params.yaml
```

Mevcut DWB `FollowPath` konfigürasyonu RPP ile değiştirilecektir.

Referans olarak:

```text
src/marco_navigation/config/nav2_sim_params.yaml
```

kullanılabilir.

Ancak:

> Repo ROS2 Humble + özel/backport Nav2 Route yapısı kullanabildiği için parametre isimleri kurulu Nav2 sürümünde doğrulanmadan yeni dokümantasyondan körlemesine kopyalanmamalıdır.

İlk fiziksel testte düşük hız kullanılmalıdır.

Önerilen başlangıç:

```text
0.15 - 0.25 m/s
```

Daha sonra tracking stabil oldukça artırılır.

---

# 29. Araç Düz Gidemiyor Problemi

Bu proje için kritik konudur.

Nav2'nin sürekli düzeltme yapması normaldir.

Ancak:

```text
sol motor ve sağ motor aynı PWM
```

verilmesi iki tekerin aynı hızda döneceği anlamına gelmez.

Nav2 tek başına büyük motor uyumsuzluğunu çözmek için kullanılmamalıdır.

---

# 30. Zorunlu Alt Seviye Motor Kontrolü

STM32 tarafında iki teker için encoder geri beslemeli kapalı çevrim hız kontrolü bulunmalıdır.

```text
Nav2 cmd_vel
     │
     ▼
v, w
     │
     ▼
Differential kinematics
     │
 ┌───┴────┐
 ▼        ▼
sol      sağ
hedef    hedef
hız      hız
 │        │
PID      PID
 │        │
motor    motor
 ▲        ▲
encoder encoder
```

Örneğin Nav2:

```text
v = 0.30 m/s
w = 0
```

verdiğinde sistem aynı PWM değil, doğru **teker hız hedeflerini** üretmelidir.

Encoder PID:

- sol teker hızlıysa azaltır,
- sağ teker yavaşsa artırır.

Bu sistem Nav2 path tracking'in altında çalışmalıdır.

---

# 31. Kontrol Katmanları

Sistem üç farklı kontrol problemi olarak düşünülmelidir.

## Katman 1 — Motor

```text
Encoder PID
```

Amaç:

> İstenen teker hızlarını gerçekten uygulamak.

## Katman 2 — Localization

```text
Encoder odometri + EKF + AMCL + LiDAR
```

Amaç:

> Robotun map üzerinde nerede olduğunu bilmek.

## Katman 3 — Path Tracking

```text
Nav2 RPP
```

Amaç:

> Robotun kayıtlı sanal rota üzerinde kalmasını sağlamak.

Bu katmanlardan biri diğerinin yerine kullanılmamalıdır.

---

# 32. Route Deviation Monitor

Yeni bir ROS2 node gereklidir.

Önerilen isim:

```text
route_guard
```

veya:

```text
route_deviation_monitor
```

Görevi:

1. Aktif referans path'i almak.
2. Robotun `map -> base_footprint` konumunu almak.
3. Robotun path'e en kısa mesafesini hesaplamak.
4. Cross-track error yayınlamak.
5. Hata büyüdüğünde hız düşürme / alarm politikasını tetiklemek.
6. Flutter ve Mission Manager'a hata değerini vermek.

Mevcut Mission Manager zaten:

```text
/route/cross_track_error
```

topic'ini dinlemektedir.

Bu topic için gerçek publisher tamamlanmalıdır.

Önerilen topic'ler:

```text
/route/cross_track_error   std_msgs/Float32
/route/active_edge         std_msgs/String
/route/tracking_state      ...
```

---

# 33. Tracking Error Hız Politikası

İlk tuning için:

```text
< 0.04 m    normal hız
0.04-0.06   dikkat
0.06-0.08   hız azalt
0.08-0.10   çok düşük hız / kritik recovery
> 0.10      violation
```

Bu politika deneysel olarak ayarlanacaktır.

10 cm sınırı yarışma şartnamesidir.

Diğer eşikler dahili güvenlik marjıdır.

Amaç robotun sürekli:

```text
9-10 cm
```

bandında çalışması değildir.

Amaç birkaç cm hata ile kararlı tracking'dir.

---

# 34. İlk Fiziksel Araç Testi

Nav2 path tracking tuning yapılmadan önce:

```text
v = 0.30 m/s
w = 0
```

komutu fiziksel robota verilir.

Robot 5 m yürütülür.

Ölç:

```text
başlangıç merkez çizgisi
vs
5 m sonraki lateral sapma
```

Bu test:

- encoder PID tuning,
- teker çapı kalibrasyonu,
- wheel separation,
- mekanik farklar

için kullanılmalıdır.

Nav2 tuning'e geçmeden önce düşük seviye hareket güvenilir olmalıdır.

---

# 35. Engel Yönetimi

Şartname engelden kaçınmayı istememektedir.

Bu yüzden:

```text
engel
  ↓
STOP
  ↓
WAIT
  ↓
engel kalktı
  ↓
aynı route üzerinde devam
```

davranışı kullanılacaktır.

Mevcut:

```text
marco_safety
collision_monitor
```

mimarisi bu amaçla kullanılmalıdır.

Global rota başka edge'e çevrilerek engelin etrafından dolaşılmamalıdır.

---

# 36. Hassas Docking

Normal route:

```text
D2 -> D3 -> A1_APPROACH
```

noktasında biter.

Sonrasında:

```text
DockToStation
```

action başlatılır.

Akış:

```text
A1_APPROACH
    │
    ├─ QR oku / A1 olduğunu doğrula
    │
    ├─ renkli çizgiyi bul
    │
    ├─ çizgiyi takip et
    │
    └─ final pickup pose
```

Final şartname hedefi:

```text
±7.5 cm
±5°
```

Docking sırasında maksimum transit hızı kullanılmamalıdır.

---

# 37. QR Davranışı

QR istasyon kimliğini doğrulamak için kullanılır.

Önerilen davranış:

1. A1 approach bölgesine ulaş.
2. QR tespit et.
3. QR içeriği beklenen istasyonla eşleşiyor mu kontrol et.
4. Eşleşiyorsa istasyon kimliğini latch et.
5. Final yaklaşmada line tracking kullan.

QR'ın 1.5 m boyunca her frame kesintisiz görünmesi zorunlu varsayılmamalıdır.

Bu, kamera geometrisine göre saha testinde doğrulanacaktır.

---

# 38. Gate / q5 Davranışı

Gate kontrolü bir mission adımına körlemesine hard-code edilmemelidir.

Daha genel davranış:

```text
aktif route q5 node'una geliyor
       ↓
robot q5'e ulaştı
       ↓
STOP
       ↓
PLC GatePermission
       ↓
izin geldi
       ↓
continue
```

Bu davranış:

- pickup sonrası,
- dropoff sonrası,
- eve dönüşte

rota q5'ten geçiyorsa aynı şekilde çalışmalıdır.

---

# 39. Yüklü Hareket

Şartnameye göre yük hareket yönünün tersi tarafta kalmalıdır.

Mission Manager:

```text
loaded = true / false
```

durumunu navigation katmanına aktarmalıdır.

Sistem yüklü taşıma sırasında gerekli yön/reverse davranışını kesin olarak sağlamalıdır.

Mevcut sim RPP konfigürasyonunda reversing desteği bulunmaktadır.

Ancak gerçek saha graph'ı ve path orientation ile reverse davranış **fiziksel testte ayrıca doğrulanmalıdır**.

Sadece:

```text
allow_reversing: true
```

yazılmış olması gereksinimin sağlandığını kanıtlamaz.

---

# 40. Flutter ile ROS Arasındaki Sorumluluk Ayrımı

## Flutter'ın görevi

- kullanıcı arayüzü,
- butonlar,
- graph durumunu göstermek,
- node isimlerini göstermek,
- segment oluşturma akışını yönetmek,
- backend'e komut göndermek,
- hata mesajlarını göstermek,
- validation sonucunu göstermek.

## Flutter'ın yapmaması gerekenler

- TF hesabı,
- AMCL yorumlama,
- route optimization,
- GeoJSON parser'ın ana implementasyonu,
- Nav2 action çağrı mantığı,
- motor kontrolü.

## ROS backend'in görevi

- pose alma,
- localization validation,
- node/edge oluşturma,
- GeoJSON,
- Nav2 Route Server,
- ComputeRoute,
- FollowPath,
- docking,
- safety,
- PLC,
- mission state.

---

# 41. Önerilen ROS API

Exact `.srv` isimleri implementasyon sırasında değişebilir, fakat mantık korunmalıdır.

Önerilen servisler:

```text
/route_editor/start_session
/route_editor/save_node
/route_editor/start_segment
/route_editor/add_intermediate
/route_editor/end_segment
/route_editor/cancel_segment
/route_editor/delete_node
/route_editor/delete_edge
/route_editor/validate
/route_editor/save
/route_editor/activate
```

Önerilen status topic'leri:

```text
/route_editor/status
/route_editor/graph_summary
/route_editor/active_segment
```

Flutter ile ROS arasında mevcut projedeki haberleşme altyapısı kullanılabilir.

Eğer ayrı bridge gerekiyorsa bu bridge yalnızca API taşımalıdır; navigasyon mantığı bridge'e konulmamalıdır.

---

# 42. `save_node` Örnek İstek Mantığı

Flutter:

```json
{
  "name": "D1",
  "type": "JUNCTION"
}
```

gönderir.

Backend:

```text
1. localization healthy?
2. robot stopped?
3. map->base_footprint TF al
4. kısa süre örnekle
5. x/y/yaw hesapla
6. unique ID üret
7. node oluştur
8. response döndür
```

Response:

```json
{
  "success": true,
  "id": 12,
  "name": "D1",
  "x": 2.14,
  "y": 1.05
}
```

---

# 43. Route Segment Internal State

Backend segment session:

```text
IDLE
 ↓
STARTED
 ↓
0..N intermediate point
 ↓
END NODE
 ↓
COMMITTED
```

Segment cancel edilirse geçici noktalar graph'a yazılmamalıdır.

Örnek:

```text
segment.start_node = D1
segment.points = [P1, P2]
segment.end_node = A1
```

Commit sonucu:

```text
edge geometry:
D1 -> P1 -> P2 -> A1
```

---

# 44. Ara Nokta İki Şekilde Tutulabilir

MVP için en basit yaklaşım:

> Her `ARA NOKTA`, graph'ta degree-2 normal node olabilir.

Avantaj:

- implementasyon basit,
- Route Server doğrudan kullanır,
- edge geometrisi kolay.

Daha sonra optimize edilirse ara noktalar edge geometry içine gömülü shape point olarak tutulabilir.

İlk yarışma sürümünde gereksiz soyutlama yapılmamalıdır.

---

# 45. Graph Validation

Flutter'da mutlaka:

```text
[DOĞRULA]
```

butonu bulunmalıdır.

Validation en az şunları yapmalıdır.

## Node kontrolleri

- START var mı?
- A1, A2, A3 var mı?
- B1, B2, B3 var mı?
- q5 var mı?
- duplicate node ID var mı?
- duplicate isim var mı?
- koordinatlar finite mi?

## Edge kontrolleri

- start node gerçekten var mı?
- end node gerçekten var mı?
- self-loop yanlışlıkla oluşmuş mu?
- edge geometry boş mu?
- edge başlangıcı start node'a uyuyor mu?
- edge sonu end node'a uyuyor mu?

## Connectivity

En az:

```text
START -> A1/A2/A3
Ai -> B1/B2/B3
Bi -> START
```

kombinasyonlarında graph route üretilebilmeli.

Yarışma görevi rastgele A ve B seçebildiği için tüm gerekli kombinasyonlar test edilmelidir.

## Gate

Saha topolojisi gerektiriyorsa gerekli geçişlerin q5 üzerinden yapılabildiği kontrol edilmelidir.

## Harita

Mümkünse:

- node occupied hücre üzerinde mi?
- edge duvardan geçiyor mu?
- robot footprint için yeterli koridor var mı?

kontrolleri eklenmelidir.

Mevcut repodaki:

```text
route_graph_validator.py
```

yeniden kullanılmalı veya genişletilmelidir.

---

# 46. Graph Test Fonksiyonu

Validation'dan ayrı olarak:

```text
[ROTA TEST]
```

özelliği faydalıdır.

Kullanıcı örneğin:

```text
START -> A2
```

seçer.

Sistem sadece ComputeRoute çalıştırır.

Flutter:

```text
START -> D1 -> D3 -> A2
mesafe: X m
```

gibi sonucu gösterir.

Fiziksel hareket başlatmak ayrı bir onay gerektirmelidir.

---

# 47. Saha Hazırlama Sonrası Kontrol Listesi

60 dakikalık saha hazırlama aşamasında hedef workflow:

## Haritalama

- [ ] LiDAR çalışıyor.
- [ ] SLAM başladı.
- [ ] Alan tamamlandı.
- [ ] Robot başlangıca geri getirildi.
- [ ] Harita kaydedildi.

## Localization

- [ ] Map Server başladı.
- [ ] AMCL başladı.
- [ ] map->odom mevcut.
- [ ] odom->base_footprint mevcut.
- [ ] Pose covariance kabul edilebilir.
- [ ] Robot hareket ettirilince harita pozu mantıklı.

## Route graph

- [ ] START kaydedildi.
- [ ] A1/A2/A3 kaydedildi.
- [ ] B1/B2/B3 kaydedildi.
- [ ] q5 kaydedildi.
- [ ] gerekli junction'lar kaydedildi.
- [ ] tüm fiziksel rota segmentleri oluşturuldu.

## Validation

- [ ] Graph valid.
- [ ] START -> tüm A.
- [ ] tüm A -> tüm B.
- [ ] tüm B -> START.
- [ ] Gate senaryoları.
- [ ] Edge/duvar kontrolü.

## Smoke test

- [ ] en az bir uzun route çalıştır.
- [ ] en az bir pickup approach.
- [ ] en az bir dropoff approach.
- [ ] q5 stop/permission.
- [ ] obstacle stop/wait.
- [ ] cross-track error logla.

---

# 48. Yarışma Runtime Akışı

Örnek PLC görevi:

```text
A2 -> B3
```

Mission flow:

```text
IDLE / START
    ↓
PLC A2/B3
    ↓
ComputeRoute(START, A2_APPROACH)
    ↓
FollowPath / RPP
    ↓
A2_APPROACH
    ↓
QR + line tracking
    ↓
pickup
    ↓
loaded = true
    ↓
ComputeRoute(A2_APPROACH, B3_APPROACH)
    ↓
route q5 içeriyorsa:
    STOP -> PLC permission -> continue
    ↓
B3_APPROACH
    ↓
QR + line tracking
    ↓
dropoff
    ↓
loaded = false
    ↓
ComputeRoute(B3_APPROACH, START)
    ↓
route q5 içeriyorsa gate behavior
    ↓
START
```

---

# 49. Route Server ve Freespace Planner Ayrımı

Route görevlerinde:

```text
ComputeRoute + FollowPath
```

ana yöntemdir.

Planner Server:

```text
NavFn / Smac
```

serbest alan ana rota üreticisi olarak kullanılmamalıdır.

Planner Server başka recovery veya özel alt görevler için sistemde bulunabilir, fakat yarışma kesikli çizgi navigasyonunun karar vericisi Route Server'dır.

---

# 50. `FollowPath` ve Path Yoğunluğu

Route Server graph üzerinden rota bulduğunda controller'a tek tek yalnızca D1/D2 gibi düğümler vermek yerine yoğun bir `nav_msgs/Path` üretir.

Mevcut:

```yaml
path_density: 0.05
```

değeri yaklaşık 5 cm path noktası yoğunluğudur.

Bu:

```text
D1 ●---------------------------● D2
```

graph edge'ini controller açısından:

```text
●●●●●●●●●●●●●●●●●●●●●●●●●
```

gibi bir referans path'e dönüştürür.

RPP bu path'i takip eder.

---

# 51. Mevcut Repo Durumu

Repository:

```text
wonlock21/marco_ws
```

Ana ilgili package'lar:

```text
lane_tracking
marco_base
marco_bringup
marco_description
marco_docking
marco_localization
marco_mission
marco_msgs
marco_navigation
marco_perception
marco_safety
marco_simulation
```

Bu belge mevcut mimariyi yıkmak için değil, tamamlamak için hazırlanmıştır.

---

# 52. Mevcut Dosyalar ve Yapılacaklar

## `src/marco_navigation/config/route_server.yaml`

Mevcut:

- Route Server
- GeoJSON loader
- DistanceScorer
- TimeScorer
- DynamicEdgesScorer
- path density 0.05

Yapılacak:

- `smooth_corners` başlangıçta kapat.
- active field graph path'i runtime'da ver.
- test/demo graph fallback'ına yarışma modunda güvenme.

---

## `src/marco_navigation/config/nav2_params.yaml`

Mevcut gerçek robot:

```text
DWB
```

Yapılacak:

```text
RPP
```

ile değiştirilmesi.

---

## `src/marco_navigation/config/nav2_sim_params.yaml`

Mevcut:

```text
RPP
allow_reversing
```

var.

Gerçek robot config'i için referans olabilir.

Ancak gerçek Nav2 sürümüyle parametre uyumluluğu doğrulanmalıdır.

---

## `src/marco_navigation/graphs/phase10_route.geojson`

Mevcut graph formatı için iyi örnektir.

Yeni `route_editor` çıktısı bu yapıyla Nav2 Route Server uyumlu olmalıdır.

---

## `src/marco_mission/marco_mission/mission_manager.py`

Mevcut:

```text
ComputeRoute
FollowPath
DockToStation
LiftLoad
PLC
```

entegrasyonu vardır.

Yapılacak:

- dinamik saha graph'ı,
- approach node,
- gate generalization,
- loaded state,
- graph validation integration.

---

## `src/marco_navigation/scripts/route_graph_validator.py`

Mevcut validator yeniden kullanılmalı/geliştirilmelidir.

---

## `marco_docking`

Final 1.5 m kamera/QR/çizgi yaklaşmasının sahibi olmalıdır.

---

## `marco_safety`

Obstacle stop/wait ve collision monitoring için kullanılmalıdır.

---

# 53. Yeni Yazılması Gereken Ana Bileşenler

## 53.1 Route Editor Backend

```text
route_editor_node
```

MVP görevleri:

- save current pose as node,
- start/end route segment,
- intermediate point,
- bidirectional edge,
- GeoJSON save,
- validation,
- activate.

---

## 53.2 Route Guard

```text
route_guard
```

MVP:

- active path,
- current map pose,
- cross-track error,
- publish `/route/cross_track_error`,
- threshold status.

---

## 53.3 Flutter Route Definition Integration

Mevcut Flutter uygulamasına:

```text
Rota Tanımlama
```

sayfası.

Ana işlemler:

- save semantic node,
- segment start/end,
- intermediate,
- validate,
- save,
- activate.

---

# 54. Geliştirme Fazları

Bu sıra değiştirilmemelidir; üst seviye navigasyon, alt katman sağlam olmadan tune edilmemelidir.

## Faz A — Base Control

- [ ] Encoder verisi güvenilir.
- [ ] Sol teker kapalı çevrim hız PID.
- [ ] Sağ teker kapalı çevrim hız PID.
- [ ] `v > 0, w = 0` testi.
- [ ] wheel radius / wheel separation kalibrasyonu.
- [ ] odometri doğrulaması.

**Çıktı:** Robot düz git komutunu makul şekilde uyguluyor.

---

## Faz B — Localization

- [ ] encoder odometry.
- [ ] EKF.
- [ ] `/odometry/filtered`.
- [ ] LiDAR.
- [ ] SLAM Toolbox.
- [ ] map save.
- [ ] Map Server.
- [ ] AMCL.
- [ ] TF zinciri.

**Çıktı:** Robotun `map` pose'u stabil.

---

## Faz C — Route Editor Backend

- [ ] graph data model.
- [ ] save node.
- [ ] start segment.
- [ ] intermediate.
- [ ] end segment.
- [ ] bidirectional edges.
- [ ] GeoJSON writer.
- [ ] save/load.
- [ ] undo/delete.

**Çıktı:** Terminal/service seviyesinde saha graph'ı oluşturulabiliyor.

---

## Faz D — Flutter

- [ ] ROS/API bağlantısı.
- [ ] route definition page.
- [ ] buttons.
- [ ] node list.
- [ ] edge list.
- [ ] validation.
- [ ] save.
- [ ] activate.
- [ ] status/errors.

**Çıktı:** Rota tanımlamak için RViz/terminal gerekmiyor.

---

## Faz E — Route Server

- [ ] generated GeoJSON load.
- [ ] ComputeRoute tests.
- [ ] all A/B combinations.
- [ ] graph activation workflow.
- [ ] speed metadata.

**Çıktı:** Route Server dinamik saha graph'ı üzerinde rota üretiyor.

---

## Faz F — RPP Path Tracking

- [ ] real `nav2_params.yaml` RPP.
- [ ] low-speed test.
- [ ] straight edge.
- [ ] 90° edge.
- [ ] arbitrary polyline.
- [ ] forward/reverse.
- [ ] loaded/unloaded.

**Çıktı:** Robot tanımlı route'u kontrollü takip ediyor.

---

## Faz G — Route Guard

- [ ] cross-track calculation.
- [ ] visualization/log.
- [ ] speed policy.
- [ ] ±10 cm test.

**Çıktı:** Rota sapması ölçülüyor ve yönetiliyor.

---

## Faz H — Docking

- [ ] route -> approach handoff.
- [ ] QR validation.
- [ ] line tracking.
- [ ] pickup.
- [ ] dropoff.
- [ ] ±7.5 cm.
- [ ] ±5°.

---

## Faz I — Gate + PLC + Safety

- [ ] q5 event.
- [ ] PLC permission.
- [ ] return crossing.
- [ ] obstacle stop/wait.
- [ ] resume.
- [ ] mission abort/failsafe.

---

# 55. Test Senaryoları

## T1 — Graph Basic

Graph:

```text
START -- D1 -- D2 -- A1
```

Test:

```text
START -> A1
```

ComputeRoute başarılı olmalı.

---

## T2 — Branch

```text
          A1
          |
START -- D1 -- D2 -- A2
```

Öğretme:

```text
D1 -> A1
D1 -> D2
D2 -> A2
```

Graph'ta yanlış:

```text
A1 -> D2
```

edge oluşmamalıdır.

---

## T3 — Non-straight

```text
D1 ---- P1
         |
         P2 ---- A1
```

RPP bu polyline'ı takip edebilmelidir.

---

## T4 — Random Task

Tüm:

```text
A1/A2/A3
x
B1/B2/B3
```

kombinasyonlarında ComputeRoute çalıştır.

---

## T5 — Cross Track

Robot bilinçli olarak path'ten:

```text
2 cm
5 cm
8 cm
```

offset ile başlatılır.

Route guard doğru hata vermeli.

---

## T6 — Obstacle

Path üzerine engel konur.

Beklenen:

```text
stop
wait
same path resume
```

Reroute olmamalı.

---

## T7 — Gate

q5'e yaklaş.

Beklenen:

```text
STOP
PLC request
WAIT
permission
GO
```

---

## T8 — Docking

Approach node'a Nav2 ile gel.

Son 1.5 m:

```text
QR + line
```

ile tamamla.

---

# 56. Loglanması Gereken Veriler

Her saha testinde en az:

```text
timestamp
robot x/y/yaw
active route
active edge
cross-track error
linear velocity
angular velocity
AMCL covariance
odom
left encoder speed
right encoder speed
obstacle state
mission state
```

loglanmalıdır.

İleride tuning sezgiyle değil veriyle yapılmalıdır.

---

# 57. Yarışma Alanı Bağımsızlığı

Kaynak kod içinde kesinlikle:

```python
A1 = (3.4, 5.7)
D1 = (2.0, 4.0)
```

gibi sabit saha koordinatları bulunmamalıdır.

Kod yalnızca semantiği bilmeli:

```text
pickup
dropoff
junction
gate
start
route
```

Koordinatlar saha hazırlığında oluşturulmalıdır.

Aynı yazılım:

```text
Saha 1
Saha 2
Saha 3
```

için yalnızca:

```text
map + route.geojson
```

değiştirerek çalışmalıdır.

---

# 58. Yarışma Modunda Yasak Kabul Edilecek Şeyler

Saha görüldükten sonra normal akışta:

- kaynak kod düzenlemek,
- Python içinde koordinat değiştirmek,
- YAML'da elle A1 yazmak,
- GeoJSON'u metin editöründe elle düzeltmek,
- RViz üzerinden zorunlu saha setup yapmak,
- her A->B kombinasyonunu ayrı path olarak hard-code etmek

gerekmemelidir.

Bunlardan biri zorunlu hale geliyorsa saha hazırlama aracı eksik tasarlanmış demektir.

---

# 59. Yapılmaması Gereken Mimari Yaklaşımlar

## Yanlış 1

```text
Manuel sürüşteki tüm x/y noktalarını kaydet.
```

Kullanılmayacak.

Sebep: araç yalpalaması route'a işlenir.

---

## Yanlış 2

```text
Sadece A1 koordinatını kaydet.
NavigateToPose(A1).
```

Ana navigasyon yöntemi olmayacak.

Sebep: tanımlı rota dışından kestirme yapabilir.

---

## Yanlış 3

```text
Tüm yollar düzdür ve 90° dönüşlüdür.
```

Varsayılmayacak.

Alan önceden bilinmiyor.

---

## Yanlış 4

```text
Nav2 motor farkını tamamen düzeltir.
```

Kabul edilmeyecek.

Encoder PID zorunludur.

---

## Yanlış 5

```text
10 cm sapma normaldir.
```

Kabul edilmeyecek.

10 cm yarışma üst sınırıdır.

---

## Yanlış 6

```text
Engel varsa başka rota hesapla.
```

Ana yarışma davranışında kullanılmayacak.

Şartname stop/wait istemektedir.

---

## Yanlış 7

```text
Route Tool RViz panelini Flutter'a göm.
```

Yapılmayacak.

Flutter Route Tool mantığını kendi arayüzünde uygular.

---

# 60. AI / Geliştirici İçin Çalışma Kuralları

Bu repository üzerinde çalışan yapay zekâ veya geliştirici:

1. Önce bu `PROJE.md` dosyasını okumalı.
2. Mevcut kodu incelemeden yeni package üretmemeli.
3. Var olan `marco_navigation`, `marco_mission`, `marco_docking`, `marco_safety` yapısını tekrar yazmamalı.
4. Küçük ve test edilebilir değişikliklerle ilerlemeli.
5. Her değişiklikte gerçek robot ve sim konfigürasyon farkını dikkate almalı.
6. ROS2 Humble / mevcut Nav2 sürümüyle parametre uyumluluğunu kontrol etmeli.
7. Kod içine yarışma alanı koordinatı hard-code etmemeli.
8. GeoJSON formatını mevcut `phase10_route.geojson` ile uyumlu tutmalı.
9. Şartname toleranslarını gevşetmemeli.
10. Önce alt seviye hareket ve localization sağlığını doğrulamadan controller tuning yapmamalı.
11. Runtime graph'ı package `share` altına yazmamalı.
12. Yeni API eklerken Flutter ve ROS sorumluluklarını ayırmalı.
13. Safety davranışını test için devre dışı bırakıp kalıcı bırakmamalı.
14. Route graph invalid ise yarışma modunu başlatmamalı.
15. Hata durumlarını sessizce yutmamalı; Flutter/status/log üzerinden görünür yapmalı.

---

# 61. Yeni Kod Yazmadan Önce Kontrol Edilecek Dosyalar

Her AI/geliştirici önce aşağıdakileri incelemelidir:

```text
src/marco_navigation/config/nav2_params.yaml
src/marco_navigation/config/nav2_sim_params.yaml
src/marco_navigation/config/route_server.yaml
src/marco_navigation/graphs/phase10_route.geojson
src/marco_navigation/launch/
src/marco_navigation/scripts/route_graph_validator.py

src/marco_mission/marco_mission/mission_manager.py

src/marco_docking/

src/marco_safety/

src/marco_localization/

src/marco_msgs/
```

Amaç yeni işlevi mevcut sisteme entegre etmektir.

---

# 62. İlk Uygulanacak Somut İş Paketi

İlk implementasyonun hedefi **tüm sistemi birden yazmak değildir**.

İlk milestone:

> Robotun mevcut `map` pozunu buton çağrısıyla kaydedip iki node arasında GeoJSON edge oluşturabilmek.

Minimum test:

1. AMCL çalışıyor.
2. Robot D1'e getiriliyor.
3. Service ile D1 kaydediliyor.
4. Robot A1'e getiriliyor.
5. Service ile A1 kaydediliyor.
6. D1 -> A1 edge oluşturuluyor.
7. `test_route.geojson` yazılıyor.
8. Route Server dosyayı okuyabiliyor.
9. `ComputeRoute(D1, A1)` başarılı.

Flutter bundan sonra bağlanabilir.

---

# 63. İkinci Somut İş Paketi

Branch-safe segment editor:

```text
D1 -> A1
D1 -> D2
```

oluştur.

Kesin kontrol:

```text
A1 -> D2
```

yanlış edge oluşmuyor.

---

# 64. Üçüncü Somut İş Paketi

Arbitrary geometry:

```text
D1 -> P1 -> P2 -> A1
```

route oluştur.

Route Server path üretmeli.

RPP sim veya gerçek robot bu yolu takip etmeli.

---

# 65. Dördüncü Somut İş Paketi

Flutter entegrasyonu.

Flutter yalnızca backend servislerini çağırmalı.

Bu aşamada graph mantığı backend'de zaten test edilmiş olmalıdır.

---

# 66. Definition of Done — Rota Tanımlama

Rota tanımlama sistemi tamamlanmış sayılması için:

- [ ] SLAM sonrası localization çalışıyor.
- [ ] Flutter'dan semantic node kaydedilebiliyor.
- [ ] Node robotun gerçek map pozundan geliyor.
- [ ] Robot hareketliyken yanlış kayıt engelleniyor.
- [ ] Segment start/end mevcut.
- [ ] Ara nokta destekleniyor.
- [ ] Branch'lerde yanlış auto-edge oluşmuyor.
- [ ] Tek/çift yönlü edge destekleniyor.
- [ ] GeoJSON oluşturuluyor.
- [ ] GeoJSON Route Server tarafından okunuyor.
- [ ] Graph validation var.
- [ ] Tüm A/B görevlerinde route bulunuyor.
- [ ] Save/activate tek arayüzden yapılabiliyor.
- [ ] Yarışma alanı koordinatı kodda yok.
- [ ] RViz zorunlu değil.

---

# 67. Definition of Done — Navigasyon

Navigasyon tamamlanmış sayılması için:

- [ ] Route Server tanımlı graph üzerinden route buluyor.
- [ ] FollowPath route path'ini takip ediyor.
- [ ] Gerçek robot RPP kullanıyor.
- [ ] Encoder PID çalışıyor.
- [ ] Cross-track error ölçülüyor.
- [ ] Normal çalışma birkaç cm tracking hedefliyor.
- [ ] 10 cm sınırı test ediliyor.
- [ ] Engel stop/wait çalışıyor.
- [ ] q5 gate handshake çalışıyor.
- [ ] A/B approach'ta docking'e handoff var.
- [ ] QR + line tracking final 1.5 m çalışıyor.
- [ ] ±7.5 cm ve ±5° test ediliyor.
- [ ] loaded hareket yönü şartı doğrulanıyor.

---

# 68. Son Sistem Özeti

Sistemin nihai çalışma biçimi tek diyagramda:

```text
=============================================================
                    SAHA HAZIRLAMA
=============================================================

Manuel sürüş
    │
    ▼
SLAM Toolbox
    │
    ▼
Occupancy Map
    │
    ▼
AMCL Localization
    │
    ▼
Flutter Rota Tanımlama
    │
    ├── START
    ├── Düğüm
    ├── Ara nokta
    ├── A1/A2/A3 approach
    ├── B1/B2/B3 approach
    └── q5
    │
    ▼
route_editor
    │
    ▼
GeoJSON Graph
    │
    ▼
Validation
    │
    ▼
ACTIVATE


=============================================================
                    YARIŞMA
=============================================================

PLC: A2 -> B3
    │
    ▼
Mission Manager
    │
    ▼
Route Server
    │
    ▼
A2'ye tanımlı graph içindeki optimum route
    │
    ▼
FollowPath + RPP
    │
    ▼
Encoder PID'li robot
    │
    ▼
A2_APPROACH
    │
    ▼
QR + Line Tracking
    │
    ▼
Pickup
    │
    ▼
Route Server
    │
    ▼
q5
    │
    ▼
PLC Gate Permission
    │
    ▼
B3_APPROACH
    │
    ▼
QR + Line Tracking
    │
    ▼
Dropoff
    │
    ▼
Return to START
```

---

# 69. Tek Cümlelik Mimari Tanımı

> **Robot önce LiDAR ile alanı haritalar; saha hazırlama sırasında operatör Flutter üzerinden robotun gerçek lokalizasyon pozlarını kullanarak izin verilen rota graph'ını öğretir; graph GeoJSON olarak Nav2 Route Server'a verilir; yarışmada Route Server yalnızca bu tanımlı graph içinde uygun rotayı hesaplar, RPP bu path'i takip eder, encoder PID aracın komutları düzgün uygulamasını sağlar ve istasyonların son yaklaşık 1.5 metresi QR + kamera tabanlı çizgi takibiyle tamamlanır.**

---

# 70. Kaynak / Referanslar

Bu mimari aşağıdaki kaynaklar dikkate alınarak kararlaştırılmıştır:

- TEKNOFEST 2026 Sanayide Robotik Uygulamalar Yarışması Şartnamesi V1.2
- Nav2 Route Server
- Nav2 Route Tool / Route Graph mantığı
- Nav2 Regulated Pure Pursuit Controller
- mevcut `wonlock21/marco_ws` repository mimarisi

Bu dosyadaki kararlarla çelişen eski test kodları veya yorumlar görülürse, önce bu dosyadaki mimari esas alınmalı; çelişki teknik olarak doğrulanıp bilinçli şekilde çözülmelidir.

---

**Belge durumu:** Ana navigasyon ve rota tanımlama mimarisi için kabul edilen güncel tasarım.

**Tarih:** 08.08.2026
