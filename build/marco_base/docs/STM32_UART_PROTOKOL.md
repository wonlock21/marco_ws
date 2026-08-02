# Orange Pi 5 ↔ STM32 UART Haberleşme Protokolü

**Sürüm:** 0.3 · **Tarih:** 30.07.2026 · **Hazırlayan:** Yazılım / Navigasyon
**Değişiklikler:** Baud 115200 · encoder tick 2¹⁶ sarma · host sıçrama filtresi (`max_tick_delta`)

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

### 3.1 `0x01` CMD_WHEEL_VELOCITY — 50 Hz

Kinematik dönüşümü (`/cmd_vel` → tekerlek hızları) **Orange Pi yapar**. STM32 yalnızca
her tekerlek için ayrı PID koşturur. Bu ayrım, tekerlek ekseni arası mesafe gibi
kalibrasyon parametrelerinin ROS tarafında kalmasını sağlar; STM32 firmware'ini
yeniden derlemeden kalibrasyon yapılabilir.

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | int16 | `left_target` | mm/s, ileri pozitif |
| 2 | int16 | `right_target` | mm/s, ileri pozitif |
| 4 | uint8 | `flags` | bit0 = motorlar etkin |

Sınır: ±838 mm/s (12 V'ta 80 RPM, 200 mm tekerlek). STM32 bu değeri aşan komutları
kırpmalı ve durum mesajında `FLAG_CMD_CLAMPED` kaldırmalıdır.

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

### 3.4 `0x04` CMD_MOTOR_PWM — 50 Hz (açık döngü)

Şerit takibi gibi kamera kapalı döngülü yollar için. STM32 **PID çalıştırmaz**;
değeri sürücü köprüsüne doğrudan yazar. `CMD_WHEEL_VELOCITY` ile aynı anda
gelmemelidir — host yalnızca birini kullanır (`base_driver` veya `pwm_bridge`).

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | int16 | `left_pwm` | ham PWM, ileri pozitif |
| 2 | int16 | `right_pwm` | ham PWM, ileri pozitif |
| 4 | uint8 | `flags` | bit0 = motorlar etkin |

Alan tipi `int16`: bugün host 0..150 gönderir; işaret geri yönü, genişlik ise
ileride 0..255 veya 0..1000'e çıkılmasını protokolü değiştirmeden mümkün kılar.
Firmware timer ARR değeri ile ölçek eşleşmesi STM32 tarafının işidir.

### 3.5 `0x05` CMD_HEARTBEAT — 10 Hz

Boş yük. Bkz. §5 watchdog.

---

## 4. STM32 → Orange Pi Mesajları

### 4.1 `0x81` STATE_ODOMETRY — 100 Hz

Bu, protokolün en kritik mesajıdır. Odometrinin tamamı buradan türetilir.

| Ofset | Tip | Alan | Birim |
|---|---|---|---|
| 0 | uint32 | `timestamp_us` | STM32 açılışından beri geçen mikrosaniye |
| 4 | int32 | `left_ticks` | **kümülatif** encoder; değer daima **[0, 65535]** (2¹⁶ sarma) |
| 8 | int32 | `right_ticks` | **kümülatif** encoder; değer daima **[0, 65535]** (2¹⁶ sarma) |
| 12 | int16 | `left_speed` | mm/s, STM32'nin ölçtüğü anlık hız |
| 14 | int16 | `right_speed` | mm/s |

**Kanonik payload boyutu: 16 bayt.** Host ≥16 baytı kabul eder ve yalnızca ilk 16'yı
çözer (30.07 sahada firmware'in 24 bayt + sondaki 8 sıfır gönderdiği görüldü).
STM32 tarafı mümkün olan en kısa sürede tam 16 bayta indirmelidir.

Üç tasarım kararı ve gerekçeleri:

**Kümülatif sayaç, fark değil.** Bir çerçeve kaybolursa kümülatif sayaç kendini
onarır — sonraki mesaj toplam mesafeyi yine doğru taşır. Fark gönderilseydi kaybolan
her çerçeve odometriden kalıcı olarak mesafe silerdi ve hata birikirdi.

**Sayaç sınırı 2¹⁶ (65536).** Değer 65535'ten sonra **0'a döner** ve artmaya devam
eder. Kablo alanı geriye dönük uyumluluk için int32 kalır; anlamlı aralık uint16'dır.
Host `tick_delta` ile sarmayı çözer. Üst sınır, uzun koşularda float ara değerlerde
hassasiyet kaybını da önler.

**Sıçrama filtresi (host).** İki ardışık okuma arasındaki `|Δtick|` parametre
`max_tick_delta` (varsayılan 2000) üstündeyse çerçeve **işlenmez**; referans korunur.
Üç ardışık redde referans yeniden alınır (STM32 reset / uzun kopukluk).

**Zaman damgası STM32'den gelir.** Host, çerçevenin varış anını kullanamaz; USB/UART
gecikmesi değişkendir ve hız hesabına doğrudan gürültü olarak yansır. STM32'nin kendi
monotonik sayacı bu jitteri ortadan kaldırır.

**Ham tick gönderilir, metre değil.** Encoder'ın redüktörün öncesinde mi sonrasında mı
olduğu henüz netleşmedi. Ham tick gönderildiğinde bu belirsizlik protokolü etkilemez;
tick→metre katsayısı ROS tarafında bir parametredir ve kalibrasyonla ayarlanır.

Yön kuralı: robot ileri giderken her iki sayaç da **artar** (mod 65536).

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

STM32, **200 ms** boyunca `CMD_WHEEL_VELOCITY`, `CMD_MOTOR_PWM` veya `CMD_HEARTBEAT`
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

1. **Encoder redüktörün öncesinde mi sonrasında mı?** Ham tick gönderdiğimiz için
   protokolü etkilemiyor, ama tick/tur değerini bilmemiz gerekiyor. Tekerlek milinde
   ise dördül kod çözmeyle 1440 tick/tur bekliyoruz.
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
