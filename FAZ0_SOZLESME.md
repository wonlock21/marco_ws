# Faz 0 Kaynak ve Sahiplik Sözleşmesi

Başlangıç HEAD: `1d43061` (`yeni_proje_plani baslangic`).
Bu çalışma kirli kullanıcı ağacını koruyarak yapılmıştır; commit/push kullanıcıya
bırakılmıştır.

## Araç değerleri

- Teker yarıçapı: `0.100 m` (100 mm, 10 cm)
- Encoder: `360 tick/tur` (firmware çıktısına tekrar ×4 uygulanmaz)
- Fiziksel/URDF teker merkez aralığı: `0.460 m`
- Saha kalibreli etkin odometri aralığı: `0.421 m`
- Footprint: `x=-1.18..0.50 m`, `y=-0.35..0.35 m`
- LiDAR (`base_link`): `[-0.300, 0.000, 0.180] m`; yerden `0.280 m`

Tek doğrulama komutu:

```bash
ros2 run marco_bringup check_vehicle_contract.py
```

## Üretim sahipliği

- Rota dış action sahibi: Mission Manager → tek `NavigateToPose`
- Route BT: `ComputeRoute`, sonra `ComputeAndTrackRoute + FollowPath`
- `/route_speed_limit`: yalnız Route Server `AdjustSpeedLimit`
- `/speed_limit`: yalnız `speed_limit_manager`
- `/route/speed_limit_reset`: Mission Manager olay isteği
- `/cmd_vel_raw`: yalnız Nav2 velocity smoother
- `/cmd_vel_safe`: yalnız Collision Monitor
- `/cmd_vel`: yalnız twist_mux; base driver yalnız abonedir
- `map→odom`: AMCL; `odom→base_footprint`: EKF; sabit TF: robot_state_publisher

Simülasyon Faz 7 kabul düğümleri test-only'dir ve gerçek sistem launch'ında açılmaz.
