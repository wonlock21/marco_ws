# Bir A/B istasyonuna son yaklasim icin saha-paketi konfigurasyonu.
string station_id
uint64 station_node_id
string approach_qr_id
# Geriye uyumlu read-only/debug alanidir. ROS rota geometrisinden turetir;
# SaveStationApproachConfig istegindeki deger kaydedilmez ve kullanilmaz.
float32 dock_heading_yaw
# Geriye uyumlu read-only/debug alanidir. Runtime local costmap'ten secer;
# SaveStationApproachConfig istegindeki deger kaydedilmez ve kullanilmaz.
string turn_direction
float32 line_follow_duration_s
