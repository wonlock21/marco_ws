#!/usr/bin/env bash
# slam_toolbox haritasini kaydeder.
#
# slam_toolbox /slam_toolbox/save_map servisini sunar. Cikti iki dosya:
#   <hedef>.pgm   — isgal grid'i
#   <hedef>.yaml  — origin, resolution, image yolu
#
# Varsayilan hedef: marco_navigation/maps/<isim>
# Saha 60 dk penceresinde tek komutla kayit icin yazildi.
#
# Kullanim:
#   ros2 run marco_localization harita_kaydet.sh
#   ros2 run marco_localization harita_kaydet.sh depo_a
#   ros2 run marco_localization harita_kaydet.sh /tmp/deneme

set -u

ISIM="${1:-harita_$(date +%Y%m%d_%H%M%S)}"

# Mutlak yol degilse workspace src/marco_navigation/maps altina yaz.
# install/share'e yazmak yanlis: symlink-install'ta yeni dosyalar install'da
# kalir, src'ye dusmez; colcon rebuild ile de kaybolabilir.
if [[ "$ISIM" = /* ]]; then
    HEDEF="$ISIM"
elif [ -d "${HOME}/marco_ws/src/marco_navigation/maps" ]; then
    HEDEF="${HOME}/marco_ws/src/marco_navigation/maps/${ISIM}"
else
    HEDEF="${HOME}/kayitlar/maps/${ISIM}"
    mkdir -p "$(dirname "$HEDEF")"
fi

# Servis ayakta mi?
if ! ros2 service list 2>/dev/null | grep -qx "/slam_toolbox/save_map"; then
    echo
    echo "HATA: /slam_toolbox/save_map servisi yok."
    echo "Once mapping'i baslat:"
    echo "  ros2 launch marco_localization mapping.launch.py sahte:=true lidar:=true"
    echo
    exit 1
fi

# /map en az bir kez yayinlanmis mi? Yalnizca kucuk metadata alanini oku;
# OccupancyGrid.data dizisini metne cevirip sonra /dev/null'a atma.
if ! timeout 5 ros2 topic echo /map --once --field info > /dev/null 2>&1; then
    echo
    echo "HATA: /map topigi 5 saniyede gelmedi. slam_toolbox baslamamis"
    echo "veya /scan / odom gelmiyor olabilir."
    echo
    exit 1
fi

echo "Harita kaydediliyor: ${HEDEF}"
# slam_toolbox SaveMap: name alani uzantisiz yol ister; .pgm/.yaml ekler.
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \
    "{name: {data: '${HEDEF}'}}"

# Sonuc dosyalari
if [ -f "${HEDEF}.yaml" ] && [ -f "${HEDEF}.pgm" ]; then
    echo
    echo "================ KAYDEDILDI ================"
    ls -lh "${HEDEF}.yaml" "${HEDEF}.pgm"
    echo
    echo "YAML ozeti:"
    cat "${HEDEF}.yaml"
    echo
    echo "Yukle (Faz 5 AMCL):"
    echo "  map_server --ros-args -p yaml_filename:=${HEDEF}.yaml"
else
    echo
    echo "UYARI: servis cagrildi ama ${HEDEF}.{yaml,pgm} bulunamadi."
    echo "slam_toolbox bazen calisma dizinine yazar. Araniyor..."
    find "$HOME" /tmp -maxdepth 3 -name "$(basename "$HEDEF").yaml" 2>/dev/null | head -5
    exit 1
fi
