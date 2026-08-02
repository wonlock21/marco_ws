#!/usr/bin/env bash
# AMCL baslangic pozunu /initialpose topigine yayinlar.
#
# RViz "2D Pose Estimate" ile ayni mesaj. Yarismada bekleme noktasi bilinen
# bir konum; bu betik o pozu sayisal verir.
#
# Kullanim:
#   ros2 run marco_localization baslangic_poz.sh <x> <y> <yaw_derece>
#   ros2 run marco_localization baslangic_poz.sh 0 0 90
#
# x,y metre (map cercevesi); yaw DERECE (kolaylik icin). Iceride radyana cevrilir.

set -u

if [ "$#" -lt 3 ]; then
    echo "Kullanim: baslangic_poz.sh <x_m> <y_m> <yaw_derece>"
    echo "Ornek:    baslangic_poz.sh 0.0 0.0 0"
    exit 1
fi

X="$1"
Y="$2"
YAW_DEG="$3"

# Derece → radyan, quaternion z/w (duzlemsel yaw)
# qz = sin(yaw/2), qw = cos(yaw/2)
read -r QZ QW <<< "$(python3 - "$YAW_DEG" <<'PY'
import math, sys
yaw = math.radians(float(sys.argv[1]))
print(f"{math.sin(yaw/2):.10f} {math.cos(yaw/2):.10f}")
PY
)"

# AMCL ayakta mi?
if ! ros2 node list 2>/dev/null | grep -q "/amcl"; then
    echo "HATA: /amcl dugumu yok. Once:"
    echo "  ros2 launch marco_localization amcl.launch.py sahte:=true lidar:=true"
    exit 1
fi

# Kovaryans: baslangicta makul belirsizlik (x,y ~0.25 m std, yaw ~10 deg)
# 6x6 poz kovaryansi satir-major: xx xy xz ... → indeks 0=xx, 7=yy, 35=yawyaw
COV_X=0.25
COV_Y=0.25
COV_YAW=0.17   # ~10 derece radyan cinsinden std

echo "Baslangic pozu: x=${X} y=${Y} yaw=${YAW_DEG} deg  (map)"

ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{
  header: {frame_id: 'map'},
  pose: {
    pose: {
      position: {x: ${X}, y: ${Y}, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: ${QZ}, w: ${QW}}
    },
    covariance: [
      ${COV_X}, 0, 0, 0, 0, 0,
      0, ${COV_Y}, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, ${COV_YAW}
    ]
  }
}"

echo
echo "Kontrol: timeout 5 ros2 topic echo /amcl_pose --once"
echo "         timeout 5 ros2 run tf2_ros tf2_echo map odom"
