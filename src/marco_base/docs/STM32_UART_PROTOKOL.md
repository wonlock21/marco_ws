# Orange Pi 5 ↔ STM32 UART Haberleşme Protokolü

**Sürüm:** 0.6 · **Tarih:** 31.08.2026 · **Hazırlayan:** Yazılım / Navigasyon
**Değişiklikler:** `0x01` hedef birimi işaretli RPM olarak kesinleştirildi.
`STATE_ODOMETRY` uint64 zaman damgası ve IMU yaw ile 24 bayttır; IMU'suz
uint64 geçiş paketi 20 bayt olarak desteklenmeye devam eder.

Bu belge Orange Pi üzerinde çalışan ROS 2 katmanı ile STM32 alt seviye kontrolcüsü
arasındaki seri haberleşmeyi tanımlar. Protokolü navigasyon ekibi belirler çünkü
odometrinin doğruluğu doğrudan burada tanımlanan tick semantiğine bağlıdır;
implementasyon elektronik ekibine aittir.

---

## 1. Fiziksel Katman

| Parametre | Değer | Gerekçe |
|---|---|---|
| Arayüz | UART, TTL 3.3 V | |
| Baud | **115200** | Ortak seri hız; Orange Pi ↔ STM32 veri aktarım protokolü (30.07) |
| Çerçeve | 8N1, akış kontrolü yok | |
| Ortak toprak | **ZORUNLU** | Raporun §7.3'ünde bu eksiklikten kaynaklanan UART hatası kayıtlı |

Orange Pi tarafında bağlantı USB-TTL dönüştürücü (`/dev/ttyUSB*`) veya STM32 Nucleo'nun
ST-Link sanal COM portu (`/dev/ttyACM*`) üzerinden olabilir. Cihaz yolu udev kuralıyla
`/dev/marco_stm32` olarak sabitlenecektir; yeniden başlatmada port numarası değişirse
sistem etkilenmemelidir.

---

## 2. Çerçeve Yapısı

Tüm çok baytlı alanlar **little-endian**'dır.

```
+--------+--------+--------+--------+---------+--------+--------+
| 0xAA   | 0x55   | LEN    | MSG_ID | PAYLOAD | CRC_L  | CRC_H  |
+--------+--------+--------+--------+---------+--------+--------+
   1B       1B       1B       1B      LEN B      1B       1B
```

- `LEN` yalnızca PAYLOAD uzunluğudur (0–64).
- `CRC16` CCITT-FALSE (poly 0x1021, init 0xFFFF), `LEN`, `MSG_ID` ve `PAYLOAD`
  baytları üzerinden hesaplanır. Senkron baytları CRC'ye dahil DEĞİLDİR.
- CRC uyuşmazsa çerçeve sessizce atılır; yeniden gönderim yoktur.

Alıcı, senkron baytlarını arayarak yeniden hizalanır. Kayıp çerçeve bir sonraki
periyotta telafi edilir (bkz. §4.1).

---

## 3. Orange Pi → STM32 Mesajları

### 3.1 `0x01` CMD_WHEEL_RPM — 50 Hz

Kinematik dönüşümü (`/cmd_vel` → tekerlek RPM hedefleri) **Orange Pi yapar**.
Tekerlek ekseni arası mesafe ve yarıçap kalibrasyonu ROS tarafında tutulur.

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | int16 | `left_target_rpm` | RPM, fiziksel ileri pozitif |
| 2 | int16 | `right_target_rpm` | RPM, fiziksel ileri pozitif |
| 4 | uint8 | `flags` | bit0 = motorlar etkin |

Sınır: ±80 RPM (200 mm tekerlekte yaklaşık ±838 mm/s). STM32 bu değeri aşan
komutları kırpmalı ve durum mesajında `FLAG_CMD_CLAMPED` kaldırmalıdır. ROS
`RPM = m/s × 60 / (2πr)` dönüşümünü uygular; 0.100 m yarıçapta 0.1 m/s yaklaşık
9.55 RPM'dir ve kabloda en yakın tam sayı olan 10 gönderilir.

### 3.2 `0x02` CMD_FORK — olay bazlı

| Ofset | Tip | Alan |
|---|---|---|
| 0 | uint8 | `action`: 0=dur, 1=yukarı, 2=aşağı |
| 1 | uint16 | `timeout_ms`, güvenlik üst sınırı |

Limit switch tetiklendiğinde STM32 hareketi kendi kesmelidir; Orange Pi'den onay beklemez.

### 3.3 `0x03` CMD_SAFETY — olay bazlı

| Ofset | Tip | Alan |
|---|---|---|
| 0 | uint8 | `command`: 0=normal, 1=yazılımsal acil duruş, 2=hatayı temizle |

Yazılımsal acil duruş, donanımsal e-stop butonunun **yerine geçmez**, ona eklenir.

### 3.4 `0x05` CMD_HEARTBEAT — 10 Hz

Boş yük. Bkz. §5 watchdog.

---

## 4. STM32 → Orange Pi Mesajları

### 4.1 `0x81` STATE_ODOMETRY — 100 Hz

Bu, protokolün en kritik mesajıdır. Odometrinin tamamı buradan türetilir.

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | uint64 | `timestamp_us` | STM32 açılışından beri geçen mikrosaniye |
| 8 | int32 | `left_ticks` | **işaretli, yönlü ve kümülatif** encoder tick sayacı |
| 12 | int32 | `right_ticks` | **işaretli, yönlü ve kümülatif** encoder tick sayacı |
| 16 | int16 | `left_speed` | işaretli mm/s, fiziksel ileri pozitif |
| 18 | int16 | `right_speed` | işaretli mm/s, fiziksel ileri pozitif |
| 20 | float32 | `imu_yaw` | derece; araç düzlemindeki göreli yaw |

**Kanonik payload boyutu: 24 bayt.** Kablo düzeni Python `struct` gösterimiyle
`<Qiihhf` şeklindedir. Host, IMU'suz fakat uint64 zaman damgalı 20 baytlık
`<Qiihh` geçiş paketini odometri için güvenle kabul eder; bu pakette
`/imu/data_raw` yayınlanmaz. Eski uint32 zaman damgalı 16 baytlık `<Iiihh`
paket yalnızca geriye uyumluluk içindir.

`imu_yaw`, STM32'nin derece cinsinden verdiği dönüş açısıdır. Orange Pi bunu
`imu_link` çerçevesinde ROS ENU yaw quaternion'una dönüştürür; EKF ilk örneği
göreli sıfır kabul eder. Fiziksel sola dönüşte işaret tersse
`imu_angle_sign: -1.0` kullanılır.

Üç tasarım kararı ve gerekçeleri:

**Kümülatif sayaç, fark değil.** Bir çerçeve kaybolursa kümülatif sayaç kendini
onarır — sonraki mesaj toplam mesafeyi yine doğru taşır. Fark gönderilseydi kaybolan
her çerçeve odometriden kalıcı olarak mesafe silerdi ve hata birikirdi.

**Sayaç işaretli ve yönlüdür.** İleri harekette artar, geri harekette azalır;
her mesaj bir önceki çerçevenin farkını değil firmware açılışından beri kümülatif
tick değerini taşır. Kablo alanı int32'dir. Host `tick_delta` ile ardışık iki
değerin farkını alır ve sayaç sarmasını güvenli biçimde çözer.

**Sıçrama filtresi (host).** İki ardışık okuma arasındaki `|Δtick|` parametre
`max_tick_delta` (varsayılan 2000) üstündeyse çerçeve **işlenmez**; referans korunur.
Üç ardışık redde referans yeniden alınır (STM32 reset / uzun kopukluk).

**Zaman damgası STM32'den gelir.** Host, çerçevenin varış anını kullanamaz; USB/UART
gecikmesi değişkendir ve hız hesabına doğrudan gürültü olarak yansır. STM32'nin kendi
monotonik sayacı bu jitteri ortadan kaldırır.

**Ham tick gönderilir, metre değil.** Orange Pi üzerinde doğrulanan firmware,
tekerin bir tam turunda yönlü ve kümülatif 360 tick üretir. Bu değer firmware'in
nihai çıktısıdır; ROS tarafında yeniden dördül ×4 uygulanmaz. 0.100 m teker yarıçapı
için katsayı yaklaşık 1.745 mm/tick'tir.

Yön kuralı: robot ileri giderken her iki sayaç da **artar**, geri giderken azalır.
Ölçülen hız alanları aynı yön kuralını kullanır: ileri pozitif, geri negatif,
dururken sıfırdır.

### 4.2 `0x82` STATE_STATUS — 10 Hz

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | uint32 | `timestamp_us` | |
| 4 | uint16 | `flags` | bkz. aşağıdaki tablo |
| 6 | uint16 | `battery_mv` | mV (MAX471) |
| 8 | int16 | `current_ma_left` | mA (ACS712) |
| 10 | int16 | `current_ma_right` | mA |
| 12 | int8 | `temperature_c` | °C (DHT22) |
| 13 | uint8 | `fork_state` | 0=alt, 1=hareket, 2=üst, 3=bilinmiyor |

Bayrak bitleri:

| Bit | Anlam |
|---|---|
| 0 | `ESTOP_ACTIVE` — donanımsal buton basılı |
| 1 | `MODE_MANUAL` — fiziksel anahtar manuel konumda |
| 2 | `MOTORS_ENABLED` |
| 3 | `LIMIT_SWITCH_UP` |
| 4 | `LIMIT_SWITCH_DOWN` |
| 5 | `OVERCURRENT` |
| 6 | `WATCHDOG_TRIGGERED` |
| 7 | `CMD_CLAMPED` |
| 8 | `ENCODER_FAULT` — bir tekerlek komut alıyor ama tick gelmiyor |

`MODE_MANUAL` şartnamenin zorunlu kıldığı kilit için kullanılır: anahtar otomatik
konumdayken uzaktan manuel komutlar uygulanmamalıdır.

---

## 5. Watchdog ve Güvenlik

STM32, **200 ms** boyunca `CMD_WHEEL_RPM` veya `CMD_HEARTBEAT`
almazsa motorları kontrollü şekilde durdurmalı ve `WATCHDOG_TRIGGERED` bayrağını
kaldırmalıdır. Orange Pi çökmesi, ROS düğümünün ölmesi veya kablo kopması durumunda
araç serbest kalmamalıdır.

Watchdog tetiklendikten sonra motorlar, host açıkça `CMD_SAFETY` ile hatayı temizleyene
kadar kilitli kalır. Komut akışının kendiliğinden geri gelmesi hareketi başlatmaz.

Aşırı akım eşiği aşıldığında STM32, host'tan onay beklemeden sürücü enable hatlarını
keser (rapor §4.3.1.4.2).

---

## 6. Açılış Dizisi

1. Host portu açar, 100 ms bekler, tampondaki artıkları temizler.
2. Host `CMD_SAFETY(0x02, hatayı temizle)` gönderir.
3. STM32 `STATE_STATUS` ile yanıt verir; host bayrakları kontrol eder.
4. E-stop basılı veya anahtar manuel konumdaysa host motorları etkinleştirmez,
   yalnızca telemetri okur.
5. Aksi halde host periyodik komut yayınına başlar.

Host ilk `STATE_ODOMETRY` mesajındaki tick değerlerini **sıfır referansı** olarak alır;
STM32'nin sayacı sıfırlaması gerekmez.

---

## 7. Elektronik Ekibinden Beklenenler

Bu protokolü uygulamak için netleşmesi gereken üç konu var; ikisi zaten navigasyon
tarafında da açık soru olarak duruyor:

1. **Encoder tick sözleşmesi doğrulandı:** firmware teker turu başına yönlü ve
   kümülatif 360 tick gönderir; ROS tarafı bu değere yeniden ×4 uygulamaz.
2. **Tekerlek ekseni arası mesafe** — kinematik dönüşüm Orange Pi'de yapıldığı için
   bu değer bize lazım.
3. **STM32 zamanlayıcı çözünürlüğü** — `timestamp_us` alanının gerçekten mikrosaniye
   hassasiyetinde olup olamayacağı. Değilse milisaniyeye düşürülür, protokol değişir.

---

## 8. Test Edilebilirlik

Elektronik ekibi hazır olana kadar navigasyon tarafı bu protokolü konuşan bir **sahte
STM32** ile geliştirilecektir. Firmware hazır olduğunda tek değişiklik seri portun
gerçek cihaza yönlendirilmesidir.

Protokol çözücüsü için birim testleri yazılacak: bozuk CRC, kayıp çerçeve, sayaç
taşması, watchdog tetiklenmesi ve senkron kayması senaryoları.
