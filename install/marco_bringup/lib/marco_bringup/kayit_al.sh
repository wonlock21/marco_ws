#!/usr/bin/env bash
# MarCO kayit alma yardimcisi.
#
# Neden var: kayit komutunu, launch'un calistigi terminale yazmak kolay bir
# hata. O terminal komutu calistirmaz, girdi tamponunda bekletir; Ctrl+C ile
# launch kapatilinca komut ancak o zaman calisir ve robot coktan olmustur.
# Sonuc, icinde tek bir /tf_static mesaji olan bos bir kayittir. Boyle bir
# kaydi "ros2 bag play --loop" ile oynatmak sonsuz donguye girer ve ekrani
# "Opened database ... READ_ONLY" satirlariyla doldurur.
#
# Bu betik once topiklerin gercekten yayinda oldugunu dogrular, degilse
# kayit almadan aciklama yapip cikar.
#
# Kullanim:
#   ros2 run marco_bringup kayit_al.sh [sure_saniye] [isim]
#
# Ornek:
#   ros2 run marco_bringup kayit_al.sh          # Ctrl+C'ye kadar kaydeder
#   ros2 run marco_bringup kayit_al.sh 30       # 30 saniye kaydeder

set -u

SURE="${1:-0}"
ISIM="${2:-kayit_$(date +%Y%m%d_%H%M%S)}"
HEDEF="${HOME}/kayitlar/${ISIM}"

TOPIKLER=(/scan /odom /joint_states /tf /tf_static /robot_description)
# Kaydin ise yaramasi icin bunlarin canli olmasi sart. /tf_static ve
# /robot_description tek seferlik yayinlandigi icin listede degil.
ZORUNLU=(/scan /odom /tf)

echo "Topikler kontrol ediliyor..."
mevcut="$(ros2 topic list 2>/dev/null)"
eksik=()
for t in "${ZORUNLU[@]}"; do
    grep -qx -- "$t" <<< "$mevcut" || eksik+=("$t")
done

if [ ${#eksik[@]} -ne 0 ]; then
    echo
    echo "HATA: su topikler yayinda degil: ${eksik[*]}"
    echo
    echo "Robot calismiyor gorunuyor. AYRI bir terminalde once sunu baslatin:"
    echo "  ros2 launch marco_bringup robot.launch.py sahte:=true lidar:=true"
    echo
    echo "Sonra BU terminale donup kayit komutunu tekrar calistirin."
    echo "Kayit komutunu launch'un calistigi terminale YAZMAYIN."
    exit 1
fi

# Topik listede gorunuyor olabilir ama yayin durmus olabilir (dugum oldu,
# kesif onbellegi bayat). Gercekten mesaj akip akmadigini dogrula.
echo "Veri akisi dogrulaniyor..."
for t in "${ZORUNLU[@]}"; do
    if ! timeout 5 ros2 topic echo "$t" --once > /dev/null 2>&1; then
        echo
        echo "HATA: $t listede var ama 5 saniyede mesaj gelmedi."
        echo "Yayinci olmus olabilir. Bayat kesif kaydini temizlemek icin:"
        echo "  ros2 daemon stop && ros2 daemon start"
        exit 1
    fi
done

mkdir -p "$(dirname "$HEDEF")"
echo
echo "Kayit basliyor: ${HEDEF}"

# stdin MUTLAKA /dev/null olmali. "ros2 bag record" SPACE ile duraklatma
# ozelligi icin terminal ayarlarini degistirmeye calisiyor (tcsetattr).
# Bu betik "ros2 run" altinda arka plan surec grubunda calistigindan,
# terminale dokundugu anda cekirdek SIGTTOU gonderip sureci DONDURUYOR:
# process "T (stopped)" durumuna dusuyor, veritabani hic olusmuyor ve
# hicbir hata mesaji cikmiyor. Ekranda yalnizca "Kayit basliyor" kalir.
# stdin tty olmayinca rosbag klavye isleyicisini hic kurmuyor.
if [ "$SURE" -gt 0 ] 2>/dev/null; then
    echo "Sure: ${SURE} saniye"
    timeout --signal=INT "$SURE" \
        ros2 bag record -o "$HEDEF" "${TOPIKLER[@]}" < /dev/null
else
    echo "Durdurmak icin Ctrl+C"
    ros2 bag record -o "$HEDEF" "${TOPIKLER[@]}" < /dev/null
fi

echo
echo "================ KAYIT OZETI ================"
ros2 bag info "$HEDEF" 2>/dev/null | grep -E "Duration|Messages|Topic:"
echo
echo "Izlemek icin, iki AYRI terminalde:"
echo "  ros2 launch marco_bringup viewer.launch.py sim:=true"
echo "  ros2 bag play ${HEDEF} --clock --loop"
