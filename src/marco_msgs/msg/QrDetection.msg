# Okunan QR kodu ve kameraya gore konumu.
# Yayinci: goruntu isleme ekibi (GM67 + OpenCV). Tuketici: marco_mission, marco_docking.
# Sartname madde 5: QR okuma ve QR kodun kameraya gore pozisyonunun hesaplanmasi.

std_msgs/Header header

# QR goruntude tespit edilebildi mi.
bool detected

# QR icerigi. Istasyon kimligi burada tasinir, gorev hedefiyle karsilastirilir.
string data

# QR kodun kamera cercevesine gore konumu.
# x ileri [m], y sola [m], theta QR duzleminin donusu [rad].
geometry_msgs/Pose2D pose_in_camera

# Tespit guveni [0.0 - 1.0].
float32 confidence

# Olcumun alindigi kamera: "front" veya "rear".
string camera_frame
