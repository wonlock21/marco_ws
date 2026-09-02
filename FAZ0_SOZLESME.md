# Faz 0 — Kaynak, Araç ve Entegrasyon Sözleşmesi

> Durum tarihi: 22.08.2026
>
> ROS başlangıç HEAD: `9d5fd47` (`main`)
>
> Flutter referans HEAD: `46ac767` (`main`)
>
> Durum: Faz 0 kapsamındaki yazılım sözleşmesi hazır; `lane_tracking`, fiziksel
> kabul ve dış bağımlılıklar açık.

## 1. Yarışma kaynağı

- Takım hareket ve kabiliyet videosunu geçmiş ve finalist olmuştur.
- Bağlayıcı teknik taban: TEKNOFEST 2026 Sanayide Robotik Uygulamalar
  Yarışması V1.1, 20.05.2026.
- V1.1 SHA-256: `8c834979f5e2572deaff3074f5846c760d15e14fec07da7c4f053e1486dd6f24`.
- Kullanıcıdaki V1.0 SHA-256:
  `2c7adb7dd6d1418909cb92e3e4f38051d43d7b7df6967ff1a82fb004c82a9a84`.
- Final: 18–20.09.2026, Mezopotamya Uluslararası Fuar ve Kongre Merkezi.
- PLC wire protokolü henüz takıma verilmemiştir. Protokol gelmeden IP/port,
  register, paket alanı, timeout veya ACK biçimi uydurulmayacaktır.

## 2. Kanonik araç değerleri

`src/marco_bringup/config/vehicle_contract.yaml` makine tarafından denetlenen
tek sözleşmedir.

| Parametre | Kanonik değer | Kaynak/durum |
|---|---:|---|
| Teker yarıçapı | `0.100 m` | CAD/fiziksel; yük altında tekrar ölçülecek |
| Encoder | `360 tick/tur` | STM32 yönlü/kümülatif çıktı; yeniden ×4 yok |
| Geometrik teker aralığı | `0.460 m` | Fiziksel/CAD |
| Odometri teker aralığı | `0.460 m` | 22.08 kararı; firmware sonrası fiziksel kabul bekliyor |
| Footprint | `x=-1.20..+0.50 m`, `y=-0.35..+0.35 m` | Nav2 ve Collision Monitor sözleşmesi |
| `base_link` yüksekliği | `0.100 m` | `base_footprint` referanslı |
| LiDAR, `base_link` | `[+0.270, 0.000, +0.200] m` | 02.09 kullanıcı fiziksel ölçümü |
| LiDAR tarama düzlemi | `0.300 m` | Zemine göre |

Önceki `0.421 m` odometri değeri, düzeltilmekte olan STM32 verileriyle
yapılan 360° hesaplarından türemiştir ve aktif sözleşmeden çıkarılmıştır.
Firmware düzeltmesi tamamlandıktan sonra `0.460 m`; iki yönde 360° dönüş,
10 m düz sürüş ve ham tick/yaw bag’iyle yeniden doğrulanacaktır. Sonuç uygun
değilse sayı yalnız tarihli ham veri ve ölçüm raporuyla değiştirilebilir.

Tek doğrulama komutu:

```bash
python3 src/marco_bringup/scripts/check_vehicle_contract.py
```

Kurulumdan sonra eşdeğer komut:

```bash
ros2 run marco_bringup check_vehicle_contract.py --workspace /home/emre/marco_ws
```

Denetim; base driver, PWM bridge, lane tracking, URDF, LiDAR TF, iki Nav2
footprint’i ve Collision Monitor stop bölgelerini birlikte kontrol eder.

## 3. Sensör ve TF durumu

- TF sahibi: sabit dönüşümler `robot_state_publisher`, `map→odom` AMCL,
  `odom→base_footprint` EKF.
- Ön kamera ölçümü: `x=+0.4765 m`, `y=0`, `base_link z=+0.0915 m`;
  zeminden yaklaşık `0.1915 m`.
- Arka kamera konumu halen simetri varsayımıdır; fiziksel ölçüm gerekir.
- Kamera eğimi yaklaşık 45° tahmindir; kalibrasyon kabulü değildir.
- Gerçek kamera modu/çözünürlüğü donanım üzerinde yeniden sorgulanacaktır.
- Bu WSL çalışma ortamında `/dev/ttyACM*`, `/dev/ttyUSB*`, `/dev/video*` veya
  `/dev/mali*` aygıtı görünmemiştir; cihaz/udev envanteri robot üzerinde alınacaktır.

## 4. Lift ve yük

- Kullanıcı doğrulamasına göre lift mekanizması ve limit sensörleri fiziksel
  olarak çalışmaktadır.
- STM32 durum telemetrisi `fork_state` alanını ve base driver fork joint
  durumunu sağlar.
- `marco_msgs/action/LiftLoad` sözleşmesi vardır.
- Üretim `LiftLoad` action sunucusu henüz yoktur; mevcut test sunucusu gerçek
  donanım kabulü değildir.
- Faz 1 öncesi alt/üst limit, timeout, iptal, e-stop, overcurrent ve yük
  var/yok semantiği action sonucuna bağlanacaktır.
- Şartname kabulü 5 kg ile ölçümlü kaldırma, taşıma, frenleme ve bırakmadır.

## 5. Flutter–ROS baseline

- Flutter proje yolu: `/mnt/c/Users/emre/desktop/liftant_v2_bitirme`.
- İncelenen referans commit: `46ac767`; inceleme anında çalışma ağacı önceden
  kirliydi (131 durum satırı). Kullanıcı değişiklikleri korunacak, kör kopyalama
  veya reset yapılmayacaktır.
- Mevcut temel: rosbridge WebSocket/reconnect, `/robot_status` bayatlık kilidi,
  fiziksel manuel mod olmadan `/cmd_vel_manual` reddi, mapping/lokalizasyon,
  harita önizleme, node/route ekranları ve görev/PLC özet kartları.
- Eksik backend: `/stations/*` ve `/routes/*` işlemleri stub/yerel draft,
  lift kontrolü pasif, gerçek PLC veri kaynağı yoktur.
- GUI’de son “GELEN/GÖNDERİLEN” alanları vardır; yarışma kabulünde zaman
  damgalı ve yönü belli sınırlı mesaj geçmişi tercih edilecektir.
- ROS ve Flutter kabul sürümleri aynı release kaydında birlikte tutulacaktır.

## 6. Üretim sahipliği

- Rota yürütme: Mission Manager + Nav2 Route Server; gerçek graph tek kaynaktır.
- `/route_speed_limit`: Route Server `AdjustSpeedLimit`.
- `/speed_limit`: yalnız `speed_limit_manager`.
- Nav2 hareketi: `/cmd_vel_raw`.
- Güvenli hareket: Collision Monitor ve twist mux üzerinden taban sürücüsü.
- Doğrudan taban hız komutu veren geliştirme launch’ları yarışma profili değildir.
- Harita: SLAM Toolbox; lokalizasyon: EKF + AMCL.
- Saha verisi: çalışma zamanında `~/marco_data/fields/<field>`; package share
  içindeki harita/graflar yalnız örnek/testtir.
- PLC transport: protokol geldiğinde mission manager’dan ayrı adaptör.
- GUI: karar/TF/rota hesabı sahibi değil, ROS API istemcisi ve izleme arayüzü.

## 7. Donanım envanteri — robot üzerinde tamamlanacak

| Bileşen | Beklenen kaynak | Faz 0 durumu |
|---|---|---|
| STM32 | base config `/dev/ttyACM0`; PWM config `/dev/marco_stm32` | Tek kalıcı udev yolu doğrulanmalı |
| YDLidar Tmini Pro | lidar launch/config | Port, USB kimliği ve yedek kablo kaydedilmeli |
| Ön kamera | varsayılan `/dev/video0` | USB kimliği, desteklenen mod ve kalibrasyon kaydedilmeli |
| Arka kamera | konum/model açık | Fiziksel ölçüm ve kalıcı device path gerekli |
| Mali GPU | `/dev/mali0`, `python3-pyopencl` | WSL’de yok; Orange Pi’de sürücü/OpenCL testi gerekli |
| Lift/limit | STM32 `fork_state` + komut protokolü | Donanım çalışıyor; action entegrasyonu eksik |
| Fiziksel mod/e-stop | STM32 state flags | Truth table ve gerçek kesme testi gerekli |
| Robot PC | Orange Pi | OS image, disk, MAC, saat ve güç kaydı gerekli |
| Kontrol PC | Windows + Flutter | MAC, çevrimdışı build ve release kimliği gerekli |

## 8. Faz 0 kabul kayıtları

Başlangıç ölçümü:

- `colcon build --symlink-install`: **14/14 paket PASS**.
- İlk araç sözleşmesi: **FAIL**, `0.460 != 0.421`; bu sözleşmede tekleştirildi.
- İlk `colcon test`: 70 sonuç içinde 1 error, 3 failure, 5 skipped.
  - `marco_mission`: WSL sandbox log yolu; `/tmp` ROS loguyla tekrar test edilir.
  - `marco_perception`: iki PEP257 docstring biçim hatası.
  - `lane_tracking`: sistemde `python3-pyopencl` yokken modülün koşulsuz importu.

Yeni baseline sonucu:

- Araç sözleşmesi: **PASS**.
- Xacro/URDF: **PASS**, model ağacı `base_footprint` kökünden hatasız ayrıştırıldı.
- Dokunulmamış kaynakla `colcon test-result`: **72 test, 1 error, 0 failure,
  5 skipped**. Tek hata `lane_tracking` test toplamasında bu WSL ortamında
  `pyopencl` bulunmamasıdır; paket kaynaklarına müdahale edilmemiştir.
- Flutter `flutter analyze`: **No issues found**.
- Flutter `flutter test`: **50 PASS, 1 SKIP**. Atlanan test canlı
  `ROS_BRIDGE_URL` gerektirir ve Orange Pi entegrasyonunda çalıştırılacaktır.
- `python3-pyopencl` bu WSL ortamında kurulu değildir. `lane_tracking` başka
  çalışma alanının sorumluluğunda olduğundan kaynak değişikliği yapılmayacaktır;
  bağımlılık ve GPU/OpenCL kabulü ilgili ekipçe Orange Pi üzerinde tamamlanacaktır.

Fiziksel kabuller otomatik test geçişiyle kapatılmaz.

## 9. Faz 0 çıkış kapısı

- [x] Finalistlik doğrulandı.
- [x] V1.1 ve hash’i kaydedildi.
- [x] ROS başlangıç HEAD’i ve Flutter referans HEAD’i kaydedildi.
- [x] 14 paket temiz derlendi.
- [x] `0.460 m` tek yazılım sözleşmesine alındı.
- [ ] Tüm çevrimdışı otomatik testler geçiyor (`lane_tracking` için
  `python3-pyopencl`/hedef donanım kabulü bekleniyor).
- [ ] STM32 firmware düzeltmesi fiziksel araçta yüklendi ve sürüm/hash kaydedildi.
- [ ] 10 m ve iki yön 360° kalibrasyonu yapıldı.
- [ ] Araç dış ölçüleri güncel şartname çizimine göre iki kişiyle ölçüldü.
- [ ] Robot üstünde USB/udev/MAC/donanım seri no envanteri tamamlandı.
- [ ] E-stop ve manuel/otomatik anahtar truth table’ı gerçek donanımda geçti.
- [ ] Lift/limit gerçek action sözleşmesi ve 5 kg test hazırlığı doğrulandı.
- [ ] Final lojistiği, saha test zamanı ve MAC bildirim yöntemi kaydedildi.
- [ ] PLC protokol belgesi geldi veya resmî teslim tarihi/temas noktası belli.

Faz 0, bütün yazılım kontrolleri geçtiğinde “yazılım baseline hazır”; bütün bu
çıkış maddeleri kapandığında “tamamlandı” sayılır.
