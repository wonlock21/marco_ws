# MarCO Test Komutları

## Her Yeni Orange Pi Terminalinde Hazırlık

```bash
cd ~/marco_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Her Yeni WSL Terminalinde Hazırlık

```bash
cd ~/marco_ws_git
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## Tüm Projeyi Derleme ve Test Etme

### Terminal 1

```bash
cd ~/marco_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
colcon test
colcon test-result --verbose
```

## Faz 1 — Robot Modeli ve TF

### Terminal 1

```bash
ros2 launch marco_description display.launch.py
```

### Terminal 2

```bash
ros2 run tf2_tools view_frames
```

## Faz 2 — WSL Gazebo ve RViz Görsel Testi

### Terminal 1 — WSL

```bash
ros2 launch marco_simulation simulation.launch.py \
  gazebo_gui:=true \
  software_gazebo_server:=true \
  software_gazebo_gui:=true \
  gazebo_gpu_adapter:=NVIDIA \
  rviz:=true \
  visual_test:=true
```

## Faz 2 — Simülasyon Topic Kontrolü

### Terminal 2

```bash
ros2 topic hz /scan
```

### Terminal 3

```bash
ros2 topic hz /odom
```

### Terminal 4

```bash
ros2 topic hz /camera/image_raw
```

## Faz 3 — Nominal Odometri ve EKF Kabulü

### Terminal 1

```bash
ros2 launch marco_localization phase3_acceptance.launch.py \
  scenario:=nominal \
  rviz:=true
```

## Faz 3 — Headless Odometri ve EKF Kabulü

### Terminal 1

```bash
ros2 launch marco_localization phase3_acceptance.launch.py \
  scenario:=nominal \
  rviz:=false
```

## Faz 3 — Tekerlek Ölçek Hatası Testi

### Terminal 1

```bash
ros2 launch marco_localization phase3_acceptance.launch.py \
  scenario:=scale_error \
  rviz:=false
```

## Faz 3 — Tekerlek Aralığı Hatası Testi

### Terminal 1

```bash
ros2 launch marco_localization phase3_acceptance.launch.py \
  scenario:=separation_error \
  rviz:=false
```

## Faz 3 — Gerçek Encoder Düz Sürüş Testi

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_localization localization.launch.py \
  sahte:=false \
  lidar:=false \
  imu:=false \
  rviz:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 run marco_localization odometry_check.py \
  --test duz \
  --distance 10.0
```

## Faz 3 — Gerçek Encoder 360 Derece Dönüş Testi

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_localization localization.launch.py \
  sahte:=false \
  lidar:=false \
  imu:=false \
  rviz:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 run marco_localization odometry_check.py \
  --test donus \
  --turn-deg 360.0
```

## Faz 4 — WSL Otomatik Haritalama Kabulü

### Terminal 1 — WSL

```bash
ros2 launch marco_localization simulation_mapping.launch.py \
  rviz:=true \
  gazebo_gui:=false \
  software_gazebo_server:=true \
  software_gazebo_gui:=true \
  gazebo_gpu_adapter:=NVIDIA \
  auto_drive:=true \
  run_acceptance:=true \
  save_map:=true \
  map_output:=/tmp/marco_phase4/marco_test
```

## Gerçek LiDAR ve Odometri Kontrolü

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_bringup robot.launch.py \
  sahte:=false \
  lidar:=true \
  rviz:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 topic hz /scan
```

### Terminal 3 — Orange Pi

```bash
ros2 topic hz /odom
```

### Terminal 4 — Orange Pi

```bash
ros2 run tf2_ros tf2_echo odom laser_link
```

## Faz 4 — Gerçek Araçla Haritalama

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_localization mapping.launch.py \
  sahte:=false \
  lidar:=true \
  imu:=false \
  rviz:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Terminal 3 — Orange Pi

```bash
ros2 topic hz /scan
```

### Terminal 4 — Orange Pi

```bash
ros2 run marco_localization harita_kaydet.sh yarin_test
```

## ROS Bag Kaydı

### Terminal 1 — Orange Pi

```bash
ros2 run marco_bringup kayit_al.sh 300 yarin_test
```

## ROS Bag Oynatma

### Terminal 1

```bash
ros2 launch marco_bringup viewer.launch.py sim:=true
```

### Terminal 2

```bash
ros2 bag play ~/kayitlar/yarin_test --clock
```

## Faz 5 — WSL AMCL Lokalizasyon Kabulü (Faz 5 Dosyaları Eklendiğinde)

### Terminal 1 — WSL

```bash
ros2 launch marco_localization simulation_localization.launch.py \
  rviz:=true \
  gazebo_gui:=false \
  software_gazebo_server:=true \
  software_gazebo_gui:=true \
  gazebo_gpu_adapter:=NVIDIA \
  auto_initial_pose:=true \
  auto_drive:=true \
  run_acceptance:=true \
  result_path:=/tmp/marco_phase5_acceptance.json
```

## Faz 5 — Gerçek Araç AMCL Lokalizasyonu

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_localization amcl.launch.py \
  sahte:=false \
  lidar:=true \
  harita:=yarin_test \
  baslangic:=false \
  rviz:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 run marco_localization baslangic_poz.sh 0 0 0
```

### Terminal 3 — Orange Pi

```bash
ros2 run marco_localization amcl_poz_kaydet.py \
  --sure 300 \
  --cikti /tmp/amcl_yarin.csv
```

### Terminal 4 — Orange Pi

```bash
ros2 run tf2_ros tf2_echo map base_footprint
```

## Faz 6 — Temel Nav2

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_navigation navigation_safe.launch.py \
  sahte:=false \
  lidar:=true \
  harita:=yarin_test \
  baslangic:=true \
  x:=0.0 \
  y:=0.0 \
  yaw:=0.0 \
  rviz:=false \
  use_sim_time:=false
```

### Terminal 2 — Orange Pi

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0},orientation: {w: 1.0}}}}"
```

## Faz 7 — Rota Ağı

### Terminal 1 — Orange Pi

```bash
  ros2 launch marco_navigation route.launch.py \
    sahte:=false \
    lidar:=true \
    harita:=nav_test \
    baslangic:=true
```

### Terminal 2 — Orange Pi

```bash
ros2 run marco_navigation rota_hesapla.py --start 0 --goal 8
```

## Faz 8 — Güvenli Rota

### Terminal 1 — Orange Pi

```bash
ros2 launch marco_navigation route_safe.launch.py \
  sahte:=false \
  lidar:=true \
  harita:=yarin_test \
  baslangic:=true
```

### Terminal 2 — Orange Pi

```bash
ros2 topic echo /cmd_vel_safe
```

### Terminal 3 — Orange Pi

```bash
ros2 topic echo /cmd_vel
```

## Faz 9 — Mock Docking

### Terminal 1

```bash
ros2 launch marco_docking docking.launch.py \
  mock:=true \
  scenario:=success \
  station_id:=istasyon_A
```

### Terminal 2

```bash
ros2 action send_goal /dock_to_station marco_msgs/action/DockToStation \
  "{station_id: 'istasyon_A', position_tolerance: 0.075, yaw_tolerance: 0.087, approach_type: 0, timeout: 60.0}"
```

## Faz 9 — QR Uyuşmazlığı Negatif Testi

### Terminal 1

```bash
ros2 launch marco_docking docking.launch.py \
  mock:=true \
  scenario:=qr_mismatch \
  station_id:=istasyon_A
```

## Faz 9 — Şerit Kaybı Negatif Testi

### Terminal 1

```bash
ros2 launch marco_docking docking.launch.py \
  mock:=true \
  scenario:=lane_lost \
  station_id:=istasyon_A
```

## Faz 10 — Mock Görev ve PLC

### Terminal 1

```bash
ros2 launch marco_mission mission.launch.py \
  simulate_steps:=false \
  task_source:=mock_plc \
  test_only_lift:=true
```

### Terminal 2

```bash
ros2 service call /mission/start marco_msgs/srv/StartMission "{}"
```

### Terminal 3

```bash
ros2 topic echo /robot_status
```

## Genel Topic Kontrolü

### Terminal 1

```bash
ros2 topic list
```

### Terminal 2

```bash
ros2 node list
```

### Terminal 3

```bash
ros2 topic info /scan --verbose
```

### Terminal 4

```bash
ros2 topic info /tf --verbose
```
