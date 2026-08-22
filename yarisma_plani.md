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
- Fiziksel etkin teker aralığı `0.460 m` kabul edilecektir. Önceki `0.421 m` değeri, düzeltilmekte olan STM32 verileri üzerinden yapılan hesaplamadan türemiştir.
- Lift sistemi ve limit sensörleri fiziksel olarak çalışmaktadır. Eksik olan kısım, bunların yarışma görev yöneticisine güvenli ve geri bildirimli ROS action olarak bağlanması ve ölçümlü kabulüdür.

Bu girdiler planlama kararıdır; firmware düzeltmesi sonrasında `0.460 m` değeri düz/rotasyon fiziksel deneyleriyle yeniden doğrulanıp araç sözleşmesine işlenecektir.

## 2. Yönetici özeti

Mevcut depo iyi bir ROS temeline sahiptir: STM32 taban sürücüsü, odometri/IMU yayını, SLAM Toolbox, AMCL, Nav2 Route Server, Regulated Pure Pursuit, güvenli hız zinciri, harita/lokalizasyon yöneticileri, docking ve görev action arayüzleri, görev durum mesajları ve simülasyon altyapısı vardır.

Ancak depo bugün itibarıyla yarışma görevinin tamamını gerçek donanımda uçtan uca yapabilecek durumda değildir. Yarışmaya çıkışı engelleyen başlıca konular şunlardır:

- Araç sözleşmesi denetimi başarısızdır: fiziksel olarak kabul edilen `0.460 m`, sözleşmede kalan eski `0.421 m` ile henüz tekleştirilmemiştir; STM32 firmware düzeltmesi sonrası yeniden kabul gerekir.
- Çalışma alanında güncel `build/` ve `install/` bulunmadığından mevcut HEAD için temiz derleme/test kanıtı yoktur.
- Operatör arayüzünden şartnameye uygun rota öğretme, semantik düğüm tanımlama ve aktif saha paketini devreye alma akışı eksiktir.
- Gerçek çizgi/QR algısının `LaneOffset` ve `QrDetection` üretim bağlantısı yoktur; QR içeriği ve kameraya göre metrik poz çıkarımı tamamlanmamıştır.
- PLC wire protokolü henüz gelmemiştir; gerçek PLC adaptörü yoktur. Lift ve limit donanımı çalışsa da gerçek `LiftLoad` action sunucusu/görev entegrasyonu yoktur.
- Görev yöneticisi q5 kapısını her iki yöndeki geçişlerde yönetmemekte, düğüm yönelimini kullanmamakta ve yük arkada kalacak hareket kuralını garanti etmemektedir.
- Üretim ortamında rota sapmasını ölçen ve `±10 cm` kuralını gözeten bir route guard yoktur.
- Flutter GUI mevcuttur ve rosbridge, mapping/lokalizasyon, görev özeti, QR/PLC alanları ile fiziksel manuel moda bağlı hız kilidi için ciddi bir temel sunar; fakat düğüm/rota kayıtları ROS backend olmadığı için yerel draft/stub seviyesindedir, gerçek PLC kaynağı yoktur ve fiziksel uçtan uca kabul beklemektedir.
- Bazı launch yolları güvenlik zincirini atlayabilmekte; mapping kontrolünde engel algılama varsayılanı yarışma için kapalıdır.
- Gerçek sistem launch’ı test haritası/grafı varsayılanlarıyla açılabilmekte ve çalışma zamanında kaydedilen saha paketini otomatik seçmemektedir.

Bu nedenle öncelik “yeni özellik eklemek” değil, aşağıdaki zorunlu zinciri eksiksiz ve ölçülebilir hâle getirmektir:

`fiziksel sözleşme → güvenli taban → lokalizasyon → saha paketi/rota → gerçek algı/docking → rota koruması → PLC/lift/görev → GUI → hata testleri → 60 dakikalık kurulum → tam prova`

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
| R07 | İstasyondan yaklaşık 1.5 m önceki çizgiyi işleme | Kısmi | F5 | Doğal navigasyondan çizgi/docking kipine güvenli devir |
| R08 | Hibrit navigasyonla hassas yanaşma | Kısmi/mok | F5 | Bekleme, alma ve bırakmada ±7.5 cm, ±5° |
| R09 | Rota sapmasını en fazla 10 cm’de tutma | Bloker | F6 | Gerçek aktif rota üzerinde zaman eşlemeli maksimum sapma ölçümü |
| R10 | Engel görünce çarpmadan durma | Temel var | F1, F8 | Hareketli ve sabit engelde temas yok, duruş mesafesi kaydı |
| R11 | Engel kalkınca göreve devam etme | Kısmi | F8 | Uzun beklemede gereksiz görev iptali olmadan otomatik devam |
| R12 | q5’te PLC’ye bildir, izin bekle, geç | Kısmi/mok | F6, F7 | Gidiş ve dönüşte izinsiz geçiş yok; tekrar mesaj güvenli |
| R13 | Yükü azami 5 kg ile taşıma | Fiziksel kanıt gerekli | F1, F10 | 5 kg ile kaldırma, taşıma, bırakma ve fren testleri |
| R14 | Yükü hareket yönünün ters tarafında tutma | Bloker | F3, F6, F7 | Yük durumuna göre yön/yaw/kenar kuralı ve video kanıtı |
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
| P0 | Fiziksel karar `0.460`; `vehicle_contract.yaml` içinde eski `0.421` kaldığı için sözleşme kontrolü başarısız; STM32 firmware düzeltmesi sürüyor | Firmware sonrası kalibrasyon ve sözleşme tekliği olmadan odometri kabul edilemez |
| P0 | Güncel kaynak için temiz build/test kurulumu yok | Geçmiş başarı kayıtları bugünkü HEAD’i kanıtlamıyor |
| P0 | PLC protokolü/adaptörü yok; çalışan lift/limit donanımının gerçek action sunucusu yok | Yük alma/bırakma ve kapı görevi uçtan uca tamamlanamaz |
| P0 | Üretim QR/çizgi düğümleri docking arayüzlerini üretmiyor | Hassas yanaşma gerçek sensörle çalışamaz |
| P0 | Flutter GUI var; `/stations/*` ve `/routes/*` açıkça backend stub, lift komutu pasif, PLC verisi gerçek kaynağa bağlı değil | Rota hazırlama ve görev ekranı yarışma backend’i olmadan tamamlanamaz |
| P0 | Görev yöneticisi q5’i yalnız sınırlı akışta ele alıyor; dönüş geçişi yok | Kapı ihlali veya senaryo kilitlenmesi riski |
| P0 | Yük arkada kalacak yön kuralı uygulanmıyor | Açık şartname ihlali |
| P1 | Semantik rota editörü, saha sürümü ve atomik aktivasyon yok | 60 dakikalık hazırlık güvenilir değil |
| P1 | Üretim route guard/cross-track yayını yok | 10 cm sapma ölçülemiyor ve korunamıyor |
| P1 | Gerçek sistem test haritası/grafı ile açılabiliyor | Yanlış saha verisiyle hareket riski |
| P1 | Mapping kontrolünde engel algılama yarışma için kapalı varsayılabiliyor | Haritalama sırasında çarpışma riski |
| P1 | Bağımsız çizgi launch’ları güvenli hız zincirini atlayabiliyor | Güvenlik mimarisi devre dışı kalabilir |
| P1 | Güvenlik yöneticisinin 15 saniye engel bekleme sonrası iptali | Şartnamedeki “engel kalkınca devam” davranışını bozabilir |
| P1 | QR docking boyunca sürekli taze algı bekliyor | QR görüşten çıkınca yanaşma gereksiz iptal olabilir |
| P1 | Kamera çözünürlüğü ve sensör TF’leri belgeler arasında çelişkili | Algı kalibrasyonu tekrarlanamaz |
| P2 | Otomatik şarj görevi yok | Yalnızca +5 ek puan kaybı; ana görevi engellemez |

### 4.3 Sözleşme ve belge çelişkileri

Bu değerler Faz 0’da tek bir tarihli “araç sözleşmesi” altında çözülecektir:

- Etkin teker aralığı kararı: fiziksel değer `0.460 m`; `0.421 m`, eski STM32 verisiyle hesaplanmış tarihsel değerdir. Firmware düzeltmesi sonrası `0.460 m` fiziksel testle doğrulanacak ve bütün sözleşme/config/belgelerde tek değer yapılacaktır.
- LiDAR konumu: eski belgelerde geride/düşük, güncel kaynak yorumunda önde ve daha yüksek değerler.
- Ön kamera ve arka kamera konumları: ön ölçüm mevcut, arka konum simetri varsayımına dayanıyor.
- Kamera eğimi: yaklaşık 45° tahmin; kalibre ölçüm değil.
- Kamera yayın biçimi: bazı ayarlar 320×240 isterken donanım notları desteklenen en düşük modun farklı olduğunu belirtiyor.
- IMU ifadesi: eski belgelerde haricî IMU, güncel gerçek profilde STM32’den gelen yaw.
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
- `role`: `WAIT`, `PICKUP_APPROACH`, `PICKUP_DOCK`, `DROPOFF_APPROACH`, `DROPOFF_DOCK`, `GATE_Q5`, `QR_TRIGGER`, `TRANSIT`, gerekirse `CHARGE`.
- `station_id`: `A1..A3`, `B1..B3`, `q1..q9`, `D1..D6` eşleşmesi.
- İzin verilen yüklülük: boş, yüklü veya her ikisi.
- İzin verilen hareket yönü ve yükün arkada kalma kuralı.
- Kenar yönü, hız limiti, dönüş yarıçapı ve kapı geçiş olayı.
- Hassas yaklaşma modu: doğal navigasyon veya line/docking.
- Harita ve araç sözleşmesi sürümü.

Validator “bütün düğümler birbirine bağlı” kontrolünden fazlasını yapmalıdır. Dokuz A×B görevi için gereken yönlü yolları, her gerekli q5 geçişini, dönüş yolunu, istasyon yaw’larını, yük yönünü, çakışan kimlikleri ve harita sınırlarını denetlemelidir.

### 5.4 Görev durum makinesi

Referans akış:

```text
BOOT/PREFLIGHT
  → WAITING_FOR_TASK
  → EMPTY_ROUTE_TO_A_APPROACH
  → QR_A_VERIFY
  → DOCK_A
  → LIFT_LOAD
  → LOADED_ROUTE_TO_B
      → (yol q5 içeriyorsa) GATE_NOTIFY → GATE_WAIT → GATE_PASS
  → QR_B_VERIFY
  → DOCK_B
  → DROP_LOAD
  → RETURN_ROUTE
      → (dönüş q5 içeriyorsa) GATE_NOTIFY → GATE_WAIT → GATE_PASS
  → WAIT_POSITION
  → TASK_COMPLETE_NOTIFY
  → WAITING_FOR_TASK
```

Her durum; giriş koşulu, timeout, tekrar deneme, güvenli duruş, PLC mesajı, GUI metni ve kalıcı olay kaydıyla tanımlanmalıdır. Aynı görev veya kapı izni tekrarlı geldiğinde çift kaldırma/indirme ya da izinsiz hareket olmamalıdır.

## 6. Faz planı

Fazların kabul kapıları zorunludur. Bir faz “çalışıyor gibi göründüğü” için değil, tanımlı kanıtları ürettiği için tamamlanır.

### F0 — Resmî sürüm, finalist durumu ve mühendislik temeli

**Süre:** 22–23 Ağustos  
**Öncelik:** P0  
**Amaç:** Yanlış şartname, yanlış fiziksel parametre veya doğrulanmamış build üzerinde çalışma riskini kaldırmak.

Yapılacaklar:

1. Finalistlik video aşamasıyla doğrulandı; takım giriş bilgilerini, final ulaşım/kurulum saatini ve saha test hakkını resmî kanaldan ayrıca doğrula.
2. V1.1’i proje arşivine sürüm/hash bilgisiyle kaydet; mail grubu ve yarışma sayfası için günlük değişiklik kontrol sorumlusu ata.
3. Güncel commit’te temiz `colcon build` ve tüm uygun `colcon test` çalıştır; sonuçları tarihli artefakt olarak sakla.
4. Fiziksel robotu ölç: gövde, toplam çatal boyu, en, yükseklik, minimum dönüş zarfı, ağırlık, 5 kg yüklü ağırlık merkezi.
5. Teker çapı, etkin teker aralığı, encoder CPR/tick, motor yönleri ve yaw işaretini yeniden ölç.
6. LiDAR, ön/arka kamera, taban, teker ve çatal TF’lerini fiziksel referans noktalarından ölç.
7. Donanım listesi çıkar: cihaz yolu, USB kimliği/udev, seri numarası, yedek parça, güç hattı ve sigorta.
8. `0.460 m` fiziksel değeri kanonik kabul et; STM32 firmware düzeltmesinden sonra düz sürüş/dönüş deneyiyle doğrula, eski `0.421 m` sözleşme ve belgelerini kontrollü biçimde güncellemeden odometri/lokalizasyon ayarını dondurma.
9. Flutter deposu bulundu; onun ROS sözleşme sürümünü kaydet. Henüz gelmeyen PLC protokol dokümanı için dış bağımlılık sahibi/takip tarihi belirle ve çalışan lift donanımının ROS action/telemetri arayüzünü belgele.
10. Zorunlu özellikler için sahiplik ve günlük entegrasyon saati belirle.

Kabul kapısı:

- Temiz build ve test raporu var.
- Araç sözleşmesi denetimi sıfır hata veriyor.
- Tüm fiziksel ölçüler imzalı ölçüm formunda.
- Güncel şartname ve finalistlik doğrulanmış; final lojistiği kayıt altındadır.
- Flutter–ROS sürüm eşleşmesi bilinir; PLC protokolü gelene kadar wire alanları uydurulmaz; lift için çalışan donanımdan action sonucuna kadar arayüz tanımlıdır.

### F1 — Fiziksel taban, lift ve güvenlik omurgası

**Süre:** 24–26 Ağustos  
**Bağımlılık:** F0  
**Amaç:** Robotu boş ve 5 kg yüklü durumda güvenli, ölçülebilir ve tekrarlanabilir hareket ettirmek.

Yapılacaklar:

1. STM32–ROS paket formatını, sayaç taşmasını, yeniden bağlanmayı, CRC hatasını ve 200 ms watchdog’u doğrula.
2. Sol/sağ teker yönü, encoder işareti, m/tick ve etkin teker aralığını kalibre et.
3. Boş ve 5 kg yüklü hâlde motor PID/feed-forward ve düşük hız kararlılığını ayrı ölç.
4. Çalışan lift/limit donanımını temel alarak gerçek `LiftLoad` action sunucusu sözleşmesini sabitle: hedef seviye, timeout, limit switch, yük var/yok, overcurrent, iptal ve sonuç kodları.
5. Yük alma/bırakma mekanizmasını 5 kg ile en az 30 çevrim mekanik teste tabi tut; düşme ve sürüklenmeyi kaydet.
6. E-stop’un teker ve lift güç/komut zincirini kestiğini fiziksel olarak test et; yazılım düğümü kapanmasına bağımlı olmasın.
7. Fiziksel mod anahtarının truth table’ını yaz: otomatik, manuel, geçiş anı, bilinmeyen/bayat sinyal.
8. Tüm hareket launch’larını tek güvenlik zincirine bağlama işi için envanter çıkar; yarışmada kullanılmayacak bypass launch’larını üretimden karantinaya al.
9. Maksimum hız, ivme, açısal hız ve frenleme mesafesini boş/yüklü profil olarak belirle.

Kabul kapısı:

- 10 m düz sürüşte mesafe hatası hedef `%2` veya daha iyi; iki yönde benzer sonuç.
- 360° dönüşlerde tekrarlanabilir yaw hatası hedef `≤3°`; lokalizasyon olmadan ve lokalizasyonla ayrı rapor.
- E-stop, haberleşme kaybı ve komut bayatlığında tüm hareket güvenli durur.
- Otomatik kipte uzaktan manuel komut robotu hareket ettiremez.
- 5 kg ile 30 kaldır/indir çevriminde yük düşmesi yok; limit ve aşırı akım davranışı doğru.
- Güvenli maksimum yarışma hızları yazılı ve config’e aktarılmaya hazırdır.

### F2 — Sensör, TF, haritalama ve lokalizasyon

**Süre:** 27–29 Ağustos  
**Bağımlılık:** F1  
**Amaç:** Haritadan bağımsız tekrar kurulabilen sensör geometrisi ve şartname toleransını destekleyen lokalizasyon.

Yapılacaklar:

1. `base_footprint → base_link → laser/camera/fork` TF zincirini ölçülen sözleşmeye göre doğrula.
2. LiDAR scan açısı, ters/ayna yönü, kör bölgeler, çatal/yük yansıması ve speckle filtresini test et.
3. Ön ve gerekiyorsa arka kamerada desteklenen gerçek çözünürlük/FPS/pixel formatı sabitle; intrinsic ve distortion kalibrasyonu yap.
4. Encoder odometrisi ile STM32 yaw birleşiminin covariance, zaman damgası ve işaretlerini doğrula.
5. SLAM sırasında loop closure, koridor paralelliği, harita çözünürlüğü ve yeniden açma davranışını ölç.
6. Harita kaydında PGM/YAML/PNG, posegraph, başlangıç pozu ve metadata’nın atomik üretildiğini test et.
7. Mapping ile AMCL’nin aynı anda çalışmadığını; geçişte eski TF/node kalmadığını doğrula.
8. AMCL başlangıç pozu, kidnapped robot, LiDAR kesintisi ve odometri sapması deneyleri yap.
9. Zeminde ölçülmüş referans işaretlerinde gerçek poz–AMCL poz farkını raporla.

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

1. Saha listesi, oluşturma, kaydetme, silmeden arşivleme, doğrulama ve atomik aktivasyon servislerini tanımla.
2. Robotun güncel lokalize pozunu GUI’den semantik düğüm olarak kaydet: bekleme, A yaklaşım/dock, B yaklaşım/dock, q1–q9, D1–D6, q5, QR trigger.
3. Her düğümde x/y yanında yaw, rol, istasyon, yük/yön kuralı ve yaklaşma modu kaydet.
4. Kenar ekleme/silme, yönlü/çift yönlü geçiş, hız limiti ve kapı olayı tanımla.
5. Harita koordinatına tıklama ile “robot pozunu kaydetme” yöntemlerini birlikte sun; istasyon yaw’ında sayısal ince ayar sağla.
6. Dokuz A×B görevi ve bekleme dönüşleri için gerekli yönlü erişilebilirlik matrisini validator’da kontrol et.
7. q5’ten geçen her kenarın kapı olayı taşıdığını, izinsiz alternatif kestirme bulunmadığını denetle.
8. Yüklü kenarlarda yükün hareket yönünün tersinde kalmasını statik olarak doğrula.
9. Aktif saha paketi değişirken Nav2/lokalizasyonun güvenli durup doğru map/graf ile yeniden açılmasını sağla.
10. Demo/test graph’larının üretim profiline yanlışlıkla seçilmesini engelle.

Kabul kapısı:

- Sıfırdan bir örnek alan, yalnız kullanıcı arayüzü kullanılarak 45 dakika içinde haritalanıp rotalanır.
- Validator dokuz A×B görevinin tümünü, gidiş/dönüş q5 durumlarını ve yük yönünü geçer.
- Eksik yaw, yinelenen ad, harita dışı düğüm, kopuk kenar ve yanlış q5 olayı aktivasyonu engeller.
- Aktif paket hash’i GUI ve robot durumunda görünür; yarım yazılmış dosya aktif olamaz.

### F4 — Yarışma GUI’si ve çevrimdışı ağ

**Süre:** 30 Ağustos–3 Eylül; F3 ile paralel  
**Bağımlılık:** F0 arayüz erişimi, F3 sözleşmeleri  
**Amaç:** Şartnamenin rota hazırlama ve izleme gereksinimlerini iki cihazlı, internetsiz yapıda karşılamak.

Mevcut Flutter tabanı `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` dizinindedir. Kaynak incelemesine göre rosbridge yeniden bağlantısı, `/robot_status` bayatlık kilidi, fiziksel manuel mod olmadan `/cmd_vel_manual` reddi, mapping/lokalizasyon akışı, node/route sayfaları ve “GELEN/GÖNDERİLEN” PLC özet alanları vardır. Buna karşılık node/route sayfaları ROS kalıcı backend’i olmadığı için yerel draft/stub kullanır; lift kontrolü bilinçli olarak pasiftir; PLC alanlarının gerçek veri kaynağı ve zaman damgalı mesaj geçmişi henüz yoktur.

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
3. Manuel sürüş denetimini yalnız fiziksel anahtar manuel sinyali tazeyken etkinleştir; GUI butonu tek başına yetki vermesin.
4. Otomatik kipte manuel topic yayını olsa bile robot tarafında ikinci kez reddet.
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

1. Görev yöneticisinin tekil `NavigateToPose` yerine semantik rota/graf yürütme sözleşmesini kullanmasını sağla.
2. Rota maliyetinde mesafe, süre, yük durumu, dönüş maliyeti, q5 bekleme ve izin verilmeyen yönleri dikkate al.
3. Düğüm yaw’ını hedef pozda uygula; her hedefi sıfır yaw ile çağırma.
4. RPP’yi düz, dar dönüş, ileri, geri, boş ve yüklü profillerde kalibre et.
5. Aktif rota geometrisine en yakın nokta/projeksiyon üzerinden zaman eşlemeli cross-track error üret.
6. Sapma için davranış bandı tanımla: örneğin `5 cm` uyarı, `8 cm` hız azaltma, `10 cm` güvenli duruş/yeniden değerlendirme. Kesin eşikler fiziksel sonuçla sabitlenir.
7. Ani köşe kestirmeyi ve global yeniden planlamanın tanımlı rotadan kaçmasını engelle; engelden dolaşmak yerine güvenli bekle.
8. q5 kenar giriş/çıkış olayını rota yürütmeden üret; yalnız “pickup sonrası bir kez” varsayımına bağlama.
9. Yüklü harekette yalnız izinli yönleri seç; yük robotun hareket yönünün arkasında kalmalı.
10. Sapma, seçilen yol, edge id, hız limiti ve duruş nedenini bag/GUI’ye yayımla.

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

### F8 — Emniyet, arıza enjeksiyonu ve kurtarma matrisi

**Süre:** 13–14 Eylül  
**Bağımlılık:** F1–F7  
**Amaç:** Her tekil arızanın güvenli, görünür ve mümkünse devam edilebilir davranışa dönüşmesi.

Zorunlu testler:

| Arıza/olay | Beklenen davranış |
|---|---|
| E-stop basılması | Teker ve lift anında güvenli durur; görev hata/e-stop; kendiliğinden tekrar hareket yok |
| E-stop bırakılması | Açık reset/preflight olmadan hareket yok |
| Yol üstünde engel | Temas etmeden durur; rota korunur |
| Engel 5/30/120 saniye sonra kalkar | Kural izin veriyorsa görev kaldığı yerden otomatik ve yumuşak devam eder |
| Engel kalıcı | Robot güvenli bekler; keyfî rota değiştirmez; GUI açık neden gösterir |
| LiDAR/scan bayat | Güvenli duruş, açık sensör hatası |
| Kamera/QR bayat | Docking hız üretmez; kontrollü bekle/iptal |
| Odom/TF/AMCL kaybı | Navigasyon durur; poz geçerli olmadan devam etmez |
| PLC bağlantısı kaybı | Güvenli durur veya tanımlı durumu tamamlar; protokol kararıyla tutarlı |
| GUI/rosbridge kaybı | Otonom görev güvenli şekilde sürer; manuel kaynak aktifleşmez |
| STM32/UART kaybı | Watchdog motorları durdurur; tekrar bağlanınca kendiliğinden hareket yok |
| Fiziksel mod anahtarı değişimi | Debounce’lu, durum makinesine uygun, çift komutsuz geçiş |
| Lift limit/overcurrent | Lift durur, sürüş engellenir, yük durumu bilinmiyor olarak işaretlenir |
| Düşük batarya | Zorunlu görev için güvenli politika; opsiyonel şarj yoksa görev başlamasını engelleyen eşik |
| Yanlış/tekrar QR | İstasyon kabul edilmez, yanlış lift eylemi yok |
| Yanlış saha paketi | Preflight görevi başlatmaz |

Kabul kapısı:

- Her satır için otomatik/mekanik test, bag ve sonuç kaydı vardır.
- Normal olmayan hiçbir durumda doğrudan `/cmd_vel` bypass’ı veya kontrolsüz lift hareketi yoktur.
- Engel bekleme timeout’u şartnamenin otomatik devam beklentisiyle uyumludur; 15 saniyelik geliştirme varsayımı yarışma davranışını belirlemez.
- E-stop ve watchdog testleri gerçek donanımda tekrarlanmıştır.

### F9 — 60 dakikalık harita ve rota hazırlama provası

**Süre:** 14–15 Eylül  
**Bağımlılık:** F2–F4, F6  
**Amaç:** İkinci aşamaya geçiş kapısı olan saha hazırlığını baskı altında tamamlamak.

Önerilen dakika planı:

| Süre | İş | Çıkış |
|---|---|---|
| 00–05 | Araç ölçü/güç/ağ/preflight, saat ve disk kontrolü | Tüm sağlıklar yeşil |
| 05–25 | Güvenli manuel haritalama, kapı ve istasyon çevreleri | Kapalı/temiz 2B harita |
| 25–30 | Harita kaydı, mapping kapatma, lokalizasyon açma | AMCL kararlı, başlangıç pozu doğru |
| 30–45 | WAIT, A1–A3, B1–B3, q1–q9, D1–D6 ve gerekli yaklaşım/dock pozlarını öğretme | Semantik düğümler |
| 45–50 | Kenarlar, yönler, yük kuralları, q5 olayları ve hızlar | Tam yönlü rota grafı |
| 50–54 | Validator ve atomik aktivasyon | Geçerli saha paketi |
| 54–58 | En uzak A→B→WAIT smoke testi; q5 el sıkışma testi | Hareket kanıtı |
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
- Eski/test haritası kullanma, yanlış graph seçme veya elle dosya düzenleme ihtiyacı yoktur.

### F10 — Tam yarışma provası ve performans

**Süre:** 15–16 Eylül  
**Bağımlılık:** F1–F9  
**Amaç:** Hakem müdahalesi dışında tek komutla tam senaryoyu puan ve süre hedefinde tamamlamak.

Yapılacaklar:

1. Görevi PLC/test sistemi rastgele seçsin; ekip önceden A/B bilmesin.
2. Robot beklemeden başlasın; pickup, q5, dropoff ve dönüşün tamamı otonom olsun.
3. Bir koşuda kısa süreli engel, bir koşuda uzun engel; bir koşuda GUI yeniden bağlantısı uygula.
4. Boş ve yüklü hızları toplam süreyi 30 dakikanın altında tutacak ancak sapma/duruş payını bozmayacak şekilde ayarla.
5. Poz toleransı, maksimum rota sapması, q5 izin zamanları, yük düşmesi ve toplam süreyi otomatik raporla.
6. En az iki farklı batarya seviyesinde ve iki farklı zemin tutuşunda dene.
7. Kullanıcı paneline izleme dışında dokunmadan tamamla.
8. Her başarısızlığı kök neden, düzeltme ve tekrar testiyle kapat; yalnız “yeniden deneyince geçti” kabul edilmez.

Kabul kapısı:

- Üç ardışık tam görev başarıyla tamamlanır.
- Her biri `<30 dakika` hedefinde; hiçbir koşu 45 dakikaya yaklaşmaz.
- Maksimum rota sapması `<10 cm`; her istasyon ve bekleme pozunda `±7.5 cm/±5°`.
- Yük düşmesi, çarpışma, izinsiz q5 geçişi veya operatör müdahalesi yoktur.
- GUI’de şartnamedeki tüm bilgiler ve PLC tx/rx geçmişi görünürdür.

### F11 — Release dondurma ve yarışma operasyonu

**Süre:** 16–17 Eylül; final boyunca kontrollü kullanım  
**Bağımlılık:** F10  
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

Kabul kapısı:

- Temiz makine/hesapta internet olmadan sistem açılır.
- Release commit’i, firmware ve GUI build’i eşleşir.
- Soğuk açılıştan göreve hazır olma iki tekrarda ölçülmüş ve prosedüre uygundur.
- Geri dönüş release’i fiziksel araçta denenmiştir.

### F12 — Opsiyonel puanlar: otomatik şarj, yerlilik, özgünlük

**Başlama şartı:** F10 üç ardışık kez geçmiş ve yarışma release’i dondurulmuş olmalı.  
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
| 13–14 Eylül | F8 arıza matrisi | safety kabulü |
| 14–15 Eylül | F9 iki 60 dk prova | saha hazırlık kabulü |
| 15–16 Eylül | F10 üç tam görev | yarışma kabulü |
| 16–17 Eylül | F11 release freeze/lojistik | imzalı final release |
| 18–20 Eylül | Yarışma finali | yalnız kontrollü hotfix |

Kritik yol: `F0 → F1 → F2 → F3 → F5 → F6 → F7 → F8 → F9 → F10 → F11`.

F4 kısmen paralel yürüyebilir. F12 kritik yolda değildir. Bir P0 blokeri hedef tarihinden iki gün fazla sarkarsa opsiyonel işler kapatılır ve ekip tam zamanlı kritik yola döner.

## 8. Gelecekte değişmesi muhtemel proje alanları

Bu bölüm değişiklik emri değil, fazlar başladığında etki analizidir.

| Alan | İncelenecek başlıca dosyalar/paketler | Beklenen iş |
|---|---|---|
| Araç sözleşmesi | `src/marco_base/config/base_driver.yaml`, `src/marco_bringup/config/vehicle_contract.yaml`, description/URDF | Ölçüm tekliği, TF ve kinematik |
| Sözleşme kapısı | `src/marco_bringup/scripts/check_vehicle_contract.py` | Tüm kritik parametrelerin fail-fast denetimi |
| Üretim launch | `src/marco_bringup/launch/real_system.launch.py` | Aktif saha, gerçek PLC/lift/perception, preflight |
| Mapping/localization | `src/marco_localization/scripts/mapping_manager.py`, `localization_manager.py`, `mapping_control.launch.py` | Atomik saha paketi, güvenli varsayılanlar |
| Rota | `marco_navigation` graph/config/launch ve `route_graph_validator.py` | Semantik editör, aktivasyon, rol/yön/q5 validator |
| Route guard | `marco_navigation` içinde yeni/uygun üretim düğümü | Aktif path ve cross-track metrikleri |
| Algı | `lane_tracking`, `marco_perception`, `qr_detector.py` | Gerçek `LaneOffset`, `QrDetection`, QR poz ve decode |
| Docking | `src/marco_docking/marco_docking/dock_server.py` | Latch, mod devri, kayıp algı, fiziksel tolerans |
| Görev | `src/marco_mission/marco_mission/mission_manager.py` | Semantik rota, yaw, q5 iki yön, yük yönü, idempotency |
| PLC | `marco_mission` veya ayrı transport paketi | Resmî protokol adaptörü, heartbeat, tx/rx log |
| Lift | `marco_base`/donanım paketi ve `LiftLoad.action` | Gerçek action sunucusu ve emniyet |
| Güvenlik | `marco_safety` config/launch/supervisor, tüm hareket launch’ları | Tek komut zinciri, obstacle resume, mod matrisi |
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
| q5 | İzinli geçiş | 0 izinsiz/tekrar etkili geçiş | Edge olayı + PLC tx/rx + poz |

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
- q5 gidiş/dönüş izinleri.
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
- [ ] GUI ile 55 dakika içinde sıfırdan saha paketi hazırlanabiliyor.
- [ ] Dokuz A×B rotası, q5 gidiş/dönüşleri ve yük yönleri validator’dan geçiyor.
- [ ] Gerçek QR decode + metrik poz + gerçek çizgi/docking çalışıyor.
- [ ] A, B ve WAIT toleransları ölçümlü olarak sağlanıyor.
- [ ] Rota maksimum sapması 10 cm’den küçük.
- [ ] Engel görülünce duruyor ve kalkınca otomatik devam ediyor.
- [ ] Gerçek PLC görev/kapı/tamamlanma haberleşmesi geçti.
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
| Son gün değişikliği regresyonu | Yüksek/Yüksek | Kanıtsız hotfix | 16 Eylül freeze, tam smoke zorunluluğu, geri dönüş release’i |
| Resmî şartname/teknik cevap değişikliği | Orta/Yüksek | Yeni PDF dosya adı/mail | Günlük sorumlu, sürüm diff’i, gereksinim matrisi güncelleme |

## 13. Kapanan girdiler ve açık sorular

Kapanan girdiler:

- Finalistlik: doğrulandı; hareket ve kabiliyet videosu geçildi.
- Flutter projesi: `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` bulundu ve plan kapsamındaki kaynakları incelendi.
- Etkin teker aralığı: fiziksel kanonik hedef `0.460 m`; firmware düzeltmesi sonrası kabul testi zorunlu.
- Lift ve limit sensörleri: fiziksel olarak çalışıyor; ROS action/görev entegrasyonu ile yüklü kabul henüz yapılacak.
- PLC protokolü: henüz takıma verilmedi; Faz 7’nin dış bağımlılığıdır.

Kalan sorular ilk fazlarda kapanmadan ilgili alt sistem tamamlanmış sayılamaz:

1. Final ulaşım, kurulum, saha test rezervasyonu ve robot/PC MAC bildirim ayrıntıları geldi mi?
2. PLC protokol belgesinin teslim tarihi veya teknik kurul temas noktası belli mi?
3. Ön/arka kamera modelleri, kullanılacak kamera sayısı, gerçek desteklenen modlar ve QR’ın fiziksel boyutu nedir?
4. QR içeriğinin beklenen şeması ile istasyon eşlemesi açıklandı mı?
5. Fiziksel manuel/otomatik anahtarın elektriksel doğruluk tablosu nedir; docking/lift için manuel kip politikası nasıl olmalı?
6. Güncel resmî araç ve palet ölçü çizimi için teknik kuruldan alınmış CAD veya yazılı açıklama var mı?
7. Kontrollü kapı protokolü ve geçiş algılama koşulu açıklandı mı; izin tek geçişlik mi ve dönüşte yeni izin kesin gerekli mi?
8. Otomatik şarj istasyonunun mekanik/elektrik çizimi yayımlandı mı?

## 14. “Yarışmaya hazır” tanımı

Proje, yalnız düğümler açıldığı veya simülasyon geçtiği için yarışmaya hazır sayılmaz. Yarışmaya hazır olma; güncel resmî şartnameye göre doğru ölçülerdeki gerçek aracın, internetsiz iki cihazlı yarışma ağı üzerinde, yeni bir sahayı 55 dakika içinde haritalayıp arayüzden geçerli rota paketi oluşturması; PLC’den rastgele A/B görevi alması; gerçek QR/çizgi algısı ile 5 kg yükü tolerans içinde alması; tanımlı rotadan 10 cm’den fazla sapmadan, yükü arkada tutarak ve q5’te her gerekli yönde izin bekleyerek taşıması; engelde çarpmadan durup engel kalkınca devam etmesi; yükü tolerans içinde bırakıp bekleme noktasına dönmesi; tüm zorunlu durum ve iletişimi GUI’de göstermesi; bunu müdahalesiz, 30 dakikanın altında ve üç ardışık koşuda tamamlamasıdır.

Bu tanım sağlanmadan opsiyonel puan özelliği veya yalnızca sunum amaçlı iyileştirme, zorunlu işlerin önüne geçmemelidir.
