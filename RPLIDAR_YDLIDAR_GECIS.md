# RPLIDAR / YDLIDAR geçiş notu

## Aktif durum

Sistem şu anda ana LiDAR olarak **SLAMTEC RPLIDAR A2M12** kullanır. Aktif
sürücü, ROS 2 Humble paket deposundaki resmi `rplidar_ros` paketidir. A2M12
için seri hız `256000`, tarama modu `Sensitivity`, açı telafisi açıktır.

Aktif veri akışı:

```text
RPLIDAR A2M12 (rplidar_ros/rplidar_node)
  -> /scan_raw
  -> scan_to_scan_filter_chain
  -> /scan
  -> SLAM Toolbox / AMCL / Nav2
```

Safety katmanı da diğer tüketiciler gibi filtrelenmiş `/scan`ı dinler.
LiDAR'ın varsayılan `/scan` çıkışı `robot.launch.py` içinde `/scan_raw`a
remap edilir; filtrelenmemiş veri nihai `/scan`a verilmez.
Güncel fiziksel ölçüme göre `base_link -> laser_link` ötelemesi
`[0.270, 0.000, 0.200] m`dir; tarama düzlemi yerden `0.300 m` yüksektedir.

Kalıcı cihaz yolu `/dev/marco_lidar`dır. Kaynak udev kuralı:

```text
src/marco_bringup/udev/99-marco-lidar.rules
```

Kural CP210x tabanlı tek bağlı LiDAR için modelden bağımsız yolu üretir.
RPLIDAR ve YDLIDAR aynı anda bağlanmamalıdır.

Kuralı yeni Orange Pi kurulumuna yüklemek için:

```bash
sudo install -m 0644 \
  ~/marco_ws/src/marco_bringup/udev/99-marco-lidar.rules \
  /etc/udev/rules.d/99-marco-lidar.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=tty
```

## RPLIDAR entegrasyonunda değişen dosyalar

- `src/marco_bringup/launch/robot.launch.py`: aktif sürücü `rplidar_node`,
  ham topic remap'i `/scan_raw`.
- `src/marco_localization/config/lidar_rplidar_a2m12.yaml`: A2M12 seri,
  frame ve tarama ayarları.
- Haritalama, lokalizasyon, rota ve gerçek sistem launch/manager dosyaları:
  varsayılan LiDAR yolu `/dev/marco_lidar`.
- `src/marco_bringup/launch/real_system.launch.py`: donanım bağımlılığı ve
  preflight kontrolü `rplidar_ros` / RPLIDAR olarak güncellendi.
- `src/lidar_filter/launch/lidar_with_filter.launch.py`: bağımsız aktif
  LiDAR testi RPLIDAR kullanır.
- `src/marco_bringup/udev/99-marco-lidar.rules`: kalıcı cihaz yolu.

YDLIDAR konfigürasyonu ve launch dosyası silinmemiştir:

```text
src/marco_localization/config/lidar_tmini_pro.yaml
src/lidar_filter/launch/ydlidar_tmini_pro_with_filter.launch.py
```

## Tekrar YDLIDAR T-mini Pro'ya dönmek

1. `src/marco_bringup/launch/robot.launch.py` içinde:
   - config dosyasını `lidar_tmini_pro.yaml` yap,
   - paketi `ydlidar_ros2_driver`, executable'ı
     `ydlidar_ros2_driver_node`, node adını `ydlidar_ros2_driver_node` yap,
   - port override anahtarını `serial_port` yerine YDLIDAR'ın `port`
     parametresi yap,
   - `('scan', '/scan_raw')` remap'ini aynen koru.
2. `src/marco_bringup/launch/real_system.launch.py` içindeki zorunlu paketi
   `rplidar_ros` yerine `ydlidar_ros2_driver` yap ve preflight etiketini
   YDLIDAR olarak değiştir.
3. Varsayılan `/dev/marco_lidar` yolu korunabilir. Ham `/dev/ttyUSB0`
   kullanılacaksa bütün `lidar_port` varsayılanlarını birlikte geri al.
4. Bağımsız test için saklanan launch kullanılabilir:

   ```bash
   ros2 launch lidar_filter ydlidar_tmini_pro_with_filter.launch.py
   ```

YDLIDAR akışı tekrar şöyle olmalıdır:

```text
YDLIDAR T-mini Pro
  -> /scan_raw
  -> mevcut filtre
  -> /scan
  -> SLAM Toolbox / AMCL / Nav2
```

## Tekrar RPLIDAR A2M12'ye dönmek

1. `robot.launch.py` içinde `rplidar_ros/rplidar_node` ve
   `lidar_rplidar_a2m12.yaml`ı etkinleştir.
2. `real_system.launch.py` zorunlu paketini `rplidar_ros` yap.
3. `/dev/marco_lidar`, `laser_link`, `/scan_raw` remap'i ve mevcut filtre
   çıkışı `/scan` olarak kalmalıdır.
4. Bağımsız doğrulama:

   ```bash
   ros2 launch lidar_filter lidar_with_filter.launch.py
   ros2 topic hz /scan_raw
   ros2 topic hz /scan
   ```
