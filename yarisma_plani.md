# MarCO — TEKNOFEST 2026 Yarışmaya Hazırlık Planı

> Durum tarihi: 22 Ağustos 2026  
> Hedef yarışma: Sanayide Robotik Uygulamalar Yarışması  
> Resmî final: 18–20 Eylül 2026, Mezopotamya Uluslararası Fuar ve Kongre Merkezi  
> Planın kapsamı: ROS 2 Humble projesinin şartnameye göre yarışmaya hazır hâle getirilmesi  
> Bu belge hazırlanırken kaynak kodda veya yapılandırmada değişiklik yapılmamıştır.

## 1. Belge dayanağı ve karar sırası

Bu plan aşağıdaki kaynakların birlikte incelenmesiyle hazırlanmıştır:

1. Kullanıcının verdiği `C:\Users\emre\Downloads\2026_SRUY_TR_76gNu.pdf`: 23 sayfa, V1.0, 05.05.2026.
2. [Resmî TEKNOFEST yarışma sayfasının](https://teknofest.org/tr/yarismalar/sanayide-robotik-uygulamalar-yarismasi/) 22.08.2026 tarihinde bağlandığı `2026_SRUY_TR_Hre2P.pdf`: 23 sayfa, V1.1, 20.05.2026.
3. Projedeki `PROJE.md`, `PROJE_PLANI.md`, `yeni_proje_plani.md`, `FAZ0_SOZLESME.md`, `AGENT_REFERANS.md`, `TEST.md`, `src/marco_navigation/maps/README.md` ve `src/marco_base/docs/STM32_UART_PROTOKOL.md`.
4. Çalışma alanındaki 14 ROS paketi ile bunların launch, config, mesaj, servis, action ve ana düğüm kaynakları.
5. Flutter kontrol uygulaması: `/mnt/c/Users/emre/desktop/liftant_v2_bitirme`; bu projenin Markdown belgeleri, `lib/` altındaki ROS/haritalama/görev modelleri, node/route sayfaları ve sözleşme testleri.

V1.1 ile V1.0 arasındaki teknik görev tanımı değişmemiştir. V1.1; başvuru ve sonuç tarihlerini değiştirmiş, finali **18–20 Eylül 2026** olarak kesinleştirmiştir. Bundan sonra karar sırası şöyledir:

1. En yeni resmî şartname, resmî duyuru ve yarışma teknik kurulunun yazılı cevabı.
2. Fiziksel araç üzerinde ölçülmüş ve tarihli kalibrasyon sonucu.
3. Sürüm kontrollü araç sözleşmesi ve aktif saha paketi.
4. Güncel kaynak kod ve otomatik test sonucu.
5. Geçmiş proje belgeleri ve geçmiş test kayıtları.

Eski belgelerde geçen “şartname V1.2”, eski sensör konumları veya eski kalibrasyon sayıları, resmî belge ya da güncel fiziksel ölçümle doğrulanmadıkça bağlayıcı kabul edilmeyecektir.

### 1.1 Kullanıcı tarafından doğrulanan güncel girdiler

- Takım hareket ve kabiliyet videosu aşamasını geçmiş ve finalist olmuştur.
- Flutter/Windows kontrol uygulamasının güncel dizini `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` olarak bildirilmiştir.
- PLC wire protokol belgesi henüz organizasyon tarafından takıma iletilmemiştir.
- Gerçek tahrik tekeri dönme eksenleri arası physical/geometric wheel separation `0.430 m`, 360° fiziksel odometri kalibrasyonundan gelen odometry-effective wheel separation `0.433 m` kabul edilecektir. Eski `0.460 m` fiziksel değer yanlış geometrik referanstan ölçülmüştür.
- Şerit takibi için yalnız lift/arka taraftaki kamera kullanılacaktır. A/B istasyon girişleri approach QR doğrulaması ve 180° dönüşten sonra rear-camera reverse docking; istasyon çıkışları lane STOP + Nav2 olacaktır.
- Kapı geçişi gidişte q5 outbound, dönüşte q6 return izin noktasıyla yönetilecek ve her fiziksel geçiş yeni izin gerektirecektir.
- Production görev `imu:=false` profiliyle çalışabilecektir; IMU etkinse ek health/yaw doğrulama kaynağı, kapalıysa yokluğu tek başına abort nedeni olmayacaktır.
- Lift sistemi ve limit sensörleri fiziksel olarak çalışmaktadır. Eksik olan kısım, bunların yarışma görev yöneticisine güvenli ve geri bildirimli ROS action olarak bağlanması ve ölçümlü kabulüdür.

Bu girdiler planlama kararıdır; `0.430 m physical / 0.433 m odometry-effective` ayrımı production araç sözleşmesine işlenecek ve düz sürüş ile iki yönlü 360° fiziksel deneyleriyle yeniden kabul edilecektir.

## 2. Yönetici özeti

Mevcut depo iyi bir ROS temeline sahiptir: STM32 taban sürücüsü, odometri/IMU yayını, SLAM Toolbox, AMCL, Nav2 Route Server, Regulated Pure Pursuit, güvenli hız zinciri, harita/lokalizasyon yöneticileri, docking ve görev action arayüzleri, görev durum mesajları ve simülasyon altyapısı vardır.

Ancak depo bugün itibarıyla yarışma görevinin tamamını gerçek donanımda uçtan uca yapabilecek durumda değildir. Yarışmaya çıkışı engelleyen başlıca konular şunlardır:

- Faz 0'daki provisional `0.460 m` tek değer sözleşmesi artık production kararı değildir; physical/geometric değer `0.430 m`, odometry-effective değer `0.433 m` olarak ayrıştırılmalı ve yeniden kabul edilmelidir.
- Çalışma alanında güncel `build/` ve `install/` bulunmadığından mevcut HEAD için temiz derleme/test kanıtı yoktur.
- Operatör arayüzünden şartnameye uygun rota öğretme, semantik düğüm tanımlama ve aktif saha paketini devreye alma akışı eksiktir.
- Gerçek çizgi/QR algısının `LaneOffset` ve `QrDetection` üretim bağlantısı yoktur; şerit kontrolü yalnız arka kamerayla reverse docking için kullanılmalı, çıkışta lane STOP sonrası Nav2 devralmalıdır.
- PLC wire protokolü henüz gelmemiştir; gerçek PLC adaptörü yoktur. Lift ve limit donanımı çalışsa da gerçek `LiftLoad` action sunucusu/görev entegrasyonu yoktur.
- Görev yöneticisi gidişte q5 outbound/dönüşte q6 return izinlerini, istasyondan ilgili approach node'a deterministik Nav2 çıkışını, rota geometrisine bağlı junction dönüşlerini ve normal segmentlerde route-heading politikasını henüz birlikte uygulamamaktadır.
- Üretim ortamında rota sapmasını ölçen ve `±10 cm` kuralını gözeten bir route guard yoktur.
- Flutter GUI mevcuttur ve rosbridge, mapping/lokalizasyon, görev özeti, QR/PLC alanları ile fiziksel manuel moda bağlı hız kilidi için ciddi bir temel sunar; fakat düğüm/rota kayıtları ROS backend olmadığı için yerel draft/stub seviyesindedir, gerçek PLC kaynağı yoktur ve fiziksel uçtan uca kabul beklemektedir.
- Bazı launch yolları güvenlik zincirini atlayabilmekte; mapping kontrolünde engel algılama varsayılanı yarışma için kapalıdır.
- Gerçek sistem launch’ı test haritası/grafı varsayılanlarıyla açılabilmekte ve çalışma zamanında kaydedilen saha paketini otomatik seçmemektedir.

Bu nedenle öncelik “yeni özellik eklemek” değil, aşağıdaki zorunlu zinciri eksiksiz ve ölçülebilir hâle getirmektir:

`fiziksel/odometri sözleşmesi → güvenli taban → lokalizasyon → saha paketi/rota → rear-camera reverse docking → lane STOP + Nav2 exit → çift yön gate/junction akışı → rota koruması → PLC/lift/görev → GUI → profile-aware hata testleri → 60 dakikalık kurulum → tam prova`

Otomatik şarj yalnızca zorunlu görevin en az üç ardışık uçtan uca provada geçtiği noktadan sonra ele alınacaktır.

## 3. Yarışma gereksinimleri izlenebilirlik tablosu

Durumlar: **Temel var** kullanılabilir altyapı var; **Kısmi** entegrasyon veya fiziksel kanıt eksik; **Bloker** yarışma görevi bu haliyle tamamlanamaz.

| ID | Şartname gereksinimi | Mevcut durum | Plan fazı | Yarışma kabul kanıtı |
|---|---|---|---|---|
| R01 | 2B lazer ile harita oluşturma | Temel var | F2, F9 | 60 dakika içinde yeni saha haritası, posegraph ve önizleme |
| R02 | Rotaları robot arayüzünden tanımlama | Kısmi; GUI var, ROS kalıcılığı yok | F3, F4 | GUI ile tüm zorunlu düğümler ve geçişler oluşturulup doğrulanır |
| R03 | Üç A ve üç B noktası arasındaki rastgele görevi alma | Kısmi | F7 | Dokuz A×B çifti statik ve rastgele testten geçer |
| R04 | Fabrika otomasyon sistemiyle haberleşme | Bloker | F7 | Gerçek protokol, bağlantı kaybı ve tekrar mesaj testleri |
| R05 | QR kodu okuma | Kısmi/mok | F5 | İçerik, zaman, güven ve istasyon eşleşmesi yayımlanır |
| R06 | QR’ın kameraya göre konumunu bulma | Bloker | F5 | Kalibre kamera ile metrik x/y/yaw veya eşdeğer poz |
| R07 | İstasyondan yaklaşık 1.5 m önceki çizgiyi işleme | Kısmi | F5, F7C, F8B | Nav2'den 180° dönüş sonrası arka kamera/geri docking kipine güvenli devir; çıkışta lane STOP |
| R08 | Hibrit navigasyonla hassas yanaşma | Kısmi/mok | F5, F7C, F8B | A/B'ye yalnız rear-camera reverse docking ile ±7.5 cm, ±5°; ilgili approach node'a Nav2 çıkışı |
| R09 | Rota sapmasını en fazla 10 cm’de tutma | Bloker | F6 | Gerçek aktif rota üzerinde zaman eşlemeli maksimum sapma ölçümü |
| R10 | Engel görünce çarpmadan durma | Temel var | F1, F8 | Hareketli ve sabit engelde temas yok, duruş mesafesi kaydı |
| R11 | Engel kalkınca göreve devam etme | Kısmi | F8 | Uzun beklemede gereksiz görev iptali olmadan otomatik devam |
| R12 | Gidişte q5, dönüşte q6 kapı izni al | Kısmi/mok | F6, F7, F8B | q5 outbound/q6 return için ayrı, yeni ve tek geçişlik izin; eski/geç mesaj güvenli |
| R13 | Yükü azami 5 kg ile taşıma | Fiziksel kanıt gerekli | F1, F10 | 5 kg ile kaldırma, taşıma, bırakma ve fren testleri |
| R14 | Yükü hareket yönünün ters tarafında tutma | Bloker | F3, F6, F7, F8B | A/B'de reverse docking, lane STOP sonrası ileri Nav2 exit ve yük yönü video kanıtı |
| R15 | Görev sonunda bekleme noktasına dönme ve bildirme | Kısmi | F7 | PLC bildirimiyle tamamlanan deterministik dönüş |
| R16 | Görevi hedef 30, en çok 45 dakikada bitirme | Test edilmedi | F10 | Resmî senaryo benzeri en az üç ölçümlü tam koşu |
| R17 | Harita ve rota hazırlığını 60 dakikada bitirme | Kısmi | F9 | Sıfırdan iki ayrı 60 dakikalık prova |
| R18 | Durum/görev/QR/PLC bilgilerini GUI’de gösterme | Kısmi; ekran/model temeli var | F4 | Şartnamedeki her bilgi için ekran ve bag/video kanıtı |
| R19 | PLC alınan/gönderilen mesajlarını GUI’de gösterme | Kısmi; son gelen/gönderilen alanları var, gerçek kaynak yok | F4, F7 | Zaman damgalı, yönü belli, sınırlı boyutlu iletişim günlüğü |
| R20 | Fiziksel anahtar manuel değilken uzaktan manueli engelleme | Temel var; fiziksel kabul gerekli | F1, F4, F8 | Otomatik kipte tüm uzaktan manuel komutların reddi |
| R21 | E-stop tüm motorları durdursun, sistemi güvenli kessin | Temel var | F1, F8 | Hareket ve lift dâhil ölçümlü gerçek donanım testi |
| R22 | Yarışma Wi‑Fi’ı, internetsiz çalışma ve yalnız iki cihaz | Test edilmedi | F4, F9 | Robot + kontrol PC, MAC kayıtlı, internet olmadan tam görev |
| R23 | Parkurda/kontrol masasında müdahalesiz otonomi | Kısmi | F10, F11 | Tek start sonrası kontrol girdisi olmadan tam görev |
| R24 | Araç, palet ve yük ölçü sınırlarına uyum | Fiziksel doğrulama gerekli | F0, F1 | Teknik çizime göre imzalı ölçüm formu ve fotoğraf |
| R25 | İsteğe bağlı otomatik şarj | Yok | F12 | Zorunlu görev bozulmadan düşük batarya davranışı |

Not: Şartname çiziminde yük `500 × 420 × 360 mm`, paletle ilgili `600 mm`, `420 mm`, `110 mm` ve alt parça aralıkları; araç için `1000 mm`, `700 mm`, `600 mm`, `650 mm` değerleri görülmektedir. Perspektif çizim yorumuna güvenilmemeli; Faz 0’da güncel resmî PDF/CAD üzerinden hangi ölçünün gövdeye, çatal çıkıntısına ve toplam sınıra ait olduğu teknik kurula sorularak fiziksel ölçüm formuna aynen geçirilmelidir.

## 4. Mevcut projenin teknik durumu

### 4.1 Kullanılacak sağlam temeller

- `marco_base`: UART V0.4 protokolü, CRC, teker komutları, enkoder odometrisi, STM32 yaw verisi, e-stop/manual/batarya durumları ve watchdog temeli.
- `marco_localization`: SLAM Toolbox, AMCL, EKF, harita ve lokalizasyon yöneticileri; harita ile başlangıç pozunu birlikte kaydetme.
- `marco_navigation`: Nav2, Route Server, Regulated Pure Pursuit, hız limiti yöneticisi ve simülasyon kabul araçları.
- `marco_safety`: Collision Monitor, twist mux ve güvenlik yöneticisi ile `cmd_vel_raw → cmd_vel_safe → cmd_vel` zinciri.
- `marco_docking`: `DockToStation` action iskeleti; e-stop ve engel denetimi.
- `marco_mission`: görev durum makinesi iskeleti, `AssignTask`, `GatePermission`, `TaskComplete`, görev/robot durum yayını ve mok PLC.
- `marco_msgs`: yarışma alanına özgü mesaj, servis ve action sözleşmeleri.
- `marco_simulation`: regresyon, arıza enjeksiyonu ve senaryo provası için kullanılabilir altyapı.
- `liftant_v2_bitirme`: rosbridge WebSocket istemcisi; `/robot_status`, `/mission/events`, `/map`, mapping/lokalizasyon servisleri; yeniden bağlantı; bayat `RobotStatus` durumunda manuel komutu kesme; harita, düğüm öğretme, rota çizme ve yarışma özet ekranı temeli.

### 4.2 Çözülmeden finale çıkılmayacak boşluklar

| Öncelik | Bulgu | Sonuç |
|---|---|---|
| P0 | Eski sözleşme physical/odometry değerlerini `0.460 m` olarak tekleştiriyor; doğrulanan production kararı `0.430 m physical / 0.433 m odometry-effective` | Ayrım config/contract/URDF'ye işlenip düz sürüş ve iki yönlü 360° kabulü geçmeden odometri dondurulamaz |
| P0 | Güncel kaynak için temiz build/test kurulumu yok | Geçmiş başarı kayıtları bugünkü HEAD’i kanıtlamıyor |
| P0 | PLC protokolü/adaptörü yok; çalışan lift/limit donanımının gerçek action sunucusu yok | Yük alma/bırakma ve kapı görevi uçtan uca tamamlanamaz |
| P0 | Üretim QR/çizgi düğümleri tek arka kamerayla reverse docking ve lane STOP → Nav2 exit arayüzlerini tamamlamıyor | Hassas yanaşma ve güvenli istasyon çıkışı gerçek sensörle çalışamaz |
| P0 | Flutter GUI var; `/stations/*` ve `/routes/*` açıkça backend stub, lift komutu pasif, PLC verisi gerçek kaynağa bağlı değil | Rota hazırlama ve görev ekranı yarışma backend’i olmadan tamamlanamaz |
| P0 | Görev yöneticisi q5'i yalnız sınırlı akışta ele alıyor; q5 outbound/q6 return geçiş kimliği ve her crossing için yeni izin yok | Kapı ihlali, eski iznin yeniden kullanılması veya senaryo kilitlenmesi riski |
| P0 | Yük arkada kalacak yön kuralı uygulanmıyor | Açık şartname ihlali |
| P1 | Semantik rota editörü, saha sürümü ve atomik aktivasyon yok | 60 dakikalık hazırlık güvenilir değil |
| P1 | Üretim route guard/cross-track yayını yok | 10 cm sapma ölçülemiyor ve korunamıyor |
| P1 | Gerçek sistem test haritası/grafı ile açılabiliyor | Yanlış saha verisiyle hareket riski |
| P1 | Mapping kontrolünde engel algılama yarışma için kapalı varsayılabiliyor | Haritalama sırasında çarpışma riski |
| P1 | Bağımsız çizgi launch’ları güvenli hız zincirini atlayabiliyor | Güvenlik mimarisi devre dışı kalabilir |
| P1 | Güvenlik yöneticisinin 15 saniye engel bekleme sonrası iptali | Şartnamedeki “engel kalkınca devam” davranışını bozabilir |
| P1 | QR docking boyunca sürekli taze algı bekliyor | QR görüşten çıkınca yanaşma gereksiz iptal olabilir |
| P1 | Tek arka kameranın production çözünürlük/exposure ayarı ve sensör TF kaydı belgeler arasında tekleştirilmemiş | Reverse docking algı kalibrasyonu tekrarlanamaz |
| P2 | Otomatik şarj görevi yok | Yalnızca +5 ek puan kaybı; ana görevi engellemez |

### 4.3 Sözleşme ve belge çelişkileri

Bu değerler Faz 0’da tek bir tarihli “araç sözleşmesi” altında çözülecektir:

- Teker aralığı kararı: physical/geometric değer `0.430 m`, odometry-effective/calibrated değer `0.433 m` olarak ayrı tutulacaktır. Eski `0.460 m` yanlış fiziksel referanstan, `0.421 m` eski STM32 verisinden gelen tarihsel değerlerdir.
- LiDAR konumu: eski belgelerde geride/düşük, güncel kaynak yorumunda önde ve daha yüksek değerler.
- Kamera yerleşimi: şerit takibi için lift/arka tarafta tek kamera vardır; öndeki donanım QR okuyucudur. Arka kamera konumu tahmin değil ölçülmüş TF ile tutulmalıdır.
- Kamera eğimi: yaklaşık 45° tahmin; kalibre ölçüm değil.
- Kamera yayın biçimi: bazı ayarlar 320×240 isterken donanım notları desteklenen en düşük modun farklı olduğunu belirtiyor.
- IMU politikası: `imu:=false` production profili desteklenir; `imu:=true` profilinde STM32 IMU/yaw ek health doğrulamasıdır ve iki profil ayrı kabul edilir.
- Araç dış sınırı: gövde, çatal ve toplam boyun şartname çizimine göre ayrı ayrı ölçülmesi gerekiyor.

### 4.4 Geçmiş test kayıtlarının kullanımı

`PROJE_PLANI.md`, `TEST.md` ve commit geçmişindeki simülasyon sonuçları regresyon senaryosu tasarlamak için değerlidir; güncel yarışma kabulü değildir. Her kabul kaydı aşağıdakileri içermelidir:

- Git commit kimliği ve temiz/kirli çalışma ağacı bilgisi.
- Build ve test komutu ile tam sonuç.
- Araç sözleşmesi, kalibrasyon ve aktif saha paketi özeti/hash’i.
- Donanım seri numarası veya cihaz eşlemesi.
- ROS bag, kısa video, metrik özeti ve testi yapan kişi.
- Tarih, zemin, yük, batarya ve ağ koşulu.

## 5. Hedef üretim mimarisi

### 5.1 Tek hız güvenlik zinciri

Tüm otonom ve manuel hareket kaynakları aşağıdaki zincirden geçmelidir:

`Nav2 / çizgi-docking / izinli manuel → twist_mux → collision_monitor → base_driver → STM32 watchdog`

Hangi topic adlarının kullanılacağı uygulama sırasında tekleştirilebilir; değişmez kurallar şunlardır:

- Hiçbir üretim launch’ı doğrudan taban sürücüsüne hız gönderemez.
- E-stop ve sensör bayatlığı tüm kaynaklardan daha yüksek önceliklidir.
- Fiziksel anahtar otomatikteyse uzaktan manuel kaynak kilitlidir.
- Manuel kipte otonom navigasyon ve docking komutlarının izin matrisi açıkça tanımlıdır.
- Lift hareketi de e-stop, limit switch, aşırı akım ve watchdog kapsamındadır.

### 5.2 Tek saha paketi

Her harita/rota kurulumu atomik bir saha paketi üretmelidir:

```text
fields/<field_id>/
  field.yaml
  map.yaml
  map.pgm
  map.png
  mapping_pose.yaml
  slam.posegraph
  slam.data
  route.geojson
  stations.yaml
  calibration_snapshot.yaml
  validation.json
```

`field.yaml` en az sürüm, oluşturma zamanı, harita çözünürlüğü, frame adları, dosya hash’leri, aktif araç sözleşmesi sürümü ve yarışma profili kimliğini tutmalıdır. Aktivasyon ancak tüm dosyalar yazılıp validator geçtiğinde atomik yapılmalıdır. Uygulama paketindeki örnek harita/graf üretim varsayılanı olamaz.

### 5.3 Semantik rota sözleşmesi

Graf düğümleri yalnız `name/x/y` içeremez. En az şu alanlar gereklidir:

- `id`, `name`, `role`, `x`, `y`, `yaw`.
- `role`: `WAIT`, `PICKUP_APPROACH`, `PICKUP_DOCK`, `DROPOFF_APPROACH`, `DROPOFF_DOCK`, `GATE_OUTBOUND_Q5`, `GATE_RETURN_Q6`, `QR_TRIGGER`, `TRANSIT`, gerekirse `CHARGE`.
- `station_id`: `A1..A3`, `B1..B3`, `q1..q9`, `D1..D6` eşleşmesi.
- Her A/B istasyonu için `approach_qr_id`, `dock_heading_yaw`, ölçülmüş
  `line_follow_duration_s` ve ilk sürümde `turn_direction: left|right`
  tutulmalıdır; ileride güvenli otomatik seçim eklenecekse `auto` açıkça
  sürümlenmelidir.
- `line_follow_duration_s` kodda sabitlenemez. GUI'den istasyon bazında
  düzenlenip saha paketine kalıcı yazılır; son ölçüm zamanı ve kullanılan
  şerit takip hız profiliyle birlikte doğrulanır.
- QR kaydı yalnız istasyon ilişkisini taşır. QR kimliğine kalıcı olarak
  `180 derece dön` gibi bir hareket aksiyonu bağlanamaz.
- İzin verilen yüklülük: boş, yüklü veya her ikisi.
- İzin verilen hareket yönü ve yükün arkada kalma kuralı.
- Kenar yönü, hız limiti, dönüş yarıçapı ve kapı geçiş olayı.
- Hassas yaklaşma modu: doğal navigasyon veya line/docking.
- Harita ve araç sözleşmesi sürümü.

Validator “bütün düğümler birbirine bağlı” kontrolünden fazlasını yapmalıdır. Dokuz A×B görevi için gereken yönlü yolları, gidişte q5 outbound ve dönüşte q6 return izin geçişlerini, dönüş yolunu, approach QR eşleşmelerini, istasyon yaw’larını, yük yönünü, çakışan kimlikleri ve harita sınırlarını denetlemelidir.

### 5.4 Görev durum makinesi

Referans akış:

```text
BOOT/PREFLIGHT
  → WAITING_FOR_TASK
  → EMPTY_ROUTE_TO_A_APPROACH (Nav2)
  → APPROACHING_STATION_A
  → QR_A_VERIFY (target_station + mission_state + QR_ID)
  → TURN_FOR_REVERSE_DOCK_A (180 derece, güvenli yön)
  → LINE_FOLLOW_DOCK_A (arka kamera, geri hareket, A süresi)
  → STOP_AND_VERIFY_A
  → PICKUP_READY
  → LIFT_LOAD
  → EXITING_STATION_A (lane STOP, Nav2 ile A'nın approach node'una çıkış)
  → LOADED_ROUTE_TO_B (Nav2)
      → q5 OUTBOUND_GATE_NOTIFY → OUTBOUND_GATE_WAIT → q6 GATE_PASS
  → APPROACHING_STATION_B
  → QR_B_VERIFY (target_station + mission_state + QR_ID)
  → TURN_FOR_REVERSE_DOCK_B (180 derece, güvenli yön)
  → LINE_FOLLOW_DOCK_B (arka kamera, geri hareket, B süresi)
  → STOP_AND_VERIFY_B
  → DROPOFF_READY
  → DROP_LOAD
  → EXITING_STATION_B (lane STOP, Nav2 ile B'nin approach node'una çıkış)
  → RETURN_ROUTE (Nav2)
      → q6 RETURN_GATE_NOTIFY → RETURN_GATE_WAIT → q5 GATE_PASS
  → WAIT_POSITION
  → TASK_COMPLETE_NOTIFY
  → WAITING_FOR_TASK
```

Her durum; giriş koşulu, timeout, tekrar deneme, güvenli duruş, PLC mesajı, GUI metni ve kalıcı olay kaydıyla tanımlanmalıdır. Aynı görev veya kapı izni tekrarlı geldiğinde çift kaldırma/indirme ya da izinsiz hareket olmamalıdır. Her fiziksel kapı geçişi yönüne özgü yeni izin kullanır; q5 outbound izni q6 return geçişini veya sonraki görevi yetkilendiremez. İstasyon QR tetikleyicisi yalnız `APPROACHING_STATION` durumunda ve QR kimliği güncel hedef istasyonla eşleştiğinde bir kez kurulmalıdır. `EXITING_STATION` durumunda aynı QR yeniden görülse bile dönüş veya şerit takibi tetiklenmemelidir. Süre sayacı QR algılandığında veya dönüş başladığında değil, 180° dönüş başarıyla bittikten ve geri şerit kontrolü gerçekten aktif olduğuna dair onay alındıktan sonra başlatılır. Süre dolunca şerit kontrolü kapatılır, sıfır hız yayımlanıp aracın durduğu doğrulanır ve ancak bundan sonra `PICKUP_READY` veya `DROPOFF_READY` durumuna geçilir. Health geçişleri profile-aware olmalı; `imu:=false` profilinde IMU yokluğu tek başına görev abort'u üretmemelidir.

## 6. Faz planı

Fazların kabul kapıları zorunludur. Bir faz “çalışıyor gibi göründüğü” için değil, tanımlı kanıtları ürettiği için tamamlanır.

### F0 — Resmî sürüm, finalist durumu ve mühendislik temeli

**Güncel ilerleme (29.08.2026, commit `a011d98`):** Çalışma ağacı temizken
14/14 paket `colcon build --symlink-install` ile derlendi. ROS test sonucu
118 test, 0 error, 0 failure ve 5 skip; araç sözleşmesi denetimi PASS. İlk testte
ROS log dizininin salt okunur olmasından kaynaklanan iki ortam hatası,
`ROS_LOG_DIR=/tmp/marco_f0_ros_logs` ile tekrarlandığında 10 PASS/1 skip oldu.
`0.460 m` bütün denetlenen yazılım tüketicilerinde tutarlıdır; ancak sözleşme
hâlâ `provisional_pending_stm32_revalidation` durumundadır. Fiziksel ölçüm,
firmware sonrası araç testi, cihaz envanteri, e-stop/mod gerçek donanım kabulü,
final lojistiği ve gerçek PLC/lift bağımlılığı açık olduğu için Faz 0
henüz kapanmamıştır.

**Süre:** 22–23 Ağustos  
**Öncelik:** P0  
**Amaç:** Yanlış şartname, yanlış fiziksel parametre veya doğrulanmamış build üzerinde çalışma riskini kaldırmak.

Yapılacaklar:

- [x] Finalistlik video aşamasıyla doğrulandı.
- [ ] Takım giriş bilgilerini, final ulaşım/kurulum saatini ve saha test hakkını resmî kanaldan ayrıca doğrula.
- [ ] V1.1’i proje arşivine sürüm/hash bilgisiyle kaydet; mail grubu ve yarışma sayfası için günlük değişiklik kontrol sorumlusu ata.
- [x] Güncel commit’te temiz `colcon build` ve tüm uygun `colcon test` çalıştır; sonuçları tarihli artefakt olarak sakla. (29.08.2026: 14/14 paket; 118 test, 0 error, 0 failure, 5 skip.)
- [ ] Fiziksel robotu ölç: gövde, toplam çatal boyu, en, yükseklik, minimum dönüş zarfı, ağırlık, 5 kg yüklü ağırlık merkezi.
- [ ] Teker çapı, etkin teker aralığı, encoder CPR/tick, motor yönleri ve yaw işaretini yeniden ölç.
- [ ] LiDAR, ön/arka kamera, taban, teker ve çatal TF’lerini fiziksel referans noktalarından ölç.
- [ ] Donanım listesi çıkar: cihaz yolu, USB kimliği/udev, seri numarası, yedek parça, güç hattı ve sigorta.
- [x] `0.460 m` değerini kanonik yazılım sözleşmesine geçir ve bütün denetlenen tüketicilerde tekleştir. (Araç sözleşmesi denetimi PASS.)
- [ ] STM32 firmware düzeltmesinden sonra `0.460 m` değerini düz sürüş/dönüş deneyiyle doğrulamadan odometri/lokalizasyon ayarını dondurma.
- [x] Flutter deposunun ve çalışan arayüzün varlığı doğrulandı.
- [ ] Flutter–ROS sözleşme sürümünü kaydet; PLC protokol dokümanı için dış bağımlılık sahibi/takip tarihi belirle ve çalışan lift donanımının ROS action/telemetri arayüzünü belgele.
- [ ] Zorunlu özellikler için sahiplik ve günlük entegrasyon saati belirle.

Kabul kapısı:

- [x] Temiz build ve test raporu var.
- [x] Araç sözleşmesi denetimi sıfır hata veriyor.
- [ ] Tüm fiziksel ölçüler imzalı ölçüm formunda.
- [ ] Güncel şartname ve finalistlik doğrulanmış; final lojistiği kayıt altındadır.
- [ ] Flutter–ROS sürüm eşleşmesi bilinir; PLC protokolü gelene kadar wire alanları uydurulmaz; lift için çalışan donanımdan action sonucuna kadar arayüz tanımlıdır.

### F1 — Fiziksel taban, lift ve güvenlik omurgası

**Güncel ilerleme (29.08.2026):** Gerçek STM32 bağlantısı ve düşük hızlı komut
yolu çalıştırıldı. Karttan gelen 24 baytlık odometri paketi ham olarak yakalandı;
ROS çözücüsü 16/20/24 bayt paketleri açık biçimde destekleyecek şekilde
düzeltildi ve 48 ilgili test geçti. Bir saniyelik ileri sürüşte sol encoder
`+119`, sağ encoder `-74` değişti; sağ encoder işareti ile teker hız farkı
kanıtlandı fakat kalibrasyon tamamlanmadı. Yük/lift bağlı olmadığı ve güncel
IMU'lu STM32 kaynağı elde olmadığı için Faz 1 kabul kapısı açıktır.

**Süre:** 24–26 Ağustos  
**Bağımlılık:** F0  
**Amaç:** Robotu boş ve 5 kg yüklü durumda güvenli, ölçülebilir ve tekrarlanabilir hareket ettirmek.

Yapılacaklar:

- [x] Gerçek STM32 seri bağlantısını ve ROS'tan düşük hızlı teker komutu yolunu doğrula.
- [x] Gerçek 24 bayt odometri paketini yakala; ROS çözücüsünde 16/20/24 bayt uyumluluğunu ve CRC birim testlerini doğrula.
- [ ] Sayaç taşmasını gerçek donanımda; yeniden bağlanmayı, CRC hata davranışını ve 200 ms watchdog’u uçtan uca doğrula.
- [x] Sol/sağ encoder işaretini gerçek ileri sürüşte ölçerek uyuşmazlığı kanıtla.
- [ ] Encoder işaretini düzelt; m/tick ve etkin teker aralığını kalibre et.
- [ ] Boş ve 5 kg yüklü hâlde motor PID/feed-forward ve düşük hız kararlılığını ayrı ölç.
- [ ] Çalışan lift/limit donanımını temel alarak gerçek `LiftLoad` action sunucusu sözleşmesini sabitle: hedef seviye, timeout, limit switch, yük var/yok, overcurrent, iptal ve sonuç kodları.
- [ ] Yük alma/bırakma mekanizmasını 5 kg ile en az 30 çevrim mekanik teste tabi tut; düşme ve sürüklenmeyi kaydet.
- [ ] E-stop’un teker ve lift güç/komut zincirini kestiğini fiziksel olarak test et; yazılım düğümü kapanmasına bağımlı olmasın.
- [ ] Fiziksel mod anahtarının truth table’ını yaz: otomatik, manuel, geçiş anı, bilinmeyen/bayat sinyal.
- [ ] Tüm hareket launch’larını tek güvenlik zincirine bağlama işi için envanter çıkar; yarışmada kullanılmayacak bypass launch’larını üretimden karantinaya al.
- [ ] Maksimum hız, ivme, açısal hız ve frenleme mesafesini boş/yüklü profil olarak belirle.

Kabul kapısı:

- 10 m düz sürüşte mesafe hatası hedef `%2` veya daha iyi; iki yönde benzer sonuç.
- 360° dönüşlerde tekrarlanabilir yaw hatası hedef `≤3°`; lokalizasyon olmadan ve lokalizasyonla ayrı rapor.
- E-stop, haberleşme kaybı ve komut bayatlığında tüm hareket güvenli durur.
- Otomatik kipte uzaktan manuel komut robotu hareket ettiremez.
- 5 kg ile 30 kaldır/indir çevriminde yük düşmesi yok; limit ve aşırı akım davranışı doğru.
- Güvenli maksimum yarışma hızları yazılı ve config’e aktarılmaya hazırdır.

### F2 — Sensör, TF, haritalama ve lokalizasyon

**Güncel ilerleme (29.08.2026):** Faz 1 encoder/PID kabulü açık kalmak
koşuluyla, hareketsiz yapılabilen TF, LiDAR, kamera ve harita yaşam döngüsü
kontrollerine paralel başlanmıştır. Encoder–IMU EKF, hareketli SLAM ve AMCL
hassasiyet kabulü STM32 düzeltmesine kadar bloke kabul edilir. Gerçek donanım
URDF ağacı ve araç sözleşmesi geçti. Harita paketi üretimi, lokalizasyon için
yeniden doğrulanması ve SLAM–AMCL karşılıklı dışlama kararları beş otomatik
testle doğrulandı; gerçek düğüm/TF kapanış testi donanım bağlıyken yapılacaktır.

**Süre:** 27–29 Ağustos  
**Bağımlılık:** F1  
**Amaç:** Haritadan bağımsız tekrar kurulabilen sensör geometrisi ve şartname toleransını destekleyen lokalizasyon.

Yapılacaklar:

- [x] URDF'yi gerçek donanım kipinde üretip XML/ağaç bütünlüğünü ve yazılım içi araç sözleşmesini doğrula. (29.08.2026: `check_urdf` PASS, araç sözleşmesi PASS.)
- [ ] `base_footprint → base_link → laser/camera/fork` TF zincirini ölçülen sözleşmeye göre doğrula.
- [ ] LiDAR scan açısı, ters/ayna yönü, kör bölgeler, çatal/yük yansıması ve speckle filtresini test et.
- [ ] Ön ve gerekiyorsa arka kamerada desteklenen gerçek çözünürlük/FPS/pixel formatı sabitle; intrinsic ve distortion kalibrasyonu yap.
- [ ] Encoder odometrisi ile STM32 yaw birleşiminin covariance, zaman damgası ve işaretlerini doğrula. *(STM32 düzeltmesini bekliyor.)*
- [x] Production haritalama profilinde (`do_loop_closing: false`) koridor paralelliği, harita çözünürlüğü ve kaydedilen haritayı yeniden açma davranışını fiziksel olarak test et. (06.09.2026: kullanıcı saha testinde haritalamanın temiz ve kararlı olduğunu doğruladı.)
- [x] Harita kaydında PGM/YAML/PNG, posegraph, başlangıç pozu ve metadata’nın atomik üretildiğini test et. (06.09.2026: fiziksel haritalama ve saha paketi kaydı kullanıcı tarafından doğrulandı.)
- [x] Harita kaydetme yazılım akışında PGM/YAML/PNG, posegraph/data, başlangıç pozu ve metadata sözleşmesini; başarısız kayıtta kısmi saha dizininin görünmediğini otomatik test et. (29.08.2026: 5 test PASS; gerçek SLAM servisiyle uçtan uca tekrar açık.)
- [ ] Mapping ile AMCL’nin aynı anda çalışmadığını; geçişte eski TF/node kalmadığını doğrula.
- [x] Mapping ve lokalizasyon yöneticilerinin birbirini iki yönde de reddettiğini otomatik test et. (29.08.2026: karar kilitleri PASS; eski TF/node çalışma zamanı kontrolü açık.)
- [x] Kaydedilen haritada AMCL'yi birden fazla kez yeniden başlatıp aynı fiziksel noktada kararlı poz verdiğini doğrula. (06.09.2026: kullanıcı fiziksel araçta doğruladı.)
- [ ] AMCL başlangıç pozu, kidnapped robot, LiDAR kesintisi ve odometri sapması deneyleri yap. *(Hassasiyet kabulü STM32 düzeltmesini bekliyor.)*
- [ ] Zeminde ölçülmüş referans işaretlerinde gerçek poz–AMCL poz farkını raporla. *(STM32 düzeltmesini bekliyor.)*

Kabul kapısı:

- Beş tekrar başlatmada aynı referans noktalarında poz hata hedefi `≤5 cm`, yaw `≤3°`; şartname sınırına en az `2.5 cm/2°` mühendislik payı.
- 20 dakikalık sürüşte TF kopması, zaman sıçraması veya sürekli AMCL kaybı yok.
- Yeni alan haritası operatör komutuyla kaydedilip aynı araç açılışında tekrar lokalize edilebiliyor.
- Lazer ve kamera konumları tahmin değil ölçüm/kamera kalibrasyon dosyasıyla izlenebilir.

### F3 — Saha paketi, rota editörü ve doğrulayıcı

**Süre:** 30 Ağustos–2 Eylül  
**Bağımlılık:** F2  
**Amaç:** 60 dakikalık kurulumda yarışma rotasının operatör tarafından güvenle öğretilebilmesi.

Yapılacaklar:

- [x] Saha listesi, oluşturma, kaydetme, silmeden arşivleme, doğrulama ve atomik aktivasyon servislerini tanımla.
- [x] Robotun güncel lokalize pozunu GUI’den semantik düğüm olarak kaydet: bekleme, A yaklaşım/dock, B yaklaşım/dock, q1–q9, D1–D6, q5, QR trigger.
- [x] Her düğümde x/y yanında yaw, rol, istasyon, yük/yön kuralı ve yaklaşma modu kaydet.
- [x] Kenar ekleme/silme, yönlü/çift yönlü geçiş, hız limiti ve kapı olayı tanımla.
- [x] Harita koordinatına tıklama ile “robot pozunu kaydetme” yöntemlerini birlikte sun; istasyon yaw’ında sayısal ince ayar sağla.
- [x] Dokuz A×B görevi ve bekleme dönüşleri için gerekli yönlü erişilebilirlik matrisini validator’da kontrol et.
- [x] q5’ten geçen her kenarın kapı olayı taşıdığını, izinsiz alternatif kestirme bulunmadığını denetle.
- [x] Yüklü kenarlarda yükün hareket yönünün tersinde kalmasını statik olarak doğrula.
- [x] Aktif saha paketi değişirken Nav2/lokalizasyonun güvenli durup doğru map/graf ile yeniden açılmasını sağla.
- [x] Demo/test graph’larının üretim profiline yanlışlıkla seçilmesini engelle.

Kabul kapısı:

- [ ] Sıfırdan bir örnek alan, yalnız kullanıcı arayüzü kullanılarak 45 dakika içinde haritalanıp rotalanır. *(Fiziksel araç kabulü bekleniyor.)*
- [x] Validator dokuz A×B görevinin tümünü, gidiş/dönüş q5 durumlarını ve yük yönünü geçer.
- [x] Eksik yaw, yinelenen ad, harita dışı düğüm, kopuk kenar ve yanlış q5 olayı aktivasyonu engeller.
- [x] Aktif paket hash’i GUI ve robot durumunda görünür; yarım yazılmış dosya aktif olamaz.

### F4 — Yarışma GUI’si ve çevrimdışı ağ

**Süre:** 30 Ağustos–3 Eylül; F3 ile paralel  
**Bağımlılık:** F0 arayüz erişimi, F3 sözleşmeleri  
**Amaç:** Şartnamenin rota hazırlama ve izleme gereksinimlerini iki cihazlı, internetsiz yapıda karşılamak.

Mevcut Flutter tabanı `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` dizinindedir. Kaynak incelemesine göre rosbridge yeniden bağlantısı, `/robot_status` bayatlık kilidi, mapping/lokalizasyon akışı, node/route sayfaları ve “GELEN/GÖNDERİLEN” PLC özet alanları vardır. Buna karşılık fiziksel mod anahtarı henüz araçta yoktur; node/route sayfaları ROS kalıcı backend’i olmadığı için yerel draft/stub kullanır; lift kontrolü bilinçli olarak pasiftir; PLC alanlarının gerçek veri kaynağı ve zaman damgalı mesaj geçmişi henüz yoktur.

**31 Ağustos uygulama durumu:**

- [x] `/robot_status` 5 Hz tek GUI telemetrisi olarak görev durumu, görev süresi, operatör açıklaması, poz/lokalizasyon, rota, güvenlik, batarya, PLC özeti, aktif saha paketi ve son QR'ın tam poz/güven/kamera bilgilerini yayımlıyor.
- [x] PC ve mobil istemcinin ortak kullanacağı rosbridge bağlantısı `9090` portunda mevcut.
- [x] Yeni ROS mesaj sözleşmesi derlendi; `marco_msgs` ve `marco_mission` doğrulamasında 15 test toplandı, 14 test geçti ve 1 telif testi atlandı.
- [ ] Fiziksel mod anahtarı araçta henüz bulunmadığı için manuel komutların donanım sinyaliyle kilitlenmesi bilinçli olarak ertelendi. Anahtar takılana kadar bu madde uygulanmayacak.
- [ ] Gerçek PLC protokolü/F7 tamamlanınca zaman damgalı RX/TX mesaj geçmişi ve dışa aktarma kaynağı eklenecek; GUI sahte PLC geçmişi üretmeyecek.
- [ ] İnternetsiz iki cihaz, GUI yeniden başlatma ve 60 dakikalık saha kabul testleri fiziksel olarak yapılacak.

GUI’de zorunlu alanlar:

- Robot durumu: boşta, görevi işliyor, yüksüz hareket, yüklü hareket, PLC bekliyor, dönüş, hata, e-stop.
- Görev kimliği, kaynak A, hedef B, görev aşaması ve geçen süre.
- Robot pozu, lokalizasyon sağlığı, aktif rota/kenar, sonraki düğüm, rota sapması.
- QR içeriği, istasyon eşleşmesi, kameraya göre poz, algı zamanı ve güven.
- PLC bağlantı durumu, son heartbeat, kapı izni ve görev sonucu.
- Alınan ve gönderilen PLC mesajları: zaman, yön, tip, kimlik, sonuç; sınırlı ring buffer ve dışa aktarma.
- Engel, e-stop, fiziksel mod, batarya, lift/yük ve sensör sağlıkları.
- Aktif saha paketi adı/sürümü/hash’i.
- Harita/rota hazırlama ve validator sonucu.

Yapılacaklar:

1. Mevcut Flutter deposunu ROS release sürecine bağla; kirli çalışma ağacını kullanıcı değişikliklerini kaybetmeden envanterle, kabul edilen GUI commit/build kimliğini kaydet ve API/ROS sözleşmesini testle.
2. Tek yarışma dashboard’u oluştur; navigasyon sırasında müdahale gerektiren geliştirme ekranlarını kapat.
3. Fiziksel mod anahtarı takıldıktan sonra manuel sürüş denetimini yalnız anahtarın manuel sinyali tazeyken etkinleştir; GUI butonu tek başına yetki vermesin.
4. Fiziksel mod anahtarı takıldıktan sonra otomatik kipte manuel topic yayını olsa bile robot tarafında ikinci kez reddet.
5. ROS bridge bağlantısı kopunca güvenli ve açık hata göster; eski veriyi canlıymış gibi gösterme.
6. Yalnız robot ve kontrol PC ile, internet/DNS/NTP olmadan, resmî Wi‑Fi benzeri ağda çalıştır.
7. Robot ve PC MAC adreslerini, statik isim/IP planını ve saat senkronizasyon yöntemini hazırla.
8. GUI’yi kapatıp açmanın otonom görevi bozmaması; yeniden bağlanınca salt izleme durumunu geri alması gerekir.

Kabul kapısı:

- Şartnamedeki her görünür bilgi için ekran görüntüsü + topic/servis kaynağı eşlemesi vardır.
- Fiziksel anahtar otomatikteyken 100 manuel komut denemesinde hareket yoktur.
- İnternetsiz iki cihaz testinde 60 dakika kurulum ve bir tam görev tamamlanır.
- GUI kapanması robotun görevini iptal etmez veya hareket kaynağını değiştirmez.

### F5 — Gerçek QR, çizgi algısı ve hassas docking

**Süre:** 3–7 Eylül  
**Bağımlılık:** F1, F2  
**Amaç:** Mok algıyı kaldırıp gerçek kameradan şartname toleransında yanaşmak.

Yapılacaklar:

1. Kamera sürücüsünden desteklenen sabit modda görüntü ve doğru `camera_info` üret.
2. QR içeriğini decode et; beklenen istasyon kimliğiyle doğrula ve yanlış/başka QR’ı reddet.
3. Bilinen QR boyutu + kalibre kamera ile QR’ın kameraya göre metrik pozunu hesapla; belirsizlik ve zaman damgası yayımla.
4. Görüntüdeki çizgiden `LaneOffset` üret: yanal hata, heading hatası, güven, tazelik ve geçerlilik.
5. Mevcut `lane_tracking` algoritmasını `marco_docking` arayüzüne adaptörle bağla; doğrudan `/cmd_vel` kullanan üretim yolu bırakma.
6. QR’ı istasyon yaklaşımında doğrulayıp güvenli biçimde latch et; QR görüşten çıktı diye kontrollü son yanaşmayı gereksiz iptal etme.
7. QR/çizgi kaybında hız azaltma, kısa kontrollü arama ve sonunda güvenli iptal politikası tanımla.
8. A ve B için hedef mesafe/yaw/çatal merkezini gerçek pallet maketiyle kalibre et.
9. Doğal navigasyon–docking devir noktasında çift komut veya hız sıçraması olmadığını doğrula.
10. Ön/arka kamera seçimi yük yönü ve manevra durum makinesiyle açıkça belirlenmeli.

Kabul kapısı:

- A ve B istasyonlarında, boş ve 5 kg yüklü, her birinde en az 20 yanaşma yapılır.
- En az 19/20 deneyde son poz `±7.5 cm` ve `±5°` içindedir; hedef tasarım bandı `±5 cm/±3°`.
- QR kimliği hatalıysa docking başlamaz; bayat algı hız komutu üretemez.
- Tüm docking hızları ana güvenlik zincirinden geçer.
- Karanlık/parlak, kısmi kapatma ve çizgi kontrastı varyasyonlarında sonuç raporu vardır.

### F6 — Rota yürütme, optimizasyon ve rota koruması

**Süre:** 7–10 Eylül  
**Bağımlılık:** F2, F3, F5  
**Amaç:** Dokuz görev için en uygun izinli rotayı seçmek ve sapmayı sürekli ölçmek.

Yapılacaklar:

1. [x] Görev yöneticisinin tekil `NavigateToPose` yerine semantik rota/graf yürütme sözleşmesini kullanmasını sağla.
2. [x] Rota maliyetinde mesafe, süre, yük durumu, dönüş maliyeti, q5 bekleme ve izin verilmeyen yönleri dikkate al.
3. [x] Düğüm yaw’ını hedef pozda uygula; her hedefi sıfır yaw ile çağırma.
4. RPP’yi düz, dar dönüş, ileri, geri, boş ve yüklü profillerde kalibre et.
5. [x] Aktif rota geometrisine en yakın nokta/projeksiyon üzerinden zaman eşlemeli cross-track error üret.
6. [x] Sapma için davranış bandı tanımla: `5 cm` uyarı, `8 cm` hız azaltma, `10 cm` güvenli duruş/yeniden değerlendirme. Kesin eşikler fiziksel sonuçla sabitlenecek.
7. [x] Ani köşe kestirmeyi ve global yeniden planlamanın tanımlı rotadan kaçmasını engelle; engelden dolaşmak yerine güvenli bekle.
8. [x] q5 kenar giriş/çıkış olayını rota yürütmeden üret; yalnız “pickup sonrası bir kez” varsayımına bağlama.
9. [x] Yüklü harekette yalnız izinli yönleri seç; yük robotun hareket yönünün arkasında kalmalı.
10. [x] Sapma, seçilen yol, edge id, hız limiti ve duruş nedenini bag/GUI’ye yayımla.

**1 Eylül ROS uygulama durumu:** `route_guard`, Nav2'nin seçtiği yolu ve
`map -> base_footprint` pozunu izleyerek `/route/cross_track_error`,
`/route/selected_path`, `/route/active_edge`, `/route/next_node`,
`/route/state` ve `/route/events` üretir. Sapma limiti hız yöneticisiyle
birleştirilir; duruş bandında yüksek öncelikli güvenlik sıfırı yayımlanır.
Görev yöneticisinin yük durumu Route Server'daki uygunsuz kenarları dinamik
olarak kapatır ve onay gelmeden yeni `ComputeRoute -> FollowPath` yürütmesi
başlatılmaz. `PenaltyScorer`, düğüm yaw'ından hesaplanan dönüş maliyetini ve q5
bekleme cezasını mesafe/süre maliyetine ekler. Yalnız 4 numaralı fiziksel RPP
kalibrasyonu açık bırakılmıştır.

Kabul kapısı:

- Dokuz A×B kombinasyonu ile gerekli dönüşlerin hepsi validator ve simülasyonda geçer.
- Fiziksel parkur benzerinde üç ardışık tam rota boyunca maksimum sapma `<10 cm`; hedef maksimum `≤8 cm`, yüzde 95 `≤5 cm`.
- Yüklü hiçbir edge yük yön kuralını ihlal etmez.
- Engel varken alternatif serbest alan planı üretip tanımlı rotadan sapmaz.
- q5 içeren her gidiş ve dönüş edge’i izin olayını doğru tetikler.

### F7 — PLC, lift ve uçtan uca görev yöneticisi

**Süre:** 10–13 Eylül  
**Bağımlılık:** F1, F3, F5, F6  
**Amaç:** Gerçek fabrika sistemi mesajından başlayıp bekleme bildirimiyle biten deterministik görev.

Yapılacaklar:

1. Resmî PLC protokolü geldiğinde taşıma katmanını mevcut ROS servislerinden ayıran bir adaptör uygula.
2. Bağlantı/heartbeat, görev kimliği, kaynak, hedef, q5 bildirimi, geçiş izni, görev tamamlandı ve hata mesajlarını sürümle.
3. Mesajların idempotent olmasını sağla: tekrar görev, tekrar izin, geç gelen yanıt ve reconnect çift eylem doğurmasın.
4. Görevi yalnız boşta ve preflight sağlıklıyken kabul et; A/B kimliklerini aktif saha paketiyle doğrula.
5. A yaklaşım → QR doğrula → line/dock → lift → yük doğrula zincirini timeout/iptal kurallarıyla uygula.
6. Yüklü rota → her q5 geçişinde bildir/bekle/geç → B docking → bırak → yük yok doğrula zincirini uygula.
7. Dönüş rotasında q5 varsa aynı güvenli el sıkışmayı yeniden yap.
8. Bekleme pozuna tolerans içinde dönünce PLC’ye tamamlandı/beklemede mesajı gönder.
9. Her FSM geçişini GUI’ye ve olay kaydına neden koduyla aktar.
10. PLC bağlantısı görev sırasında koparsa güvenli dur; yeniden bağlanınca aynı görev kimliğiyle kontrollü devam veya açık hata politikasını uygula.
11. Navigasyon/docking/lift action iptallerini gerçek sonuç kodlarına göre ayır; kör yeniden deneme yapma.
12. Yarışma başına sayaçlar: görev süresi, bekleme süresi, deneme sayısı, yük düşmesi/algı hatası operatör görünürlüğü.

Kabul kapısı:

- Gerçek PLC yoksa önce protokol uyumlu test sunucusunda; sonra mutlaka gerçek sistemle kabul.
- Dokuz A×B görevinin her biri simülasyonda; seçilmiş en kötü üçü fiziksel araçta geçer.
- Rastgele verilen en az beş ardışık görevde yanlış A/B, çift lift veya q5 ihlali yok.
- PLC kopma/tekrar/yeniden bağlanma testlerinde tehlikeli hareket veya çift bildirim etkisi yok.
- 5 kg yük üç ardışık uçtan uca görevde düşmeden taşınır.

### F7A — İstasyon–QR sözleşmesi ve durumla yetkilendirilmiş tetikleme

**Süre:** F7 sonrasında 0.5 gün
**Bağımlılık:** F3, F5, F7
**Amaç:** Ön QR okuyucusunu donanımdan bağımsız bir ROS sözleşmesine bağlamak ve QR'ın tek başına hareket başlatmasını engellemek.

**Durum (2 Eylül):** ROS altyapısı tamamlandı. Saha-paketi ayar servisleri,
donanımdan bağımsız QR mesajı/adaptörü, hedef+state+QR kapısı, tazelik,
debounce, tek-sefer tüketim ve `RobotStatus` görünürlüğü eklendi. Flutter
ekranı, gerçek QR okuyucu sürücüsü ve altı istasyonun fiziksel kabul ölçümü
bekliyor; dönüş ve süreli şerit kontrolü F7B/F7C kapsamındadır.

Donanım sözleşmesi:

- Araçta önde ayrı bir QR okuyucu, arkada şerit takibi için tek kamera vardır.
- QR okuyucu için bir donanım adaptörü oluşturulur. Donanıma özgü veri önce
  `/qr_reader/qr_detection` üzerinde en az `qr_id`, `valid`, zaman damgası ve
  mümkünse güven/hata bilgisiyle yayımlanır; adaptör bunu üretim sisteminin
  kanonik `QrDetection` sözleşmesine dönüştürür.
- Arka kamera QR okuyucu yerine kullanılmaz; ön QR okuyucu şerit kontrolü üretmez.

Yapılacaklar:

1. Saha paketinde her A/B istasyonu ile yaklaşım QR'ını eşleştir:
   `A1→q2`, `A2→q3`, `A3→q4`, `B1→q9`, `B2→q8`, `B3→q7` örnek saha
   eşleşmesidir; kimlikler kodda sabitlenmez, GUI/ROS saha verisinden okunur.
2. GUI'nin istasyon için `approach_qr_id`, `dock_heading_yaw`,
   `line_follow_duration_s` ve `turn_direction: left|right|auto`
   düzenleyebileceği servis ve doğrulama sözleşmesini tanımla; değerleri saha
   paketinde kalıcı sakla. Süre pozitif, sonlu ve belirlenen güvenli üst sınır
   içinde olmalıdır.
3. Tetikleme koşulunu yalnız
   `target_station + mission_state=APPROACHING_STATION + QR_ID` eşleşmesi
   olarak uygula.
4. QR tazelik, geçerlilik, debounce ve aynı yaklaşım oturumu içinde tek sefer
   tüketim kuralı ekle. Yanlış, bayat veya tekrar QR hiçbir hareket üretmez.
5. Süreli geri yanaşma başlayınca QR tetikleyicisini tüket. Lift tamamlanıp
   durum `EXITING_STATION` olduğunda aynı QR tekrar okunsa bile yok say.
6. Yeni bir istasyon yaklaşımı başladığında yalnız o hedef için yeniden armed ol.
7. Armed/disarmed, beklenen/okunan QR ve red nedenini GUI/olay kaydına yayımla.

Kabul kapısı:

- Altı A/B eşleşmesinin tamamı saha paketinden yüklenir; kodda istasyon adına
  bağlı `if q2` benzeri karar bulunmaz.
- Altı istasyonun her biri için GUI'den farklı süre kaydedilip yeniden
  okunduğu ve süre değişikliğinin yalnız ilgili istasyonu etkilediği doğrulanır.
- Doğru QR yalnız doğru hedef ve doğru state'te bir kez tetikler.
- Yanlış hedef, normal Nav2 geçişi, `EXITING_STATION`, tekrar okuma ve bayat QR
  testlerinin hiçbirinde dönüş veya şerit komutu oluşmaz.

### F7B — Güvenli 180° dönüş ve Nav2’den docking’e atomik devir

**Süre:** F7A sonrasında 1 gün
**Bağımlılık:** F6, F7A
**Amaç:** Doğrulanmış istasyon QR'ından sonra robotu güvenli yönde 180° çevirip kontrolü geri yanaşma sistemine tek sahipli olarak devretmek.

**Durum (2 Eylül):** ROS altyapısı tamamlandı. Nav2, istasyona ait QR/yaklaşım
düğümünde başarıyla bitip ölçülen hız sabit sıfır olmadan dönüş başlamaz.
`left/right` yönündeki dönüş Nav2 `/spin` action ile mevcut costmap ve güvenlik
zincirinden yürütülür; hedef yön saha paketindeki `dock_heading_yaw` değeridir.
Dönüş boyunca STM32 IMU verisi, IMU+encoder `/odometry/filtered`, AMCL/TF,
engel, e-stop, timeout ve action tek-sahipliği denetlenir. `auto`, iki costmap
yayı karşılaştırılmadığı sürece güvenli biçimde reddedilir. Gerçek araçta altı
istasyon için ≤3° kabul testi ve dönüş yönü kalibrasyonu bekliyor.

Yapılacaklar:

1. Nav2 yaklaşım hedefinin başarıyla tamamlandığını ve çıkış hızının sıfır
   olduğunu doğrulamadan dönüş başlatma.
2. İlk sürümde saha paketindeki `turn_direction: left|right` değerini kullan;
   `auto` seçeneğini ancak iki aday dönüş yayı costmap/ayak iziyle kontrol
   edilip güvenli olan yön deterministik seçilebiliyorsa etkinleştir.
3. 180° dönüşü açık bir manevra/action olarak yürüt; hedef yaw, açısal tolerans,
   timeout, engel, lokalizasyon kaybı ve iptal sonuçlarını ayrı kodla bildir.
4. Dönüş sırasında Nav2 yol takibini ve şerit komutunu yetkisiz bırak; yalnız
   manevra kaynağı ana güvenlik zincirinden geçsin.
5. Dönüş hedef toleransına girmeden `LINE_FOLLOW_DOCKING` durumuna geçme.
6. Güvenli dönüş yayı yoksa veya dönüş tamamlanamazsa robot durmuş kalsın;
   otomatik ters yöne ikinci deneme açık bir politika olmadan yapılmasın.
7. İstasyon kimliğinden bağımsız aynı state/action akışını bütün A/B noktalarında kullan.

Kabul kapısı:

- Altı istasyon yaklaşımının her birinde seçilen yönde tekrarlanabilir 180°
  dönüş ve hedef tasarım bandı `≤3°` yaw hatası gösterilir.
- Nav2, dönüş ve docking arasında aynı anda iki sıfır-dışı hız kaynağı yoktur.
- Engel, timeout, e-stop ve AMCL/TF kaybında docking başlamaz ve araç güvenli durur.

### F7C — Arka kamera ile geri docking, tamamlama ve ileri Nav2 çıkışı

**Süre:** F7B sonrasında 1 gün
**Bağımlılık:** F5, F7, F7B
**Amaç:** Bütün alma ve bırakma istasyonlarına yalnız arka kamera/geri şerit takibiyle yanaşmak; işlemden sonra şeridi kullanmadan ileri Nav2’ye dönmek.

**Durum (2 Eylül):** ROS entegrasyonu tamamlandı. Gerçek şerit takip düğümü
tek ortak arka kamera topic'ini IDLE durumda dinler; görev yöneticisi dönüşten
sonra istasyonun `line_follow_duration_s` değerini docking action'a aktarır.
Action, güncel kamera karesi + `/lane_tracking/active` + dönüş sonrasında
üretilmiş sıfır-dışı `/cmd_vel_lane` görülmeden monotonik sayacı başlatmaz.
Şerit komutu ters hareket için sınırlandırılıp yalnız `/cmd_vel_dock` üzerinden
güvenlik zincirine girer. Süre sonunda şerit `STOP` edilir ve filtreli odometri
sabit sıfır göstermeden `PICKUP_READY/DROPOFF_READY` ile lift'e geçilmez.
Kamera, şerit komutu/aktiflik, IMU+encoder odometri, AMCL/TF, engel, e-stop ve
iptal kayıpları ayrı fail-safe sonuçlardır. Altı istasyonun süre kalibrasyonu,
`reverse_angular_sign` yön kontrolü ve fiziksel ±7.5 cm/±5° kabulü bekliyor.

Yapılacaklar:

1. `pickup/dropoff` işlem türünü hareket yönü ve kamera seçiminden ayır. Hem A
   hem B docking için hareket `reverse`, algı kaynağı `rear_camera` olmalıdır.
2. FAZ 5'te üretilen gerçek şerit çıktısını bir docking action/adaptörüne bağla;
   algoritmayı görev yöneticisine veya launch dosyasına kopyalama.
3. Görev yöneticisi hedef istasyonun `line_follow_duration_s` değerini aktif
   saha paketinden okur. Sayaç yalnız 180° dönüş tamamlandıktan, şerit takip
   action/control isteği kabul edildikten ve geri şerit kontrolünün aktifliği
   doğrulandıktan sonra monotonik saatle başlatılır.
4. Tanımlı süre boyunca geri şerit kontrolü çalışır. Süre dolunca kontrol
   iptal/durdurulur, `/cmd_vel_dock` sıfırlanır ve ölçülen hızın sıfıra indiği
   doğrulanır; ardından pickup için `PICKUP_READY`, dropoff için
   `DROPOFF_READY` durumuna geçilip lift başlatılır.
5. Sürenin dolması sensör arızasını başarıya çeviremez. Şerit/kamera bayatlığı,
   şerit kaybı, engel, e-stop, lokalizasyon kaybı, action reddi veya iptali
   süre içinde ayrı hata sonucu ve sıfır hız üretmelidir.
6. Lift sonucu ve yük var/yok doğrulandıktan sonra state'i
   `EXITING_STATION` yap, şerit kontrolünü disarm et ve ileri yöndeki izinli
   rota kenarında Nav2'yi doğrudan başlat.
7. Çıkışta süreyi veya şerit takibini kullanma ve yaklaşım QR'ını yeniden
   aksiyona bağlama.
   İleri Nav2 devri palet/istasyon costmap geometrisinde güvenli başlamalıdır.
8. Şerit komutunu yalnız `/cmd_vel_dock` üzerinden; Nav2, manuel ve docking
   kaynaklarını tek sahipli mux/güvenlik zincirinden geçir.
9. Hedef istasyon, ayarlı/geçen/kalan süre, arka kamera/şerit geçerliliği,
   kontrol aktifliği, duruş doğrulaması ve hata nedenini GUI/RobotStatus/olay
   kaydına aktar.

Kabul kapısı:

- A1–A3 ve B1–B3 için genel aynı kod yolunda
  `Nav2 → QR doğrula → 180° → geri şerit aktif → istasyon süresi → sıfır hız → PICKUP_READY/DROPOFF_READY → lift → ileri Nav2`
  sırası doğrulanır.
- Çıkış sırasında aynı QR yeniden görülse bile dönüş veya şerit takibi başlamaz.
- Her istasyon süresi en az üç fiziksel geri yanaşma ölçümünden belirlenir;
  aynı sabit hız profiliyle tekrarlandığında şartname kabul sınırı
  `±7.5 cm/±5°` aşılmaz. Süre/hız profili değişirse yeniden kalibre edilir.
- Fiziksel testte bütün A/B istasyonlarında ileri Nav2 çıkışı yük/paletle
  çarpışmadan başlar ve yük hareket yönünün arkasında kalır.

### F8 — Emniyet, arıza enjeksiyonu ve kurtarma matrisi

**Süre:** 14–15 Eylül
**Bağımlılık:** F1–F7C
**Amaç:** Her tekil arızanın güvenli, görünür ve mümkünse devam edilebilir davranışa dönüşmesi.

Uygulama durumu (5 Eylül 2026):

- [x] Engel için production zaman aşımı kaldırıldı. Engel varken Nav2,
  manuel ve docking hız kaynakları sıfırda tutuluyor; engel kalkınca mevcut
  görev sırf bekleme süresi dolduğu için iptal edilmiyor.
- [x] E-stop bırakıldıktan sonra kendiliğinden hareketi önleyen latch ve açık
  `/safety/reset` akışı eklendi. Hareket komutu veya güvenlik arızası varken
  reset reddediliyor.
- [x] STM32/UART geçerli paket tazeliği `/base/communication_ok` ile safety ve
  mission katmanlarına bağlandı; kayıp/bayat iletişimde hareket kilitleniyor,
  yeni görev reddediliyor ve aktif görev güvenli abort oluyor.
- [x] Otomatik testte kalıcı engelin 121 saniyelik eşdeğer beklemede abort
  üretmediği, E-stop sonrası açık reset gerektiği ve UART taze/bayat geçişi
  doğrulandı.
- [ ] Engel kalkınca aynı gerçek Nav2 action'ının 5/30/120 saniye sonrasında
  devamı fiziksel araçta ve bag kaydıyla doğrulanacak.
- [ ] Fiziksel E-stop'un sürüş ve lifti durdurduğu kullanıcı tarafından
  doğrulandı; ölçümlü tekrar ve reset kabul kaydı alınacak.
- [ ] Batarya telemetrisi gelmediği için düşük/kritik batarya politikası;
  fiziksel mod anahtarı olmadığı için mod geçiş testi son entegrasyonda
  tamamlanacak.

Zorunlu testler:

| Arıza/olay | Beklenen davranış |
|---|---|
| E-stop basılması | Teker ve lift anında güvenli durur; görev hata/e-stop; kendiliğinden tekrar hareket yok |
| E-stop bırakılması | Açık reset/preflight olmadan hareket yok |
| Yol üstünde engel | Temas etmeden durur; rota korunur |
| Engel 5/30/120 saniye sonra kalkar | Kural izin veriyorsa görev kaldığı yerden otomatik ve yumuşak devam eder |
| Engel kalıcı | Robot güvenli bekler; keyfî rota değiştirmez; GUI açık neden gösterir |
| PLC bağlantısı kaybı | Güvenli durur veya tanımlı durumu tamamlar; protokol kararıyla tutarlı |
| GUI/rosbridge kaybı | Otonom görev güvenli şekilde sürer; manuel kaynak aktifleşmez |
| Lift limit/overcurrent | Lift durur, sürüş engellenir, yük durumu bilinmiyor olarak işaretlenir |
| Yanlış/tekrar QR | İstasyon kabul edilmez, yanlış lift eylemi yok |
| Yanlış saha paketi | Preflight görevi başlatmaz |
| q5 gidiş izni verilmez | Robot q5'te güvenli durmuş kalır ve q6 tarafına geçmez |
| q6 dönüş izni verilmez | Robot q6'da güvenli durmuş kalır ve q5 tarafına geçmez |
| Kapı izni timeout | Robot ilgili izin noktasında güvenli durmuş kalır; izinsiz rota segmenti başlamaz PLC belgesi geldiğinde gereken mesaj verilecek |
| Eski/geç gate izni | Önceki veya ters yönlü geçiş izni yeni fiziksel geçişi yetkilendirmez |
| D1–D6 junction Spin sırasında engel | Robot güvenli durur; engel politikası sağlanmadan Spin veya sonraki FollowPath başlamaz |
| Junction Spin timeout/action abort | Sonraki FollowPath segmenti başlamaz; görev açık hata nedeni ile güvenli bekler |
| 180°/junction dönüşünde lokalizasyon kaybı | Dönüş ve görev güvenli durur; geçerli poz gelmeden devam etmez |
| `imu:=false` profili | Yalnız IMU mesajı gelmediği için safety veya mission abort oluşmaz |
| İstasyon çıkışında aynı QR'ın yeniden okunması | 180° dönüş/docking/lane tracking tekrar tetiklenmez; Nav2 kesilmez |
| Lane STOP → Nav2 kontrol devri | Aynı anda iki sıfır-dışı motion source oluşmaz; devir sıfır hız üzerinden atomiktir |
| q5/q6 çift yön gate arıza enjeksiyonu | Gidiş ve dönüş izinleri ayrı görev/geçiş kimlikleriyle sınanır; biri diğerini yetkilendirmez |

Kabul kapısı:

- Her satır için otomatik/mekanik test, bag ve sonuç kaydı vardır.
- Normal olmayan hiçbir durumda doğrudan `/cmd_vel` bypass’ı veya kontrolsüz lift hareketi yoktur.
- Engel bekleme timeout’u şartnamenin otomatik devam beklentisiyle uyumludur; 15 saniyelik geliştirme varsayımı yarışma davranışını belirlemez.
- E-stop ve watchdog testleri gerçek donanımda tekrarlanmıştır.
- q5 outbound ve q6 return için izin yok, timeout, geç/eski izin ve reconnect arızalarının her biri ayrı log/bag ile kanıtlanmıştır.
- Junction Spin engel/timeout/action abort ve dönüş sırasında lokalizasyon kaybında sonraki FollowPath'in başlamadığı kanıtlanmıştır.
- Lane STOP → Nav2 devrinde hareket kaynağı çakışması olmadığı ve EXITING_STATION sırasında QR tekrarının aksiyon üretmediği kanıtlanmıştır.

### F8A — Production araç, yön ve IMU sözleşmesi

**Uygulama sırası:** F8'den sonra, F9/F10 saha provası ve kabulünden önce

**Süre:** 15 Eylül

**Bağımlılık:** F3, F6, F7A–F7C, F8

**Amaç:** Production hareket temelini doğru fiziksel ölçü, normal rota heading politikası ve profile-aware IMU davranışıyla sabitlemek.

> Bu fazda kullanılan production kararları, F0–F7C dönemindeki provisional teknik kabullerin yerini alır; geçmiş faz kayıtları izlenebilirlik için değiştirilmemiştir.

Yerine geçen kararlar:

- Eski physical `0.460 m` → yeni physical `0.430 m` / odometry-effective `0.433 m`.
- Tek q5 gate yaklaşımı → outbound q5 / return q6.
- İleri station exit lane → lane STOP + Nav2.
- Kör final node yaw → route heading + explicit turn action'ları.
- IMU zorunlu → profile-aware IMU.
- D waypoint → rota geometrisi gerektirince explicit junction Spin.

Yapılacaklar:

- [x] URDF teker eksenlerinin fiziksel `±0.215 m` mantığıyla tutarlı olduğunu doğrula.
- [x] TRANSIT, q1–q9, gate ve normal D segmentlerinde final pose'a kör kayıtlı node yaw yazmayı kaldır.
- [x] Normal FollowPath hedef heading'ini son geçerli rota segmentinin geometrisinden üret.
- [x] İstasyon 180° dönüşünü `dock_heading_yaw` kullanan ayrı Spin action olarak tut.
- [x] D1–D6 junction dönüşünü ayrı Spin action olarak tut.
- [x] Küçük terminal yaw, motor deadband ve `FollowPath status=6` için regresyon testi ekle.
- [x] Manevra health kontrolünü IMU enabled/disabled profiline ayır.
- [x] `imu:=false` profilinde IMU freshness yokluğunun abort üretmesini engelle.
- [x] IMU kapalıyken encoder odometry, `/odometry/filtered`, AMCL ve map/odom/base TF ile dönüş kabulü yap.
- [x] `imu:=true` profilinde IMU'yu ek health/yaw doğrulama kaynağı olarak kullan ve bayatlık fail-safe politikasını koru.

F8A kabul kapısı:

- [ ] Normal Nav2 segmentleri gereksiz terminal node yaw istemiyor ve deadband kaynaklı `status=6` regresyonu geçiyor.
- [ ] `imu:=false` profilinde normal rota ve ayrı Spin manevrası IMU-yokluğu abort'u olmadan; `imu:=true` profilinde bayat IMU fail-safe ile çalışıyor.

### F8B — İstasyon çıkışı ve çift yönlü gate

**Uygulama sırası:** F8A'dan sonra, F9/F10 öncesi

**Süre:** 15–16 Eylül

**Bağımlılık:** F7A–F7C, F8, F8A

**Amaç:** Reverse docking sonrasında deterministik Nav2 çıkışını ve her fiziksel kapı geçişinde yönüne özgü yeni izin alınmasını production mission'a yerleştirmek.

Yapılacaklar:

- [x] Lift başarıyla bitince lane tracking'i STOP/disarm et.
- [x] Kontrol devrini sıfır hız üzerinden yaparak Nav2'yi hemen devral.
- [x] İlk Nav2 hedefini aktif saha paketindeki ilgili approach node yap: A1/q2, A2/q3, A3/q4, B1/q9, B2/q8, B3/q7.
- [x] Approach node'a çıktıktan sonra ana loaded/return rotaya devam et.
- [x] EXITING_STATION sırasında aynı QR yeniden okunduğunda hiçbir istasyon aksiyonu oluşmadığını doğrula.
- [x] İstasyon çıkışında ileri lane tracking'in hiçbir zaman başlamadığını doğrula.
- [ ] q5 outbound entry ve q6 return entry semantiğini aktif saha paketinde tanımla.
- [x] Gidişte q5'te, dönüşte q6'da dur/izin/bekle/geç davranışını uygula.
- [x] Her fiziksel crossing için yeni, geçiş yönüne bağlı handshake iste.
- [x] Gate handshake'i pickup sonrası tek çağrı olmaktan çıkarıp aktif route crossing'ine bağla.
- [x] Validator'a iki yönde unauthorized gate bypass kontrolü ekle.
- [x] RobotStatus/mission event tarafında izin beklenen gate entry ve yönünü göster.

Not: F8B backend sözleşmesi ve testleri hazırdır. Güncel
`saha_test/route.geojson` dosyasının `features` listesi boş olduğundan q5/q6
düğümleri ile `q5_outbound`/`q6_return` kenarları gerçek aktif saha paketine,
düğümler ve kenarlar GUI'den öğretildikten sonra yazılacaktır.

F8B kabul kapısı:

- [ ] A/B istasyonlarında yalnız arka kamera ile geri docking yapılıyor; çıkışta lane STOP sonrası Nav2 devralıyor.
- [ ] Her istasyon çıkışının ilk Nav2 hedefi aktif saha paketindeki kendi approach QR node'u oluyor.
- [ ] EXITING_STATION sırasında QR tekrarının dönüş, docking veya lane tracking üretmediği kanıtlanıyor.
- [ ] Gidişte q5, dönüşte q6 gate handshake çalışıyor; eski/geç izin diğer geçişi yetkilendirmiyor ve iki yönde izinsiz geçiş mümkün değil.

### F8C — Junction manevraları ve segmentli rota yürütme

**Uygulama sırası:** F8B'den sonra, F9/F10 öncesi

**Süre:** 15–16 Eylül

**Bağımlılık:** F6, F8, F8A, F8B

**Amaç:** D1–D6 kavşaklarında rota geometrisine göre gereken dönüşleri açık, atomik manevralarla yürütmek ve tam production rotayı doğrulamak.

Yapılacaklar:

- [x] Aktif route üzerindeki mevcut ve sonraki edge geometrisinden gerekli heading değişimini hesapla.
- [x] Yaklaşık 90° değişimde açık Spin/junction maneuver uygula; düz devamda Spin yapma.
- [x] Keskin dönüş içeren yolu tek FollowPath'e bırakmak yerine gerekli yerde segmentlere ayır.
- [x] `FollowPath → sıfır hız → Spin → sıfır hız → sonraki FollowPath` sırasını atomik uygula.
- [x] Engel, timeout, localization kaybı veya action failure sonrasında sonraki segmente geçme.
- [x] Junction kararını QR'a veya hardcoded A/B senaryosuna değil aktif rota geometrisine bağla.
- [x] Junction Spin hedefini F8A route-heading politikasıyla üret ve motor deadband altında kalan terminal düzeltmeyi normal FollowPath'e yükleme.
- [ ] `A2 → B3 → WAIT` referans senaryosunu segment, junction ve gate olaylarıyla düşük hızlı production smoke testinde çalıştır.

Not: F8C ROS yürütücüsü ve birim/regresyon testleri tamamlandı. Junction
kararı yalnız `role=transit` düğümlerinde, Route Server'ın sıralı edge
geometrisinden ve varsayılan `60°–120°` banttan üretilir. Düz geçişte Spin
oluşmaz; herhangi bir segment/Spin/health hatasında sonraki segment başlamaz.
Gerçek `A2 → B3 → WAIT` smoke testi, aktif saha grafiği öğretildikten sonra
yapılacaktır.

F8C kabul kapısı:

- [ ] D1–D6'da rota gerektirince yaklaşık 90° Spin yapılıyor; düz D geçişinde gereksiz Spin oluşmuyor.
- [ ] Her junction'da FollowPath tamamen bitip sıfır hız doğrulanmadan Spin, Spin bitmeden sonraki FollowPath başlamıyor.
- [ ] Engel/timeout/localization/action abort durumunda sonraki segment başlamıyor.
- [ ] `imu:=false` profiliyle junction turn ve segmentli route yürütme çalışıyor.
- [ ] `A2 → B3 → WAIT` örnek senaryosu en az düşük hızlı production smoke testinde tamamlanıyor.

### F9 — 60 dakikalık harita ve rota hazırlama provası

**Süre:** 16 Eylül

**Bağımlılık:** F2–F4, F6, F8A–F8C

**Amaç:** İkinci aşamaya geçiş kapısı olan saha hazırlığını baskı altında tamamlamak.

**Başlangıç durumu (06.09.2026):** RPLIDAR ile fiziksel harita üretimi ve
harita paketinin kaydı kullanıcı tarafından başarılı kabul edildi. Bu, F9'un
haritalama ön koşulunu karşılar; süreli sıfırdan saha provası yerine geçmez.
Kaydedilen haritada AMCL'nin tekrarlı başlatmalarda aynı fiziksel noktada
kararlı kaldığı da kullanıcı tarafından doğrulandı.
Mevcut `saha_test` paketinde harita dosyaları vardır ancak `route.geojson`
henüz `0` düğüm/`0` kenardır. F9'da semantik düğüm, istasyon ayarı, kenar,
validator, aktivasyon ve smoke-test adımları ayrıca tamamlanacaktır.

Önerilen dakika planı:

| Süre | İş | Çıkış |
|---|---|---|
| 00–05 | Araç ölçü/güç/ağ/preflight, saat ve disk kontrolü | Tüm sağlıklar yeşil |
| 05–25 | Güvenli manuel haritalama, kapı ve istasyon çevreleri | Kapalı/temiz 2B harita |
| 25–30 | Harita kaydı, mapping kapatma, lokalizasyon açma | AMCL kararlı, başlangıç pozu doğru |
| 30–45 | WAIT, A1–A3, B1–B3, q1–q9, D1–D6 ve altı istasyon approach/dock pozunu öğretip station config ile ilişkilendirme | Semantik düğümler ve A1/q2, A2/q3, A3/q4, B1/q9, B2/q8, B3/q7 eşleşmeleri |
| 45–50 | Kenarlar, yönler, yük kuralları, q5 outbound/q6 return gate semantiği, D1–D6 junction geometrisi ve hızlar | Tam yönlü rota grafı |
| 50–54 | Dokuz A×B, B→WAIT, çift yönlü gate, junction bağlantıları ve approach QR eşleşmeleri için validator; atomik aktivasyon | Geçerli saha paketi |
| 54–58 | En uzak A→B→WAIT smoke testi; outbound q5 + return q6 gate el sıkışma testi | Hareket ve çift yönlü izin kanıtı |
| 58–60 | Paket yedeği/hash, yarışma profilini kilitleme | Hazır ve geri alınabilir release |

Prova koşulları:

- Yarışma günü erişilecek süre başlamadan önce gizli ölçüm/ön harita kullanılmaz.
- İnternet kapalı, yalnız robot ve kontrol PC bağlıdır.
- En fazla iki takım üyesi parkurda; roller haritalama sürücüsü ve GUI/validator operatörü olarak önceden belirlenir.
- Birinci prova tanıdık parkurda, ikinci prova düğüm yerleri değiştirilmiş sahada yapılır.
- Hedef 50 dakika; kalan 10 dakika hata payıdır. 60 dakikaya göre tasarlanan normal akış kabul edilmez.

Kabul kapısı:

- İki farklı günde sıfırdan iki prova da `≤55 dakika` içinde geçer.
- Prova sonunda dokuz A×B yol matrisinin tamamı geçerli ve en az bir tam görev çalışır.
- Sıfırdan oluşturulan sahada q5 outbound/q6 return gate semantiği, D1–D6 junction dönüş geometrisi ve altı approach QR eşleşmesi GUI üzerinden üretilebilir ve validator’dan geçer.
- B→WAIT dönüşlerinde q6 izni zorunluluğu ile gerekli junction manevraları rota üzerinde doğrulanır.
- Eski/test haritası kullanma, yanlış graph seçme veya elle dosya düzenleme ihtiyacı yoktur.

### F10 — Tam yarışma provası ve performans

**Süre:** 16–17 Eylül

**Bağımlılık:** F1–F9, F8A–F8C

**Amaç:** Hakem müdahalesi dışında tek komutla tam senaryoyu puan ve süre hedefinde tamamlamak.

Yapılacaklar:

1. Görevi PLC/test sistemi rastgele seçsin; ekip önceden A/B bilmesin.
2. Robot beklemeden başlasın; pickup, q5 outbound, dropoff, q6 return ve WAIT dönüşünün tamamı production FSM ile otonom olsun.
3. Bir koşuda kısa süreli engel, bir koşuda uzun engel; bir koşuda GUI yeniden bağlantısı uygula.
4. Boş ve yüklü hızları toplam süreyi 30 dakikanın altında tutacak ancak sapma/duruş payını bozmayacak şekilde ayarla.
5. Poz toleransı, maksimum rota sapması, q5 outbound ve q6 return izin zamanlarını ayrı ayrı, yük düşmesini ve toplam süreyi otomatik raporla.
6. En az iki farklı batarya seviyesinde ve iki farklı zemin tutuşunda dene.
7. Kullanıcı paneline izleme dışında dokunmadan tamamla.
8. Her başarısızlığı kök neden, düzeltme ve tekrar testiyle kapat; yalnız “yeniden deneyince geçti” kabul edilmez.
9. Dokuz A×B kombinasyonunu graph/sim üzerinde doğrula; en az üç tam fiziksel senaryo çalıştır ve bunlardan birini junction sayısı yüksek seç.
10. `A2 → B3 → WAIT` akışını zorunlu fiziksel kabul senaryolarından biri yap.
11. En az bir tam görevi `imu:=false` production profiliyle tamamla.
12. Her normal Nav2 segmentinde route heading kullanıldığını ve `FollowPath status=6` terminal-yaw abort'u oluşmadığını doğrula.
13. A/B çıkışlarının tamamında lane tracking'in STOP/disarm olduğunu, ilk Nav2 hedefinin ilgili approach node olduğunu ve ileri lane tracking'in hiç etkinleşmediğini logla.
14. q5 ve q6 geçişlerinde izin gelmeden önce robotun kapının doğru tarafında kaldığını bağımsız poz/log kanıtıyla doğrula.

Production tam görev akışı:

`WAIT → A approach → hedef QR → 180° Spin → arka kamera ile geri docking → pickup → lane STOP → Nav2 ile A approach node'a çıkış → loaded route → gerekli D junction Spin → q5 outbound izin → q6 → B approach → 180° Spin → arka kamera ile geri docking → dropoff → lane STOP → Nav2 ile B approach node'a çıkış → return route → gerekli junction Spin → q6 return izin → q5 → D1 → q1 → WAIT → görev tamamlandı`

`A2 → B3 → WAIT` referans kabul akışı:

1. `Başlangıç → q1 → D1` Nav2; D1'de D2 yönüne yaklaşık 90° Spin.
2. `D1 → D2` Nav2; D2'de q3 yönüne yaklaşık 90° Spin; `D2 → q3` Nav2.
3. q3 doğrulama → 180° Spin → arka kamera ile geri `q3 → A2` docking → pickup → lane STOP → Nav2 ile `A2 → q3` çıkış.
4. `q3 → D2` Nav2; D2'de D3 yönüne junction Spin; `D2 → D3 → q5` Nav2.
5. q5'te dur → outbound izin al → `q6 → D4` Nav2; D4'te D6 yönüne Spin; `D4 → D6` Nav2; D6'da q7 yönüne gereken Spin; `D6 → q7` Nav2.
6. q7 doğrulama → 180° Spin → arka kamera ile geri `q7 → B3` docking → dropoff → lane STOP → Nav2 ile `B3 → q7` çıkış.
7. `q7 → D6` Nav2; D6'da D4 yönüne gereken Spin; `D6 → D4` Nav2; D4'te q6 yönüne Spin; `D4 → q6` Nav2.
8. q6'da dur → return izin al → `q5 → D3 → D2 → D1` Nav2; D1'de q1 yönüne Spin; `D1 → q1 → Başlangıç` Nav2 → görev tamamlandı.

Kabul kapısı:

- Üç ardışık tam görev başarıyla tamamlanır.
- Dokuz A×B kombinasyonu graph/sim doğrulamasından, en az üç fiziksel tam senaryo kabulden geçer; fiziksel koşulardan biri `A2 → B3 → WAIT` olur.
- Her biri `<30 dakika` hedefinde; hiçbir koşu 45 dakikaya yaklaşmaz.
- Maksimum rota sapması `<10 cm`; her istasyon ve bekleme pozunda `±7.5 cm/±5°`.
- Yük düşmesi, çarpışma, izinsiz q5 outbound veya q6 return geçişi ya da operatör müdahalesi yoktur.
- Hiçbir koşuda ileri lane tracking, istasyon çıkışında tekrar QR aksiyonu veya normal route sonunda terminal-yaw kaynaklı `FollowPath status=6` görülmez.
- `imu:=false` production profiliyle en az bir tam görev başarıyla tamamlanır.
- GUI’de şartnamedeki tüm bilgiler ve PLC tx/rx geçmişi görünürdür.

### F11 — Release dondurma ve yarışma operasyonu

**Süre:** 17 Eylül; final boyunca kontrollü kullanım

**Bağımlılık:** F10, F8A–F8C

**Amaç:** Çalışan sistemin yarışma yerine aynı biçimde taşınması.

Yapılacaklar:

1. Yarışma release tag’i, paket bağımlılıkları ve çevrimdışı kurulum paketi üret.
2. Son kabul edilen config, firmware, GUI ve saha şema sürümlerini birlikte kilitle.
3. Tek komutlu yarışma launch’ı ve tek komutlu yalnız izleme launch’ı hazırla.
4. Açılış preflight’ı zorunlu kıl: cihazlar, TF, scan, camera, odom, lokalizasyon, PLC, lift, e-stop, mod, disk, batarya, aktif saha paketi.
5. Otomatik rosbag ve olay günlüğü başlat; disk doluluğu için sınır koy.
6. Bir önceki kabul edilen release’e geri dönüş prosedürünü prova et.
7. Robot/PC yedek depolama, kablo, sigorta, USB adaptör, LiDAR/kamera bağlantısı, şarj ve mekanik takım kontrol listesi hazırla.
8. MAC adresleri, ağ adı, yerel IP ve firewall kurallarını yazılı taşı.
9. İki parkur görevlisi ve kontrol masası rolleri için kısa operasyon kartları hazırla.
10. 17 Eylül’den sonra yalnız P0 güvenlik veya görev engelleyici hata için değişiklik; her değişiklik tam smoke test ister.
11. Release config/contract kapısında physical wheel separation `0.430 m`, odometry-effective separation `0.433 m` ve seçili production IMU profilini doğrula.
12. Altı station approach QR eşleşmesini, q5 outbound/q6 return semantiğini ve junction-turn production davranışını doğrula.
13. Normal route final-yaw politikasının route heading kullandığını; explicit yaw'ın yalnız docking ve junction Spin action'larında bulunduğunu doğrula.
14. Placeholder/test graph'ın seçili olmadığını, aktif saha paketi hash'inin doğru olduğunu ve tek komutlu production launch'ın F8A–F8C akışını kullandığını fail-fast kontrol et.

Kabul kapısı:

- Temiz makine/hesapta internet olmadan sistem açılır.
- Release commit’i, firmware ve GUI build’i eşleşir.
- Soğuk açılıştan göreve hazır olma iki tekrarda ölçülmüş ve prosedüre uygundur.
- Geri dönüş release’i fiziksel araçta denenmiştir.
- Dondurulan release ile q5 outbound + q6 return gate smoke testi geçer.
- En az bir junction-turn smoke testi ve bir A/B reverse docking → lane STOP → Nav2 approach çıkış smoke testi geçer.

### F12 — Opsiyonel puanlar: otomatik şarj, yerlilik, özgünlük

**Başlama şartı:** F8A–F8C ve F10 kabul kapıları geçmiş, F10 üç ardışık kez tamamlanmış ve yarışma release’i dondurulmuş olmalı.

**Öncelik:** P2

Otomatik şarj için:

1. Batarya yüzdesini gerçek BMS/ölçümle kalibre et; yalnız tahmini voltaja dayanma.
2. Eşik altına yükle girildiyse önce bırakma görevini tamamla, sonra şarja git.
3. Robot yüksüzse güvenli şekilde şarj istasyonuna git.
4. Şarj istasyonu pozunu, temas algısını, akım/gerilim doğrulamasını ve başarısız docking güvenliğini uygula.
5. Şartnamede istasyon ayrıntılarının sonradan bildirileceği söylendiğinden resmî çizim gelmeden mekanik tasarımı dondurma.

Yerlilik/özgünlük için kod, elektronik, mekanik ve algoritma kanıtlarını sunum dosyasında izlenebilir hâle getir. Bu çalışmalar zorunlu görevin kararlılığını veya release takvimini riske atamaz.

## 7. Takvim ve kritik yol

22 Ağustos’tan 18 Eylül final başlangıcına 27 takvim günü vardır. Aşağıdaki plan agresiftir; ayrı mekanik/firmware, ROS-navigasyon, algı ve GUI/PLC sorumlularının aynı entegrasyon sözleşmesiyle paralel çalışmasını gerektirir.

| Tarih | Ana çıktı | Git/release kapısı |
|---|---|---|
| 22–23 Ağustos | F0 sözleşme, temiz build, resmî durum ve eksik girdiler | `baseline` |
| 24–26 Ağustos | F1 taban/lift/e-stop/manual güvenliği | fiziksel taban kabulü |
| 27–29 Ağustos | F2 sensör/TF/SLAM/AMCL | lokalizasyon kabulü |
| 30 Ağustos–3 Eylül | F3 saha/rota + F4 GUI/ağ | ilk 60 dk araçları |
| 3–7 Eylül | F5 gerçek QR/çizgi/docking | istasyon toleransı |
| 7–10 Eylül | F6 route yürütme/guard | 10 cm rota kabulü |
| 10–13 Eylül | F7 gerçek PLC/lift/tam FSM | ilk tam görev |
| 13 Eylül | F7A istasyon–QR/state sözleşmesi | yanlış/tekrar QR hareket üretmiyor |
| 13–14 Eylül | F7B güvenli 180° dönüş ve kontrol devri | tek hız sahibiyle dönüş kabulü |
| 14 Eylül | F7C geri şerit docking ve lane STOP sonrası Nav2 çıkışı | altı istasyon entegrasyonu |
| 14–15 Eylül | F8 arıza matrisi | safety kabulü |
| 15 Eylül | F8A araç/yön/IMU production sözleşmesi | 0.430/0.433 ayrımı, route heading ve IMU profili |
| 15–16 Eylül | F8B istasyon çıkışı ve çift yön gate | lane STOP → approach Nav2, q5 outbound/q6 return |
| 15–16 Eylül | F8C junction ve segmentli rota | D1–D6 Spin ve atomik segment geçişi |
| 16 Eylül | F9 iki 60 dk prova | saha hazırlık kabulü |
| 16–17 Eylül | F10 üç tam görev | yarışma kabulü |
| 17 Eylül | F11 release freeze/lojistik | imzalı final release |
| 18–20 Eylül | Yarışma finali | yalnız kontrollü hotfix |

Kritik yol: `F0 → F1 → F2 → F3 → F5 → F6 → F7 → F7A → F7B → F7C → F8 → F8A → F8B → F8C → F9 → F10 → F11`.

F4 kısmen paralel yürüyebilir. F12 kritik yolda değildir. Bir P0 blokeri hedef tarihinden iki gün fazla sarkarsa opsiyonel işler kapatılır ve ekip tam zamanlı kritik yola döner.

## 8. Gelecekte değişmesi muhtemel proje alanları

Bu bölüm değişiklik emri değil, fazlar başladığında etki analizidir.

| Alan | İncelenecek başlıca dosyalar/paketler | Beklenen iş |
|---|---|---|
| Araç sözleşmesi | `src/marco_base/config/base_driver.yaml`, `src/marco_bringup/config/vehicle_contract.yaml`, description/URDF | Physical `0.430 m`, odometry-effective `0.433 m` ayrımı, TF ve kinematik |
| Sözleşme kapısı | `src/marco_bringup/scripts/check_vehicle_contract.py` | Tüm kritik parametrelerin fail-fast denetimi |
| Üretim launch | `src/marco_bringup/launch/real_system.launch.py` | Aktif saha, gerçek PLC/lift/perception, preflight |
| Mapping/localization | `src/marco_localization/scripts/mapping_manager.py`, `localization_manager.py`, `mapping_control.launch.py` | Atomik saha paketi, güvenli varsayılanlar |
| Rota | `marco_navigation` graph/config/launch ve `route_graph_validator.py` | Semantik editör, aktivasyon, rol/yön, q5 outbound/q6 return ve junction validator |
| Route guard | `marco_navigation` içinde yeni/uygun üretim düğümü | Aktif path ve cross-track metrikleri |
| Algı | `lane_tracking`, `marco_perception`, `qr_detector.py` | Gerçek `LaneOffset`, `QrDetection`, QR poz ve decode |
| Docking | `src/marco_docking/marco_docking/dock_server.py` | Tek arka kamera ile reverse docking, lane STOP, atomik Nav2 devri, kayıp algı ve fiziksel tolerans |
| Görev | `src/marco_mission/marco_mission/mission_manager.py` | Approach-node çıkışı, route-heading, explicit docking/junction Spin, q5 outbound/q6 return ve idempotency |
| PLC | `marco_mission` veya ayrı transport paketi | Resmî protokol adaptörü, heartbeat, tx/rx log |
| Lift | `marco_base`/donanım paketi ve `LiftLoad.action` | Gerçek action sunucusu ve emniyet |
| Güvenlik | `marco_safety` config/launch/supervisor, tüm hareket launch’ları | Tek komut zinciri, obstacle resume, profile-aware IMU ve kontrol devri matrisi |
| GUI | `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` | Var olan rosbridge/mapping/dashboard temelini kalıcı rota backend’i, lift action, gerçek PLC kaynağı ve zaman damgalı PLC günlüğüyle tamamlama |

Yeni mesaj/servis eklemeden önce mevcut `marco_msgs` sözleşmelerinin genişletilmesi değerlendirilmelidir. Geriye dönük uyumsuz değişiklik varsa GUI, PLC adaptörü ve ROS release’i birlikte sürümlenmelidir.

## 9. Ölçüm ve kabul matrisi

| Metrik | Şartname sınırı | Mühendislik hedefi | Ölçüm yöntemi |
|---|---:|---:|---|
| Rota maksimum yanal sapma | 10 cm | max 8 cm, p95 5 cm | Aktif polyline’a izdüşüm + bağımsız zemin referansı |
| Bekleme/pickup/dropoff pozisyonu | ±7.5 cm | ±5 cm | Ölçülmüş saha fiducial/şerit ve robot referans noktası |
| Bekleme/pickup/dropoff yönelimi | ±5° | ±3° | Kalibre açı referansı/ölçüm aparatı |
| Engel çarpışması | Temas yok | Güvenli marj ≥10 cm | Video + lidar + cmd_vel + gerçek mesafe |
| Engel sonrası devam | Otomatik | Kontrollü ivmeyle ≤3 s içinde | Engel kalkış zamanı–hareket zamanı |
| Saha hazırlığı | ≤60 dk | ≤55 dk | Kesintisiz ekran/video ve olay logu |
| Görev | ≤45 dk, hedef 30 dk | <30 dk | PLC görev zamanı–WAIT bildirimi |
| Yük | ≤5 kg | 5 kg’da tam kabul | Kalibre tartım + görev videosu |
| Docking başarı oranı | Açık oran yok | ≥95% | A/B, boş/yüklü 20’şer deneme |
| Manuel kilit | Otomatikte hareket yok | 0/100 ihlal | Fiziksel switch + manuel komut enjeksiyonu |
| q5 outbound gate | Her gidiş geçişinde yeni izin | 0 izinsiz/eski izinle geçiş | q5 edge olayı + PLC tx/rx + kapı öncesi/sonrası poz |
| q6 return gate | Her dönüş geçişinde yeni izin | 0 izinsiz/eski izinle geçiş | q6 edge olayı + PLC tx/rx + kapı öncesi/sonrası poz |
| Junction turn | Rota geometrisi gerektirdiğinde kontrollü dönüş | Gerekli yaklaşık 90° dönüşlerin %100'ü; düz geçişte 0 gereksiz Spin | Edge heading farkı + Spin action sonucu + odom/AMCL |
| Reverse docking → Nav2 exit | A/B'de geri docking, çıkışta lane yok | 0 ileri-lane/çift hareket kaynağı; ilk hedef doğru approach node | Motion-source logu + QR/state + route action |
| IMU kapalı production | IMU tek başına zorunlu değil | `imu:=false` tam görevde 0 IMU-kaynaklı abort | Health/state olayları + odom/TF + görev sonucu |

Tek bir AMCL pozuna dayanarak poz ve rota kabulü yapılmamalıdır; aynı lokalizasyon kaynağı hem kontrol hem “hakem” olursa sistematik hata görünmez. En azından kalibre saha işaretleri/video ölçümü veya bağımsız referansla periyodik çapraz kontrol gerekir.

## 10. Günlük test disiplini

Her entegrasyon günü şu sırayla kapanır:

1. Temiz build ve ilgili birim testleri.
2. Araç sözleşmesi ve launch preflight.
3. Simülasyon smoke/regresyonu.
4. Tekerler havada kısa donanım I/O testi.
5. Zeminde düşük hızlı güvenlik testi.
6. İlgili fazın ölçümlü fiziksel kabulü.
7. Bag/video/metrik arşivi.
8. Son bilinen iyi sürüme dönüş testi veya en azından doğrulanmış release işareti.

Her gece zorunlu regresyon kümesi:

- Build/test ve araç sözleşmesi.
- Mapping–localization karşılıklı dışlama.
- Nav2 lifecycle ve tek hız zinciri.
- Engel dur/devam.
- QR/çizgi bayatlığı.
- Dokuz A×B graph validator matrisi.
- q5 outbound ve q6 return izinleri; eski/geç iznin ters yöndeki yeni geçişte reddi.
- Rota gerektiren D1–D6 junction Spin ve düz D geçişinde gereksiz Spin olmaması.
- A/B reverse docking → lane STOP → ilgili approach node'a Nav2 çıkışı; EXITING_STATION QR tekrarının etkisizliği.
- `imu:=false` profilinde 180° dönüş, junction turn ve kısa mission smoke testi.
- Lift timeout/limit/e-stop.
- GUI topic sözleşmesi ve PLC tx/rx görünürlüğü.
- En az bir kısa uçtan uca mok görev; fiziksel kabul günlerinde gerçek görev.

## 11. Go / No-Go kontrol listesi

Robot ancak tüm zorunlu maddeler “GO” ise yarışma parkuruna çıkar:

- [ ] Güncel şartname ve resmî kurul ek açıklamaları işlendi.
- [ ] Finalistlik, 18–20 Eylül lokasyonu ve saha erişim saatleri teyit edildi.
- [ ] Araç/palet/yük ölçüleri güncel çizime uygun.
- [ ] Temiz release build/test ve araç sözleşmesi geçiyor.
- [ ] E-stop, watchdog, mod anahtarı ve lift emniyeti gerçek donanımda geçti.
- [ ] 5 kg yük ile kaldırma/taşıma/bırakma kabulü geçti.
- [ ] Haritalama ve AMCL fiziksel kabulü geçti.
- [ ] Production araç sözleşmesinde physical wheel separation `0.430 m`, odometry-effective separation `0.433 m`; URDF teker eksenleri fiziksel `±0.215 m` ile tutarlı.
- [ ] GUI ile 55 dakika içinde sıfırdan saha paketi hazırlanabiliyor.
- [ ] Dokuz A×B rotası, q5 outbound/q6 return izinleri, D1–D6 junction bağlantıları, approach QR eşleşmeleri ve yük yönleri validator’dan geçiyor.
- [ ] Gerçek QR decode + metrik poz + gerçek çizgi/docking çalışıyor.
- [ ] A/B istasyonlarında yalnız arka kamera ile geri docking; çıkışta lane STOP ve doğru approach node'a Nav2 devri çalışıyor.
- [ ] Rota gerektiren D1–D6 kavşaklarında kontrollü junction Spin var; düz geçişte gereksiz Spin yok.
- [ ] Normal route heading politikası terminal node yaw/deadband kaynaklı `FollowPath status=6` üretmiyor.
- [ ] `imu:=false` production profiliyle 180° dönüş, junction turn, docking ve tam görev kabulü geçti.
- [ ] A, B ve WAIT toleransları ölçümlü olarak sağlanıyor.
- [ ] Rota maksimum sapması 10 cm’den küçük.
- [ ] Engel görülünce duruyor ve kalkınca otomatik devam ediyor.
- [ ] Gerçek PLC görev/kapı/tamamlanma haberleşmesi geçti.
- [ ] Gidişte q5 ve dönüşte q6 izni ayrı ayrı sınandı; eski/geç izin başka geçişi yetkilendirmiyor.
- [ ] Otomatik kipte uzaktan manuel sürüş donanım ve yazılım katmanlarında engelli.
- [ ] GUI tüm zorunlu bilgileri ve PLC alınan/gönderilen mesajlarını gösteriyor.
- [ ] İnternetsiz, iki cihazlı ağ provası geçti; MAC bilgileri hazır.
- [ ] Üç ardışık tam görev müdahalesiz ve 30 dakikanın altında tamamlandı.
- [ ] Release, firmware, GUI, config ve geri dönüş paketi birlikte donduruldu.

Herhangi bir P0 madde NO-GO ise otomatik şarj, görsel iyileştirme veya yeni optimizasyon çalışması durdurulur.

## 12. Risk kaydı

| Risk | Olasılık/etki | Erken işaret | Azaltma |
|---|---|---|---|
| PLC protokolünün geç gelmesi | Yüksek/Yüksek | Doküman veya test uç noktası yok | Servis sınırını sabitle, protokol simülatörü hazırla, gerçek entegrasyon için tarih kapısı koy |
| Flutter–ROS backend uyumsuzluğu | Yüksek/Yüksek | UI “Backend yok” gösteriyor; node/route yalnız yerelde | Ortak mesaj/servis sözleşmesi, sözleşme testleri, aynı release kimliği ve canlı Orange Pi kabulü |
| Teker aralığı/TF yanlışlığı | Orta/Yüksek | Dönüşlerde harita/odom ayrışması | F0 ölçüm, tek sözleşme, fail-fast |
| QR/çizgi ışık hassasiyeti | Yüksek/Yüksek | Güven ve poz zıplaması | Sabit exposure, kalibrasyon, çeşitli ışık veri seti, kontrollü hız |
| 5 kg’da motor/fren/lift yetersizliği | Orta/Yüksek | Akım, kayma, limit timeout | Erken yüklü test, hız/ivme profili, mekanik iyileştirme |
| Rota sapması 10 cm’yi aşması | Orta/Yüksek | Köşe kesme, AMCL sıçrama | Lokalizasyon marjı, RPP yüklü profil, route guard, doğru yol geometrisi |
| 60 dakika kuruluma yetişememe | Orta/Yüksek | Elle dosya düzenleme, validator geç kalması | GUI otomasyonu, hazır rol şablonu, iki farklı saha provası, 55 dk hedef |
| Güvenlik bypass launch kullanımı | Orta/Çok yüksek | Doğrudan `/cmd_vel` | Üretim allowlist, launch testi, topic yayıncı denetimi |
| Wi‑Fi/rosbridge kopması | Orta/Yüksek | GUI bayat, PLC gecikmesi | Robot otonomluğu GUI’den bağımsız, reconnect/idempotency, iki cihaz provası |
| Terminal yaw/motor deadband | Yüksek/Yüksek | Hedef koordinatta çok düşük RPM isteği, robot duruyor, `FollowPath status=6` | Normal node'larda route heading, explicit dönüşleri ayrı Spin action, deadband regresyonu |
| Yanlış gate yönü veya eski izin | Orta/Çok yüksek | q5/q6 yönü karışıyor, önceki izin yeni geçişi açıyor | Outbound q5/return q6 geçiş kimliği, tek kullanımlık izin, iki yönlü fault injection |
| Junction-turn başarısızlığı | Orta/Yüksek | Robot D düğümünde ters/çapraz kalıyor veya sonraki segment erken başlıyor | Edge-geometri kararı, FollowPath–STOP–Spin–STOP sırası, abortta sonraki segmente geçmeme |
| İstasyon çıkışında kontrol kaynağı çakışması | Orta/Çok yüksek | Lane ve Nav2 aynı anda sıfır-dışı hız üretiyor veya QR tekrar dönüş başlatıyor | EXITING_STATION yetkilendirmesi, lane STOP/disarm, motion-source sahipliği testi |
| Son gün değişikliği regresyonu | Yüksek/Yüksek | Kanıtsız hotfix | 16 Eylül freeze, tam smoke zorunluluğu, geri dönüş release’i |
| Resmî şartname/teknik cevap değişikliği | Orta/Yüksek | Yeni PDF dosya adı/mail | Günlük sorumlu, sürüm diff’i, gereksinim matrisi güncelleme |

## 13. Kapanan girdiler ve açık sorular

Kapanan girdiler:

- Finalistlik: doğrulandı; hareket ve kabiliyet videosu geçildi.
- Flutter projesi: `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` bulundu ve plan kapsamındaki kaynakları incelendi.
- Teker aralığı: gerçek tahrik tekeri eksenleri arası physical/geometric değer `0.430 m`; 360° odometri kalibrasyonundan gelen odometry-effective değer `0.433 m`.
- Kamera/docking yerleşimi: şerit takibi için lift/arka tarafta tek kamera vardır; A ve B girişleri 180° dönüş sonrası bu kamerayla geri docking, çıkışları lane STOP + Nav2'dir.
- Saha örneği approach eşleşmeleri: A1/q2, A2/q3, A3/q4, B1/q9, B2/q8, B3/q7; production'da aktif saha paketinden okunacaktır.
- Kapı yönü: gidişte q5 outbound izin noktası, dönüşte q6 return izin noktasıdır ve her fiziksel geçiş yeni izin gerektirir.
- IMU politikası: production görev `imu:=false` ile çalışabilmeli; IMU yalnız etkin profilde ek health/yaw doğrulama kaynağıdır.
- Lift ve limit sensörleri: fiziksel olarak çalışıyor; ROS action/görev entegrasyonu ile yüklü kabul henüz yapılacak.
- PLC protokolü: henüz takıma verilmedi; Faz 7’nin dış bağımlılığıdır.

Kalan sorular ilk fazlarda kapanmadan ilgili alt sistem tamamlanmış sayılamaz:

1. Final ulaşım, kurulum, saha test rezervasyonu ve robot/PC MAC bildirim ayrıntıları geldi mi?
2. PLC protokol belgesinin teslim tarihi veya teknik kurul temas noktası belli mi?
3. Arka kameranın yarışma sahasında kullanılacak sabit exposure/FPS modu ve QR’ın resmî fiziksel boyutu kesinleşti mi?
4. QR içeriğinin beklenen şeması ile istasyon eşlemesi açıklandı mı?
5. Fiziksel manuel/otomatik anahtarın elektriksel doğruluk tablosu nedir; docking/lift için manuel kip politikası nasıl olmalı?
6. Güncel resmî araç ve palet ölçü çizimi için teknik kuruldan alınmış CAD veya yazılı açıklama var mı?
7. Kontrollü kapının resmî mesaj şeması, endpoint'i, heartbeat/timeout değerleri ve geçişin fiziksel olarak tamamlandığını bildiren koşul açıklandı mı?
8. Otomatik şarj istasyonunun mekanik/elektrik çizimi yayımlandı mı?

## 14. “Yarışmaya hazır” tanımı

Proje, yalnız düğümler açıldığı veya simülasyon geçtiği için yarışmaya hazır sayılmaz. Yarışmaya hazır olma; güncel resmî şartnameye göre doğru ölçülerdeki gerçek aracın, internetsiz iki cihazlı yarışma ağı üzerinde, yeni bir sahayı 55 dakika içinde haritalayıp arayüzden geçerli rota paketi oluşturması; PLC’den rastgele A/B görevi alması; hedef approach QR'ını aktif saha paketinden doğrulayıp 180° dönmesi; yalnız arka kamera ile geri docking yaparak 5 kg yükü tolerans içinde alması/bırakması; lift sonrasında lane STOP edip önce ilgili approach node'a Nav2 ile çıkması; gerekli D1–D6 kavşaklarında rota geometrisine bağlı junction Spin uygulaması; normal segmentlerde route heading kullanarak terminal-yaw/deadband abort'u üretmemesi; gidişte q5'te, dönüşte q6'da her fiziksel geçiş için yeni izin beklemesi; tanımlı rotadan 10 cm’den fazla sapmaması; engelde çarpmadan durup engel kalkınca devam etmesi; `imu:=false` production profiliyle de çalışabilmesi; WAIT noktasına dönüp görevi tamamlaması; tüm zorunlu durum ve iletişimi GUI’de göstermesi ve bunu müdahalesiz, 30 dakikanın altında üç ardışık koşuda tamamlamasıdır.

Bu tanım sağlanmadan opsiyonel puan özelliği veya yalnızca sunum amaçlı iyileştirme, zorunlu işlerin önüne geçmemelidir.
