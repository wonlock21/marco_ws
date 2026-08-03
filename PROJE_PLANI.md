# MarCO Otonom Forklift — ROS 2, Lokalizasyon ve Navigasyon Proje Planı

> Kaynaklar: `marcorapor.pdf` (Proje Detay Raporu, 60 sf.) ve `2026_SRUY_TR_76gNu.pdf`
> (TEKNOFEST 2026 Sanayide Robotik Uygulamalar Şartnamesi, 23 sf.)
> Hedef: TEKNOFEST 2026 Finalleri — 30 Eylül / 4 Ekim 2026, Şanlıurfa
> Son ROS durum denetimi: **02.08.2026** — PDR iddiaları mevcut `src/` kodu ve
> eldeki test kanıtlarıyla karşılaştırıldı.

---

## 1. Amaç ve Kapsam

Fabrika içi lojistik senaryosunda paletli yükü otonom taşıyan bir forklift AGV'nin
**lokalizasyon** ve **navigasyon** yazılımını ROS 2 Humble üzerinde sıfırdan kurmak.

### Bizim sorumluluğumuz
Robot modeli ve TF ağacı · odometri tüketimi ve kalibrasyonu · sensör füzyonu (EKF) ·
SLAM haritalama · harita üzerinde lokalizasyon (AMCL) · rota ağı tanımlama, optimizasyon
ve takibi · engel algılama ve güvenli duruş · hassas istasyon yanaşmasının **kontrol**
tarafı.

### Başka ekiplerin sorumluluğu
STM32 gömülü yazılımı (motor PID, encoder, aktüatör, e-stop) · kamera ve görüntü işleme
ile şerit takibi · QR okuma · Flutter GUI · PLC haberleşmesi · PCB, güç, mekanik.

Bu bileşenlerle **arayüzleri biz tanımlayacağız** (bkz. §6.1); implementasyonları bize ait
değil. Geliştirme sırasında her biri için sahte (mock) yayıncı kullanılacak, böylece
ilgili ekip gecikse bile bizim tarafımız ilerleyebilir.

### Takvim notu
Hareket-Kabiliyet Videosu teslimi **11.08.2026 17:00**. Videoda bizim kapsamımıza giren
tek madde **haritalama gösterimi**. Diğer maddeler (A→B hareket, yük alma-bırakma, çizgi
takibi, e-stop, GUI) diğer ekiplerin işi. Dolayısıyla bizim video kritik yolumuz:
gerçek araç üzerinde **YDLidar Tmini Pro + gerçek encoder odometrisi** ile çalışan bir
SLAM demosu.

---

## 2. Şartnamenin Dayattığı Sert Kısıtlar

Bunlar tasarımı doğrudan belirleyen, pazarlık payı olmayan gereksinimler:

| # | Gereksinim | Puan Etkisi |
|---|---|---|
| 1 | 2D lazer tarayıcı ile haritalama | +30 |
| 2 | Arayüz üzerinden rota tanımlama | +20 |
| 3 | **Tanımlı rotalar üzerinde** hareket, rotadan sapma ≤ **10 cm** | -5 (max 2 kez) |
| 4 | Alma/bırakma/bekleme alanlarına **±7.5 cm** konum, **±5°** yön toleransı | -5 (max 2 kez) |
| 5 | Rota optimizasyonu **robot tarafından** hesaplanacak | +20 (rota hazırlama) |
| 6 | Engelde **güvenli duruş** — kaçınma beklenmiyor; engel kalkınca devam | +10 |
| 7 | İstasyona 1.5 m kala QR + renkli şerit ile hassas yanaşma | +10 / +10 |
| 8 | PLC ile Wi-Fi haberleşme, q5 noktasında kapı geçiş izni | +20 / +20 |
| 9 | Yük, **hareket yönünün tersinde** taşınacak | görev şartı |
| 10 | Otomatik şarj kabiliyeti | +5 (opsiyonel) |

**Zaman baskısı:** Haritalama + rota tanımlama için sahada yalnızca **60 dakika**.
Görev süresi hedefi **30 dk**, üst limit **45 dk**. Bu ikisi tooling kalitesini
doğrudan puana çeviriyor — harita ve rota tanımlama akışı hızlı ve tekrarlanabilir olmalı.

**Senaryo akışı:** başlangıç → PLC bağlantısı → rastgele 1 alma + 1 bırakma noktası →
alma noktasına git → QR doğrula → şerit takibi → yükü al → q5 kapı noktası → PLC'den izin →
bırakma noktası → QR + şerit → bırak → bekleme noktasına dön → PLC'ye bildir.

---

## 3. Donanım ve Ortam Envanteri

### Araç (rapordan)

| Özellik | Değer |
|---|---|
| Boyut | 1536 × 650 × 550 mm |
| Yerden yükseklik / lift stroku | 30 mm / 100 mm |
| Sürüş | Diferansiyel: 2 tahrik tekeri + 4 sarhoş teker, sıfır dönüş yarıçapı |
| Tekerlek çapı | 200 mm (r = 0.1 m, çevre = 0.6283 m) |
| Tahrik motoru | 2× Linix 112ZY24, 24 V/140 RPM nominal, **12 V'ta 80 RPM** |
| Encoder | 2× Fenac OVW6-036-2HC, 360 PPR artımlı A/B |
| Motor sürücü | 3× BTS7960B (2 tahrik + 1 lift) |
| Maks. yük | 5 kg palet |

### Hesaplanmış türev değerler

- **Gerçek maksimum hız:** 80 RPM × 0.6283 m = **0.838 m/s**
  Raporun belirttiği 1.46 m/s, 24 V / 140 RPM değeridir; 12 V çalışmada ulaşılamaz.
  Nav2 `max_vel_x` bu değere göre değil, gerçek tavana göre ayarlanacak.
- **Odometri çözünürlüğü:** 360 PPR × 4 (dördül kod çözme) = 1440 tick/tur
  → 0.6283 / 1440 = **0.436 mm/tick**. Yeterli.
- **Ayak izi yarıçapları:** çevrel 0.834 m, iç teğet 0.325 m. Dairesel ayak izi
  varsayımı bu araçta kullanılamaz; poligon zorunlu.

### Hesaplama ve algı

- **Orange Pi 5 Plus** — RK3588, 8 çekirdek aarch64, 7.7 GB RAM, 48 GB boş disk
- **Ubuntu 22.04.5 / ROS 2 Humble** (331 paket), Nav2 1.1.20, slam_toolbox, nav2_route kurulu
- **2× STM32 Nucleo** — motor PID, encoder, aktüatör, limit switch, e-stop (C/C++, UART)
- **YDLidar Tmini Pro** — 2D LiDAR; Orange Pi üzerinde masa testinde çalıştı
  (`/scan` ≈9.96 Hz, 430 nokta). Rapordaki RPLIDAR A3 bilgisi güncel değil.
- **2× IMX219** — ön/arka MIPI CSI kamera (henüz bağlı değil)
- **GM67** — USB QR okuyucu; gerçek ROS düğümü henüz yok
- **IMU — YOK** (bkz. §4.2)

---

## 4. Raporda Tespit Edilen Boşluklar ve Alınan Kararlar

### 4.1 `map → odom` katmanı tanımlanmamış — KRİTİK

Raporda AMCL veya eşdeğeri bir lokalizasyon katmanı hiç geçmiyor. SLAM Toolbox ile harita
çıkarılıyor, Nav2 ile navigasyon yapılıyor, ancak robotun kayıtlı harita üzerindeki
konumunu düzelten katman yok. Bu haliyle robot yalnızca odometriye güvenir ve birkaç
metrede kayarak hem 10 cm rota toleransını hem de ±7.5 cm istasyon toleransını kaybeder.

**Karar:** `nav2_amcl` ile parçacık filtresi kullanılacak. Yedek olarak slam_toolbox'ın
`localization` modu değerlendirilecek (harita güncelleme esnekliği verir).

### 4.2 IMU yok

Konum tahmini tamamen encoder'a dayandırılmış. 4 sarhoş tekerli, 1.5 m uzunluğunda bir
araçta yerinde dönüş sırasında tekerlek kayması kaçınılmaz; sadece encoder'dan türetilen
yaw açısı hızla birikimli hata yapar. Bu doğrudan ±5° yön toleransını tehdit eder.

**Karar (kullanıcı onayı: opsiyonel):** Yazılım mimarisi IMU'lu ve IMU'suz iki
konfigürasyonu da destekleyecek şekilde kurulacak. EKF konfigürasyonunda IMU girdisi
bir launch argümanı ile açılıp kapanabilir olacak. Donanım eklenirse tek satır değişiklikle
devreye girer. **Öneri: BNO055 veya ICM-20948 eklenmesi.**

### 4.3 "Kalman Filtresi" elle yazılmak isteniyor

Rapor, konum tahmini için Python'da özel bir Kalman filtresi öngörüyor.

**Karar:** `robot_localization` paketinin `ekf_node`'u kullanılacak. Test edilmiş,
TF'i doğru yayınlıyor, kovaryans yönetimi hazır. Elle yazmak zaman kaybı ve hata kaynağı.

### 4.4 Serbest planlama ↔ tanımlı rota çelişkisi — KRİTİK

Rapor, Nav2'nin harita üzerinde hedefe serbestçe rota planlamasını anlatıyor. Şartname ise
**önceden tanımlanmış rotalar** üzerinde, ≤10 cm sapmayla hareket ve **robot tarafından
hesaplanan rota optimizasyonu** istiyor. NavFn/Smac gibi serbest planlayıcılar bu
gereksinimi karşılamaz — koridorun ortasından geçen kendi yolunu üretirler.

**Karar:** `nav2_route` paketi kullanılacak (kurulu, sürüm 1.1.20). Bu paket tam olarak
bu iş için var:

- Rota ağı **GeoJSON** graf dosyası olarak tanımlanır (düğüm + kenar)
- `DistanceScorer` / `TimeScorer` / `PenaltyScorer` ile **kenar maliyetlendirme ve
  optimizasyon** → şartname madde 5 karşılanır
- `AdjustSpeedLimit` ile kenar bazlı hız limiti → istasyon yaklaşımlarında yavaşlama
- `TriggerEvent` ile düğüm/kenar olaylarında servis çağrısı → **QR okuma, PLC kapı
  el sıkışması ve docking tetikleme buraya bağlanacak**

Üretilen rota `controller_server`'a `FollowPath` ile verilir; global planlayıcı devre dışı
ya da yalnızca düğümler arası kısa bağlantılar için kullanılır.

### 4.5 Engel davranışı: durmak, kaçınmak değil

Şartname engelden kaçınmayı **beklemiyor**; güvenli duruş ve engel kalkınca devam istiyor.
Nav2'nin varsayılan davranış ağacı ise engelde yeniden planlar ve etrafından dolaşır —
bu da rotadan >10 cm sapma cezası demek.

**Karar:** Dinamik engeller global costmap'e işlenmeyecek. `nav2_collision_monitor` ile
yavaşlama ve durma bölgeleri tanımlanacak; davranış ağacı engelde **bekleyecek**,
yeniden planlamayacak. Engel kalkınca aynı rotadan devam edilecek.

### 4.6 Yükün ters yönde taşınması

Yük alındıktan sonra çatallar arkada kalacak şekilde ilerlenecek. Diferansiyel sürüşte
iki seçenek var: yerinde 180° dönmek veya geri viteste sürmek.

**Karar:** Kontrolcü `allow_reversing` ile geri sürüşe izin verecek; arka kamera bu yüzden
var. Rota grafında kenarlara yön metadata'sı eklenerek hangi kenarın ileri hangisinin geri
kat edileceği belirtilecek.

### 4.7 Hız parametreleri

Şartnamenin 10 cm rota toleransı ve ±7.5 cm istasyon toleransı, yüksek hızla uyumsuz.

**Karar — başlangıç değerleri (saha testinde kalibre edilecek):**

| Faz | Hedef hız |
|---|---|
| Transit (yüksüz) | 0.50 m/s |
| Transit (yüklü) | 0.35 m/s |
| İstasyon yaklaşımı (son 1.5 m) | 0.15 m/s |
| Docking / son hizalama | 0.05 m/s |
| Açısal (maks.) | 0.6 rad/s |

### 4.8 Encoder montaj yeri belirsiz

Rapor bir yerde "tekerlek millerine", başka bir yerde "tahrik motorlarının miline" diyor.
Redüktör öncesi/sonrası farkı tick→metre katsayısını doğrudan değiştirir.

**Aksiyon:** Mekanik/elektronik ekibinden netleştirilecek. §7'deki açık sorular listesinde.

### 4.9 URDF, TF ağacı, simülasyon hiç ele alınmamış

Raporda URDF, TF veya Gazebo geçmiyor. Bunlar Nav2 ve SLAM'in ön koşulu.

**Karar:** Faz 1 ve 2'de sıfırdan kurulacak.

### 4.10 Simülatör kararı ve Faz 2A temel uygulaması — 02.08.2026

`ros-humble-gazebo-ros-pkgs` aarch64 için paketlenmemiş. Ayrıca bu kartta OpenGL
`llvmpipe` üzerinden, yani tamamen yazılımsal çalışıyor (panfrost yüklü değil).

**Karar:** Gazebo/`ros_gz` simülasyonu kullanıcının x86 bilgisayarındaki **WSL2 + Ubuntu
22.04** üzerinde çalıştırılacak; Orange Pi yalnızca gerçek-araç çalışma zamanı ve hafif
donanım testleri için kullanılacak. `marco_simulation`, Gazebo Fortress dünyası,
diferansiyel sürüş, 2D LiDAR, ön kamera, `ros_gz_bridge`, RViz yapılandırması ve görsel
otomatik sürüş testiyle uygulandı. WSLg'nin Ogre2/D3D12 `copyTo` hatası nedeniyle Gazebo
sunucusu ve isteğe bağlı GUI yazılım renderer ile, RViz ise normal OpenGL ile çalıştırılıyor.

### 4.11 PDR ROS yazılımı eksik analizi — 02.08.2026

Bu tablo raporun özellikle §4.3.2 (algoritmalar), §4.3.3 (yazılım), §4.4 (arayüzler)
ve §6.6 (yazılım testleri) bölümleri ile mevcut kaynak kodun karşılaştırmasıdır.

**Durum anahtarı:** ✅ = gerçek entegrasyon ve kabul kanıtı var · 🟡 = yalnız kaynak,
arayüz, mock veya masa borusu var · ⬜ = gerçek uygulama/entegrasyon yok.

| PDR'deki ROS işlevi | Bugün doğrulanan durum | Tamamlanması gereken iş / kabul kanıtı |
|---|---|---|
| Üst seviye görev durum makinesi | 🟡 Durum adları ve mock PLC akışı var | `mission_manager` gerçek Nav2 rota action'larını, docking'i, lift'i ve dönüş rotasını çağırmalı; action sonucu/iptal/zaman aşımı ile durum değiştirmeli. `simulate_steps:=false` şu an hiçbir hareket çağırmadan adımları geçiyor. |
| Güvenli hata ve e-stop yönetimi | 🟡 STM32 bayrakları loglanıyor; e-stop/manual Bool yayınları var | Haberleşme kaybı, encoder, aşırı akım, watchdog, fork, LiDAR/kamera/TF/AMCL eskimesi tek hata yöneticisinde toplanmalı; aktif Nav2/docking/lift iptal edilip sıfır hız doğrulanmalı. E-stop sırasında görev iş parçacığının ilerlemesi engellenmeli. |
| SLAM haritalama | 🟡 Tmini Pro + SLAM Toolbox borusu ve harita kaydı var | Hareketli gerçek araçta encoder + LiDAR birlikte kullanılarak parkur haritası çıkarılmalı; 60 dakikalık kurulum prosedürü ve tekrar edilebilir harita kanıtı kaydedilmeli. Sabit LiDAR + sahte odom gerçek kabul değildir. |
| Kayıtlı haritada lokalizasyon | 🟡 AMCL/EKF borusu var | Gerçek araçta başlangıç pozu, yeniden lokalizasyon ve 5 dk doğruluk testi (<5 cm, <3°) yapılmalı; lokalizasyon geçerliliği görev yöneticisine bağlanmalı. |
| Rota tanımlama ve optimizasyon | 🟡 `nav2_route`, demo GeoJSON ve rota hesaplama var | Gerçek parkur grafı ile GUI/RViz rota-nokta editörü yapılmalı; alma/bırakma/bekleme/QR/q5/şarj düğümleri saklanmalı ve PLC kimlikleriyle eşlenmeli. |
| Tanımlı rotayı takip | 🟡 Yol hesaplanıyor, fiziksel takip yok | Gerçek araçta çapraz rota hatası ölçülüp ≤10 cm tutulmalı. `/robot_status.cross_track_error` gerçek değerden beslenmeli ve limit aşımı güvenli davranış üretmeli. |
| Yüklü/yüksüz ve ters yönde sürüş | ⬜ DWB yapılandırması yalnız ileri sürüyor; yük durumu rota kontrolüne bağlı değil | Yüklü hız profili, geri sürüşe uygun kontrolcü (`RPP allow_reversing` veya doğrulanmış eşdeğer), ön/arka algı seçimi ve graf yön metadata'sı uygulanmalı. |
| Kenar hız limiti ve rota olayları | 🟡 GeoJSON'da hız metadata'sı var, `TriggerEvent` yok | Mevcut BT `ComputeRoute + FollowPath` olduğu için `AdjustSpeedLimit` takip sırasında uygulanmıyor. `ComputeAndTrackRoute`/eşdeğer akışa geçilmeli; QR, docking ve q5 PLC olayları gerçek callback/action'lara bağlanmalı. |
| Engel algılama, durma ve devam | 🟡 Collision Monitor masa testi var | Hareketli araçta durma mesafesi ve aynı rotadan devam kanıtlanmalı. Geri sürüş için arka stop alanı eklenmeli; mevcut stop poligonu aracın -x tarafının tamamını kapsamıyor. Engel durumu görev/GUI'ye bağlanmalı. |
| Gerçek şerit algılama | 🟡 Ayrı `lane_tracking` prototipi var ama sözleşmeye uymuyor | Kamera düğümü piksel `Float32` yerine kalibre edilmiş `LaneOffset` (metre, açı, güven, kamera) yayınlamalı. Mevcut doğrudan `/pwm_left/right` yolu güvenlik zincirini baypas etmemeli; `/cmd_vel_dock` mimarisine bağlanmalı. Taze kurulumdaki `trackerfinal` entry-point'i de kaynakta yok. |
| QR okuma ve QR pozu | ⬜ Yalnız mock `QrDetection` var | GM67 veri düğümü, hedef kimliği doğrulama ve kamera/OpenCV ile QR pozu üretimi yazılmalı; ön/arka kamera seçimi ve yanlış/eskimiş QR hata akışı test edilmeli. |
| Hassas yanaşma | 🟡 Action server mock veriyle çalışıyor | Gerçek kamera topic'leri bağlanmalı. Boylamsal mesafe/son durma ölçümü eklenmeli; mevcut kontrol başarıyı yalnız yanal sapma ve açıyla belirliyor. E-stop/engel sonucu ve 20 denemede ≥18 başarı saha kanıtı gerekli. |
| Yük alma/bırakma ve lift | 🟡 UART protokolünde fork komutu/geri bildirimi var | ROS service/action, `base_driver` komut yolu, limit-switch/fork hata geri bildirimi ve görev durumları yazılmalı. Lift yalnız doğru QR+docking sonrası çalışmalı; yüklü/yüksüz durum doğrulanmalı. |
| PLC ve kapı geçişi | 🟡 ROS servis sözleşmeleri + mock PLC var | Yarışma Wi-Fi/PLC protokol köprüsü, bağlantı yeniden kurma, zaman aşımı/ret davranışı, q5'te fiziksel bekleme ve görev tamamlandı bildirimi gerçek PLC ile test edilmeli. |
| PC/mobil GUI entegrasyonu | 🟡 `RobotStatus` mesajı var, ağ köprüsü yok | `rosbridge`/seçilecek taşıma katmanı kurulmalı. Harita/poz/rota, bağlantılar, batarya-akım-voltaj-sıcaklık, QR, engel, hata ve olay günlüğü canlı veriden beslenmeli. Mevcut `mission_manager` pozunu sıfır, rota hatasını 0, lokalizasyonu sürekli geçerli yayımlıyor. |
| Manuel kontrol ve fiziksel mod kilidi | 🟡 `twist_mux` girişi/kilidi var | GUI joystick ve lift komutları gerçek zincire bağlanmalı; fiziksel anahtarın “manuelde hangi ROS komutları geçer?” semantiği STM32 ile netleştirilip test edilmeli. Otomatik/docking komutları manuel modda ilerlememeli. |
| Batarya ve otonom şarj | 🟡 `/base/battery` telemetrisi var | Görev yöneticisi batarya eşiğini tüketmeli; görev kabul/bitirme politikası, şarj düğümüne rota, docking, fiziksel temas ve şarj başladı/bitti protokolü uygulanmalı. Yalnız Nav2 BT eklentisinin listede bulunması işlev değildir. |
| STM32 gerçek entegrasyonu | 🟡 Protokol, seri transport ve sahte STM32 testleri var | Gerçek iki STM32 topolojisi/portları, firmware mesaj uyumu, motor PID, encoder yönü/ölçeği, lift ve tüm hata bayrakları donanımda doğrulanmalı; seri bağlantı kopması/yeniden bağlanma ve topic freshness tanıları eklenmeli. |
| Gazebo/WSL2 simülasyonu | 🟡 Faz 2A temel kabul tamam (02.08) | Fortress dünya, diferansiyel sürüş, LiDAR/kamera, `ros_gz_bridge`, tek launch, RViz ve tekrar çalıştırılabilir otomatik sürüş testi doğrulandı. Faz 2B için yarışma parkurunun tam 3 alma + 3 bırakma istasyonu, koridorları, kapısı, paletleri ve görev senaryosu uygulanmalı. |
| Test ve kabul kanıtı | 🟡 İşlevsel otomatik testler ağırlıkla `marco_base` içinde | Mission, docking, safety, route ve entegrasyon için unit/launch testleri eklenmeli. PDR §6.6'daki gerçek araç iddiaları rosbag, tarihli metrik ve saha test sonucu olmadan tamamlandı sayılmamalı. |

**Tamamlandı sayma kuralı:** Bir PDR maddesi ancak (1) gerçek ROS bağlantısı, (2) hata
yolu, (3) tekrar edilebilir test komutu ve (4) tarihli çıktı/rosbag/metrik kanıtı birlikte
varsa ✅ yapılacaktır. Mock ile başarılı bir action veya topic'in görünmesi yalnız 🟡'dır.

---

## 5. Hedef Mimari

### 5.1 TF ağacı

```
map
 └── odom                    (AMCL yayınlar)
      └── base_footprint     (EKF yayınlar)
           └── base_link
                ├── laser_link          (YDLidar Tmini Pro)
                ├── imu_link            (opsiyonel)
                ├── camera_front_link
                ├── camera_rear_link
                ├── left_wheel_link
                ├── right_wheel_link
                ├── caster_*_link  ×4
                └── fork_link           (prizmatik, lift eksenі)
```

### 5.2 Lokalizasyon zinciri

```
STM32 (encoder tick)
   │ UART
   ▼
marco_base_driver ──► /odom (nav_msgs/Odometry) + /joint_states
                          │
(opsiyonel) /imu/data ────┤
                          ▼
              robot_localization/ekf_node
                          │  odom → base_footprint TF
                          ▼
/scan (YDLidar Tmini Pro) ──► nav2_amcl ──► map → odom TF
```

### 5.3 Navigasyon zinciri

```
Görev yöneticisi (durum makinesi)
        │ ComputeRoute / ComputeAndTrackRoute
        ▼
   nav2_route  ◄── rota grafı (GeoJSON)
        │ nav_msgs/Path
        ▼
  controller_server (hedef: Regulated Pure Pursuit; mevcut: DWB)
        │ /cmd_vel_raw
        ▼
 nav2_collision_monitor
        │ /cmd_vel_safe
        ▼
     twist_mux  ◄── /cmd_vel_manual (GUI/teleop)
        │        ◄── /cmd_vel_dock   (hassas yanaşma)
        │        ◄── /base/estop     (kilit, en yüksek öncelik)
        │        ◄── /base/manual_mode (kilit)
        ▼
 marco_base_driver ──► STM32
```

Kontrolcü seçimi: **Regulated Pure Pursuit**. MPPI daha iyi rota takibi verir ama
RK3588'de CPU maliyeti yüksek; RPP hem ucuz hem de rota ağı takibi için yeterli.
Sapma toleransı tutturulamazsa MPPI'ye geçiş değerlendirilecek. **Bu hedef durumdur:**
mevcut `nav2_params.yaml` hâlâ yalnız ileri hız üreten DWB kullanıyor; RPP ve ters sürüş
henüz uygulanıp doğrulanmadı.

### 5.4 Hassas yanaşma (docking)

Nav2 tek başına ±7.5 cm / ±5° veremez. QR noktasında (istasyona 1.5 m kala) `nav2_route`
bir `TriggerEvent` ile docking action server'ı çağıracak.

Docking döngüsü: GM67'den QR kimliği doğrula → ön/arka kameradan renkli şeridi çıkar
(HSV eşikleme + ağırlık merkezi) → şerit merkezinin görüntü merkezinden sapmasını ve
şeridin açısını hesapla → açısal ve doğrusal hızı kapalı çevrimde sür → hedef toleransa
girince dur → sonucu görev yöneticisine bildir.

Hız komutu `/cmd_vel_dock` üzerinden `twist_mux`'a Nav2'den yüksek öncelikle girer.

---

## 6. ROS 2 Paket Yapısı

`◆` = bizim · `◇` = arayüzünü tanımlayıp mock'layacağımız, implementasyonu başkasında

```
~/marco_ws/src/
├── ◆ marco_msgs/          # özel mesaj, servis, action tanımları
├── ◆ marco_description/   # URDF/xacro, meshler, sensör çerçeveleri, sim eklentileri
├── ◆ marco_bringup/       # üst seviye launch, parametre kompozisyonu
├── ◆ marco_base/          # STM32 UART köprüsü: /cmd_vel → tick, tick → /odom
├── ◆ marco_localization/  # ekf.yaml, amcl.yaml, odometri kalibrasyon araçları
├── ◆ marco_navigation/    # nav2 parametreleri, davranış ağaçları, rota grafı, haritalar
├── ◆ marco_docking/       # hassas yanaşma kontrolcüsü (action server)
├── ◆ marco_safety/        # twist_mux, collision monitor, e-stop mantığı
├── ◆ marco_simulation/    # Fortress dünya, eklentiler, köprü, RViz ve test launch'ı
├── ◇ marco_perception/    # şerit sapması + QR pozu — mock yayıncı bizden, gerçeği onlardan
└── ◇ marco_mission/       # görev durum makinesi, PLC arayüzü — mock bizden
```

Kaynak ağacında ayrıca görüntü ekibinden alınmış `lane_tracking` paketi bulunuyor. Paket
şu hâliyle bu mimarinin parçası değildir: topic tipleri sözleşmeyle uyuşmuyor, doğrudan
PWM üretip güvenlik zincirini atlıyor ve temiz kaynak kurulumunda entry-point'i eksik.

### 6.1 Ekipler arası arayüz sözleşmesi

Bu arayüzler erken sabitlenmeli; her biri için `marco_msgs` altında tanım ve
`marco_*/mock/` altında sahte yayıncı yazılacak.

| Arayüz | Yön | Tip | Durum / sağlayan |
|---|---|---|---|
| `/cmd_vel` | ROS → STM32 | `geometry_msgs/Twist` | `marco_base` yolu var; gerçek firmware testi bekliyor |
| `/odom` + encoder tick | STM32 → ROS | `nav_msgs/Odometry` | Protokol/sahte donanım var; gerçek kabul bekliyor |
| `/joint_states` | STM32 → ROS | `sensor_msgs/JointState` | Teker/fork yayını var; gerçek kabul bekliyor |
| `/scan` | LiDAR → ROS | `sensor_msgs/LaserScan` | YDLidar sürücüsü masa testinde çalıştı |
| `/imu/data` | IMU → ROS | `sensor_msgs/Imu` | Opsiyonel boru var; gerçek sürücü/donanım yok |
| `/lane/offset` | görüntü → docking | `marco_msgs/LaneOffset` | Mock var; gerçek `lane_tracking` bu tipe uymuyor |
| `/qr/detection` | GM67/kamera → görev+docking | `marco_msgs/QrDetection` | Yalnız mock var |
| `/base/estop` | STM32 → ROS | `std_msgs/Bool` | Sürücü yayımlıyor; fiziksel kabul bekliyor |
| `/base/manual_mode` | STM32 → ROS | `std_msgs/Bool` | Sürücü yayımlıyor; uçtan uca mod semantiği bekliyor |
| `/base/battery` | STM32 → ROS | `sensor_msgs/BatteryState` | Sürücü yayımlıyor; görev/GUI tüketmiyor |
| lift komutu + durum/hata | ROS ↔ STM32 | yeni service/action + status | ⬜ ROS API ve sürücü bağlantısı yok |
| ayrıntılı taban hatası/bağlantı sağlığı | STM32/sensörler → görev+GUI | `diagnostic_msgs` veya özel msg | ⬜ tanımlanmadı |
| görev hedefi/kapı/tamamlandı | PLC ↔ görev | `AssignTask`, `GatePermission`, `TaskComplete` | Mock servisler var; ağ protokol köprüsü yok |
| `/robot_status` | ROS → GUI | `marco_msgs/RobotStatus` | Mesaj var; alanların çoğu canlı kaynaklara bağlı değil |
| `/cmd_vel_manual` + manuel lift | GUI → güvenlik/STM32 | `Twist` + lift action | Mux girişi var; GUI köprüsü ve lift yolu yok |

**STM32 UART protokol taslağı Faz 3'te yazıldı ve sahte STM32 ile test edildi.** Kalan iş,
elektronik ekibinin gerçek iki STM32 firmware'ini bu sözleşmeye uydurması ve mesaj
formatı, CRC, tick semantiği, watchdog, lift ve hata bayraklarının fiziksel donanımda
uçtan uca kabul edilmesidir.

---

## 7. Karara Bağlanacak Açık Konular

| Konu | Kime sorulacak | Neden önemli | Durum (02.08) |
|---|---|---|---|
| Simülatör çalışma yeri | Kullanıcı | Faz 2 | ✅ WSL2 + Ubuntu 22.04 üzerinde Fortress/ros_gz uygulandı ve test edildi |
| Encoder redüktör öncesi mi sonrası mı? | Elektronik ekibi | Odometri katsayısı | ⬜ açık |
| Gerçek iki STM32'nin görev/port topolojisi | Elektronik ekibi | Sürücü, lift ve hata yönetimi | ⬜ açık |
| Tekerlek ekseni arası mesafe (wheel separation) | Mekanik ekibi | Açısal odometri | ✅ CAD ≈0.460 m; sahada kalibre edilecek |
| `base_link` orijini nerede? | Mekanik ekibi | Ayak izi ve TF | ✅ tahrik aksı ortası |
| Tmini Pro'nun tam montaj pozu/yüksekliği | Mekanik ekibi | `laser_link` TF | 🟡 masa TF'i tahmini; mm saha ölçümü yok |
| IMX219/USB yedek kamera ve gerçek topic sözleşmesi | Görüntü ekibi | Şerit/QR/docking | ⬜ açık |
| PLC haberleşme protokolü | TEKNOFEST/PLC ekibi | Faz 10 | ⬜ protokol bekleniyor; yalnız mock servis var |
| Şarj istasyonu teknik detayları | TEKNOFEST | Opsiyonel +5 puan | ⬜ açık |
| IMU eklenecek mi, hangi model? | Takım kararı | Yön doğruluğu | 🟡 yazılım yolu hazır; model/sürücü yok |
| GUI Wi-Fi köprüsü ve veri sözleşmesi | Yazılım | Flutter canlı telemetri/kontrol | ⬜ eklenmedi |
| Fiziksel manuel modda ROS komut yetkisi | Elektronik+GUI+ROS | Güvenlik kilidi | ⬜ semantik netleştirilecek |
| Araç mekanik montaj / entegrasyon | Mekanik+elektronik | Faz 11 | ⬜ araç Orange Pi'ye bağlı değil |

---

## 8. Yol Haritası

Her fazın sonunda somut bir kabul kriteri var; kriter sağlanmadan sonraki faza geçilmez.
Bu, raporun §7.4'te "önce her modülü tek başına dene, sonra entegre et" şeklinde
kaydettiği kendi tecrübenizle de uyumlu.

**Durum anahtarı:** ✅ = fazın kendi kabul kriteri kanıtlandı · 🟡 = kaynak/arayüz/mock
veya masa borusu var fakat gerçek entegrasyon/kabul eksik · ⬜ = uygulanmadı. Bu tarihten
itibaren yalnız topic'in görünmesi ya da mock action'ın başarılı olması ✅ sayılmaz.
Detaylı durum özeti: `AGENT_REFERANS.md`.

### Faz 0 — Ortam hazırlığı ✅ (26.07)
- Eksik paketlerin kurulumu: `robot_localization`, `xacro`, `joint_state_publisher`,
  `twist_mux`, `cv_bridge`, `imu_tools`, `tf_transformations`; Tmini Pro sürücüsü ayrı YDLidar overlay'inde
- `marco_ws` iskeleti, 11 paketin oluşturulması, `colcon build` temiz geçmeli
- **Kabul:** boş workspace hatasız derleniyor, `ros2 pkg list | grep marco` 11 paket veriyor

### Faz 1 — Robot modeli ve TF ✅ (26.07)
- `marco_description`: xacro ile parametrik URDF, gerçek ölçüler (1536×650×550)
- Tüm sensör çerçeveleri, prizmatik fork eklemi
- `robot_state_publisher` + `joint_state_publisher` launch
- **Kabul:** RViz2'de model doğru görünüyor, `ros2 run tf2_tools view_frames` ağacı kopuksuz
- CAD ile `wheel_separation`≈0.460 m ve ayak izi poligonu güncellendi; ileri = gövde (+x)

### Faz 2 — Simülasyon ortamı 🟡 TEMEL KABUL TAMAM, TAM PARKUR EKSİK

#### Faz 2A — Temel Gazebo/RViz ve sensör kabulü ✅ (02.08.2026)

- ✅ Hafif test dünyası: zemin, dört duvar, LiDAR engelleri ve renkli kamera hedefleri
- ✅ Gazebo Fortress diferansiyel sürüş, 2D LiDAR ve ön kamera eklentileri
- ✅ `/clock`, `/cmd_vel`, `/odom`, `/scan`, `/camera/image_raw`,
  `/camera/camera_info`, `/tf`, `/tf_static` ve `/robot_description` doğrulandı
- ✅ Teknik test: odom ≈43.7 Hz, LiDAR ≈9.0 Hz (430/430 geçerli ölçüm), kamera
  ≈13.1 Hz ve 640×480 RGB8/921600 bayt
- ✅ 5 saniyelik manuel sürüşte odometri yaklaşık (0.000, 0.000) → (1.037, 0.599);
  otomatik görsel rotada (0.000, 0.000) → (1.413, 0.649), son Twist sıfır
- ✅ TF zinciri `odom → base_footprint → base_link → laser_link/camera_front_link`;
  `odom → base_footprint` için tek yayıncı doğrulandı
- ✅ Gazebo GUI yazılım renderer ile, RViz normal OpenGL 4.2 ile açıldı; RobotModel,
  TF, LaserScan, Odometry ve kamera display'leri yapılandırmadan yüklendi

#### Faz 2B — Şartnameye uygun yarışma parkuru ve senaryo ⬜

- ⬜ Şartnamedeki koridor geometrisini ve çalışma alanını dünyaya ekle
- ⬜ Üç alma ve üç bırakma istasyonunu doğru konum/ölçülerle modelle
- ⬜ Kapı, paletler ve istasyonların LiDAR/kamera tarafından algılanabilir görsellerini
  ve çarpışma geometrilerini ekle
- ⬜ Alma → taşıma → bırakma akışını sınayan tekrar çalıştırılabilir görev senaryosu ekle
- ⬜ Parkurda sensör görünürlüğünü, çarpışmasız sürüşü ve istasyon erişimini kanıtla
- **Faz 2'nin tamamı**, Faz 2B maddeleri gerçek çalıştırma kanıtıyla doğrulanmadan ✅
  sayılmayacak.

### Faz 3 — Odometri ve EKF 🟡 sahte donanım/boru (02.08.2026)
- ✅ `marco_base`: STM32 UART köprüsü. Sürücü yalnızca soyut bir `Transport` arayüzüne
  bağlı; gerçek seri port ile yazılım taklidi arasındaki geçiş tek parametre
  (`sahte:=true`). Böylece navigasyon geliştirmesi firmware'i beklemiyor.
- ✅ Sahte STM32 yalnızca "çalışıyormuş gibi" yapmıyor: motor birinci mertebe tepkisi,
  200 ms watchdog, kesirli tick birikimi ve **bilinçli hata enjeksiyonu** içeriyor
  (tekerlek ölçek hatası, teker arası mesafe hatası, kayma). Ayrıca gerçek konumu
  yayınlıyor, böylece odometri hatası sayısal olarak ölçülebiliyor.
- ✅ Kalibrasyon aracı `odometry_check.py`. Manevralar kapalı çevrim; ölçtüğü şey
  odometrinin inandığı hareket ile gerçekleşen hareket arasındaki fark.
  İki yönlü kare testinin tanı kuralı **tahminle değil, bilinen hata enjekte edilip
  ölçülerek** belirlendi (ilk yazdığım kural tersti). 2 cm'lik teker arası mesafe
  hatası enjekte edildiğinde araç düzeltmeyi 0.06 mm yaklaşıklıkla buldu.
- ✅ `robot_localization` EKF konfigürasyonu, IMU girdisi launch argümanıyla
  anahtarlanabilir (`imu:=true` → `ekf_imu.yaml` + madgwick). Odometri kovaryansı
  hıza göre ölçekleniyor. Encoder girdisinden yalnız `vx` ve pose `yaw` füze
  ediliyor; `vyaw` kapalı olduğundan aynı yaw bilgisi pose+twist olarak iki kez
  sayılmıyor. `odom0_differential: false`.
  Çıktı: `/odometry/filtered` (Nav2 bunu kullanır).
- **Kabul:** 10 m düz sürüşte konum hatası < %2; 360° dönüş sonrası yaw hatası < 5°
- ✅ Sahte STM32 nominal 10 m kabulü (02.08.2026): gerçek **10.0085 m**,
  ham konum hatası **%0.003**, EKF son konum hatası **0.0073 m**, ham yanal
  sapma **0.0000 m**. Bu yalnız taklit tutarlılığı kanıtıdır.
- ✅ Sahte STM32 nominal 360° kabulü (02.08.2026): gerçek **360.584°**,
  ham yaw hatası **0.041°**, EKF yaw hatası **4.543°**.
- ✅ RViz yükü performans düzeltmesi (02.08.2026): büyüyen Path mesajı metrik
  callback'inden çıkarılıp ayrı `odometry_paths.py` process'ine alındı. İzler
  hareket eşiğiyle en çok 10 Hz örnekleniyor, 500 noktayla sınırlı ve 2 Hz,
  best-effort/depth 1 yayımlanıyor. Robot durduktan sonra 2 s EKF settle var.
  Üç headless koşuda EKF birikimli/son yaw hatası **0.028–0.091°**, üç RViz
  koşusunda **0.049–0.060°**; altı koşunun tamamı PASS. `odom0_queue_size=10`
  korundu: ölçülen timestamp yaşları milisaniye düzeyinde ve kuyruk taşması
  kanıtı yok. Bu sonuç encoder yaw'ının EKF'de korunmasıdır; bağımsız sensörle
  doğruluk iyileşmesi iddiası değildir.
- ✅ EKF topic/TF/rate kabulü: `/odom` **100.000 Hz**, ground truth
  **100.014 Hz**, `/odometry/filtered` **50.001 Hz**; `odom → base_footprint`
  sürücüde kapalı ve EKF tarafından yayınlanıyor. Frame değerleri ve sonluluk
  kabul aracınca doğrulandı.
- ✅ Hata enjeksiyonu algılandı: iki tekere `%5` ölçek hatasında 10 m ham hata
  **%4.997 FAIL**; gerçek wheel separation `0.520 m` iken 360° ham yaw hatası
  **41.582° FAIL**, önerilen değer **0.51997 m**.
- 🟡 `fake_imu.py` ile IMU boru/smoke testi: `/imu/data_raw → /imu/data → EKF`
  50 Hz, `imu_link` ve sonlu/anlamlı kovaryanslar doğrulandı. Sahte IMU bağımsız
  doğruluk kanıtı değildir; gerçek IMU kabulü yapılmadı.
- **Genel durum: 🟡.** Sahte donanım kabul aracı ve boru başarılıdır; bu sonuçlar
  gerçek araç/encoder/zemin kalibrasyonu sonucu gibi yorumlanamaz.

- ⬜ `sahte:=false` ile gerçek seri port ve iki STM32 firmware uyumu kabul edilecek
- ⬜ Gerçek encoder ile 10 m/360° saha testi ve wheel radius/separation kalibrasyonu
- ⬜ Gerçek, bağımsız IMU ile füzyon doğruluğu kabulü
- ⬜ Lift komut action/service'i ve fork/limit/hata geri bildirimi `base_driver`a bağlanacak
- ⬜ Seri kopma/yeniden bağlanma, topic freshness ve ayrıntılı fault/diagnostic yayını eklenecek

**Bu fazda çıkan tasarım sorusu — güvenlik bütçesi:** haberleşme kesildiğinde araç
watchdog süresi boyunca kör gidiyor. Ölçüldü: en yüksek hızda (0.838 m/s) 200 ms
watchdog + 80 ms motor zaman sabiti = **23 cm**. Şartname rota sapmasını 10 cm'de
sınırlıyor. Elektronik ekibiyle görüşülüp watchdog'un 100 ms'e indirilmesi veya
`nav2_collision_monitor` güvenlik bölgelerinin bu mesafeye göre boyutlanması gerekiyor.
Değer bir testle kilitli (`test_haberlesme_kesintisi_durma_mesafesi_butcesi`).

### Faz 4 — Haritalama 🟡 simülasyon kabulü (03.08.2026)
- `slam_toolbox` async mode, YDLidar Tmini Pro (0.03–12 m) parametreleri
- `ros2 launch marco_localization mapping.launch.py` → EKF + LiDAR + slam
- `ros2 run marco_localization harita_kaydet.sh <isim>` → `marco_navigation/maps/`
- **Masa borusu:** `/map` yayınlandı, `map→odom` TF oluştu ve `oda_test` kaydedildi
- ✅ WSL/Gazebo Fortress `scan → slam_toolbox → /map` zinciri gerçek süreçlerle çalıştı
- ✅ `map → odom → base_footprint → base_link → laser_link` TF zinciri doğrulandı;
  mapping sırasında base_driver/EKF çalıştırılmadı ve her dinamik TF'nin tek sahibi vardı
- ✅ Harita iki bağımsız boş SLAM oturumunda kaydedildi: 279×199 ve 279×200 @ 0.05 m;
  bilinen hücre oranı %96.47 / %96.33, TF kesintisi 0, son `/cmd_vel` sıfır
- ✅ YAML+PGM yapısı, boş/dolu/bilinmeyen sınıfları doğrulandı; ikinci harita gerçek
  `nav2_map_server` lifecycle düğümünde active olup 279×200 `/map` olarak yeniden yüklendi
- ✅ Kontrollü topic-yok/map-yok koşusu `/scan`, `/odom`, `/map`, TF ve map-saver
  hatalarını PASS vermeden raporladı; Ignition oturum izolasyonu tekrarlı koşu için eklendi
- ✅ Dönüşteki geçici LaserScan ayrışmasının simülasyon kök nedeni ölçüldü: DiffDrive'ın
  tekerlekten bütünlediği odometri, temas/kaster kayması sırasında GPU LiDAR'ın fiziksel
  gövde pozundan ayrılıyordu. Simülasyonda tek `odom→base_footprint` sahibi Fortress
  OdometryPublisher yapıldı; tekerlek odometrisi yalnız `/wheel_odom`/`/wheel_tf`te tutuldu
- ✅ 15 Hz LiDAR ve fiziksel-pose odometrisiyle endpoint→occupied ortalama/p95 hata
  0.20, 0.35 ve 0.50 rad/s dönüşlerde sırasıyla 0.0209/0.0374 m,
  0.0202/0.0368 m ve 0.0205/0.0368 m oldu (eski 0.50 rad/s ortalama 0.446 m);
  TF extrapolation 0, odom 50 Hz, TF 90 Hz, RTF ortalama 0.984, son komut sıfır
- ✅ `missing_laser_link` kontrollü negatifinde scan 14.89 Hz gelirken SLAM `/map`
  üretmedi ve kabul aracı 8.46 saniyede FAIL verdi; eksik sensör TF gizlenmedi
- **Deskew sınırı:** Fortress GPU LiDAR `scan_time=0` ve `time_increment=0` yayıyor;
  uydurma ışın zamanı/deskew eklenmedi. Bu davranış gerçek YDLidar ile sahada yeniden
  ölçülüp doğrulanmalıdır
- 🟡 RViz yapılandırması Map, RobotModel, TF, LaserScan, Odometry ve Path ile hazır;
  dönüş hizası sayısal kabulü geçti, son WSLg görsel incelemesi operatör kabulüdür
- ⬜ Gerçek araç + gerçek encoder + gerçek YDLidar ile geçerli parkur haritası
- ⬜ Sahada 60 dakikalık kurulum/haritalama/kayıt provası
- **Sınır:** `marco_test.sdf` sonucu simülasyon kabulüdür; resmî parkur veya gerçek araç
  kabulü değildir. Bu nedenle genel Faz 4 durumu 🟡 kalır.

### Faz 5 — Lokalizasyon 🟡 simülasyon kabulü (03.08.2026)
- ✅ WSL/Fortress tek komut zinciri: simülasyon + `map_server` + `nav2_amcl` +
  lifecycle + güvenilir `/initialpose` + kontrollü sürüş + kabul aracı + isteğe bağlı RViz.
- ✅ Paketlenmiş **simülasyon test haritası** `marco_test`: 279×199, 0.05 m,
  origin `[-6.96,-4.98,0]`; install alanından map_server ile yüklendi. Bu resmî
  parkur haritası veya gerçek araç haritası değildir.
- ✅ TF sahipliği: AMCL `map→odom`, Fortress OdometryPublisher
  `odom→base_footprint`, robot_state_publisher robot içi TF'ler; slam_toolbox,
  EKF ve base_driver simülasyon launch'ında yok. Kurulu zincir sonrasında exact-time
  TF düşmesi/ekstrapolasyonu üç nominal koşuda sıfır.
- ✅ Bağımsız karşılaştırma: `/odom` truth sayılmadı. Gazebo
  `/world/marco_test/dynamic_pose/info` içindeki model/world pozu TF yayınlamayan
  `/ground_truth/odom` konusuna çevrildi. SLAM başlangıcında map ve world eksenleri
  çakıştığından sabit `map←world=[0,0,0]` dönüşümü açıkça uygulandı.
- ✅ Üç temiz nominal koşunun tamamı PASS. Konum mean/p95/max/final (m):
  `0.0148/0.0285/0.0368/0.0132`, `0.0132/0.0283/0.0364/0.0082`,
  `0.0144/0.0287/0.0361/0.0214`. Yaw mean/p95/max/final (°):
  `0.552/1.549/1.808/0.099`, `0.527/1.564/1.850/0.032`,
  `0.542/1.548/1.848/0.062`. Yakınsama: 7.32/7.33/7.02 s; scan ≈14.8 Hz,
  odom ≈48.9 Hz, AMCL ≈4.8 Hz, RTF ortalama 0.981, 301 parçacık, final cmd sıfır.
- ✅ Doğruya yakın initial pose (+0.10 m/+5°): 10.39 s yakınsama, rota PASS.
- 🟡 Hatalı initial pose (+0.50 m/+15°): 57.22 s içinde hedef banda döndü ve final
  0.0188 m/0.043° oldu; warm-up dâhil p95 konum 0.472 m olduğundan nominal kabul
  JSON'u dürüstçe FAIL. Bu sonuç yalnız yeniden yakınsama senaryosudur.
- ✅ Kontrollü lifecycle restart: map_server ve Gazebo açıkken AMCL
  deactivate→cleanup→configure→activate; yeni initial pose ve hareket sonrası
  `/amcl_pose` ile `map→odom` geri geldi, ek TF sahibi oluşmadı.
- 🟡 `reinitialize_global_localization` servisi mevcut ve çağrıldı. Simetrik test
  dünyasında kısa dönüş sonrası parçacık tahmini doğru moda toplanmadı
  (pozisyon covariance toplamı ≈0.918); sonuç gizlenmeden belirsiz/FAIL bırakıldı.
- ✅ Negatif kanıt: olmayan map yolu launch'u açık hata ile reddetti. Initial pose
  verilmeyen kontrollü timeout `/amcl_pose`, `map→odom`, yakınsama ve initial-pose
  koşullarını FAIL raporladı ve kabul aracı `/cmd_vel=0` yayımladı.
- ✅ Operatör RViz simülasyon görsel kabulünü onayladı: map, robot, TF,
  Best Effort/queue=1/decay=0 scan, odom, AMCL covariance/particles ile farklı
  renkli ground-truth ve AMCL yolları görünür doğrulandı.
- **Genel durum: 🟡.** Aşağıdaki gerçek donanım kabul maddeleri tamamlanmadı:
  gerçek encoder odometrisi, gerçek YDLidar, gerçek parkur haritası, 5 dakika gerçek
  araç sürüşü, saha <5 cm/<3° kabulü ve başlangıç/yeniden lokalizasyon saha provası.

### Faz 6 — Temel Nav2 🟡 simülasyon entegrasyonu (03.08.2026)
- ✅ Simülasyona özel `simulation_navigation.launch.py`, Faz 5
  `simulation_localization.launch.py` zincirini `auto_drive:=false` ve Faz 5 kabulü
  kapalı include ediyor; map_server, AMCL, initial pose ve TF yayıncıları çoğaltılmıyor.
- ✅ Dokuz lifecycle düğümü gerçek WSL/Fortress koşusunda active görüldü:
  map_server, amcl, planner/controller/smoother/behavior server, bt_navigator,
  waypoint_follower ve velocity_smoother.
- ✅ Kurulu plugin XML'lerinden doğrulanan Smac Hybrid (`REEDS_SHEPP`) + Rotation
  Shim içinde Regulated Pure Pursuit yüklendi. RPP `allow_reversing: true` ve
  `use_rotate_to_heading: false`; shim yalnız son hedef yaw hizalamasını yapıyor ve
  başlangıçta 180° dönerek Reeds-Shepp geri segmentini ileriye çevirmiyor.
- ✅ Simülasyon odom girdisi `/odom`; gerçek donanım `navigation.launch.py` ve
  `nav2_params.yaml` değiştirilmedi. Hızlar +0.50/-0.30 m/s ve ±0.60 rad/s ile sınırlı.
- ✅ CAD footprint `[[0.50,0.35],[0.50,-0.35],[-1.18,-0.35],[-1.18,0.35]]`;
  global costmap static+inflation ve unknown/outside kapalı, local costmap `/scan`
  marking/clearing+inflation olarak gerçek düğümlerde yüklendi.
- ✅ `ComputePathToPose`: serbest hedef SUCCEEDED (2.000 m, 29 poz, map frame);
  occupied, harita dışı ve eksik-TF hedefleri kontrollü FAIL verdi.
- ✅ Uzun arka footprint için geçersiz ilk geri hedefin kök nedeni statik kırmızı
  kutuya yetersiz açıklıktı; footprint/inflation küçültülmedi. Açık alandaki yeni
  hedefte planın 12/12 segmenti geri, Nav2 minimum `linear.x=-0.30 m/s`, action
  SUCCEEDED, final 0.081 m/3.71°, kesişim 0 ve son Twist sıfır ölçüldü.
- ✅ Dört hedefli dizinin üç bağımsız temiz headless oturumu PASS. AMCL konum p95:
  0.0303/0.0382/0.0368 m; yaw p95: 0.429/0.533/0.447°; minimum footprint
  açıklığı 0.0739/0.0360/0.0735 m; tüm action'lar SUCCEEDED, TF drop/extrapolation
  ve footprint kesişimi 0, final Twist sıfır.
- ✅ Kontrollü kırmızı dinamik engel local costmap/RPP tarafından görüldü; robot
  durdu, BT Wait görüldü, engel kaldırılınca aynı action SUCCEEDED oldu. Wait 14.22 s,
  kesişim 0 ve son Twist sıfır.
- ✅ Action cancel ayrı gerçek oturumda CANCELED ve cmd_vel sıfır; controller lifecycle
  inactive testi action'ı güvenli FAIL'e götürdü ve controller yeniden active yapıldı.
  Occupied, harita dışı ve eksik-TF hedefleri kontrollü FAIL verdi.
- ✅ Kalan negatifler ayrı temiz süreç/JSON ile gerçek çalıştırıldı: izole Nav2 scan
  gate kapatıldığında local costmap freshness (`expected_update_rate=0.20 s`) düştü,
  action güvenli timeout/cancel ve sıfır hızla bitti; Smac `max_planning_time=1 µs`
  planı kontrollü FAIL yaptı; initial pose verilmeden action server hedefi kabul etmedi;
  AMCL deactivate + TF cache expiry sonrası map→odom kaybı güvenli timeout/cancel ile
  sonlandı. Her koşudan sonra Twist sıfırlandı ve süreçler SIGINT ile temizlendi.
- ✅ Son görünür WSL koşusu dört hedefle PASS (`/tmp/marco_phase6/final.json`): Gazebo
  server/GUI software renderer, RViz WSLg D3D12 GPU/OpenGL 4.2; Map, robot, TF,
  Best Effort scan, AMCL, iki costmap, planlar, footprint ve iki tahmin yolu açık.
  Operatör map/plan/costmap/footprint/LiDAR görüntüsünü, dört hedefi, recovery=0 ve
  son cmd_vel sıfırı onayladı; ardından Gazebo/RViz/launch kontrollü SIGINT ile kapatıldı.
- **Genel durum: 🟡.** Gerçek encoder ve YDLidar, gerçek parkur haritası, gerçek araçta
  hedefe gidiş/çarpışmasızlık, hız-ivme kalibrasyonu, fiziksel acil durdurma ve
  yüklü/yüksüz ileri/geri saha davranışı açık kalır.

### Faz 7 — Rota ağı 🟡 rota hesaplama borusu (30.07)
- `nav2_route` entegrasyonu, GeoJSON graf formatının projeye uyarlanması
  (`graphs/demo_rota.geojson`, `route_server.yaml`, `route.launch.py`)
- Rota grafı üretme: CLI `rota_hesapla.py` (düğüm ID / pose); RViz/Flutter editör sonra
- Kenar hız metadata'sı (`abs_speed_limit`) ve scorer'lar tanımlı; takipte uygulanması eksik
  (`ComputeRoute + FollowPath`, `ComputeAndTrackRoute` değil)
- BT: `navigate_route_wait.xml` — ComputeRoute + FollowPath + Wait
- `TriggerEvent` QR/PLC/dock bağlantıları ve gerçek düğüm rolleri henüz yok
- 🟡 İki nokta arası rota hesabı doğru (`0→8` SUCCEEDED, ~7.5 m)
- ⬜ Gerçek parkur grafı ve GUI/RViz düğüm-kenar editörü yapılacak
- ⬜ Pickup/dropoff/bekleme/QR/q5/şarj rolleri, ileri/geri ve yüklü hız metadata'sı eklenecek
- ⬜ Çapraz rota hatası hesaplanıp `/robot_status` ve güvenlik limitine bağlanacak
- **Kabul (saha):** araç yalnız tanımlı kenarlarda, en iyi rotayı seçerek sapma ≤10 cm

**Simülasyon kabulü (03.08.2026):**
- ✅ `simulation_route.launch.py`, Faz 6 simülasyon zincirini tek kez kullanıyor; simülasyona özel
  route server/lifecycle, doğrulanmış `marco_test_route.geojson`, RViz graph görünümü ve kabul
  istemcileri eklendi. Gerçek `route.launch.py` ve gerçek parametreler değiştirilmedi.
- ✅ Kurulu `ComputeRoute`, `ComputeAndTrackRoute`, `Route/RouteNode/RouteEdge`, `SpeedLimit`,
  `DynamicEdgesScorer`, `AdjustSpeedLimit` arayüzleri yerel kurulumdan doğrulandı.
- ✅ Graph validator GeoJSON/ID/uç/directed erişilebilirlik/metadata/hız/CAD footprint map sweep
  kontrollerini route server başlamadan uyguluyor (6 node, 12 yönlü edge).
- ✅ Gerçek `ComputeRoute` action: node→node, ters yön, aynı node, olmayan node ve tek-yön
  alternatif kontrolleri; path frame/sonluluk/uzunluk/maliyet ve edge dizisi bağımsız doğrulandı.
- ✅ Üç temiz nominal simülasyon koşusunda beş görev segmenti SUCCEEDED; hızlı `0.50`, yavaş
  `0.15`, geri `0.15 m/s` limitleri uygulandı; geri edge Nav2 ile negatif `linear.x` üretti;
  son hız limiti reset ve son `/cmd_vel=0` oldu.
- ✅ Ground-truth çapraz hata: üç koşuda p95 `0.079/0.072/0.070 m`, maksimum
  `0.081/0.076/0.071 m`; simülasyon ≤10 cm kabulü geçti. Bu sonuç saha kabulü değildir.
- ✅ Üç nominal koşu tamamlandı.
- ✅ Faz 7 lifecycle/TF/scan/cancel negatifleri yeniden çalıştırılmadı; ortak Nav2 zinciri için
  Faz 6 bölümündeki scan gate, controller inactive, map→odom kaybı, planner timeout,
  pre-convergence ve action cancel gerçek koşu kanıtları referans alındı.
- ✅ Dynamic edge kabulü tamamlandı: edge `106` rota öncesi kapatılınca `[106,107]` yerine
  `[105]` seçildi; tekrar açılınca `[106,107]` geri geldi.
- ✅ SpeedLimit kabulü tamamlandı: tek `/speed_limit` yayıncısı, aktif GeoJSON
  `abs_speed_limit` kaynağı, hızlı/yavaş/geri gerçek cmd sınırları ve rota bitimi/cancel/hata
  resetleri doğrulandı; son `/cmd_vel=0`.
- ✅ Canlı ağırlıklı scorer kabulü: saf `DistanceScorer` gerçek `ComputeRoute` sonucunda
  kısa edge `[105]`, saf `TimeScorer` ise hızlı `[106,107]` seçti; scorer kontrolünde robot
  hareket ettirilmedi (`/tmp/marco_phase7/scorer_live.json`).
- ✅ Aktif kısa edge `105` üzerindeki tek engel koşusunda rota öncesi ve engel sırasında
  `[105]` kaldı; Wait görüldü, Spin/BackUp görülmedi, engel kalkınca aynı action SUCCEEDED
  oldu. Dynamic edge/alternatif rota kullanılmadı; son Twist sıfır ve hız limiti resetlendi.
- ✅ Aynı koşunun ground-truth ölçümü: footprint kesişimi `0`, minimum açıklık `0.1972 m`,
  yanlış-edge ve graph-dışı kestirme örneği `0`; cross-track mean/p95/max
  `0.0261/0.0631/0.0665 m` (`/tmp/marco_phase7/obstacle_route.json`).
- ⬜ Resmî parkur graph'ı; gerçek pickup/dropoff/q5/şarj rolleri; gerçek araçta ≤10 cm;
  gerçek hız profilleri; QR/PLC/docking TriggerEvent; graph editörü ve saha engel/bekleme kabulü açık.

### Faz 8 — Güvenlik ve engel davranışı 🟡 masa borusu (30.07)
- `nav2_collision_monitor` yavaşlama/durma bölgeleri (`marco_safety`)
- "Dur ve bekle, kaçınma" davranış ağacı (Faz 6/7 Wait BT)
- `twist_mux` öncelik zinciri: estop > dock > manual > nav;
  e-stop `/base/estop`, manuel `/base/manual_mode` kilitleri
- Zincir: Nav2 → `cmd_vel_raw` → CM → `cmd_vel_safe` → mux → `cmd_vel`
- `route_safe.launch.py`
- 🟡 Masa testinde stop poligonunda LiDAR → `cmd_vel_safe=0` görüldü
- ⬜ Geri sürüşte aracın -x boyunu kapsayan arka stop/yavaşlama bölgesi eklenecek
- ⬜ Engel durumu görev yöneticisi ve GUI'ye bağlanacak; action beklerken zaman aşımı politikası tanımlanacak
- ⬜ E-stop, STM32 haberleşme kaybı ve sensör freshness için fiziksel fail-safe testi yapılacak
- **Kabul (saha):** ölçülen güvenli mesafede duruş, engel kalkınca aynı rota ve ≤10 cm sapma

### Faz 9 — Hassas yanaşma 🟡 yalnız mock veriyle (30.07)
- Docking action server: `marco_docking` `/dock_to_station` → `/cmd_vel_dock`
- 🟡 Mock `/lane/offset` + `/qr/detection` ile action smoke testi başarılı
- ⬜ `lane_tracking` piksel Float32 üretiyor; `LaneOffset` metre/açı/güven sözleşmesine dönüştürülecek
- ⬜ Doğrudan `/pwm_left/right` kontrolü kaldırılıp güvenli `/cmd_vel_dock` yoluna alınacak
- ⬜ GM67 okuma ve kamera tabanlı gerçek QR poz düğümü yazılacak
- ⬜ Boylamsal mesafe/son durma ölçümü ile e-stop/engel/action iptal davranışı eklenecek
- **Kabul (saha):** gerçek kamera+QR ile 20 denemenin en az 18'inde ±7.5 cm ve ±5°

### Faz 10 — Görev, PLC ve GUI 🟡 yalnız mock arayüz (30.07)
- ✅ Servis/mesaj sözleşmeleri, `mock_plc`, `/mission/start` ve temel durum geçişleri var
- 🟡 `simulate_steps:=true` yalnız zaman gecikmesiyle senaryoyu taklit ediyor
- ⬜ `simulate_steps:=false` için Nav2 `ComputeAndTrackRoute`/FollowPath action client'ı yok
- ⬜ Docking action client'ı, lift action'ı, yük durumu ve dönüş rotası bağlanmadı
- ⬜ E-stop/hata sırasında aktif action iptali ve durum geçişlerini dondurma yok
- ⬜ Gerçek PLC Wi-Fi/protokol köprüsü, yeniden bağlanma ve q5 fiziksel bekleme yok
- ⬜ GUI Wi-Fi/rosbridge katmanı ve manuel joystick/lift komut yolu yok
- ⬜ `/robot_status` poz, kovaryans, rota sapması, engel ve QR alanları canlı topic'lerden gelmiyor
- ⬜ Batarya politikası, otonom şarj, sistem mesajları ve zaman damgalı olay günlüğü yok
- **Kabul:** rastgele görev → alma → QR/şerit → lift → q5 izin → bırakma → bekleme →
  PLC tamamlandı akışı; ret/zaman aşımı/e-stop/engel/haberleşme kaybı testleriyle gerçek sistemde çalışmalı

### Faz 11 — Gerçek donanım entegrasyonu ⬜
- İki gerçek STM32'nin port/topolojisi, firmware protokolü, motor PID, encoder ve lift kabulü
- YDLidar'ın mm cinsinden montaj TF'i; gerçek encoder ile SLAM ve AMCL saha kalibrasyonu
- IMX219 veya USB yedek kamera, GM67 ve gerçek `LaneOffset`/`QrDetection` düğümleri
- Yön duyarlı ön/arka güvenlik bölgeleri; e-stop, haberleşme kaybı ve tüm hata zinciri
- Lift action'ı, limit-switch geri bildirimi ve yüklü/yüksüz hız/geri sürüş davranışı
- Tek bir gerçek-sistem launch'ı: base + localization + route + safety + docking + mission
- Gerçek PLC köprüsü ve Flutter GUI ağ köprüsü/canlı telemetri
- Mission `simulate_steps:=false` ile gerçek Nav2+docking+lift action sonuçlarına bağlı uçtan uca senaryo
- **Sayısal kabul:** 10 m odom <%2; 360° yaw <5°; AMCL 5 dk <5 cm/<3°;
  rota sapması ≤10 cm; docking 20 denemede ≥18 kez ±7.5 cm/±5°; engelde dur/devam
- **Kanıt:** tarihli rosbag, test komutu/çıktısı, metrik özeti ve fiziksel video
- **Video önceliği:** 11.08.2026 için önce gerçek STM32 + encoder + Tmini Pro haritalama

---

## 9. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| WSL2/Gazebo ile gerçek Orange Pi parametreleri ayrışır | Simülasyonda geçip sahada kalır | Aynı ROS/Humble arayüzleri, version pin ve gerçek rosbag replay testi |
| IMU olmadan ±5° yön toleransı tutturulamaz | -5 puan, tekrarlı | IMU ekle; AMCL'e daha çok güven; docking'de görsel düzeltme |
| IMX219 MIPI CSI sürücüsü RK3588'de sorun çıkarır | Şerit takibi çalışmaz (-10) | Erken prototiple; yedek olarak USB kamera |
| Rota sapması 10 cm'i aşar | -5, tekrarlı | Hızı düşür, RPP ayarı, gerekirse MPPI |
| 60 dakikalık haritalama penceresine yetişilemez | Yarışmadan elenme | Prosedürü tekrar tekrar prova et, tek komuta indir |
| PLC protokolü geç gelir | Faz 10 gecikir | Protokolü soyutla, sahte PLC sunucusu ile geliştir |
| `lane_tracking` doğrudan PWM ile güvenliği baypas eder | Kontrolsüz hareket/e-stop riski | PWM yolunu kaldır; `LaneOffset → docking → cmd_vel_dock → safety` zorunlu olsun |
| Mock/masa testi tamamlandı sanılır | Fiziksel entegrasyon geç kalır | ✅ yalnız tarihli gerçek kabul kanıtıyla verilsin |

---

## 10. Çalışma Şekli

- Bu dosya projenin tek plan referansıdır; kararlar değiştikçe burası güncellenir.
- ✅ yalnız gerçek bağlantı + hata yolu + tekrar edilebilir test + tarihli kanıtla verilir.
- Mock, stub, sahte donanım ve yalnız topic/action smoke sonucu en fazla 🟡 olabilir.
- Kabul kanıtı için komut, parametre, rosbag/log yolu ve sayısal sonuç birlikte kaydedilir.
- Değişiklikten sonra `AGENT_REFERANS.md` durum özeti bu planla eşitlenir.
