# MarCO Forklift AMR — Güncel Uygulama Planı

> Tarih: 22.08.2026
>
> Ana teknik kaynak: `PROJE.md`  
> Mevcut durum ve geçmiş kanıtlar: `PROJE_PLANI.md`, `AGENT_REFERANS.md`,
> `TEST.md` ve güncel `src/` kaynak ağacı

## 1. Belge amacı

Bu belge eski fazları yeniden yaptırmak için değil, mevcut sistemden yarışmada
çalışacak fiziksel sisteme ulaşmak için hazırlanmıştır. Mimari karar çatışmasında
öncelik sırası şöyledir:

1. `PROJE.md` içindeki bağlayıcı mimari kararlar,
2. güncel kaynak kodunun gerçek davranışı,
3. tarihli ve tekrar üretilebilir test kanıtları,
4. eski plan ve referans belgelerindeki tarihsel bilgiler.

`PROJE_PLANI.md` geçmiş çalışmaların ayrıntılı günlüğü olarak korunacaktır. Bundan
sonraki aktif iş takibi bu dosyada yapılacaktır.

## 2. Durum anahtarı ve tamamlanma kuralı

- ✅ Tamamlandı: kaynak, hata yolu, tekrar edilebilir test ve uygun kabul kanıtı var.
- 🟡 Kısmi: kod veya simülasyon var; fiziksel kabul ya da uçtan uca entegrasyon eksik.
- ⬜ Başlanmadı veya doğrulanmadı.

Simülasyon sonucu fiziksel araç fazını yeşile çevirmeyecektir. Fiziksel kabul gereken
bir madde için tarihli komut, parametre özeti, rosbag/JSON ve sayısal sonuç tutulacaktır.

## 3. Değişmeyecek ana mimari

- Haritalama: YDLidar + SLAM Toolbox.
- Lokalizasyon: encoder odometrisi → EKF → AMCL.
- Global TF: `map → odom → base_footprint`.
- Rota: operatörün öğrettiği GeoJSON graph + Nav2 Route Server.
- Rota takibi: RPP; serbest alan planlayıcısı yarışma rotasının sahibi olmayacak.
- Engel: kaçınma/reroute değil, güvenli dur ve aynı rota üzerinde devam et.
- İstasyon: Nav2 yalnız `*_APPROACH` noktasına kadar; son yaklaşık 1.5 m QR ve
  renkli çizgi tabanlı docking.
- Hız zinciri: Nav2 → `/cmd_vel_raw` → Collision Monitor → `/cmd_vel_safe` →
  twist_mux → `/cmd_vel` → STM32.
- Flutter yalnız kullanıcı arayüzü ve ROS API istemcisi olacak; TF, GeoJSON,
  graph doğrulama ve rota hesabı ROS tarafında kalacak.
- Runtime saha verisi package `share` içine yazılmayacak.

## 4. Mevcut sistem özeti

| Bileşen | Durum | Mevcut gerçeklik |
|---|---|---|
| URDF ve TF | 🟡 | Model ve çerçeveler hazır; gerçek LiDAR montajı işlendi, bazı mekanik değerlerin tek kaynağa alınması gerekiyor. |
| STM32 sürücüsü | 🟡 | UART protokolü, seri transport, odometri ve fake STM32 var; gerçek firmware ve saha kalibrasyonu tamamlanmadı. |
| SLAM ve AMCL | 🟡 | Simülasyon kabulü ve gerçek masa/harita denemeleri var; gerçek araç sayısal kabulü yok. |
| Nav2 Route Server | 🟡 | GeoJSON, Route Server, scorer'lar ve simülasyon testleri var; aktif saha graph yönetimi yok. |
| RPP | 🟡 | Ortak taban ve gerçek/sim override dosyaları var; gerçek araç tuning'i yok. |
| Hız metadata'sı | 🟡 | `AdjustSpeedLimit` bağlandı; değiştirilen üretim BT'sinin dinamik kabulü henüz alınmadı. |
| Güvenlik zinciri | 🟡 | Collision Monitor, supervisor ve twist_mux simülasyonda çalışıyor; fiziksel duruş kabulü yok. |
| Docking | 🟡 | Action server ve simülasyon test girdileriyle 20/20 kabul var; gerçek kamera/QR/şerit yok. |
| Mission Manager | 🟡 | Görev, iptal, e-stop, mock PLC ve çok durak API'si var; saha graph semantiği, genel q5 olayı ve gerçek lift/PLC eksik. |
| Rosbridge/GCS | 🟡 | Flutter uygulaması `/mnt/c/Users/emre/desktop/liftant_v2_bitirme` altında; rosbridge/mapping ekranları var, kalıcı rota backend'i eksik. |
| Tek gerçek launch | 🟡 | `real_system.launch.py` mevcut; hâlâ package içi harita/graf ve eksik gerçek donanım adaptörlerine bağlı. |
| Rota editörü | ⬜ | `route_editor_node` ve servisleri yok. |
| Route guard | ⬜ | Mission `/route/cross_track_error` dinliyor fakat gerçek yayıncı yok. |

## 5. İlk çözülmesi gereken tutarsızlıklar

1. Teker parametreleri tek sözleşmede tutulacak: teker yarıçapı `0.100 m`
   (100 mm/10 cm), encoder `360 tick/tur`, fiziksel ve odometri teker aralığı
   `0.460 m`. Önceki `0.421 m`, düzeltilmekte olan STM32 verisiyle türetilmiş
   tarihsel değerdir; firmware sonrası `0.460 m` fiziksel olarak doğrulanacaktır.
2. ✅ Kanonik route sahibi kesinleştirildi: Mission Manager tek `NavigateToPose`
   action'ı açar; özel BT ilk ComputeRoute'tan sonra ComputeAndTrackRoute ile tek
   FollowPath'i eşzamanlı yürütür.
3. `real_system.launch.py` harita ve graph'ı package dizininden çözüyor. Yarışma
   verisi `~/marco_data/fields/<saha>/` altına taşınmalı.
4. Mission Manager graph'ı yalnız başlangıçta okuyup node `id/x/y` alanlarını
   kullanıyor; rol, yaw, yaklaşma, yön ve graph sürümü kullanılmıyor.
5. ✅ Route Server `/route_speed_limit`, Mission Manager yalnız reset olayı üretir;
   `/speed_limit` konusunun tek sahibi `speed_limit_manager` olmuştur.
6. `route_graph_validator.py` simülasyon odaklı ve ayak izini kod içinde sabitliyor;
   saha rolleri ve A/B erişilebilirlik matrisi henüz doğrulanmıyor.
7. ✅ `TEST.md` mock görev komutu güncel gerçek sözleşmeye geçirildi.
8. ✅ `AGENT_REFERANS.md` encoder, LiDAR ve route yürütme değerleri güncellendi.

---

## Faz 0 — Kaynak ve sözleşme tabanını sabitleme 🟡

**Amaç:** Yeni geliştirme başlamadan önce tek, derlenebilir ve çelişkisiz taban oluşturmak.

- ✅ Mevcut değişiklikler korunarak ROS başlangıç HEAD `9d5fd47` ve Flutter
  referans HEAD `46ac767`, `FAZ0_SOZLESME.md` içinde kaydedildi. Commit/push
  kullanıcıya bırakıldı.
- ✅ Kilitli araç değerlerini belgeleyip doğru tüketiciye bağla: teker yarıçapı
  `0.100 m`, encoder `360 tick/tur`, fiziksel ve odometri teker aralığı
  `0.460 m`; bu değerlerin tüketiciler arasında ayrışmasını test et.
- ✅ Nav2 footprint poligonu ile Collision Monitor bölgelerinin yazılım
  sözleşmesini kapsadığını ve 11.08 fiziksel ölçümüne göre LiDAR TF'nin
  `base_link`e göre `x=+0.350`, `y=0.000`, `z=+0.350 m` olduğunu otomatik
  testle doğrula. `base_link` yerden `0.100 m` olduğu için LiDAR tarama düzlemi
  yerden `0.450 m` olur.
- ✅ Route yürütme mimarisini kesinleştir: Route Server kenar olaylarını canlı tutan,
  FollowPath'i tek kez sahiplenen ve aktif path/edge yayınlayan tek akış kullan.
- ✅ `/speed_limit`, `/cmd_vel_raw`, `/cmd_vel_safe` ve `/cmd_vel` sahiplerini belgeleyip
  aynı topic'te belirsiz çoklu sahipliği kaldır.
- ✅ `AGENT_REFERANS.md` ve `TEST.md` içindeki güncel kodla çelişen komut/değerleri düzelt.
- ✅ Tüm 14 paketi temiz ortamda derle ve çevrimdışı otomatik testleri çalıştır.
- ⬜ STM32 firmware, fiziksel ölçüm/kalibrasyon, USB/udev envanteri, e-stop/mod
  truth table, lift action kabulü, final lojistiği ve PLC takip bilgisini kapat.

**Kabul durumu:** 22.08.2026 parametre tutarlılık testi PASS ve 14/14 paket
build PASS. Dokunulmamış kaynakla `colcon test-result` 72 testte 1 error,
0 failure, 5 skip göstermektedir; tek error ayrı çalışma alanı olan
`lane_tracking` paketinin WSL'de eksik `pyopencl` bağımlılığıdır. Flutter
`analyze` temiz; Flutter testlerinde 50 PASS, canlı rosbridge ortamı gerektiren
1 test SKIP. Fiziksel araç ve `lane_tracking` hedef ortam kabulleri ayrıca
tamamlanacaktır.

## Faz 1 — Gerçek taban sürüşü ve odometri kalibrasyonu ⬜

**Bağımlılık:** Faz 0.

- ⬜ STM32 `STATE_ODOMETRY` veri düzenini firmware kaynaklarıyla kilitle: kümülatif
  yönlü tick, 360 tick/tur, sarma, hız birimi ve zaman damgası.
- ⬜ Sol ve sağ motorun encoder PID'ini ayrı doğrula; eşit hız hedefinde düz sürüşü ölç.
- ⬜ Gerçek yük altında etkin teker yarıçapını 10 m ileri/geri testleriyle kalibre et.
- ⬜ Wheel separation değerini iki yönde 360° dönüşlerle kalibre et; seçilen değeri
  URDF/base/test konfigürasyonlarında tek kaynaktan uygula.
- ⬜ Seri kopma, CRC hatası, watchdog ve yeniden bağlanma sırasında sıfır komut ve
  diagnostic/freshness üret.
- ⬜ Fork/lift komutunun gerçek STM32 yolu, limit switch ve hata geri bildirimi için
  üretim `LiftLoad` action server'ını ekle.

**Kabul:** 10 m hata <%2, iki yönde 360° yaw hatası <5°, düz sürüş lateral sapması
tarihsel olarak kaydedilmiş, seri kopmada güvenli duruş ve lift limit testleri PASS.

## Faz 2 — Gerçek haritalama ve lokalizasyon tabanı ⬜

**Bağımlılık:** Faz 1.

- ⬜ LiDAR `x/y/z/yaw` konumunu fiziksel ölçümle doğrula; TF ile gerçek montaj aynı olsun.
- ⬜ Gerçek scan rate, `scan_time`, `time_increment`, menzil ve QoS değerlerini kaydet.
- ⬜ Gerçek araçla tekrar edilebilir SLAM haritası çıkar; dönüşlerde duvar çoğalması ve
  kaymayı rosbag üzerinden incele.
- ⬜ Haritalama sonunda robot başlangıç noktasına dönerken son
  `map → base_footprint` pozunu sakla.
- ⬜ Kaydedilen map ile Map Server + AMCL'e geç ve saklanan pozu güvenli initial pose
  olarak kullan.
- ⬜ Sabit, düz, dönüş ve yeniden başlatma senaryolarında AMCL sağlık ölçümünü yap.

**Kabul:** Map kaydet/yükle PASS; TF tek sahipli; 5 dakika fiziksel sürüşte konum
<5 cm ve yaw <3°; başlangıç/yeniden lokalizasyon prosedürü tekrar edilebilir.

## Faz 3 — Saha veri deposu ve Route Editor çekirdeği ⬜

**Bağımlılık:** Faz 2 lokalizasyon sağlığı.

- ⬜ Yazılabilir veri yapısını oluştur:
  `~/marco_data/fields/<saha>/{map.yaml,map.pgm,route.geojson,field_meta.json}`.
- ⬜ Saha oluşturma, listeleme, seçme, kopyalama ve güvenli silme işlemlerini ROS API
  arkasına al; kaynak kod veya package share üzerine yazma.
- ⬜ Graph dahili modelini oluştur: node ID/name/type/x/y/yaw/station_id ve edge
  ID/start/end/polyline/yön/hız/yük/olay metadata'sı.
- ⬜ `route_editor_node` ekle; `map → base_footprint` pozunu kısa pencereyle örnekleyip
  x/y medianı ve circular yaw ortalaması hesapla.
- ⬜ Localization geçersiz, TF/scan/odom stale veya robot hareketliyken node kaydını reddet.
- ⬜ `START_WAIT`, `JUNCTION`, `PICKUP_APPROACH`, `DROPOFF_APPROACH`, `GATE` ve
  `INTERMEDIATE` rollerini destekle.
- ⬜ Segment durum makinesini uygula: başlat → ara noktalar → bitir/iptal.
- ⬜ Tek ve çift yönlü edge, undo ve delete işlemlerini ekle.
- ⬜ GeoJSON'u geçici dosya → doğrulama → atomik rename ile yaz; son iyi yedeği koru.

**Kabul:** Servis seviyesinde `D1 → A1` ve ayrı `D1 → D2` segmentleri oluşturulur;
yanlış `A1 → D2` edge'i oluşmaz; yeniden yüklenen GeoJSON aynı graph'ı verir.

## Faz 4 — Graph doğrulama, kayıt ve canlı aktivasyon ⬜

**Bağımlılık:** Faz 3.

- ⬜ Validator'ı gerçek saha verisine genelleştir; footprint ve map metadata'sını
  ortak konfigürasyondan al.
- ⬜ Duplicate ID/name, eksik uç, self-loop, boş geometri, finite olmayan koordinat,
  node-edge uç uyuşmazlığı ve hatalı metadata kontrollerini tamamla.
- ⬜ START, A1–A3 approach, B1–B3 approach ve q5 rollerinin varlığını doğrula.
- ⬜ Yönlü graph'ta START→tüm A, tüm A→tüm B ve tüm B→START erişilebilirlik
  matrisini hesapla.
- ⬜ Edge boyunca CAD footprint'in occupied, unknown ve map dışına taşmadığını kontrol et.
- ⬜ Kurulu Nav2 sürümündeki `SetRouteGraph` davranışını gerçek süreçle doğrula;
  yetersizse lifecycle reconfigure/restart uygulamasını backend'e gizle.
- ⬜ Aktif görev varken graph değişimini reddet; graph sürümünü Mission Manager,
  Route Server, GUI ve görselleştiricide atomik olarak değiştir.
- ⬜ Hareket başlatmadan ComputeRoute tabanlı “Rota Test” API'si ekle.

**Kabul:** Temiz bir saha graph'ı validate → atomik kaydet → canlı aktive et →
tüm dokuz A/B kombinasyonunda route üret akışı PASS; invalid graph hareketten önce reddedilir.

## Faz 5 — Flutter saha hazırlama ve rota öğretme ekranı ⬜

**Bağımlılık:** Faz 3 ve Faz 4 ROS API'leri.

- ⬜ GCS'ye “Saha Hazırlama / Rota Tanımlama” sayfası ekle.
- ⬜ Localization, robot durmuş bilgisi, aktif saha ve graph sürümünü göster.
- ⬜ START, junction, A1–A3 approach, B1–B3 approach ve q5 kayıt butonlarını bağla.
- ⬜ Segment başlat, ara nokta, bitir, iptal, tek/çift yön, hız ve hareket yönü
  işlemlerini backend servislerine bağla.
- ⬜ Node/edge listesi, silme, geri alma, doğrulama hataları ve route test sonucunu göster.
- 🟡 Map görüntüsü, robot pozu ve graph geometrisini canlı göster; piksel→map dönüşümünde
  OccupancyGrid resolution/origin/yaw bilgisini kullan.
  (`liftant_v2_bitirme`: OccupancyGridFrame + mapToPixel/pixelToMap, rosbridge `/map`
  throttle+isolate parse, `GcsMapView` occupancy arka planı, controller `onMapFrame`.
  Canlı rosbridge kanıtı bu oturumda yok — test: map_server + rosbridge açıkken GCS bağlan,
  Harita sekmesinde OccupancyGrid + robot pozu görünmeli; unit: `occupancy_grid_xform_test`.)
- ⬜ Kaydet ve Aktifleştir işlemlerini ayır; fiziksel hareket için ayrıca açık onay iste.
- ⬜ Bağlantı kopması, timeout ve tekrar tıklamada idempotent davranış sağla.

**Kabul:** Operatör RViz, terminal ve kaynak düzenleme olmadan bir saha graph'ı
oluşturup doğrulayabilir ve aktive edebilir.

## Faz 6 — Üretim Route yürütücüsü, RPP ve hız limitleri ⬜

**Bağımlılık:** Faz 1, Faz 2 ve Faz 4.

- ⬜ Mission Manager/route yürütücü tek kanonik akışla aktif saha graph'ını kullanacak;
  test graph veya isim fallback'i gerçek modda olmayacak.
- ⬜ Başlangıç ve hedef semantik node ID'leri üzerinden Route Server route'u hesaplanacak;
  serbest planner kestirme üretmeyecek.
- ⬜ `ComputeAndTrackRoute` kenar takibi ile FollowPath action sahipliği yarışsız ve
  iptal edilebilir biçimde çalışacak.
- ⬜ `smooth_corners:false` ve `path_density:0.05` üretim süreçlerinde doğrulanacak.
- ⬜ GeoJSON `abs_speed_limit` değerlerinin `/speed_limit` ve gerçek `/cmd_vel_raw`
  sınırına dönüştüğü hızlı/yavaş/geri edge'lerde ölçülecek.
- ⬜ Rota bitimi, cancel, hata ve e-stop sonrası hız limiti reseti ve son Twist sıfır olacak.
- ⬜ Gerçek araç RPP hız, ivme, lookahead ve collision horizon parametreleri düşük hızdan
  başlayarak saha verisiyle ayarlanacak.
- ⬜ İleri, geri, düz, 90° ve ara noktalı yay/polyline path'ler test edilecek.

**Kabul:** Robot yalnız tanımlanan polyline üzerinde hareket eder; yanlış edge/kestirme
yoktur; hız metadata'sı uygulanır; action cancel/hata güvenli biter.

## Faz 7 — Route Guard ve 10 cm koruması ⬜

**Bağımlılık:** Faz 6 aktif path yayını.

- ⬜ Üretim aktif path ve aktif edge için tek sahipli topic tanımla.
- ⬜ `route_guard`, `map → base_footprint` ile polyline'a en kısa mesafeyi 20–50 Hz hesaplasın.
- ⬜ `/route/cross_track_error`, tracking state ve active edge'i Mission Manager ve
  `RobotStatus` üzerinden Flutter'a aktar.
- ⬜ Eşiklere histerezis/süre uygula: normal <5 cm, warning 5–7 cm, kritik 7–10 cm,
  ihlal >10 cm.
- ⬜ Kritik bölgede hız azalt; >10 cm, stale TF/path ve NaN/Inf için güvenli politika uygula.
- ⬜ Edge bazında RMS, p95, maksimum ve ihlal süresini JSON/rosbag'e yaz.

**Kabul:** Kontrollü 2/5/8/>10 cm sapmalar doğru sınıflanır; fiziksel düz, köşe,
yay ve geri rotalarda şartname sınırı ölçülerek doğrulanır.

## Faz 8 — Approach ve gerçek hassas docking ⬜

**Bağımlılık:** Faz 2, Faz 4 ve gerçek perception çıktıları.

- ⬜ A/B graph node'larının gerçek palet noktası değil `*_APPROACH` olduğunu kesinleştir;
  `*_DOCK` istasyon geometrisini ayrı tut.
- ⬜ Nav2 action tamamen bittikten ve hız sahipliği bırakıldıktan sonra DockToStation başlat.
- ⬜ QR'ı approach başlangıcında beklenen istasyonla bir kez eşleştir ve latch et;
  QR görüşten çıkınca nominal docking'i iptal etme.
- ⬜ Gerçek kamera kalibrasyonu, şerit offset/yaw/confidence ve freshness sözleşmesini bağla.
- ⬜ Son mesafeyi doğrulanmış görsel/geometrik ölçümle hesapla; süre tabanlı başarı kullanma.
- ⬜ Yanlış QR, şerit/kamera kaybı, engel, e-stop, cancel ve timeout'ta iki cmd topic'i de sıfırla.
- ⬜ Ön/arka kamera seçimi ile pickup/dropoff yaklaşma yönünü doğrula.

**Kabul:** Gerçek kamera ve gerçek çizgiyle 20 denemenin en az 18'i ±7.5 cm ve
±5° içinde; bütün negatiflerde action güvenli FAIL ve son Twist sıfır.

## Faz 9 — Gerçek görev, q5, yük yönü, lift ve PLC ⬜

**Bağımlılık:** Faz 4, Faz 6 ve Faz 8.

- ⬜ PLC yarışma görevi tam olarak bir A1–A3 ve bir B1–B3 çifti olarak alınsın;
  çok duraklı GUI modu ek özellik olarak ayrı kalsın.
- ⬜ Mission Manager node adlarını string prefix ile değil graph rol/station metadata'sıyla doğrulasın.
- ⬜ Aktif route q5 node/edge olayına her ulaştığında dur, PLC'ye bildir, izin bekle ve devam et.
- ⬜ Pickup sonrası ve eve dönüş dahil rota q5'ten her geçişte aynı genel kapı davranışını uygula.
- ⬜ Gerçek LiftLoad action; limit switch, timeout ve donanım fault sonucuyla mission'a bağlansın.
- ⬜ `loaded` durumu edge yönü, path orientation, RPP reverse ve hız profiline gerçekten etki etsin;
  yük hareket yönünün tersinde kalsın.
- ⬜ Gerçek PLC Wi-Fi adaptörü heartbeat, tekrar bağlanma, görev, kapı ve tamamlandı
  sözleşmelerini mevcut ROS API arkasında uygulasın.
- ⬜ PLC ret/kayıp, lift/docking/navigation hatası, e-stop ve safety abort'ta tek action
  sahipliği ve güvenli sıfır doğrulansın.

**Kabul:** `bekleme → Ax approach/dock → yük al → q5 izin → Bx approach/dock →
bırak → gerekiyorsa q5 izin → bekleme → PLC tamamlandı` gerçek sistemde PASS.

## Faz 10 — Fiziksel güvenlik ve arıza matrisi ⬜

**Bağımlılık:** Faz 1, Faz 6 ve Faz 9.

- ⬜ Collision Monitor ön/arka poligonlarını gerçek footprint, hız, gecikme ve durma
  mesafesiyle yeniden boyutlandır.
- ⬜ Fiziksel e-stop'un ROS'tan bağımsız olarak motor enerjisini kestiğini doğrula;
  ROS durumu ve görev iptali bunun üzerine ek güvenlik olsun.
- ⬜ STM32 watchdog süresini fiziksel durma bütçesine göre belirle.
- ⬜ Scan/odom/TF/PLC/kamera/seri freshness ve fault durumlarını ortak diagnostic/status'a bağla.
- ⬜ İleri ve geri hareket sırasında engel: dur, bekle, aynı action/route üzerinde devam et.
- ⬜ Engel kalkması e-stop veya latched fault sonrası kendiliğinden harekete neden olmasın.

**Kabul:** Ölçülen fiziksel durma mesafesi güvenlik poligonunun içinde; arıza
matrisinin tüm satırları güvenli son durum ve sıfır Twist ile tamamlanır.

## Faz 11 — 60 dakikalık saha hazırlama provası ⬜

**Bağımlılık:** Faz 2–Faz 7.

- ⬜ Tek operatör akışını oluştur: donanım kontrol → SLAM → başlangıca dönüş → map kaydet
  → AMCL → node/segment öğret → validate → aktive et → hareketsiz rota testleri → kısa smoke.
- ⬜ Bütün işlemler Flutter üzerinden yapılabilsin; terminal yalnız tanı/yedek yol olsun.
- ⬜ Süreleri otomatik kaydet ve hangi adımın geciktiğini raporla.
- ⬜ Yanlış node, eksik edge, invalid graph, localization kaybı ve aktivasyon hatasında
  kullanıcıya düzeltilebilir, açık hata göster.

**Kabul:** Sıfırdan geçerli map + graph + kısa fiziksel rota smoke toplam ≤60 dakika;
aynı prosedür iki bağımsız provada tekrarlanır.

## Faz 12 — Uçtan uca yarışma kabulü ⬜

**Bağımlılık:** Faz 1–Faz 11.

- ⬜ `real_system.launch.py` gerçek encoder, YDLidar, perception, lift, safety, PLC ve
  rosbridge ile test-only sunucular olmadan başlasın.
- ⬜ Dokuz A/B kombinasyonunun tamamında graph erişilebilirliği hareketsiz test edilsin.
- ⬜ En az üç rastgele fiziksel görev arka arkaya tamamlanarak görevler arasında stale
  state, hız limiti veya action kalmadığı doğrulansın.
- ⬜ Rota sapması ≤10 cm; istasyon ±7.5 cm/±5°; engelde dur/devam; q5 izinleri;
  yük arkada; son Twist sıfır kabul edilsin.
- ⬜ Görev hedefi ≤30 dakika, zorunlu üst sınır <45 dakika olsun.
- ⬜ Her koşuda commit kimliği, saha verisi sürümü, parametre snapshot'ı, rosbag,
  route_guard JSON'u, Mission olayları, GCS kaydı ve fiziksel video saklansın.

**Kabul:** Aynı yazılım ve yalnız farklı `map + route.geojson` saha verisiyle iki ayrı
günde tam fiziksel görev PASS. Mock veya yalnız simülasyon bu fazı tamamlamaz.

## 6. Faz bağımlılık sırası

```text
Faz 0
  └─ Faz 1
      └─ Faz 2
          ├─ Faz 3 → Faz 4 → Faz 5
          └───────────────→ Faz 6 → Faz 7
                              └────→ Faz 8 → Faz 9 → Faz 10
                                             └────────────→ Faz 11 → Faz 12
```

## 7. Şimdi başlanacak ilk üç iş paketi

1. **Parametre ve route mimarisi kilidi:** `0.460 m` teker aralığını araç
   sözleşmesinde ve bütün tüketicilerde tekleştir; route yürütme sahibini ve
   speed-limit sahipliğini sabitle.
2. **Gerçek odometri/lokalizasyon kanıtı:** 10 m, iki yön 360°, gerçek SLAM ve AMCL
   ölçümlerini tamamla. Route Editor güvenilir map pozuna bağımlıdır.
3. **Route Editor MVP:** İki mevcut node arasında branch-safe segment oluşturup
   writable saha dizinine doğrulanmış GeoJSON yaz.

## 8. Bu planda özellikle tekrar edilmeyecek işler

- Gazebo temel dünya, sensör bridge ve RViz altyapısı yeniden yazılmayacak.
- Var olan base transport/protocol/odometry katmanı yeniden yazılmayacak; gerçek
  firmware'e göre düzeltilecek.
- Var olan SLAM, AMCL, Route Server, RPP, safety, docking ve mission paketleri yerine
  yeni paralel paketler kurulmayacak.
- `lane_tracking` başka ekibin sahipliğinde kalacak; ROS sözleşmesine adaptasyon ayrı
  entegrasyon katmanında yapılacak.
- Flutter içine RViz Nav2 Route Tool gömülmeyecek.
- Saha koordinatları Python/YAML kaynak koduna hard-code edilmeyecek.
- Ham manuel sürüş izi doğrudan referans rota yapılmayacak; anchor/ara nokta segmentleri
  kullanılacak.
