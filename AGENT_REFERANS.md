# AGENT REFERANS — MarCO Forklift AGV

Ajanın her adımda okuyacağı sıkıştırılmış bağlam. Detay: `PROJE_PLANI.md`.
Kaynak PDF metinleri: `/tmp/marcorapor.txt`, `/tmp/sartname.txt` (yeniden üretmek için
`pdftotext -layout ~/Downloads/<dosya>.pdf`).

## ⚠ TAKVİM — EN KRİTİK KISIT
| Tarih | Aşama | Durum |
|---|---|---|
| 01.07.2026 | PDR son teslim | geçti |
| 10.07.2026 | PDR sonucu | geçti |
| **11.08.2026 17:00** | **Hareket-Kabiliyet Videosu son teslim** | **YAKLAŞIYOR** |
| 18.08.2026 | Finalist açıklanma | |
| 30 Eyl–4 Eki 2026 | TEKNOFEST Şanlıurfa (final) | |

**Video = toplam puanın %15'i. Göndermeyen takım finale KATILAMAZ.**
Video FİZİKSEL ROBOT gerektirir, simülasyon kabul edilmez. Göstermesi gerekenler:
A→B dengeli hareket · yükü alıp doğru alana bırakma · bilgisayardan komutla hareket ·
çizgi takibi · engelde durma · sağa/sola dönüş · haritalama · GUI · **e-stop'ta tüm
motorların durup sistemin kapanması**. Min 720p, 2-3 dk alt / 5 dk üst sınır, mp4,
YouTube herkese açık, ortam sesi duyulacak.
Kabul EDİLMEYEN: engele çarpma, istemsiz dönüş/sürüş, dışarıdan otonom-dışı kontrol.

## KAPSAM (2026-07-26 netleşti)
**BİZİM:** URDF/TF · odometri tüketimi+kalibrasyon · EKF · SLAM · AMCL · rota ağı ·
engel/güvenli duruş · docking'in KONTROL tarafı · Nav2'nin tamamı
**BAŞKA EKİPLER:** STM32 firmware · kamera/şerit takibi · QR okuma · Flutter GUI ·
PLC haberleşmesi · PCB/güç/mekanik
→ Onların çıktıları için **mock yayıncı** yaz, bekleme.
→ STM32 UART protokolünü BİZ tanımlarız (onlar implement eder).
Videoda bize düşen tek madde: **haritalama gösterimi**.

## DONANIM DURUMU
- Araç şasi+motor+teker HAZIR, yürüyor — ama **şu an OrangePi'ye BAĞLI DEĞİL**, başka yerde
- OrangePi'de `/dev/ttyUSB*`, `/dev/ttyACM*` YOK; lsusb'de LiDAR/seri dönüştürücü YOK
- `/dev/video*` yalnızca donanım codec (video-dec0/enc0) → kamera yok
- PDR sonucu: **100 puan**, video aşamasındayız
- Sim: **WSL2 + Ubuntu 22.04 kullanıcının PC'sinde**; Fortress/ros_gz Faz 2 testi ✅ 02.08

## ORTAM
- OrangePi 5 Plus, RK3588 aarch64, Ubuntu 22.04.5, 8 core, 7.7GB RAM, 48GB boş
- ROS 2 **Humble**, Nav2 **1.1.20**, Python 3.10.12
- KURULU: nav2 (tam), nav2_route, nav2_mppi, nav2_smac, nav2_collision_monitor,
  slam_toolbox, rviz2, robot_state_publisher, teleop_twist_keyboard
- KURULDU (Faz 0, 26.07): robot_localization, xacro, joint_state_publisher(+gui),
  twist_mux, rplidar_ros, cv_bridge, image_transport(+plugins), imu_tools,
  tf_transformations, camera_info_manager, usb_cam, rqt_tf_tree, rqt_graph
- Ağ: WiFi `wlx4822541cd7c3` → 192.168.86.116, internet VAR. Cursor 192.168.55.2 üzerinden.
- Derleme: `cd ~/marco_ws && source /opt/ros/humble/setup.bash && colcon build --symlink-install`
- ARM64'te YOK: `ros-humble-gazebo-ros-pkgs`, `gazebo11` → Gazebo Classic imkânsız
- VAR: `ros-humble-ros-gz` 0.244.25 + `ignition-fortress` (Fortress eşi)
- OpenGL = **llvmpipe** (yazılımsal, panfrost yok) → sim çok yavaş olacak
- Workspace: `~/marco_ws` — 11 paket; `marco_simulation` Fortress ortamı uygulanmış

## SERT SAYILAR
| | |
|---|---|
| Gövde | 1536 × 650 × 550 mm |
| Yerden yükseklik / lift | 30 mm / 100 mm |
| Tekerlek | çap 200mm, r=0.1m, çevre 0.6283m |
| Motor | Linix 112ZY24, 12V'ta 80 RPM |
| **Gerçek max hız** | **0.838 m/s** (rapordaki 1.46 m/s YANLIŞ, o 24V değeri) |
| Encoder | firmware çıktısı **360 tick/tur**, tekrar ×4 YOK = **1.745 mm/tick** |
| Ayak izi yarıçapı | çevrel 0.834 m, iç teğet 0.325 m → POLİGON kullan, daire DEĞİL |
| Maks. yük | 5 kg palet |
| Sürüş | diferansiyel, 2 tahrik + 4 sarhoş, sıfır dönüş yarıçapı |

Hız hedefleri: transit yüksüz 0.50 · yüklü 0.35 · yaklaşma 0.15 · docking 0.05 m/s ·
açısal max 0.6 rad/s

## ŞARTNAME KISITLARI (pazarlıksız)
- Rota sapması ≤ **10 cm** (ceza -5, max 2 kez)
- İstasyon toleransı **±7.5 cm** konum, **±5°** yön (ceza -5, max 2 kez)
- **Tanımlı rotalar** üzerinde hareket + rota optimizasyonu ROBOT hesaplayacak
- Engelde **DUR ve BEKLE** — kaçınma İSTENMİYOR, engel kalkınca devam
- İstasyona 1.5 m kala yerde QR + renkli şerit → hassas yanaşma
- Yük **hareket yönünün TERSİNDE** taşınacak (çatal arkada, geri sürüş)
- q5 = kapı kontrol noktası, PLC'den geçiş izni
- Saha süresi: haritalama+rota **60 dk** · görev **30 dk** hedef / **45 dk** limit
- 3 alma + 3 bırakma noktası, PLC rastgele seçer
- Wi-Fi "YARISMA AGI", internet yok, MAC filtreli, 2 cihaz (robot + monitör PC)
- Puanlar: haritalama+30 rota+20 PLC+20 kapı+20 GUI+20 görev+30 çizgi+10 QR+10
  çarpışma+10 sunum+10 yerlilik+5 özgünlük+5 otoşarj+5

## MİMARİ KARARLARI
- `map→odom` = **nav2_amcl** (raporda YOKTU, eklendi — kritik)
- `odom→base_footprint` = **robot_localization/ekf_node** (elle Kalman YAZMA)
- IMU **opsiyonel** — EKF konfigü launch argümanıyla IMU'lu/IMU'suz çalışmalı
- Rota takibi = **nav2_route** + GeoJSON graf (serbest planlayıcı DEĞİL)
  - `DistanceScorer`/`TimeScorer` → rota optimizasyonu
  - `AdjustSpeedLimit` → kenar bazlı hız
  - `TriggerEvent` → QR okuma, PLC kapı, docking tetikleme
- Kontrolcü = **Regulated Pure Pursuit** (`allow_reversing: true`), MPPI yedek
- Dinamik engel global costmap'e İŞLENMEYECEK; `nav2_collision_monitor` + "bekle" BT
- Hassas yanaşma = ayrı **docking action server**, `/cmd_vel_dock` → twist_mux
- twist_mux önceliği: estop > dock > manual > nav

## TF AĞACI
`map → odom → base_footprint → base_link → {laser_link, imu_link, camera_front_link,
camera_rear_link, left/right_wheel_link, caster_*_link ×4, fork_link(prizmatik)}`

## PAKETLER (11)
`marco_msgs` `marco_description` `marco_bringup` `marco_base` `marco_localization`
`marco_navigation` `marco_perception` `marco_docking` `marco_safety` `marco_mission`
`marco_simulation`

## FAZ DURUMU
| Faz | İş | Kabul kriteri | Durum |
|---|---|---|---|
| 0 | Paket kurulumu + workspace iskeleti | temiz `colcon build`, 11 paket | ✅ 26.07 |
| 1 | URDF/xacro + TF | RViz'de model doğru, TF kopuksuz | ✅ 26.07 |
| 2 | Simülasyon dünyası | /scan /odom /image yayınlanıyor | ✅ 02.08 |
| 3 | Odometri + EKF + kalibrasyon | 10m'de <%2, 360°'de yaw <5° | ✅ 26.07 |
| 4 | slam_toolbox haritalama | harita çıkıyor+kaydediliyor | ✅ 29.07 |
| 5 | AMCL lokalizasyon | 5dk sürüşte <5cm, <3° | ✅ boru 29.07¹ |
| 6 | Temel Nav2 | RViz hedefine çarpmadan varış | ✅ boru 30.07² |
| 7 | nav2_route rota ağı | sapma <10cm, en kısa rota doğru | ✅ boru 30.07³ |
| 8 | Güvenlik + engel davranışı | engelde dur, kalkınca devam | ✅ boru 30.07⁴ |
| 9 | Hassas yanaşma | 20 denemede ≥18 kez ±7.5cm/±5° | ✅ boru 30.07⁵ |
| 10 | Görev katmanı + PLC | ortak PLC/mock/GUI zinciri | 🟡 ROS/sim 04.08⁶ |
| 11 | Gerçek donanım | saha kalibrasyonu | ⬜ |

## FAZ 1 ÇIKTISI (URDF)
Dosyalar: `marco_description/urdf/` → `marco.urdf.xacro` (üst), `properties.xacro`
(**TÜM ölçüler burada, başka yeri elleme**), `common.xacro` (renk+atalet makroları),
`base.xacro`, `wheels.xacro`, `fork.xacro`, `sensors.xacro`
Test: `ros2 launch marco_description display.launch.py` · `xacro ... | check_urdf`

Cerçeveler: `base_footprint`(z=0) → `base_link`(z=0.10, **tahrik aksı ortası = dönme
merkezi**) → chassis_link, left/right_wheel_link, 4× caster, fork_link(prizmatik 0–0.10),
laser_link, imu_link, camera_front/rear_link(+`_optical_frame`)

Türetilmiş: şasi 0.756×0.650×0.520 @ (0.128, 0, 0.190) · çatal başlangıcı x=0.506 ·
teker açısal limit 8.38 rad/s · toplam uzunluk 1.536 ✓
NOT: 30mm yerden yükseklik + 200mm teker → tahrik tekerleri şasi içine gömülü, normal.

**properties.xacro'da `TAHMINI` etiketli her değer mekanik ekibinden doğrulanmalı.**
Güncel Faz 0 değerleri: fiziksel ve odometri `wheel_separation=0.460`;
`lidar_x/y/z=+0.350/0/+0.350` (`base_link`, tarama zeminden 0.450 m);
`body_length=0.950`. Önceki `0.421` ve eski LiDAR konumu tarihsel/geçersizdir.

## FAZ 3 İLERLEMESİ (marco_base) — sürücü katmanı BİTTİ, EKF kaldı
**BİTTİ:**
- `docs/STM32_UART_PROTOKOL.md` — elektronik ekibine **iletildi** (26.07).
  Kümülatif tick (fark değil) · 2¹⁶ sarma (0..65535) · max_tick_delta filtresi ·
  STM32 zaman damgası · ham tick (metre değil) ·
  200ms watchdog · CRC16-CCITT · 115200 baud
- `marco_base/protocol.py` — çerçeve kodlama/çözme, `FrameParser` akış tabanlı,
  bozuk CRC'de tek bayt kayarak yeniden senkron.
  `decode_wheel_velocity/fork/safety` de var (özel alanlara erişmeden kullan)
- `marco_base/odometry.py` — `DifferentialOdometry` (tam yay integrasyonu),
  `tick_delta` (uint16/2¹⁶ taşma), sıçrama filtresi, `twist_to_wheel_speeds` (oransal kırpma)
- `marco_base/transport.py` — `Transport` protokolü + `SerialTransport` (pyserial 3.5,
  bloklamayan okuma). Sürücü yalnızca bu arayüze bağlı → gerçek/sahte geçişi tek parametre
- `marco_base/fake_stm32.py` — firmware'in davranışsal modeli. Motor birinci mertebe
  tepki (τ=0.08s) · 200ms watchdog · kesirli tick birikimi · e-stop/fault kilidi ·
  **`true_x/y/theta` = gerçek konum** (odometri hatasını ölçmeyi sağlar)
  Hata enjeksiyonu: `slip_factor`, `wheel_scale_error_left/right`
- `marco_base/base_driver.py` — ROS düğümü. `/cmd_vel`→ters kinematik→UART;
  tick→`/odom`(100Hz)+`/joint_states`(100Hz); durum→`/base/estop`,`/base/manual_mode`,
  `/base/battery`(10Hz). Sahte donanımda ayrıca `/base/ground_truth`.
  Kovaryans **anlık hıza göre ölçekleniyor** (EKF `odom0_differential: true` kullanacak)
- `launch/base_driver.launch.py` + `config/base_driver.yaml` (argümanlar: `sahte`, `tf`, `port`)
- `marco_bringup/launch/robot.launch.py` — robot_state_publisher + sürücü
  (+ `config/robot.rviz`: sabit çerçeve **odom**, odometri izi açık.
  `marco_description/rviz/model.rviz` ızgarayı robota bağlar → araç hareket etse bile
  yerinde duruyormuş gibi görünür, o yalnızca modeli incelemek için)
- `marco_localization/scripts/odometry_check.py` — kalibrasyon/doğrulama aracı (aşağıda)
- `test/` — **37 test geçiyor** (flake8 + pep257 dahil)

Çalıştır: `ros2 launch marco_bringup robot.launch.py sahte:=true`
Test: `cd ~/marco_ws/src/marco_base && python3 -m pytest -q` (kökten değil, paketten!
kökten çalıştırılırsa flake8 `install/` dizinini de tarar ve düşer)

### EKF konfigürasyonu (26.07, BİTTİ)
`marco_localization/config/ekf_odom.yaml` — IMU'suz (varsayılan)
`marco_localization/config/ekf_imu.yaml` — IMU'lu (opsiyonel)
`marco_localization/launch/localization.launch.py` — her ikisini de içeriyor

Çalıştır: `ros2 launch marco_localization localization.launch.py sahte:=true [imu:=true]`

**Parametre seçimleri:**
- Odometri: yalnızca **twist** (vx + vyaw) füze ediliyor — absolute pose değil.
  Neden: poz integrasyonun kendisi; birikmişi EKF'e vermek hatayı katlar.
  Uzun vadeli drift AMCL'in işi.
- IMU: yalnızca **vyaw** (gyro) + **ax** (ivme) — mutlak yaw YOK (manyetometre yok)
- `two_d_mode: true` — z/roll/pitch ihmal ediliyor
- `use_control: true` — `/cmd_vel` ön kestirim için kullanılıyor
- EKF TF yayınlar, sürücü `publish_tf:=false` alıyor (çakışma yok, doğrulandı)
- `/odometry/filtered` → 50 Hz (Nav2 bu topiği kullanacak)
- IMU geldiğinde: `imu_filter_madgwick` da başlatılıyor (`use_mag: false`)
  ham `/imu/data_raw` → filtered `/imu/data` → EKF

### LiDAR — YDLidar Tmini Pro (çalışıyor, 28.07)
**RPLIDAR A3 DEĞİL.** Elde olan birim YDLidar Tmini Pro; saatler harcanan
"RPLIDAR yanıt vermiyor" arayışının tek nedeni buydu — RPLIDAR protokol komutları
gönderiliyordu. Cihaz kimliğini komut göndermeden önce doğrula.

Sürücü ayrı workspace'te: `~/ydlidar_ros2_ws` (SDK 1.2.20 → `/usr/local`).
Derlerken ve çalıştırırken **önce onu source et**, `marco_ws` üstüne overlay olur:
```
source /opt/ros/humble/setup.bash
source ~/ydlidar_ros2_ws/install/setup.bash
source ~/marco_ws/install/setup.bash
ros2 launch marco_bringup robot.launch.py sahte:=true lidar:=true
```

Yapılandırma: `marco_localization/config/lidar_tmini_pro.yaml`

Gerçek veri hattı: YDLidar `/scan_raw` yayınlar; `LaserScanSpeckleFilter`
(`filter_window=2`, `max_range_difference=0.15 m`) SLAM/AMCL/Nav2 için `/scan`
üretir. Collision Monitor ve safety supervisor gerçek sistemde güvenlik amacıyla
filtresiz `/scan_raw` kullanır. Gövde/açı maskesi bu hatta dahil değildir.

Not: kullanılan YDLidar ROS 2 sürümü `invalid_range_is_inf` parametresini okuyup
uygulamıyordu. Yerel sürücü düzeltmesi `patches/ydlidar_invalid_range_is_inf.patch`
olarak saklanır; temiz sürücü klonuna bu patch uygulanıp overlay yeniden derlenmelidir.
`frame_id: laser_link` (sürücünün kendi varsayılanı `laser_frame`; URDF ile
eşleşmesi için değiştirildi, ekstra static TF gerekmiyor).

| Ölçüt | Değer |
|---|---|
| Model kodu / firmware | 150 / 1.1, HW 2, seri 2025122400091259 |
| Port, baud | `/dev/ttyUSB0`, 230400 |
| `/scan` hızı | 9.96 Hz (30 sn, std 0.7 ms, sıfır hata) |
| Tarama | 360° tam, `angle_increment` 0.0146 rad → **430 nokta** |
| Menzil | 0.03 – 12.0 m |
| Geçerli ölçüm oranı (kapalı oda) | %74 |
| TF `odom → laser_link` | çözülüyor; sabit `base_link→laser_link=(-0.300,0,0.180)` |

**SIRADA:** Faz 11 (gerçek donanım) veya saha/araç gelince rota takibi + docking kalibrasyonu.  
¹ AMCL boru hattı doğrulandı (map_server + lifecycle + initial pose).  
`map→odom` TF tarama gelince yayınlanır; sahada 5 dk doğruluk ölçümü araç yürüyünce.  
² Nav2 boru 30.07: `navigation.launch.py` lifecycle active, `compute_path_to_pose`
SUCCEEDED (`nav_test` 10×10 m harita). Fiziksel hedefe varış araç yürüyünce.  
³ nav2_route boru 30.07: `route.launch.py` + `compute_route` SUCCEEDED
(`demo_rota.geojson`, düğüm 0→8). Sapma <10 cm araç yürüyünce.  
⁴ güvenlik boru 30.07: `collision_monitor` active; masa LiDAR’ı stop
poligonuna girince `/cmd_vel_safe` → 0. `twist_mux` estop>dock>manual>nav.
Engel kalkınca devam = saha + FollowPath; BT zaten Wait.  
⁵ docking boru 30.07: mock lane/QR + `dock_to_station` SUCCEEDED
(pos_err≈2 mm, yaw≈0.16°). 20/18 saha kabulü kamera+şerit gelince.  
⁶ görev arayüz 30.07: `mission.launch` + mock PLC; `/mission/start` →
IDLE→…→RETURNING→IDLE, `/robot_status` yayınlanıyor. Gerçek PLC protokolü bekleniyor.

### Nav2 — temel navigasyon (✅ boru 30.07)
```
ros2 launch marco_navigation navigation.launch.py \\
    sahte:=true lidar:=true harita:=nav_test baslangic:=true
# IMU donanimi/sürücü hazırsa: imu:=true
# (donanim yokken) ros2 run marco_localization fake_imu.py
```
- Params: `marco_navigation/config/nav2_params.yaml`
- BT: `behavior_trees/navigate_to_pose_wait.xml` — engelde **Wait**, Spin/BackUp yok
- Ayak izi CAD poligon: `[[0.50,±0.35],[-1.18,±0.35]]` (daire DEĞİL)
- odom: `/odometry/filtered` · max_vel 0.50 m/s · yaw tol 0.09 rad (~5°)
- Global costmap: yalnız static+inflation (dinamik engelden kaçınma yok)
- `oda_test` haritası (~1.5×2.7 m) CAD ayak izi için **çok küçük** → `nav_test` kullan
- `map→odom` için LiDAR şart (`lidar:=false` ile planlama asılı kalır)

### nav2_route — rota ağı (✅ boru 30.07)
```
ros2 launch marco_navigation route.launch.py \\
    sahte:=true lidar:=true harita:=nav_test baslangic:=true
# Smoke (düğüm ID):
ros2 run marco_navigation rota_hesapla.py --start 0 --goal 8
```
- Graf: `graphs/demo_rota.geojson` (3×3 ızgara, çift yönlü kenarlar, `abs_speed_limit`)
- Params: `config/route_server.yaml` — DistanceScorer+TimeScorer+DynamicEdgesScorer
  (CostmapScorer YOK → engelden kaçınma yok)
- Operations: yalnız `AdjustSpeedLimit` (ReroutingService yok)
- BT: `navigate_route_wait.xml` — ilk ComputeRoute, ardından eşzamanlı
  ComputeAndTrackRoute + tek FollowPath; engelde Wait
- Launch: `route.launch.py` (navigation + `route_server` + lifecycle)
- Serbest `navigation.launch.py` hâlâ GridBased (NavFn) — yarışma yolu `route.launch.py`

### Güvenlik — collision_monitor + twist_mux (✅ boru 30.07)
```
ros2 launch marco_safety safety.launch.py
# Tam yigin (rota + guvenlik):
ros2 launch marco_navigation route_safe.launch.py \\
    sahte:=true lidar:=true harita:=nav_test baslangic:=true
```
- Paket: `marco_safety` — `config/collision_monitor.yaml`, `twist_mux.yaml`
- Zincir: `/cmd_vel_raw` → CM → `/cmd_vel_safe` → mux → `/cmd_vel`
- CM: PolygonStop + PolygonSlow (CAD ayak izine yakin); scan kaynağı
- Mux oncelik: estop(255) > dock(120) > manual(100) > nav(10);
  kilitler: `/base/estop`, `/base/manual_mode`
- BT Wait zaten Faz 6/7'de; CM komutu keser, engel dusunce Nav2 devam eder
- Masa smoke: odadaki LiDAR noktalari stop bolgesinde → `cmd_vel_safe=0` (beklenen)

### Docking — hassas yanaşma (✅ boru 30.07)
```
ros2 launch marco_docking docking.launch.py mock:=true
ros2 action send_goal /dock_to_station marco_msgs/action/DockToStation \\
  "{station_id: 'istasyon_A', position_tolerance: 0.075, yaw_tolerance: 0.087,
    approach_type: 0, timeout: 60.0}"
```
- `marco_perception/mock_lane_qr.py` → `/lane/offset`, `/qr/detection` (gerçek HSV/QR görüntü ekibinde)
- `marco_docking/dock_server.py` → action `/dock_to_station`, cmd `/cmd_vel_dock`
- Fazlar: qr_verify → lane_align → final_approach → settling
- Tolerans varsayılan: ±7.5 cm / ±5° (şartname); mux’ta dock önceliği nav’dan yüksek
- Smoke: SUCCEEDED (~2 mm / ~0.16° mock ile). 20 deneme sahada.

### Görev + PLC arayüz (✅ arayüz 30.07)
```
ros2 launch marco_mission mission.launch.py
ros2 service call /mission/start marco_msgs/srv/StartMission "{}"
ros2 topic echo /robot_status
```
- `mock_plc`: `/plc/assign_task`, `/plc/gate_permission`, `/plc/task_complete`
- `mission_manager`: durum makinesi + `/mission/start` + `/robot_status` (GUI)
- Akış: IDLE → TASK_RECEIVED → MOVING_UNLOADED → MOVING_LOADED → WAITING_PLC
  → MOVING_LOADED → RETURNING → IDLE. Eski `simulate_steps:=true` stub kaldırıldı;
  testte `task_source:=mock_plc test_only_lift:=true` kullanılır.
- Gerçek PLC protokolü gelince aynı servis imzaları korunur; `mock_plc` değişir

### IMU (30.07 — ekip ekledi, Orange Pi'de henüz görünmüyor)
EKF yolu hazır: `imu:=true` → `ekf_imu.yaml` + `imu_filter_madgwick`.
Beklenen topiikler: `/imu/data_raw` → madgwick → `/imu/data` → EKF (vyaw + ax).
Donanım sürücüsü yazılana kadar: `ros2 run marco_localization fake_imu.py`
**Model/bağlantı (USB/I2C/adres) söylenince gerçek sürücü bağlanacak.**
Şu an `lsusb`/`ttyUSB*` yalnız LiDAR CP210x; I2C'de tipik MPU/BNO adresi boş.

### AMCL — harita lokalizasyonu (✅ boru 29.07)
```
ros2 launch marco_localization amcl.launch.py sahte:=true lidar:=true harita:=oda_test
ros2 run marco_localization baslangic_poz.sh 0 0 0          # veya launch'ta baslangic:=true
ros2 run marco_localization amcl_poz_kaydet.py --sure 60    # CSV kayit
```
- Config: `amcl.yaml` — DifferentialMotionModel, Tmini Pro 12 m, IMU yok → alpha↑
- TF: `map→odom` AMCL, `odom→base_footprint` EKF
- **mapping ile aynı anda çalışmaz** (ikisi de map→odom yazar)
- `map→odom` yalnızca `/scan` geldikten sonra yayınlanır
- Doğrulandı: harita yükleniyor (31×54 @5cm), AMCL active, `Setting pose` OK
- LiDAR `0x202` olursa USB çıkar-tak; aksi halde tarama yok → TF yok

### slam_toolbox — haritalama (✅ 29.07)
```
ros2 launch marco_localization mapping.launch.py sahte:=true lidar:=true
ros2 run teleop_twist_keyboard teleop_twist_keyboard   # ayri terminal
ros2 run marco_localization harita_kaydet.sh <isim>    # ayri terminal
```
- Config: `marco_localization/config/slam_toolbox.yaml` (Tmini Pro 12 m, 5 cm hücre)
- Launch: EKF + LiDAR + `async_slam_toolbox_node` → TF `map→odom`
- Kayıt: `src/marco_navigation/maps/<isim>.{pgm,yaml}` (install'a YAZMA)
- Doğrulandı: `/map` yayınlanıyor, `map→odom` çözülüyor, `oda_test` kaydedildi
- slam açıkken `/scan` ~9 Hz (arada 1.5 s boşluk olabilir). RViz AÇMA.
- **pwm_bridge ile aynı anda çalışmaz** — mapping `base_driver` ister (`/odom`)
- **Sahte odom + sabit LiDAR ile teleop YANLIŞ harita üretir** (odom hareket,
  tarama sabit). Gerçek harita için araç (veya LiDAR+encoder) birlikte hareket etmeli.

### Sahte donanımla doğrulanan ölçümler (26.07)
| Ölçüt | Sonuç |
|---|---|
| Düz 2 m, odometri↔gerçek | **0.2 mm** |
| Kare 1×1 m kapanma (kusursuz taklit) | 1.3 / 1.7 mm |
| `/odom` hızı | 100.0 Hz |
| Haberleşme kesilince durma mesafesi @0.838 m/s | **23 cm** |

### odometry_check.py — kalibrasyon aracı
`ros2 run marco_localization odometry_check.py --test {duz|donus|kare|hepsi}`

Manevralar **kapalı çevrim** (odometriye göre) + savrulma düzeltme aşamalı. Açık
çevrimde (süre hesabıyla) sürmek YANLIŞ ölçüm verir: motor rampası yüzünden eksik
kalan mesafe odometri hatası sanılır.

Ölçtüğü şey: odometrinin *inandığı* hareket ile *gerçekleşen* hareket farkı.
Robot manevrayı kusurlu yapsa bile odometri doğru olabilir; ikisi ayrı şeyler.

**Ayırt etme kuralı — taklide bilinen hata enjekte edilip DENEYSEL doğrulandı:**
| Hata | Açı hatası imzası | Ölçülen |
|---|---|---|
| `wheel_separation` yanlış (0.520 sanılıp gerçekte 0.500) | iki yönde **ZIT** işaret | +14.43° / −14.47° → araç 0.49994 önerdi (gerçek 0.500) |
| Tekerlek yarıçapları farklı (sağ %2) | iki yönde **AYNI** işaret | −12.16° / −5.15° |

Sezgi tersini söylüyor, kuralı ezberden yazma — tablo ölçümden geliyor.
Mantığı: teker arası hatası yalnızca dönüşlerde etkir ve araç gittiği yönde fazladan
döner (yön değişince işaret değişir); yarıçap farkı düz kısımlarda sabit bir kavis
yapar ve kavsin yönü karenin sürülme yönünden bağımsızdır.

**Geçerlilik koşulu:** UMBmark, robotun *odometrisine göre* başlangıca dönmüş olmasını
varsayar. Araç bunu denetliyor; odometrinin kendi kapanması ölçülen gerçek hataya
göre büyükse tanıyı atlıyor. Yarıçap hatası durumunda düz kısımlarda **yön koruma**
şart, yoksa odometrinin inandığı yol kare olmaz (111 mm → 7.4 mm'ye düştü).

Gerçek robotta `/base/ground_truth` olmayacak → kapanma **şerit metreyle** ölçülüp
karşılaştırılacak. Araç bu durumda tanı yapmaz, yöntemi hatırlatır.

## CAD ÖLÇÜMLERİ — SolidWorks montajı (28.07)

Kaynak: `~/Downloads/STL/STL`, 100 parça, binary STL, montaj koordinatlarında
ihraç edilmiş (konumlar mutlak). Betikler `marco_description/scripts/stl_*.py`.

**CAD eksenleri:** x = genişlik, y = yükseklik (yukarı +), z = uzunluk.
**Zemin:** y = 13.778 (sarhoş teker teması, montajın en alt noktası).
**Tahrik aksı:** z = 1171.95, gövde orta ekseni x = 365.40.

| Parametre | Eski (tahmin) | **Ölçülen** | Not |
|---|---|---|---|
| `wheel_radius` | 0.100 | **0.100** | kusursuz silindir, kabuk saçılımı 0.000 mm |
| `wheel_width` | 0.050 | **0.050** | |
| **`wheel_separation`** | 0.520 | **0.460** | **%13 hata — düzeltildi** |
| `total_length` | 1.536 | **1.637** | rapor 1536 diyor, CAD 1637 |
| `body_width` | 0.650 | **0.655** | |
| `total_height` | 0.550 | **0.545** | zeminden |
| `body_length` | 0.756 | **0.950** | şasi z 696.9..1646.9 |
| `fork_length` | 0.780 | **0.556** | |
| `fork_tine_width` | 0.090 | **0.100** | |
| `fork_tine_spacing` | 0.300 | **0.250** | |
| `caster_y` | 0.260 | **0.200** | tahrik tekerleri ±230, sarhoşlar içte |
| `ground_clearance` | 0.030 | **0.022** | en alçak sabit nokta: çatal altı |

**`wheel_separation` neden kritikti:** açısal hız `(v_sağ − v_sol)/L`. L %13 büyük
sanılınca odometri her dönüşü %11.5 eksik sayar — gerçek 101.7° dönüş 90° olarak
raporlanır. Şartnamenin ±5° yön toleransı **tek dönüşte** aşılıyordu.

**Tahrik üniteleri YAYLI.** 4 adet helezon yay (3 mm tel, Ø20 mm sarım, 75 mm
serbest boy), aksın üzerinde. CAD'de tahrik tekeri zeminden **11.5 mm yukarıda**
duruyor — bu hata değil, yayın serbest konumu; araç ağırlığı altında basıyor.
Sonucu: etkin yarıçap yük altında değişebilir, `odometry_check.py` ile ölçülmeli.

**Yerleşim:** çatallar z 11.6..567 → direk (mast, dikey U-profil + Ø20 lineer mil,
400 mm kurs) z≈620 → şasi z 697..1647. Tahrik tekerleri ortada (z=1172),
4 sarhoş teker aksın 320 mm bir yanında ve 340 mm öbür yanında. Akü z 1314..1560.

**Çatal ucu tahrik aksından 1160 mm uzakta** ve altında teker yok (en yakın sarhoş
teker 320 mm ötede). Yüklü haldeki devrilme momenti mekanik ekibin sorunu ama
Nav2 ayak izi bu 1160 mm çıkıntıyı içermek zorunda.

**LiDAR ve kameralar CAD'de YOK** — rapor 3D baskı tutucudan bahsediyor ama
ihraç edilmemiş. Montaj konumları hâlâ ölçüm bekliyor.

### ÖN YÜZ PANEL KESİKLERİ (29.07, STL'den ölçüldü)
Kullanıcı SolidWorks ekran görüntüsüyle LiDAR ve kamera yerlerini işaretledi.
Panel kesikleri STL'de mevcut olduğu için ölçülebildi.
Betik: `marco_description/scripts/stl_on_yuz_haritasi.py` (dış yüz üçgenlerini
dolu çizip rasterler, kenara bağlı olmayan boşlukları kesik sayar).

Ön yüzün dış yüzü **x_urdf = +476.5 mm**. `ÖnAltKapak-1` panelindeki kesikler:

| kesik | boyut | merkez y | zeminden z | ne |
|---|---|---|---|---|
| 1 | 60 × 54 mm | +0.3 | **191.5** | **ön kamera** ✅ |
| 2 | 70 × 90 mm | −138.7 | 93.5 | sarhoş teker açıklığı |
| 3 | 70 × 90 mm | +137.3 | 93.5 | sarhoş teker açıklığı |

→ `camera_front_z = 0.1915 − 0.100 = 0.0915` (base_link aks yüksekliğinde).
Eski tahmin 0.350 idi, **26 cm sapma**. Kameranın zeminde gördüğü alan
yükseklikle ölçekleniyor, şerit takibi kalibrasyonu buna bağlı.

`Arka-1` panelinde kamera açıklığı YOK; sadece y=−130 / z=373.5'te 10 × 30 mm
bir yarık var. Arka kamera hâlâ simetri varsayımı.

`ÜstKapak-2` üzerindeki iki büyük oval + eğik ızgara + MARCO logosu,
kullanıcının fotoğrafındaki üst bölgeyi doğruluyor — panel eşleşmesi kesin.

Fotoğrafta işaretlenen üç küçük çizgi STL'deki hiçbir şeyle örtüşmüyor; ön
panellerde bulunan 4–6 mm delikler panel bağlantı vidaları (z=299.5 ve
z=379.5'te y=−234.7/−74.7/+74.3/+234.3, yani 160 mm aralıklı). LiDAR tutucusu
bu ihraçta yok.

### LiDAR KARARI (29.07, kullanıcı) — ÜSTTE, 360° ENGELSİZ
Kullanıcı önce ön dikey paneli işaretledi; ön panel montajı taramanın arka
yarısını gövdeyle kapatacağı (~180°) ve panelin ~3 cm'de sahte engel halkası
olarak görüneceği söylendi. Kullanıcı kararı: **şimdilik LiDAR tepede kabul
edilsin, 360° görsün.** Sektör maskeleme (`ignore_array`) ve geri sürüş
körlüğü konuları GÜNDEMDEN ÇIKARILDI — tekrar açma.

Üst kapağın düz üst yüzeyi ÖLÇÜLDÜ: zeminden **544.5 mm** (`ÜstKapak-2` ve
`DM_Üst-1` üst yüzleri aynı düzlemde). Tmini Pro gövdesi 33 mm → tarama
düzlemi yüzeyin ~20 mm üzerinde.

Bu 29.07 yerleşim kararı, 11.08 kullanıcı fiziksel ölçümüyle geçersiz olmuştur.
Güncel montaj: `lidar_x=+0.350`, `lidar_y=0`, `lidar_z=+0.350`
(`base_link`e göre); tarama düzlemi zeminden `0.450 m`. Fiziksel montaj
değişirse yeniden ölçülmelidir.

### İLERİ YÖN KARARI (28.07, kullanıcı onayladı)
**+x = GÖVDE tarafı. Çatallar ARKADA.**

Mekanik ekibin adlandırmasıyla uyumlu ("Ön" kapaklar gövde ucunda, CAD z≈1648)
ve şartname madde 6 ile de tutarlı: *"yükü aldıktan sonra taşıma, yük hareket
yönün tersi tarafta olacak şekilde devam etmelidir."*

**CAD → URDF dönüşümü** (CAD mm cinsinden):
```
x_urdf = (z_cad - 1171.95) / 1000     ileri +
y_urdf = (x_cad -  365.40) / 1000     sol +
z_urdf = (y_cad -   13.778) / 1000    yukarı +
```
Sonuçları CAD nokta bulutu URDF çerçevesine taşınıp model üstüne bindirilerek
görsel olarak doğrulandı: `scripts/urdf_cad_dogrula.py`.

| Çerçeve | Konum (base_link'e göre) |
|---|---|
| `base_link` | tahrik aksı ortası, zeminden 0.100 |
| sol / sağ tahrik tekeri | x=0, y=**+0.230 / −0.230** |
| ön sarhoş tekerler | x=**+0.340**, y=±0.200 |
| arka sarhoş tekerler | x=**−0.320**, y=±0.200 |
| çatal kökü | x=**−0.605** (dişler oradan −x'e uzanır) |
| çatal ucu | x=**−1.160** |
| gövde ön yüzü | x=**+0.476** |

CAD'de sol teker x_cad=595.40, sağ teker x_cad=135.40 — yani STL örneği
`00_00-2` SOL, `00_00-1` SAĞ. Sezginin tersi, dikkat.

### NAV2 İÇİN İKİ KRİTİK SONUÇ
**1. Ayak izi çok asimetrik.** Ölçülen dış sınırlar base_link merkezli:
`x −1.160 … +0.476`, `y −0.327 … +0.328`. base_link'in 1.16 m **arkasına**,
yalnızca 0.48 m önüne uzanıyor. Dairesel ayak izi kesinlikle kullanılamaz;
merkezi olmayan poligon şart.

**2. Nav2 GERİ SÜRÜŞ yapmak zorunda.** Şartname madde 6 taşımanın gövde
önde (ileri) yapılmasını istiyor, ama madde 5 yükü alırken çatalın paletin
içine girmesini gerektiriyor — o manevra **−x yönünde**. Tek yönlü bir
planlayıcı/kontrolcü yapılandırması YETERSİZ. Yük alma fazında geri sürüş
gerekiyor ve şerit takibi arka kameradan yapılacak.

**Çatal ucunun altında teker yok** (en yakın sarhoş teker 320 mm ötede,
çatal ucu aksın 1160 mm gerisinde). Devrilme momenti mekanik ekibin konusu,
ama ayak izi bu çıkıntıyı içermek zorunda.

## AÇIK SORULAR (cevap gelince buraya yaz)
- [x] ~~Simülatör kararı~~ → WSL2 Ubuntu 22.04 + Gazebo Fortress/ros_gz; Faz 2 doğrulandı 02.08
- [ ] Encoder redüktör öncesi mi sonrası mı? → tick katsayısı
- [x] Fiziksel ve odometri wheel separation **0.460 m**. Önceki **0.421 m**,
      düzeltilmekte olan STM32 verisiyle türetilmişti; firmware sonrası tekrar
      fiziksel kabul yapılacak.
- [x] ~~`base_link` orijini~~ → tahrik aksı ortası, CAD z=1171.95 (şasinin tam ortası)
- [x] ~~İleri yön~~ → gövde tarafı +x, çatallar arkada (28.07)
- [x] **LiDAR montaj konumu** — 11.08 kullanıcı fiziksel ölçümü:
      x=+0.350, y=0, z=+0.350 (`base_link`), tarama zeminden 0.450 m.
- [x] **Ön kamera konumu** — ÖLÇÜLDÜ 29.07: x=+0.4765, y=0, zeminden 0.1915
      (`camera_front_z=0.0915`). Panel kesiğinden, bkz. ÖN YÜZ PANEL KESİKLERİ.
- [ ] Arka kamera konumu (CAD'de açıklık yok; simetri varsayıldı)
- [ ] Yük altında etkin tekerlek yarıçapı — tahrik üniteleri yaylı, lastik ezilmesi
      yarıçapı düşürebilir. `odometry_check.py --test duz` ile ölçülmeli.
- [ ] PLC protokolü (TEKNOFEST ön aşama sonrası verecek)
- [ ] Şarj istasyonu detayları (TEKNOFEST yayınlayacak)
- [ ] **IMU model + bağlantı** — ekip ekledi (30.07); Orange Pi'de henüz
      görünmüyor. Model (MPU/BNO/ICM/Wit…) ve I2C/USB adresi lazım.
      Yazılım yolu `imu:=true` + `fake_imu.py` ile hazır.
- [ ] **Watchdog süresi 200 ms kalsın mı?** Ölçüldü: haberleşme kesildiğinde araç
      0.838 m/s'de **23 cm** kör yol alıyor (200 ms watchdog + 80 ms motor sabiti).
      Şartname rota sapmasını 10 cm'de sınırlıyor. Elektronik ekibiyle konuşulup
      100 ms'e indirilmesi veya güvenlik bölgelerinin bu mesafeye göre boyutlanması
      gerekiyor. Test bunu kilitliyor:
      `test_haberlesme_kesintisi_durma_mesafesi_butcesi` (sınır 25 cm).

## TUZAKLAR
- **USB kamera: `cv2.VideoCapture(0)` ÇALIŞMAZ, `cv2.VideoCapture(0, cv2.CAP_V4L2)`
  yaz.** Varsayılan GStreamer arka ucu bu kamerada pipeline kuramıyor
  (`v4l2src ... Internal data stream error`) ve tek kare bile gelmiyor. Belirtisi
  sessiz: düğüm sadece "kare alınamadı" basıp durur. Ayrıca kamera **320x240
  DESTEKLEMİYOR** — MJPG'de en küçük 640x480, YUYV'de yalnız 640x360
  (`v4l2-ctl -d /dev/video0 --list-formats-ext`). Desteklenmeyen boyut istenince
  format anlaşması çöker ve yine hiç kare gelmez.
- **Kamerayı aynı anda tek süreç açabilir.** Test başlatmadan önce
  `fuser -v /dev/video0` ile kontrol et; arka planda unutulmuş bir `tracker`
  varsa yeni süreç sessizce boş kare alır.
- **`/scan` QoS'u BEST_EFFORT.** Varsayılan (RELIABLE) abonelikle *hiç* mesaj gelmez;
  ROS yalnızca "incompatible QoS" uyarısı verir, topic `ros2 topic hz` ile canlı
  görünür. Abone olurken `qos_profile_sensor_data` kullan. slam_toolbox ve Nav2
  bunu kendileri doğru yapar, elle yazılan kontrol/test betikleri yapmaz.
- **YDLidar düğümünün adı değiştirilemez.** YAML parametreleri düğüm adıyla eşlenir;
  `name="ydlidar"` verilince `ydlidar_ros2_driver_node:` bloğu hiç uygulanmaz ve SDK
  kendi gömülü varsayılanına düşer → `cannot bind to [serial port:/dev/ydlidar]`.
  Belirtisi kafa karıştırıcı: YAML'de `/dev/ttyUSB0` yazarken hata `/dev/ydlidar` der.
- **Tmini Pro'da `intensity: true` yapma.** Sürücü "automatically adjusted to [0]bit"
  diyerek geri döner ve o sırada çerçeve boyunu yanlış hesapladığı için sürekli
  `Checksum error` üretir. `intensity: false` ile açılışta 11 hata olur, sonra sıfır.
- **`internal error [0x202]` / `health status bad`**: LiDAR önceki oturumdan kötü
  durumda kalmış. USB'yi fiziksel olarak çıkar-tak. Yazılımdan düzelmiyor.
- **AMCL + slam mapping aynı anda çalışmaz.** İkisi de `map→odom` yayınlar.
- **AMCL `map→odom` yayınlamıyor** → büyük ihtimalle `/scan` gelmiyor.
  Önce `ros2 topic hz /scan`. LiDAR `0x202` ise USB çıkar-tak.
  Başlangıç pozu verildi ama tarama yoksa TF oluşmaz (normal).
- **Mapping + pwm_bridge aynı anda çalışmaz.** pwm_bridge `/odom` yayınlamaz;
  slam_toolbox odometri ister. Ayrıca ikisi seri portu paylaşamaz. Mapping öncesi
  `pkill -f 'pwm[_bridge]|marco_pwm'`.
- **Sahte odometriyle teleop edip LiDAR sabitken harita çıkarma.** Odom hareket
  eder, tarama etmez → slam duvarları sürükler. Ya gerçek araç yürüsün, ya
  LiDAR'ı odom ile tutarlı hareket ettir.
- **Haritayı `install/.../maps`'e kaydetme.** `harita_kaydet.sh` artık
  `src/marco_navigation/maps/` yazar. install'a yazılan dosya colcon rebuild ile
  kaybolabilir / src'ye düşmez.
- **`Package 'marco_bringup' not found`** → terminal workspace'i source etmemiş.
  28.07'de `~/.bashrc`'ye kalıcı olarak eklendi (humble → ydlidar_ros2_ws →
  marco_ws sırasıyla, dosya varlık kontrolüyle). Artık yeni terminaller hazır
  geliyor; o an açık olan terminaller için `source ~/.bashrc` gerekiyor.
- **`ros2 bag record`'u betik içinden çağırırken `< /dev/null` ŞART.**
  Kayıtçının "SPACE ile duraklat" özelliği terminal ayarlarını değiştiriyor
  (`tcsetattr`). Betik `ros2 run` altında arka plan süreç grubunda çalıştığı
  için terminale dokunduğu anda çekirdek **SIGTTOU** gönderip süreci
  donduruyor: `/proc/<pid>/status` → `State: T (stopped)`, veritabanı hiç
  oluşmuyor, **hiçbir hata mesajı çıkmıyor**. Ekranda sadece "Kayit basliyor"
  kalıyor ve komut sonsuza kadar asılı duruyor. `timeout` SIGINT gönderse bile
  durmuş süreç yanıt vermiyor.
  Teşhiste tuzak: tty'siz kabukta (Cursor'ın Shell aracı, CI, `nohup`) sorun
  ÜREMİYOR — orada testler geçiyor, kullanıcının terminalinde patlıyor.
  Doğrulamak için `script -qec "komut" /dev/null` ile pty tahsis et.
- **Kayıt komutunu launch'un çalıştığı terminale YAZMA.** O terminal komutu
  çalıştırmaz, girdi tamponunda bekletir; Ctrl+C ile launch kapanınca komut
  ancak o zaman çalışır ve robot çoktan ölmüştür. Sonuç: içinde tek bir
  `/tf_static` mesajı olan, süresi 0 saniye olan boş kayıt. Böyle bir kaydı
  `ros2 bag play --loop` ile oynatmak sonsuz döngüye girer ve ekranı
  `Opened database ... READ_ONLY` satırlarıyla doldurur — hata mesajı vermez,
  bu yüzden sebebi anlaşılmıyor. Bunu önlemek için
  `ros2 run marco_bringup kayit_al.sh [sure] [isim]` kullan: önce topiklerin
  gerçekten yayında olduğunu doğruluyor, değilse açıklama yapıp çıkıyor.
- **RViz testi için `viewer.launch.py` kullan** (28.07 eklendi, test edildi).
  Yalnızca `robot_state_publisher` + `rviz2` başlatır, sürücü/sensör açmaz.
  Kayıttan oynatma akışı doğrulandı: araç hareket ederken RViz hiç açılmaz,
  sadece `ros2 bag record` alınır; sonra `viewer.launch.py sim:=true` +
  `ros2 bag play --clock` ile izlenir. Böylece ölçüm doğruluğu bozulmaz.
  13 sn kayıt = 2.7 MB, `/scan` 10 Hz ve `/odom` 100 Hz eksiksiz korunuyor.
  `sim:=true` kullanıp `--clock` vermezsen TF gelecekten gelmiş görünür ve
  RViz hiçbir şey çizmez.
- **RViz'i Orange Pi ÜZERİNDE çalıştırma.** İki kez ölçüldü: RViz **%244–312 CPU**
  alıyor ve LiDAR sürücüsünü açlığa sokuyor — `/scan` 9.96 Hz'den **4.3–6 Hz'e**
  düşüyor, ardarda **3.3 saniyelik** boşluklar oluşuyor. 0.838 m/s'de bu ~2.8 m kör
  yol demek; yarışmada kabul edilemez.

  **Hata imzası — bunları görünce LiDAR'ı değil CPU'yu suçla:**
  ```
  [error] Timeout count: 1/2/3
  [error] [YDLIDAR]: -1 Operation timed out
  [ERROR] ... Failed to get scan
  [warn]  Real points 489 > fixed points 430
  [rviz2] Message Filter dropping message ... queue is full
  ```
  Mesajlar sürücüden geldiği için insan LiDAR arızası sanıyor; kablo/port
  değiştirmeye kalkışmak zaman kaybı. RViz'i kapatınca aynı saniyede düzeliyor.
  (`Real points > fixed points`: okumalar geciktiği için sürücü bir turun daha
  uzun sürdüğünü sanıyor ve `fixed_resolution: true` ile sabitlenen 430 noktalık
  çerçeveye sığmıyor. `fixed_resolution: false` uyarıyı susturur ama sorunu
  çözmez, örtbas eder.)

  `robot.launch.py` artık `lidar:=true rviz:=true` birlikte verilirse açılışta
  yüksek sesli uyarı basıyor. Doğru yol: `viewer.launch.py` + rosbag.

  **KÖK NEDEN (28.07 bulundu): RViz bu kartta GPU KULLANMIYOR.**
  `glxinfo` → `OpenGL renderer: llvmpipe`, yani tamamen CPU'da yazılım
  render. Sebebi düzeltilebilir değil: Mali çekirdek sürücüsü yüklü
  (`/dev/mali0` var) ve `libmali-valhall-g610` kurulu, ama o blob yalnızca
  **OpenGL ES 3.2** sunuyor. RViz/Ogre ise masaüstü OpenGL 3.3+ istiyor,
  GLES ile çalışmıyor → Mesa `llvmpipe`'a düşüyor. DRM düğümleri de yalnızca
  `rockchip-drm` (ekran) ve `RKNPU`; Mali için DRM render düğümü yok.
  Sonuç: **Orange Pi üzerinde RViz her zaman pahalı olacak**, ayar
  değiştirerek kurtarılamaz. Bu yüzden uzak makine veya kayıt-oynat tek yol.
- **`joint_state_publisher` ile `base_driver` AYNI ANDA çalışmaz.** İkisi de
  `/joint_states`'e yazar, robot_state_publisher karışık alır, TF gerçek tekerlek
  dönüşünü göstermez. Belirtisi: `/joint_states` hızı 100 yerine ~121 Hz.
  `joint_state_publisher` YALNIZCA `marco_description/display.launch.py` içinde
  (modeli elle kurcalamak için). `robot.launch.py` onu bilinçli olarak başlatmaz.
- **`publish_tf` çakışması**: sürücü `publish_tf` default **true** (`robot.launch.py`
  doğrudan çalıştırıldığında EKF yok, sürücü TF yayınlar). `localization.launch.py`,
  `robot.launch.py`'yi `tf:=false` ile çağırır → EKF yayınlar. İkisini aynı anda
  başlatma. **Zaten yapılandırıldı ve doğrulandı**: `localization.launch.py` altında
  `/tf`'de yalnızca EKF kaynağı var.
- `base_driver.yaml` ile `properties.xacro` kinematik değerleri **birlikte** güncellenmeli.
  Ayrışırlarsa odometri ile TF çelişir; hata Nav2 seviyesinde tuhaf davranış olarak
  çıkar, kaynağı zor bulunur.
- launch'ta `robot_description` için `ParameterValue(Command([...]), value_type=str)`
  şart; yoksa launch URDF'i YAML sanıp ayrıştırmaya çalışır ve hata verir.
- pytest'i **paket dizininden** çalıştır (`cd src/marco_base`); kökten çalıştırılırsa
  flake8 `install/` altını tarar ve düşer.
- `pkill -f <desen>` kabuğun KENDİ komut satırıyla eşleşip kendini öldürür (çıktı boş
  gelir, komut 150 ms'de "biter"). Desende köşeli parantez kullan (`base[_]driver`)
  VE aynı komutta o adı bir daha yazma.
- Rapordaki 1.46 m/s'i Nav2'ye YAZMA → 0.838 m/s tavan
- Dairesel ayak izi kullanma → araç 1.5m uzunluğunda
- Nav2 varsayılan BT engelde yeniden planlar → şartnameye AYKIRI, değiştir
- IMX219 MIPI CSI, RK3588'de device tree overlay ister; şu an `/dev/video*` yalnızca
  donanım codec (video-dec0/enc0), kamera YOK → yedek plan USB kamera
- RPLIDAR ve kameralar şu an fiziksel olarak BAĞLI DEĞİL
- Donanım henüz yok → önce simülasyon
